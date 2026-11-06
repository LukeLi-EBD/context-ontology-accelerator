# 43 · PROV-O 判定溯源（B-02）

> 文档编号：43 · 日期：2026-11-06 · 性质：B-02 功能交付说明（设计 + 验证）
> 交付提交：`6a2185f`（代码）；文档提交见本轮 docs commit
> 对应台账：`41-借鉴任务编号台账.md` B-02；规格来源：`39-借鉴结论汇总.md` §1.5.4.1
> 前置：B-01 值级溯源（`4daa9dd`）；本轮 schema 27→28

## 1. 目标

把三类"判定"从不可反查变为可反查，并纳入可校验的追加式审计链：

| 判定 | 必须回答 | 埋点 |
|---|---|---|
| 口径判定 | `inference` / `publishable` / `decision_recommendation` 由谁判、依据哪条文本、改前值 | `/answer` 选中指标时；`POST /metrics/{id}/decision` 重判 |
| 规则触发 | 规则 ID、阈值、spec 字段、命中值、阈值出处 | `POST /metrics/{id}/rules` 每次执行 |
| 拒答 | 缺哪层哪项、哪次检索参数（strategy/topK/chunks/packId） | `/answer` 拒答分支 |

只追加：重判产生新 Activity，新结论 `prov:wasDerivedFrom` 指向旧结论。

## 2. 模型（PROV-O）

命名图：`urn:platform:prov`（唯一写入目标）。

| RDF 元素 | 本体表达 |
|---|---|
| 判定动作 | `<urn:platform:prov:activity/act-xxx> a prov:Activity`；`prov:startedAtTime`/`prov:endedAtTime`/`prov:wasAssociatedWith`/`prov:generated`/`prov:type` |
| 被判定对象 | `urn:platform:metric/<metricId>`、`urn:platform:customer/<id>`、`urn:platform:request/<requestId>`，均 `a prov:Entity`，经 `prov:used` 关联 |
| 判定结论 | `<urn:platform:prov:conclusion/act-xxx> a prov:Entity`；`prov:value`（JSON 结论）、`prov:wasGeneratedBy`、`prov:wasAttributedTo`、可选 `prov:wasDerivedFrom` |
| 依据文本 | `<urn:platform:prov:evidence/<sha256[:16]> a prov:Entity`；`prov:value` 原文、`rdfs:seeAlso` 出处引用、`prov:type prov:...:term/evidence` |
| Agent | `<urn:platform:prov:agent/<actor-slug>> a prov:Agent`；系统 `prov:SoftwareAgent` / 人工 `prov:Person` |

依据 Entity 的 `rdfs:seeAlso` 三类来源：

- 口径定义行：`platform.metric_definition#FIN-BANK-002@v3.0`
- 37 号判定书条目：`_design/37-指标口径判定书-v8.md#FIN-BANK-002`
- 规则 spec 字段：`platform.metric_definition#FIN-BANK-002@v3.0.rule_set_json.R03.spec`（另附 `threshold`、`threshold_source`、`observed-values`）

关系四件套全部使用：`used`（对象/依据）、`wasGeneratedBy`（结论）、`wasDerivedFrom`（重判或观测值）、`wasAttributedTo`（结论→Agent）。

## 3. 存储与审计

| 位置 | 内容 |
|---|---|
| `platform.prov_event`（V28） | `event_id`、`activity_id`、`kind`、`metric_id`、`subject_key`、`actor`、`actor_kind`、`conclusion jsonb`、`evidence jsonb`、`payload jsonb`、`prev_event`、`hash`、`created_at` |
| 索引 | `(activity_id)` 唯一、`(kind, subject_key, event_id)`、`(metric_id, event_id)` |
| 只追加 | DB 触发器 `prov_event_append_only_trg`：`DELETE` 直接 `RAISE EXCEPTION`；`UPDATE` 仅允许改 `hash`（链写入在同一事务内完成一次） |
| 哈希链 | 与 `platform.fact_event` 同一算法：`event_body`（不含时间戳的规范化 JSON）+ `prev_hash` + SHA-256；`prev_event` 逐条相连 |
| 校验面 | `GET /prov/verify`（`ok/checked/lastHash/separation`）；`GET /ontology/verify` 增加 `prov` 兄弟块，一次调用可同时校验 ontology 与 prov 两条链 |

> 关于"同一审计链"：fact/ontology/prov 均为**同构的追加哈希链**（相同的 canonical body 与 `prev_hash` 规则），并由同一 verify 面输出；未把 prov 事件塞进 `ontology_event`，避免治理事件与判定事件混表。

## 4. 图隔离（零混写）

写入侧唯一入口 `ProvService.write_triples(graph_iri, triples)`：

```
if graph_iri != "urn:platform:prov": raise E_PROV_GRAPH_MIXING
```

`POST /prov/graph/guard {"graph":"urn:platform:graph:tbox:ont-..."}` 返回 422 `E_PROV_GRAPH_MIXING`。

读侧 `separation()` 双向断言（实测）：

| 指标 | 值 |
|---|---:|
| `provTriples`（`urn:platform:prov` 三元组数，验收后） | 1279 |
| `tboxProvTriples`（T-Box 中 subject 属于 `urn:platform:prov:`） | 0 |
| `provTboxTriples`（PROV 图中 fsldm/T-Box 主体或谓词） | 0 |
| `tboxLegacyProvPredicateTriples`（当前 T-Box 版本既有 `prov:` 谓词，信息项，不参与门禁） | 0（ont-3f57d8ce6636 曾观察到 20，属既有内容） |

说明：T-Box 在 B-02 之前就用 `prov:` 谓词描述本体条目的来源（主体为 `https://w3id.org/fsldm/terms#entry-*`、`review-batch*`），属于既有不可变 T-Box 内容。B-02 的"零混写"断言因此定义为：**判定 PROV 节点绝不进入 T-Box，T-Box 主体绝不进入 PROV 图**；上表后两行为 0。

## 5. 反查接口

| 接口 | 用途 | 返回 |
|---|---|---|
| `GET /prov/decisions?metricId=FIN-BANK-002` | 按指标查判定历史 | 谁判（actor/actorKind）、何时、依据文本、结论、`before`（改前值）、`derivedFrom`、`prevEvent`、`hash` |
| `GET /prov/rules?ruleId=R03` | 按规则 ID 查触发实例 | 规则/阈值/spec 字段/命中值（`observed.dpd`）/客户/层级别/依据 |
| `GET /prov/refusals?requestId=...` 或 `?query=...` | 按请求或问题反查缺口 | 缺失层与项（`missing[]`、`layers[]`）、检索参数（`retrieval.strategy/topK/chunks/packId`）、reasonCode |
| `GET /prov/verify` | 链连续 + 图隔离 | `ok/checked/lastHash/separation` |

写入入口：

| 接口 | 说明 |
|---|---|
| `POST /metrics/{id}/decision` | 显式判定/重判；自动 `wasDerivedFrom` 上一条结论，并回填 `before` |
| `POST /metrics/{id}/rules` | 执行规则后每个命中写一条 Activity |
| `POST/GET /answer` | 选中指标→写 decision；拒答→写 refusal；响应附 `requestId` 与 `prov.activityId` |

## 6. 验证（真实数据）

三类正查（容器内 `test_prov.py`，9/9 通过）：

1. **口径判定**：`FIN-BANK-002` → `publishable=false`、`inference=true`、`decision_recommendation.recommendation.formulaExpr=band(dpd, 30, 6)`；依据含 37 号判定书条目；二次判定 `derivedFrom` 指向首条结论、`prevEvent` 相连、`before.definitionVersion=v3.0`。
2. **规则触发**：`R03`（`dpd >= 61`，阈值 `>=61 天`，L2）；命中值 `dpd=75`、`spec.field=dpd`、`spec.value=61`、客户 `CUST-PROV-001`；依据含 `rule_set_json.R03.spec` 与 `req-test-rule#customer=` 观测值。
3. **拒答**：真实 `/answer` 拒绝"量子纠缠担保品的监管处置口径是什么"，`E_ANSWER_NOT_COVERED`；缺失层 `ontology/terms/metrics`；检索参数 `strategy=lexical, topK=3, chunks=1`；证据 `answerable.missing#ontology/E_LAYER_ONTOLOGY_GAP` 等。

反例（均明确拒绝）：

| 反例 | 结果 |
|---|---|
| 查不存在的判定：`/prov/decisions?metricId=PROV-NOPE` | 404 `E_PROV_SUBJECT_NOT_FOUND` |
| 物理删除：`DELETE /prov/activities/act-x`；DB 直删 | 422 `E_PROV_APPEND_ONLY`；触发器 `... append-only: physical delete refused`，行仍在 |
| 图混写：`POST /prov/graph/guard` 指向 T-Box | 422 `E_PROV_GRAPH_MIXING` |

## 7. 验收与结束态

| 项 | 结果 |
|---|---|
| `tests/test_prov.py` | 9/9 OK |
| 全量单测 | 200 OK（原 191 + 9） |
| `tests/acceptance.ps1` | 43 passed / 0 failed / 0 skipped / 0 degraded |
| `scripts/acceptance-s14.ps1` | 155 passed / 0 failed / 0 skipped |
| PROV 链（验收后） | 69 事件：decision 33 / rule_trigger 21 / refusal 15；`checked=69, ok=true` |
| schema | 28（`V27`→`V28`） |
| 图指针 | `tbox/current=ont-3f57d8ce6636`、`inferred=997` |
| 就绪 | `/readyz=200` |

## 8. 文件清单

| 文件 | 变更 |
|---|---|
| `src/platform_core/prov.py` | 新增：PROV-O 三元组构建、链写入、三类记录、三反查、verify/separation |
| `src/platform_core/sql/V28__prov.sql` | 新增：`platform.prov_event` + 追加式触发器 |
| `src/platform_core/api.py` | 新增 `/metrics/{id}/decision`、`/prov/*`；`/answer` 与 `/metrics/{id}/rules` 埋点；`/ontology/verify` 增加 `prov` 块 |
| `src/platform_core/assembly.py` | `Runtime.prov` 注入 |
| `src/platform_core/adapters/metadata_pg.py` | `SUPPORTED_SCHEMA_VERSION=28` + 迁移注册 |
| `tests/test_prov.py` | 新增：3 正查 + 3 反例 + 链连续 + 双向零混写 |

## 9. 边界

- 不改变既有断言语义、口径门禁与 `answerable` 判定；PROV 写入失败不影响 `/answer` 返回（`prov.error` 会回传）。
- 不做物理清理：测试/验收产生的 PROV 事件永久保留，正是"只追加"的证据。
- 未把 PROV 事件并入 `ontology_event`；采用同构链 + 同一校验面，避免治理与判定混表。
