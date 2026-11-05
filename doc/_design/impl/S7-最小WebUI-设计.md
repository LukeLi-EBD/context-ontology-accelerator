# S7 最小 Web UI · 设计

> 切片：S7 · 版本：v0.1 · 日期：2026-11-05
> 上游：10 §3（S7 定义）、04（既有 API 契约）、S2/S3/S4/S5/S6 已验收接口
> 原则：UI **只调用已稳定的 API**，不写业务算法；静态资源 + 原生 JS，不引入前端框架与 Node 构建链（D18）。

## 1. 目标、范围与不做

### 1.1 目标

1. 打开浏览器即可看到平台是否可用：版本指针、五容器状态、各命名图三元组数。
2. 走通「上传 → 解析 → 检索 → 审批 → 物化」一条链，且每步失败都有明确错误码。
3. 降级可见：`degraded`/`truncated` 必须出现在界面上（黄色提示条 + 徽标），不得静默。
4. 一条命令起站（`scripts/up.ps1`），一条命令灌示例数据（`scripts/seed.ps1`）。

### 1.2 交付形态

| 项 | 取值 |
|---|---|
| 资源 | `_impl/web/`：`index.html`/`ontology.html`/`documents.html`/`search.html`/`approvals.html` + `app.css` + `app.js` |
| 托管 | 平台 `StaticFiles` 挂 `/ui`（`html=true`），`GET /` → **307** `/ui/` |
| 直开 | `index.html` 用 `file://` 打开时，`API_BASE = http://127.0.0.1:8080` |
| 构建 | 无。无 npm / 无打包 / 无框架；CSS/JS 原样下发 |
| 浏览器 | 现代 Chromium/Firefox/Edge；不使用 ES module import 之外的构建特性 |

`app.js` 唯一的环境分支：`location.protocol === 'file:' ? 'http://127.0.0.1:8080' : ''`，其余逻辑同源。

### 1.3 明确不做

- **不做登录、不做鉴权、不做权限、不做多用户**（单机单租户，端口层不暴露用户概念）。
- **不做图表美化**：三元组数用表格/数字，不引图表库，不做看板编排。
- 不做实时推送（如需刷新用浏览器刷新）；不做前端路由；不做 i18n；不做移动端适配优化。
- 不做答案生成（检索页只展示片段/事实/引用，不调 LLM 写回答）。
- 不做指标/追踪/告警。

## 2. 页面清单与接口依赖

| # | 页面 | 文件 | 依赖接口 | 能做什么 |
|---|---|---|---|---|
| ① | 概览 | `index.html` | `GET /ui/api/overview`、`GET /status`（可选） | 看版本指针/五容器/图计数/候选数/物化指针 |
| ② | 本体浏览 | `ontology.html` | `GET /ui/api/ontology`、`GET /ui/api/entities?q=`、`GET /ui/api/neighbors?iri=` | 浏览类/属性、搜实体、看邻居子图（表格形式） |
| ③ | 文档库 | `documents.html` | `POST /documents`、`GET /documents`、`GET /documents/{id}`、`GET /documents/{id}/chunks`、`POST /documents/{id}/index`、`POST /documents/{id}/extract` | 上传、看解析状态、看原文片段、触发索引/抽取 |
| ④ | 检索与问答 | `search.html` | `GET /ui/api/search`（内部为 `ContextResolver`） | 输入问题 → 片段 + 事实 + citations，展示 `truncated`/`degraded` |
| ⑤ | 审批队列 | `approvals.html` | `GET /ui/api/candidates`、`POST /candidates/{id}/approve`、`POST /candidates/{id}/reject`、`POST /reasoning/materialize` | 逐条通过/拒绝，查看来源片段，触发物化 |

### 2.1 页面字段（对实现的约束）

- **概览**：`ontology.pointer`（`versionId`/`semver`/`graph`）、`services[]`（postgres/oxigraph/embedding/reasoner/storage）、`graphs[]`（`iri`/`triples`）、`counts`（documents/chunks/embeddings/candidatesPending）、`reasoning.pointer.targetGraph`、`degraded`。
- **本体浏览**：`classes[]`（`iri`/`label`/`parents`）、`properties[]`（`iri`/`label`/`kind`/`domain`/`range`）、`entities.items[]`（`iri`/`label`/`types`）、`neighbors.edges[]`（`s`/`p`/`o`）。
- **文档库**：列表 `documentId`/`filename`/`status`/`pages`/`degraded`；片段 `items[]`（`chunkId`/`text`/`tokenEstimate`）。
- **检索**：`chunks[]`（含 `documentId`/`page`/`text`/`score`）、`facts[]`、`truncated`/`degraded`/`steps`。
- **审批**：`subject`/`predicate`/`object`/`confidence`/`state`/`evidence`（来源 chunk 文本）。

## 3. 空态、错误态与降级呈现

| 场景 | 页面行为 | 判据 |
|---|---|---|
| 无本体/无实体 | 表格显示「暂无数据」，不显示空白页 | 容器 DOM 存在空态节点 |
| 本体未发布 | 概览 `pointer = null` 显示「未发布」 | 页面仍 200 |
| 上传失败（格式/损坏） | 红色错误块显示 `providerCode`（如 `E_DOC_FORMAT_UNSUPPORTED`） | 错误文本含错误码 |
| 上传成功但扫描件 | 行内 `degraded` 徽标 + `NO_OCR_ENABLED` | 徽标可见 |
| 检索超预算 | 黄色警告条「结果已截断」+ `truncated=true` | 警告块存在 |
| 检索降级（图/embedding 停） | 黄色警告条「降级」+ `degraded=true` | 警告块存在 |
| 审批冲突（已处理） | 错误块显示 `409` + `providerCode` | 不静默刷新为成功 |
| 物化失败（推理器停/违规） | 错误块显示 `503`/`409` 与错误码；**图不变** | 概览计数不增 |
| 服务不可达 | 概览对应行标 `unavailable`，其余页仍可打开 | 页面 200 |

统一错误渲染：`api()` 捕获非 2xx，`showError()` 输出 `HTTP <status> <code>` + `detail`，不使用 `alert()`，不吞错。

## 4. 一条命令起站与示例数据

### 4.1 `scripts/up.ps1`

1. 检查 `docker version` 可用；
2. 检查 8080 是否已被本平台占用（`/healthz` 200 → 跳过 `compose up`，直接等待 healthy）；
3. `docker compose up -d`（`.env` 的 `COMPOSE_PROFILES=learn` 带 5 容器）；
4. 轮询 `/readyz`（上限 150s，3s 间隔）；
5. 打印五容器状态表、`http://127.0.0.1:8080/ui/`、seed 命令、`/docs` 地址。

失败即非零退出并提示 `docker compose logs --tail 40 platform`。

### 4.2 `scripts/seed.ps1`

1. `platform ontology import --file /app/examples/ontology/sample.ttl --semver 1.0.0 --label coastal-sample`；
2. 正则提取 `versionId` → `ontology publish`；
3. 对 `examples/documents/*.txt`：`curl.exe -F` 上传 → `/index` → `/extract`；
4. 打印 overview 计数（`documents/chunks/embeddings/pendingCandidates`）。

示例本体：`Facility/MonitoringSite/Region/Pollutant/WaterBody` + `urn:platform:rel:locatedIn`（domain `MonitoringSite`、range `Region`），与 S4 规则抽取、S5 形状一致，保证「打开即有内容」。

脚本全部为 ASCII（Windows PowerShell 5.1 以 GBK 解析无 BOM 文件，中文会导致 `Unexpected token`）。

## 5. 验收用例（`platform smoke-s7`，26 条）

| 组 | 断言 |
|---|---|
| 页面 | 5 个 HTML 均 200 且含 `data-page` 标记；`/` 307 → `/ui/`；静态资源可达 |
| 直开 | `Origin: null` 请求 `/ui/api/overview` 返回 `access-control-allow-origin: null` |
| 概览 | `pointer` 非空、`graphs` 非空、五服务全在 |
| 本体 | 发布示例本体后 `classes`/`properties` 非空 |
| 浏览 | `entities` 命中、`neighbors` 返回边；`iri=""` → 400 `E_UI_BAD_IRI` |
| 文档 | 上传 200、`index` 200、`chunks.items` 非空、`extract.inserted > 0` |
| 审批 | 候选带 `evidence`；`approve` 后 A-Box 计数增加 |
| 物化 | `materialize` 200 且 `stages` 含 `rdfs`/`owl`/`shacl` |
| 幂等 | 同版本重跑 `skipped=true` |
| 降级可见 | `tokenBudget=32` 时 `truncated=true`，且静态资源含 `truncated`/`degraded` 字样 |
| 状态 | `/status` 的 `slice=S7` |

## 6. 依赖与复用

| 复用 | 说明 |
|---|---|
| S2 文档端点 | 上传/列表/片段/索引，UI 不新增解析逻辑 |
| S3 `SearchService` | 检索页只调 `ContextResolver`，不重复 RRF |
| S4 审批端点 | 通过/拒绝直接调用，UI 不改状态机 |
| S5 `materialize()` | 审批页按钮直接触发，不复制推理/校验逻辑 |
| S6 `ContextResolver` | 检索页的 `chunks`/`facts`/`citations`/`truncated`/`degraded` 全部来自 pack |

新增代码仅 `webui.py`（只读视图）、`api.py` 六个 `/ui/api/*` 路由 + `StaticFiles` 挂载。`webui.py` 只查询、不写图。

## 7. 风险

| 风险 | 处置 |
|---|---|
| `file://` 直开时 CORS | 平台已允许本机来源；若浏览器拒绝，改用 `http://127.0.0.1:8080/ui/`（一条命令起站的默认路径） |
| Powershell 5.1 编码 | 脚本全 ASCII；页面 UTF-8 |
| 大文件上传超时 | 本切片演示用小文本；>10MB 走 S2 既有对象路由，不在 UI 做分片 |
| 空图导致页面 500 | `webui.py` 对图/元数据异常分别捕获，返回结构化空值与 `error` 字段 |

## 8. 实施结果（2026-11-05）

| 项 | 结果 | 证据 |
|---|---|---|
| `platform smoke-s7` | **26/26** | 5 页面 200+marker、`/` 307、`Origin: null` 直开、publish、ontology、entities、neighbors、upload/index/chunks、extract、candidates evidence、approve、abox 写入、`materialize.chain`、`materialize.idempotent`、truncated 可见、`slice=S7`、`E_UI_BAD_IRI` |
| `tests/acceptance.ps1` | **passed=30 failed=0** | S1 17/17、S2 17/17、S3 18/18、S4 22/22、S5 27/27、S6 19/19、S7 26/26 |
| 一条命令起站 | `scripts/up.ps1` 实测成功 | 五容器 Up，`/readyz` 200，打印 `/ui/` |
| 示例数据 | `scripts/seed.ps1` 实测成功 | `documents=36 chunks=38 embeddings=20 pendingCandidates=35` |

### 8.1 实施中发现并修正

| # | 现象 | 修正 |
|---|---|---|
| 1 | `webui._values` 只读 `item["value"]`，IRI term 实际在 `iri` 键 → 类/实体/图全空 | `item.get("value", item.get("iri", ""))` |
| 2 | 实体列表空 → `neighbors?iri=` 触发 FastAPI `min_length` → 422 | 同上修复后自愈；仍保留 `E_UI_BAD_IRI` 400 |
| 3 | 平台 init watcher 每 30s 把用户发布的 T-Box 回退到 bootstrap，S7 页面的类会消失 | `ontology_pg.bootstrap` 在 pointer 的 `semver ≠ init_semver` 时 `skipped`（"pointer managed outside init source"） |
| 4 | PowerShell 5.1 按 GBK 解析无 BOM 中文脚本 → `Unexpected token` | `up.ps1`/`seed.ps1` 全 ASCII |
| 5 | CLI 先输出 JSON 日志行再输出 pretty JSON，`ConvertFrom-Json` 失败 | seed 用正则 `'"versionId"\s*:\s*"(ont-[^"]+)"'` 提取 |
| 6 | smoke 字段名与实现不符（`items`/`inserted`/`subject`） | 同步修正 smoke 与 `app.js` |
| 7 | `file://` 直开时 `Origin: null`，无 CORS 头 → 数据加载被浏览器拦截 | `api.py` 加 `CORSMiddleware`（`null` + 本机 8080 两个来源，GET/POST）；smoke 增 `ui.file_origin` 断言 |

## 9. 可复现命令

```powershell
cd D:\agentABC\_impl
powershell -ExecutionPolicy Bypass -File .\scripts\up.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\seed.ps1
start http://127.0.0.1:8080/ui/
docker compose exec -T platform platform smoke-s7
powershell -ExecutionPolicy Bypass -File .\tests\acceptance.ps1
```
