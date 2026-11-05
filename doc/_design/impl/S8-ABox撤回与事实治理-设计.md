# S8 A-Box 撤回与事实治理 · 设计

> 切片：S8 · 版本：v0.1 · 日期：2026-11-05
> 上游：OQ-30（错误事实无法撤回）、OQ-31（smoke 污染演示库）、04 §5.4（审批/物化）、S4/S5/S6/S7 已验收接口
> 纪律：不做鉴权/指标；不重构已通过部分；无新增第三方依赖。

## 1. 问题、目标与不做

### 1.1 问题

A-Box 是三元组集合，**只有“加”没有“减”**。写同主语同谓词的新值不会让旧值消失，只是让它变成“两个都成立”；
一旦抽取把脏三元组写进 `urn:platform:graph:abox:main`，随后的 SPARQL 查询、`ContextResolver` 召回、
RDFS/OWL 物化都会建立在错误前提上，且没有任何可审计的“这条不再成立”的表达。

### 1.2 目标

1. 撤回是**显式状态变更**，不是覆盖、不是删除三元组后假装没发生。
2. 每条断言带 **来源 / 断言时间 / 状态**，可单条撤回、按来源批量撤回、撤回后回滚。
3. 同一 `(s, p)` 多值时**不静默取最新**：全部返回并标 `conflict`（API 与 UI 都可见）。
4. 撤回立即对 `ContextResolver` 生效；物化重跑后 inferred 图不含该事实的推导。
5. 审计只追加，**撤回不得物理删除审计记录**。

### 1.3 明确不做

- 不做鉴权、审批人身份体系（`actor` 只是字符串，默认 `api`）。
- 不做前端复杂交互（治理面板沿用 S7 原生 JS，只做列表/撤回/恢复/按来源撤回）。
- 不做自动冲突消解、不做“按时间取最新”、不做真值维护（truth maintenance）算法。
- 不做 RDF 具象化（reification）/ 每条断言一个命名图的分片方案（取舍见 §2.2）。

## 2. 方案与取舍

### 2.1 采纳：PG 账本 + A-Box 投影

`platform.fact_assertion` 是事实的**唯一权威账本**；`urn:platform:graph:abox:main`（或测试图）只是
**当前 active 断言的投影**。查询/物化/审计都围绕账本工作：

| 字段 | 含义 |
|---|---|
| `fact_id` | 断言 id（`fact-<12hex>`） |
| `subject_iri` / `predicate_iri` / `object_kind` / `object_value` | 三元组（object 分 `iri`/`literal`） |
| `graph_iri` | 该断言所属命名图（主库或测试图） |
| `source_kind` | `extraction` / `manual` / `import` |
| `source_document_id` / `source_run_id` / `candidate_id` | 来源定位（文档 / 抽取 run / 候选） |
| `state` | `active` / `retracted` / `superseded` |
| `asserted_at` / `updated_at` / `retracted_at` / `retract_reason` | 时间线与撤回理由 |

「撤回」= `state → retracted` 并写 `platform.fact_event`；图里的三元组只有在**同一三元组已无任何 active 断言**
时才被移除（多来源断言同一条时不误删）。「恢复」= `state → active` 并重新插入三元组。审计事件永不删除，
`purge_test` 只清测试断言行。

### 2.2 否掉的方案及理由

| 方案 | 否掉理由 |
|---|---|
| **覆盖写**（同 `(s,p)` 写新值，认为旧值被取代） | 语义上两个值都成立，查询会同时看到脏值与新值；没有“不再成立”的表达，也无法回滚。 |
| **自动 `superseded` / 取 `asserted_at` 最新** | 用户明确要求“不要静默取最新”。平台无法判断哪条为真；自动取最新会把一次抽取错误悄悄变成“事实”。`superseded` 字段保留，但**系统不自动产生**，仅作未来人工治理的保留态；恢复接口拒绝恢复 `superseded`。 |
| **每条断言一个命名图 + 图级元数据** | 图数量随断言线性增长，每次查询要枚举图；撤回=删图，审计信息必须另存，等价于账本但仍多一层图管理。单机版本体不需要。 |
| **RDF reification 表达撤回** | 每条断言膨胀 4 条三元组，SPARQL 过滤复杂，且“谁在何时因何撤回”仍需外部存储；审计不可删的要求无法只靠 RDF 满足。 |
| **物理删除三元组 + 日志文件** | 不可查询、不可恢复、与 PG 事务割裂；无法保证“撤回后 ContextResolver 不再召回”的一致性窗口。 |

### 2.3 冲突规则

- 同一 `(subject, predicate)` 存在 **>1 个不同 object 的 active 断言** → 该对为冲突。
- `GET /facts`、`/facts/conflicts`、`ContextResolver.facts[]` 都返回**全部值**，并对涉及项标
  `conflict: true` 与 `conflictValues: [...]`。
- 不做自动合并、不排序成“最新优先”，UI 以红色 `conflict` 徽标展示。
- 唯一索引 `(s,p,object,source_document,source_run,graph) WHERE state='active'` 只防同源重复，不阻止多值。

### 2.4 依赖

无新增依赖。使用既有 `psycopg`（PG 事务/部分索引）、`rdflib`（字面量/IRI 序列化）、Oxigraph SPARQL。
版本沿用 `_impl/requirements.txt` 的 pin，不引入迁移框架之外的库。

## 3. 与既有链路的关系

| 链路 | 变化 | 保证 |
|---|---|---|
| 审批 `POST /candidates/{id}/approve` | 新增可选 `graph`（默认 `abox:main`），写图后调 `FactLedger.record`，返回 `factId`/`conflict` | 原有响应字段不变，仅新增 |
| `ContextResolver` | 取图事实后先 `filter_retracted`，再 `annotate`（附 `factId/source/status/conflict`） | inferred 图未重跑时也不会召回“已撤回且无其他来源”的事实 |
| 物化 `POST /reasoning/materialize` | 新增可选 `aboxGraphs`（`urn:platform:` IRI 列表）；validate/SHACL 用第一个图 | 未传时行为与 S5 完全一致 |
| 审计 | `fact_event` append-only；`purge_test` 不触碰 | 测试清理后仍可查撤回链 |
| UI 审批页 | 新增“事实治理”面板：状态/来源/冲突徽标、单条撤回/恢复、按来源撤回 | 调用的都是 S8 API，无前端算法 |

## 4. API

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/facts` | 断言：`subject/predicate/object/objectKind/graph/sourceKind/sourceDocumentId/sourceRunId` |
| `GET` | `/facts` | 列表：`state=active|retracted|superseded|all`、`subject`、`predicate`、`sourceDocumentId`、`conflict`、`limit` |
| `GET` | `/facts/conflicts` | 冲突对与全部值 |
| `POST` | `/facts/retract` | 按来源批量撤回：`sourceDocumentId` 或 `sourceRunId`（至少一个） |
| `POST` | `/facts/{id}/retract` | 单条撤回：`reason`、`actor` |
| `POST` | `/facts/{id}/restore` | 回滚：仅 `retracted → active` |
| `GET` | `/facts/{id}` / `/facts/{id}/events` | 断言详情 + 审计链 |

错误码：`E_FACT_BAD_IRI`、`E_FACT_BAD_SOURCE`、`E_FACT_BAD_GRAPH`、`E_FACT_NOT_FOUND`、`E_FACT_STATE`、
`E_FACT_SUPERSEDED`、`E_REASONING_ABOX_GRAPHS`。

## 5. 迁移

`V7__s8.sql`：`platform.fact_assertion`、`platform.fact_event`、active 唯一索引、subject/predicate 与
source_document 部分索引。`SUPPORTED_SCHEMA_VERSION` 7。迁移只加表加索引，不改旧表；失败时平台以
schema 版本错误 fail-fast（沿用 S0 机制）。

## 6. 验收（映射 smoke-s8）

| # | 要求 | 断言 |
|---|---|---|
| 1 | 单条撤回 → 查询与 context 均不再出现、审计有记录 | `facts.retract.single` + `facts.retract.audit` + `facts.context.no_retracted` |
| 2 | 按来源批量撤回 → 计数正确、其他来源不受影响 | `facts.retract.batch` + `facts.retract.batch_scope` + `facts.batch.audit` |
| 3 | 撤回后物化 → inferred 不含其推导 | 先 `facts.materialize.pre` 证有推导，撤回后 `facts.materialize.no_retracted` |
| 4 | 恢复 → 回到撤回前状态 | `facts.restore` + `facts.restore.context` + `facts.restore.materialize` |
| 5 | 冲突 → 两值都在、标 `conflict` 且不崩 | `facts.conflict.visible` + `facts.conflict.endpoint` + `facts.conflict.context` |
| 6 | 撤回不得物理删除审计 | `facts.audit.chain` + `facts.audit.survives_purge`（`purge_test` 后事件仍在） |

## 7. OQ-31：smoke 隔离与演示库纯净

- 所有 smoke 的 A-Box 写入一律使用 `urn:platform:test:<nonce>:sN` 独立图；审批带 `graph`，物化带
  `aboxGraphs`；`finally` 中 `DROP GRAPH` + `FactLedger.purge_test`（审计不删）。
- `tests/acceptance.ps1` 在 smoke 前记录 `urn:platform:graph:abox:main` 三元组数，smoke-s8 之后：
  `after == baseline` 且 `urn:platform:test:` 图计数为 0，断言名 `demo abox purity`。
- 因此验收跑完，演示库 A-Box 与 seed 一致，测试数据不再永久残留。

## 8. 风险与已知边界

- `FactLedger.record` 先写账本再写图；若图写入失败，账本为 `active` 但投影缺三元组（单机内存/网络故障窗口）。
  后续物化只读图，不会自愈；恢复/重放需重插。接受该窗口，不引入 outbox（超范围）。
- `annotate` / `filter_retracted` 每次读取全表 active/retracted（单机演示规模可接受；量大时加 `(subject,predicate)` 索引已就绪）。
- 冲突不阻断物化；冲突事实会同时进入 inferred 推导，需人工治理后再重跑。

## 9. 实施结果（2026-11-05）

- `platform smoke-s8`：**20/20**，覆盖断言 6 类（`facts.assert`、`facts.materialize.pre`、
  `facts.retract.single`、`facts.context.no_retracted`、`facts.retract.batch`、`facts.retract.batch_scope`、
  `facts.materialize.no_retracted`、`facts.restore`、`facts.restore.context`、`facts.restore.materialize`、
  `facts.conflict.visible`、`facts.conflict.endpoint`、`facts.conflict.context`、
  `facts.audit.chain`、`facts.audit.survives_purge`、`facts.cleanup.test_graph` 等）。
- 回归：`smoke-s1..s7` 全绿；`tests/acceptance.ps1` **32/32**（新增 `platform smoke-s8` 与
  `demo abox purity`，原 30 条全部保持）。
- 演示库纯净：`demo abox purity baseline=0 after=0 testGraphs=0 smokeSubjects=0`；本次同时清理了
  S8 之前旧版 smoke 直接写入 `abox:main` 的历史测试三元组，此后 A-Box 只含 seed（本次为 0 条）。
- 修复过程中发现并纠正：`ContextResolver` 构造参数 `facts` 曾覆盖同名方法 `_facts`（改为 `_ledger`）；
  `smoke-s5` 的 `/validation/run` 原先校验 `abox:main`，演示库清空后必然 400，改为校验自己的测试图。
- schema `V7__s8.sql` 已在净室/现有卷上应用，`schema_version=7`。
