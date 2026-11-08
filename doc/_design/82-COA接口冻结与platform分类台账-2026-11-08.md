# COA 接口冻结与 platform 分类台账（2026-11-08）

> 编号 82，承接 `81-COA契约与platform_core整合方案-2026-11-08.md`。
> 状态：P0 交付物，只读核实 + 文档/清单；未改业务代码、未动 8080、未启动长驻服务。
> 配套台账：[`82-platform-ledger.csv`](./82-platform-ledger.csv)（296 行，逐文件）。
> 行数口径：全文一律用**非空行**（与 79/80/81 一致）；物理行数只在对照处单独标注。

---

## 0. 结论摘要

| 项 | 结论 |
|---|---|
| 接口冻结范围 | COA 已有 15 个主抽象（E1–E15）+ 新增 12 个接口（N1–N12），合计 27 项，逐项冻结 |
| 判定分布 | 已有：14 够用、1 要扩展（`DataSourceLookup`）；新增：12；合计 27 |
| 优先级分布 | 必须有 16 项、以后再说 11 项 |
| 默认实现 | 每个接口一个 `COA_PROVIDER_<INTERFACE>`；默认值是 AWS 原实现，`COA_PROFILE=local` 只作未显式设置时的种子 |
| 混搭 | 逐接口允许；只承诺 V1–V4 四档组合，其余 `COA_ALLOW_UNVERIFIED_COMBOS=false` 启动失败 |
| 台账总量 | `platform/` 296 个文本/代码文件，非空 77,230 行，物理 84,434 行 |
| 产品代码 | `src/platform_core` Python 82 文件、43,775 非空行（物理 47,766）；A 6,208 / B 15,795 / C 17,162 / S 4,610 |
| SQL | 41 文件、5,964 非空行，全部 C/EXT，去向 `platform-core` |
| 闭合 | `43,775 = 6,208 + 15,795 + 17,162 + 4,610`；全部 scope 合计 77,230，逐项见 §6.3 |
| 4,810 vs 4,610 | 200 行差额**全部且仅在脚手架一个数字内**；4,810 比实测 4,610 多 200，且使 80 四项相加变成 43,975。4,810 无法从任何文件组合唯一复现，判定为笔误/未公开口径，不作为台账依据 |
| P0 是否有代码阻塞 | 无。P0 只产出文档与清单；`p0_blocking` 列按「是否阻塞紧随其后的 P1 全本地切片」判定 |

---

## 1. 冻结规则

### 1.1 取值定义

| 字段 | 取值 | 定义 |
|---|---|---|
| 判定 | 够用 / 要扩展 / 要新增 | 够用=签名可直接承载本地实现；要扩展=方向对但缺方法或返回结构；要新增=COA 无对应抽象 |
| 优先级 | 必须有 / 以后再说 | 必须有=P1/P2 阻塞；以后再说=位置预留、不阻塞 P1 |
| AWS 落点 | 文件:行号 类/函数 | 必须是 COA 上游已存在的实现，不写计划 |
| 本地落点 | `platform_core` 文件:类 | 已有文件必须写准文件名；没有现成实现的写「新增」并给建议文件 |
| 默认实现 | 实现名 | 未显式配置时的值；不等于推荐值 |
| 混搭 | 是 / 是（受限）/ 不适用 | 是否允许与其它接口不同族 |
| 已知约束 | 文本 | 混搭时必须满足的硬条件 |

### 1.2 配置解析（冻结，不允许扩展语义）

1. 一个接口一个 key：`COA_PROVIDER_<INTERFACE>`。
2. 显式 key > `COA_PROFILE` 种子；除这两层外没有回退。
3. 未设置且 profile 也没有种子 → 启动失败，不静默选 AWS 或本地。
4. 未知实现名 → 启动失败，不近似映射。
5. 未验证组合：`COA_ALLOW_UNVERIFIED_COMBOS=false`（默认）启动失败；`true` 仅告警并在 `/providerz` 标 `verified:false`。
6. 热切换：v1 一律重启生效；`/providerz` 只报告 `reload: "restart"`。

### 1.3 混搭总则

- 允许逐接口混搭，不允许「整体切 AWS/本地」的隐式假设。
- 混搭的正确性由三件事保证：provider 的 `capabilities()` 声明、启动期校验、`IndexProjector.verify` 差异集。
- 任何 provider 初始化失败都直接退出，不回落到另一实现。
- 只承诺 V1–V4 四档（§4）；其余组合「可配不承诺」。

### 1.4 行数口径（本次冻结）

| 对象 | 物理行 | 非空行 |
|---|---:|---:|
| `src/platform_core` Python（82 文件） | 47,766 | **43,775** |
| `api.py` | 6,280 | **5,891** |
| 15 个 `smoke*.py` | 5,116 | **4,610** |
| `tests/*.py` | 14,674 | **12,841** |
| `web/` | — | **6,255** |

79/80/81 引用的 `43,775`、`5,891`、`4,610` 都是非空行。后续文档如未特别说明，行数一律指非空行。

---

# 第一部分 接口冻结（交付一）

## 2. 已有抽象 E1–E15

### E1 `GraphClient`

- **签名/IO**：`async query(sparql: str) -> list[dict]`；`async ask(sparql: str) -> bool`；`async health_check() -> dict`。输入是 SPARQL 文本，输出是绑定行列表或布尔。
- **错误语义**：查询失败抛后端异常/超时；`health_check` 永不抛，返回状态字典。
- **判定**：够用。
- **优先级**：必须有。
- **AWS 落点**：`packages/context-manager/src/coa_serve/clients/neptune.py:118` `NeptuneGraphClient`。
- **本地落点**：`platform/src/platform_core/adapters/graph_oxigraph.py`（`OxigraphHttpStore`，同步 port 需 async 薄壳）；`adapters/graph_fuseki.py`（`FusekiHttpStore`）。
- **默认实现**：AWS `neptune`；V1 为 `oxigraph`。
- **配置 key/默认值**：`COA_PROVIDER_GRAPH`，默认 `neptune`。
- **混搭/约束**：允许。只承诺 SPARQL 1.1 共同子集，不使用 Neptune 扩展语法；变量图查询走守卫。

### E2 `VectorClient`

- **签名/IO**：`async search(query_vector, *, namespace, top_k, index, entity_type, require_mapped, ontology_ids, query_backend) -> list[VectorHit]`；`async hybrid_search(query_text, query_vector, *, namespace, top_k, index) -> list[VectorHit]`；`async health_check() -> dict`。
- **错误语义**：search 失败抛出；`VectorHit.score` 必须是 0–1 余弦；`health_check` 永不抛。
- **判定**：够用。
- **优先级**：必须有。
- **AWS 落点**：`packages/context-manager/src/coa_serve/clients/opensearch.py:121` `OpenSearchVectorClient`。
- **本地落点**：`adapters/vector_pg.py`（`PgVectorStore`）+ `adapters/search_pg.py`（`PgSearchIndex`），async 薄壳。
- **默认实现**：AWS `aoss`；V1 为 `pgvector`。
- **配置 key/默认值**：`COA_PROVIDER_VECTOR`，默认 `aoss`。
- **混搭/约束**：允许。向量模型与维度必须与写入侧一致；`search_nearest` 余弦区间强制；AOSS 最终一致必须在 `capabilities()` 声明。

### E3 `LLMClient`

- **签名/IO**：`async converse(prompt, *, system, guardrail_id, max_tokens, temperature, top_p, guard_content, model_id) -> ConverseResult`；`converse_stream(...) -> AsyncIterator[str]`；`async embed(text) -> list[float]`；`async health_check() -> dict`。
- **错误语义**：护栏拦截抛 `GuardrailBlockedError`；模型自过滤抛 `ContentFilteredError`；截断由 `ConverseResult.truncated` 显式可见；`health_check` 永不抛。
- **判定**：够用（能力上报通过新增可选方法 `capabilities()`，不改已有签名）。
- **优先级**：必须有。
- **AWS 落点**：`packages/context-manager/src/coa_serve/clients/bedrock.py:309` `BedrockLLMClient`。
- **本地落点**：`adapters/llm_openai.py`（`LlmClient`，OpenAI 兼容；需补 `converse`/`converse_stream` 薄壳）；`adapters/embedding.py`（`EmbeddingClient`）。
- **默认实现**：AWS `bedrock`；V1 为 `openai` + `tei`。
- **配置 key/默认值**：`COA_PROVIDER_LLM` 默认 `bedrock`；`COA_PROVIDER_EMBEDDING` 默认 `bedrock`。
- **混搭/约束**：允许。本地无护栏时 `GuardrailOutcome` 必须显式返回 `NONE` 并记录「无护栏」，不得冒充已护栏；截断必须可见。

### E4 `QueryExecutor`

- **签名/IO**：`async execute(sql, *, namespace, data_source_id, params, max_rows, timeout_seconds) -> QueryResult(rows, columns, row_count, truncated, duration_ms, engine)`；`async health_check() -> dict`。
- **错误语义**：SQL/权限/超时抛出；结果截断必须置 `truncated=True`；`health_check` 永不抛。
- **判定**：够用。
- **优先级**：必须有。
- **AWS 落点**：`clients/athena.py:151` `AthenaQueryExecutor`；`clients/redshift_data.py:79` `RedshiftDataAPIExecutor`；`clients/source_db.py:121` `SourceDBQueryExecutor`；`clients/composite_executor.py:43` `CompositeQueryExecutor`。
- **本地落点**：新增 `platform-core/providers/query_pg.py`（薄壳，复用 `adapters/metadata_pg.py:MetadataPg` 的连接；平台当前没有现成 Executor 抽象）。
- **默认实现**：AWS `composite`；V1 为 `postgres`。
- **配置 key/默认值**：`COA_PROVIDER_QUERY_EXECUTOR`，默认 `composite`。
- **混搭/约束**：允许，但必须与 `SourceCatalog` 同族；异构时硬校验降级为结构校验并显式标 `source_enforcement=false`。

### E5 `GraphStore`

- **签名/IO**：17 个同步方法——ontology CRUD 5、schema 元素 3、批量 Turtle 2、统计/顶点/搜索 5、namespace schema/健康 2（完整签名见 81 附录 A）。核心：`create_ontology/get_ontology/update_ontology/delete_ontology`、`store_class/store_property`、`bulk_load_turtle`、`search_graph`、`health_check`。
- **错误语义**：缺省返回 `None`/`False` 表示不存在；后端不可枚举时返回 `None` 或 `skipped`，不伪造空结果；`health_check` 永不抛。
- **判定**：够用；**列表权威不在 GraphStore**，另立 `OntologyRegistry`（N2）。
- **优先级**：必须有。
- **AWS 落点**：`packages/ontology-engine/src/coa_ontology/stores/neptune_db_graph.py:503` `NeptuneDBGraphStore`；`stores/na_graph.py:19` `NeptuneAnalyticsGraphStore`。
- **本地落点**：`adapters/ontology_pg.py:OntologyRegistry`（已有）+ `adapters/graph_oxigraph.py`/`graph_fuseki.py` 的 SPARQL 读写；17 方法适配层建议新增 `platform-core/providers/graph_store_adapter.py`。
- **默认实现**：AWS `neptune_db`；V1 为 `ontology_pg` + `oxigraph`。
- **配置 key/默认值**：`COA_PROVIDER_GRAPH_STORE`，默认 `neptune_db`。
- **混搭/约束**：允许。`ontology_id` 必须来自 `OntologyRegistry`；图侧不得自行发现本体；切换图实现后必须 `IndexProjector.reindex`。

### E6 `VectorStore`

- **签名/IO**：`dimensions: int` + 10 个同步方法——写入 2、读取 3、搜索 1、删除 3、健康 1。核心：`store_embedding/store_embeddings_batch`、`search_nearest`、`delete_embeddings_for_ontology`、`delete_index`、`health_check`。
- **错误语义**：`search_nearest` 的 `score` 必须统一为 `[-1,1]` 余弦；删除不能全删时抛异常；`delete_index` 返回是否存在；`health_check` 永不抛。
- **判定**：够用（`OpenSearchVectorStore` 的 `[0,1]` 语义差见 S15，属实现缺陷，不改契约）。
- **优先级**：必须有。
- **AWS 落点**：`stores/opensearch_vector.py:56` `OpenSearchVectorStore`；`stores/na_vector.py:22` `NeptuneAnalyticsVectorStore`。
- **本地落点**：`adapters/vector_pg.py:PgVectorStore`。
- **默认实现**：AWS `aoss`；V1 为 `pgvector`。
- **配置 key/默认值**：`COA_PROVIDER_VECTOR_STORE`，默认 `aoss`。
- **混搭/约束**：允许。维度启动即固定；切换必须重建索引；删除必须允许部分失败并抛出。

### E7 `LexicalGraphStore`

- **签名/IO**：`get_class_nodes() -> list[ClassRecord]`；`get_class_relations() -> list[RelationRecord]`；`get_entities_by_class(classification, limit) -> list[EntityRecord]`；`get_facts_for_entities(entity_ids) -> list[FactRecord]`（>500 必须分批）；`get_topics() -> list[TopicRecord]`；`get_graph_schema() -> ClassSchemaResult`。
- **错误语义**：无匹配返回空列表；批量超限必须分批而非截断；后端失败抛出。
- **判定**：够用。
- **优先级**：以后再说（induction 用）。
- **AWS 落点**：`packages/ontology-engine/src/coa_ontology/inducer/unstructured/stores/na_lexical.py:320` `NeptuneAnalyticsLexicalStore`；`ndb_lexical.py:51` `NeptuneDatabaseLexicalStore`。
- **本地落点**：复用 `lexical_graph` 投影；新增 `platform-core/providers/lexical_pg.py`（基于 PG，按 class/fact 投影）。
- **默认实现**：AWS `na_lexical`；V1 为 `pg_projection`。
- **配置 key/默认值**：`COA_PROVIDER_LEXICAL_STORE`，默认 `na_lexical`。
- **混搭/约束**：是（受限）。必须读同一张图；graph=AWS 时 lexical 只能走 Neptune 同源，不能本地另起一份。

### E8 `DataSourceLookup`（→ N4 `SourceCatalog`）

- **签名/IO**：`data_source_exists(id) -> bool`；`table_exists(id, table) -> bool`；`get_table_columns(...) -> list[ColumnMetadata] | None`；`catalog_available(id) -> bool`；`known_tables(id) -> set[str]`；`table_rejection_reason(...) -> str | None`；`get_column_type(...)`。
- **错误语义**：缺省 fail-open：无法枚举时 `known_tables` 为空，使「表不存在」不可证明，不得硬拒；`None` 表示元数据不可读，不是「不存在」。
- **判定**：**要扩展**。缺 `list_sources`、`get_source`、`list_tables` 分页、审批状态、`discover`。扩展后即 N4。
- **优先级**：必须有（扩后）。
- **AWS 落点**：`packages/metric-service/src/coa_metrics/lookups.py:249` `SmusCatalogDataSourceLookup`。
- **本地落点**：`adapters/metadata_pg.py:MetadataPg` + 指标 binding 表。
- **默认实现**：AWS `smus`；V1 为 `postgres`。
- **配置 key/默认值**：`COA_PROVIDER_METADATA`，默认 `smus`。
- **混搭/约束**：允许。与 QueryExecutor 混族时只能 fail-open，不得硬拒表不存在；审批状态必须显式。

### E9 `MetadataStoreClient`

- **签名/IO**：10 个同步方法——项目 3（`create_project/delete_project/get_project`）、资产 6（`create_asset/create_asset_revision/delete_asset/get_asset/search_assets/get_asset_forms`）、成员 1（`create_project_membership`）。
- **错误语义**：统一抛 `MetadataStoreError`（继承 `SCLError`）；未找到也抛。
- **判定**：够用（SMUS 语义）。
- **优先级**：以后再说（P3 数据源）。
- **AWS 落点**：`libs/common/src/coa_common/metadata_store/smus.py:65` `SMUSClient`。
- **本地落点**：`adapters/metadata_pg.py` 把 project/asset 映射到 schema/table；不共享 ID 空间。
- **默认实现**：AWS `smus`；V1 为 `postgres`。
- **配置 key/默认值**：`COA_PROVIDER_METADATA_STORE`，默认 `smus`。
- **混搭/约束**：允许。project/asset ID 空间与 namespace 分离；不得把 `asset_id` 当 `namespace_id`。

### E10 `EngineAdapter`

- **签名/IO**：ABC；`async open_connection(DBCredentials) -> ConnHandle`；`async run(conn, sql, params, timeout_seconds, schema) -> (rows, columns)`；`async close(conn)`；钩子 `inject_limit(sql, max_rows)`。
- **错误语义**：连接/执行失败抛驱动异常；`inject_limit` 解析失败时回退到引擎自己的行数限制写法（SQL Server 用 `TOP`）。
- **判定**：够用。
- **优先级**：以后再说（外部库）。
- **AWS 落点**：`clients/db_adapters/mysql.py:44`、`postgres.py:78`、`postgres.py:203` `RedshiftAdapter`、`sqlserver.py:55`。
- **本地落点**：不新增本地替代；按数据源引擎选择；PG 复用 `postgres.py` 分支即可。
- **默认实现**：由数据源配置决定，不设全局默认。
- **配置 key/默认值**：`COA_PROVIDER_ENGINE_ADAPTER`，默认 `auto`（按 source 的 engine 解析）。
- **混搭/约束**：不适用。同一 source 固定一个 adapter，无跨引擎混搭。

### E11 `StructuredQueryStrategy`

- **签名/IO**：`name: str`；`supported_backends: frozenset[StructuredBackend]`；`async resolve(query, namespace, context) -> StrategyResult | None`。
- **错误语义**：返回 `None` 表示未命中而非失败；异常由 runner 记录并降级。
- **判定**：够用。
- **优先级**：必须有（Tier2 本地策略）。
- **AWS 落点**：`tier2/nl_to_sql/strategy.py:241` `NLtoSQLStrategy`；`tier2/nl_to_sql/agentic_strategy.py:124` `AgenticStrategy`；`tier2/ontop/strategy.py:71` `OntopStrategy`；`tier2/sparql/strategy.py:86` `SparqlStrategy`。
- **本地落点**：新增 `platform-core/providers/strategy_local.py`，包装 `facts.py`/`context.py`，复用 `metric_compiler.py`。
- **默认实现**：AWS `nl_to_sql`；V1 为 `local_facts`。
- **配置 key/默认值**：`COA_PROVIDER_STRATEGY`，默认 `auto`（按 `supported_backends` 选择）。
- **混搭/约束**：允许。每个策略声明 `supported_backends`；并行超时与空结果置信下限一致。

### E12 `OntologySource`

- **签名/IO**：`async load(namespace) -> Ontology`。
- **错误语义**：后端失败必须抛出，由 Tool 记录来源与失败。
- **判定**：够用。
- **优先级**：以后再说（Agentic Tier3）。
- **AWS 落点**：`tier3/agentic/ontology/factory` 按 graph/vector 构造（NDB/NA 源）。
- **本地落点**：`adapters/ontology_pg.py:OntologyRegistry`（只读已发布版本）。
- **默认实现**：AWS `ndb`；V1 为 `ontology_pg`。
- **配置 key/默认值**：`COA_PROVIDER_ONTOLOGY_SOURCE`，默认 `ndb`。
- **混搭/约束**：允许。只读已发布图；未发布草稿不可见。

### E13 `Tool`

- **签名/IO**：`name`/`description`/`input_schema`/`output_schema` 4 个必填字段；`async invoke(*, namespace, **kwargs) -> ToolResult`。
- **错误语义**：注册时校验字段非空与 schema 为 dict；运行失败抛。
- **判定**：够用。
- **优先级**：以后再说。
- **AWS 落点**：`tier3/agentic/tools/` 现有 Agentic tools（检索、SPARQL、SQL 等）。
- **本地落点**：`platform-ext` 的检索/事实工具；接口层新增 `platform-ext/tools/registry.py`。
- **默认实现**：AWS `coa_agentic`；V1 为 `platform_ext`。
- **配置 key/默认值**：`COA_PROVIDER_TOOLSET`，默认 `coa_agentic`。
- **混搭/约束**：允许。每个工具单独选 provider；schema 必须自洽。

### E14 `SparqlEndpointClient`

- **签名/IO**：`async query(sparql, *, max_results) -> list[dict]`；`async ask(sparql) -> bool`；`async construct(sparql, *, max_triples) -> list[{'s','p','o'}]`；`async close()`。
- **错误语义**：引擎不支持抛 `UnsupportedSparqlEngineError`；查询失败抛。
- **判定**：够用。
- **优先级**：以后再说（多源 A-Box）。
- **AWS 落点**：`clients/sparql_clients.py:103` `SparqlClientCache` 的 Neptune 分支（`build_sparql_client`）。
- **本地落点**：`adapters/graph_oxigraph.py` / `graph_fuseki.py` 新增 `SparqlEndpointClient` 分支。
- **默认实现**：AWS `neptune`；V1 为 `oxigraph`。
- **配置 key/默认值**：`COA_PROVIDER_SPARQL_ENDPOINT`，默认 `neptune`。
- **混搭/约束**：允许。按 source 配置选引擎，不支持引擎显式报错。

### E15 `MetadataConnector`

- **签名/IO**：`test_connection(config) -> ConnectionTestResult`；`discover_metadata(config) -> DiscoveredMetadata`。
- **错误语义**：连接失败按现有连接器实现返回失败结果或抛出；发现失败抛。
- **判定**：够用。
- **优先级**：以后再说（数据源接入）。
- **AWS 落点**：`packages/sources/src/coa_sources/database/connectors/custom_connector.py:162`；`glue_catalog.py:43`；各 Dialect。
- **本地落点**：新增 `platform-core/providers/connector_pg.py`（PG/文件连接器）。
- **默认实现**：AWS `glue`；V1 为 `postgres`。
- **配置 key/默认值**：`COA_PROVIDER_METADATA_CONNECTOR`，默认 `glue`。
- **混搭/约束**：允许。连接器与数据源类型绑定，不跨源复用凭证。

---

## 3. 新增接口 N1–N12

> 以下签名是**冻结的最小集**；实现可以增加可选方法，不得改已有方法语义。

### N1 `NamespaceRegistry`

- **签名/IO**：`create(name, description) -> NamespaceRecord`；`get(id) -> NamespaceRecord | None`；`list(limit, offset) -> list[NamespaceRecord]`；`update_status(id, status) -> NamespaceRecord`；`delete(id) -> bool`。
- **错误语义**：`NamespaceExists` / `NamespaceNotFound` / `NamespaceNotEmpty`；ID 由注册表生成，不由调用方编造。
- **判定**：要新增。
- **优先级**：必须有。
- **AWS 落点**：`packages/control-plane/src/coa_control_plane/namespace/create_handler.py:36` 及同型 handler 的 `DynamoDBDAO`。
- **本地落点**：`adapters/metadata_pg.py` + `namespace` 表（新增）。
- **默认实现**：AWS `dynamo`；V1 为 `postgres`。
- **配置 key/默认值**：`COA_PROVIDER_NAMESPACE_REGISTRY`，默认 `dynamo`。
- **混搭/约束**：允许。必须与 graph/vector 的作用域 key 一致；ID 由注册表生成。

### N2 `OntologyRegistry`

- **签名/IO**：`create(namespace, ontology_uri, title) -> OntologyRecord`；`get(id) -> OntologyRecord | None`；`list(namespace) -> list[OntologyRecord]`；`update_status(id, status) -> OntologyRecord`；`delete(id) -> bool`；`resolve_graph_uri(namespace, ontology_id) -> str`。
- **错误语义**：`OntologyNotFound`；`OntologyAlreadyPublished`；注册表是列表权威，图存储不得自行发现。
- **判定**：要新增（从 `GraphStore` 拆出）。
- **优先级**：必须有。
- **AWS 落点**：`packages/control-plane` 的 `dynamo_store.list_ontologies_registry` / registry DAO。
- **本地落点**：`adapters/ontology_pg.py:OntologyRegistry`（已有同名类）。
- **默认实现**：AWS `dynamo`；V1 为 `ontology_pg`。
- **配置 key/默认值**：`COA_PROVIDER_ONTOLOGY_REGISTRY`，默认 `dynamo`。
- **混搭/约束**：允许。列表权威；与 `GraphStore` 混用时按 `ontology_id` 对齐，不做双向发现。

### N3 `MetricRepository`

- **签名/IO**：`create/get/list/update/delete/validate/bulk_delete`；`import_osi/export_osi`；`get_import_job(job_id)`。
- **错误语义**：`MetricNameConflict`；`MetricNotFound`；`MetricNotExecutable`；不可执行不得返回结果。
- **判定**：要新增。
- **优先级**：必须有。
- **AWS 落点**：`packages/metric-service/src/coa_metrics/api/*.py` + Dynamo 表。
- **本地落点**：`metrics.py:MetricService` + `metric_loader.py` + PG 表。
- **默认实现**：AWS `dynamo`；V1 为 `postgres`。
- **配置 key/默认值**：`COA_PROVIDER_METRIC_REPOSITORY`，默认 `dynamo`。
- **混搭/约束**：允许。与 `SourceCatalog` 同族优先；异构时指标只能「结构可算」，不得标「可执行」。

### N4 `SourceCatalog`（E8 扩展）

- **签名/IO**：`list_sources(namespace) -> list[SourceRecord]`；`get_source(id) -> SourceRecord | None`；`list_tables(id, limit, offset) -> list[TableRecord]`；`get_table(id, table) -> TableRecord | None`；`approve(id)/reject(id)`；`discover(id) -> JobHandle`；保留 E8 的 7 个方法。
- **错误语义**：`SourceNotFound`；`TableUnprovable`（不可证明不存在时不得硬拒）；审批状态必须显式。
- **判定**：要扩展。
- **优先级**：必须有（P2）。
- **AWS 落点**：`lookups.py:249` `SmusCatalogDataSourceLookup` + SMUS asset 列表。
- **本地落点**：`adapters/metadata_pg.py:MetadataPg` + `data_source`/`table` 表。
- **默认实现**：AWS `smus`；V1 为 `postgres`。
- **配置 key/默认值**：`COA_PROVIDER_SOURCE_CATALOG`，默认 `smus`。
- **混搭/约束**：允许。与 `QueryExecutor` 混族时只能 fail-open。

### N5 `ConversationStore`

- **签名/IO**：`create(user_id, namespace, title) -> SessionRecord`；`validate_ownership(user_id, session_id) -> bool`；`update_activity(...)`；`list_sessions(...)`；`get_history(session_id, limit, before)`；`delete(session_id)`。
- **错误语义**：`SessionNotFound`；`SessionForbidden`；TTL 到期视为不存在。
- **判定**：要新增。
- **优先级**：以后再说（P3）。
- **AWS 落点**：`packages/context-manager/src/coa_serve/session_metadata.py:53` `SessionMetadataStore`（Dynamo）。
- **本地落点**：新增 `platform-core/providers/session_pg.py`（PG `session_metadata` 表）。
- **默认实现**：AWS `dynamo`；V1 为 `postgres`。
- **配置 key/默认值**：`COA_PROVIDER_SESSION`，默认 `dynamo`。
- **混搭/约束**：允许。TTL 由 session 侧声明；storage 侧不重复设 TTL；删除只能尽力级联。

### N6 `MemoryStore`

- **签名/IO**：`append_turn(session_id, turn) -> TurnRecord`；`get_window(session_id, turns) -> list[TurnRecord]`；`search(namespace, query, top_k)`；`delete_session(session_id)`；`gc(expires_before)`。
- **错误语义**：`MemoryExpired`；写入失败不得阻断回答，必须降级并留痕。
- **判定**：要新增。
- **优先级**：以后再说（P3）。
- **AWS 落点**：`packages/context-manager/src/coa_serve/session.py` `SessionManager`（AgentCore Memory）。
- **本地落点**：新增 `platform-core/providers/memory_pg.py`（PG `session_turn` 表）。
- **默认实现**：AWS `agentcore`；V1 为 `postgres`。
- **配置 key/默认值**：`COA_PROVIDER_MEMORY`，默认 `agentcore`。
- **混搭/约束**：允许。与 `ConversationStore` 生命周期对齐；跨 store 无事务，失败降级并留痕。

### N7 `JobQueue`

- **签名/IO**：`submit(kind, payload, *, namespace, idempotency_key) -> JobHandle`；`status(job_id) -> JobStatus`；`cancel(job_id) -> bool`。
- **错误语义**：至少一次投递；幂等键冲突返回既有 Job；状态机 `queued/running/succeeded/failed/cancelled`。
- **判定**：要新增。
- **优先级**：以后再说（P3，induction/scan）。
- **AWS 落点**：SQS / Step Functions / Lambda 异步。
- **本地落点**：`inline` 同步执行器；P3 可加 PG 队列（新增 `platform-core/providers/job_inline.py`）。
- **默认实现**：AWS `sqs`；V1 为 `inline`。
- **配置 key/默认值**：`COA_PROVIDER_DISPATCH`，默认 `sqs`。
- **混搭/约束**：允许。至少一次语义；必须带幂等键；inline 实现返回已完成句柄，不假装异步。

### N8 `ObjectStore`

- **签名/IO**：`put/get/head/delete/list`；`presign_put(key, ttl, content_type) -> UploadTicket`；`presign_get(key, ttl) -> str`；`capabilities()`。
- **错误语义**：`ObjectNotFound`；`PreconditionFailed`；`ObjectTooLarge`；无预签名能力时 `upload_mode="proxy"`，不得假装支持。
- **判定**：要新增。
- **优先级**：必须有。
- **AWS 落点**：S3 + 预签名。
- **本地落点**：`adapters/object_fs.py:FsCasBackend`；`object_layered.py:LayeredObjectStore`；`object_pg.py:PgByteaBackend`。
- **默认实现**：AWS `s3`；V1 为 `fs`。
- **配置 key/默认值**：`COA_PROVIDER_STORAGE`，默认 `s3`。
- **混搭/约束**：允许。预签名能力必须在 `capabilities()` 声明；不支持时走代理上传。

### N9 `SecretProvider`

- **签名/IO**：`get(name: str) -> str`。
- **错误语义**：`SecretNotFound`；永不记录值；缺失时 fail-closed，不回落到默认口令。
- **判定**：要新增。
- **优先级**：必须有。
- **AWS 落点**：Secrets Manager / IAM。
- **本地落点**：`ports.py:EnvSecretProvider`（已有）。
- **默认实现**：AWS `aws_secrets_manager`；V1 为 `env`。
- **配置 key/默认值**：`COA_PROVIDER_SECRET`，默认 `aws_secrets_manager`。
- **混搭/约束**：允许。缺失 fail-closed；不得日志输出值。

### N10 `CredentialProvider`

- **签名/IO**：`resolve_db(namespace, data_source_id) -> DBCredentials`。
- **错误语义**：`CredentialUnavailable`；不得返回匿名连接。
- **判定**：要新增。
- **优先级**：以后再说（外部库 P3）。
- **AWS 落点**：Secrets Manager + SMUS。
- **本地落点**：新增 `platform-core/providers/credential_pg.py`（PG 凭证表 + 环境变量，仅本地）。
- **默认实现**：AWS `secrets_manager`；V1 为 `pg_env`。
- **配置 key/默认值**：`COA_PROVIDER_CREDENTIAL`，默认 `secrets_manager`。
- **混搭/约束**：允许。本地凭证表仅开发；生产必须外部密钥源。

### N11 `ObservabilitySink`

- **签名/IO**：`span(name, attributes)` 上下文；`metric(name, value, unit, tags)`；`event(kind, payload)`。
- **错误语义**：永不向业务路径抛；丢弃时计数自增。
- **判定**：要新增。
- **优先级**：必须有（最小）。
- **AWS 落点**：CloudWatch EMF / X-Ray。
- **本地落点**：`logging_setup.py` + 本地事件表。
- **默认实现**：AWS `cloudwatch`；V1 为 `local`。
- **配置 key/默认值**：`COA_PROVIDER_OBSERVABILITY`，默认 `cloudwatch`。
- **混搭/约束**：允许。只降级不阻断；provider 名必须进 span 标签。

### N12 `IndexProjector`

- **签名/IO**：`project(ontology_id, entities) -> ProjectionResult`；`verify(ontology_id, expected) -> VerifyResult`；`reindex(namespace) -> JobHandle`。
- **错误语义**：不得宣称跨图/向量原子性；`verify` 必须返回差异集合；失败可重试且幂等。
- **判定**：要新增。
- **优先级**：必须有（P2 混搭）。
- **AWS 落点**：最终一致轮询（AOSS/NA 语义）。
- **本地落点**：`adapters/embedding.py:EmbeddingClient` + `reindex.py:ReindexService` + 同步投影。
- **默认实现**：AWS `eventual`；V1 为 `sync`。
- **配置 key/默认值**：`COA_PROVIDER_INDEX_PROJECTOR`，默认 `eventual`。
- **混搭/约束**：允许。一致性模式 `sync` / `eventual` 必须显式；不得声称跨库原子。

---

## 4. 配置矩阵与已验证组合

| 组合 | graph | vector | llm | metadata | storage | session | dispatch | 状态 |
|---|---|---|---|---|---|---|---|---|
| V1 全本地 | oxigraph | pgvector | openai | postgres | fs | postgres | inline | P1 验收 |
| V2 仅图换 AWS | neptune | pgvector | openai | postgres | fs | postgres | inline | P2 验收 |
| V3 图+向量 AWS | neptune | aoss | openai | postgres | fs | postgres | inline | P3 验收 |
| V4 全 AWS | neptune | aoss | bedrock | smus | s3 | dynamo | sqs | P4 验收 |

只承诺这四档。其余组合技术上可配、但不承诺可用；`COA_ALLOW_UNVERIFIED_COMBOS=false` 时启动失败。

---

## 5. 隐式耦合与混搭约束

| 耦合点 | 症状 | 接口层规则 |
|---|---|---|
| graph ↔ vector | 图删了向量还在；图更新向量是旧描述 | 由 `IndexProjector` 统一投影；先落图再投影；`verify` 返回差异集；禁止跨库事务承诺；切换任一实现必须 `reindex` |
| namespace ↔ graph/vector | 本地建了 namespace，AWS 图不认识 | `NamespaceRegistry` 是作用域权威；所有 store 构造必须带 namespace 并先 `get()` 校验 |
| ontology registry ↔ graph | ListOntologies 与 GraphSearch 对不上 | registry 拥有 ID 与状态；graph 只按 ID 存取；禁止从图反推本体列表 |
| metric repo ↔ source catalog ↔ executor | 指标引用的 dataSourceId 在另一族目录不存在 | 三者同族优先；异构时 `source_enforcement=false`，指标最多「结构可算」 |
| session ↔ memory ↔ storage | session 过期 memory 还在；附件无人回收 | TTL 只由 `ConversationStore` 声明；`MemoryStore` 按其过期；`ObjectStore` 用 `gc` 尽力回收 |
| ObjectStore ↔ 上传契约 | 本地没有预签名，上传 URL 语义断裂 | `capabilities().presign` 如实；不支持时 `upload_mode="proxy"`，不返回假 URL |
| auth ↔ local | 本地无策略引擎，`auth_enabled=true` 却放行 | 鉴权启用而 provider 无策略引擎时 fail-closed 启动失败 |
| observability ↔ providers | 出问题不知道走哪个实现 | 所有 span/metric 必须带 `provider.<interface>=<name>` 标签 |

---

# 第二部分 分类台账（交付二）

## 6. 台账说明

### 6.1 文件与范围

- 范围：`platform/` 下全部文本/代码文件，排除 `logs/`（运行日志）、`.pdf`（二进制）、`.lock`、`__pycache__`、`node_modules`、`.venv`、`dist`、`build`。
- 文件数：296。
- 非空行合计：77,230；物理行合计：84,434。
- `A/B/C` 只适用于产品代码（`product` + `sql`）；`S` 是 smoke 脚手架，按 80 的四桶口径单列；测试/前端/脚本/配置/文档/数据/基础设施用 `T/W/O/F/D/I`，不计入 A/B/C 小计。

### 6.2 实测汇总

`src/platform_core` Python（82 文件、43,775 非空行）：

| 桶 | 文件数 | 非空行 | 含义 |
|---|---:|---:|---|
| A | 27 | 6,208 | 实现 COA 已有接口的 provider / 装配 / 解析校验 |
| B | 9 | 15,795 | 与 COA 同职责但需适配或收敛 |
| C | 31 | 17,162 | COA 没有的净新增能力（含工具） |
| S | 15 | 4,610 | 验收 smoke 脚手架 |
| **合计** | **82** | **43,775** | 与 79/80/81 对齐 |

按 `class`（全部 296 文件）：

| class | 文件数 | 非空行 | 含义 |
|---|---:|---:|---|
| A | 27 | 6,208 | 可回灌 |
| B | 9 | 15,795 | 与 COA 重叠 |
| C | 72 | 23,126 | 净新增（含 41 个 SQL） |
| S | 15 | 4,610 | smoke 脚手架 |
| T | 56 | 13,418 | 测试 |
| W | 25 | 6,255 | 前端 |
| O | 11 | 1,787 | 运维脚本 |
| F | 18 | 2,318 | 配置/文档 |
| D | 55 | 3,263 | 数据/夹具/种子/示例 |
| I | 8 | 450 | 独立基础设施镜像 |
| **合计** | **296** | **77,230** | — |

SQL（41 文件、5,964 非空行）：全部 `C/EXT`，去向 `platform-core`；product 段表不含 SQL，class 表的 `C=72` 由 31 个 product C + 41 个 SQL 组成。

按 scope：

| scope | 文件数 | 非空行 | 物理行 |
|---|---:|---:|---:|
| product | 82 | 43,775 | 47,766 |
| sql | 41 | 5,964 | 6,207 |
| test | 56 | 13,418 | 15,326 |
| fixture | 45 | 2,791 | 2,804 |
| web | 25 | 6,255 | 6,730 |
| ops | 11 | 1,787 | 1,933 |
| config | 13 | 830 | 896 |
| doc | 5 | 1,488 | 1,741 |
| data | 10 | 472 | 507 |
| infra | 8 | 450 | 524 |
| **合计** | **296** | **77,230** | **84,434** |

按去向包：

| destination | 文件数 | 非空行 |
|---|---:|---:|
| platform-core | 72 | 17,715 |
| platform-ext | 55 | 23,949 |
| platform-internal | 1 | 5,891 |
| platform-gateway | 0 | 0 |
| none | 168 | 29,675 |
| **合计** | **296** | **77,230** |

按子判定 `sub`：

| sub | 文件数 | 非空行 | 含义 |
|---|---:|---:|---|
| L | 23 | 5,515 | 可直接挂接 |
| AD | 13 | 16,488 | 需适配层 |
| EXT | 92 | 25,552 | 扩展能力 |
| RET | 0 | 0 | 退役（本台账没有无条件退役文件） |
| TOOL | 87 | 23,644 | 工具/测试/脚手架 |
| `-` | 81 | 6,031 | 配置、文档、数据、夹具等非接入项 |
| **合计** | **296** | **77,230** |

按是否阻塞 P1 切片：

| p0_blocking | 文件数 | 非空行 |
|---|---:|---:|
| yes | 69 | 17,438 |
| no | 227 | 59,792 |
| **合计** | **296** | **77,230** |

`p0_blocking` 的口径：P0 本身只产出文档与清单，没有代码阻塞项；该列判定的是「是否阻塞紧随 P0 的 P1 全本地首个切片」。`RET=0` 不是遗漏：81 已把 B 类从「一律废弃」改为逐模块重判，没有整文件无条件退役；`api.py` 也只是退为内部服务，不是退役。

说明：`platform-gateway` 本阶段没有存量文件，它由 P1 新增，因此为 0 是预期结果，不是漏登记。`none` 含测试、夹具、前端之外的非包资产、smoke、工具、运维、配置、文档、数据、sidecar。

### 6.3 闭合校验

```
产品代码：6,208 + 15,795 + 17,162 + 4,610 = 43,775
scope：43,775 + 5,964 + 13,418 + 2,791 + 6,255 + 1,787 + 830 + 1,488 + 472 + 450 = 77,230
去向：17,715 + 23,949 + 5,891 + 0 + 29,675 = 77,230
```

三条均精确闭合，无「约」数。

### 6.4 与 79/80 的对账

80 的 A/B/C 没有发布逐文件定义，只有方向性口径。本台账按三条可复核规则重判：① 是否实现 COA 已有接口 → A；② 是否与 COA 同职责但需适配 → B；③ COA 完全没有 → C。因此小计与 80 不同，差异如下：

| 桶 | 80 原文 | 本台账实测 | 差额 | 结论 |
|---|---:|---:|---:|---|
| A 可回灌 | 8,659 | 6,208 | -2,451 | 80 未发布逐文件；其 A 口径更宽，含本台账判为 B/C 的模块 |
| B 重叠 | 16,404 | 15,795 | -609 | 方向一致；逐文件归属不可复现 |
| C 净新增 | 14,102 | 17,162 | +3,060 | 80 把部分净新增计入 A/B |
| S 脚手架 | 4,810 | 4,610 | -200 | 80 数字本身破坏闭合，见 §6.5 |
| **合计** | **43,975** | **43,775** | **-200** | 80 四项相加多 200 |

结论：80 的四个数字相加不等于实测总量；本台账是唯一逐文件、可机器复核的口径。上表差额不修改 79/80 原文，只在新文档中标记。

### 6.5 `4,810` 与 `4,610` 的 200 行差额

调查过程：

1. 用 `Get-Content`/Python 对 `platform/` 全量文件计算物理行与非空行，发现 79/80/81 的 43,775 对应**非空行**，物理行为 47,766。
2. 15 个 `smoke*.py` 实测非空行合计 **4,610**（物理 5,116），逐文件：`smoke.py 134`、`smoke_embed.py 274`、`smoke_s1.py 244`、`smoke_s10.py 397`、`smoke_s11.py 353`、`smoke_s12.py 258`、`smoke_s13.py 343`、`smoke_s2.py 312`、`smoke_s3.py 345`、`smoke_s4.py 345`、`smoke_s5.py 355`、`smoke_s6.py 267`、`smoke_s7.py 323`、`smoke_s8.py 342`、`smoke_s9.py 318`（非空口径；合计 4,610）。
3. 对 `platform/` 下 227 个候选文件（非空行 1–400、排除 smoke）做 1–3 元子集和搜索，命中 3,667 组非空行之和恰为 200 的组合；没有任何一组对应文档里的「验收脚手架」定义，无法唯一归因。
4. 80 原文四项：`8,659 + 16,404 + 14,102 + 4,810 = 43,975`；实测总量 43,775；二者恰好差 200。
5. 若把 4,810 换成实测 4,610：`8,659 + 16,404 + 14,102 + 4,610 = 43,775`，与实测完全闭合。

结论：

- **200 行差额全部且仅在「验收脚手架」一个数字内**，不是 A/B/C 分散误差。
- 80 的 `4,810` 比实测 `4,610` 多 200；该数字使四项之和变成 43,975。
- `4,810` 没有逐文件组成账本，无法唯一复现；判定为 80 号笔误/未公开口径，**不作为台账依据**。
- 台账与后续文档一律以实测 `4,610` 为准。

### 6.6 台账使用方法

```powershell
# 校验总量与三个维度的小计
python -c "import csv,collections;rows=list(csv.DictReader(open(r'doc/_design/82-platform-ledger.csv',encoding='utf-8-sig')));print(len(rows),sum(int(r['loc_nonblank']) for r in rows));print(collections.Counter(r['class'] for r in rows));print(collections.Counter(r['destination'] for r in rows))"
```

---

## 7. P0 完成定义与遗留

**完成定义**

- 82 文档冻结 27 个接口的全部字段：签名/IO、错误语义、判定、优先级、AWS 落点、本地落点、默认实现、配置 key 与默认值、混搭与约束。
- 台账覆盖 `platform/` 全部 296 个文本/代码文件，且总量、scope、class、destination 四个维度闭合。
- `4,810` vs `4,610` 的 200 行差额有结论，未使用「约」。

**遗留（不阻塞 P0，进入 P1 前置）**

1. `platform-gateway` 尚无存量文件，需在 P1 新建；台账 `destination=platform-gateway` 为 0。
2. `adapters/graph_oxigraph.py`、`graph_fuseki.py`、`metadata_pg.py`、`llm_openai.py` 需要 async/17 方法薄壳，按 AD 计；薄壳代码不在 P0 产出内。
3. `E7 LexicalGraphStore`、`E9 MetadataStoreClient`、`E10 EngineAdapter`、`E12 OntologySource`、`E13 Tool`、`E14 SparqlEndpointClient`、`E15 MetadataConnector` 的本地实现位置已冻结，但实现分别在 P2/P3。
4. `OpenSearchVectorStore` 的 `[0,1]` 与 `[-1,1]` 语义差（S15）属实现缺陷，仍需在 P2 前修复或显式声明能力缺失。

---

## 附录 A 接口 → AWS/本地落点速查

| # | 接口 | AWS 实现 | 本地实现 | key |
|---|---|---|---|---|
| E1 | GraphClient | `clients/neptune.py:118` `NeptuneGraphClient` | `adapters/graph_oxigraph.py` / `graph_fuseki.py` | `COA_PROVIDER_GRAPH` |
| E2 | VectorClient | `clients/opensearch.py:121` `OpenSearchVectorClient` | `adapters/vector_pg.py` + `search_pg.py` | `COA_PROVIDER_VECTOR` |
| E3 | LLMClient | `clients/bedrock.py:309` `BedrockLLMClient` | `adapters/llm_openai.py` + `embedding.py` | `COA_PROVIDER_LLM` / `_EMBEDDING` |
| E4 | QueryExecutor | `athena.py:151` / `redshift_data.py:79` / `source_db.py:121` / `composite_executor.py:43` | 新增 `providers/query_pg.py` | `COA_PROVIDER_QUERY_EXECUTOR` |
| E5 | GraphStore | `stores/neptune_db_graph.py:503` / `na_graph.py:19` | `adapters/ontology_pg.py` + `graph_*` | `COA_PROVIDER_GRAPH_STORE` |
| E6 | VectorStore | `stores/opensearch_vector.py:56` / `na_vector.py:22` | `adapters/vector_pg.py` | `COA_PROVIDER_VECTOR_STORE` |
| E7 | LexicalGraphStore | `na_lexical.py` / `ndb_lexical.py` | 新增 `providers/lexical_pg.py` | `COA_PROVIDER_LEXICAL_STORE` |
| E8 | DataSourceLookup | `lookups.py:249` `SmusCatalogDataSourceLookup` | `adapters/metadata_pg.py` | `COA_PROVIDER_METADATA` |
| E9 | MetadataStoreClient | `metadata_store/smus.py:65` `SMUSClient` | `adapters/metadata_pg.py` | `COA_PROVIDER_METADATA_STORE` |
| E10 | EngineAdapter | `db_adapters/*` | 按源引擎 | `COA_PROVIDER_ENGINE_ADAPTER` |
| E11 | StructuredQueryStrategy | `tier2/*/strategy.py` | 新增 `providers/strategy_local.py` | `COA_PROVIDER_STRATEGY` |
| E12 | OntologySource | `tier3/agentic/ontology` | `adapters/ontology_pg.py` | `COA_PROVIDER_ONTOLOGY_SOURCE` |
| E13 | Tool | `tier3/agentic/tools/` | `platform-ext/tools/` | `COA_PROVIDER_TOOLSET` |
| E14 | SparqlEndpointClient | `sparql_clients.py:103` | `graph_oxigraph.py` / `graph_fuseki.py` | `COA_PROVIDER_SPARQL_ENDPOINT` |
| E15 | MetadataConnector | `connectors/custom_connector.py:162` / `glue_catalog.py:43` | 新增 `providers/connector_pg.py` | `COA_PROVIDER_METADATA_CONNECTOR` |
| N1 | NamespaceRegistry | `control-plane` Dynamo DAO | `adapters/metadata_pg.py` | `COA_PROVIDER_NAMESPACE_REGISTRY` |
| N2 | OntologyRegistry | `dynamo_store` registry | `adapters/ontology_pg.py:OntologyRegistry` | `COA_PROVIDER_ONTOLOGY_REGISTRY` |
| N3 | MetricRepository | `metric-service` Dynamo | `metrics.py` + `metric_loader.py` | `COA_PROVIDER_METRIC_REPOSITORY` |
| N4 | SourceCatalog | `SmusCatalogDataSourceLookup` | `adapters/metadata_pg.py` | `COA_PROVIDER_SOURCE_CATALOG` |
| N5 | ConversationStore | `session_metadata.py:53` | 新增 `providers/session_pg.py` | `COA_PROVIDER_SESSION` |
| N6 | MemoryStore | `session.py:SessionManager` | 新增 `providers/memory_pg.py` | `COA_PROVIDER_MEMORY` |
| N7 | JobQueue | SQS / Step Functions | `inline` / 新增 `providers/job_inline.py` | `COA_PROVIDER_DISPATCH` |
| N8 | ObjectStore | S3 | `adapters/object_fs.py` / `object_layered.py` / `object_pg.py` | `COA_PROVIDER_STORAGE` |
| N9 | SecretProvider | Secrets Manager | `ports.py:EnvSecretProvider` | `COA_PROVIDER_SECRET` |
| N10 | CredentialProvider | Secrets Manager + SMUS | 新增 `providers/credential_pg.py` | `COA_PROVIDER_CREDENTIAL` |
| N11 | ObservabilitySink | CloudWatch EMF | `logging_setup.py` | `COA_PROVIDER_OBSERVABILITY` |
| N12 | IndexProjector | 最终一致轮询 | `embedding.py` + `reindex.py` | `COA_PROVIDER_INDEX_PROJECTOR` |
