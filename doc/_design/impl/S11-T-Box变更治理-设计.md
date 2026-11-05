# S11 T-Box 变更治理 · 设计

> 文档编号：S11 · 状态：已实施 · 日期：2026-11-05
> 上游：`S1-本体存储与版本-设计.md`、`S5-校验与物化-设计.md`、`S10-可逆裁决与审计回放-设计.md`、`_design/10-实施路线图.md`
> 原则：本体能加载、能切指针，但没有「谁能改、改了怎么审、出事怎么回」；本切片只补这条治理链，不改已通过的读写语义。

## 1. 目标与边界

### 做

- 版本生命周期 `draft → proposed → approved → published → superseded`，落 PG（复用 `ontology_version`），每次流转追加 `ontology_event` 审计事件。
- 任何 governed publish **必须**关联 proposal：变更说明、diff、影响面。没有 proposal 的旧路径只保留给 bootstrap/S1 兼容。
- `diff(from, to)` 全部走 Oxigraph SPARQL（`MINUS`/`CONSTRUCT`），输出机器 JSON + Markdown 摘要 + `breaking` 标记。
- 三道发布门禁：SHACL、一致性（ROBOT/ELK，不允许跳过）、breaking 显式确认。
- 发布后切指针并触发物化（RDFS→OWL→SHACL）；物化失败则回滚发布状态与指针。
- `rollbackTo(version)` 只切指针与状态，两个版本的图都保留，任何版本不物理删除。
- 导入 TTL/OWL → 指定命名图；默认 `on_conflict=reject`，绝不静默覆盖。
- 当前版本导出 Turtle + N-Quads；导出再导入后 diff 为空。
- 本体页最小增量：版本列表、提案表单、diff 预览、发布/回滚按钮。

### 不做

- 不做富文本编辑器、不做可视化图编辑、不做鉴权/多用户。
- 不新增依赖：diff 用 SPARQL，Markdown 摘要用字符串拼接，导出用 rdflib 已有序列化。
- 不重构 S1–S10 已通过的读写路径；`ontology.rollback`（S1 语义）保留不动。
- 不做 OQ-45/46（过滤导出与增量重放），留给 S12。

## 2. 数据模型：V10

`V10__s11.sql` 放宽版本状态 CHECK，并新增两张 append-only 表：

```sql
ALTER TABLE platform.ontology_version
  ADD CONSTRAINT ontology_version_status_check
  CHECK (status IN ('draft','proposed','approved','published','superseded',
                    'deprecated','rejected'));
```

| 表 | 关键列 | 用途 |
|---|---|---|
| `ontology_proposal` | `proposal_id`、`version_id`、`against_version`、`change_summary`、`status`、`breaking`、`acknowledged_breaking`、`diff jsonb`、`impact jsonb`、`created_by/at`、`approved_by/at`、`published_at` | 提案、diff 快照、影响面、审批与确认痕迹 |
| `ontology_event` | `event_id bigserial`、`version_id`、`proposal_id`、`action`、`actor`、`reason`、`payload jsonb`、`prev_event`、`hash char(64)`、`created_at` | 与 A-Box 同一套哈希链：`hash=sha256(prev_hash + "\n" + canonical_json(body))` |

事件动作：`imported`、`proposed`、`approved`、`published`、`superseded`、`rolled_back`、`breaking_acknowledged`、`publish_reverted`、`import_conflict_accepted`。
`_append_event` 在事务内取 `pg_advisory_xact_lock(hashtext('platform:ontology:event'))`，保证 `prev_event`/`hash` 串行；`verify_events()` 可离线核对整链。

## 3. 版本生命周期

```
draft ──propose──▶ proposed ──approve──▶ approved ──publish──▶ published
                                                                 │
                                                    rollback / 新版本发布
                                                                 ▼
                                                            superseded
```

- `propose` 只接受 `draft|proposed`，必须给非空 `change_summary`；默认 `against_version=当前指针`。
- `approve` 只接受 `proposed`；已 `published` 再审批 → `E_ONTOLOGY_PROPOSAL_STATUS`。
- `publish` 要求版本 `approved` 且 proposal `approved`，否则 `E_ONTOLOGY_NOT_APPROVED` / `E_ONTOLOGY_PROPOSAL_NOT_APPROVED`。
- `superseded` 只表示「不是当前默认版本」：`GET /ontology/versions/{id}` 仍可读，图不删，`version=` 查询仍可读。
- 发布同一事务内：旧 published → `superseded`（事件 `superseded`）、新版本 → `published`、proposal → `published`、写 `published` 事件、切 `graph_pointer`。

**legacy direct publish**：`publish(version_id)` 不带 proposal 时沿用 S1 路径（不跑门禁、不物化、不看 breaking），仅供 bootstrap 与 S1 smoke 使用；带 proposal（显式或该版本最新提案）即进入 governed 路径。这样启动期 reasoner 未就绪不会把主干打红，也不给正常治理流程留后门。

## 4. diff（SPARQL，不写图比较算法）

`diff(from_version_id, to_version_id)` 在两张命名图上执行：

- `MINUS` 双向计数：`addedTriples`、`removedTriples`；
- 类集合差：`rdf:type owl:Class|rdfs:Class` → `addedClasses` / `removedClasses`；
- 属性集合差：`owl:ObjectProperty|owl:DatatypeProperty|owl:AnnotationProperty|rdf:Property` → `addedProperties` / `removedProperties`；
- `rdfs:domain` / `rdfs:range` 变化：按属性比对新旧值集合 → `domainChanges[]` / `rangeChanges[]`（`from`/`to` 数组）；
- 被删除类的现存实例数：在 A-Box 图上 `SELECT (COUNT(?s) AS ?count)` → `removedClassInstances[]`；
- 可选必填收窄：`owl:minCardinality` / `owl:minQualifiedCardinality` 由无到有 → `property_became_required`。

输出三件：

| 产物 | 内容 |
|---|---|
| JSON `summary` | 上述全部计数与明细，供 UI/CLI/提案快照使用 |
| JSON `breakingItems[]` | `class_removed`、`property_removed`、`domain_narrowed`、`range_narrowed`、`property_became_required` |
| `markdown` | 人类可读片段，直接进 UI 的 diff 预览框 |

`breaking = len(breakingItems) > 0`。判定刻意保守：删除即破坏、domain/range 集合变小即破坏、可选变必填即破坏；不做「实例是否真的违反」的二次推断（那属于一致性检查）。

## 5. 发布门禁

governed publish 依次执行，任一失败即拒绝：

| 门 | 检查 | 失败码 |
|---|---|---|
| ① SHACL | `validator.validate(tbox)`（pySHACL，形状来自 `data/shapes/*.ttl`） | `E_ONTOLOGY_SHACL_FAILED`（409，details 含 violations） |
| ② 一致性 | `reasoner.check_consistency(tbox)`（ROBOT/ELK，无跳过开关） | `E_ONTOLOGY_INCONSISTENT`（409，details 含 explain） |
| ③ breaking 确认 | `diff.breaking && !acknowledge_breaking` | `E_ONTOLOGY_BREAKING`（409，details 含 `breakingItems` 与完整 `diff`） |

门禁依赖不可用（reasoner/validator 未装配）→ `E_ONTOLOGY_GATE_UNAVAILABLE`，不允许静默放行。

发布后流程：

1. 事务内切指针与状态（见 §3）；
2. `materializer()` 串联 RDFS→OWL→SHACL（S5 链路）；
3. 物化失败 → `_restore_after_failed_publish`：新版本回 `approved`、proposal 回 `approved` 并清 `published_at`、旧版本回 `published`、指针复原、追加 `publish_reverted` 事件；抛 `E_ONTOLOGY_MATERIALIZE_FAILED`。

## 6. 回滚与并存

```python
rollback_to(version_id, actor="operator", reason=None)
```

- 拒绝 `draft`（`E_ONTOLOGY_STATUS`）；目标图必须存在。
- 事务内 advisory lock → 当前 published 置 `superseded`（事件 `superseded`）→ 目标置 `published` → 切指针 → 事件 `rolled_back`。
- 目标已是当前指针 → `unchanged=true`，不写事件。
- 可选触发 `materializer()`；物化失败只记 warning，指针留在目标版本（回滚是本意，不因物化失败回退）。
- 不删任何版本行、不删任何命名图；旧版本内容始终可按 `version=` 读回。

## 7. 导入与导出

### 7.1 导入冲突检测

`import_source(path, semver, label, rdf_format=None, on_conflict="reject", graph_iri=None)`：

- 解析后与**当前指针图**按 subject IRI 比较出向三元组集合；同一 IRI 定义不同 → 冲突。
- `on_conflict=reject`（默认）：抛 `E_ONTOLOGY_IMPORT_CONFLICT`，details 为 `{onConflict, conflictCount, conflicts[:50]}`，每条含 `iri`、`existing`、`incoming` 差异摘要；不写版本、不动指针。
- `on_conflict=new_version`：照常建 draft 版本，返回 `conflicts[]`，追加 `import_conflict_accepted` 事件；绝不覆盖原图。
- `graph_iri` 必须 `urn:platform:graph:tbox:` 前缀（`E_ONTOLOGY_BAD_GRAPH`）；已被其他版本占用 → `E_ONTOLOGY_GRAPH_IN_USE`。

### 7.2 导出与往返

`export_version(version_id, format)`：

- `turtle`：rdflib 从命名图导出后序列化；
- `nquads`：逐三元组拼 `<s> <p> <o> <graph> .`（保留命名图标识）。

往返测试：导出 Turtle → 以 `on_conflict=reject` 再导入 → `diff(原版本, 新版本)` 的 `addedTriples/removedTriples` 均为 0、类集合差为空、`breaking=false`。内容哈希一致时导入返回 `skipped=true`（OQ-13 语义不变）。

## 8. 接口与 CLI

| 入口 | 说明 |
|---|---|
| `GET /ontology/versions` | 版本列表 + 当前指针 |
| `GET /ontology/versions/{id}` | 版本详情（状态、semver、图、三元组数、proposals、events） |
| `GET /ontology/versions/{id}/diff?against=` | JSON + markdown + breaking |
| `GET /ontology/versions/{id}/export?format=turtle\|nquads` | 导出当前内容 |
| `POST /ontology/versions/{id}/propose` | `{summary, against?, actor?}` |
| `GET /ontology/proposals?versionId=` | 提案列表 |
| `POST /ontology/proposals/{id}/approve` | 审批 |
| `POST /ontology/publish` | `{versionId, proposalId?, acknowledgeBreaking?}` |
| `POST /ontology/rollback` | `{versionId, reason?}` → `rollback_to` |
| `GET /ontology/events` / `GET /ontology/verify` | 审计链与校验 |

CLI：`platform ontology propose|approve|publish|diff|rollback-to|export|events|verify|proposals`，新增 `--summary/--against/--proposal/--acknowledge-breaking/--on-conflict/--graph-iri/--out/--actor/--reason`；`--format` 支持 `nquads`。`smoke-s11` 子命令进入验收。

manifest：`slice=S11`，capabilities 增 `ontology.propose/approve/diff/publish.governed/rollbackTo/export/audit`。

## 9. UI

本体页新增「T-Box 变更治理」分区（不新增页面）：

- 版本列表：semver / 状态 / 时间 / 说明；
- 提案表单：版本、变更说明、操作者（三字段，最少可用）；
- diff 预览：调 `/diff`，展示 Markdown 摘要与 breaking 项；
- `发布`：带 `acknowledgeBreaking` 复选；
- `回滚`：选中历史版本后调用 `rollbackTo`。

不做富文本编辑、不做可视化图编辑。

## 10. 八条验收映射

| 验收 | 实现证据（`smoke-s11`） |
|---|---|
| ① propose→approve→publish 走通且审计链完整 | `lifecycle.propose` + `lifecycle.publish`（actions ⊇ `imported/proposed/approved/published`，`verify_events().ok`） |
| ② 未 approve 直接 publish 被拒，错误码明确 | `publish.unapproved` → `E_ONTOLOGY_NOT_APPROVED`，指针不动 |
| ③ breaking 未确认被拒、确认后成功 | `breaking.detected` + `breaking.reject`（`E_ONTOLOGY_BREAKING`）+ `breaking.acknowledge`（事件 `breaking_acknowledged`） |
| ④ 一致性失败发布被拒且指针不动 | `consistency.reject` → `E_ONTOLOGY_INCONSISTENT`，指针留在 v4 |
| ⑤ diff 正确识别新增/删除/domain 变化（3 版比对） | `diff.added`（v1→v2：+Gamma/+extra，link domain Alpha→Gamma）+ `diff.removed`（v2→v3：−Gamma/−extra，+Delta） |
| ⑥ rollback 后 `version=` 旧版可读、被回滚版 superseded | `rollback.pointer`（v1 published、v4 superseded、两图三元组 >0、`GET /ontology/versions/v4` 200） |
| ⑦ 导入冲突默认 reject 且给出差异 | `import.conflict_reject`（`conflictCount≥1`，含 Alpha 的差异）+ `import.conflict_new_version`（draft + conflicts） |
| ⑧ 导出→再导入→diff 为空 | `export.roundtrip`（added/removed=0、类集合差空、breaking=false、N-Quads 行数=三元组数） |

补充：`setup.import` 五个最小版本、`http.ontology`/`http.status`（`slice=S11`）、`ui.governance`（页面与脚本控件）、`cleanup.pointer`（恢复测试前指针）。

## 11. 实施结果（2026-11-05）

- `platform smoke-s11`：**18/18**。
- `tests/acceptance.ps1`：**40/40**（新增 smoke-s11）。
- 全量 smoke：s1–s10 17/17、17/17、18/18、22/22、27/27、19/19、26/26、20/20、18/18、22/22。
- `demo abox purity`：baseline=0 after=0 testGraphs=0 smokeSubjects=0。
- `schema_version=10`，`/status` `slice=S11`。
- 测试使用独立命名空间 `urn:platform:smoke:s11:<nonce>:`；结束时只把指针恢复到运行前版本，测试版本图按「不删除任何版本」保留。

## 12. 已知边界

- **legacy direct publish 绕过门禁**：无 proposal 的 `publish` 不跑 SHACL/一致性/breaking，也不触发物化；这是启动期与 S1 兼容所需，正常治理必须带 proposal（可后续在 API 层强制要求 proposal，属新切片决策）。
- **`rollback_to` 与 S1 `rollback` 并存**：前者改指针与状态、不新建版本；后者按 OQ-14 新建版本行。两者语义不同，未合并。
- **breaking 判定是集合规则**：只要 domain/range 变小即判破坏，不判断「现存实例是否真的受影响」；实例数只作为影响面参考（`removedClassInstances`）。
- **diff 只比较默认命名图内的三元组**：不推断等价类、不做空白节点规范化（受 OQ-13 约束）。
- **导入冲突按 subject 出向三元组**：仅比较候选文件与当前指针图，不与全部历史版本比较；冲突明细最多返回 50 条（`conflictCount` 为全量）。
- **导出 N-Quads 的 graph 段**：使用版本自身命名图 IRI，再导入同一版本内容可往返一致；跨图迁移需要显式 `graph_iri`。
- **OQ-45/46 未处理**：过滤导出不可离线自证、增量重放缺席，按用户要求排到 S12。
