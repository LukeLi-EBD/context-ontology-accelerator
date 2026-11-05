# 运行手册（platform）

面向"另一台机器 clone 后能跑起来"。`platform/` 是独立项目：所有命令都在
**`coa/platform`** 目录下执行，无需 `-f` 指定 compose 文件。

三行起（已装 Docker Desktop，且 `D:\agentABC\data` 已就位）：

```powershell
git clone <repo> coa && cd coa\platform
Copy-Item .env.example .env        # 填 POSTGRES_PASSWORD、ARK_API_KEY
docker compose up -d --wait        # 首次构建 reasoner 需联网下载 robot.jar（见 §2）
```

## 1. 前置条件

- Docker Desktop（WSL2 后端）。实测 VM 上限：**12 CPU / 11.68 GiB**；16 CPU 会被 Docker Desktop 直接拒绝。
- 宿主建议 16 GB 内存、D 盘可用 ≥ 20 GB（`/readyz` 会因 `min_free_pct=10` 失败）。
- 端口占用（全部绑 `127.0.0.1`）：
  - `8080` 平台 API/UI，`8081` embedding（TEI），`5432` PostgreSQL，`7879` reasoner
  - `7878` Oxigraph **不映射宿主**（无鉴权，暴露即可绕过 GSP 治理）
- 模型与镜像：`agent-platform:0.1-s5`、`agent-reasoner:0.1-s5`、`agent-rdfs:0.1-s5`、pgvector、oxigraph、TEI 均由本地构建或拉取。

## 2. 目录准备（数据不在 git 里）

运行时数据统一放在 **`D:\agentABC\data`**（compose 以绝对路径 bind 到容器 `/data`），
仓库里只有占位 `platform/data/README.md`。首次在新机器部署：

```powershell
Copy-Item .env.example .env                            # 放 coa/platform/.env（gitignored）
New-Item -ItemType Directory -Force D:\agentABC\data
Copy-Item platform.example.yaml D:\agentABC\data\platform.yaml   # 填 database.url 口令（与 .env 一致）
New-Item -ItemType Directory -Force D:\agentABC\data\blobs,D:\agentABC\data\tmp,D:\agentABC\data\shapes | Out-Null
```

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

迁移在平台启动时自动执行，脚本位于 `src/platform_core/sql/V1__s0.sql … V19__metric_observation.sql`，
**当前最新为 V19**（历史任务描述里的 V16/V17 已过时）。

期望返回：

```powershell
curl.exe -s http://127.0.0.1:8080/readyz
# {"ok":true,"checks":{"database":{"status":"ok"},"graph":{"status":"ok"},
#  "storage":{"status":"ok","disk_free_pct":...},"embedding":{...},"reasoner":{...}}}
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

`acceptance.ps1` 覆盖 `docker compose config`、各 smoke-sN、演示库纯净性等；单项失败不中断，最后汇总。
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

bundle 是跨环境迁移用的只读包（清单 + 数据文件 + 校验和）。**本体不入库**（`_freeze/v1-20261105` 约 79 MB，
含 `vectors/embeddings.npz`）；仓库只保留清单副本 `platform/freeze-manifests/v1-20261105.json`。

### 8.1 导出（只读，不写生产库）

```powershell
docker compose exec -T platform `
  python -m platform_core.cli export-bundle --config /data/platform.yaml `
  --out /data/freeze --tag v1-20261105
# 默认只导元数据；连 CAS 原文一起打包加 --include-blobs（体积显著增大）
```

产物落在宿主 `D:\agentABC\data\freeze/v1-20261105/`（`data/` 已在 `.gitignore` 中）。

### 8.2 目录结构

```
v1-20261105/
  MANIFEST.json                # bundleVersion=1 / schemaVersion=17 / tag / totals / files[]
  graph/tbox.ttl               # T-Box（owl:imports 已内联展开）
  graph/abox.ttl               # A-Box（本 bundle 为空）
  graph/shapes.ttl             # 已部署的 SHACL shapes
  ledger/fact_events.jsonl     # 事实事件账本
  ledger/verify.json           # 哈希链校验结果
  meta/documents.jsonl         # 1122 条
  meta/chunks.jsonl            # 13274 条
  meta/ontology_import.jsonl   # 15 条
  vectors/embeddings.npz       # 11905 × 1024（BGE-M3）
  vectors/README
  blobs/<aa>/<sha256>          # 仅 --include-blobs 时存在
```

### 8.3 导入（恢复到一次性测试库，绝不写 `platform`）

```powershell
docker compose exec -T platform `
  python -m platform_core.cli import-bundle --config /data/platform.yaml `
  --bundle /data/freeze/v1-20261105 --database platform_restore_test --replace
```

- 目标库名等于生产库名会被拒（`E_BUNDLE_PROD_TARGET`）；库已存在需 `--replace`
- 导入前先 `verify_bundle`：清单、每个文件的 sha256/大小/行数、NPZ 维度、账本哈希链
- 失败保留现场加 `--keep-db-on-failure`；CLI 打印 `checks[]`，任一项 `ok=false` 退出码非 0

### 8.4 五项核对表

| 项 | 期望（本 bundle） |
| --- | --- |
| documents | 与 `totals.documents` 相等（1122） |
| chunks | 与 `totals.chunks` 相等（13274） |
| vectors | 行数 = `totals.embeddings`（11905），chunk_id 集合一致；抽 20 条余弦 ≥ 0.999 |
| triples | T-Box + restore A-Box 合计 = `totals.triples`（2676） |
| facts | `fact_event` = `totals.factEvents`（3280），`fact_assertion` = 0 |

### 8.5 两条硬约束

- **`schemaVersion` 必须与代码完全匹配**（`manifest.schemaVersion == SUPPORTED_SCHEMA_VERSION`，当前 19）；
  不一致直接 `E_BUNDLE_SCHEMA_MISMATCH`，不做隐式升级/降级 —— 先把库迁到对应版本再导。
- **blobs 不在 bundle 内**（`totals.blobs.included=false`）。要完整还原原文下载/预览，需单独同步
  `data/blobs/`（CAS 目录）；只缺 blobs 时元数据仍可恢复，但 `/documents/{id}/source` 会 404。

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

### 9.2 起一套短时验证栈

```powershell
# 第二套：api 8081 / pg 5433 / oxigraph 7879，独立卷与独立数据根
powershell -ExecutionPolicy Bypass -File scripts/stack.ps1 up -Name platform-b `
  -ApiPort 8081 -PgPort 5433 -OxigraphPort 7879 `
  -DataRoot D:/agentABC/data-b `
  -Services postgres,oxigraph,platform

powershell -ExecutionPolicy Bypass -File scripts/stack.ps1 status -Name platform-b -ApiPort 8081
curl.exe -s http://127.0.0.1:8081/readyz
```

注意：默认栈的 embedding 占 8081、reasoner 占 7879。若 B 必须用这两个端口，先临时
`docker compose stop embedding reasoner`（它们都是 learn-only，不影响 `/readyz`），
或者把 B 改成 `-ApiPort 8082 -OxigraphPort 7880`。

`stack.ps1 up` 会先做端口预检：端口被别人占用时直接
`E_STACK_PORT_IN_USE: ... used by pid=... (not project 'platform-b')`，不会盲起容器；
`/readyz` 探测带 `-WaitSeconds`（默认 180s）/`-ProbeSeconds`（默认 5s）超时。

### 9.3 资源预算（硬约束）

- Docker VM 实测上限 **12 CPU / 11.68 GiB**，16 CPU 会被 Docker Desktop 拒绝。
- B 栈只用于**短时验证**，不常驻；验证栈建议只起 `postgres,oxigraph,platform` 三个核心容器。
- **不得两套同时跑重型作业**（批量导入、全量索引、acceptance、reasoner 物化）；同一时间只允许
  一套做重活，另一套保持只读/空闲。
- B 栈不要挂 `learn` profile（embedding 常驻约 6g、reasoner 4g），否则内存直接超预算。

### 9.4 拆除与残渣核对

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stack.ps1 down -Name platform-b `
  -ApiPort 8081 -PgPort 5433 -OxigraphPort 7879 `
  -DataRoot D:/agentABC/data-b -RemoveDataRoot
```

`down -v` 删除 B 的命名卷，`-RemoveDataRoot` 删除 `D:/agentABC/data-b`；脚本末尾打印
`residual containers/volumes for 'platform-b'`，两者都应为 `none`。
