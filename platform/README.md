# 本体平台 · 上手指南

单机、单用户、learn 档（5 容器）的版本化本体平台：文档入库 → 检索 → 抽取候选 → 审批 → RDFS/OWL 物化 → Web UI。
本文件面向使用者，不解释内部实现；开发/设计文档在 `_design/`。

## 1. 5 分钟路径

### 前置条件

- Windows + Docker Desktop（含 Compose v2），默认 5 个端口空闲：`8080 5432 7878 8081 7879`。
- 本地已有 BGE-M3 权重：`D:\agentABC\data\models\bge-m3\`（12 个文件，约 2.3 GB，必须有 `pytorch_model.bin`）。
  首次拿不到可先跳过 embedding，系统会以词法检索降级运行（`degraded=true`）。
- 内存建议 ≥ 8 GB（TEI 加载模型约 2 GB）。

### 步骤

```powershell
cd D:\agentABC\coa\platform
powershell -ExecutionPolicy Bypass -File .\scripts\up.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\seed.ps1
```

1. `up.ps1`：检查 Docker 与 8080 占用 → `docker compose up -d` → 等 `/readyz` → 打印五容器状态与访问地址。
2. `seed.ps1`：发布示例本体（`coastal-sample 1.0.0`）→ 等待 BGE-M3 就绪 → 上传 2 份示例文档 → 索引 → 抽取 → 打印计数。
3. 打开 **http://127.0.0.1:8080/ui/**（`index.html` 也可以直接双击打开，会自动连 `127.0.0.1:8080`）。
4. 先看 **概览**：版本指针、5/5 服务、各图三元组数、文档/片段/候选计数。
5. 去 **审批队列**：通过 1 条候选 → 点「物化」；回概览看 `inferred` 计数增加。
6. 去 **检索与问答**：输入「青岛监测站位于哪里？」，看片段、引用与 `truncated`/`degraded` 提示。

**从零实测（2026-11-05，镜像已构建、模型已在本机）**：`up` 11.3 s + `seed` 124.1 s ≈ **2 分 15 秒**；
其中约 110–180 s 是 TEI 冷加载 2.3 GB 权重。首次在干净机器上还要拉镜像/构建（未计入）。

## 2. 常用命令

```powershell
# 起站 / 停止 / 清空数据（down -v 会删 PG 与 Oxigraph 卷，先备份）
powershell -ExecutionPolicy Bypass -File .\scripts\up.ps1
docker compose down
docker compose down -v

# 状态 / 日志
docker compose ps
docker compose logs --tail 40 platform
curl.exe -s http://127.0.0.1:8080/readyz

# 示例数据（可重复执行，幂等）
powershell -ExecutionPolicy Bypass -File .\scripts\seed.ps1

# 批量入库（同一目录再次执行即断点续跑；--dry-run 只报数）
# --batch-size 控制单次文件数，--max-seconds 控制单次墙钟预算（默认 180s，到点只停投递、在飞文件跑完）
docker compose exec -T platform platform import /data/<dir> --dry-run
docker compose exec -T platform platform import /data/<dir> --batch-size 5 --max-seconds 180
docker compose exec -T platform platform import /data/<dir> --retry-failed
docker compose exec -T platform platform imports --status failed

# embedding 分区重建（可中断续跑；全部补齐后自动切换指针；旧分区保留）
docker compose exec -T platform platform reindex --provider=local-bge --batch-size 32
docker compose exec -T platform platform reindex --provider=ark --batch-size 32
docker compose exec -T platform platform reindex --provider=ark --activate-only

# 验收
docker compose exec -T platform platform smoke
docker compose exec -T platform platform smoke-s8
docker compose exec -T platform platform smoke-s9
docker compose exec -T platform platform smoke-s10
docker compose exec -T platform platform smoke-s11
docker compose exec -T platform platform smoke-s12
docker compose exec -T platform platform smoke-s13
docker compose exec -T platform platform smoke-embed
powershell -ExecutionPolicy Bypass -File .\tests\acceptance.ps1

# 审计导出 / 离线校验 / 空库重放（NDJSON + summary.md + assertions.ndjson + export.json）
# events.ndjson 永远是到 cutoff_seq 的完整前缀链；--from/--to/--source 只过滤窗口视图
# facts-verify 输出 verified_prefix=true 才代表这是可自证的完整前缀
docker compose exec -T platform platform facts-export --out /data/tmp/audit-export
docker compose exec -T platform platform facts-export --out /data/tmp/audit-window --from "2026-11-05T06:00:00+08:00"
docker compose exec -T platform platform facts-verify --file /data/tmp/audit-export/events.ndjson
docker compose exec -T platform platform facts-replay --file /data/tmp/audit-export/events.ndjson --dry-run
docker compose exec -T platform platform facts-replay --file /data/tmp/audit-export/events.ndjson

# 配置自检（不连依赖）
docker compose exec -T platform platform check-config
docker compose exec -T platform platform probe

# 本体：导入 / 提案 / 审批 / 发布 / 回滚 / diff / 导出（S11 治理，S12 起无 proposal 也走隐式提案+三门禁）
docker compose exec -T platform platform ontology import --file /app/examples/ontology/sample.ttl --semver 1.0.1 --label demo
docker compose exec -T platform platform ontology propose --version <versionId> --summary "add CoastalStation" --against <currentVersionId>
docker compose exec -T platform platform ontology approve --proposal <proposalId>
docker compose exec -T platform platform ontology publish --version <versionId> --proposal <proposalId> [--acknowledge-breaking]
docker compose exec -T platform platform ontology rollback-to --version <oldVersionId> --reason "bad publish"
docker compose exec -T platform platform ontology diff --version <versionId> --against <otherVersionId>
docker compose exec -T platform platform ontology export --version <versionId> --format turtle --out /data/tmp/tbox.ttl
docker compose exec -T platform platform ontology events --version <versionId>
docker compose exec -T platform platform ontology verify
docker compose exec -T platform platform ontology status

# 文档：上传 / 索引 / 抽取 / 片段
curl.exe -F "file=@D:\path\doc.txt" http://127.0.0.1:8080/documents
curl.exe -X POST http://127.0.0.1:8080/documents/<documentId>/index
curl.exe -X POST http://127.0.0.1:8080/documents/<documentId>/extract
curl.exe -s http://127.0.0.1:8080/documents/<documentId>/chunks

# 检索 / 上下文
curl.exe -s "http://127.0.0.1:8080/search?q=%E9%9D%92%E5%B2%9B&limit=5"
curl.exe -s -X POST http://127.0.0.1:8080/context/resolve -H "Content-Type: application/json" -d "{\"query\":\"青岛监测站位于哪里\"}"

# 审批 / 物化
curl.exe -s "http://127.0.0.1:8080/candidates?state=pending"
curl.exe -X POST http://127.0.0.1:8080/candidates/<candidateId>/approve
curl.exe -X POST http://127.0.0.1:8080/reasoning/materialize
curl.exe -s http://127.0.0.1:8080/reasoning/status

# 备份（不要直接拷运行中的 RocksDB 目录）
New-Item -ItemType Directory -Force .\data\backups | Out-Null
docker compose exec -T postgres pg_dump -U platform -d platform --no-owner > .\data\backups\platform.sql
# S14H-16: oxigraph 不再映射宿主端口，备份走容器网络（platform 容器有 python）
docker compose exec -T platform python -c "import urllib.request as u; r=u.Request('http://oxigraph:7878/store', headers={'Accept':'application/n-quads'}); open('/data/backups/oxigraph.nq','wb').write(u.urlopen(r).read())"
```

## 3. 端口与目录

| 端口 | 服务 | 说明 |
|---|---|---|
| 8080 | platform | Web UI `/ui/`、REST API、`/docs`（OpenAPI） |
| 5432 | postgres | 仅绑定 `127.0.0.1`；元数据/片段/pgvector |
| 7878 | oxigraph | **不映射宿主端口**（仅容器网络 `oxigraph:7878`）；无鉴权，映射即等于绕过平台 GSP 治理 |
| 8081 | embedding | TEI，OpenAI 兼容 `/v1/embeddings`；冷启动约 2 分钟 |
| 7879 | reasoner | ROBOT/ELK + Jena `riot` 批处理 |

| 路径 | 内容 |
|---|---|
| `D:\agentABC\data\platform.yaml` | 运行配置（容器内 `/data/platform.yaml`） |
| `D:\agentABC\data\models\bge-m3\` | BGE-M3 权重（只读挂载到 TEI） |
| `D:\agentABC\data\ontology\bootstrap.ttl` | 启动引导本体（`init_semver=0.0.0`；用户发布更高 semver 后不会被覆盖） |
| `D:\agentABC\data\documents\` | 大对象 CAS（`storage.large_object_provider=fs`） |
| `D:\agentABC\data\shapes\` | SHACL 形状（`reasoning.shapes_dir`） |
| `D:\agentABC\data\backups\` | 备份落点 |
| `examples\` | 示例本体与文档（镜像内 `/app/examples`） |
| `web\` | 静态前端（镜像内 `/app/web`） |

## 4. 怎么换实现

所有配置都在 `D:\agentABC\data\platform.yaml`，也可用环境变量覆盖：
`PLATFORM__<SECTION>__<KEY>`（**双下划线**分隔），如 `PLATFORM__SEARCH__ENABLED=false`。
改完配置后必须重建 platform 容器：`docker compose up -d --force-recreate platform`（配置只在启动时读取）。

### 4.1 LLM（抽取用，可选）

当前只有 `openai-compatible` 一种协议；`llm.base_url`/`llm.model` 为空时自动退化为「仅规则抽取」（`degraded=llm:unconfigured(rules_only)`）。

| 目标 | 配置 |
|---|---|
| DeepSeek | `llm.base_url: https://api.deepseek.com/v1`；`llm.model: deepseek-chat`；`llm.api_key_env: LLM_API_KEY` |
| 火山方舟 | `llm.base_url: https://ark.cn-beijing.volces.com/api/v3`；`llm.model: <接入点ID>` |
| Ollama（本机） | `llm.base_url: http://host.docker.internal:11434/v1`；`llm.model: qwen2.5:7b`；key 可留空 |

密钥放在 `coa/platform/.env`（Compose 会注入 platform 容器），键名与 `llm.api_key_env` 一致。改后重启 platform。
Ollama 在 Linux 上需把 `host.docker.internal` 换成宿主 IP 或加 `extra_hosts`。

### 4.2 Embedding

| 目标 | 配置 | 额外动作 |
|---|---|---|
| 换本地模型 | 权重放 `data/models/<name>/`；把 compose 的 TEI `--model-id` 改为该路径；`embedding.model` 同步改 | `docker compose up -d --force-recreate embedding`（重新加载权重），再重启 platform |
| 换外部 OpenAI 兼容服务 | `embedding.provider: openai-compatible`；`embedding.endpoint: https://.../v1`；`embedding.model: <名称>`；密钥 `embedding.api_key_env` | 重启 platform；**必须输出 1024 维**（`embedding.dimensions` 是 `Literal[1024]`） |
| 关闭向量 | `embedding.provider: disabled` | 重启 platform；检索自动退词法并 `degraded=true` |

`fake` 仅用于 `smoke-s3` 的确定性测试，生产配置会被标记 `embedding:fake(test_only)`，不要使用。

### 4.3 图存储

| 目标 | 配置 | 现状 |
|---|---|---|
| Oxigraph HTTP（默认，唯一可用） | `graph.provider: oxigraph-http`；`graph.endpoint: http://oxigraph:7878` | ✅ 已实现 |
| 嵌入式 / Fuseki / AGE | `pyoxigraph` / `fuseki` / `age` | ❌ **均未装配**：当前版本启动直接拒绝（`E_PROVIDER_UNSUPPORTED`），别改 |

**GSP 口径（S14H-16 起）：** 平台面 `/store` = **不支持**（读 `GET` → 405，写 `POST/PUT/DELETE` → 403 `E_GSP_GOVERNANCE_REQUIRED`，含 staging）；后端 Oxigraph 直连 = **full**，仅内部使用，不映射宿主端口。`/status` 中 `gsp_support=none`、`gsp_platform{read:unavailable, write:forbidden}`、`gsp_backend_support=full`；字段定义见 `_design/04-单机接口契约.md` 4.3 节。

### 4.4 对象存储

| 目标 | 配置 | 现状 |
|---|---|---|
| 本地文件 CAS（默认） | `storage.large_object_provider: fs`；`storage.root: /data` | ✅ |
| PostgreSQL 大对象 | `storage.large_object_provider: pg` | ❌ 未实现（启动报错） |
| Silo | `storage.large_object_provider: silo` 或 `storage.provider: silo` | ❌ P1 未实现（启动报错） |
| 小对象走 PG / FS | `storage.small_object_provider: pg`（默认）或 `fs` | ✅ |

### 4.5 推理与物化

`reasoning.mode` 控制链路走到哪一步（改后重启 platform）：

| 值 | RDFS 闭包（Jena） | OWL（ROBOT/ELK） | SHACL 门禁 | 写 inferred |
|---|---|---|---|---|
| `off` | — | — | — | 否 |
| `validate` | — | — | ✅ | 否 |
| `rdfs` | ✅ | — | ✅ | ✅ |
| `materialize`（默认） | ✅ | ✅ | ✅ | ✅ |

`reasoning.engine`/`profile` 当前固定 ROBOT + ELK；SHACL 形状放 `data/shapes/*.ttl`，改形状后重新物化即可（不必重启）。
同版本同 mode 重跑会 `skipped=true`；变更 A-Box/T-Box/mode 才重算。

### 4.6 什么时候必须重启

| 改动 | 动作 |
|---|---|
| `platform.yaml` 或 `PLATFORM__*` 环境变量 | `docker compose up -d --force-recreate platform` |
| `.env` 端口/密码 | `docker compose up -d`（相关容器会重建） |
| 换 embedding 模型权重/TEI 参数 | `docker compose up -d --force-recreate embedding` + 重启 platform |
| 换 `bootstrap.ttl` | 不用重启：watch 每 30 s 读一次；只影响 `init_semver=0.0.0` 指针 |
| 换 `data/shapes/*.ttl` | 不用重启：下次 `materialize`/`validate` 读取 |
| 新增文档/审批/索引 | 不用重启：走 API，立即生效 |

## 5. 明确不支持

- **无鉴权、无权限、无多用户、无租户隔离**：服务只应监听本机（compose 已绑定 `127.0.0.1`）。
- **无 OCR**：扫描版 PDF/图片入库会 `degraded=true` + `NO_OCR_ENABLED`，不解析文字。
- **无事件总线/异步队列**：索引、抽取、物化都是同步 API 作业；大文档会让请求变慢。
- **无 LLM 答案生成**：检索返回片段/事实/引用，不生成自然语言答案。
- **无 Fuseki/AGE、无 PG 大对象、无 Silo**（配置键存在但启动拒绝）。
- 无图表美化、无多语言 UI、无移动端适配。
- Windows 是开发环境；Linux 生产部署未验证。

## 6. 故障排查前 6 条

1. **端口被占**：`Get-NetTCPConnection -LocalPort 8080 -State Listen`；`up.ps1` 看到已有平台会跳过 `compose up`，不是本平台就改 `.env` 的 `PLATFORM_PORT`。
2. **reasoner 没起来**：物化返回 `503 E_REASONER_UNAVAILABLE`；`docker compose logs --tail 60 reasoner`，首次 Java 启动需 ~60–90 s，`/healthz` 绿后再物化。
3. **模型没下载/加载失败**：`docker compose logs embedding` 若报权重缺失，确认 `data/models/bge-m3` 有 12 个文件（~2.3 GB）；加载完成前 `/health` 不可用，索引会自动退词法（`degraded=true`）。
4. **PG 卷残留/密码不一致**：日志 `28P01` 或旧 schema → 备份后 `docker compose down -v`；改 `.env` 的 `POSTGRES_PASSWORD` 必须同时清卷，否则认证失败。
5. **CORS**：`file://` 直开（`Origin: null`）已允许；若被浏览器/公司策略拦截，改用 `http://127.0.0.1:8080/ui/`（同源，无 CORS）。
6. **磁盘权限/空间**：容器内 `/data` 必须可写；`storage.min_free_pct=10`，空间不足写入会报存储错误。不要把 `data/` 放在只读同步盘（OneDrive/受控目录）上。

## 7. 自检参考

| 命令 | 期望 |
|---|---|
| `platform smoke` | 7/7 |
| `platform smoke-s1` … `smoke-s13` | 17/17、17/17、18/18、22/22、27/27、19/19、26/26、20/20、18/18、22/22、18/18、11/11、13/13 |
| `tests/acceptance.ps1` | `ACCEPTANCE passed=42 failed=0` |
| `GET /status` | `slice=S13`，`schema_version=12` |
