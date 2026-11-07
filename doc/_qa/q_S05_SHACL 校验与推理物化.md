# q_S05 · SHACL 校验与推理物化

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_S05` |
| 特性名称 | SHACL 校验与推理物化 |
| 分组 | A 核心工作流 S0-S14 |
| 文档依据 | 10-实施路线图.md S5；52 §3 HermiT/推理扩展专章 |
| **评估轮次** | **R2（第 2 轮复评）** |
| **本轮采集时间 T2** | **2026-11-07 07:56:21 +0800** |
| **判据栈** | 数据栈 |
| 结论（T2） | **PARTIAL** |
| 证据截图 | ![终端输出截图](screenshots/q_S05.png) |
| 完整原始输出 | `evidence/q_S05.txt` |

## 0 时间区分（本轮新增）

> 同一特性在不同时间点、不同栈上的状态不同，结论必须带坐标。T0/T1 的旧产物完整保存在
> `_history/2026-11-06_2352/`，独立复核见 `../_evidence-audit/qa_verdict_recheck.md`。

| 轮次 | 时间 | 栈 / 代码基线 | 结论 | 说明 |
| --- | --- | --- | --- | --- |
| **T0 原始采集** | 2026-11-06 23:52 +08 | 数据栈 8080 · 旧镜像 | PARTIAL | R1 采集器，存在 200KB 静默截断与写死结论 |
| **T1 独立复核 / 修复基线** | 2026-11-07 05:45–06:08 +08 | 验收栈 8082 · `8b3f36f` | PARTIAL | 复核定性：文案错 |
| **T2 本轮复评** | 2026-11-07 07:56:21 +0800 | 数据栈 8080 + 验收栈 8082 双栈同题 | **PARTIAL** | 采集器已修截断、verdict 由证据动态推导 |

栈说明：
- **数据栈 8080**：镜像 `715d59e8`（11-07 00:53 +08 构建），全量数据，用于验证「数据内容 / 规模」类判据。注意 T0(11-06 23:52) 时 8080 跑的是更早的镜像，容器在 00:53 被重建过，**同一端口跨时间也不是同一个基线**。
- **验收栈 8082**：镜像 `80cb274f` / `agent-platform:0.1-s5`（11-07 05:45 +08 构建），代码等价 `8b3f36f`，验收残留小库，用于验证「代码行为 / 契约」类判据。
- 验收栈 A-Box 为空导致的 `404 / 0` 不判为功能缺陷；两栈版本不同属独立数据库，不计为漂移。

## 1 测试目标

验证 SHACL shapes 已装载、推理服务可用、物化产物写入独立命名图，且推理作业没有持续失败。

## 2 输入

- `GET /validation/shapes`
- `GET /reasoning/status`
- `GET /health/dashboard（取 inferenceFailures / shaclViolations）`

> 零污染约束：仅 HTTP GET、只读 SQL `SELECT`、只读 SPARQL `SELECT`、一个已确认不写库的纯读
> `POST /context/resolve`。未调用 `/answer`（会写 PROV 拒答事件），未运行 smoke/acceptance，
> 未触发 seed / refresh / import / materialize / approve / publish / reindex / rollback。
> 验收栈 SPARQL 因 A-Box 为空显式标注 `SKIP`，不做无意义的图查询。

## 3 期待输出

shapes 文件非空；reasoner available=true；inferenceFailures.count 应为 0 或极低；aboxGraphs 应覆盖真实 A-Box 命名图。

## 4 真实输出（T2 · 双栈同题）

### 4.1 数据栈 127.0.0.1:8080（全量数据 / 旧代码）

```
$ GET /validation/shapes
  -> 200  16ms  460 chars | FULL_LENGTH=460 chars  SHA256=a3bf4ae6c2ae582d  PARSE=dict  KEYS=shapesDir,files,shapesVersion,namespaces
  shapesDir = /data/shapes
  files = ["core.ttl"]
  shapesVersion = c33943c929040b570b82a5f7d701786c322f57e39577205969296d90b6f0b0a0
  namespaces = [{"namespace": null, "dir": ".", "files": ["core.ttl"], "version": "c33943c929040b570b82a5f7d701786c322f57e39577205969296d90b6f0b0 ...(截断)
$ GET /reasoning/status
  -> 200  23ms  1014 chars | FULL_LENGTH=1014 chars  SHA256=9460f7a82cf0f837  PARSE=dict  KEYS=mode,provider,engine,profile,serviceEnabled,endpoint,available,inferredGraphPrefix,aboxGraphs,shapesDir,pointer,lastJob
  mode = materialize
  provider = robot/EL
  engine = robot
  profile = EL
  serviceEnabled = true
  endpoint = http://reasoner:7879
$ GET /health/dashboard
  -> 200  1130ms  3000 chars | FULL_LENGTH=3000 chars  SHA256=29cea96ba6641685  PARSE=dict  KEYS=sampledAt,coverage,orphanInstances,shaclViolations,inferenceFailures,migration,readyz,tbox,pointerStatus,ontologyDiff,dataSource,readOnly
  sampledAt = 2026-11-06T23:56:35.686177+00:00
  coverage = {"classes": {"total": 159, "withInstances": 156, "ratio": 0.9811, "unlabeled": 0, "error": null, "source": "SPARQL GRAPH <urn:plat ...(截断)
  orphanInstances = {"count": 0, "error": null, "source": "A-Box：无出边（除 rdf:type/rdfs:label）且无入边的实例"}
  shaclViolations = {"count": 0, "conforms": true, "importId": "imp-e34387c39d06", "versionId": "ont-draft-b814289626a0", "sampledAt": "2026-11-07T00: ...(截断)
  inferenceFailures = {"count": 336, "lastJob": {"jobId": "rsn-b0dbf674542d", "kind": "materialize", "state": "succeeded", "ontologyVersion": "ont-11f92 ...(截断)
  migration = {"codeVersion": 34, "dbVersion": 34, "consistent": true, "source": "platform.schema_version MAX(version) vs SUPPORTED_SCHEMA_VERSI ...(截断)
$ GET /readyz
  -> 200  28ms  537 chars | FULL_LENGTH=537 chars  SHA256=0fb8ec1aa53f054c  PARSE=dict  KEYS=status,checks,pointerStatus,warnings,note
  status = ok
  checks = {"database": {"status": "ok"}, "graph": {"status": "ok"}, "storage": {"status": "ok", "disk_free_pct": 32.64}}
```

### 4.2 验收栈 127.0.0.1:8082（新代码 8b3f36f / 小库）

```
$ GET /validation/shapes
  -> 200  17ms  460 chars | FULL_LENGTH=460 chars  SHA256=a3bf4ae6c2ae582d  PARSE=dict  KEYS=shapesDir,files,shapesVersion,namespaces
  shapesDir = /data/shapes
  files = ["core.ttl"]
  shapesVersion = c33943c929040b570b82a5f7d701786c322f57e39577205969296d90b6f0b0a0
  namespaces = [{"namespace": null, "dir": ".", "files": ["core.ttl"], "version": "c33943c929040b570b82a5f7d701786c322f57e39577205969296d90b6f0b0 ...(截断)
$ GET /reasoning/status
  -> 200  5ms  1123 chars | FULL_LENGTH=1123 chars  SHA256=7455177dc66e6ba2  PARSE=dict  KEYS=mode,provider,engine,profile,serviceEnabled,endpoint,available,inferredGraphPrefix,aboxGraphs,shapesDir,pointer,lastJob
  mode = materialize
  provider = robot/EL
  engine = robot
  profile = EL
  serviceEnabled = true
  endpoint = http://reasoner:7879
$ GET /health/dashboard
  -> 200  18ms  5834 chars | FULL_LENGTH=5834 chars  SHA256=d62d17108f34f1a8  PARSE=dict  KEYS=sampledAt,coverage,orphanInstances,shaclViolations,inferenceFailures,migration,readyz,tbox,pointerStatus,ontologyDiff,termsGate,dataSource
  sampledAt = 2026-11-06T23:56:36.839553+00:00
  coverage = {"classes": {"total": 156, "withInstances": 0, "ratio": 0.0, "unlabeled": 0, "error": null, "source": "SPARQL GRAPH <urn:platform: ...(截断)
  orphanInstances = {"count": 0, "error": null, "source": "A-Box：无出边（除 rdf:type/rdfs:label）且无入边的实例"}
  shaclViolations = {"count": null, "conforms": null, "sampledAt": null, "source": "platform.ontology_import（最新导入记录）", "note": "无导入记录，未以 0 代替"}
  inferenceFailures = {"count": 3, "lastJob": {"jobId": "rsn-cc97af80d34f", "kind": "materialize", "state": "failed", "ontologyVersion": "ont-6e81732555 ...(截断)
  migration = {"codeVersion": 40, "dbVersion": 40, "consistent": true, "source": "platform.schema_version MAX(version) vs SUPPORTED_SCHEMA_VERSI ...(截断)
$ GET /readyz
  -> 200  6ms  537 chars | FULL_LENGTH=537 chars  SHA256=014659d11612174f  PARSE=dict  KEYS=status,checks,pointerStatus,warnings,note
  status = ok
  checks = {"database": {"status": "ok"}, "graph": {"status": "ok"}, "storage": {"status": "ok", "disk_free_pct": 32.64}}
```

> 完整响应（含 `FULL_LENGTH` / `SHA256` / 结构化摘要，超大正文显式标记 `[BODY OMITTED]`）见
> `evidence/q_S05.txt`；终端渲染截图见 `screenshots/q_S05.png`。

## 5 结论

**PARTIAL** — reasoner 服务 available=True、SHACL conforms 记录可读；但 aboxGraphs=['urn:platform:graph:abox:main'] 仍只含 abox:main，未包含真实实例所在的 abox:synthetic；inferenceFailures.count=336（历史累计）。验收栈同字段=3（小库）。

R1 文案「最近一次作业可能为 succeeded」被证据反证，本轮以实测 lastJob.state=succeeded 表述。

---
[返回总报告](README.md) · [T0 归档](<_history/2026-11-06_2352/q_S05_SHACL 校验与推理物化.md>)
