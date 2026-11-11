# luke 演示 runbook 端到端复跑（真数据）

- 基线：`luke` @ `38b9c4c5`；分支 `verify/luke-runbook`；树 `D:\agentABC\wt\luke-runbook`
- 数据源：容器 `coa-takeover-pg`（`127.0.0.1:5944`，库 `platform`，用户 `platform`，schema max = 53）
- 一键脚本：[luke-demo-runbook.ps1](../tools/luke-demo-runbook.ps1)
- 复跑结论：**8 项判据 = PASS 7 / WARN 1 / FAIL 0**；其中第 4 步"SPARQL 经桥"未通过（503），第 1 步的 web 页面未起、用 API 端点代替渲染验证。未通过/未验证项在第 7 节逐条写明卡在哪一层。

## 1. 端口与边界

| 端口 | 用途 | 归属 |
| --- | --- | --- |
| 8210 | 平台桥 `doc/coa-x/tools/coa_api_local.py` | 本次新起（复用则跳过） |
| 7878 | Oxigraph（容器 `runbook-oxigraph`，卷 `runbook-oxigraph-data`） | 本次新起（复用则跳过） |
| 8081 | BGE-M3 嵌入（容器 `agent-platform-embedding`） | **只读复用既有栈**，不启停 |
| 8091 | context-manager（SPARQL 经桥需要的下游） | 尝试启动失败，未监听（见 7.1） |
| 8080 / 8082 | 冻结平台栈 | **未触碰**，只 GET `/readonly` |

不碰 `D:\agentABC\data\READONLY`，不删除、不重命名。所有数据库指向只写在 `.runbook\platform.yaml`（运行时从仓库基线复制并改四项），以及本次进程的环境变量里；仓库内 DSN / compose / env 默认值零改动。

## 2. 前置

1. Docker 可用，`coa-takeover-pg` 已起（5944），`agent-platform-embedding` 已起（8081）。
2. 桥用的 venv：`D:\agentABC\coa\.venv-coa-local\Scripts\python.exe`。本机曾缺以下包，已补装（**装在 venv，不在仓库**）：
   `anyio>=4`、`annotated-doc`、`annotated-types`、`botocore`、`boto3`；`cedarpy` 按 `uv.lock` 固定为 `4.8.3`（4.12.2 打包缺陷会导致 `ImportError: cannot import name 'pst'`）。
3. 脚本自动生成 `.runbook\platform.yaml`：从 `packages/platform-core/config/authoritative-8080.yaml` 复制，只替换
   `database.url` → `postgresql://platform:platform_dev@127.0.0.1:5944/platform`、
   `graph.endpoint` → `http://127.0.0.1:7878`、
   `embedding.endpoint` → `http://127.0.0.1:8081/v1`、
   `storage.root/tmp_dir` → `.runbook/storage`。

## 3. 一条命令

```powershell
# 起栈 + 全部只读校验（不写库）
powershell -NoProfile -ExecutionPolicy Bypass -File doc\coa-x\tools\luke-demo-runbook.ps1 -Start -Check

# 加一遍真实导入（会向 5944 的 platform 库新增 1 个批次）
powershell -NoProfile -ExecutionPolicy Bypass -File doc\coa-x\tools\luke-demo-runbook.ps1 -Import

# 停掉本脚本起的桥与 oxigraph 容器
powershell -NoProfile -ExecutionPolicy Bypass -File doc\coa-x\tools\luke-demo-runbook.ps1 -Stop
```

`-Check` 也可对已在跑的栈单独执行（不加 `-Start`）。

## 4. 分步记录

### 步骤 1 起栈

命令（脚本内部）：`docker run -d --name runbook-oxigraph -p 127.0.0.1:7878:7878 -v runbook-oxigraph-data:/data oxigraph/oxigraph:0.5.7 serve ...`，再以 8210 起桥。

实测：

```
[config] D:\agentABC\wt\luke-runbook\.runbook\platform.yaml（database/graph/storage 指向本机 5944/7878）
[auth] local dev token ok
```

```
GET http://127.0.0.1:8210/health
200 {"status":"ok","provider":"postgres"}
```

判据：桥 `/health` 200 且 `provider=postgres`（真库，不是内存桩）。**PASS**

另：Oxigraph 默认图已 seed `doc/_fsldm/fsldm-merged.ttl`，`SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }` = `2675`。

### 步骤 2 列表页数字

命令：

```
docker exec coa-takeover-pg psql -U platform -d platform -tAc "select count(*) from platform.ontology_version"
docker exec coa-takeover-pg psql -U platform -d platform -tAc "select count(*) from platform.ontology_proposal"
GET /namespaces/5f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11/ontologies/ont-demo/versions
GET /namespaces/5f1c3a8e-4b56-4f0a-9c3d-1e7b8a9f0c11/ontologies/ont-demo/proposals
```

实测：

```
[PASS] 版本列表 total = DB count — API total=1910 = DB 1910（本页 items=612）
[PASS] 提案列表 count = DB count — API count=1314 = DB 1314（本页 items=50）
```

判据：版本 `total` = 库 `count(*)`；提案 `count` = 库 `count(*)`。**PASS**

观察（事实，不是结论）：列表路由的 `ontologies/{id}` 段不参与过滤，传 `ont-demo` 也返回全量 1910 / 1314；版本列表 `items` 只回 612 条（`count=612`），提案 `items` 回 50 条，分页由 `total`/`count` 区分。

### 步骤 3 详情页逐值

命令（取库里最新一条版本、最新一条提案）：

```
psql -tAc "select version_id||'|'||semver||'|'||status||'|'||trim(content_hash)||'|'||triple_count from platform.ontology_version order by created_at desc limit 1"
GET /namespaces/{ns}/ontologies/ont-53fb5cb43f5b/versions/ont-53fb5cb43f5b
GET /namespaces/{ns}/ontologies/ont-demo/proposals/prop-32e6cc1834cd
```

库里版本行：

```
ont-53fb5cb43f5b|0.15.0|proposed|99e91747048d8fa4f6870f3f610f2fe12a7066124d521e7269d0cf111bc470a6|13|p13-impact-local|urn:platform:graph:tbox:ont-53fb5cb43f5b
```

API 返回（节选关键字段）：

```json
{"id":"ont-53fb5cb43f5b","semver":"0.15.0","status":"proposed",
 "contentHash":"99e91747048d8fa4f6870f3f610f2fe12a7066124d521e7269d0cf111bc470a6",
 "tripleCount":13,"label":"p13-impact-local","graph":"urn:platform:graph:tbox:ont-53fb5cb43f5b",
 "createdAt":"2026-11-10T13:03:54.658230+00:00","publishedAt":null}
```

库里提案行：

```
prop-32e6cc1834cd|ont-53fb5cb43f5b|ont-57544cc6264b|proposed|f|P13 F107 impact panel verification
```

API 返回：

```json
{"proposal":{"proposalId":"prop-32e6cc1834cd","versionId":"ont-53fb5cb43f5b",
 "againstVersion":"ont-57544cc6264b","status":"proposed","breaking":false,
 "changeSummary":"P13 F107 impact panel verification"}, "versionStatus":"proposed"}
```

判据：版本五字段（id / semver / status / contentHash 全文 / tripleCount）逐值相等；提案三字段（proposalId / versionId / status）逐值相等。**PASS**

观察：详情路由的 `ontologies/{id}` 段同样不参与过滤（传 `ont-demo` 与传 versionId 返回一致）；提案详情的 `impact.analysisError` 为 `E_OBJECT_NOT_FOUND`（对象存储里缺 `ontology/sources/92bda143…ttl`），不影响本步字段核对，但演示时不要点"影响分析"。

### 步骤 4 图查询

**直连 7878**

```
POST /query  SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }
→ {"bindings":[{"n":{"value":"2675",...}}]}

POST /query  SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 3
→ 9 个 term（3 条 bindings），样例：
  s=https://w3id.org/fsldm/product#featureValue
  p=http://www.w3.org/2000/01/rdf-schema#comment
  o="特性值统一存字符串，由 featureCode 决定如何解释。…"@zh
```

判据"返回结果而不是空"：**PASS**（直连）。

**经桥 8210**

```
POST /namespaces/{ns}/sparql   body {"sparql":"SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 3"}
→ HTTP 503 {"message": "context manager unreachable: ConnectError", "code": "ConnectError"}
```

判据"不是空或 503"：**未通过**。分层定位见 7.1。

**取消 / 超时语义（504）**

- `doc/coa-x/tools` 下搜 `504`：0 命中。
- 桥的 kernel 调用是 `timeout=120.0`（推理物化 600s），异常统一走 [coa_api_local.py:2130-2138](../tools/coa_api_local.py#L2130-L2138) 的 `except Exception` → `503 {"error":"ontology lifecycle unavailable"}`。
- 结论：**本栈没有 504 映射**，超时若发生会以 503 出现；端到端"触发一次超时并观察状态码"本轮**未验证**（SPARQL 在更早一层就 503 了，见 7.2）。

### 步骤 5 导入一条

命令（脚本 `-Import` 内部，每次生成一个新的源目录 `.runbook\import-src\run-<时间戳>\`，含 1 个 md）：

```
python -m platform_core.cli import <dir> --namespace-id 5f1c3a8e-… --config .runbook\platform.yaml \
       --parse-concurrency 1 --embed-concurrency 1 --batch-size 5
```

实测（最终成功一次）：

```
[PASS] 导入一条 — import_run 4 -> 5；列表新批次 63c59f16-c6e1-452f-aef4-45b922e30a7b
       （total=1 indexed=1 documentsAdded=0 status=COMPLETED）；详情 200
```

`platform.import_run` 实际 5 行（含 1 行本次排障中的失败）：

```
17452ea6-…|06a3e261-…|completed|0
7de712fc-…|06a3e261-…|completed|0
25d31ca0-…|b7ab5eb8-…|completed|1   ← E_EMBED_UNAVAILABLE（7.3）
9912654c-…|0e8ab91d-…|completed|0
5563a664-…|63c59f16-…|completed|0   ← 脚本 -Import 的最终一次
```

判据三项：`import_run` 加 1、`ingestion-runs` 列表出现该行、详情可打开。**PASS**

两个实测细节：

- 批次按 `root` 去重：对同一目录再导一次只新增 item run，列表 `totalCount` 不变（03:39 实测 1→1）。所以脚本每次用新目录，才能出现"新的那 1 行"。
- 批次详情形状是 `{"run":{...},"items":[...]}`，`total/indexed` 在 `run` 下；列表项是扁平结构。详情必须传**批次 id**，传 item run id 会 `E_INGESTION_RUN_NOT_FOUND`。

### 步骤 6 冻结护栏

```
GET http://127.0.0.1:8080/readonly → 200
Test-Path D:\agentABC\data\READONLY → True
docker ps：agent-platform-api | Up 3 hours (healthy)
```

判据：`/readonly` 200、哨兵存在、8080 容器未重启、脚本对 8080 只发过这一条 GET。**PASS**

同一冻结态的补充证据（写接口 409 + `E_PLATFORM_READ_ONLY`、OpenAPI 139 path / 149 operation、DSN 三处与镜像 tag）见 [p1-15-readonly-mirror.md](p1-15-readonly-mirror.md)。

## 5. 脚本输出（最终一次完整跑）

```
[PASS] 版本列表 total = DB count — API total=1910 = DB 1910（本页 items=612）
[PASS] 提案列表 count = DB count — API count=1314 = DB 1314（本页 items=50）
[PASS] 版本详情逐值核对 — ont-53fb5cb43f5b semver=0.15.0 status=proposed hash=99e91747048d… triple=13
[PASS] 提案详情逐值核对 — prop-32e6cc1834cd versionId=ont-53fb5cb43f5b status=proposed
[PASS] SPARQL 直连 :7878 — 返回 bindings（9 个 term）
[WARN] SPARQL 经桥 :8210 — HTTP 503 — {"message": "context manager unreachable: ConnectError", "code": "ConnectError"}（context-manager :8091 依赖 bedrock_agentcore，本机起不来；见 evidence）
[PASS] 导入一条 — import_run 4 -> 5；列表新批次 63c59f16-…（total=1 indexed=1 documentsAdded=0 status=COMPLETED）；详情 200
[PASS] 8080 冻结护栏 — /readonly=200，哨兵 D:\agentABC\data\READONLY 存在

总计 8 项：PASS 7 / WARN 1 / FAIL 0
```

退出码 0（有 FAIL 时才 `exit 1`）。

## 6. 副作用（本次演示写入了什么）

- `5944/platform`：`import_run` 0 → 5（4 次成功 + 1 次 `E_EMBED_UNAVAILABLE` 失败），对应 4 个批次；文档对象落 `.runbook\storage`、`.runbook\objects`。
- 新增容器 `runbook-oxigraph` + 卷 `runbook-oxigraph-data`（`-Stop` 会删容器，卷保留）。
- **未写 8080**，未写 `agent-platform-postgres`（8080 栈的库），未动 `D:\agentABC\data\READONLY`。
- 仓库工作区：仅未跟踪的 `.runbook/` 与新增脚本/本文档；`platform.yaml` 只在 `.runbook/` 下，仓库配置零改动。

## 7. 未通过 / 未验证项（如实记录）

### 7.1 SPARQL 经桥 = 503，卡在 context-manager

- 现象：`POST /namespaces/{ns}/sparql` → `503 {"message":"context manager unreachable: ConnectError","code":"ConnectError"}`。
- 分层：HTTP 桥 8210 → KERNEL 图查询端口 → local-http context-manager（默认 `127.0.0.1:8091`）→ 未监听。
- 启动 8091 的实际失败：`python doc/coa-x/tools/run_local.py context-manager --port 8091` → `ModuleNotFoundError: No module named 'bedrock_agentcore'`（AWS AgentCore SDK，本机与 uv venv 均无）；`doc/_design/78-COA单机可运行性评估-2026-11-08.md` 记为"能起，全程不可用"，其下游是 Neptune/OpenSearch/AWS。
- 定性：这是**环境缺件**（本机未装 AWS SDK），不是代码缺陷。本轮不安装 SDK、不改代码绕开，只把"503 的根因就是这一层"记录在此。
- 结论：**跑不通 + 卡在 context-manager 这一层**。绕过方案（直连 7878）能出结果，但不算"经平台"通过。

### 7.2 504 / 取消语义未验证

- 代码层没有 504：`coa_api_local.py` 内 `504` 零命中，超时/异常统一 503（`:2130-2138`，`timeout=120.0`）。
- 端到端也触发不到超时：SPARQL 请求在 context-manager 连接阶段就 503，没走到"等 120s 再超时"的路径。
- 结论：记"未验证"，不要当作"返回 504"。

### 7.3 导入曾失败一次：临时 config 的 embedding 仍指容器名

- 现象：`1 files failed: E_EMBED_UNAVAILABLE=1`，`elapsedSeconds=2.66`，item 失败但批次状态仍 `COMPLETED`。
- 根因：仓库基线 `authoritative-8080.yaml` 的 `embedding.endpoint` 是 `http://embedding:80/v1`（compose 服务名），宿主机进程解析不到；脚本已补一条替换 → `127.0.0.1:8081/v1`，随后导入 `indexed=1`。
- 另：脚本判据用 `run.indexed >= 1`，不会把"import_run 加了 1 但文档全失败"误判为通过。

### 7.4 web 页面未渲染验证

- `packages/web-app/vite.dev-local.config.mjs` 在本树不存在（`coa` 树有、未跟踪），该配置的 proxy 指向 8080，且依赖生成的 `@auth` stub。
- 本轮"列表页/详情页"用它们背后的 HTTP 端点验证（`/versions`、`/proposals`、详情路由），**没有**起 5273 渲染 UI，也没有截图。
- 结论：接口层 PASS；页面层未验证，演示前需补 web 起栈（且 proxy 不能指 8080）。

## 8. 复跑检查表

| # | 判据 | 本轮 |
| --- | --- | --- |
| 1 | 桥 `/health` 200 且 `provider=postgres` | PASS |
| 2 | 版本 `total` = DB 1910；提案 `count` = DB 1314 | PASS |
| 3 | 版本 5 字段、提案 3 字段与库逐值相等 | PASS |
| 4 | 真实 SPARQL 返回 bindings（不空、不 503） | 直连 PASS；经桥 503（7.1） |
| 5 | 导入后 `import_run` +1、列表出新行、详情 200 | PASS |
| 6 | 8080 `/readonly` 200、哨兵在、未写 8080 | PASS |
