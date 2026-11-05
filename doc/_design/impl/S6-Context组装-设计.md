# S6 Context 组装 · 设计

> 切片：S6 · 版本：v0.1 · 日期：2026-11-05
> 上游：04 §5.3（`ContextResolver` v1 契约）、03 §6.5（D19 RRF `k=60` 写死）、03 §6.5（D20 默认只读最新版本）、10 §3（S6）
> 原则：D18「只做编排」——子图交 Oxigraph 求值，召回交 pgvector/FTS，融合沿用 S3 的固定 RRF；**应用层不做结果集合并/重排**。

## 1. 目标、范围与不做

### 1.1 目标

1. 一个入口把「问题 + 实体提示 + 图列表 + top-k + token 预算」组装成可序列化的 `ContextPack`。
2. 每条片段/事实都可追溯：文档 id、chunk id、三元组、图版本（`ontologyVersion` + `graph`）。
3. 明确的降级：图服务不可用 → 仅文档片段 + `degraded=true`；检索不可用 → 仅图事实 + `degraded=true`；两者都不可用 → 结构化空包（HTTP 200）。
4. token 预算按**固定顺序截断**，返回 `truncated=true` 与被省略数量。

### 1.2 边界（重点）

- **只拼查询与参数**：SPARQL 文本、`FROM`/`FROM NAMED` 数据集、`LIMIT`、检索 top-k、预算数值；求值全部在 Oxigraph / pgvector / PG FTS 内完成。
- **不合并多路结果集**：图事实与检索片段各自成段（`facts` / `chunks`），不存在“图分 + 向量分”加权重排；chunk 排序直接沿用 S3 `SearchService.hybrid_search` 的 RRF 结果。
- **不做**：答案生成（LLM 回答在 S7/调用方）、缓存实现、术语学习、实体消解、`warm()`、独立的 `explain()` 端点（本切片把步骤内联在 `steps` 字段）。

### 1.3 明确不做

- 不做应用层“多路重排算法”，不改 RRF `k=60`，不引入权重配置；
- 不做跨版本结果并集（D20）：`ontologyVersion` 只影响 `FROM` 的图；
- 不做 HTML 渲染/Web UI（S7）；
- 不做鉴权、指标、事件总线。

## 2. 接口与数据模型

### 2.1 端口

```text
port ContextResolver v1
resolve(request: ContextRequest) -> ContextPack
```

### 2.2 请求

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `query` | string（必填，非空） | — | 问题/检索词 |
| `taskType` | `answer\|extract\|classify\|plan` | `answer` | 只影响输出标注，不改变算法 |
| `entityHints` | IRI[] | `[]` | 为空时由图按 `rdfs:label` 包含 `query` 反查种子（`LIMIT graph.seed_limit`）|
| `graphs` | IRI[] | 当前 T-Box 图 + inferred 指针图 | 图列表；非法（无 scheme）→ `E_CONTEXT_GRAPH` |
| `ontologyVersion` | string | 已物化版本（`reasoning` 指针），回退到当前已发布版本 | 决定 T-Box 图；未知版本 → `E_CONTEXT_VERSION` |
| `strategy` | `hybrid\|vector\|lexical` | `hybrid` | 传给 `SearchService`（04 的 `strategies[]` 收敛为单值） |
| `topK` | int | `context.default_top_k` | 1..50 |
| `tokenBudget` | int | `context.default_token_budget` | 1..`context.max_token_budget` |

### 2.3 响应 `ContextPack`

```jsonc
{
  "id": "pack-<hex>",
  "taskType": "answer",
  "ontologyVersion": "ont-...",
  "graphs": ["urn:platform:graph:tbox:ont-...", "urn:platform:inferred:ont-..."],
  "terms":   [{"term":"urn:...","label":"...","sourceGraph":"..."}],
  "entities":[{"id":"urn:...","types":["urn:..."],"label":"..."}],
  "facts":   [{"subject":"urn:a","predicate":"urn:p","object":{"kind":"iri","iri":"urn:b"},
               "graph":"urn:platform:inferred:ont-...","ontologyVersion":"ont-...",
               "citationId":"triple:<sha1>"}],
  "chunks":  [{"docId":"doc-...","chunkId":"chk-...","text":"...","score":0.0327,
               "pageFrom":1,"pageTo":2,"citationId":"doc:<docId>#<chunkId>"}],
  "citations":[{"id":"doc:<docId>#<chunkId>","kind":"chunk","ref":"<chunkId>",
                "documentId":"doc-...","locator":"p1-2"},
               {"id":"triple:<sha1>","kind":"triple","ref":"<s> <p> <o>",
                "graph":"...","ontologyVersion":"ont-..."}],
  "tokenEstimate": 512,
  "tokenBudget": 2048,
  "truncated": false,
  "omitted": {"chunks": 0, "facts": 0},
  "strategy": "hybrid",
  "degraded": false,
  "warnings": [],
  "steps": [{"name":"graph.seed","durationMs":12,"output":{"seeds":2}},
            {"name":"graph.facts","durationMs":8,"output":{"facts":5}},
            {"name":"search.hybrid","durationMs":240,"output":{"hits":10}},
            {"name":"budget.cut","durationMs":1,"output":{"truncated":false}}]
}
```

- `object` 与 `GraphStore.query` 的 term 结构一致（`iri|literal|bnode`），不做二次序列化。
- `citationId` 是稳定可定位的键：chunk 用 `doc:<docId>#<chunkId>`，三元组用 `triple:<sha1(s p o graph)>`。

## 3. 配置

```yaml
context:
  enabled: true
  default_token_budget: 2048   # 64..32768
  max_token_budget: 8192       # 64..65536
  default_top_k: 10            # 1..50
  graph_limit: 50              # 每个查询返回的三元组上限
  seed_limit: 10               # 无 entityHints 时按 label 反查的种子上限
```

校验（`check-config`）：

| 条件 | 结果 |
|---|---|
| `default_token_budget > max_token_budget` | `E_CONFIG_CONTEXT`（78） |
| `context.enabled=false` | `E_CONTEXT_DISABLED`（400，调用 `resolve` 时） |

## 4. 编排流程与失败语义

1. **解析版本与图**：`ontologyVersion` 显式时用之；否则取 `reasoning.status().pointer.ontologyVersion`（已物化版本），无指针时回退 `OntologyRegistry.current()`。图默认 = 该版本 T-Box 图 + 同版本 inferred 指针图；显式版本与指针版本不一致时只用 T-Box（避免跨版本混图）。
2. **种子**：`entityHints` 非空则直接用；否则按 `SELECT DISTINCT ?s WHERE { VALUES ?g {...} GRAPH ?g { ?s rdfs:label ?l } FILTER(CONTAINS(STR(?l), "...")) } LIMIT n`，由 Oxigraph 求值。
3. **图事实**：单个 `SELECT ?s ?p ?o`，`FROM <tbox> FROM <inferred>` + `VALUES ?s { seeds }` + `LIMIT graph_limit`；`FROM` 数据集交 Oxigraph 求值（D20）。
4. **文档片段**：调 `SearchService.hybrid_search(query, limit=topK, mode=strategy)`；RRF 在 S3 内完成，本层不重排。
5. **预算**：先 chunks（按 S3 分数序），再 facts（按 `citationId` 字典序，确定性）；估算 `tokens = CJK 字符数 + 其余字符数/4 + 1`；超预算即停，`truncated=true` 并记 `omitted`。
6. **降级**：图/检索任一路 `PortError` → 该段为空 + `degraded=true` + `warnings=[<providerCode>]`；两路同时失败仍返回 200 的空包。
7. **日志**：`event=context_resolve`，字段 `packId/version/chunks/facts/tokens/degraded/ms`。

### 4.1 错误码

| 场景 | 端口码 | HTTP |
|---|---|---|
| `query` 为空 | `InvalidArgument/E_CONTEXT_QUERY_EMPTY` | 400 |
| `tokenBudget` 越界 | `InvalidArgument/E_CONTEXT_BUDGET` | 400 |
| `taskType` 非法 | `InvalidArgument/E_CONTEXT_TASK` | 400 |
| `strategies/topK` 非法 | `InvalidArgument/E_CONTEXT_ARG` | 400 |
| `graphs` 非法 IRI | `InvalidArgument/E_CONTEXT_GRAPH` | 400 |
| `ontologyVersion` 不存在 | `NotFound/E_CONTEXT_VERSION` | 404 |
| `context.enabled=false` | `Unsupported/E_CONTEXT_DISABLED` | 400 |
| 图不可用 | 降级（`E_GRAPH_UNAVAILABLE`） | 200 + `degraded` |
| 检索不可用 | 降级（`E_SEARCH_DISABLED`/`E_EMBED_UNAVAILABLE`） | 200 + `degraded` |
| 无命中（预算内） | 正常空包（`chunks=[] facts=[]`） | 200 |

## 5. 验收用例

| # | 场景 | 期望 |
|---|---|---|
| 1 | 语料含唯一 nonce，索引后 `resolve(nonce)` | `chunks>=1`，`tokenEstimate>0`，`degraded=false` |
| 2 | 引用可追溯 | 每条 chunk 的 `docId/chunkId` 在 PG 中存在，`citations` 与其一一对应 |
| 3 | 发布 v1 + 写 A-Box + 物化，`resolve(entityHints=[alice])` | `facts>=1`，含 `alice a Person`；fact 的 `graph` 为 inferred，`ontologyVersion` 为当前版本 |
| 4 | `tokenBudget=64` 且语料较长 | `truncated=true`，`tokenEstimate<=64`，`omitted>0` |
| 5 | 图 endpoint 指向 127.0.0.1:9 | 200，`degraded=true`，`chunks` 仍有内容，`facts=[]` |
| 6 | `search.enabled=false` | 200，`degraded=true`，`chunks=[]`，`facts` 仍有内容 |
| 7 | 无关查询（乱码串）且空图 | 200，结构化空包，非 500 |
| 8 | `query=""` | 400 `E_CONTEXT_QUERY_EMPTY` |
| 9 | `tokenBudget=0` | 400 `E_CONTEXT_BUDGET` |
| 10 | `graphs=["bogus"]` | 400 `E_CONTEXT_GRAPH` |
| 11 | `ontologyVersion=<v1>` | 包内 `ontologyVersion==v1`，`graphs` 含 v1 的 T-Box 图 |
| 12 | `default_token_budget>max_token_budget` 配置 | 78 `E_CONFIG_CONTEXT` |
| 13 | `GET /status` | `slice=S6`，providers 含 `context` |
| 14 | `POST /context/resolve`（HTTP） | 200 且字段完整；空 query → 400 |

回归：`smoke` 7/7、`smoke-s1` 17/17、`smoke-s2` 17/17、`smoke-s3` 18/18、`smoke-s4` 22/22、`smoke-s5` 27/27、`smoke-s6` 全过、`acceptance.ps1` 全过。

## 6. 依赖与复用

| 复用 | 来源 | 用途 |
|---|---|---|
| `SearchService.hybrid_search` | S3 | 片段召回 + RRF（不新增排序逻辑） |
| `OntologyRegistry.current()/get()` | S1 | 版本与 T-Box 图 |
| `ReasoningService.status().pointer` | S5 | inferred 图与版本 |
| `GraphStore.query()` | S0/S1 | SPARQL（含 `FROM`）交 Oxigraph |
| `MetadataPg` | S1 | 校验 chunk/document 存在性（测试用） |

无新增第三方依赖、无新增容器。

## 7. 与上游契约的对应

| 04 §5.3 字段 | S6 落点 |
|---|---|
| `ContextRequest.query/taskType/entityHints/ontologyVersion/tokenBudget/strategies` | §2.2 全量；`filters/metadata` 不实现（无消费方）；`strategies[]` 收敛为单值 `strategy` |
| `ContextPack.terms/entities/facts/chunks/citations/provenance` | §2.3；`provenance` 并入 `citations`（每项带 `graph`/`documentId`） |
| `strategy` 实际主策略 | 请求字段 `strategy`，默认 `hybrid` |
| `degraded` 必带 `warnings` | §4 第 6 步 |
| `explain(packId)` | 本切片改为响应内联 `steps`（OQ-38） |

## 8. 风险

| 风险 | 应对 |
|---|---|
| 无 entityHints 时按 label 反查可能扫全图 | `LIMIT seed_limit` + 仅查 `rdfs:label`；learn 档数据量小 |
| token 估算是固定启发式（非真实分词） | 作为保守估算写死公式；预算严格按估算值截断 |
| 片段与事实两段不重排，可能“事实很多、片段很少” | 预算按 §4 第 5 步固定顺序；调用方可调 `tokenBudget`/`topK` |
| 图与检索双降级返回空包，调用方难区分 | `degraded=true` + `warnings` 给出两个 providerCode |

## 9. 实施结果

实测（2026-11-05，`docker compose exec -T platform platform smoke-s6`）：

- `smoke-s6` **19/19**：`corpus.index`、`ontology.materialize`、`context.chunks`、`context.citations`、`context.traceable_chunks`（逐条回查 `platform.document_chunk`）、`context.facts`、`context.fact_citations`、`context.budget_truncated`（`tokenBudget=64` → `truncated=true`, `omitted.chunks>=1`）、`context.empty`、`context.graph_down`（`E_GRAPH_UNAVAILABLE`，仅 chunks）、`context.search_disabled`（`E_SEARCH_DISABLED`，仅 facts）、`bad_query/bad_budget/bad_graph`、`context.version`、`http.status`、`http.context_resolve`、`http.context_bad_request`、`config.failfast`（`E_CONFIG_CONTEXT` exit 78）。
- 与设计偏差（已回填本文）：① 04 的 `strategies[]` 收敛为单值 `strategy`；② 默认版本取 **reasoning 指针的已物化版本**（而非 T-Box 发布指针），否则 `facts.graph` 与 `ontologyVersion` 可能来自不同版本；显式版本与指针不一致时只用该版本 T-Box 图。
- 空结果探针使用固定串 `zzzqqqxxxjjj`（先实测 pg_trgm/FTS 均为 0 命中；原 `zzqx-none-<nonce>` 会被 trigram 命中）。
- 回归：`smoke-s4` 22/22、`smoke-s5` 27/27（形状调整后），全量 `tests/acceptance.ps1` **passed=29 failed=0**（含 `smoke-s6` 与 `bad_config_context`）。

## 10. 可复现命令

```powershell
cd D:\agentABC\_impl
docker compose up -d
docker compose exec -T platform platform smoke-s6
powershell -ExecutionPolicy Bypass -File .\tests\acceptance.ps1
```
