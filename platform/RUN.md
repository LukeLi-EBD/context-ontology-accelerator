# 运行手册（platform）

面向"另一台机器 clone 后能跑起来"。`platform/` 是独立项目：所有命令都在
**`coa/platform`** 目录下执行，无需 `-f` 指定 compose 文件。

三行起（已装 Docker Desktop；全新机器**不需要**预置数据目录）：

```powershell
git clone <repo> coa && cd coa\platform
Copy-Item .env.example .env        # 填 POSTGRES_PASSWORD；不要保留 CHANGE_ME
powershell -ExecutionPolicy Bypass -File scripts\stack.ps1 up -Name agent-platform -DataRoot D:/agentABC/data
```

> 必须用 `stack.ps1 up`，不要只跑 `docker compose up -d --wait`：`stack.ps1` 会自动建目录、
> 生成 `data/platform.yaml`，并从仓库内 `platform/seed/` 拷贝 `ontology/bootstrap.ttl` 与
> `shapes/`。全新机器上直接 `compose up` 会因缺少 T-Box 种子以 `E_ONTOLOGY_TBOX_MISSING`（69）
> 退出（2026-11-06 迁移演练实测）。

## 1. 前置条件

- Docker Desktop（WSL2 后端）。实测 VM 上限：**12 CPU / 11.68 GiB**；16 CPU 会被 Docker Desktop 直接拒绝。
- 宿主建议 16 GB 内存、D 盘可用 ≥ 20 GB（`/readyz` 会因 `min_free_pct=10` 失败）。
- 端口占用（全部绑 `127.0.0.1`）：
  - `8080` 平台 API/UI，`8081` embedding（TEI），`5432` PostgreSQL，`7879` reasoner，`3030` fuseki
  - `7878` Oxigraph **不映射宿主**（无鉴权，暴露即可绕过 GSP 治理）；二套栈如需访问用
    `docker-compose.oxigraph-host.yml` + `-OxigraphPort`
  - 二套栈必须避开上面所有默认端口（尤其 8081/7879/3030）；`stack.ps1` 的预检覆盖
    api/postgres/reasoner/embedding/oxigraph/fuseki，**不是只查 api**
- 模型与镜像：`agent-platform:0.1-s5`、`agent-reasoner:0.1-s5`、`agent-rdfs:0.1-s5`、pgvector、oxigraph、TEI 均由本地构建或拉取。

## 2. 目录准备（数据不在 git 里）

运行时数据统一放在 **`D:\agentABC\data`**（compose 以绝对路径 bind 到容器 `/data`）。
`stack.ps1 up` 会自动完成下面全部步骤；手工部署时可照做：

```powershell
Copy-Item .env.example .env                            # 放 coa/platform/.env（gitignored）
New-Item -ItemType Directory -Force D:\agentABC\data
Copy-Item platform.example.yaml D:\agentABC\data\platform.yaml   # 填 database.url 口令（与 .env 一致）
Copy-Item seed\ontology\bootstrap.ttl D:\agentABC\data\ontology\
Copy-Item seed\shapes\* D:\agentABC\data\shapes\ -Recurse
```

- **T-Box 种子随仓库提供**：`platform/seed/ontology/bootstrap.ttl`（660 B）与
  `platform/seed/shapes/`（core + fsldm）。非默认数据根优先从默认数据根拷贝，找不到时回退到
  `platform/seed/`；两者都没有时启动会以 `E_ONTOLOGY_TBOX_MISSING` 失败。
- `platform.yaml` 里 `database.url` 的口令必须与 `.env` 的 `POSTGRES_PASSWORD` 一致。`serve`
  会读 compose 注入的 `PLATFORM__DATABASE__URL`，但 `smoke-s3` 这类会用文件里 URL 起第二个池的
  子命令不走覆盖，口令不一致会 `password authentication failed`。`stack.ps1` 检测到
  `CHANGE_ME` 会打印 WARNING。
- `D:\agentABC\data\models\bge-m3\`：BGE-M3 模型约 **2.14 GB**（含 `pytorch_model.bin` 2.17 GB），目录固定，只读挂载给 TEI。
  离线拷贝：`robocopy <源>\models D:\agentABC\data\models /E`。不放入时 embedding 容器无法启动，检索退化为仅词法（响应标注 `lexicalOnly`）。
- `reasoner/robot.jar`（93 MB）**不需要手工放置**：`reasoner` 镜像构建时自动下载并校验，见下节。
- `D:\agentABC\data\` 全部内容不进 git；`coa/.gitignore` 已排除 `platform/data/`、`platform/logs/`、`platform/models/`、`platform/.env`。

### robot.jar（reasoner，构建时自动下载）

`platform/reasoner/Dockerfile` 默认在构建时从 ROBOT 官方 release 拉取 `robot.jar`
（v1.9.6，93,636,279 字节），并用 `ROBOT_JAR_SHA256` 校验；下载失败或文件为空时**构建直接失败**，
不会静默留下空文件。

联网构建（标准）：

```powershell
docker compose build reasoner
# 等价：docker build -t agent-reasoner:0.1-s5 -f platform/reasoner/Dockerfile platform/reasoner
```

换版本或换源（两个 build-arg）：

```powershell
docker compose build reasoner `
  --build-arg ROBOT_JAR_URL=https://github.com/ontodev/robot/releases/download/v1.9.6/robot.jar `
  --build-arg ROBOT_JAR_SHA256=3d112f47a5c2e82fd96c2bc40e582a86d1e6ad24f67648ef103ec5f21985ba5e
# 内网镜像若提供的是不同的构建，传 ROBOT_JAR_SHA256= 可关闭校验（不建议）
```

> 本机实测（2026-11-05）：GitHub 直链约 **32 KB/s**（93.6 MB 约需 50 分钟）。
> 已验证的替代源：`https://gh-proxy.com/https://github.com/ontodev/robot/releases/download/v1.9.6/robot.jar`
> （约 21 MB/s，完整 93,636,279 字节；构建内 `sha256sum -c` 通过，证明与官方字节一致）。
> 这是第三方代理，只作加速示例，正式环境优先用内网制品库。

离线 / 内网（两种替代路径）：

1. **内网制品库（推荐）**：`--build-arg ROBOT_JAR_URL=<内网直链>`，sha 校验照常生效。
2. **完全无网络**：`--build-arg ROBOT_JAR_URL=` 构建出不含 jar 的镜像（会打印 WARNING），
   运行时把本机 jar 挂到 `/opt/robot/robot.jar`：

```powershell
docker compose build reasoner --build-arg ROBOT_JAR_URL=
docker run --rm -v D:\agentABC\coa\platform\reasoner\robot.jar:/opt/robot/robot.jar:ro `
  agent-reasoner:0.1-s5 java -jar /opt/robot/robot.jar --version
```

   用 compose 时加一个 override 文件（如 `platform/reasoner.local.yml`）：

```yaml
services:
  reasoner:
    volumes:
      - ./reasoner/robot.jar:/opt/robot/robot.jar:ro
```

校验（容器内，跑完即删，不占端口）：

```powershell
docker run --rm agent-reasoner:0.1-s5 java -jar /opt/robot/robot.jar --version
# 实测输出：ROBOT version 1.9.6
```

本机实测（2026-11-05，Docker Desktop 29.9.2）：

- 构建耗时 **104.3 s**（robot.jar 走上表的代理源，Jena 走本地镜像；pip 走清华源）
- 镜像 **383 MB**，其中 jar 层 **93.6 MB**
- `java -jar /opt/robot/robot.jar --version` → **`ROBOT version 1.9.6`**
- 反例：`--build-arg ROBOT_JAR_URL=https://github.com/ontodev/robot/releases/download/v9.9.9/robot.jar`
  构建退出码 **1**，不产镜像（`curl` 重试耗尽后失败），证明不会静默留空
- 离线：`--build-arg ROBOT_JAR_URL=` 构建退出码 0，镜像内 `/opt/robot/robot.jar` 不存在，需运行时挂载
- Jena 官方 `archive.apache.org` 在本机仅约 **20 KB/s**（23.6 MB 约 20 分钟）；同样可用
  `--build-arg JENA_URL=<内网镜像直链>` 指到快源（实测用本地 HTTP 镜像）

## 3. 启动顺序

```powershell
docker compose build      # 首次构建；reasoner 会联网下载 robot.jar（见上节）
docker compose up -d
docker compose ps
```

迁移在平台启动时自动执行，脚本位于 `src/platform_core/sql/V1__s0.sql … V43__source_ref_stale_mark.sql`，
**当前最新为 V43（schema_version=43）**（以 `sql/` 目录里编号最大的文件与实际 `SUPPORTED_SCHEMA_VERSION` 为准）。

期望返回：

```powershell
curl.exe -s http://127.0.0.1:8080/readyz
# {"ok":true,"checks":{"database":{"status":"ok"},"graph":{"status":"ok"},
#  "storage":{"status":"ok","disk_free_pct":...}}}
# 只检查 database/graph/storage；embedding/reasoner 不可用不会让 /readyz 非 200
# 任一 status=fail 时 HTTP 非 200，detail 指明原因

curl.exe -s http://127.0.0.1:8080/status
# 关键字段：disk{free_pct,free_bytes,total_bytes}、counts{blobs,refs}、
#          ontology{pointer,versions,statuses}、triples
```

UI：浏览器打开 `http://127.0.0.1:8080/`（原生 HTML，无需前端构建链）。

## 4. 验收入口

| 命令 | 期望 |
| --- | --- |
| `docker compose exec -T platform platform smoke-s1` | 逐项 `[PASS]`，退出码 0 |
| `docker compose exec -T platform platform smoke-embed` | 8/8 `[PASS]`（含 `E_EMBED_MODEL_MISMATCH` 守卫断言） |
| `powershell -File tests/acceptance.ps1` | 逐项输出 `[PASS] name detail` / `[FAIL] name detail`，末尾统计；**退出码 0 = 全部通过**，非 0 = 有失败项 |
| `powershell -File scripts/acceptance-s14.ps1` | S14 专项一键验收：g01 / governance / browse / terms / metric / q7 / q8；末尾 `S14 ACCEPTANCE passed=N failed=N skipped=N`，**失败退出码 1** |

`acceptance.ps1` 覆盖 `docker compose config`、各 smoke-sN、演示库纯净性等；单项失败不中断，最后汇总。
`acceptance-s14.ps1` 用当前镜像 + 挂载工作树 `src`/`tests` 跑 S14 用例（默认 `-ComposeProject agent-platform`、`-Image agent-platform:0.1-s5`、网络 `<project>_default`），自动持重型锁；失败**不会计成 skipped**，而是计入 `failed` 并退出 1。可用 `-NoLock` 跑已持锁场景。
所有 smoke 写入独立命名图并在结束时清理，不污染演示库。

## 5. 并发与资源

- 重型锁：`scripts/compose-guard.ps1` 管理 `.lock/`，长操作必须
  `compose-guard acquire -Purpose <描述> -TtlMinutes 30 -Owner <owner>` →
  每 ≤5 分钟 heartbeat → 结束 `compose-guard release`。
  `status` 查看当前持有者；`-Force` 仅用于确认遗留死锁后强制接管。
- `up.ps1` 通过锁检查；`-AssumeLock -Owner <owner>` 仅在 owner 与当前锁一致时跳过检查。
- embedding 档位（`scripts/burst.ps1`）——**默认 background，burst 必须显式开启**：
  - `burst.ps1 background`（= `off`）：cpus **4** / `RAYON_NUM_THREADS` **4** / `MAX_CONCURRENT_REQUESTS` **4** /
    `max_chunks_per_sec` **1.0**；切完跑 `smoke-embed` 12/12 + `/readyz`，是**日常默认档**，一键回落用。
  - `burst.ps1 on`：cpus→8 / RAYON→8 / rate→0（不限速）；**必须人工显式开启**，且切档过程持重型锁
    （`compose-guard acquire`），不得在并发验收/他人作业期间提档。
  - `burst.ps1 status`：只读打印当前 `cpus/rayon/rate`；`-Cpus/-Rayon` 用于阶梯测试。
  - 适用场景与判据：

    | 档 | 适用 | 判据（实测） |
    |---|---|---|
    | background（4 核/rate 1.0） | 日常入库、验收、与人共享机器 | 64 真实 chunk 0.525 chunk/s、P50 1,277.5 ms / P95 5,605.9 ms；宿主 CPU 峰 28%（<50%）、可用内存 ≥11.23 GB（>8 GB）→ 机器始终可用 |
    | burst（8 核/rate 0） | 无人值守的批量回填窗口 | real-11 0.60 chunk/s、real-22 0.777 chunk/s；12 核对 8 核仅 +6.5%（<15% 阈值），16 核被 Docker Desktop 拒绝（VM 仅 12 CPU） |

  - 结论：**不追 12/16 核**；瓶颈是 TEI 单飞 + 长块推理（长块 3.76 s/chunk，平台侧仅 3.1 ms/chunk），不是核数。
  - 切档后必须 `readyz` + `smoke-embed` 全过才可批量作业。
  - `smoke-s13` 撞上他人 heavy job 时**排队等待**（2s 间隔，预算 180s）；预算耗尽输出
    `SKIP blocked_by_heavy` 并以**退出码 75** 结束，`acceptance.ps1` 计入 `skipped` 而非 `failed`。
- 批量入库：`scripts/bulk-index.ps1` 分段可续跑；限速默认 `max_chunks_per_sec=1.0`（约实测上限 2.19 chunk/s 的 60%）。

## 6. 常见故障

| 现象 | 原因与处置 |
| --- | --- |
| `E_DB_MIGRATION_MISMATCH` | 库里 `schema_version` 与代码期望不一致（多为旧数据卷）。比对 `platform.schema_version` 最大值与 `sql/` 最新 Vxx；必要时重建数据卷（会丢数据） |
| `E_EMBED_MODEL_MISMATCH` | 查询/写入的向量模型与分区指针不一致。检查 `embedding.active_model` 与 `dim`，不要混用模型向量；切回旧模型需 `platform reindex --provider` |
| embedding 容器反复重启，日志含 `queue.rs` `Full(..)` panic | `MAX_CONCURRENT_REQUESTS` 过低（=1 必崩）。compose 默认 4，回退不要低于 4 |
| PowerShell 报 `MissingSwitchStatementClause` / 脚本乱码 | `.ps1` 必须以 **UTF-8 BOM** 保存（Windows PowerShell 5.1 按 ANSI 读取无 BOM 文件） |
| `docker compose build` 在 `pip install` 处很慢或 `Read timed out` | 默认 `PIP_INDEX_URL=https://pypi.org/simple`；国内改用 `--build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple`（或设同名环境变量） |
| `docker compose build` 卡在 Jena 下载（RUN 里的 `curl ... "$JENA_URL" \| tar`） | 官方 `archive.apache.org` 实测仅约 20 KB/s（23.6 MB）；用 `--build-arg JENA_URL=<内网/快源直链>` |
| reasoner 构建在下载 robot.jar 处失败（`curl` 非 0） | GitHub release 不可达；改 `--build-arg ROBOT_JAR_URL=<内网镜像直链>`，或 `ROBOT_JAR_URL=` 后运行时挂载 jar（见 §2） |
| `/readyz` 中 `storage.status=fail` | `data/blobs` 目录缺失或磁盘可用低于 10% |
| reasoner 相关接口 `E_REASONER_UNAVAILABLE` | reasoner 容器未起（缺 `robot.jar` 或 profile 未开）；平台其余功能不受影响 |

## 7. 已知限制

- 扫描件（图片型 PDF）需显式开启 OCR（`ocr.enabled=true`，镜像内置 tesseract 中英文）。
- `.ppt` / `.doc` 旧格式需先转换为 `.pptx` / `.docx` 才能解析。
- 加密 PDF 不可解析，入库时会标记失败计数。
- 平台面 GSP（Graph Store Protocol）**只读返回 405、写入返回 403 `E_GSP_GOVERNANCE_REQUIRED`**；
  后端 Oxigraph 仅容器内网访问，调试需 `docker compose exec platform ...`。
- 外部 embedding（如火山方舟）为实验性适配器，默认不装配；默认仅本机 BGE-M3。

## 8. 迁移与固化（bundle）

bundle 是跨环境迁移用的只读包（清单 + 数据文件 + 校验和）。**本体在 Oxigraph，不写入关系库**：
`graph/tbox.ttl` 是已发布的 Turtle 源，导入时走 `import_document -> publish` 治理链。2026-11-06 演练
实测：默认导出 **110 MB / 13 个文件**（不含附件原文）；`--include-blobs` 导出 **772.6 MB / 3206 个文件**
（含 3191 个 committed blob）。源栈与恢复栈的比对见 `_design/28-迁移恢复演练.md`。

### 8.1 导出（只读，不写生产库）

```powershell
docker compose exec -T platform `
  python -m platform_core.cli export-bundle --config /data/platform.yaml `
  --out /data/freeze --tag <tag>
# 默认不含附件原文；--include-blobs 会把全部 committed blob 字节（fs CAS + PG
# bytea 两层）打进 blobs/<aa>/<sha256>，并写 meta/blobs.jsonl 清单。
# import-bundle 会写回 CAS 并逐个校验 sha256/大小（见 8.6）
```

产物落在宿主 `D:\agentABC\data\freeze/<tag>/`（`data/` 已在 `.gitignore` 中）。

### 8.2 目录结构

```
<tag>/
  MANIFEST.json                  # bundleVersion=1 / schemaVersion=当前 20 / tag / totals / files[]
  graph/tbox.ttl                 # T-Box（owl:imports 已内联展开，含条款/术语个体）
  graph/abox.ttl                 # A-Box（当前为空）
  graph/shapes.ttl               # 已部署的 SHACL shapes
  ledger/fact_events.jsonl       # 事实事件账本（含 createdAt）
  ledger/verify.json             # 哈希链校验结果
  meta/documents.jsonl           # 文档元数据
  meta/chunks.jsonl              # 分块
  meta/document_pages.jsonl      # 逐页正文（2026-11-06 新增）
  meta/ontology_import.jsonl     # 本体导入历史
  meta/metric_definitions.jsonl  # 指标口径注册表（2026-11-06 新增）
  meta/metric_observations.jsonl # 指标观测（时间序列，2026-11-06 新增）
  meta/metric_entity_facts.jsonl # ins_payment_record + loan_installment_plan（2026-11-06 新增）
  meta/blobs.jsonl               # blob 清单（hash/size/mime/tier/refs，仅 --include-blobs）
  vectors/embeddings.npz         # chunk 向量（BGE-M3）
  vectors/README
  blobs/<aa>/<sha256>            # 原文 CAS，仅 --include-blobs 时存在（import 会写回）
```

**包含关系**：本体 ✔ / 事实 ✔ / 术语 ✔（T-Box 内 `terms#TermEntry` 个体，`source.tbox.termEntries`
记数）/ 指标定义 ✔ / 观测与实体事实 ✔ / 文档元数据、分块、逐页正文、向量 ✔ / **附件原文** 默认 ✘、
`--include-blobs` ✔（fs 与 PG bytea 两层都导出，导入写回 fs CAS）。

### 8.3 导入

默认恢复到一次性测试库，**绝不写 `platform`**：

```powershell
docker compose exec -T platform `
  python -m platform_core.cli import-bundle --config /data/platform.yaml `
  --bundle /data/freeze/<tag> --database platform_restore_test --replace
```

迁移/容灾到一套**全新启动的栈**时，显式允许就地恢复：

```powershell
docker compose exec -T platform `
  python -m platform_core.cli import-bundle --config /data/platform.yaml `
  --bundle /data/freeze/<tag> --database platform --into-empty-platform
```

- 目标库名等于生产库名且未加 `--into-empty-platform` → `E_BUNDLE_PROD_TARGET`
- 加了 `--into-empty-platform` 但目标已有 `document`/`fact_event`/`metric_observation` 任一非空
  → `E_BUNDLE_TARGET_NOT_EMPTY`（防止误写生产）；刚启动、只有 bootstrap T-Box 的栈算空
- 库已存在需 `--replace`（仅限非生产库）；失败保留现场加 `--keep-db-on-failure`
- 导入前先 `verify_bundle`：清单、每个文件的 sha256/大小/行数、NPZ 维度、账本哈希链、
  指标注册表内容哈希与术语计数；blob 清单还会逐项核对“文件大小 = 清单大小、文件名 = sha256”
- **附件原文**：bundle 带 `blobs/` 时，先把所有 payload 校验完再写 CAS（`blobs/<aa>/<sha256>`，
  tmp→fsync→同卷 rename），已存在则重新校验后跳过；任一 sha256/大小不符即整批失败并回滚本次
  新写入的文件。恢复后 `platform.blob` 统一为 `tier=fs`，`blob_ref` 一并恢复
- `--dry-run` 只统计 blob：`total/bytes/toWrite/existing/missing/conflicts`，不落盘、不建库
- CLI 打印 `checks[]`，任一项 `ok=false` 退出码非 0

### 8.4 核对表（2026-11-06 生产栈 → drill 栈实测，含原文）

| 项 | 源 | 目标 | 结果 |
| --- | --- | --- | --- |
| T-Box triples | 2961 | 2961 | 等 |
| 术语 `terms#TermEntry` | 18 | 18 | 等 |
| `metric_definition` | 79（hash 一致） | 79 | 等 |
| `metric_observation` | 0 | 0 | 等 |
| `ins_payment_record` / `loan_installment_plan` | 0 / 0 | 0 / 0 | 等 |
| `document` | 2092 | 2092 | 等 |
| `document_chunk` | 14244 | 14244 | 等 |
| `chunk_embedding` | 14215 | 14215 | 等 |
| `document_page` | 6245 | 6245 | 等 |
| `fact_event` | 6675 | 6675 | 等 |
| committed blob（不含 ontology 源 TTL） | 2104 / 693,883,503 B | 2104 / 693,883,503 B | 等 |
| 附件原文回读 `/documents/{id}/source` | 3 个文档 200 | 3 个文档 200，字节 sha256 一致 | 等（S2 smoke 17/17） |
| 账本导出字节 | sha256 一致 | 一致 | 等（`created_at` 已保真） |

### 8.5 硬约束

- **`schemaVersion` 必须与代码完全匹配**（`manifest.schemaVersion == SUPPORTED_SCHEMA_VERSION`，
  当前 20）；不一致直接 `E_BUNDLE_SCHEMA_MISMATCH`，不做隐式升级/降级。
- **默认仍不含附件原文**（`totals.blobs.included=false`）；需要完整恢复时显式加 `--include-blobs`。
  导出会读 fs CAS 与 PG `platform.blob_bytea` 两层；导入写回 fs CAS 并恢复 `blob/blob_ref`，
  逐字节校验通过才算成功（见 8.6）。
- **恢复后写序列自动校正**：replay 会把 `fact_event` 的 bigserial 设到 `MAX(event_id)` 之后，
  否则新事实写入会撞 `fact_event_pkey`（演练中 `smoke-s8/s12` 曾因此失败）。

### 8.6 bundle 含原文（--include-blobs）

**语义**

- 导出范围是 `platform.blob` 里全部 `state='committed'` 的行，不只是文档引用的那些；
  每个 blob 的字节从原 tier 读取（`fs` 读 CAS 文件，`pg` 读 `blob_bytea.content`），
  统一写到 `blobs/<sha前两位>/<sha>`，并生成 `meta/blobs.jsonl`（hash/size/mime/tier/refs）。
- 导入先把 `meta/blobs.jsonl` 与文件清单交叉校验（文件名=sha256、大小=清单），再写 CAS：
  tmp → fsync → 同卷 rename；目标已存在则重新校验后跳过，不重写。
  任一 sha256/大小不符 → `E_BUNDLE_BLOBS`，整批失败并回滚本次新写入的文件，不留半套。
  成功后 `platform.blob` 统一 `tier='fs'`、`path='blobs/<aa>/<sha>'`，`blob_ref` 一并恢复。
- `--dry-run` 只统计：`total / bytes / toWrite / existing / missing / conflicts`，不落盘、不建库。
- 幂等：同一 bundle 第二次导入 `written=0`、`existing=全部`，文件数与总字节不变。

**体积 / 耗时 / 磁盘（2026-11-06 实测）**

| 项 | 实测 |
| --- | --- |
| 默认 bundle | 110 MB / 13 个文件（无原文） |
| 含原文 bundle | **772.6 MB / 3206 个文件**，blob 3191 个 / 697,362,787 B（pg 3174 + fs 17） |
| 导出 | 约 100 s（读 700 MB 两层字节 + 逐文件 sha256） |
| 导入 | 约 130 s（verify ~30 s + 700 MB 落盘 + 逐文件校验） |
| 目标磁盘 | 至少预留 bundle + CAS 两份 ≈ 1.6 GB；导入后 CAS 约 697 MB |
| 对照结果 | `drill-migrate.ps1` 11/11 等；3 个文档 `/source` 200 且字节 sha256 一致；S2 smoke 17/17 |

> 导入时本体导入会重新生成当前版本的源 TTL（规范化 N-Triples），目标会多 1 个约 207 KB 的
> `ontology/sources/*` blob；blob 总数对比时排除该来源，其余 2104 个 committed blob
> （693,883,503 B）逐项相等。

## 9. 并行双栈（compose 参数化）

并行瓶颈不是 git，而是共用一套 compose 栈、一个重型锁和 12 核的 Docker VM 上限。
`docker-compose.yml` 已把项目名、宿主端口、容器名和数据根改为 env 驱动；**默认值等价于
原来的单栈**（`docker compose config --hash` 逐服务哈希不变）。两套栈用不同项目名、
不同数据根、不同宿主端口即可同时存活。

### 9.1 参数与默认值

| 项 | 变量 | 默认（=历史行为） |
| --- | --- | --- |
| 项目名 | `COMPOSE_PROJECT_NAME` / `-p` | `agent-platform` |
| 容器名 | 由 `COMPOSE_PROJECT_NAME` 派生 | `agent-platform-{postgres,oxigraph,api,...}` |
| 数据根 | `PLATFORM_DATA_ROOT` | `D:/agentABC/data` |
| api | `PLATFORM_PORT` | 8080 |
| postgres | `POSTGRES_PORT` | 5432 |
| oxigraph | `OXIGRAPH_PORT` | **默认不映射**（无鉴权，防绕过 GSP）；仅 `docker-compose.oxigraph-host.yml` 显式启用 |
| reasoner | `REASONER_PORT` | 7879 |
| embedding | `EMBEDDING_PORT` | 8081 |
| fuseki | `FUSEKI_PORT` | 3030 |
| 重型锁 | `-Stack <name>` | `.lock/heavy.lock`；其他栈为 `.lock/<name>.heavy.lock` |

命名卷（`pgdata`、`oxigraph-data`）由 compose 按项目名自动加前缀，两套栈不会共用；
`/data` 是 bind mount，必须用 `PLATFORM_DATA_ROOT` 指到不同目录，两套栈才不共用库/文件。
同一栈内重型锁仍互斥；**跨栈不互斥是刻意的**，靠下面的资源预算约束。

### 9.2 起一套短时验证栈（drill）

默认栈在跑时，二套栈必须把 **api / pg / oxigraph / reasoner** 全部换成非默认端口；
`reasoner` 不能省（见下方说明）。

```powershell
# 第二套：api 8083 / pg 5434 / reasoner 7884 / oxigraph 7882，独立卷与独立数据根
powershell -ExecutionPolicy Bypass -File scripts/stack.ps1 up -Name platform-drill `
  -ApiPort 8083 -PgPort 5434 -ReasonerPort 7884 -OxigraphPort 7882 `
  -DataRoot D:/agentABC/data-drill `
  -Services postgres,oxigraph,platform,reasoner

powershell -ExecutionPolicy Bypass -File scripts/stack.ps1 status -Name platform-drill -ApiPort 8083
curl.exe -s http://127.0.0.1:8083/readyz
```

为什么必须带 `reasoner`：启动时 `ontology.init_source` 走 `materialize`，平台要连 reasoner 完成
首次 T-Box 物化；只起三容器时 `serve` 以 `E_ONTOLOGY_INIT_FAILED` 退出 78，容器反复重启，
`/readyz` 永远不会 200（2026-11-06 实测，等待 180s 后失败）。RUN.md 旧版本"只起三个核心容器"的说法
是错的。

- 只起 `-Services postgres,oxigraph,platform,reasoner` 可让端口预检跳过 embedding/fuseki；
  若要一起起 embedding，还要 `-EmbeddingPort 8084` 并接受约 6g 常驻内存。
- `-OxigraphPort` 不给时 Oxigraph 不映射宿主（默认行为）；给 0 以外的值会自动追加
  `docker-compose.oxigraph-host.yml`。
- 首次 `up` 会 `docker compose up -d`：本地没有镜像时会现场构建 `platform` / `reasoner` /
  `rdfs`。全新机器请先单独 `docker compose build platform reasoner`（reasoner 需联网下载 jar）。
- `stack.ps1 up` 会先做端口预检：端口被别人占用时直接
  `E_STACK_PORT_IN_USE: ... used by pid=... (not project 'platform-drill')`，不会盲起容器；
  `/readyz` 探测带 `-WaitSeconds`（默认 180s）/`-ProbeSeconds`（默认 5s）超时。
- 新数据根的 `platform.yaml` 口令仍是 `CHANGE_ME` 时，按 §2 改成与 `.env` 的
  `POSTGRES_PASSWORD` 一致，否则 `smoke-s3` 会认证失败。

### 9.3 资源预算（硬约束）

- Docker VM 实测上限 **12 CPU / 11.68 GiB**，16 CPU 会被 Docker Desktop 拒绝。
- B 栈只用于**短时验证**，不常驻；最小可启动集合是 `postgres,oxigraph,platform,reasoner`，
  不是三容器。
- **不得两套同时跑重型作业**（批量导入、全量索引、acceptance、reasoner 物化）；同一时间只允许
  一套做重活，另一套保持只读/空闲。
- B 栈不要起 embedding（闲置也占约 6g 限额），否则内存容易超预算；reasoner 空闲实测仅约 30 MB，
  但与默认栈 reasoner 并行做物化时会翻倍。

### 9.4 拆除与残渣核对

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stack.ps1 down -Name platform-drill `
  -ApiPort 8083 -PgPort 5434 -ReasonerPort 7884 -OxigraphPort 7882 `
  -DataRoot D:/agentABC/data-drill -RemoveDataRoot
```

`down -v` 删除 B 的命名卷，`-RemoveDataRoot` 删除 `D:/agentABC/data-drill`；脚本末尾打印
`residual containers/volumes for 'platform-drill'`，两者都应为 `none`。

### 9.5 代码更新与一键迁移演练

`stack.ps1 up` 发现 api 端口已被本栈发布时会直接跳过 compose up，**`git pull` 后代码不会自动更新**。
升级二套栈：

```powershell
git pull
docker compose build platform
$env:COMPOSE_PROJECT_NAME='platform-drill'; $env:PLATFORM_PORT='8083'
$env:POSTGRES_PORT='5434'; $env:REASONER_PORT='7884'; $env:OXIGRAPH_PORT='7882'
$env:PLATFORM_DATA_ROOT='D:/agentABC/data-drill'
docker compose -p platform-drill -f docker-compose.yml -f docker-compose.oxigraph-host.yml `
  up -d --force-recreate --no-deps platform
```

（必须带全部端口/数据根 env；少了就会回落到 8080 与默认栈冲突。）

一键演练（导出 → 起新栈 → 导入 → 数字比对，默认只碰 drill 栈）：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/drill-migrate.ps1 -DryRun   # 先看会执行什么
powershell -ExecutionPolicy Bypass -File scripts/drill-migrate.ps1            # 实跑
powershell -ExecutionPolicy Bypass -File scripts/drill-migrate.ps1 -ResetTarget  # 目标已有数据时先重建
```

脚本默认参数：source=`agent-platform`（8080，只读导出）、target=`platform-drill`
（8083/5434/7884/7882，数据根 `D:/agentABC/data-drill`）。任何一项计数不等都会打印 `MISMATCH` 并以
非 0 退出；它不会 `down` 默认栈，也不会写默认库。

## 10. 生产/验收栈的非仓库内配置清单

仓库只提供结构与默认值；下列配置**必须由部署环境提供**，缺一项就会以可观察的方式失败。换机器/
新栈按此清单逐项核对后再启动。

| 配置项 | 位置（均不在仓库内） | 必填内容 | 缺失/错误的可观察后果 |
| --- | --- | --- | --- |
| `platform.yaml` | `${PLATFORM_DATA_ROOT}/platform.yaml`（api 以 `--config` 读取，默认挂载 `D:/agentABC/data`） | `database.url` 与栈的 `POSTGRES_PASSWORD` 一致；`paths` 指向数据根；`reasoning.abox_graphs` **至少同时含** `urn:platform:graph:abox:main` 与 `urn:platform:graph:abox:synthetic` | 缺文件 → api 启动失败；口令不一致 → `password authentication failed`；`abox_graphs` 只剩 `abox:main`（与仓库 `platform.example.yaml:121-122` 一样）→ `/reasoning/status.aboxGraphs` 只报 main 且 `abox:main` 计数 0，`emptyAbox=true`、`coverage.instances.graphs` 与状态集合不一致，P01 的「状态与看板不一致」原样重现，B04 实例数归零 |
| `platform/.env` | `platform/.env`（gitignored，compose `env_file` 注入） | `POSTGRES_PASSWORD`、`ARK_API_KEY`、`PLATFORM_SMOKE_TOKEN` | 见下三行 |
| `PLATFORM_SMOKE_TOKEN` | `.env` 或本机环境变量，经 compose 传 `PLATFORM_SMOKE_TOKEN` 给 api | 单值内部 token；轮换后 `docker compose up -d --force-recreate api` | 未配置 → fail-closed：`purpose=smoke` 发布一律 409 `E_TERM_GATE_BLOCKED`（`tokenStatus="unconfigured"`），smoke 自检探针全部被拒——这是安全默认，不是功能回归 |
| `ARK_API_KEY` | 同上 | Ark/豆包 key | 抽取与 LLM 问答步骤失败或降级，只读本体/指标接口不受影响 |
| 镜像 tag | 部署侧 override（见 10.2） | 指向本次发布镜像（如 `agent-platform:merged-42`） | 不带 override → 回落 `docker-compose.yml` 的默认 `agent-platform:0.1-s5`；该镜像 schema 上限低于当前迁移链（`SUPPORTED_SCHEMA_VERSION = 43`），api 就绪检查报 `E_DB_MIGRATION_MISMATCH` |
| BGE-M3 权重 | `${PLATFORM_DATA_ROOT}/models/bge-m3` | 完整模型目录 | `learn`/`embedding` profile 起不来，检索降级为 `lexicalOnly` |
| T-Box/SHACL 种子 | `${PLATFORM_DATA_ROOT}/seed/`（自 `platform/seed/` 复制） | `bootstrap.ttl`、`shacl.ttl` 等 | 首次引导失败：`E_ONTOLOGY_TBOX_MISSING`（退出码 69），`/tbox/current` 为空 |
| `robot/robot.jar` | `${PLATFORM_DATA_ROOT}/robot/robot.jar`（构建期也允许联网下载） | HermiT 推理所需 | reasoner 无法物化，A-Box 推理保持 deferred、`/reasoning/status` 推理计数不增长 |

> `datagen.allow_official_schema: true` 仅验收栈需要（允许 synthetic 写入 `platform.*` 事实表）。
> 生产栈保持 `false`；否则 `run` 会以 `E_DATAGEN_TARGET_FORBIDDEN` 拒绝写官方 schema。这是数据
> 安全开关，不是部署便利项。
>
> **权威栈配置基线**：仓库内默认值（`platform.example.yaml`、`config.py`）**仅用于开发和单测**。
> AS-8080 权威栈必须显式加载脱敏基线 `platform/config/authoritative-8080.yaml`；按默认值起栈
> 会得到“另一个系统”：`/browse/canvas/*` **503 `E_CANVAS_DISABLED`**、B04 归零、
> `abox:synthetic` 缺失、合成数据被拒。启动后必须跑
> `powershell -File scripts/stack-verify.ps1`，PASS 之前的对外数字不得引用。

### 10.1 新栈启动前最小核对

1. `docker compose config` 里 `platform.image` 与预期 tag 一致（不是默认 `0.1-s5`）；
2. `PLATFORM_SMOKE_TOKEN` 非空，且 `purpose=smoke` 探针返回 200 而非 409；
3. `/reasoning/status` 的 `aboxGraphs` 与 `/health/dashboard` 的 `coverage.instances.graphs` 是同一非空集合
   （代码不强制相等：看板在 `abox:synthetic` 图存在时会自动追加它，即使它没写进 `reasoning.abox_graphs`；
   不相等按部署配置错误处理）；
4. `GET /tbox/current` 非空、`/readyz` 返回 200。

### 10.2 镜像 tag 与 override：属部署环境，不入仓

判断依据：

- 现有 8080/8082 override 的**全部内容只有一行 `image:`**（`merged-42` / `merged-r02`）。提交进仓库
  等于把某一时点的 tag 固化，下一次重建即过期，并会诱导新栈误用旧 tag（本轮已发生 tag 与库版本
  错位，8082 库在 42 而镜像只支持 40）。
- 这些 override 位于各工作树的 `platform/` 下（如
  `wt/metrics-report/platform/docker-compose.8080-override.yml`），是单次部署的临时产物，路径不可移植。
- 仓库能承诺的是「构建 + 运行契约」，不是某次部署的快照：`docker-compose.yml`（结构与默认镜像）
  + `docker-compose.oxigraph-host.yml` / `docker-compose.acceptance.yml`（网络与端口形态）+ 本节
  清单已足以重建。tag → commit → image id 的台账由部署侧维护。

复现当前形态（部署侧自行创建 override，内容两行）：

```yaml
services:
  platform:
    image: agent-platform:<tag>
```

```powershell
docker compose -f platform/docker-compose.yml -f <override> up -d --no-deps platform
docker inspect agent-platform-api --format '{{.Config.Image}} {{.Image}}'   # tag 与 image id 双核对
```

不改 `SUPPORTED_SCHEMA_VERSION`：本清单只约束部署，schema 版本号等口径基准表定稿后再统一调整。

## 11. 离线全量推理（A-Box materialize）

全量推理是**离线按需**能力，不是发布副作用。本节是唯一入口；必须在确认无并行重活后执行。

### 11.1 为什么在线不自动触发

- 开关：`reasoning.materialize_online` 默认 `false`（`platform/src/platform_core/config.py`）。发布/回滚钩子
  `ReasoningService.publish_materializer()` 只返回 deferral，不启动推理：
  `{"jobId": null, "inferred": 0, "skipped": true, "deferred": "offline_only",
   "reason": "reasoning.materialize_online=false"}`。发布证据 `gates.materialization` 原样记录该对象
  （`adapters/ontology_pg.py` 的 publish 钩子）；回滚钩子里的物化失败只记 warning，不改变已提交的
  T-Box 指针。
- 代价：304,919 行 A-Box 全量实测 **212.6 s**，峰值 API **2.14 GiB** + reasoner **1.43 GiB** +
  oxigraph **0.93 GiB** ≈ **4.5 GiB**，存储 **+215.9 MiB**。Docker VM 只有 11.68 GiB，embedding 还占
  6g 限额——把发布成功率绑在一次 3 分半、4.5 GiB 的推理上不可接受。
- 事务顺序：发布事务先提交，再调 materializer；普通报错会走 `_restore_after_failed_publish` 回补，
  但进程被 OOM kill 时回补来不及执行，结果是"版本已发布、推断指针仍是旧的"。

**误开启/窗口内内存打爆的表现**：`docker inspect agent-platform-api --format '{{.State.OOMKilled}}'`
为 `true`，`docker compose ps` 显示重启或 ExitCode 137；客户端拿到连接重置/502 而不是 JSON；
reasoner 也可能 137，`/reasoning/status.available=false`；`platform.reasoning_job` 停在
`state='running'`（进程来不及写 failed）；`docker stats` 里 API RSS 冲到 2 GiB+，VM/宿主 swap 增长
（本轮实测已动用 2.7 GiB swap）。

### 11.2 跑之前

1. **模式**：`reasoning.mode=materialize`。`rdfs` 只做 RDFS 闭包、`validate` 只跑 SHACL 不写图、
   `off` 直接报 `E_REASONING_DISABLED`；`profile=EL`、`engine=robot`。
2. **图集**：`reasoning.abox_graphs` 必须同时含 `urn:platform:graph:abox:main` 与
   `urn:platform:graph:abox:synthetic`（与 `/reasoning/status.aboxGraphs` 一致）。
3. **输入规模**：T-Box ~0.55 MB + A-Box 41,755,655 B（304,919 行）= **40.34 MiB**，是
   `max_source_bytes`（默认 50 MiB）的 80.7%。再涨约 10 MiB 会在开跑前报
   `E_REASONING_INPUT_TOO_LARGE`；不要为提高上限直接改配置。
4. **内存**：不含 embedding 时至少留 **5 GiB** 可用；embedding 常驻时 11.68 GiB 的 VM 必然用 swap，
   先用 `docker stats --no-stream` 看实际余量。API 容器没有 `mem_limit`，打爆的是整台 VM；
   reasoner 是 `mem_limit=4g` + `JAVA_OPTS=-Xmx2g`，不要调低。
5. **互斥**：同一 target 同时只允许一个 materialize，重入报 `E_REASONING_BUSY`（retryable）；
   同时不得跑批量索引、验收或另一套栈的物化（见 §5 重型锁、§9.3）。
6. **时间**：按 10 分钟窗口预留；reasoner 单次调用上限 300 s（`timeout_ms=300000`），超时是
   `E_REASONER_TIMEOUT` 失败，不会无限等待。

### 11.3 触发命令（原文）

```powershell
curl.exe -s -X POST http://127.0.0.1:8080/reasoning/materialize
```

- 同步请求，跑完才返回；实测端到端 **212.6 s**（内部 `ms=210904`；RDFS 43.9 s / ELK 73.1 s /
  SHACL 64.1 s）。
- **没有 CLI 子命令**：唯一入口是这个 POST（`api.py` 的 `/reasoning/materialize`），无鉴权，
  空 body 合法；等价写法 `-H "Content-Type: application/json" -d '{}'`。
- 强制重跑（输入未变时默认短路成 `skipped=true, inferred=0`）：

```powershell
curl.exe -s -X POST http://127.0.0.1:8080/reasoning/materialize `
  -H "Content-Type: application/json" -d '{"force":true}'
```

- 只跑指定图（必须是 `urn:platform:` 前缀的非空列表，否则 `E_REASONING_ABOX_GRAPHS`；
  不传则用配置里的全部图）：

```powershell
curl.exe -s -X POST http://127.0.0.1:8080/reasoning/materialize `
  -H "Content-Type: application/json" `
  -d '{"force":true,"aboxGraphs":["urn:platform:graph:abox:synthetic"]}'
```

### 11.4 跑完怎么校验

```powershell
curl.exe -s http://127.0.0.1:8080/reasoning/status
```

- `lastJob.state` = `succeeded`；失败则是 `failed` + `errorCode`/`errorMessage`。
- `lastJob.inferred` = 本轮推断条数；`inferredTriples`（= `pointer.inferred`）应从 **1,171**
  变为 **322,021**（本轮实测：RDFS 173,163 + OWL 148,858，重叠 0）。A-Box 变化后以本次
  `lastJob.inferred` 为准，不要记死 322,021。
- `materializeOnline`：直接给出现行策略（`false` = 发布/回滚只登记 `deferred=offline_only`，
  `true` = 发布/回滚即触发推理）；确认策略不用再从发布证据的 `deferred` 反推。
- `pointer.targetGraph` = `urn:platform:inferred:<当前 versionId>`；`pointer.ontologyVersion` 与
  `/tbox/current` 一致；`pointer.updatedAt` 是本次时间。
- 立刻复跑应返回 `skipped=true, inferred=0`（幂等）；要重算必须 `force=true`。
- `/health/dashboard`：`inferenceFailures.count` 不增加；`coverage.instances.graphs` 与 status 的
  `aboxGraphs` 同集合。注意 `coverage.instances.total` 是"有 `rdf:type` 的 DISTINCT 主体数"，
  不是三元组数，不能拿它和 322,021 对。
- 发布门禁侧（可选）：一致性证据应显示 `emptyAbox=false`，`aboxGraphTriples` =
  `{"urn:platform:graph:abox:main": 0, "urn:platform:graph:abox:synthetic": 304919}`、`aboxTriples=304919`。

### 11.5 失败与回退

- **源图不动**：推断只写 `urn:platform:inferred:<versionId>`，从不覆盖 `abox:*` / T-Box。预检、
  SHACL 或一致性失败时目标图完全未动；写入失败会尝试清空半写的目标图（再失败记
  `reasoning.cleanup_failed`）。
- **指针只在写图成功后更新**：若出现"图已换、指针没换"，下一次重跑会因
  "`count_graph(target)` ≠ `pointer.inferred`" 自动重算（`replace_graph` 是 DROP+INSERT，可重入）。
- **推荐回退**：修好原因后重跑同一版本，不需要回滚源数据；要回到旧推断，先完成 T-Box 回滚，
  再 POST 一次 materialize（旧版本推断图仍在，指针会指回旧目标图）。不要手工删图或改库。
- **OOM kill**：等容器恢复、`/readyz` 200 后直接重跑；advisory lock 随连接释放，卡住的
  `state='running'` 记录不影响重跑。
- **存储**：推断图按 `versionId` 累积、不自动回收（每轮实测 +215.9 MiB），按版本数预留磁盘；
  清理不在本流程内。
