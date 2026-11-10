# 09 · platform-core 整合方案 v2（唯一入口收敛）

- 版本：**v2**（2026-11-09）。v1 的「三、丢弃」层作废，v1 结论「部分能整合」同时作废。
- 对象：`packages/platform-core`（原 `platform/`，43,775 非空行）
- 性质：**只写文档，不动代码、不提交、不碰 8080/8082**
- 施工依据：`00-总计划.md`；本文与计划冲突处在 §11 明列，不悄悄改计划

---

## 0. 一页结论

**结论：能整合，而且必须整合；整合的终点是 `platform-core` 目录不存在。**

三句话：

1. **最终形态只有一套**：COA 原生包在跑（`control-plane` / `data-layer` / `metric-service` / `ontology-engine` / `sources` / `context-manager` / `vkg` / `web-app`），`platform-core` 的每一块能力都搬进上述包的具体模块，搬完原文件删除。
2. **137 个 HTTP 端点不保留任何一条**。8 条直接落到 COA 已有 operation；73 条落到新增的 86 个 Smithy operation；56 条是同一件事的重复入口，合并进 operation。`platform-core/web` 的 10 个 HTML 页面全部消失，能力在 `web-app` 找到落点（§5）。
3. **工作量按「搬迁 + 契约扩展 + 功能点落点 + 出口切换/删除核对 + 数据接管」重算：161–237 人日（±40%）**。删除本身只占 10–14 人日，真正的成本是证明搬干净了（§8 闸门）与证明 COA 能接管 8080 的数据（§8.3）。
4. **`platform-core/web` 的原子功能点共 143 条：已具备 37 条、需新增 102 条、纯前端无后端 4 条**（§6.3）。只许合并，不许消失。

**四个阶段的下线路径**：能力搬迁 → 出口切换 → 目录删除 → 实例退役。第 4 步必须最后做，前置是 §8.3 的数据接管判据全绿。

---

## 1. 第一原则（本方案的硬约束）

**COA 是同一个 UI、同一个出入口、统一的功能点。必须坚守。**

| # | 约束 | 本方案的可判定含义 |
|---|---|---|
| P1 | 一个 UI | 只有 `packages/web-app`。`platform-core/web` 10 个页面不是调试工具，是**删**；能力按原子功能点逐条落位（§6.3），**只许合并、不许消失**；验收照表逐条点 |
| P2 | 一个入口 | 所有能力走 COA 契约：`ControlPlaneService`（83 op）+ `DataLayerService`（5 op）+ `OntologyService`（新增，先承载 36 个新 op）。对外**只有一个网关、一个 base URL**；网关之后可以是多个 service（§5.0）。`api.py` 137 个端点**不得作为第二组路由并存**，逐条搬进 operation |
| P3 | 一套契约 | COA 契约没有的能力，用**新增 Smithy operation** 补；不在契约外挂私活（脚本、内部 HTTP、直连库都算私活） |
| P4 | 一套功能点 | 不许两套说法、两套指标口径、两套健康检查。同一能力只有一个 owner operation、一个 UI 路由、一个数据源 |

判定优先级：P1–P4 高于「少改代码」「先跑起来」；与 `00-总计划.md` §3 其余原则冲突时以本节为准。

---

## 2. 事实基线

| 项 | 事实 | 证据 |
|---|---|---|
| 规模 | 43,775 非空行；`api.py` 6,280 行 / **137 个端点**（含 5 组 `/api/*` 与 `/ontology/*` 同义别名）；`ontology_pg.py` 4,420 行 | 目录统计；`api.py` 路由扫描 |
| 适配器 | 17 个文件、约 10,800 行，已按端口写好 | `platform-core/src/platform_core/adapters/` |
| 业务模块 | 20+ 个，指标、文档、抽取、事实账本、溯源、bundle、合成数据、健康、影响、术语、搜索、推理、实体视图、画布 | 同目录 |
| 前端 | `web/` 10 个 HTML（index / browse / answer_panel / entity / search / governance / approvals / documents / ontology / health） | `packages/platform-core/web/` |
| HTTP 入口 | FastAPI `create_app` + CLI `platform_core.cli:main` | `api.py:1736`、`pyproject.toml` |
| 平台自有端口 | `ports.py` 的 `GraphStorePort` / `ObjectStorePort` / `CanvasPort`，带 `manifest()`、返回 dict | `ports.py:26-58` |
| COA 契约 | `ControlPlaneService` 83 op（health 2 / namespace 6 / role 3 / grant 7 / sources 21 / metric 11 / induction 19 / ontology graph 14）+ `DataLayerService` 5 op；合计 88（2026-11-09 按 `^operation ` 与 `@http(` 实测） | `models/src/main/smithy/*.smithy` service 块 |
| COA 前端 | 24 条路由，React + Vite + Cloudscape，dev 5173 | `web-app/src/App.tsx:570-643` |
| **唯一完整数据实例** | **8080：3,066 份文档、6 万级实例断言、已发布版本 610** | 运行实例（用户给定，2026-11-09） |

**判断：成本不在「适配器能不能挂」，而在「每块能力搬到哪个包 + 怎么证明搬干净 + 怎么证明数据接管」。**

---

## 3. 四层清单（第三层已改为「能力迁移」）

### 3.1 第一层：可直接挂端口（原样挂 + 物理搬迁）

适配器逻辑不改，但**文件必须搬出 `platform-core`**，否则删不掉目录。目标落点统一为 `packages/local-providers/src/coa_local_providers/providers/`。

| 模块 | 目标落点 | 动作 | 工作量（人日） | 风险 |
|---|---|---|---|---|
| `adapters/graph_oxigraph.py`（432） | `providers/graph/oxigraph.py` | 原样搬 | 0.5 | 低：探针受 `urn:platform:` 白名单约束 |
| `adapters/graph_fuseki.py`（372） | `providers/graph/fuseki.py` | 原样搬 | 0.5 | 低：只读，无写入 |
| `adapters/vector_pg.py`（255） | `providers/vector/pgvector.py` | 原样搬 | 0.5 | 低 |
| `adapters/search_pg.py`（75） | `providers/search/pg.py` | 原样搬 | 0.2 | 低 |
| `adapters/embedding.py`（500） | `providers/embedding/bge.py` | 原样搬 | 0.5 | 低 |
| `adapters/llm_openai.py`（249） | `providers/llm/openai_compatible.py` | 原样搬 | 0.5 | 中：流式/embed unsupported 语义保留 |
| `adapters/metadata_pg.py`（320） | `providers/metadata/pg.py` | 原样搬 | 0.5 | 低 |
| `adapters/object_fs.py`（151） | `providers/object/fs.py` | 原样搬 | 0.3 | 低 |
| `adapters/object_pg.py`（35）+ `object_layered.py`（489） | `providers/object/pg.py`、`layered.py` | 原样搬 | 1–1.5 | 中：依赖 `platform.blob` 表 |
| `adapters/canvas_disabled.py`（47） | `providers/canvas/disabled.py` | 原样搬 | 0.2 | 低 |
| `adapters/ontology_pg.py`（4,420） | **不在此层**：进 `ontology-engine`，见 §3.2 | 改造 | — | 高 |
| 引用改写 | 全部 `import platform_core` → 新包路径 | 胶水 | 2–3 | 中：含测试与 entry point |
| **小计** | | | **6–9** | |

### 3.2 第二层：逻辑对、形状不对，改造后才能挂

| 模块 | 目标落点（具体到包/模块） | 改造动作 | 工作量 | 风险 |
|---|---|---|---|---|
| `adapters/ontology_pg.py`（4,420） | `packages/ontology-engine/src/coa_ontology/stores/pg/` | 加 ACL，把 `OntologyStore` 的读写/版本/事务映射到 `coa_ontology.stores` 契约；只做形状与错误码转换 | 10–14 | **高**：单文件最大未知量，先做 2–3 人日 spike |
| `metrics.py` + `metric_compiler.py` | `metric-service/src/coa_metrics/domain/`、`compiler/` | 定义 CRUD 删除（见 §3.4），只保留编译与口径校验，接 `CreateMetric/ValidateMetric` 的应用服务 | 3–5 | 中：字段与 `MetricDefinition` 对齐 |
| `metric_facts.py` | `metric-service/src/coa_metrics/observations/` | 事实投影 → 观测值，写路径接 `GetMetricObservations`/`ComputeMetric` | 4–6 | 中：口径与 COA 窗口/粒度一致 |
| `rules.py`（263） | `metric-service/src/coa_metrics/rules/` | 规则执行器保留，IO 改端口、错误改 `PortError` | 1–2 | 低 |
| `documents.py` + `importer.py` + `parsers.py` | `sources/src/coa_sources/documents/` | 用 `ObjectStorePort` + `MetadataStorePort` 替换 platform `Runtime`；切块模型对齐 `Chunk` | 6–9 | 中：切块策略与 chunkId 稳定性 |
| `search.py`（651） | `context-manager/src/coa_serve/retrieval/rrf.py` | 只迁 RRF/融合算法，服务形态删除；对外由 `KBSearch` 承担 | 4–6 | 中：排序口径与 `KBSearch` 一致 |
| `answerable.py` | `context-manager/src/coa_serve/answerability/` | 覆盖度预检迁入，接 `CheckAnswerable` | 3–5 | 低 |
| `entity_view.py` | `ontology-engine/src/coa_ontology/entity/view.py` | 主语聚合视图，接 `GetEntity` | 2–3 | 低 |
| `validation.py`（230） | `ontology-engine/src/coa_ontology/validation/shacl_gate.py` | 复用现有 SHACL 入口，补报告格式；不另起 shapes 加载器 | 2–3 | 低 |
| `extraction.py`（697） | `ontology-engine/src/coa_ontology/extraction/` | 候选生成迁入；审批状态由 `control-plane` 的新 operation 承载 | 5–7 | 中：权限接 `IdentityPort` |
| `facts.py`（1,418） | `ontology-engine/src/coa_ontology/facts/ledger.py` | A-Box 账本：断言表 + 活跃投影 + 幂等重放 | 7–10 | 中：幂等与重放需真跑 |
| `prov.py`（855） | 拆两处：`metric-service/src/coa_metrics/provenance/`（决策/规则活动）+ `ontology-engine/src/coa_ontology/provenance/`（实体溯源） | 统一 PROV 图，禁止两套活动表 | 6–8 | 中：活动量与索引 |
| `bundle.py`（2,016） | `ontology-engine/src/coa_ontology/bundle/` | 导出/校验/导入三段，走 `ObjectStorePort` | 9–13 | 高：跨版本兼容 |
| `datagen.py`（2,172）+ `datagen_abox.py` | `sources/src/coa_sources/synthetic/` | 按 live schema 生成，不写生产库；入口改为 operation 触发的作业 | 7–10 | 中：schema 漂移 |
| `healthboard.py`（938） | `control-plane/src/coa_control_plane/health/` | 跨上下文只读视图，统一由 `GetSystemHealth` 输出；禁止第二套健康检查 | 4–6 | 低 |
| `impact.py`（651） | `ontology-engine/src/coa_ontology/impact/` | 版本 diff + 影响面，接 `AnalyzeOntologyImpact` | 4–6 | 中：依赖版本模型 |
| `canvas_simple.py`（710）+ `canvas_full.py`（1,617） | `ontology-engine/src/coa_ontology/canvas/` | 先迁 simple 作为唯一实现，full 的算法折进同一模块；不保留两套 | 5–8 | 中高：性能与限制 |
| `termgov.py` + `termgate.py` + `termlex.py` | `ontology-engine/src/coa_ontology/terms/` | 术语治理、发布 gate、覆盖率/冲突报告 | 6–8 | 中：与发布流程耦合 |
| `reasoning.py`（263）+ `reasoner_hermit/robot.py` | `ontology-engine/src/coa_ontology/reasoning/` | 先 RDFS/SHACL；HermiT/ROBOT 作为可选 profile，需 JVM | 4–6 | 高：镜像体积 |
| `ontology_init.py` / 生命周期 | `ontology-engine/src/coa_ontology/lifecycle/` | 初始化/发布状态机迁入，owner 唯一 | 3–5 | 中：避免两个发布源 |
| **小计** | | | **88–126** | |

### 3.3 第三层：能力迁移（原「丢弃」层作废）

**规则**：本节每条都必须有落点——目标包/模块、目标 operation、目标 UI 路由。没有落点的条目不允许存在。

| 能力 | 平台模块 | 目标包/模块 | 目标 operation | 目标 UI 路由 | 工作量 |
|---|---|---|---|---|---|
| 指标定义/编译/观测 | `metrics.py`、`metric_compiler.py`、`metric_facts.py` | `metric-service` | `CreateMetric`…`GetMetricObservations`、`ComputeMetric` | `/namespaces/:namespaceId/metrics`、`/metrics/:metricName` | 7–11 |
| 指标规则与判定 | `rules.py` | `metric-service/rules` | `ExecuteMetricRules`、`RecordMetricDecision` | `/namespaces/:namespaceId/metrics/:metricName`（面板） | 1–2 |
| 指标报告 | `api.py` 报告段 | `metric-service/report` | `GetMetricReportManifest`、`ListMetricFamilies` | 新增 `/namespaces/:namespaceId/metrics/reports` | 3–5 |
| 文档摄入 | `documents.py`、`importer.py`、`parsers.py` | `sources/documents` | `UploadDocument`…`ExtractDocumentFacts` | 新增 `/namespaces/:namespaceId/documents` | 6–9 |
| 抽取审批 | `extraction.py` | `ontology-engine/extraction` + `control-plane` 审批 | `ListFactCandidates`、`ApproveFactCandidate`、`RejectFactCandidate` | 新增 `/namespaces/:namespaceId/approvals` | 5–7 |
| A-Box 账本 | `facts.py` | `ontology-engine/facts` | `ListFacts`…`ResolveFactConflicts` | `/namespaces/:namespaceId/ontology/graph`（事实页签） | 7–10 |
| 值级溯源 | `prov.py` | `metric-service/provenance` + `ontology-engine/provenance` | `ListMetricDecisions`…`GetEntityProvenance` | `/namespaces/:namespaceId/ontology/entities/:entityId` | 6–8 |
| 本体版本/发布 | `ontology_init.py`、`api.py` 版本段 | `ontology-engine/lifecycle` | `ListOntologyVersions`…`RollbackOntology` | `/namespaces/:namespaceId/ontology` | 6–9 |
| 治理提案/审批 | `api.py` governance 段 | `ontology-engine/governance` | `ProposeOntologyVersion`、`ReviewOntologyProposal`、`ListOntologyTransitions` | 新增 `/namespaces/:namespaceId/governance` | 4–6 |
| 迁移 bundle | `bundle.py` | `ontology-engine/bundle` | `ExportBundle`、`InspectBundle`、`ImportBundle` | `/namespaces/:namespaceId/governance`（bundle 面板） | 9–13 |
| 合成数据 | `datagen.py`、`datagen_abox.py` | `sources/synthetic` | `GenerateSyntheticData`（派生自 `ExtractDocumentFacts` 作业模型，若不需要可并入） | `/namespaces/:namespaceId/sources`（生成入口） | 7–10 |
| 健康看板 | `healthboard.py` | `control-plane/health` | `GetSystemHealth`（扩展字段） | `/system-health` | 4–6 |
| 影响分析 | `impact.py` | `ontology-engine/impact` | `AnalyzeOntologyImpact` | `/namespaces/:namespaceId/ontology`（影响面板） | 4–6 |
| 术语治理 | `termgov.py` 等 | `ontology-engine/terms` | `ListTerms`、`GetTermCoverage`、`DiffTerms`、`ImportTerms`、`ListTermChecks`、`GetTermGate` | 新增 `/namespaces/:namespaceId/ontology/terms` | 6–8 |
| 画布 | `canvas_simple.py`、`canvas_full.py` | `ontology-engine/canvas` | `GetCanvasManifest`、`GetCanvasSubgraph` | 新增 `/namespaces/:namespaceId/ontology/canvas` | 5–8 |
| 实体视图 | `entity_view.py` | `ontology-engine/entity` | `GetEntity` | `/namespaces/:namespaceId/ontology/entities/:entityId` | 2–3 |
| 问答覆盖度 | `answerable.py` | `context-manager/answerability` | `CheckAnswerable`、`GetAnswerQuality` | `/playground` | 3–5 |
| 检索融合 | `search.py` | `context-manager/retrieval` | `KBSearch`（补 `mode`） | `/playground` | 4–6 |
| 推理/校验 | `reasoning.py`、`validation.py` | `ontology-engine/reasoning`、`validation` | `MaterializeReasoning`、`GetReasoningStatus`、`RunValidation`、`GetOntologyShapes` | `/namespaces/:namespaceId/ontology`（高级页签） | 6–9 |
| 数据字典/目录 | `api.py` catalog 段 | `sources/catalog` | `ListDictionaries`…`BindDictionary` | `/namespaces/:namespaceId/sources/:sourceId` | 4–6 |
| 图浏览/查询 | `api.py` browse 段 | `ontology-engine/graph/browse` | `GetOntologyTree`、`ListStatements`、`FindLinks`、`FindGraphPath` | `/namespaces/:namespaceId/ontology/graph` | 4–6 |
| UI BFF `/ui/api/*` | `api.py` 7 条 | **不迁**：`web-app` 直连契约 | 复用 `GetOntologyOverview`/`GetOntology`/`GraphSearch`/`GraphTraverse`/`GetEntity`/`ListFactCandidates`/`KBSearch` | 对应各页 | 0.5 |
| **小计** | | | | | **≈88–129（与 §3.2 重叠部分不重复计）** |

> §3.2 与 §3.3 是同一批工作的两个视角：§3.2 看「形状改造成本」，§3.3 看「落点」。**总量只按 §6 的工作量表计一次。**

### 3.4 第四层：纯重复实现（唯一允许「删」的类别）

| 文件/模块 | 与谁重复 | COA 的那一份在哪 | 删除前置 |
|---|---|---|---|
| `ports.py`（159） | 端口定义 | `packages/coa-ports/src/coa_ports/`（13 端口 + DTO + `PortError`） | 所有 import 已改到 `coa_ports` |
| `assembly.py`（226） | 组合根 | `packages/coa-runtime/src/coa_runtime/registry.py` + `catalog.py` | 每个 provider 已登记且真跑通 |
| `metrics.py` 的定义 CRUD 段 | 指标定义管理 | `metric-service` 的 `CreateMetric/GetMetric/ListMetrics/UpdateMetric/DeleteMetric` | 定义页在 `web-app` 可用 |
| `ontology_init.py` / 发布生命周期中的初始化段 | 本体上传/拉取 | `ontology-engine` + `UploadOntology`/`FetchOntology`/`PublishOntology` | 版本页在 `web-app` 可用 |
| `search.py` 作为独立 HTTP 服务 | 检索 | `context-manager` + `KBSearch` | `/search` 流量切换完成 |
| `webui.py`（397）+ `web/*.html`（10） | 前端 | `packages/web-app`（24 路由） | §5 每个页面能力有路由落点 |
| `api.py` 的 `/ui/api/*`（7） | UI BFF | 同左，直连契约 | 7 条能力均已在 `web-app` 走 operation |
| `cli.py`（950） | 启动/运维入口 | `coa-x up` → `docker compose -f deploy/local/compose.yml` | compose 入口可用 |
| `validation.py` 中的 shapes 加载副本 | SHACL 校验 | `ontology-engine` 现有校验入口 | `RunValidation` 真跑一次 |
| `smoke_s*.py`、`bench_embed.py`、`smoke_embed.py` | 验收脚本 | 迁 `scripts/acceptance/`（不在产品路径） | 迁移后不进镜像 |
| **小计（删除核对，不含搬迁）** | | | **3–5** |

**没有「不建议整合但保留」的条目。** v1 的「降级为调试工具」作废：调试由 `scripts/acceptance/` 与测试承担，不靠保留第二套产品界面。

---

## 4. 137 个端点 → COA operation（核心交付）

### 4.1 分类统计

| 分类 | 行数 | 含义 |
|---|---|---|
| 已有 | 8 | COA 契约已有对应 operation（`/search` 需补 `mode` 字段） |
| 需扩展 | 73 | 能力保留但契约没有 → 新增 86 个 operation（含 13 个「可合并」行的合并目标） |
| 可合并 | 56 | 同一件事的多个入口（含 5 组 `/api/*` 别名） → 收敛为一个 operation |
| **合计** | **137** | 与 `api.py` 路由扫描数一致 |

### 4.2 健康与状态（9）

| 平台端点 | 分类 | COA operation | 说明 |
|---|---|---|---|
| `GET /healthz` | 可合并 | `HealthCheck` | 与 `/readyz` 合一，输出加 `ready` |
| `GET /readyz` | 可合并 | `HealthCheck` | |
| `GET /status` | 可合并 | `GetSystemHealth` | |
| `GET /` | 可合并 | —（UI） | HTML 首页，落 `web-app` `/` |
| `GET /health/dashboard` | 可合并 | `GetSystemHealth` | 看板字段并入 |
| `GET /health/ontology-diff` | 需扩展 | `GetOntologyDiff` | |
| `GET /health/ontology-diff/flow` | 可合并 | `GetOntologyDiff` | `includeFlow=true` |
| `GET /health/ontology-snapshot` | 需扩展 | `GetOntologySnapshot` | |
| `GET /metrics-readiness` | 需扩展 | `GetMetricReadiness` | |

### 4.3 文档摄入（9）

| 平台端点 | 分类 | COA operation | 说明 |
|---|---|---|---|
| `POST /documents` | 需扩展 | `UploadDocument` | |
| `GET /documents` | 需扩展 | `ListDocuments` | |
| `GET /documents/{document_id}` | 需扩展 | `GetDocument` | |
| `GET /documents/{document_id}/chunks` | 需扩展 | `ListDocumentChunks` | |
| `GET /documents/{document_id}/source` | 需扩展 | `DownloadDocument` | 原始字节，`ObjectStorePort` |
| `GET /imports/batches` | 可合并 | `ListIngestionRuns` | `kind=BATCH` |
| `GET /imports/items` | 可合并 | `ListIngestionRuns` | `kind=ITEM` |
| `POST /documents/{document_id}/index` | 需扩展 | `StartDocumentIndex` | |
| `POST /documents/{document_id}/extract` | 需扩展 | `ExtractDocumentFacts` | |

### 4.4 检索与问答（8）

| 平台端点 | 分类 | COA operation | 说明 |
|---|---|---|---|
| `GET /search` | 已有（补字段） | `KBSearch` | 需加 `mode=hybrid\|vector\|lexical` |
| `GET /answerable` | 可合并 | `CheckAnswerable` | 与 POST 合一 |
| `POST /answerable` | 可合并 | `CheckAnswerable` | |
| `GET /answer` | 已有 | `Query` | GET 参数映射到 `Query` 输入 |
| `POST /answer` | 已有 | `Query` | 策略映射 `mode`/`strategy` |
| `GET /answerable/panel` | 可合并 | `CheckAnswerable` | `includePanel=true` |
| `GET /answer/quality` | 需扩展 | `GetAnswerQuality` | |
| `POST /context/resolve` | 需扩展 | `ResolveContext` | |

### 4.5 指标（14）

| 平台端点 | 分类 | COA operation | 说明 |
|---|---|---|---|
| `GET /metrics` | 已有 | `ListMetrics` | |
| `GET /metrics/{metric_id}` | 已有 | `GetMetric` | `metric_id` 映射 `name` |
| `GET /metrics/{metric_id}/output` | 需扩展 | `GetMetricObservations` / `ComputeMetric` | 按 `compute` 分流 |
| `GET /metrics/{metric_id}/computations` | 需扩展 | `ListMetricComputations` | |
| `POST /metrics/{metric_id}/rules` | 需扩展 | `ExecuteMetricRules` | |
| `POST /metrics/{metric_id}/decision` | 需扩展 | `RecordMetricDecision` | |
| `GET /metrics/{metric_id}/compute` | 可合并 | `ComputeMetric` | |
| `GET /metrics/report/manifest` | 需扩展 | `GetMetricReportManifest` | |
| `GET /metrics/report/manifest.csv` | 可合并 | `GetMetricReportManifest` | `format=CSV` |
| `GET /metrics/report/families` | 需扩展 | `ListMetricFamilies` | |
| `GET /metrics/report/families/{family_id}` | 需扩展 | `GetMetricFamily` | |
| `GET /browse/metrics` | 可合并 | `ListMetrics` | `view=browse` |
| `GET /browse/metrics/{metric_id}` | 可合并 | `GetMetric` | |
| `GET /browse/metrics/{metric_id}/card` | 可合并 | `GetMetric` | `view=card` |

### 4.6 溯源（7）

| 平台端点 | 分类 | COA operation | 说明 |
|---|---|---|---|
| `GET /prov/decisions` | 需扩展 | `ListMetricDecisions` | |
| `GET /prov/rules` | 需扩展 | `ListRuleTriggers` | |
| `GET /prov/refusals` | 需扩展 | `ListRefusals` | |
| `GET /prov/verify` | 需扩展 | `GetProvenanceIntegrity` | |
| `POST /prov/graph/guard` | 可合并 | `GetProvenanceIntegrity` | `checkGraph` |
| `DELETE /prov/activities/{id}` | 可合并 | `GetProvenanceIntegrity` | 反例测试；不可变由 `immutable=true` 表达 |
| `GET /entity/provenance` | 需扩展 | `GetEntityProvenance` | |

### 4.7 事实账本与候选（18）

| 平台端点 | 分类 | COA operation | 说明 |
|---|---|---|---|
| `GET /browse/facts` | 需扩展 | `SampleFactRows` | |
| `GET /source/resolve` | 需扩展 | `ResolveSourceRef` | |
| `GET /facts` | 需扩展 | `ListFacts` | |
| `GET /facts/conflicts` | 需扩展 | `ListFactConflicts` | |
| `POST /facts/conflicts/resolve` | 可合并 | `ResolveFactConflicts` | `action=RESOLVE` |
| `POST /facts/conflicts/undo` | 可合并 | `ResolveFactConflicts` | `action=UNDO` |
| `POST /facts/conflicts/unmerge` | 可合并 | `ResolveFactConflicts` | `action=UNMERGE` |
| `POST /facts/conflicts/batch` | 可合并 | `ResolveFactConflicts` | `action=BATCH` |
| `POST /facts` | 需扩展 | `CreateFacts` | |
| `POST /facts/retract` | 可合并 | `RetractFacts` | 批量 |
| `GET /facts/{fact_id}` | 需扩展 | `GetFact` | |
| `POST /facts/{fact_id}/retract` | 可合并 | `RetractFacts` | 单条 |
| `POST /facts/{fact_id}/restore` | 需扩展 | `RestoreFact` | |
| `GET /facts/{fact_id}/events` | 需扩展 | `ListFactEvents` | |
| `GET /facts/events/export` | 可合并 | `ListFactEvents` | `format=NDJSON` |
| `GET /candidates` | 需扩展 | `ListFactCandidates` | |
| `POST /candidates/{id}/approve` | 需扩展 | `ApproveFactCandidate` | |
| `POST /candidates/{id}/reject` | 需扩展 | `RejectFactCandidate` | |

### 4.8 本体版本与治理（34）

| 平台端点 | 分类 | COA operation | 说明 |
|---|---|---|---|
| `GET /ontology/versions` | 需扩展 | `ListOntologyVersions` | |
| `GET /ontology/versions/{id}` | 需扩展 | `GetOntologyVersion` | doc 85 已规划，未落地 |
| `GET /ontology/versions/{id}/diff` | 需扩展 | `DiffOntologyVersions` | |
| `GET /ontology/versions/{id}/export` | 需扩展 | `ExportOntologyVersion` | |
| `POST /ontology/versions/{id}/propose` | 需扩展 | `ProposeOntologyVersion` | |
| `GET /ontology/proposals` | 需扩展 | `ListOntologyProposals` | |
| `POST /ontology/proposals/{id}/approve` | 可合并 | `ReviewOntologyProposal` | `decision=APPROVE` |
| `POST /ontology/publish` | 需扩展 | `PublishOntology` | |
| `POST /ontology/rollback` | 需扩展 | `RollbackOntology` | |
| `GET /ontology/events` | 需扩展 | `ListOntologyEvents` | |
| `GET /ontology/verify` | 需扩展 | `VerifyOntology` | |
| `POST /governance/proposals` | 可合并 | `ProposeOntologyVersion` | `target=GOVERNANCE` |
| `GET /governance/proposals` | 可合并 | `ListOntologyProposals` | |
| `GET /governance/proposals/{id}` | 需扩展 | `GetOntologyProposal` | |
| `POST /governance/proposals/{id}/approve` | 可合并 | `ReviewOntologyProposal` | |
| `POST /governance/proposals/{id}/reject` | 可合并 | `ReviewOntologyProposal` | |
| `POST /governance/publish` | 可合并 | `PublishOntology` | |
| `GET /governance/rollback/plan` | 可合并 | `RollbackOntology` | `planOnly=true` |
| `POST /governance/rollback-to` | 可合并 | `RollbackOntology` | `targetVersionId` |
| `POST /governance/rollback` | 可合并 | `RollbackOntology` | |
| `POST /governance/bundle/export` | 需扩展 | `ExportBundle` | |
| `GET /governance/bundle/inspect` | 需扩展 | `InspectBundle` | |
| `POST /governance/bundle/import` | 需扩展 | `ImportBundle` | |
| `GET /governance/events` | 可合并 | `ListOntologyEvents` | |
| `POST /ontology/import` | 可合并 | `ImportOntology` | 与 `/api/*` 别名合一 |
| `POST /api/ontology/import` | 可合并 | `ImportOntology` | 别名，删 |
| `GET /ontology/imports/{id}` | 可合并 | `GetOntologyImport` | |
| `GET /api/ontology/imports/{id}` | 可合并 | `GetOntologyImport` | 别名，删 |
| `POST /ontology/imports/{id}/publish` | 可合并 | `PublishOntologyImport` | |
| `POST /api/ontology/imports/{id}/publish` | 可合并 | `PublishOntologyImport` | 别名，删 |
| `PUT /ontology/shapes` | 可合并 | `PutOntologyShapes` | |
| `PUT /api/ontology/shapes` | 可合并 | `PutOntologyShapes` | 别名，删 |
| `GET /ontology/shapes` | 可合并 | `GetOntologyShapes` | |
| `GET /api/ontology/shapes` | 可合并 | `GetOntologyShapes` | 别名，删 |

### 4.9 推理与校验（4）

| 平台端点 | 分类 | COA operation | 说明 |
|---|---|---|---|
| `POST /reasoning/materialize` | 需扩展 | `MaterializeReasoning` | |
| `GET /reasoning/status` | 需扩展 | `GetReasoningStatus` | |
| `POST /validation/run` | 需扩展 | `RunValidation` | |
| `GET /validation/shapes` | 可合并 | `GetOntologyShapes` | 同一份 shapes |

### 4.10 UI BFF（7，全部退役）

| 平台端点 | 分类 | COA operation | 说明 |
|---|---|---|---|
| `GET /ui/api/overview` | 可合并 | `GetOntologyOverview` | `web-app` 直连 |
| `GET /ui/api/ontology` | 可合并 | `GetOntology` | |
| `GET /ui/api/entities` | 可合并 | `GraphSearch` | |
| `GET /ui/api/neighbors` | 可合并 | `GraphTraverse` | |
| `GET /ui/api/entity` | 可合并 | `GetEntity` | 新增 op |
| `GET /ui/api/candidates` | 可合并 | `ListFactCandidates` | |
| `GET /ui/api/search` | 可合并 | `KBSearch` | |

### 4.11 影响与证据（4）

| 平台端点 | 分类 | COA operation | 说明 |
|---|---|---|---|
| `GET /ontology/impact` | 需扩展 | `AnalyzeOntologyImpact` | |
| `GET /ontology/impact/export` | 可合并 | `AnalyzeOntologyImpact` | `format=EXPORT` |
| `GET /ontology/evidence` | 需扩展 | `ListOntologyEvidence` | |
| `GET /ontology/evidence/{id}/download` | 需扩展 | `DownloadOntologyEvidence` | |

### 4.12 术语治理（6）

| 平台端点 | 分类 | COA operation | 说明 |
|---|---|---|---|
| `GET /ontology/terms/coverage` | 需扩展 | `GetTermCoverage` | |
| `POST /ontology/terms/diff` | 需扩展 | `DiffTerms` | |
| `POST /ontology/terms/import` | 需扩展 | `ImportTerms` | |
| `GET /ontology/terms/checks` | 需扩展 | `ListTermChecks` | |
| `GET /ontology/terms/gate` | 需扩展 | `GetTermGate` | |
| `GET /browse/terms` | 需扩展 | `ListTerms` | |

### 4.13 图浏览与画布（8）

| 平台端点 | 分类 | COA operation | 说明 |
|---|---|---|---|
| `GET /browse/ontology/tree` | 需扩展 | `GetOntologyTree` | |
| `GET /browse/ontology/instances` | 已有 | `GraphSearch` | |
| `GET /browse/triples` | 需扩展 | `ListStatements` | |
| `GET /browse/sparql` | 已有 | `Query` | SPARQL 直查 |
| `GET /browse/links` | 需扩展 | `FindLinks` | |
| `GET /browse/path` | 需扩展 | `FindGraphPath` | |
| `GET /browse/canvas/manifest` | 需扩展 | `GetCanvasManifest` | |
| `GET /browse/canvas/full` | 需扩展 | `GetCanvasSubgraph` | |

### 4.14 数据字典与目录（6）

| 平台端点 | 分类 | COA operation | 说明 |
|---|---|---|---|
| `GET /catalog/dictionaries` | 需扩展 | `ListDictionaries` | |
| `GET /catalog/dictionaries/{table}` | 需扩展 | `GetDictionary` | |
| `POST /catalog/dictionaries/refresh` | 需扩展 | `RefreshDictionaries` | |
| `GET /catalog/dictionaries/views/{view}` | 需扩展 | `GetDictionaryView` | |
| `GET /catalog/dictionaries/comment-coverage` | 需扩展 | `GetDictionaryCommentCoverage` | |
| `POST /catalog/dictionaries/bind` | 需扩展 | `BindDictionary` | |

### 4.15 治理流转（3）

| 平台端点 | 分类 | COA operation | 说明 |
|---|---|---|---|
| `POST /governance/proposals/{id}/review` | 可合并 | `ReviewOntologyProposal` | |
| `GET /governance/proposals/{id}/transitions` | 可合并 | `ListOntologyTransitions` | |
| `GET /governance/versions/{id}/transitions` | 可合并 | `ListOntologyTransitions` | `subjectType=VERSION` |

### 4.16 不做等价物（明确不迁的旧语义）

以下三条 platform 端点**不进入 COA 契约**，不新增对应的 GET operation。它们是 platform 的旧语义（用 HTTP 方法承载查询），为兼容它们给契约加 GET 属于让旧系统污染新契约，故明确不做。

| 平台端点 | 原映射（作废） | 不做的理由 | 迁移方式（web-app 侧） |
|---|---|---|---|
| `GET /search` | `KBSearch` | 检索带查询体、过滤器、分页 token，GET 只能拼串 | 改调 `KBSearch`（`POST /namespaces/{ns}/kb/search`） |
| `GET /answer` | `Query` | 问答输入多字段，GET 无法承载；且与 `POST /answer` 重复 | 改调 `Query`（`POST /namespaces/{ns}/query`） |
| `GET /browse/sparql` | `Query` | SPARQL 直查是执行语义，不是读取资源；把查询串放 URL 会漏进日志与代理 | 改调 `Query`（`POST`，`strategy=nl_to_sparql`）或 `TranslateSPARQL`（`POST`，预览）；**不保留任意 SPARQL 串直查入口** |

落地要求：

1. 迁移方式是 **web-app 改用 POST 语义**：`platform-core/web` 的 search / answer / browse-sparql 三个页面搬迁时，只能接上表的 POST operation，不得为旧 GET 新增调用点或兼容层。
2. **旧 GET 随 M3b 出口切换、`platform-core` 目录退役一起消失**，不设过渡期、不做别名。
3. 2026-11-10 核查：`packages/web-app/src` 下对 `/search`、`/answer`、`/browse/sparql` 三个路径的引用为 **0**，无待改调用点。

---

## 5. 新增 operation 规格（86 个，派活材料）

通用：所有 op 按 §5.0 的归属分挂 `ControlPlaneService` / `DataLayerService` / `OntologyService`（`models/src/main/smithy/` 对应领域文件），路径前缀 `/namespaces/{namespaceId}`；通用错误 `ValidationError` / `InternalServerError` / `ServiceUnavailableError`，下表只列**额外**错误。`Content` 一律 `base64` 或 `downloadUrl` 二选一，禁止在 operation 里透出密钥。

### 5.0 新增 operation 的 service 归属（决策记录）

2026-11-09 负责人拍板：**「一个入口」= 对外一个网关、一个 base URL，不等于塞进同一个 Smithy service**。86 个新增 operation 按限界上下文分挂三套契约；拆分只改 Smithy service 归属，**不改变 HTTP 路径**，对外仍是同一个 base URL。

| 目标 service | 新增 op 数 | 边界 |
|---|---:|---|
| `ControlPlaneService` | 32 | 命名空间、数据源、权限、审批、指标定义、A-Box 账本治理、数据字典 |
| `DataLayerService` | 18 | 查询、检索、图遍历、指标计算、回答与溯源读取 |
| `OntologyService`（新增） | 36 | 本体归纳、提案、评审、发布、回滚、术语、形状、迁移包、推理与校验 |

#### 5.0.1 临时归属：向量检索两 op（记账，不是定论）

已落地的 `GetEntityEmbeddings`、`SearchEmbeddings` **当前挂在 `ControlPlaneService`**，属于**临时归属**，原因只有一个：仓库尚无 `OntologyService`，为它们单开一套 service 会把「先能跑」变成「先分裂」。

- **迁移触发条件（硬性）**：本体那 36 个 op 开工建 `OntologyService` 时，**同一次改动内**把这两 op 一并迁入 `OntologyService`，不留第二次迁移。
- **迁移范围**：`models/src/main/smithy/embeddings.smithy` 的 `use` 与 `control-plane.smithy` 的 `operations` 列表两处归属；HTTP 路径不变（`/namespaces/{namespaceId}/embeddings/...`），对外 base URL 不变。
- **禁止**：不得因「已经能跑」而把临时归属当最终决策；下一次 service 归属评审必须显式确认这两 op 是否已迁。

| # | operation | 目标 service | 理由（一句话） |
|---:|---|---|---|
| 1 | `UploadDocument` | `ControlPlaneService` | 文档入库属数据源摄入域的写入口 |
| 2 | `ListDocuments` | `ControlPlaneService` | 文档清单是摄入域的读模型 |
| 3 | `GetDocument` | `ControlPlaneService` | 文档元数据由摄入域维护 |
| 4 | `ListDocumentChunks` | `ControlPlaneService` | 切片元数据与文档同域 |
| 5 | `DownloadDocument` | `ControlPlaneService` | 原文下载属文档资产管理 |
| 6 | `ListIngestionRuns` | `ControlPlaneService` | 批量导入作业属摄入调度 |
| 7 | `StartDocumentIndex` | `ControlPlaneService` | 索引作业属摄入调度 |
| 8 | `GetMetricReadiness` | `ControlPlaneService` | 指标定义就绪度属定义侧 |
| 9 | `GetMetricReportManifest` | `ControlPlaneService` | 报告清单是定义侧元数据 |
| 10 | `ListMetricFamilies` | `ControlPlaneService` | 指标族是定义结构 |
| 11 | `GetMetricFamily` | `ControlPlaneService` | 指标族详情是定义结构 |
| 12 | `RecordMetricDecision` | `ControlPlaneService` | 口径决策记录属治理 |
| 13 | `ListMetricDecisions` | `ControlPlaneService` | 指标决策审计属治理 |
| 14 | `ListFacts` | `ControlPlaneService` | A-Box 账本治理视图 |
| 15 | `GetFact` | `ControlPlaneService` | 单条断言及其事件属账本 |
| 16 | `CreateFacts` | `ControlPlaneService` | 断言写入必须过账本治理 |
| 17 | `RetractFacts` | `ControlPlaneService` | 撤回是账本治理动作 |
| 18 | `RestoreFact` | `ControlPlaneService` | 恢复是账本治理动作 |
| 19 | `ListFactEvents` | `ControlPlaneService` | 断言事件审计属账本 |
| 20 | `ListFactConflicts` | `ControlPlaneService` | 冲突列表供人工裁决 |
| 21 | `ResolveFactConflicts` | `ControlPlaneService` | 冲突裁决属人工治理 |
| 22 | `ListFactCandidates` | `ControlPlaneService` | 候选清单是审批输入 |
| 23 | `ApproveFactCandidate` | `ControlPlaneService` | 候选通过是审批动作 |
| 24 | `RejectFactCandidate` | `ControlPlaneService` | 候选拒绝是审批动作 |
| 25 | `SampleFactRows` | `ControlPlaneService` | 事实源抽样属数据源校验 |
| 26 | `ResolveSourceRef` | `ControlPlaneService` | 源引用解析属数据源域 |
| 27 | `ListDictionaries` | `ControlPlaneService` | 数据字典属数据源目录 |
| 28 | `GetDictionary` | `ControlPlaneService` | 表字典详情属数据源目录 |
| 29 | `RefreshDictionaries` | `ControlPlaneService` | 字典刷新是目录作业 |
| 30 | `GetDictionaryView` | `ControlPlaneService` | 字典视图是目录读模型 |
| 31 | `GetDictionaryCommentCoverage` | `ControlPlaneService` | 注释覆盖率是目录质量指标 |
| 32 | `BindDictionary` | `ControlPlaneService` | 表列绑定术语属目录治理 |
| 33 | `CheckAnswerable` | `DataLayerService` | 可答性判定属查询规划 |
| 34 | `GetAnswerQuality` | `DataLayerService` | 回答质量是查询域聚合 |
| 35 | `ResolveContext` | `DataLayerService` | 上下文解析属检索 |
| 36 | `GetMetricObservations` | `DataLayerService` | 观测值查询走数据面 |
| 37 | `ComputeMetric` | `DataLayerService` | 指标计算是数据面执行 |
| 38 | `ListMetricComputations` | `DataLayerService` | 计算记录属数据面 |
| 39 | `ExecuteMetricRules` | `DataLayerService` | 规则执行发生在数据面 |
| 40 | `ListRuleTriggers` | `DataLayerService` | 规则触发是执行溯源 |
| 41 | `ListRefusals` | `DataLayerService` | 拒答记录属查询域 |
| 42 | `GetProvenanceIntegrity` | `DataLayerService` | 溯源完整性属查询域 |
| 43 | `GetEntityProvenance` | `DataLayerService` | 实体溯源是图读的延伸 |
| 44 | `GetOntologyTree` | `DataLayerService` | 图树浏览属图遍历 |
| 45 | `ListStatements` | `DataLayerService` | 三元组浏览属图遍历 |
| 46 | `FindLinks` | `DataLayerService` | 邻接查询属图遍历 |
| 47 | `FindGraphPath` | `DataLayerService` | 路径查询属图遍历 |
| 48 | `GetCanvasManifest` | `DataLayerService` | 画布能力清单是图读视图 |
| 49 | `GetCanvasSubgraph` | `DataLayerService` | 画布子图是图遍历结果 |
| 50 | `GetEntity` | `DataLayerService` | 实体详情是 A-Box 读 |
| 51 | `ExtractDocumentFacts` | `OntologyService` | 文档抽取属本体归纳 |
| 52 | `ListOntologyVersions` | `OntologyService` | 版本清单属本体生命周期 |
| 53 | `GetOntologyVersion` | `OntologyService` | 版本详情属本体生命周期 |
| 54 | `DiffOntologyVersions` | `OntologyService` | 版本差异属本体治理 |
| 55 | `ExportOntologyVersion` | `OntologyService` | 版本导出属本体治理 |
| 56 | `ProposeOntologyVersion` | `OntologyService` | 提案创建属本体治理 |
| 57 | `ListOntologyProposals` | `OntologyService` | 提案列表属本体治理 |
| 58 | `GetOntologyProposal` | `OntologyService` | 提案详情属本体治理 |
| 59 | `ReviewOntologyProposal` | `OntologyService` | 提案评审属本体治理 |
| 60 | `ListOntologyTransitions` | `OntologyService` | 状态迁移审计属本体治理 |
| 61 | `PublishOntology` | `OntologyService` | 发布是本体生命周期的终态动作 |
| 62 | `RollbackOntology` | `OntologyService` | 回滚是本体生命周期动作 |
| 63 | `ListOntologyEvents` | `OntologyService` | 本体事件属本体域 |
| 64 | `VerifyOntology` | `OntologyService` | 本体一致性校验属本体域 |
| 65 | `ImportOntology` | `OntologyService` | 本体导入属本体生命周期 |
| 66 | `GetOntologyImport` | `OntologyService` | 导入状态属本体生命周期 |
| 67 | `PublishOntologyImport` | `OntologyService` | 导入发布属本体生命周期 |
| 68 | `PutOntologyShapes` | `OntologyService` | SHACL 形状属本体 schema |
| 69 | `GetOntologyShapes` | `OntologyService` | 形状读取属本体 schema |
| 70 | `ExportBundle` | `OntologyService` | 迁移包是本体版本产物 |
| 71 | `InspectBundle` | `OntologyService` | 迁移包检查属本体治理 |
| 72 | `ImportBundle` | `OntologyService` | 迁移包导入属本体治理 |
| 73 | `ListTerms` | `OntologyService` | 术语属本体词表 |
| 74 | `GetTermCoverage` | `OntologyService` | 术语覆盖率属本体质量 |
| 75 | `DiffTerms` | `OntologyService` | 术语差异属本体治理 |
| 76 | `ImportTerms` | `OntologyService` | 术语导入属本体词表 |
| 77 | `ListTermChecks` | `OntologyService` | 术语检查属本体质量 |
| 78 | `GetTermGate` | `OntologyService` | 术语门禁属本体质量 |
| 79 | `GetOntologyDiff` | `OntologyService` | 本体 diff 属本体域健康视图 |
| 80 | `GetOntologySnapshot` | `OntologyService` | 本体快照属本体域 |
| 81 | `AnalyzeOntologyImpact` | `OntologyService` | 影响分析依赖本体版本 |
| 82 | `ListOntologyEvidence` | `OntologyService` | 本体证据属发布审计 |
| 83 | `DownloadOntologyEvidence` | `OntologyService` | 证据下载属发布审计 |
| 84 | `MaterializeReasoning` | `OntologyService` | 推理物化属本体语义层 |
| 85 | `GetReasoningStatus` | `OntologyService` | 推理状态属本体语义层 |
| 86 | `RunValidation` | `OntologyService` | SHACL 校验属本体门禁 |

**现有 op 的处理**：本次只重排 86 个新增 op；现有 88 个 op 暂留原 service。M2 第一批把 `ontology-induction.smithy`（19）与 `ontology-graph.smithy`（14）迁入 `OntologyService`，路径不变、C2 总量不变（88），迁移完成前不宣称「三套契约已收口」。

### 5.1 文档摄入（8）

| operation | HTTP | 输入 | 输出 | 额外错误 |
|---|---|---|---|---|
| `UploadDocument` | `POST /documents` | `filename`, `contentType`, `contentBase64` 或 `contentSha256`, `title?`, `metadata?` | `documentId`, `version`, `contentHash`, `status` | `ConflictError`（contentHash 已存在） |
| `ListDocuments` | `GET /documents` | `cursor?`, `limit?`, `status?` | `items[]{documentId,title,status,chunkCount,updatedAt}`, `nextToken?` | — |
| `GetDocument` | `GET /documents/{documentId}` | `documentId` | `documentId`, `title`, `status`, `latestVersion`, `versions[]` | `NotFoundError` |
| `ListDocumentChunks` | `GET /documents/{documentId}/chunks` | `documentId`, `cursor?`, `limit?` | `items[]{chunkId,page,text,charStart,charEnd}`, `nextToken?` | `NotFoundError` |
| `DownloadDocument` | `GET /documents/{documentId}/source` | `documentId` | `contentBase64` 或 `downloadUrl`, `contentType`, `contentHash` | `NotFoundError` |
| `ListIngestionRuns` | `GET /ingestion-runs` | `kind=BATCH\|ITEM`, `cursor?`, `limit?` | `items[]{runId,documentId,status,total,succeeded,failed,startedAt}`, `nextToken?` | — |
| `StartDocumentIndex` | `POST /documents/{documentId}/index` | `documentId`, `maxBatches?` | `jobId`, `status` | `ConflictError`（已索引中） |
| `ExtractDocumentFacts` | `POST /documents/{documentId}/extract` | `documentId`, `ontologyVersion?`, `options?` | `jobId`, `candidateCount` | `ConflictError` |

### 5.2 检索与问答（3）

| operation | HTTP | 输入 | 输出 | 额外错误 |
|---|---|---|---|---|
| `CheckAnswerable` | `POST /answerable` | `query`, `ontologyVersion?`, `minCoverage?`, `metricId?`, `intent?`, `includeLayers?`, `includePanel?` | `answerable`, `coverage`, `missing[]`, `layers[]`, `panel?` | `NoResultError` |
| `GetAnswerQuality` | `GET /answer/quality` | `sampleSize?`, `since?` | `metrics{coverage,citationRate,refusalRate}`, `samples[]` | — |
| `ResolveContext` | `POST /context/resolve` | `query`, `sessionId?`, `maxItems?` | `entities[]`, `metrics[]`, `documents[]`, `trace` | `NoResultError` |

### 5.3 指标（9）

| operation | HTTP | 输入 | 输出 | 额外错误 |
|---|---|---|---|---|
| `GetMetricObservations` | `GET /metrics/{name}/observations` | `name`, `periodStart`, `periodEnd`, `grain?`, `entityKey?`, `dataSource?` | `observations[]{periodStart,periodEnd,value,unit,dimensions,synthetic,dataSourceId}`, `definitionVersion` | `NotFoundError` |
| `ComputeMetric` | `POST /metrics/{name}/compute` | `name`, `asOf?`, `periodStart?`, `periodEnd?`, `entityKey?`, `institution?`, `dataSource` | `value`, `unit`, `window`, `sampleCount`, `computedAt`, `definitionVersion`, `computationRef` | `ValidationError`（缺 dataSource） |
| `ListMetricComputations` | `GET /metrics/{name}/computations` | `name`, `limit?` | `records[]{ref,issuedAt,locator}` | `NotFoundError` |
| `ExecuteMetricRules` | `POST /metrics/{name}/rules` | `name`, `facts[]`, `asOf?`, `actor?`, `requestId?` | `triggered[]`, `prov{activityId,graph}`, `provGraph` | `ValidationError` |
| `RecordMetricDecision` | `POST /metrics/{name}/decision` | `name`, `actor?`, `reason?`, `requestId?` | `decisionId`, `recordedAt`, `priorDecisionId?` | `NotFoundError` |
| `GetMetricReadiness` | `GET /metrics-readiness` | `domain?` | `items[]{metricName,ready,reasons[]}`, `summary` | — |
| `GetMetricReportManifest` | `GET /metrics/report/manifest` | `format=JSON\|CSV`, `domain?` | `manifest{generatedAt,entries[]}`, `contentType` | — |
| `ListMetricFamilies` | `GET /metrics/report/families` | `cursor?` | `items[]{familyId,name,metricCount}`, `nextToken?` | — |
| `GetMetricFamily` | `GET /metrics/report/families/{familyId}` | `familyId` | `familyId`, `name`, `metricNames[]`, `definition` | `NotFoundError` |

### 5.4 溯源（5）

| operation | HTTP | 输入 | 输出 | 额外错误 |
|---|---|---|---|---|
| `ListMetricDecisions` | `GET /prov/decisions` | `metricName`, `limit?` | `records[]{decisionId,actor,reason,recordedAt,priorDecisionId}` | — |
| `ListRuleTriggers` | `GET /prov/rules` | `ruleId`, `limit?` | `records[]{activityId,metricName,ruleId,triggeredAt,outcome}` | — |
| `ListRefusals` | `GET /prov/refusals` | `requestId?`, `query?`, `limit?` | `records[]{requestId,query,reason,at}` | — |
| `GetProvenanceIntegrity` | `GET /prov/integrity` | `checkGraph?` | `ok`, `separation{}`, `immutable`, `violations[]` | — |
| `GetEntityProvenance` | `GET /entities/{iri}/provenance` | `iri` | `activities[]`, `statements[]`, `citations[]` | `NotFoundError` |

### 5.5 事实账本（13）

| operation | HTTP | 输入 | 输出 | 额外错误 |
|---|---|---|---|---|
| `ListFacts` | `GET /facts` | `subject?`, `predicate?`, `state?`, `cursor?`, `limit?` | `items[]{factId,subject,predicate,object,state,graphUri,updatedAt}`, `nextToken?` | — |
| `GetFact` | `GET /facts/{factId}` | `factId` | `fact`, `eventCount` | `NotFoundError` |
| `CreateFacts` | `POST /facts` | `facts[]{subject,predicate,object,graphUri,sourceRef?}`, `actor?` | `created[]{factId,status}`, `rejected[]` | `ConflictError` |
| `RetractFacts` | `POST /facts/retract` | `factIds[]` 或 `filter`, `reason?` | `retracted[]`, `skipped[]` | `NotFoundError` |
| `RestoreFact` | `POST /facts/{factId}/restore` | `factId` | `factId`, `state` | `ConflictError` |
| `ListFactEvents` | `GET /facts/{factId}/events` | `factId`, `cursor?`, `limit?`, `format?` | `items[]{eventId,type,at,actor,payload}`, `nextToken?` | `NotFoundError` |
| `ListFactConflicts` | `GET /facts/conflicts` | `state?`, `cursor?` | `items[]{conflictId,subject,predicate,values[],state}`, `nextToken?` | — |
| `ResolveFactConflicts` | `POST /facts/conflicts/resolve` | `action=RESOLVE\|UNDO\|UNMERGE\|BATCH`, `conflictIds[]`, `winner?`, `actor?` | `resolved[]`, `failed[]` | `ConflictError` |
| `ListFactCandidates` | `GET /candidates` | `documentId?`, `status?`, `cursor?` | `items[]{candidateId,subject,predicate,object,confidence,status}`, `nextToken?` | — |
| `ApproveFactCandidate` | `POST /candidates/{candidateId}/approve` | `candidateId`, `actor?`, `factOverrides?` | `factId`, `status` | `ConflictError` |
| `RejectFactCandidate` | `POST /candidates/{candidateId}/reject` | `candidateId`, `actor?`, `reason` | `status` | `NotFoundError` |
| `SampleFactRows` | `GET /facts/samples` | `table`, `limit?` | `rows[]`, `sourceRefs[]` | `AccessDeniedError`（非注册事实源） |
| `ResolveSourceRef` | `GET /source-refs/{ref}` | `ref` | `ref`, `kind`, `locator`, `resolveUrl` | `NotFoundError` |

### 5.6 本体与治理（21）

| operation | HTTP | 输入 | 输出 | 额外错误 |
|---|---|---|---|---|
| `ListOntologyVersions` | `GET /ontologies/{ontologyId}/versions` | `cursor?` | `items[]{versionId,contentHash,publishedAt,status}`, `nextToken?` | `NotFoundError` |
| `GetOntologyVersion` | `GET /ontologies/{ontologyId}/versions/{versionId}` | `versionId` | `versionId`, `contentHash`, `publishedAt`, `graphUri`, `statementCount` | `NotFoundError` |
| `DiffOntologyVersions` | `GET /ontologies/{ontologyId}/versions/{versionId}/diff` | `versionId`, `against` | `added[]`, `removed[]`, `changed[]` | `NotFoundError` |
| `ExportOntologyVersion` | `GET /ontologies/{ontologyId}/versions/{versionId}/export` | `versionId`, `format?` | `contentBase64` 或 `downloadUrl`, `contentType` | `NotFoundError` |
| `ProposeOntologyVersion` | `POST /ontologies/{ontologyId}/proposals` | `target=ONTOLOGY\|GOVERNANCE`, `baseVersionId`, `contentBase64` 或 `patch`, `rationale` | `proposalId`, `status` | `ConflictError` |
| `ListOntologyProposals` | `GET /ontologies/{ontologyId}/proposals` | `status?`, `cursor?` | `items[{proposalId,status,author,createdAt}]`, `nextToken?` | — |
| `GetOntologyProposal` | `GET /ontologies/{ontologyId}/proposals/{proposalId}` | `proposalId` | `proposal`, `transitions[]` | `NotFoundError` |
| `ReviewOntologyProposal` | `POST /ontologies/{ontologyId}/proposals/{proposalId}/review` | `proposalId`, `decision=APPROVE\|REJECT`, `comment?`, `actor?` | `proposalId`, `status`, `transitionId` | `ConflictError`（已终态） |
| `ListOntologyTransitions` | `GET /ontologies/{ontologyId}/transitions` | `subjectType=PROPOSAL\|VERSION`, `subjectId?`, `cursor?` | `items[]{transitionId,from,to,actor,at}` | — |
| `PublishOntology` | `POST /ontologies/{ontologyId}/publish` | `versionId`, `actor?` | `publishedVersion`, `publishedAt` | `ConflictError` |
| `RollbackOntology` | `POST /ontologies/{ontologyId}/rollback` | `targetVersionId`, `planOnly?`, `actor?` | `plan{steps[]}`, `publishedVersion?` | `ConflictError` |
| `ListOntologyEvents` | `GET /ontologies/{ontologyId}/events` | `cursor?`, `limit?` | `items[]{eventId,type,at,payload}`, `nextToken?` | — |
| `VerifyOntology` | `POST /ontologies/{ontologyId}/verify` | `versionId?` | `ok`, `checks[]{name,status,details}` | — |
| `ImportOntology` | `POST /ontologies/{ontologyId}/import` | `format`, `contentBase64` 或 `sourceUrl`, `contentType` | `importId`, `status` | `ValidationError` |
| `GetOntologyImport` | `GET /ontologies/{ontologyId}/imports/{importId}` | `importId` | `importId`, `status`, `counts`, `errors[]` | `NotFoundError` |
| `PublishOntologyImport` | `POST /ontologies/{ontologyId}/imports/{importId}/publish` | `importId` | `versionId`, `status` | `ConflictError` |
| `PutOntologyShapes` | `PUT /ontologies/{ontologyId}/shapes` | `shapesTtl`, `contentType` | `shapesVersion`, `contentHash` | `ValidationError` |
| `GetOntologyShapes` | `GET /ontologies/{ontologyId}/shapes` | — | `shapesTtl`, `shapesVersion` | `NotFoundError` |
| `ExportBundle` | `POST /ontologies/{ontologyId}/bundles/export` | `versionId?`, `includeInstances?` | `bundleRef`, `manifest` | — |
| `InspectBundle` | `GET /ontologies/{ontologyId}/bundles/inspect` | `bundleRef` | `manifest`, `compatibleVersions[]` | `ValidationError` |
| `ImportBundle` | `POST /ontologies/{ontologyId}/bundles/import` | `bundleRef`, `mode=VALIDATE\|APPLY` | `importId`, `status` | `ConflictError` |

### 5.7 术语（6）

| operation | HTTP | 输入 | 输出 | 额外错误 |
|---|---|---|---|---|
| `ListTerms` | `GET /ontology/terms` | `query?`, `cursor?` | `items[]{termId,prefLabel,altLabels,definition,status}`, `nextToken?` | — |
| `GetTermCoverage` | `GET /ontology/terms/coverage` | `versionId?` | `coverage{covered,total}`, `byClass[]` | — |
| `DiffTerms` | `POST /ontology/terms/diff` | `leftVersionId`, `rightVersionId` | `added[]`, `removed[]`, `changed[]` | `NotFoundError` |
| `ImportTerms` | `POST /ontology/terms/import` | `format`, `contentBase64` | `importId`, `counts` | `ValidationError` |
| `ListTermChecks` | `GET /ontology/terms/checks` | — | `items[]{checkId,severity,message,termId}` | — |
| `GetTermGate` | `GET /ontology/terms/gate` | — | `passed`, `blockers[]` | — |

### 5.8 图与画布（6）

| operation | HTTP | 输入 | 输出 | 额外错误 |
|---|---|---|---|---|
| `GetOntologyTree` | `GET /graph/tree` | `rootUri?`, `maxDepth?` | `nodes[]`, `edges[]` | `NotFoundError` |
| `ListStatements` | `GET /graph/statements` | `subject?`, `predicate?`, `object?`, `graphUri?`, `cursor?`, `limit?` | `items[]{subject,predicate,object,graphUri}`, `nextToken?` | — |
| `FindLinks` | `GET /graph/links` | `entityUri`, `direction?`, `limit?` | `links[]{source,target,predicate}` | `NotFoundError` |
| `FindGraphPath` | `GET /graph/path` | `sourceUri`, `targetUri`, `maxHops?` | `paths[]{nodes[],edges[]}` | `NoResultError` |
| `GetCanvasManifest` | `GET /graph/canvas/manifest` | — | `capabilities{layout,renderers}`, `limits{}` | — |
| `GetCanvasSubgraph` | `GET /graph/canvas` | `startUri`, `hops?`, `maxNodes?`, `maxEdges?` | `nodes[]`, `edges[]`, `layout` | `NotFoundError` |

### 5.9 健康与快照（2）

| operation | HTTP | 输入 | 输出 | 额外错误 |
|---|---|---|---|---|
| `GetOntologyDiff` | `GET /health/ontology-diff` | `includeFlow?` | `added[]`, `removed[]`, `flow[]` | — |
| `GetOntologySnapshot` | `GET /health/ontology-snapshot` | — | `versionId`, `contentHash`, `counts{classes,properties,instances}`, `generatedAt` | — |

### 5.10 数据字典（6）

| operation | HTTP | 输入 | 输出 | 额外错误 |
|---|---|---|---|---|
| `ListDictionaries` | `GET /catalog/dictionaries` | `cursor?` | `items[]{table,description,columnCount}`, `nextToken?` | — |
| `GetDictionary` | `GET /catalog/dictionaries/{table}` | `table` | `table`, `columns[]{name,type,description,boundTerm}` | `NotFoundError` |
| `RefreshDictionaries` | `POST /catalog/dictionaries/refresh` | `tables?` | `jobId`, `status` | `ConflictError` |
| `GetDictionaryView` | `GET /catalog/dictionaries/views/{view}` | `view` | `view`, `rows[]` | `NotFoundError` |
| `GetDictionaryCommentCoverage` | `GET /catalog/dictionaries/comment-coverage` | — | `covered`, `total`, `byTable[]` | — |
| `BindDictionary` | `POST /catalog/dictionaries/bind` | `table`, `column`, `termIri` | `ok`, `boundTerm` | `NotFoundError` |

### 5.11 影响、证据、推理、校验、实体（7）

| operation | HTTP | 输入 | 输出 | 额外错误 |
|---|---|---|---|---|
| `AnalyzeOntologyImpact` | `GET /ontologies/{ontologyId}/impact` | `fromVersion`, `toVersion`, `format?` | `impacted[]{asset,kind,severity}`, `summary` | `NotFoundError` |
| `ListOntologyEvidence` | `GET /ontologies/{ontologyId}/evidence` | `cursor?` | `items[]{evidenceId,kind,createdAt,size}` | — |
| `DownloadOntologyEvidence` | `GET /ontologies/{ontologyId}/evidence/{evidenceId}` | `evidenceId` | `downloadUrl` 或 `contentBase64` | `NotFoundError` |
| `MaterializeReasoning` | `POST /ontologies/{ontologyId}/reasoning/materialize` | `profile=RDFS\|SHACL\|OWL` | `jobId`, `status`, `materializedCount` | `UnsupportedError`（OWL 未装 JVM） |
| `GetReasoningStatus` | `GET /ontologies/{ontologyId}/reasoning/status` | — | `running`, `lastRunAt`, `lastResult` | — |
| `RunValidation` | `POST /ontologies/{ontologyId}/validation/run` | `shapesVersion?`, `scope?` | `conforms`, `report` | — |
| `GetEntity` | `GET /entities/{iri}` | `iri` | `entity{iri,types,statements[]}`, `provenance?` | `NotFoundError` |

> 共 8+3+9+5+13+21+6+6+2+6+7 = **86 个新 operation**。其中 `ListIngestionRuns`、`CheckAnswerable`、`ResolveFactConflicts`、`RetractFacts`、`ComputeMetric`、`RollbackOntology`、`ReviewOntologyProposal`、`ImportOntology`、`GetOntologyImport`、`PublishOntologyImport`、`PutOntologyShapes`、`GetOntologyShapes`、`ListOntologyTransitions` 是「可合并」行的合并目标。

---

## 6. UI 落点（10 个平台页面 → web-app）

### 6.1 页面级落点

| 平台页面 | 能力 | `web-app` 落点 | 已有/新增 | 背书 operation |
|---|---|---|---|---|
| `index.html` | 总览 | `/`、`/namespaces` | 已有 | `GetOntologyOverview`、`ListNamespaces` |
| `browse.html` | 本体树/实例/三元组/SPARQL/链接/路径 | `/namespaces/:namespaceId/ontology/graph` | 已有 | `GetOntologyTree`、`GraphSearch`、`ListStatements`、`Query`、`FindLinks`、`FindGraphPath` |
| `answer_panel.html` | 问答/检索/追踪 | `/playground`、`/playground/trace/:sessionId/:requestId` | 已有 | `Query`、`KBSearch`、`CheckAnswerable`、`GetAnswerQuality` |
| `entity.html` | 实体视图/溯源 | `/namespaces/:namespaceId/ontology/entities/:entityId` | **新增** | `GetEntity`、`GetEntityProvenance` |
| `search.html` | 语义检索 | `/playground` | 已有 | `KBSearch` |
| `governance.html` | 提案/审批/发布/回滚/bundle | `/namespaces/:namespaceId/governance` | **新增** | `ListOntologyProposals`、`ReviewOntologyProposal`、`PublishOntology`、`RollbackOntology`、`ExportBundle`、`ImportBundle` |
| `approvals.html` | 候选审批 | `/namespaces/:namespaceId/approvals` | **新增** | `ListFactCandidates`、`ApproveFactCandidate`、`RejectFactCandidate` |
| `documents.html` | 文档/切片/导入 | `/namespaces/:namespaceId/documents` | **新增** | `UploadDocument`、`ListDocuments`、`ListDocumentChunks`、`ListIngestionRuns` |
| `ontology.html` | 本体/版本/形状/影响/术语/画布 | `/namespaces/:namespaceId/ontology`（+ `/ontology/terms`、`/ontology/canvas` 新增） | 已有 + **新增 2** | `ListOntologyVersions`、`GetOntologyShapes`、`AnalyzeOntologyImpact`、`GetTermCoverage`、`GetCanvasSubgraph` |
| `health.html` | 健康看板 | `/system-health` | 已有 | `GetSystemHealth`、`GetOntologyDiff`、`GetOntologySnapshot` |

### 6.2 路由增量

- 现有 24 条不变。
- 新增 6 条：`/namespaces/:namespaceId/documents`、`.../approvals`、`.../governance`、`.../ontology/terms`、`.../ontology/canvas`、`.../ontology/entities/:entityId`。
- 新增路由的硬规则：**每条必须有 §4 里的 operation 背书，并在 `web-app` 的路由表旁写 operation 名**；没有背书的页面不许加。
- 指标报告页（`/metrics/reports`）作为 `/metrics` 的子页签实现，不新增一级路由。

---

### 6.3 原子功能点迁移总表（143 条）

粒度：可执行动作或可展示信息。原位置写「文件:行号 / 元素 id / JS 函数」。后端列 `已有：Op` 表示契约现有 operation 可直接支撑（含字段扩展）；`新增：Op` 指向 §5 的规格。

#### A. 概览 `index.html`（14 条 / 已有 3 / 新增 10 / 无后端 1）

| # | 功能点 | 原位置 | web-app 落点 | 后端 | 验收动作 |
|---|---|---|---|---|---|
| F01 | 系统概览卡（版本指针/容器状态/命名图） | `index.html:29` `#overview`；`app.js:65` `loadOverview` | `/` 首页概览卡 | 已有：`GetSystemHealth` + `GetOntologyOverview` | 打开 `/`，卡片显示版本号与命名图计数 |
| F02 | 刷新概览 | `index.html:27` `#refresh`；`app.js:746` | 合并：F01 + F02 → 概览卡刷新按钮 | 已有：同上 | 点刷新，网络请求重发且数据更新 |
| F03 | 下一步引导（seed 提示） | `index.html:33` | `/` 首次使用引导卡 | 无后端 | 空环境打开 `/` 显示引导 |
| F04 | 路径查询表单（起点/终点/hops） | `browse_path.js:61,70` `#canvas-path-form` | `/namespaces/:namespaceId/ontology/canvas` | 新增：`FindGraphPath` | 填两个 IRI 提交，返回路径 |
| F05 | 路径结果表（paths） | `browse_path.js:139` `pathsTable` | 合并：F05 + F06 → 路径结果区 | 新增：`FindGraphPath` | 表格至少一行，列含 hops |
| F06 | 路径边表（edges） | `browse_path.js:164` `edgesTable` | 同上 | 新增：`FindGraphPath` | 边数与路径长度一致 |
| F07 | 路径 SVG 可视化 | `browse_path.js:186` `svg` | 同一结果区 | 新增：`FindGraphPath` | SVG 节点数 = 路径节点数 |
| F08 | 画布筛选（类型/图/limit） | `canvas_full.js:147,157` `kinds/queryParams` | `/ontology/canvas` 工具条 | 新增：`GetCanvasSubgraph` | 改类型后节点集合变化 |
| F09 | 画布加载更多（cursor） | `canvas_full.js:123` `#cf-more` | 合并：F08 + F09 + F10 → 画布工具条 | 新增：`GetCanvasSubgraph` | 点更多，节点累加且不重复 |
| F10 | 画布清空 | `canvas_full.js:129` `clear` | 同上 | 新增：`GetCanvasSubgraph` | 清空后回空态 |
| F11 | 画布统计/覆盖率/截断警告 | `canvas_full.js:288,305` | 合并：F11 + F13 → 画布侧栏 | 新增：`GetCanvasSubgraph` | 超限时显式显示 `truncated` |
| F12 | 画布节点/边表格 | `canvas_full.js:335` `renderTables` | 同一页下半区 | 新增：`GetCanvasSubgraph` | 表格行数 = 图节点数 |
| F13 | 画布 manifest 能力探测 | `canvas_full.js:522` | 合并进 F11 | 新增：`GetCanvasManifest` | 打开即显示 capabilities/limits |
| F14 | 概览交叉链接 | `browse_answer.js:508` `mountOverviewLink` | 合并进 F01 | 已有：`GetOntologyOverview` | 概览卡片可点进本体页 |

#### B. 文档库 `documents.html`（10 条 / 新增 10）

| # | 功能点 | 原位置 | web-app 落点 | 后端 | 验收动作 |
|---|---|---|---|---|---|
| F15 | 上传单个文件 | `documents.html:24-27` `#upload-form`；`app.js:265` | `/namespaces/:namespaceId/documents` | 新增：`UploadDocument` | 选 1 个 txt 上传，列表新增 1 条 |
| F16 | 上传状态提示 | `#upload-status`；`app.js:265` | 合并进 F15 | 新增：`UploadDocument` | 成功/失败各有明确文案 |
| F17 | 导入批次列表 | `#import-progress`；`app.js:165` `loadImports` | `/documents` 批次页签 | 新增：`ListIngestionRuns`(`kind=BATCH`) | 显示批次状态与成功/失败数 |
| F18 | 刷新导入进度 | `#import-refresh`；`app.js:778` | 合并进 F17 | 新增：`ListIngestionRuns` | 点刷新后计数更新 |
| F19 | 文档列表 | `#documents`；`app.js:195` `loadDocuments` | `/documents` 主表 | 新增：`ListDocuments` | 分页可翻到末页，总数=3,066 |
| F20 | 点文档查看分块 | `app.js:214` link | 合并：F20 + F21 → 分块抽屉 | 新增：`ListDocumentChunks` | 点文档 ID 右侧出现分块 |
| F21 | 分块内容（页码/字符区间） | `#chunks`；`app.js:249` `loadChunks` | 同上 | 新增：`ListDocumentChunks` | 分块含 page、charStart/charEnd |
| F22 | 解析（切块+索引） | `app.js:220` button | `/documents` 行操作 | 新增：`StartDocumentIndex` | 点解析，状态变 indexing→indexed |
| F23 | 抽取候选 | `app.js:232` button | 同行操作 | 新增：`ExtractDocumentFacts` | 点抽取后候选数 > 0 |
| F24 | 文档状态提示 | `#doc-status` | 合并进 F19 | 新增：`ListDocuments` | 行状态与操作结果一致 |

#### C. 审批队列 `approvals.html`（17 条 / 新增 17）

| # | 功能点 | 原位置 | web-app 落点 | 后端 | 验收动作 |
|---|---|---|---|---|---|
| F25 | 待审批候选列表 | `#candidates`；`app.js:324` | `/namespaces/:namespaceId/approvals` | 新增：`ListFactCandidates` | 列表显示 s/p/o 与置信度 |
| F26 | 通过候选 | `app.js:343` | 候选行「通过」 | 新增：`ApproveFactCandidate` | 通过后候选消失、事实出现 |
| F27 | 拒绝候选 | `app.js:354` | 候选行「拒绝」 | 新增：`RejectFactCandidate` | 拒绝后状态 rejected |
| F28 | 冲突列表 | `#conflicts`；`app.js:435` | `/approvals` 冲突页签 | 新增：`ListFactConflicts` | 同 (s,p) 多值可见 |
| F29 | 冲突裁决：保留单值 | `app.js:472` | 冲突行三选一 | 新增：`ResolveFactConflicts`(`RESOLVE`) | 选赢家后冲突消失 |
| F30 | 冲突裁决：两者都保留 | `app.js:478` | 同上 | 新增：`ResolveFactConflicts`(`UNMERGE`) | 状态变 unmerged |
| F31 | 冲突裁决：合并 | `app.js:484` | 同上 | 新增：`ResolveFactConflicts`(`MERGE`) | 合并值在事实表可查 |
| F32 | 撤销上次裁决 | `#conflict-undo`；`app.js:496` | 冲突区工具条 | 新增：`ResolveFactConflicts`(`UNDO`) | 撤销后冲突重现 |
| F33 | 按谓词批量保留 | `#conflict-batch`；`app.js:520` | 冲突区工具条 | 新增：`ResolveFactConflicts`(`BATCH`) | 批量后该谓词冲突清零 |
| F34 | 刷新冲突 | `#conflicts-refresh`；`app.js:788` | 合并进 F28 | 新增：`ListFactConflicts` | 刷新可重复执行 |
| F35 | 事实列表 | `#facts`；`app.js:368` | `/approvals` 事实页签 | 新增：`ListFacts` | 显示 active/retracted 状态 |
| F36 | 事实撤回 | `app.js:394` | 事实行操作 | 新增：`RetractFacts` | 撤回后状态 retracted |
| F37 | 事实恢复 | `app.js:406` | 事实行操作 | 新增：`RestoreFact` | 恢复后回 active |
| F38 | 事实事件查看 | `app.js:416` | 事实行展开 | 新增：`ListFactEvents` | 显示事件时间线 |
| F39 | 刷新事实 | `#facts-refresh`；`app.js:787` | 合并进 F35 | 新增：`ListFacts` | 刷新可用 |
| F40 | 运行物化 | `#materialize-btn`；`app.js:546` | 审批完成后的动作区 | 新增：`MaterializeReasoning` | 点后返回作业号与阶段结果 |
| F41 | 物化结果（skipped/阶段） | `#materialize-result` | 合并进 F40 | 新增：`MaterializeReasoning` | 显示 skipped 与各阶段状态 |

#### D. 只读浏览 `browse.html`（40 条 / 已有 19 / 新增 19 / 无后端 2）

| # | 功能点 | 原位置 | web-app 落点 | 后端 | 验收动作 |
|---|---|---|---|---|---|
| F42 | 7 个页签切换 | `browse.js:60,70` | `/ontology/graph` 页签组 | 无后端 | 7 个页签均可切换且 URL 稳定 |
| F43 | 本体类树 | `#ontology-tree`；`browse.js:181` | `/ontology` 左栏 | 新增：`GetOntologyTree` | 展开到 3 层有子类 |
| F44 | 类树节点选中 | `browse.js:93,106` | 合并进 F46 | 新增：`GetOntologyTree` | 点击类高亮且右侧刷新 |
| F45 | 属性列表 | `#ontology-properties` | `合并：F45 + F133 → 属性列表` | 已有：`GetGraphObjectProperty`/`GetGraphDatatypeProperty` | 对象/数据属性分组显示 |
| F46 | 类下实例列表 | `#instance-list`；`browse.js:114` | `/ontology/graph` 右栏 | 已有：`GraphSearch` | 选类后显示实例 |
| F47 | 实例分页 | `browse.js:172,176` | 合并进 F46 | 已有：`GraphSearch` | 翻页游标前进/后退 |
| F48 | 口径卡「域」筛选 | `#filter-domain` | `/metrics` 筛选条 | 已有：`ListMetrics` | 选 bank 后只剩 bank |
| F49 | 口径卡 evidenceBasis 筛选 | `#filter-basis` | `/metrics` 筛选条 | 已有：`ListMetrics`（补字段） | 选 regulatory 后只剩该档 |
| F50 | 口径卡 publishable 筛选 | `#filter-publishable` | `/metrics` 筛选条 | 已有：`ListMetrics`（补字段） | true/false 过滤生效 |
| F51 | 口径卡刷新 | `#metrics-refresh`；`browse.js:358` | 合并进 F52 | 已有：`ListMetrics` | 刷新后数据重载 |
| F52 | 口径卡表格（8 列） | `browse.js:256` | `/metrics` 表格 | 已有：`ListMetrics` | 8 列表头与数据齐全 |
| F53 | 口径卡详情 | `browse.js:297,322` | `/metrics/:metricName` | 已有：`GetMetric` | 点击行显示公式与口径 |
| F54 | 类/字段绑定链接 | `browse.js:398,437` | 合并进 F53 | 已有：`GetMetric`（补字段） | 绑定项可跳到实体页 |
| F55 | 家族视图/变体切换 | `browse_metrics.js:357,426` | `/metrics` 家族侧栏 | 新增：`GetMetricFamily` | 切变体后详情变化 |
| F56 | 口径卡卡片视图 + 外部状态 | `browse_metrics.js:233,188` | 合并进 F53 | 已有：`GetMetric`（补 `externalStatus`） | 卡片显示外部状态徽标 |
| F57 | manifest 外部状态增强 | `browse_metrics.js:94,161` | 合并进 F52 | 新增：`GetMetricReportManifest` | 行内出现 manifest 状态 |
| F58 | 术语锚点类计数 | `#terms-classes`；`browse.js:727` | `/ontology/terms` | 新增：`ListTerms` | 锚点类计数与列表一致 |
| F59 | 术语别名表（7 列） | `browse.js:727` | `/ontology/terms` 表 | 新增：`ListTerms` | 7 列齐全（档位/confidence 等） |
| F60 | 字典筛选（表/列/来源/绑定档位） | `browse.js:801` `dictQueryUrl` | `/sources/:sourceId` 字典页签 | 新增：`ListDictionaries` | 组合筛选生效 |
| F61 | 字典查询 | `#dict-query`；`browse.js:888` | 合并进 F63 | 新增：`ListDictionaries` | 查询返回预期行 |
| F62 | 字典刷新（内省） | `#dict-refresh`；`browse.js:906` | `/sources/:sourceId` 工具条 | 新增：`RefreshDictionaries` | 连按两次行数不变（幂等） |
| F63 | 字典表格（10 列） | `browse.js:823` | 合并：F61 + F63 + F64 → 字典表 | 新增：`GetDictionary` | 10 列齐全 |
| F64 | 字典分页 | `browse.js:898,902` | 合并进 F63 | 新增：`ListDictionaries` | 翻页可用 |
| F65 | 字典视图切换 | `browse_dict.js:105,145` | 合并进 F60 | 新增：`GetDictionaryView` | 切换视图表格列变化 |
| F66 | 字典注释覆盖率 | `browse_dict_coverage.js:54` | `/sources/:sourceId` | 新增：`GetDictionaryCommentCoverage` | 显示覆盖百分比与分表 |
| F67 | 三元组筛选（s/p/o/graph/limit） | `browse.js:483` `tripleFilters` | `/ontology/graph` 三元组页签 | 新增：`ListStatements` | 条件组合生效 |
| F68 | 三元组查询 | `#triples-query`；`browse.js:543` | 合并进 F67 | 新增：`ListStatements` | 返回结果表 |
| F69 | 清空三元组条件 | `#triples-reset`；`browse.js:544` | 合并进 F67 | 新增：`ListStatements` | 条件清空后回默认 |
| F70 | 三元组分页 | `browse.js:556,560` | 合并进 F67 | 新增：`ListStatements` | 翻页游标变化 |
| F71 | 三元组行跳转实体 | `browse.js:492` | `/ontology/entities/:iri` | 已有：`GetEntity` | 点 subject 进入实体页 |
| F72 | SPARQL 运行 | `#sparql-run`；`browse.js:686` | `/ontology/graph` SPARQL 页签 | 已有：`Query` | SELECT 返回表格 |
| F73 | SPARQL 结果表 | `browse.js:586` | 合并进 F72 | 已有：`Query` | 变量列与行数正确 |
| F74 | SPARQL 错误原样展示 | `browse.js:654` | 合并进 F72 | 已有：`Query`（错误语义） | 写查询显示 400/providerCode |
| F75 | 问答输入（问题/策略/topK） | `browse.js:1153` `askQuestion` | `/playground` | 已有：`Query` + `KBSearch` | 提交后返回答案 |
| F76 | 覆盖度四层条形 | `browse.js:945` | `/playground` 覆盖度区 | 新增：`CheckAnswerable` | 四层命中可视化 |
| F77 | 回答文本 | `browse.js:1122` | 合并进 F75 | 已有：`Query` | 有答案且非空 |
| F78 | 引用 chips | `browse.js:1057` | 合并进 F75 | 已有：`Query` | chip 带 docId/chunkId |
| F79 | 缺口与补法 | `browse.js:1093` | 合并进 F76 | 新增：`CheckAnswerable` | missing 列表非空 |
| F80 | 步骤时间线 | `browse.js:1021` | 合并进 F75 | 已有：`Query`（steps） | 步骤数 > 0 |
| F81 | 示例填充 | `#qa-example`；`browse.js:1194` | 合并进 F75 | 无后端 | 点击后问题框有示例 |

#### E. 检索与问答 `search.html`（4 条 / 已有 3 / 无后端 1）

| # | 功能点 | 原位置 | web-app 落点 | 后端 | 验收动作 |
|---|---|---|---|---|---|
| F82 | 检索表单（query/strategy/topK/tokenBudget） | `search.html:24-34` | `/playground` 检索面板 | 已有：`KBSearch`（补 `mode`/预算） | 提交返回结果 |
| F83 | 检索结果（片段+事实+元数据） | `app.js:284` `runSearch` | 合并进 F82 | 已有：`KBSearch` | 片段带 docId/chunkId/页码 |
| F84 | 截断/降级显式提示 | `search.html:35` | 合并进 F82 | 已有：`KBSearch`（`truncated`/`degraded`） | 触发截断时显示警告 |
| F85 | 检索与问答合并入口 | `search.html` + `browse.html` 问答页签 | 合并：F82 + F85 → `/playground` | 无后端 | 同一页完成检索与问答 |

#### F. 检索问答质量 `answer_panel.html`（8 条 / 已有 1 / 新增 7）

| # | 功能点 | 原位置 | web-app 落点 | 后端 | 验收动作 |
|---|---|---|---|---|---|
| F86 | R-01 分层覆盖度面板 | `answer_panel.html:47`；`browse_answer.js:88,123` | `/playground/quality`（新增） | 新增：`GetAnswerQuality` | 显示四层覆盖与趋势 |
| F87 | R-01 筛选/刷新 | `browse_answer.js:94,96` | 合并进 F86 | 新增：`GetAnswerQuality` | 切策略后面板重算 |
| F88 | R-01 误判下钻 | `browse_answer.js:222` | 合并进 F86 | 新增：`GetAnswerQuality` | 点行展开明细 |
| F89 | R-02 引用与拒答质量 | `browse_answer.js:237` | `/playground/quality` | 新增：`GetAnswerQuality` | 引用率/断链率显示 |
| F90 | R-03 实体溯源查询 | `browse_answer.js:313,527` | `/ontology/entities/:iri` 溯源区 | 新增：`GetEntityProvenance` | 输入 IRI 出徽标 |
| F91 | R-03 徽标三态 | `browse_answer.js:313` | 合并进 F90 | 新增：`GetEntityProvenance` | 有/无/推断三态可辨 |
| F92 | R-04 浏览交叉跳转 | `browse_answer.js:378,405` | 拆：→ F53 / F71 / F43 | 已有：`GetMetric`/`GetEntity`/`GetOntologyTree` | 三条跳转均可达 |
| F93 | 内联溯源按钮 | `browse_answer.js:369` | 合并进 F90 | 新增：`GetEntityProvenance` | 按钮触发查询 |

#### G. 实体详情 `entity.html`（9 条 / 已有 2 / 新增 7）

| # | 功能点 | 原位置 | web-app 落点 | 后端 | 验收动作 |
|---|---|---|---|---|---|
| F94 | 实体 IRI 查询 | `entity.html:28-32`；`entity.js:226` | `/ontology/entities/:iri` | 新增：`GetEntity` | 输入 IRI 出详情 |
| F95 | 实体摘要 | `entity.js:56` | 合并进 F94 | 新增：`GetEntity` | 标签/类型显示 |
| F96 | 类归属与父类链 | `entity.js:73` | 合并进 F94 | 新增：`GetEntity` | 父类链完整 |
| F97 | 必需属性与取值 | `entity.js:91` | 合并进 F94 | 新增：`GetEntity` | 缺失必填显式标红 |
| F98 | 属性取值 | `entity.js:112` | 合并进 F94 | 新增：`GetEntity` | 全部属性列出 |
| F99 | 邻居子图 | `entity.js:127` | 合并进 F94 | 已有：`GraphTraverse` | 邻居数 > 0 |
| F100 | 相关指标 | `entity.js:149` | 合并进 F94 | 已有：`GetMetric`（补 `fieldBindings`） | 按绑定反查指标 |
| F101 | 来源与溯源 | `entity.js:178` | 合并进 F94 | 新增：`GetEntityProvenance` | sourceRef 可点击 |
| F102 | 数据来源说明 | `entity.js:199` | 合并进 F94 | 新增：`GetEntity` | 显示来源与生成时间 |

#### H. 治理控制台 `governance.html`（21 条 / 新增 21）

| # | 功能点 | 原位置 | web-app 落点 | 后端 | 验收动作 |
|---|---|---|---|---|---|
| F103 | actor 输入与必填 | `governance.html:27`；`governance.js:11` | `/governance` 顶栏 | 新增：`ReviewOntologyProposal`（错误语义） | 清空 actor 提交报错 |
| F104 | 创建提案 | `:34-39`；`governance.js:433` | `/governance` 提案区 | 新增：`ProposeOntologyVersion` | 创建后列表出现 |
| F105 | 刷新提案 | `:41`；`governance.js:451` | 合并进 F106 | 新增：`ListOntologyProposals` | 刷新可用 |
| F106 | 提案列表 | `:43`；`governance.js:103` | `/governance` 左栏 | 新增：`ListOntologyProposals` | 列表显示状态/作者 |
| F107 | 提案详情（diff + impact） | `:44`；`governance.js:132` | `/governance` 右栏 | 新增：`GetOntologyProposal` + `AnalyzeOntologyImpact` | 详情显示 diff 与影响 |
| F108 | 待审批列表 | `:49`；`governance.js:154` | 合并进 F106（`status=PROPOSED`） | 新增：`ListOntologyProposals` | 只显示待审 |
| F109 | 批准提案（带理由） | `governance.js:185` | 提案行「批准」 | 新增：`ReviewOntologyProposal` | 状态变 APPROVED |
| F110 | 拒绝提案（带理由） | `governance.js:205` | 提案行「拒绝」 | 新增：`ReviewOntologyProposal` | 状态变 REJECTED |
| F111 | 发布：版本/提案选择 | `:59-60`；`governance.js:227` | `/governance` 发布区 | 新增：`PublishOntology` | 下拉有候选 |
| F112 | breaking/publishExisting 勾选 | `:61-62` | 合并进 F114 | 新增：`PublishOntology` | 勾选改变 gates 结果 |
| F113 | dry-run gates | `:63`；`governance.js:253` | 发布区「dry-run」 | 新增：`PublishOntology`（`planOnly`） | 显示 gates 表 |
| F114 | 真发布（二次确认） | `:64`；`governance.js:277` | 发布区「发布」 | 新增：`PublishOntology` | 发布后版本指针变化 |
| F115 | 回滚预览 | `:75`；`governance.js:321` | `/governance` 回滚区 | 新增：`RollbackOntology`（`planOnly`） | 显示将被替换版本 |
| F116 | rollback-to | `:76`；`governance.js:342` | 回滚区 | 新增：`RollbackOntology` | 指针回到目标版本 |
| F117 | rollback 并新建版本 | `:77`；`governance.js:342` | 回滚区 | 新增：`RollbackOntology` | 版本号 +1 |
| F118 | export-bundle（含 blobs） | `:85-90`；`governance.js:461` | `/governance` 迁移区 | 新增：`ExportBundle` | 导出目录生成 |
| F119 | inspect-bundle | `:91-94`；`governance.js:475` | 合并进 F118 | 新增：`InspectBundle` | 显示清单与计数 |
| F120 | import-bundle | `:95-101`；`governance.js:486` | 迁移区 | 新增：`ImportBundle` | 导入 throw-away 库成功 |
| F121 | 审计事件过滤 | `:107-121`；`governance.js:395` | `/governance` 审计区 | 新增：`ListOntologyEvents` | 按动作过滤生效 |
| F122 | 审计事件计数 | `:119` | 合并进 F121 | 新增：`ListOntologyEvents` | 计数与列表一致 |
| F123 | 迁移结果展示 | `:102`；`governance.js:378` | 合并进 F118/F120 | 新增：`ExportBundle`/`ImportBundle` | 结果显示成功/失败 |

#### I. 健康看板 `health.html`（8 条 / 已有 3 / 新增 5）

| # | 功能点 | 原位置 | web-app 落点 | 后端 | 验收动作 |
|---|---|---|---|---|---|
| F124 | 系统状态摘要 | `:30`；`health.js:48` | `/system-health` | 已有：`GetSystemHealth` | 摘要显示服务状态 |
| F125 | 刷新看板 | `:28`；`health.js:218` | 合并进 F124 | 已有：`GetSystemHealth` | 刷新可用 |
| F126 | 覆盖率（T-Box vs A-Box） | `:35`；`health.js:75` | `/system-health` 覆盖区 | 新增：`GetOntologySnapshot` | 显示覆盖百分比 |
| F127 | 质量与推理（孤实例/无标签类/SHACL） | `:40`；`health.js:96` | `/system-health` 质量区 | 新增：`RunValidation` + `GetReasoningStatus` | 四类指标齐全 |
| F128 | 迁移与 schema 一致性 | `:45`；`health.js:118` | `/system-health` 迁移区 | 新增：`GetSystemHealth`（补 `schemaVersion`） | 代码版本与库版本对比 |
| F129 | 本体 diff 表单 | `:50-57`；`health.js:199` | `/system-health` diff 区 | 新增：`GetOntologyDiff` | 提交 from/to 出结果 |
| F130 | diff 结果 | `:58`；`health.js:172` | 合并进 F129 | 新增：`GetOntologyDiff` | 新增/删除项列出 |
| F131 | 数据来源说明 | `:63`；`health.js:132` | 合并进 F124 | 已有：`GetSystemHealth` | 显示数据源 |

#### J. 本体浏览 `ontology.html`（12 条 / 已有 6 / 新增 6）

| # | 功能点 | 原位置 | web-app 落点 | 后端 | 验收动作 |
|---|---|---|---|---|---|
| F132 | 类列表 | `#classes`；`app.js:107` | `/ontology` | 已有：`GetGraphClass` | 类列表非空 |
| F133 | 属性列表 | `#properties` | 合并进 F132 | 已有：`GetGraphObjectProperty`/`GetGraphDatatypeProperty` | 属性列表非空 |
| F134 | 图信息 | `#graphs-info` | 合并进 F132 | 已有：`DescribeSchema` | 显示命名图 IRI |
| F135 | 版本列表 | `#onto-versions`；`app.js:574` | `/ontology` 版本区 | 新增：`ListOntologyVersions` | 列表含版本 610 |
| F136 | 创建提案 | `:33-38`；`app.js:657` | 合并进 F104 | 新增：`ProposeOntologyVersion` | 创建成功 |
| F137 | diff 预览 | `:40`；`app.js:689` | `/ontology` 版本区 | 新增：`DiffOntologyVersions` | 预览显示差异 |
| F138 | 发布 | `:41`；`app.js:700` | 合并进 F114 | 新增：`PublishOntology` | 发布成功 |
| F139 | 回滚 | `:42`；`app.js:725` | 合并进 F116 | 新增：`RollbackOntology` | 回滚成功 |
| F140 | 审批提案 | `app.js:641` | 合并进 F109 | 新增：`ReviewOntologyProposal` | 审批成功 |
| F141 | 实体搜索 | `:49-53`；`app.js:127` | `/ontology/graph` 搜索框 | 已有：`GraphSearch` | 搜「监测点」有结果 |
| F142 | 邻居子图 | `:55`；`app.js:149` | 合并进 F141 | 已有：`GraphTraverse` | 点实体出邻居 |
| F143 | 实体结果跳转 | `app.js:139` | 合并进 F71 | 已有：`GetEntity` | 跳转实体页 |

**统计：143 条 = 已具备 37 + 需新增 102 + 纯前端 4。** 需新增的 102 条全部落在 §5 的 86 个 operation 上，无悬空功能点。

### 6.4 合并记录（只许合并不许消失）

| 合并 | 原功能点 | 合并后入口 |
|---|---|---|
| 概览刷新 | F01 + F02 → | 概览卡刷新按钮 |
| 路径结果 | F05 + F06 → | 路径结果区（表 + 边表） |
| 画布工具条 | F08 + F09 + F10 → | 画布工具条 |
| 画布侧栏 | F11 + F13 → | 画布侧栏 |
| 上传面板 | F15 + F16 → | 上传面板 |
| 文档分块 | F20 + F21 → | 分块抽屉 |
| 口径卡筛选 | F49 + F50 + F51 → F52 | 口径卡筛选条 |
| 口径卡详情 | F54 + F56 → F53 | 指标详情页 |
| 字典表 | F61 + F63 + F64 → F63 | 字典表格 |
| 三元组工具条 | F68 + F69 + F70 → F67 | 三元组工具条 |
| SPARQL 面板 | F73 + F74 → F72 | SPARQL 结果区 |
| 问答面板 | F77 + F78 + F80 + F81 → F75 | 问答结果区 |
| 覆盖度 | F79 → F76 | 覆盖度面板 |
| 检索面板 | F83 + F84 + F85 → F82 | `/playground` |
| 质量面板 | F87 + F88 → F86；F91 + F93 → F90 | 质量面板 / 溯源区 |
| 交叉跳转 | F92 → F53 + F71 + F43 | 拆到三个目标页 |
| 实体详情 | F95–F98 + F101 + F102 → F94 | 实体页各分区 |
| 提案 | F105 + F108 → F106 | 提案列表 |
| 发布 | F112 → F114 | 发布区 |
| 迁移 | F119 + F123 → F118 | 迁移区 |
| 审计 | F122 → F121 | 审计区 |
| 健康 | F125 + F126 + F127 + F131 → F124 | 健康看板 |
| 本体 | F133 + F134 → F132；F136 → F104；F138 → F114；F139 → F116；F140 → F109；F142 + F143 → F141 | 本体页 / 治理页 |
| 降级提示 | F84 → F82 | 检索面板 |

**没有「删除且无落点」的功能点。**

### 6.5 新增增强项（另表记录，不计入 143 条）

| # | 增强项 | 说明 | 优先级 |
|---|---|---|---|
| E1 | 全局搜索（Ctrl/⌘+K） | 跨命名空间/指标/文档/实体 | 中 |
| E2 | 面包屑与最近访问 | 降低深层路由回退成本 | 低 |
| E3 | 空态引导与一键示例数据 | 替代 `seed.ps1` 提示 | 中 |
| E4 | 表格列显隐/排序持久化 | 原页面无此能力 | 低 |
| E5 | 候选多选批量审批 | 原页面只能逐条 | 中 |
| E6 | 深色主题 | Cloudscape 主题切换 | 低 |
| E7 | diff 行级高亮 | 原 diff 为整块展示 | 中 |
| E8 | 健康看板趋势图 | 基于快照历史 | 低 |

**规则：增强项不得挤占原有功能点的排期；原有功能点未 100% 落位前，不排 E 系列。**

### 6.6 功能点口径工作量

| 项 | 条数 | 单价（人日） | 小计 |
|---|---|---|---|
| 已具备（只接线） | 37 | 0.1–0.2 | 4–7 |
| 需新增（前端；后端能力见 §3.2） | 102 | 0.22–0.35 | 22–36 |
| 纯前端 | 4 | 0.25–0.5 | 1–2 |
| **前端合计** | **143** | — | **27–45** |

总量按「搬迁 + 契约扩展 + 功能点前端 + 出口切换/删除核对 + 数据接管」：

| 分项 | 人日 |
|---|---|
| 后端能力搬迁（§3.2） | 88–126 |
| 契约扩展（86 operation） | 22–30 |
| 功能点前端（本节） | 27–45 |
| 出口切换 + 删除核对 | 10–14 |
| 数据接管（回填 + 比对 + 双跑） | 14–22 |
| **合计** | **161–237（±40%）** |

## 7. 目标形态

### 7.1 一次请求的路径（整合后）

```
[浏览器 5173]
  packages/web-app （React + Vite + Cloudscape，24 + 6 条路由）
        │ Cloudscape 组件 + ApiClient
        ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ 唯一入口：ControlPlaneService(83 op) + DataLayerService(5 op)    │
  │ 本地由 deploy/local 的 ASGI 适配层提供，路由表由 Smithy 生成     │
  └─────────────────────────────────────────────────────────────────┘
        │ 契约调用（无第二套 HTTP 路由）
        ▼
  control-plane   data-layer   metric-service   ontology-engine
  context-manager  vkg   sources   mcp-server
        │ 只依赖 coa-ports / 各自内部应用服务
        ▼
  packages/coa-runtime（组合根：每个接口一个配置键）
        ▼
  packages/local-providers（薄壳 + 从 platform-core 搬入的 providers/）
        ▼
  PostgreSQL(5433)   Oxigraph   TEI/BGE   fs/MinIO   llama.cpp / 外部 LLM
```

### 7.2 原生与新增对照

| 层 | COA 原生 | 我们加的 | platform-core 残留 |
|---|---|---|---|
| UI | `web-app` 24 路由、Cloudscape | 6 条新路由 + 页面 | **0**（10 页 HTML 删除） |
| 入口 | `ControlPlaneService` + `DataLayerService` | 86 个新 operation 按 §5.0 分挂 `ControlPlaneService`（32）/ `DataLayerService`（18）/ `OntologyService`（36）；对外仍一个网关、一个 base URL | **0**（137 端点删除） |
| 服务 | 8 个原生包 | 各包内新增模块（§3.3 落点） | **0** |
| 端口 | `coa-ports` 13 端口 + 2 例外 | 不新增端口；`CanvasPort` 等留服务内部 | **0**（`ports.py` 删除） |
| 组合 | `coa-runtime` | 新增 provider 登记 | **0**（`assembly.py` 删除） |
| 实现 | `local-providers` 薄壳 | 搬入 `providers/` 的 11 类实现 | **0**（`platform_core` 引用归零） |
| 存储 | 本地 PG / Oxigraph / TEI / fs | 继续用现有 `platform.*` 表（一次性回填，见 §8.3） | 0 |

---

## 8. 四步下线路径与闸门

### 8.1 四步总览

| 步 | 动作 | 进入下一步的闸门（机械可查） |
|---|---|---|
| 1 | **能力搬迁**（搬一块验一块） | ① 迁移台账 100% 行有「已搬 / 已删」状态；② 每块能力在目标包有 ≥1 次**真跑通**；③ `grep -rn "platform_core" <目标包>` = 0；④ 双跑：同一请求在旧实现与新实现结果一致 |
| 2 | **出口切换**（137 端点不再对外） | ① 137 条路由访问日志连续 7 天 = 0（`/healthz` 除外，且它也已由 `HealthCheck` 承担）；② 86 个新 operation 按 §5.0 分挂三套契约，全部有契约测试与一次真跑通；③ `web-app` 网络请求只命中 Smithy 定义路径；④ C9 通过（对外只有一个 base URL）；⑤ 仅保留 8080 只读快照用于比对 |
| 3 | **目录删除** | ① `Test-Path packages/platform-core` = `False`；② `grep -rn "platform_core" --include=*.py --include=*.toml --include=*.yml .` = 0；③ compose / pyproject / uv workspace 无引用；④ CI 全绿 |
| 4 | **实例退役**（8080 / 8082） | §8.3 数据接管判据 8 条全绿 + 双跑 ≥14 天零差异；停服后 5173 全功能可用 |

### 8.2 第 4 步的硬约束

- **8080 是唯一完整数据实例**（3,066 文档 / 6 万级实例 / 已发布版本 610）。第 4 步必须最后做，且前置是「COA 能接管这批数据」。
- 接管 = **一次性回填 + 双跑比对 + 冻结写入**，三者缺一不可：
  1. 回填：文档与切片、图断言、本体版本与形状、指标定义与观测、PROV 活动、字典绑定，逐类导入 COA 存储。
  2. 冻结：回填完成即把 8080 置只读（禁止新写入），否则比对永远不收敛。
  3. 双跑：同一批请求同时打 8080 与 COA，比对结果；差异 = 0 才允许推进。

### 8.3 数据接管判据（可验证）

| # | 判据 | 机械检查 |
|---|---|---|
| T1 | 文档总量一致 | 8080 `count(documents)` = 3,066；COA `ListDocuments` 分页累加 = 3,066 |
| T2 | 切片一致 | 每文档 chunk 数逐条相等（3,066 条全量比对，不抽样）；缺失/多余 = 0 |
| T3 | 文档字节一致 | 随机 50 条 `DownloadDocument` 的 SHA-256 = 8080 原文件 SHA-256 |
| T4 | 实例断言一致 | 每个命名图的 statement 数相等（6 万级总量 + 分图计数） |
| T5 | 版本一致 | 已发布版本 610 在 `GetOntologyVersion` 的 `contentHash` 与 8080 相同；发布历史条数一致 |
| T6 | 黄金查询一致 | 固定 20 条（10 指标 / 5 SPARQL / 5 问答），结果规范化 JSON 的 SHA-256 两端相等 |
| T7 | 溯源一致 | 随机 20 个 fact/decision 的 PROV 链可解析，活动数与端点归属相同 |
| T8 | 指标行 100% 有命名空间归属（补 T3/T4 的覆盖空档） | 接管后：① 旧表每行 `metric_id` 在映射表中命中（未命中 = 0）；② 每条映射的目标 namespace 在 `ListNamespaces` 中存在（悬空 = 0）；③ 随机 20 条映射在 COA `GetMetric` 可读。三项任一不为 0 即判不过 |

任一判据不过，第 4 步不启动；差异必须定位到具体文档/断言/版本后才允许修复重跑。

T8 单独补空档的原因：T3/T4 比的是文档字节与命名图 statement 计数，**指标行不在覆盖范围**；而旧表 `platform.metric_definition` 没有 namespace 列（旧平台单租户、COA 多命名空间）。没有 T8，接管全做完也可能「假绿」——所有指标悬空却查不出。T8 是 `07-研发台账.md` §7.1 M3b 前置条件的机器兜底：映射表靠人执行，T8 靠机器发现悬空。

---

## 9. 收敛判据（「只有一个入口」怎么证明）

每轮交付都要跑，结果贴进当轮记录。以下命令为 PowerShell / bash 等价写法。

| # | 检查 | 命令（示例） | 通过标准 |
|---|---|---|---|
| C1 | 对外网关入口唯一 | `grep -rn "FastAPI(\|APIRouter(\|@app\.\(get\|post\|put\|delete\)" packages --include=*.py` | 只命中 `deploy/local/` 的网关适配层；网关内可挂 3 个 service router，但对外注册点 = 1，其余 0 |
| C2 | 路由由契约生成 | 对比 `grep -c "@http(" models/src/main/smithy/*.smithy` 与本地路由表导出行数 | 当前两侧相等（83 + 5 = 88，2026-11-09 实测）；86 个新 op 落地后两侧同为 174；任何时点两侧必须相等 |
| C3 | web-app 路由有背书 | `grep -o 'path="[^"]*"' packages/web-app/src/App.tsx \| sort -u` | 每条都在 §6.3 功能点表中有 operation 背书；无背书新增 = 0 |
| C4 | 无第二套 UI | `Test-Path packages/platform-core/web`；`grep -rn "webui" packages --include=*.py` | 均为 0 |
| C5 | 无第二套入口 | `grep -rn "create_app(" packages --include=*.py` | 0（`platform_core.api` 已删） |
| C6 | 无平台自有端口 | `grep -rn "class .*Port(Protocol)" packages/platform-core`（删除前）；`grep -rn "manifest()" packages/coa-ports` | 删除前只允许 platform 包内部；删除后为 0 |
| C7 | 目录归零 | `grep -rn "platform_core" --include=*.py --include=*.toml --include=*.yml .` | 0（历史文档除外） |
| C8 | 8080/8082 无监听 | `Test-NetConnection 127.0.0.1 -Port 8080` / `8082` | 第 4 步前允许监听；第 4 步后必须失败 |
| C9 | 对外 base URL 唯一 | `grep -rn "VITE_API_BASE\|baseURL\|API_BASE" packages/web-app --include=*.ts --include=*.tsx --include=*.mjs` | 只出现 1 个对外网关地址；`deploy/local/` 之外的构建产物不得内嵌第二个对外 base URL |

补充硬规则：

1. 新增任何对外路由，必须在同一次提交里出现对应的 Smithy operation；否则视为第二入口，直接拒绝。
2. 新增任何 UI 页面，必须在 `App.tsx` 路由旁标注 operation 名；否则视为第二套说法。
3. 健康检查只允许 `HealthCheck` / `GetSystemHealth` 两个 op；其他服务内的 `/health` 只能作为内部探针，不得对外暴露。
4. 「一个入口」= 一个网关、一个 base URL；service 数量不设上限，但新增 service 必须先在 §5.0 的归属表里登记，否则视为私活。

---

## 10. 落地顺序（先做哪三件，让 5173 有真东西）

**第 1 件：5173 接本地 control-plane + data-layer（2–3 人日）**
- 改 `packages/web-app/vite.dev-local.config.mjs`，把 `/ws` 与 API 代理指到本地 COA；`/namespaces`、`/namespaces/:id`、`/namespaces/:id/sources` 读真数据。
- 不依赖 `platform-core`，先把「前端 → 唯一入口」链路打通。闸门：三页无空态、无 mock。

**第 2 件：指标页与本体页接本地实现（3–5 人日）**
- 指标：`ListMetrics`/`GetMetric` 接本地 PG；本体：`ListOntologies`/`GetOntology`/`GraphSearch` 接 `GraphStorePort=oxigraph`。
- 闸门：`/namespaces/:id/metrics`、`.../metrics/:name`、`.../ontology`、`.../ontology/graph` 四条路由有真实数据。

**第 3 件：搬 `metric_facts.py` + 新增 `GetMetricObservations`（6–9 人日）**
- 按 §3.2 落点搬进 `metric-service/src/coa_metrics/observations/`，同批加 operation 与契约测试。
- 闸门：`/namespaces/:id/metrics/:metricName` 显示真实观测；`grep platform_core` 在该模块 = 0；旧 `metric_facts` 删除。

**后续批次**

| 批次 | 内容 | 目的 |
|---|---|---|
| A | 文档摄入 + 抽取审批 + `documents.html` 落点 | 打通「上传 → 切片 → 候选 → 审批」 |
| B | A-Box 账本 + 冲突处理 + `approvals` 落点 | 事实可写、可回滚 |
| C | 本体版本/治理 + bundle | 发布与迁移闭环 |
| D | 术语、影响、画布、健康、溯源、合成数据 | 补齐增量能力 |
| E | `ontology_pg` spike → ACL 接入 | 最后处理最大不确定项 |
| F | 出口切换 → 目录删除 → 数据接管 → 实例退役 | 四步下线 |

---

## 11. 与 `00-总计划.md` 的冲突点

> 本节只列差异；`00` 本次已落地的增补，逐条标在「建议」列。

| # | 计划现状 | 本方案结论 | 建议 |
|---|---|---|---|
| 1 | §1「`platform_core` 是实现库」 | 最终状态是**目录不存在**，不是长期实现库 | 已改为「过渡期实现库，阶段 7 删除」（已在 `00` §1 落地） |
| 2 | §3 原则表无「一个 UI/入口」 | 第一原则高于其余原则 | 增补为第 0 条（已在 `00` §3 落地） |
| 3 | §5 阶段 5/6 才做新特性 | 平台已有实现的特性应**搬迁**，不是阶段 5/6 重写；搬迁与阶段并行 | 阶段 5/6 判据加「平台已有实现按搬迁计，禁止重写」（已在 `00` §5 落地） |
| 4 | §5 阶段 7 只写「硬骨头 + 全量回归」 | 阶段 7 必须包含 `platform-core` 删除与 8080/8082 退役闸门 | 增补 §5.2 下线线（已在 `00` 落地） |
| 5 | §2 DoD 无「单一入口」判据 | 需要机械可查的收敛判据 | 增补 D8（已在 `00` 落地） |
| 6 | §5 阶段 1 判据未禁止第二套 UI/入口 | 阶段 1 起就不得新建第二套 | §11.5 增补第 7 条（已在 `00` 落地） |
| 7 | §4 现状「`platform_core` 43,775 行」 | 数量对，但未记 137 端点与 96 个可迁移能力 | 已在 `00` §4 增索引「137 端点 → operation 见 09 §4」 |
| 8 | §2 D1 的 `deploy/local/compose.yml` | 仓库当前不存在 | 未修复；登记为 W8（`11` §4），D1 完成前必须落地 |

---

## 12. 待决策与风险

1. **共享 `platform.*` schema 还是翻译层。** 建议先共用（回填最快），阶段 7 前不再改；隔离作为后续独立议题。
2. **`ontology_pg` 是否整体替换 `dynamo_store`。** 先 2–3 人日 spike 验证读写/版本/事务，再决定；失败则退回「PG 只存 T-Box 快照」的窄方案。
3. **86 个 operation 的命名与分组。** 已拍板（2026-11-09）：不挂同一 service，按 §5.0 分挂 `ControlPlaneService` 32 / `DataLayerService` 18 / `OntologyService` 36；对外仍一个网关、一个 base URL。命名不变，只改归属。
4. **合成数据是否需要对外 operation。** 若只用于测试，应放在 `scripts/`，不进契约；本方案暂按「有 UI 入口」处理。
5. **推理的 JVM 依赖。** 第一波只做 RDFS/SHACL，OWL 返回 `UnsupportedError`。
6. **工作量置信度。** 161–237 人日按模块行数与接口面估算，`ontology_pg`、`bundle`、数据接管三项误差各可达 ±50%。

---

## 13. 证据索引

| 事实 | 路径 |
|---|---|
| 137 个端点 | `packages/platform-core/src/platform_core/api.py`（路由装饰器扫描） |
| 平台自有端口 | `packages/platform-core/src/platform_core/ports.py:26-58` |
| 10 个 HTML | `packages/platform-core/web/*.html` |
| COA 契约 operation | `models/src/main/smithy/{control-plane,data-layer,serve,metric-service,ontology-graph,unified-sources,namespace,grant,role}.smithy` |
| COA 前端路由 | `packages/web-app/src/App.tsx:570-643` |
| 组合根与 catalog | `packages/coa-runtime/src/coa_runtime/` |
| 端口定义 | `packages/coa-ports/src/coa_ports/` |
| 本地 provider | `packages/local-providers/src/coa_local_providers/` |
| 计划与验收档位 | `doc/coa-x/00-总计划.md` §2、§3、§4.1、§5 |

---

## 14. 需扩展清单（2026-11-09 追加：A-Box「类下实例」）

**结论：契约里没有「查某个类下的实例」的 operation，本次不发明私活路由。** 下面两条是缺口与拟新增规格，派活依据。

### 14.1 缺口一：没有实例维度的 operation，也没有实例维度

实测（`models/src/main/smithy/ontology-graph.smithy`）：

- `GraphVertexKind` 只有 `class` / `object-property` / `datatype-property` / `annotation-property` / `ontology` / `property` / `literal` / `blank-node` / `unknown`，**没有 `individual`**。
- graph 组 14 个 operation 全是「按 IRI 取一个顶点」或「按子串搜」：`GraphSearch`、`GetGraphClass`、`GetGraphObjectProperty`、`GetGraphDatatypeProperty`、`GetOntologyOverview`。没有「按类列举实例」。
- 引擎里存在 `/graph/vertex`（任意顶点，不校验 kind）与 `/graph/schema`，但都**不在契约内**，8099 桥也不转发（`doc/coa-x/tools/coa_api_local.py` 的路由表只有 search / ontology-overview / class / object-property / datatype-property）。
- 平台的旧能力在 `POST /browse/ontology/instances?class=<iri>&limit=&offset=`（`packages/platform-core/src/platform_core/api.py:2434`），返回 `{class, items[{iri,label,graph}], total, limit, offset, pointer}`。这才是需要被 COA 契约接住的那条。

### 14.2 拟新增 operation：`ListGraphClassInstances`

```
GET /namespaces/{namespaceId}/graph/class/instances

input:
  namespaceId  Uuid        (httpLabel, required)
  uri          VertexIri   (httpQuery "uri", required)   与 GetGraphClass 同参，避免 IRI 双编码
  ontologyId   OntologyId  (httpQuery "ontology_id", optional)  限定单个命名图
  limit        Integer     (httpQuery, 1..500, 默认 50)
  offset       Integer     (httpQuery, 0..1000000, 默认 0)
output: GraphInstancePage
  items      GraphInstanceSummaryList   // { uri, label, graphUris, types }
  totalCount Integer                    // 独立于 limit/offset
  limit      Integer
  offset     Integer
errors: NotFoundError(类不在该命名空间) / ValidationError(IRI 非法、limit·offset 越界)
```

错误语义要点：

- 类存在但无实例 → `200` + `items: []` + `totalCount: 0`；只有「类本身不存在」才 `404`。与 8080 的行为一致（它返回空 items）。
- `totalCount` 与分页窗口必须由同一条 where 子句派生，服务端一次算清，前端不许自己猜。
- 排序必须确定（label 小写优先、IRI 兜底），否则 offset 分页会漂。
- 同时给 `GraphVertexKind` 补 `INDIVIDUAL = "individual"`；`GraphSearch` 命中实例时 `kind` 应报 `individual` 而不是现在的 `unknown`（实例的 `rdf:type` 不是 owl 元类，`_kind_from_type` 落空）。

### 14.3 缺口二（更硬）：现有 `GraphSearch` 在实例量级上跑不通

A-Box 灌入后实测（18,020 实例 / 121,130 三元组，同一台本机 Oxigraph）：

| 调用 | 结果 |
|---|---|
| `count_entities` 同一条 where（带 label `CONTAINS`） | 0.7 s |
| `search_entities`（内层带 label `CONTAINS` + 外层 `GRAPH ?g`） | **101.8 s** |
| 直接把同一段 SPARQL 发 Oxigraph | **134.3 s** |
| 经 8099 → 8101（读超时 30 s） | `500` / `The ontology service did not respond in time` |
| 同一条 SQL 换成 `GRAPH <常量图>` + 去掉 label `CONTAINS` | 0.2 s |

原因是查询形状：`GRAPH ?g { ?s ?_p ?_o }` + `FILTER(STRSTARTS(STR(?g), …))` 无法把图按下标裁剪，外层又对每条解重取 label/type，Oxigraph 规划成近似笛卡尔。**这不是「数据不对」，是「把实例塞进 T-Box 图存储」这条路本身不成立。**

因此：

1. 新 operation 必须**按类索引**取数（`?s a <类IRI>` + `GRAPH <图URI>` 常量绑定），禁止复用现在的 `GRAPH ?g` + STRSTARTS 形状。
2. 生产语义上实例本就不该常驻 T-Box 图：契约里 `coa:isMapped` 才是结构化 Tier-2（NL→SQL/Ontop）的入口。本地这份 A-Box 的 `agreement#Policy` 等类 `isMapped` 为空，说明「类→表→实例」的映射也没落，需要一起补。
3. 在 operation 落地前，5173 上**不做实例页**；验证只到存储与 SPARQL 层（见 `12-A-Box与写入链路本地化评估.md`）。

### 14.4 决策：`GraphSearch` 命名空间级检索改为常量图绑定（2026-11-10）

§14.3 的 101.8 s 与 M2 第一批的 90 s 是同一个病根：不传 `ontology_id` 时 `?g` 不绑定，`GRAPH ?g { … }` + `FILTER(STRSTARTS(STR(?g), …))` 让引擎先扫全库再过滤，外层又对每条解重取 label/type。

**测量（本机 Oxigraph，5 个命名图 / 123,828 三元组；同一查询形状、同一空结果集）：**

| 形状 | 耗时 |
|---|---|
| `GRAPH ?g` + `STRSTARTS`（原） | 86.281 s |
| `GRAPH ?g` + `VALUES ?g { 3 个命名空间图 }` | 0.058 s |
| `GRAPH <常量图>` | 0.0028 s |
| 仅枚举 `SELECT DISTINCT ?g WHERE { GRAPH ?g { } }` | 0.0036 s |

**结论：选方案 ②（枚举命名空间图 + 常量图绑定），不强制 `ontology_id`。** 理由：

1. 契约与 UI 都需要「整个命名空间」的浏览：`GraphSearch.ontology_id` 本就是可选，Explorer 的 `ALL_ONTOLOGIES` 是默认视图。强制必填等于用契约去补实现缺口，会把可用的浏览能力变成不可用。
2. 语义零变化：`VALUES` 列出的图与 `STRSTARTS` 接受的是同一集合（都按 `{base}/{namespace}/` 前缀），结果集与 `total_count` 不变（实测 namespace 路径 100 hits / total 156，与 `ontology_id` 路径一致）。
3. 不新建「按类索引」：图列表取自存储自身的命名图字典（3.6 ms），无一致性维护成本。按类索引留给 §14.3 的实例级 operation（那条仍必须 `?s a <类IRI>` + 常量图）。

**生产路径影响：AWS 默认不改。** 范围模式按 provider 决定：`COA_PROVIDER_ONTOLOGY_GRAPH=oxigraph`（本地）→ `values`；其余（Neptune、未设置）→ `prefix`，即原查询形状完全不变。原因是 Neptune 的执行计划依赖图统计，`VALUES` + `GRAPH` 没有生产实测，不在无证据时改线上形状。`COA_ONTOLOGY_GRAPH_SCOPE=values|prefix` 可单环境覆盖；切换只影响性能，不影响结果。

验证：`/namespaces/{ns}/graph/search?q=*&kind=class&limit=100` → 1.19 s（原同形状空结果集 86.3 s）；带 `ontology_id` → 0.52 s；相关单测 270 passed。
