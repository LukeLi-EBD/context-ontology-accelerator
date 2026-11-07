# q_S03 · 混合检索与 RRF 融合

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_S03` |
| 特性名称 | 混合检索与 RRF 融合 |
| 分组 | A 核心工作流 S0-S14 |
| 文档依据 | 10-实施路线图.md S3；45-产品架构介绍.md |
| **评估轮次** | **R2（第 2 轮复评）** |
| **本轮采集时间 T2** | **2026-11-07 07:56:21 +0800** |
| **判据栈** | 双栈 |
| 结论（T2） | **PASS** |
| 证据截图 | ![终端输出截图](screenshots/q_S03.png) |
| 完整原始输出 | `evidence/q_S03.txt` |

## 0 时间区分（本轮新增）

> 同一特性在不同时间点、不同栈上的状态不同，结论必须带坐标。T0/T1 的旧产物完整保存在
> `_history/2026-11-06_2352/`，独立复核见 `../_evidence-audit/qa_verdict_recheck.md`。

| 轮次 | 时间 | 栈 / 代码基线 | 结论 | 说明 |
| --- | --- | --- | --- | --- |
| **T0 原始采集** | 2026-11-06 23:52 +08 | 数据栈 8080 · 旧镜像 | PASS | R1 采集器，存在 200KB 静默截断与写死结论 |
| **T1 独立复核 / 修复基线** | 2026-11-07 05:45–06:08 +08 | 验收栈 8082 · `8b3f36f` | PASS | 复核定性：一致 |
| **T2 本轮复评** | 2026-11-07 07:56:21 +0800 | 数据栈 8080 + 验收栈 8082 双栈同题 | **PASS** | 采集器已修截断、verdict 由证据动态推导 |

栈说明：
- **数据栈 8080**：镜像 `715d59e8`（11-07 00:53 +08 构建），全量数据，用于验证「数据内容 / 规模」类判据。注意 T0(11-06 23:52) 时 8080 跑的是更早的镜像，容器在 00:53 被重建过，**同一端口跨时间也不是同一个基线**。
- **验收栈 8082**：镜像 `80cb274f` / `agent-platform:0.1-s5`（11-07 05:45 +08 构建），代码等价 `8b3f36f`，验收残留小库，用于验证「代码行为 / 契约」类判据。
- 验收栈 A-Box 为空导致的 `404 / 0` 不判为功能缺陷；两栈版本不同属独立数据库，不计为漂移。

## 1 测试目标

验证 pgvector + FTS 双路召回、RRF(k=60) 融合，且非降级模式。

## 2 输入

- `GET /search?q=青岛&limit=3`
- `GET /ui/api/search?q=青岛&limit=3`

> 零污染约束：仅 HTTP GET、只读 SQL `SELECT`、只读 SPARQL `SELECT`、一个已确认不写库的纯读
> `POST /context/resolve`。未调用 `/answer`（会写 PROV 拒答事件），未运行 smoke/acceptance，
> 未触发 seed / refresh / import / materialize / approve / publish / reindex / rollback。
> 验收栈 SPARQL 因 A-Box 为空显式标注 `SKIP`，不做无意义的图查询。

## 3 期待输出

HTTP 200；mode=hybrid、rrfK=60、routes 含 vector 与 lexical、degraded=false、results 非空且每条带 chunkId 与 citation。

## 4 真实输出（T2 · 双栈同题）

### 4.1 数据栈 127.0.0.1:8080（全量数据 / 旧代码）

```
$ GET /search?q=%E9%9D%92%E5%B2%9B&limit=3
  -> 200  29ms  4224 chars | FULL_LENGTH=4224 chars  SHA256=eb9420bd170d48f0  PARSE=dict  KEYS=query,mode,rrfK,routes,lexicalOnly,degraded,reasons,results,timingMs,embeddingCache
  query = 青岛
  mode = hybrid
  rrfK = 60
  routes = ["vector", "lexical"]
  lexicalOnly = false
  degraded = false
$ GET /ui/api/search?q=%E9%9D%92%E5%B2%9B&limit=3
  -> 200  45ms  10831 chars | FULL_LENGTH=10831 chars  SHA256=4922254492689ead  PARSE=dict  KEYS=id,taskType,ontologyVersion,graphs,terms,entities,facts,chunks,citations,tokenEstimate,tokenBudget,truncated
  id = pack-47f2821f7759
  taskType = answer
  ontologyVersion = ont-11f92ebb3326
  graphs = ["urn:platform:graph:tbox:ont-11f92ebb3326", "urn:platform:inferred:ont-11f92ebb3326"]
  terms = []
  entities = []
$ GET /readyz
  -> 200  28ms  537 chars | FULL_LENGTH=537 chars  SHA256=0fb8ec1aa53f054c  PARSE=dict  KEYS=status,checks,pointerStatus,warnings,note
  status = ok
  checks = {"database": {"status": "ok"}, "graph": {"status": "ok"}, "storage": {"status": "ok", "disk_free_pct": 32.64}}
  pointerStatus = {"name": "tbox/current", "ok": true, "level": "ok", "status": "published", "versionId": "ont-11f92ebb3326", "semver": "1.2.1", "tr ...(截断)
  warnings = []
  note = pointerStatus 仅告警，不参与就绪状态码（避免启动即崩）
$ GET /status
  -> 200  642ms  11200 chars | FULL_LENGTH=11200 chars  SHA256=e7dc32324bc2d0e8  PARSE=dict  KEYS=status,version,slice,mode,runtime_mode,config_version,config_file,providers,not_implemented,degraded,storage,graph
  status = ok
```

### 4.2 验收栈 127.0.0.1:8082（新代码 8b3f36f / 小库）

```
$ GET /search?q=%E9%9D%92%E5%B2%9B&limit=3
  -> 200  21ms  1712 chars | FULL_LENGTH=1712 chars  SHA256=b6601d0f2354b08a  PARSE=dict  KEYS=query,mode,rrfK,routes,lexicalOnly,degraded,reasons,results,timingMs,embeddingCache
  query = 青岛
  mode = hybrid
  rrfK = 60
  routes = ["vector", "lexical"]
  lexicalOnly = false
  degraded = false
$ GET /ui/api/search?q=%E9%9D%92%E5%B2%9B&limit=3
  -> 200  13ms  10998 chars | FULL_LENGTH=10998 chars  SHA256=bdd3ca025422c9ab  PARSE=dict  KEYS=id,taskType,ontologyVersion,graphs,terms,entities,facts,chunks,citations,tokenEstimate,tokenBudget,truncated
  id = pack-4d12389674e8
  taskType = answer
  ontologyVersion = ont-6e81732555e5
  graphs = ["urn:platform:graph:tbox:ont-6e81732555e5", "urn:platform:inferred:ont-6e81732555e5"]
  terms = []
  entities = []
$ GET /readyz
  -> 200  6ms  537 chars | FULL_LENGTH=537 chars  SHA256=014659d11612174f  PARSE=dict  KEYS=status,checks,pointerStatus,warnings,note
  status = ok
  checks = {"database": {"status": "ok"}, "graph": {"status": "ok"}, "storage": {"status": "ok", "disk_free_pct": 32.64}}
  pointerStatus = {"name": "tbox/current", "ok": true, "level": "ok", "status": "published", "versionId": "ont-6e81732555e5", "semver": "0.0.0", "tr ...(截断)
  warnings = []
  note = pointerStatus 仅告警，不参与就绪状态码（避免启动即崩）
$ GET /status
  -> 200  58ms  11356 chars | FULL_LENGTH=11356 chars  SHA256=406a3270929bc0c9  PARSE=dict  KEYS=status,version,slice,mode,runtime_mode,config_version,config_file,providers,not_implemented,degraded,storage,graph
  status = ok
```

> 完整响应（含 `FULL_LENGTH` / `SHA256` / 结构化摘要，超大正文显式标记 `[BODY OMITTED]`）见
> `evidence/q_S03.txt`；终端渲染截图见 `screenshots/q_S03.png`。

## 5 结论

**PASS** — 混合检索端点 HTTP 200，mode=hybrid、rrfK=60、routes=['vector', 'lexical']、degraded=False、results=3 条。



---
[返回总报告](README.md) · [T0 归档](<_history/2026-11-06_2352/q_S03_混合检索与 RRF 融合.md>)
