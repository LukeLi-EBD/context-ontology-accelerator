# COA 契约与 platform_core 整合方案（2026-11-08）

> 状态：设计稿，只读核实，未改代码、未启动长期服务、未触碰 8080。
> 前置：`78-COA单机可运行性评估`、`79-COA二开路线评估`、`80-platform整合进COA可行性`。
> 本版修正：① 契约加本地实现，可配置切换 AWS / 本地 / 第三方；② B 类不再一律废弃，重判为可挂接的 local 实现候选；③ COA 上游可改，但只允许「写死改可注入/可配置」；④ 允许逐接口混搭，配置按接口一项一 key。

---

## 0. 结论摘要

| 问题 | 结论 |
|---|---|
| COA 契约分几层 | 5 层：Smithy 线协议、Python Protocol、HTTP 内部面、数据/指标语义、术语/本体语义。对外权威是 Smithy；进程内权威是 Protocol |
| `platform_core` 怎么落位 | 4 个包：`platform-core`（provider/装配）、`platform-ext`（净新增能力）、`platform-internal`（原 `api.py` 内部服务）、`platform-gateway`（COA 契约门面） |
| B 类 16,404 行 | 不再一律废弃。按 L/AD/EXT/RET/TOOL 五档逐模块重判；真正无条件退役的只有「重复的对外路由绑定」，不是业务逻辑 |
| `api.py` 5,891 行 | 推荐退成**内部服务**，由 COA 契约层统一对外；不把它改写为契约适配层，也不直接废弃 |
| 实现切换 | 每个接口一个 `COA_PROVIDER_<INTERFACE>`，支持逐接口混搭；只承诺 4 档已验证组合，其余「可配不承诺」 |
| 第一期 | 全本地最小组合，单机跑通、不依赖 AWS；用 `neptune_replay` 录放实现证明「换 AWS 时门面调用链不变」 |
| 第二期 | 只把 graph 换成 Neptune，其余保持本地，验证混搭真实可用 |
| COA 上游改动 | G1–G8，合计约 250–410 行；只动装配缝与硬编码，不动业务逻辑 |
| 工作量 | 60–88 人日（±30%），比「零改动」约束的 1.5–5× 明显下降 |

---

# 第一部分 接口清单（第一交付物）

接口清单先冻结，再写实现。判定口径：

- **够用**：现有签名可直接承载本地实现，不需要改 Protocol。
- **要扩展**：现有抽象方向正确，但缺必要方法或返回结构，需要新增方法（不得改已有方法语义）。
- **要新增**：COA 没有对应抽象，必须新建契约。
- **必须有**：P1/P2 阻塞项，缺了就跑不通。
- **以后再说**：不阻塞 P1，但接口位置先预留。

## 1.0 契约定五层与边界

| 层 | 权威物 | 必须严格对齐 | 允许本地扩展 |
|---|---|---|---|
| L1 Smithy 线协议 | `models/src/main/smithy/*.smithy`（88 个 operation、2 个 service） | operation 名、HTTP method/URI、必填字段、枚举值、错误形状、分页、`Uuid` 格式、状态码 | 只能新增独立 operation/独立 service；不得改上游 shape 的必填性与枚举；新增可选字段视为契约变更，需单独批准 |
| L2 Python Protocol | `clients/base.py`、`stores/base.py`、`lookups.py` 等 15 个主抽象 + 12 个新接口 | 方法名、参数、async/sync、返回结构、异常类型、health 永不抛 | 只允许新增可选方法（如 `capabilities()`）；不得改已有方法语义 |
| L3 HTTP/REST 面 | Smithy 绑定路径是唯一对外契约；`ontology-engine` 的 `/ontologies`、`/graph`、`/induce`、`/validate` 只是内部开发面 | 对外路径、状态码、错误体、上传/下载语义 | 平台独有能力统一挂 `/ext`；内部服务端口不对外 |
| L4 数据与指标语义 | `MetricDefinition`、`QueryResult`、`ConfidenceScore`、`SupportingContent`、namespace/ontology 记录 | 必填字段、指标 name 模式、tier 语义、confidence/trace 必填、dataSourceId/sourceTable | `publishable/executable`、观测、事实绑定、readiness 作为扩展资源；不得塞进契约 shape 冒充必填 |
| L5 术语与本体语义 | RDF/RDFS/OWL/SHACL/SKOS 的实际用法与发布可见性 | 已发布 T-Box 是唯一可见语义；SKOS 标签/定义进入本体；版本不得冒充本体 | 术语治理工作流、门禁、批注流程是流程扩展，结论必须物化为 SKOS |

**边界判据**：L1/L4 的任何变更都会影响外部客户端，必须走契约版本；L2 影响进程内调用方，可在不破坏已有方法的前提下增量扩展；L3 的内部路由可自由实现，但不得冒充对外契约；L5 的流程可本地化，但语义必须落在 RDF 模型里，不能只存在平台数据库。

## 1.1 COA 已有抽象逐项

### 1.1.1 核心运行时抽象

| # | 抽象 | 定义位置 | 方法签名与输入输出 | 错误语义 | 判定 | 档 |
|---|---|---|---|---|---|---|
| E1 | `GraphClient` | `packages/context-manager/src/coa_serve/clients/base.py:69-86` | `async query(sparql) -> list[dict]`；`async ask(sparql) -> bool`；`async health_check() -> dict` | 查询失败抛后端异常/超时；`health_check` 永不抛，返回状态字典 | 够用 | 必须有 |
| E2 | `VectorClient` | 同上 `:122-157` | `async search(query_vector, *, namespace, top_k, index, entity_type, require_mapped, ontology_ids, query_backend) -> list[VectorHit]`；`async hybrid_search(query_text, query_vector, *, namespace, top_k, index) -> list[VectorHit]`；`async health_check() -> dict` | search 失败抛出；hit 的 `score` 为 0–1 余弦相似度；health 永不抛 | 够用 | 必须有 |
| E3 | `LLMClient` | 同上 `:253-312` | `async converse(prompt, *, system, guardrail_id, max_tokens, temperature, top_p, guard_content, model_id) -> ConverseResult`；`converse_stream(...) -> AsyncIterator[str]`；`async embed(text) -> list[float]`；`async health_check() -> dict` | 护栏拦截抛 `GuardrailBlockedError`；模型自过滤抛 `ContentFilteredError`；截断通过 `ConverseResult.truncated` 显式可见；health 永不抛 | 够用（需补能力上报，见 1.2） | 必须有 |
| E4 | `QueryExecutor` | 同上 `:336-361` | `async execute(sql, *, namespace, data_source_id, params, max_rows, timeout_seconds) -> QueryResult(rows, columns, row_count, truncated, duration_ms, engine)`；`async health_check() -> dict` | SQL/权限/超时抛出；结果截断必须置 `truncated=True`；health 永不抛 | 够用 | 必须有 |
| E5 | `GraphStore` | `packages/ontology-engine/src/coa_ontology/stores/base.py:192-488` | 17 个同步方法：ontology CRUD 5、schema 元素 3、批量 Turtle 2、统计/顶点/搜索 5、namespace schema/健康 2（完整见附录 A） | 缺省返回 `None`/`False` 表示不存在；后端不可枚举时返回 `None` 或 `skipped`，不伪造空结果；`health_check` 永不抛 | 够用；**列表权威不在 GraphStore**，需新增 `OntologyRegistry` | 必须有 |
| E6 | `VectorStore` | 同上 `:45-185` | `dimensions: int`；10 个同步方法：写入 2、读取 3、搜索 1、删除 3、健康 1（完整见附录 A） | `search_nearest` 的 `score` 必须统一为 `[-1,1]` 余弦；删除不能全删时抛异常；`delete_index` 返回是否存在；健康永不抛 | 够用 | 必须有 |
| E7 | `LexicalGraphStore` | `packages/ontology-engine/src/coa_ontology/inducer/unstructured/stores/protocol.py:132-215` | `get_class_nodes() -> list[ClassRecord]`；`get_class_relations() -> list[RelationRecord]`；`get_entities_by_class(classification, limit) -> list[EntityRecord]`；`get_facts_for_entities(entity_ids) -> list[FactRecord]`（>500 必须分批）；`get_topics() -> list[TopicRecord]`；`get_graph_schema() -> ClassSchemaResult` | 无匹配返回空列表；批量超限必须分批而非截断；后端失败抛出 | 够用 | 以后（induction 用） |
| E8 | `DataSourceLookup` | `packages/metric-service/src/coa_metrics/lookups.py:51-124` | `data_source_exists(id) -> bool`；`table_exists(id, table) -> bool`；`get_table_columns(...) -> list[ColumnMetadata] \| None`；`catalog_available(id) -> bool`；`known_tables(id) -> set[str]`；`table_rejection_reason(...) -> str \| None`；`get_column_type(...)` | 缺省 fail-open：无法枚举时 `known_tables` 为空，使「表不存在」不可证明，不得硬拒；`None` 表示元数据不可读，不是「不存在」 | **要扩展**：缺 list/get source、审批状态、表分页 | 必须有（扩后） |
| E9 | `MetadataStoreClient` | `libs/common/src/coa_common/metadata_store/base.py:39-163` | 10 个同步方法：项目 3、资产 6、成员 1（`create_project`/`delete_project`/`get_project`/`create_asset`/`create_asset_revision`/`delete_asset`/`get_asset`/`search_assets`/`get_asset_forms`/`create_project_membership`） | 统一抛 `MetadataStoreError`（继承 `SCLError`）；未找到也抛 | 够用（SMUS 语义）；本地实现需把 project/asset 映射到 schema/table | 以后（P3 数据源） |
| E10 | `EngineAdapter` | `packages/context-manager/src/coa_serve/clients/db_adapters/base.py:94-139` | ABC；`async open_connection(DBCredentials) -> ConnHandle`；`async run(conn, sql, params, timeout_seconds, schema) -> (rows, columns)`；`async close(conn)`；钩子 `inject_limit(sql, max_rows)` | 连接/执行失败抛驱动异常；`inject_limit` 在解析失败时回退到引擎自己的行数限制写法（SQL Server 用 `TOP`） | 够用 | 以后（外部库） |
| E11 | `StructuredQueryStrategy` | `packages/context-manager/src/coa_serve/tier2/strategy.py:136-146` | `name: str`；`supported_backends: frozenset[StructuredBackend]`；`async resolve(query, namespace, context) -> StrategyResult \| None` | 返回 `None` 表示未命中而非失败；异常由 runner 记录并降级 | 够用 | 必须有（Tier2 本地策略） |
| E12 | `OntologySource` | `packages/context-manager/src/coa_serve/tier3/agentic/ontology/source.py:132-143` | `async load(namespace) -> Ontology` | 后端失败必须抛出，由 Tool 记录来源与失败 | 够用 | 以后（Agentic Tier3） |
| E13 | `Tool` | `packages/context-manager/src/coa_serve/tier3/agentic/tools/base.py:90-113` | `name/description/input_schema/output_schema` 4 个必填字段；`async invoke(*, namespace, **kwargs) -> ToolResult` | 注册时校验字段非空与 schema 为 dict；运行失败抛 | 够用 | 以后 |
| E14 | `SparqlEndpointClient` | `packages/context-manager/src/coa_serve/clients/sparql_clients.py:48-65` | `async query(sparql, *, max_results) -> list[dict]`；`async ask(sparql) -> bool`；`async construct(sparql, *, max_triples) -> list[{'s','p','o'}]`；`async close()` | 引擎不支持抛 `UnsupportedSparqlEngineError`；查询失败抛 | 够用 | 以后（多源 A-Box） |
| E15 | `MetadataConnector` | `packages/sources/src/coa_sources/database/connectors/base.py:33-42` | `test_connection(config) -> ConnectionTestResult`；`discover_metadata(config) -> DiscoveredMetadata` | 连接失败返回失败结果还是抛出，按现有连接器实现；发现失败抛 | 够用 | 以后（数据源接入） |

**次要抽象（不阻塞 P1，接口位置预留）**：`CedarAuthorizer`、`Tier2SkipEvaluator`、`StepPlanner`、`EmbedClient`、`EmbedFn`、`GraphExpander`、`IRIResolver`、`LLMDescriptionClient`、`ClassEmbeddingClient`、`SourceLookup`、`NamespaceAuthorizer`。其中 `InductionStrategy` 是 Smithy 枚举，不是 Protocol；`EngineAdapter`、`MetadataStoreClient` 是 ABC，不是 Protocol；清单里按「抽象类型」标注，不混称。

### 1.1.2 已有抽象的边界结论

- **够用但不要改语义**：E1–E7、E10–E15。允许新增*可选*方法（如 `capabilities()`），不允许改已有方法签名、返回结构或异常类型。
- **必须扩展**：E8 `DataSourceLookup` 扩成 `SourceCatalog`（见 1.2.4）。
- **必须新增而不应塞进旧接口**：`OntologyRegistry`、`NamespaceRegistry`、`MetricRepository`。`GraphStore` 注释已明确「命名空间内的本体权威列表在 Dynamo registry」，所以列表能力不能在 `GraphStore` 上硬加。
- **不能用于切换的假抽象**：`MetadataStoreClient` 的 project/asset 是 SMUS 概念，不能拿它冒充 COA 的 namespace/ontology；本地实现要另立映射，不共享 ID 空间。

## 1.2 COA 没有、但必须有的抽象

| # | 新接口 | 建议签名（最小集） | 错误语义 | 档 |
|---|---|---|---|---|
| N1 | `NamespaceRegistry` | `create(name, description) -> NamespaceRecord`；`get(id) -> NamespaceRecord \| None`；`list(limit, offset) -> list[...]`；`update_status(id, status) -> NamespaceRecord`；`delete(id) -> bool` | `NamespaceExists` / `NamespaceNotFound` / `NamespaceNotEmpty`；ID 由注册表生成，不由调用方编造 | 必须有 |
| N2 | `OntologyRegistry` | `create(namespace, ontology_uri, title) -> OntologyRecord`；`get/list(namespace) -> ...`；`update_status(id, status)`；`delete(id)`；`resolve_graph_uri(namespace, ontology_id) -> str` | `OntologyNotFound`；`OntologyAlreadyPublished`；注册表是列表权威，图存储不得自行发现 | 必须有 |
| N3 | `MetricRepository` | `create/get/list/update/delete/validate/bulk_delete`；`import_osi/export_osi`；`get_import_job(job_id)` | `MetricNameConflict`；`MetricNotFound`；`MetricNotExecutable`；不可执行不得返回结果 | 必须有 |
| N4 | `SourceCatalog`（扩展 E8） | `list_sources(namespace)`；`get_source(id)`；`list_tables(id, limit, offset)`；`get_table(id, table)`；`approve/reject(id)`；`discover(id) -> JobHandle` | `SourceNotFound`；`TableUnprovable`（不可证明不存在时不得硬拒）；审批状态必须显式 | 必须有（P2） |
| N5 | `ConversationStore` | `create(user_id, namespace, title) -> SessionRecord`；`validate_ownership(user_id, session_id) -> bool`；`update_activity(...)`；`list_sessions(...)`；`get_history(session_id, limit, before)`；`delete(session_id)` | `SessionNotFound`；`SessionForbidden`；TTL 到期视为不存在 | 以后（P3） |
| N6 | `MemoryStore` | `append_turn(session_id, turn) -> TurnRecord`；`get_window(session_id, turns) -> list[TurnRecord]`；`search(namespace, query, top_k)`；`delete_session(session_id)`；`gc(expires_before)` | `MemoryExpired`；写入失败不得阻断回答，必须降级并留痕 | 以后（P3） |
| N7 | `JobQueue` | `submit(kind, payload, *, namespace, idempotency_key) -> JobHandle`；`status(job_id) -> JobStatus`；`cancel(job_id) -> bool` | 至少一次投递；幂等键冲突返回既有 Job；状态机 `queued/running/succeeded/failed/cancelled` | 以后（P3，induction/scan） |
| N8 | `ObjectStore` | `put/get/head/delete/list`；`presign_put(key, ttl, content_type) -> UploadTicket`；`presign_get(key, ttl) -> str`；`capabilities()` | `ObjectNotFound`；`PreconditionFailed`；`ObjectTooLarge`；无预签名能力时 `upload_mode="proxy"`，不得假装支持 | 必须有 |
| N9 | `SecretProvider` | `get(name) -> str` | `SecretNotFound`；永不记录值；缺失时 fail-closed，不回落到默认口令 | 必须有 |
| N10 | `CredentialProvider` | `resolve_db(namespace, data_source_id) -> DBCredentials` | `CredentialUnavailable`；不得返回匿名连接 | 以后（外部库 P3） |
| N11 | `ObservabilitySink` | `span(name, attributes)` 上下文；`metric(name, value, unit, tags)`；`event(kind, payload)` | 永不向业务路径抛；丢弃时计数自增 | 必须有（最小） |
| N12 | `IndexProjector` | `project(ontology_id, entities) -> ProjectionResult`；`verify(ontology_id, expected) -> VerifyResult`；`reindex(namespace) -> JobHandle` | 不得宣称跨图/向量原子性；`verify` 必须返回差异集合；失败可重试且幂等 | 必须有（P2 混搭） |

**判断依据**：N1/N2/N3/N8/N9/N11 是 P1 跑通 COA 契约的最小闭环；N12 是 graph/vector 混搭的一致性载体，P2 必须；N5/N6/N7/N10 不阻塞 P1，但必须在接口层预留，不能等实现时再临时造。

## 1.3 双实现落位

| 接口 | AWS 实现（COA 原有/薄封装） | 本地实现（`platform_core` 对应模块） |
|---|---|---|
| GraphClient | `clients/neptune.py`；`SparqlEndpointClient` 的 Neptune 分支 | `adapters/graph_oxigraph.py` / `graph_fuseki.py`（同步 port 包 async） |
| VectorClient | `clients/opensearch.py`；NA 向量 | `adapters/vector_pg.py` + `search_pg.py` |
| LLMClient | `clients/bedrock.py` | `adapters/llm_openai.py` |
| QueryExecutor | `source_db.py` + Athena | `adapters/metadata_pg.py` + PG 执行器（新增薄壳） |
| GraphStore | `stores/neptune_db_graph.py`；`na_*` | `adapters/graph_oxigraph.py` / `ontology_pg.py` |
| VectorStore | `stores/opensearch.py`；`na_*` | `adapters/vector_pg.py` |
| LexicalGraphStore | `ndb_lexical.py`；`na_lexical.py` | 复用 `lexical_graph` 投影或新增 PG 实现 |
| DataSourceLookup → SourceCatalog | `SmusCatalogDataSourceLookup` | `adapters/metadata_pg.py` + metric bindings |
| MetadataStoreClient | `SMUSClient` | `metadata_pg` 映射 project/asset → schema/table |
| EngineAdapter | 现有 Postgres/Redshift/MySQL/SQLServer | 不需要本地替代；按数据源引擎选择 |
| StructuredQueryStrategy | `tier2/nl_to_sql`、`tier2/sparql` | `facts.py` / `context.py` 包装为策略 |
| OntologySource | NDB/NA 源、file 源 | `ontology_pg` 发布版本读取 |
| Tool | 现有 Agentic tools | `platform-ext` 的检索/事实工具 |
| SparqlEndpointClient | Neptune/Athena 分支 | Oxigraph/Fuseki 分支 |
| MetadataConnector | Glue/SMUS 连接器 | PG/文件连接器 |
| NamespaceRegistry（新） | `control-plane` Dynamo DAO | `adapters/metadata_pg.py` + `namespace` 表 |
| OntologyRegistry（新） | `dynamo_store` registry | `ontology_pg` 注册表部分 |
| MetricRepository（新） | `metric-service` Dynamo 表 | `metrics.py` + `metric_loader.py` + PG 表 |
| ConversationStore（新） | `SessionMetadataStore`（Dynamo） | PG `session_metadata` 表（新增） |
| MemoryStore（新） | `SessionManager`（AgentCore Memory） | PG `session_turn` 表（新增） |
| JobQueue（新） | SQS / Step Functions / Lambda 异步 | `inline` 同步执行器；P3 可加 PG 队列 |
| ObjectStore（新） | S3 + 预签名 | `adapters/object_fs.py` / `object_layered.py` |
| SecretProvider（新） | Secrets Manager / IAM | `EnvSecretProvider`（已有） |
| CredentialProvider（新） | Secrets Manager + SMUS | PG 凭证表 + 环境变量（仅本地） |
| ObservabilitySink（新） | CloudWatch EMF / X-Ray | `logging_setup.py` + 本地事件表 |
| IndexProjector（新） | 最终一致轮询（AOSS/NA 语义） | 同步投影 + `reindex.py` |

## 1.4 配置绑定方式

**采用 provider registry，不用一个全局 impl。** 每个接口一个 key，值选实现；registry 只负责 `(interface, name) → factory`，不做隐式回退。

```yaml
# config/local.yaml
coa:
  providers:
    graph: oxigraph            # oxigraph | fuseki | neptune | neptune_analytics
    vector: pgvector           # pgvector | aoss | neptune_analytics
    llm: openai                # openai | bedrock
    embedding: tei             # tei | bedrock
    query_executor: postgres   # postgres | athena | source_db
    metadata: postgres         # postgres | smus
    namespace_registry: postgres   # postgres | dynamo
    ontology_registry: postgres    # postgres | dynamo
    metric_repository: postgres    # postgres | dynamo
    storage: fs                # fs | s3
    session: postgres          # postgres | dynamo | none
    memory: postgres           # postgres | agentcore | none
    dispatch: inline           # inline | sqs | stepfunctions
    secret: env                # env | aws_secrets_manager
    observability: local       # local | cloudwatch
```

等价环境变量（部署侧用这套，避免 YAML 与 env 两套真相）：

```bash
COA_PROVIDER_GRAPH=oxigraph
COA_PROVIDER_VECTOR=pgvector
COA_PROVIDER_LLM=openai
COA_PROVIDER_EMBEDDING=tei
COA_PROVIDER_QUERY_EXECUTOR=postgres
COA_PROVIDER_METADATA=postgres
COA_PROVIDER_NAMESPACE_REGISTRY=postgres
COA_PROVIDER_ONTOLOGY_REGISTRY=postgres
COA_PROVIDER_METRIC_REPOSITORY=postgres
COA_PROVIDER_STORAGE=fs
COA_PROVIDER_SESSION=postgres
COA_PROVIDER_MEMORY=postgres
COA_PROVIDER_DISPATCH=inline
COA_PROVIDER_SECRET=env
COA_PROVIDER_OBSERVABILITY=local

# 仅作为未显式设置时的默认种子；显式 key 优先级更高
COA_PROFILE=local
# 未验证组合的策略：false = 启动失败（默认），true = 仅告警
COA_ALLOW_UNVERIFIED_COMBOS=false
```

解析规则：

1. 显式 `COA_PROVIDER_<INTERFACE>` > `COA_PROFILE` 种子；不存在第二层以外的回退。
2. 未设置的接口没有默认值就**启动失败**，不静默选 AWS 或本地。
3. 未知实现名启动失败，不近似映射到最近实现。
4. `COA_PROFILE` 仅给出一组种子默认，不允许覆盖显式 key。

注入点（全部在装配期完成，不在业务逻辑里判断 provider 名）：

- `context-manager`：`clients/factory._build_default_clients()` 与 `main.py:237-239` 的直构客户端都改为 `registry.build(settings)`。
- `ontology-engine`：`stores/factory.build_stores()` 改为 `registry.resolve("graph"/"vector")`。
- `metric-service`：`data_source_lookup_factory.build_data_source_lookup()` 改为 `registry.resolve("metadata")`。
- `control-plane`：`namespace/create_handler._get_service()` 等 handler 的 DAO 构造改为 registry（P3；P1 由 gateway 提供本地控制面，不改 control-plane）。
- `platform-gateway`：启动时构建 `ProviderRegistry`，业务对象只收到具体端口实例。

**热切换**：v1 一律**重启生效**。provider 构造持有连接池、索引维度、模型 ID，热切换会破坏一致性。`/providerz` 只报告 `reload: "restart"`，不提供热切换端点。以后只有 `observability`、`llm` 可评估热切换，且必须是显式白名单。

## 1.5 每个接口的混搭策略（三项必标）

| 接口 | 允许混搭 | 已知约束 | 默认实现（本地 / AWS） |
|---|---|---|---|
| GraphClient | 是 | 只承诺 SPARQL 1.1 共同子集；不使用 Neptune 扩展语法；变量图查询走守卫 | oxigraph / neptune |
| VectorClient | 是 | 向量模型与维度必须与写入侧一致；`search_nearest` 余弦区间强制；AOSS 最终一致 | pgvector / aoss |
| LLMClient | 是 | 本地无护栏；`GuardrailOutcome` 必须显式返回 `NONE` 并记录「无护栏」，不得冒充已护栏；截断必须可见 | openai / bedrock |
| QueryExecutor | 是 | 必须与 `SourceCatalog` 同族，否则硬校验降级为结构校验并显式标 `source_enforcement=false` | postgres / athena |
| GraphStore | 是 | ontology_id 必须来自 `OntologyRegistry`；图侧不得自行发现本体；切换图实现后必须 `IndexProjector.reindex` | oxigraph / neptune |
| VectorStore | 是 | 维度启动即固定；切换必须重建索引；删除必须抛部分失败 | pgvector / aoss |
| LexicalGraphStore | 是（受限） | 必须读同一张图；graph=AWS 时 lexical 只能走 Neptune 同源，不能本地另起一份 | pg 投影 / nautilus |
| DataSourceLookup/SourceCatalog | 是 | 与 QueryExecutor 混族时只能 fail-open，不得硬拒表不存在 | postgres / smus |
| MetadataStoreClient | 是 | project/asset ID 空间与 namespace 分离；不得把 asset_id 当 namespace_id | pg 映射 / smus |
| EngineAdapter | 不适用（按源引擎选） | 无跨引擎混搭；同一 source 固定一个 adapter | 由数据源配置决定 |
| StructuredQueryStrategy | 是 | 每个策略声明 `supported_backends`；并行超时与空结果置信下限一致 | facts/context / nl_to_sql |
| OntologySource | 是 | 只读已发布图；未发布草稿不可见 | ontology_pg 发布版 / ndb |
| Tool | 是 | 每个工具单独选 provider；schema 必须自洽 | platform-ext / agentic tools |
| SparqlEndpointClient | 是 | 按 source 配置选引擎，不支持引擎显式报错 | oxigraph / neptune |
| MetadataConnector | 是 | 连接器与数据源类型绑定，不跨源复用凭证 | pg/file / glue |
| NamespaceRegistry | 是 | 必须与 graph/vector 的作用域 key 一致；ID 由注册表生成 | postgres / dynamo |
| OntologyRegistry | 是 | 列表权威；与 GraphStore 混用时按 ontology_id 对齐，不做双向发现 | postgres / dynamo |
| MetricRepository | 是 | 与 SourceCatalog 同族优先；异构时指标只能「结构可算」，不得标「可执行」 | postgres / dynamo |
| ConversationStore | 是 | TTL 由 session 侧声明；storage 侧不重复设 TTL；删除只能尽力级联 | postgres / dynamo |
| MemoryStore | 是 | 与 ConversationStore 生命周期对齐；跨 store 无事务，失败降级并留痕 | postgres / agentcore |
| JobQueue | 是 | 至少一次语义；必须带幂等键；inline 实现返回已完成句柄，不假装异步 | inline / sqs |
| ObjectStore | 是 | 预签名能力必须在 `capabilities()` 声明；不支持时走代理上传 | fs / s3 |
| SecretProvider | 是 | 缺失 fail-closed；不得日志输出值 | env / secrets manager |
| CredentialProvider | 是 | 本地凭证表仅开发；生产必须外部密钥源 | pg/env / secrets manager |
| ObservabilitySink | 是 | 只降级不阻断；provider 名必须进 span 标签 | local / cloudwatch |
| IndexProjector | 是 | 一致性模式 `sync` / `eventual` 必须显式；不得声称跨库原子 | sync / eventual |

**已有/新增统计**：COA 已有 15 个主抽象，其中 14 个「够用」、1 个「要扩展」（`DataSourceLookup`）；另需从 `GraphStore` 拆出 1 个新接口（`OntologyRegistry`）。新增接口合计 12 个。必须有 16 项，以后再说 11 项。

## 1.6 已验证组合与「可配不承诺」

| 组合 | graph | vector | llm | metadata | storage | session | dispatch | 状态 |
|---|---|---|---|---|---|---|---|---|
| V1 全本地 | oxigraph | pgvector | openai | postgres | fs | postgres | inline | **P1 验收** |
| V2 仅图换 AWS | neptune | pgvector | openai | postgres | fs | postgres | inline | **P2 验收** |
| V3 图+向量 AWS | neptune | aoss | openai | postgres | fs | postgres | inline | P3 验收 |
| V4 全 AWS | neptune | aoss | bedrock | smus | s3 | dynamo | sqs | P4 验收 |

- **只承诺上表四档。** 其余组合「技术上可配、但不承诺可用」；`COA_ALLOW_UNVERIFIED_COMBOS=false` 时直接启动失败，`true` 时只告警并在 `/providerz` 标 `verified:false`。
- 组合爆炸不靠测试穷举解决，靠**能力声明 + 启动校验**：每个 provider 声明 `capabilities`（如 `hybrid_search`、`presign`、`strong_consistency`、`sparql_construct`），启动时按启用的功能校验；缺能力即失败。
- 没有任何静默降级：provider 初始化失败直接退出，不回落到另一实现。

## 1.7 隐式耦合点与接口层规则

| 耦合点 | 症状 | 接口层规则 |
|---|---|---|
| graph ↔ vector | 图删了、向量还在；或图更新、向量是旧描述 | 由 `IndexProjector` 统一投影；写入先落图、再投影；`verify` 返回差异集；禁止跨库事务承诺；切换任一实现必须 `reindex` |
| namespace ↔ graph/vector | 本地建了 namespace，AWS 图不认识 | `NamespaceRegistry` 是作用域权威；所有 store 构造必须带 namespace 并先 `get()` 校验；不存在即失败 |
| ontology registry ↔ graph | ListOntologies 来自 registry，GraphSearch 来自图，两边对不上 | registry 拥有 ID 与状态；graph 只按 ID 存取；禁止从图反推本体列表 |
| metric repository ↔ source catalog ↔ executor | 指标引用的 dataSourceId 在另一族目录里不存在 | 三者同族优先；异构时 `source_enforcement=false`，指标最多「结构可算」，不得标「可执行」 |
| session ↔ memory ↔ storage | session 过期但 memory 还在；附件对象无人回收 | TTL 只由 `ConversationStore` 声明；`MemoryStore` 按其过期；`ObjectStore` 用 `gc` 任务尽力回收；无跨库事务，失败必须留痕 |
| ObjectStore ↔ 上传契约 | 本地对象存储没有预签名，COA 上传 URL 语义断裂 | `capabilities().presign` 必须如实；不支持时 `upload_mode="proxy"`，由 gateway 代理上传，不返回假 URL |
| auth ↔ local | 本地无 Cedar/鉴权实现，`auth_enabled=true` 却放行 | 若鉴权启用而 provider 无策略引擎，**fail-closed** 启动失败；设计阶段不实现鉴权，但不得默认放行 |
| observability ↔ providers | 出问题不知道走的是哪个实现 | 所有 span/metric 必须带 `provider.<interface>=<name>` 标签 |

**接口清单自检**：
- [x] 15 个已有抽象均有定义位置、签名/IO、错误语义、判定。
- [x] 12 个新增接口均给最小签名与错误语义。
- [x] 每个接口都有「AWS 实现落位 / 本地实现落位」。
- [x] 每个接口都有「是否允许混搭 / 已知约束 / 默认实现」三项。
- [x] 配置按接口一 key，给 YAML 与 env 两套示例。
- [x] 只承诺 V1–V4 四档组合，其余明确「可配不承诺」。
- [x] 8 类隐式耦合点均有接口层规则。

## 1.8 已存在的 S1 切片（不重造）

仓库已有未跟踪的 S1 切片，正好是本方案的第一个「接口 → local 实现」样本：

| 现有物 | 内容 | 与本方案的关系 |
|---|---|---|
| `packages/local-providers/` | `coa_local_providers`：`JsonDataSourceLookup`（实现 `DataSourceLookup` 7 个方法）、`OsiMetric → metric_body` 桥、只读快照导出、Windows `resource` shim | 作为 P1 的 `DataSourceLookup` 首个 local provider 直接复用；不重写。P1 落地 `platform-core` 时把 provider 文件迁入 core，或保留该包作为独立 provider 包，二选一，不能两套 registry |
| `.venv-coa-local/` | 独立 venv + `PYTHONPATH`，绕过根 workspace | G4 修复前的临时手段；G4 完成后回归 workspace，不再长期保留双环境 |
| `doc/_evidence-coa-integration/s1-2026-11-08/` | 指标快照与校验证据 | 本方案指定的证据目录基线；P1 继续在此目录下分批次写，不并入 `doc/_qa` |

**边界一致性**：S1 只新增文件、不改上游、不连 AWS、不启动长驻服务，与本方案 P1 的约束一致；区别仅是本方案允许 G1–G8 的装配缝改动。

---

# 第二部分 COA 上游可注入化改动

## 2.1 允许改的边界

**允许**：
- 把写死的 URL、ARN、scheme、签名、backend 选择、table 名、客户端构造改成读配置/注入。
- 抽出现有类的方法为 Protocol/ABC（行为不变）。
- 在 factory/装配函数里按配置选择实现。
- 修死配置（接上或删除）。

**禁止**：
- 重写检索、问答、指标、本体、推理等业务逻辑。
- 借「可注入」改返回语义、错误码、默认行为。
- 大规模格式化/改名，制造无意义冲突。
- 在业务函数里写 `if provider == ...` 分支。

**每处改动的必备说明**：改了什么、为什么必须改、不改的替代方案、预计行数、与上游冲突等级。

## 2.2 G1–G8 逐项

| 编号 | 位置 | 现状（写死点） | 改法 | 行数估计 | 不改的替代 | 冲突等级 |
|---|---|---|---|---|---|---|
| G1 | `packages/context-manager/src/coa_serve/clients/neptune.py:130-165, 267, 281, 309-321` | `https://` 写死；`_sign_request` 永远 SigV4 | 构造参数 `scheme` / `sign_requests`，env `COA_NEPTUNE_SCHEME`、`COA_NEPTUNE_SIGN`；关闭签名时 `_sign_request` 返回 `{}` | 12–18 | 另写 Fuseki 客户端绕开 Neptune；但 `GraphClient` 路径仍 AWS 锁死，不满足「同一调用链切换」 | 低–中 |
| G2 | `ontology-engine/src/coa_ontology/stores/factory.py:33-62`；`context-manager/src/coa_serve/clients/factory.py:100-122`；`context-manager/src/coa_serve/main.py:237-239`；`config.py:94, 318-327` | 向量只有 AOSS/NA；Tier3 默认绑 `graphrag-lexical-graph` | factory 增加 `local` 分支，按 `COA_PROVIDER_*` 解析；Tier3 增加 `lexical_retriever_backend=graphrag\|local`，local 返回 `None` 并走内置向量检索；直构客户端改为 registry | COA 侧 30–45；本地实现另计（platform 侧） | 保留 AOSS 用本地 OpenSearch 容器：仍需 AWS 语义、镜像重，非单机 | 中 |
| G3 | `packages/data-layer/src/coa_data_layer/handler.py:40-51`；`packages/mcp-server/src/coa_mcp/server.py:75`；`packages/mcp-server/src/coa_mcp/config.py:41`；`packages/mcp-proxy/src/config.ts:59-62` | AgentCore Runtime URL/ARN 由固定域名拼出；data-layer 导入期强制读 ARN | 增加完整 URL 覆盖：`AGENTCORE_INVOKE_URL`、`CM_RUNTIME_URL`、`SCL_RUNTIME_URL`；ARN 读取延迟到首次调用，缺 URL 才报错 | 25–40 | 只改 ARN：URL 仍拼 AWS 域名，本地无法指向 gateway | 低 |
| G4 | 根 `pyproject.toml:50-61` | workspace members 含不存在的 `smithy-generated/*` | 移入 `exclude` 或条件加载；保留生成脚本说明 | 3–5 | 提交生成代码：污染仓库且随契约漂移；CI 生成：需 JDK/Gradle，违背 P1 单机 | 低（但每次上游升级会再冲突，需固定补丁） |
| G5 | `packages/mcp-server/src/coa_mcp/config.py:41`；`server.py` discovery 工具构造 | `use_fuseki` 是死配置，`src/` 无调用点 | 接上：按 `COA_PROVIDER_GRAPH=fuseki` 构造本地 SPARQL 客户端；或删除配置与测试 | 接上 50–70；删除 3–5 | 删除最省，但 P2 本地 MCP discovery 仍要重加 | 低–中 |
| G6 | `packages/control-plane/src/coa_control_plane/namespace/create_handler.py:36-48` 及其余 handler | `_get_service()` 直接 new `DynamoDBDAO`/`SMUSClient`，导入期读 env | 抽 `build_namespace_service()` 到 registry；DAO/元数据 store 可注入 | 40–80（多 handler 同型） | 不改 control-plane，由 `platform-gateway` 本地实现控制面契约；代价是 COA control-plane 服务本身不能本地跑 | 中–高 |
| G7 | `packages/metric-service/src/coa_metrics/api/*.py` 与 `data_source_lookup_factory.py:67-100` | 指标 CRUD/导入直接操作 Dynamo 表；lookup 直接读 SMUS env | 先抽 `MetricRepository`，再让 handler 注入；lookup 走 registry | 60–100（10 个 handler） | 不改 metric-service，由 gateway 本地实现指标契约；契约一致但 COA 指标服务不能本地跑 | 中 |
| G8 | `context-manager/src/coa_serve/session_metadata.py:53-268`；`session.py` | 会话元数据 Dynamo、记忆 AgentCore，均无抽象 | 抽出 `ConversationStore` / `MemoryStore` Protocol，保留原实现为 AWS 实现 | 30–50（只抽接口与构造注入） | 不改，会话仅 AWS 可用；P1 关闭 session 可绕过，但 P3 必须补 | 中 |

**为什么必须改（逐项）**：
- G1：不改，`GraphClient` 只能连 AWS Neptune 的 https + SigV4，无法指向本地/第三方 SPARQL 端点，违反「同一接口可切换」。
- G2：不改，向量只有 AOSS/NA、Tier3 固定绑 `graphrag-lexical-graph`，单机没有向量检索路径。
- G3：不改，三个服务在导入期拼 AWS Runtime 域名，本地 gateway 无法被调用，且导入即失败。
- G4：不改，`uv sync` 因缺失 workspace 成员失败，单机装不出环境。
- G5：不改，`use_fuseki` 永远不可达；接上才能让 MCP 走本地 SPARQL。
- G6/G7：不改，control-plane / metric-service 在 handler 内直接 new AWS DAO，本地 repository 无注入点。
- G8：不改，会话/记忆只有 AWS 实现，没有任何接口可挂本地实现。

**合计**：COA 上游改动约 **250–410 行**（不含本地 provider 实现）。改动全部集中在装配缝与硬编码点；业务算法文件零改动。

## 2.3 与上游合并能力

| 改动 | 是否破坏与上游合并 | 说明 |
|---|---|---|
| G1 构造函数加参数 | 不破坏 | 默认值保持原行为；上游改同文件可能小冲突 |
| G2 factory 加分支 | 低风险 | 上游常改 factory；补丁需按函数级重放 |
| G3 URL 覆盖 | 不破坏 | 纯新增回退分支；默认仍走 AWS |
| G4 members | **会反复冲突** | 上游会重新加回；必须登记为 fork 固定补丁，每次升级重放 |
| G5 接上 use_fuseki | 低风险 | 删除则与上游测试冲突 |
| G6/G7 抽 repository | **中高风险** | 触及 handler 构造与存储访问；上游重构时冲突概率高。策略：先用 gateway 本地实现绕开，等契约稳定再回头改 COA 服务 |
| G8 Protocol 抽取 | 低–中 | 原类保留，仅加 Protocol 与注入点 |

**结论**：G1/G3/G4/G5 可以现在改；G2 可以现在改；G6/G7 建议延到 P3，并在 P1/P2 由 gateway 承担控制面/指标面的本地实现。这样既满足「接口先定义」，又避免过早改高冲突文件。

---

# 第三部分 platform_core 落位

## 3.1 四包结构

```
coa/
  packages/
    platform-core/            # 运行时内核：ports/providers/装配/迁移；无 HTTP
      src/platform_core/
        ports.py errors.py assembly.py config.py capabilities.py
        providers/            # 由 adapters/* 迁入（A 组）
        ontology/             # ontology_pg 的存储/注册能力
        sql/
    platform-ext/             # 净新增能力（C 组 + 部分 B 扩展）
      src/platform_ext/
        facts/ prov/ source_ref/ terms/ canvas/ datagen/ healthboard/ impact/
    platform-internal/        # 原 api.py：内部服务，不对外承诺 COA 契约
      src/platform_internal/
        app.py routes/ services/
    platform-gateway/         # COA 契约 HTTP 门面（新）
      src/platform_gateway/
        app.py routers/ adapters/ providerz.py
```

**依赖方向**：
- `platform-core` 不 import `platform-ext` / `platform-gateway` / `platform-internal`。
- `platform-ext` 依赖 `platform-core`。
- `platform-gateway` 依赖 `platform-core` + `platform-ext`，并调用 COA 业务类。
- `platform-internal` 依赖 `platform-core` + `platform-ext`，不依赖 gateway。
- COA 包不得 import `platform-*`；`platform-*` 可以 import COA 的 Protocol 类型（仅类型与 `isinstance` 校验）。

## 3.2 模块去向与「尽量整合」判据

判据按优先级：
1. **I1 同职责且可挂**：能实现已有/新增接口，且适配代码 ≤ 模块 30% → 整合为 provider。
2. **I2 独有资产**：数据/算子在 COA 没有替代（事实、溯源、观测、指标绑定）→ 整合为 ext 能力，挂到相应接口后面。
3. **I3 语义冲突但有用**：平台语义与 COA 契约冲突、无法诚实表达 → 留 ext，不做契约声明，不伪造字段。
4. **I4 无消费者且被替代**：确认无路由/无测试/无内部调用 → 退役。
5. **I5 脚手架**：smoke/bench/datagen/cli → 移到 tools 或 tests，不进 core 运行时。

「尽量整合」= 默认 I1/I2；I4 只在有证据时执行，不为干净而删可用资产。

## 3.3 主要模块去向

| 模块 | 行数 | 去向 | 判据 |
|---|---:|---|---|
| `adapters/*`（不含 `ontology_pg.py`、`canvas_*`） | 2,997 | core/providers | I1 |
| `config.py` `assembly.py` `ports.py` `errors.py` `logging_setup.py` `capabilities.py` `bootstrap.py` | 1,978 | core | I1（装配） |
| `ontology_pg.py` | 4,191 | core/ontology + ext 生命周期 | I1/I2 |
| `parsers.py` `validation.py` `shapes.py` `rules.py` `sqlsplit.py` `ontology_init.py` | 1,230 | core | I1 |
| `replay.py` `evidence.py` `fact_export.py` `reindex.py` `metric_binding_overrides.py` | 912 | core/ext 工具 | I2/I5 |
| `catalog.py` 1,199；`bundle.py` 1,843；`importer.py` 892 | 3,934 | ext/adapters | I1/I2 |
| `documents.py` 509；`extraction.py` 649；`entity_view.py` 685 | 1,843 | ext | I3 |
| `reasoning.py` 594；`impact.py` 593；`healthboard.py` 832 | 2,019 | ext | I2/I3 |
| `metrics.py` 410；`metric_loader.py` 427；`metric_compiler.py` 330 | 1,167 | core/metrics + ext | I1/I2 |
| `metric_facts.py` 628；`metric_backfill.py` 353 | 981 | ext | I2 |
| `facts.py` 1,344；`context.py` 542；`answerable.py` 313；`search.py` 612 | 2,811 | ext + provider | I1/I2 |
| `prov.py` 789；`source_ref.py` 580 | 1,369 | ext | I2 |
| `termgate.py` 350；`termgov.py` 623；`termlex.py` 274 | 1,247 | ext + SKOS 投影 | I2 |
| `ontology_lifecycle.py` 187 | 187 | ext | I2 |
| `canvas_full.py` 1,524；`canvas_simple.py` 660；`canvas_disabled.py` 34 | 2,218 | ext（默认 off） | I3 |
| `datagen*.py` 2,828；`cli.py` 858；`bench_embed.py` 143 | 3,829 | tools | I5 |
| `webui.py` | 358 | ext / 条件退役 | I3/I4 |
| `smoke*.py` 4,610 | 4,610 | tests/tools | I5 |
| `api.py` 5,891 | 5,891 | platform-internal | 见第五部分 |
| 其他（`__init__.py` 等） | 3 | core | I1 |
| **合计** | **43,775** | | |

**账本校准**：79/80 未发布逐文件 A/B/C 台账；80 的 8,659/16,404/14,102 与 4,610 脚手架相加正好 43,775。但 80 文中「验收脚手架 4,810」与实际 `smoke*.py` 合计 4,610 差 200 行；按 80 的四个数字相加为 43,975，比 `platform_core` 实际 43,775 多 200。且逐文件归属无法从文档复现。P0 必须产出 `doc/_design/81-ledger.csv`，逐文件标 A/B/C/脚手架并求和，才算账本闭环。**本表不冒充原台账。**

---

# 第四部分 B 类 16,404 行处置

## 4.1 判定规则

**新口径**：B 类 16,404 行不再是「一律废弃」。其中与 COA 同职责的部分，按「能不能挂到现有/新增接口」重判为 local 实现或适配层；只有重复的对外路由绑定、以及被完全替代且无消费者的死代码才退役。A 类 provider（graph_oxigraph / vector_pg / llm_openai / embedding / object_fs 等）本身就是可直接挂上的 local 实现；B 类里真正属于 L 档的是少数（如 `search.py`、`metric_compiler.py`），大多数是 AD 或 EXT。

| 档 | 含义 | 条件 |
|---|---|---|
| L | 直接当 local 实现挂上 | 已有接口方法可直接由该模块实现，适配 ≤ 100 行或 ≤ 模块 15% |
| AD | 需适配层 | 业务逻辑可复用，但返回形状/错误/语义与契约不同，需独立 adapter |
| EXT | 无 COA 对应接口，作为扩展能力 | 可被 Query/检索内部调用，但不对外冒充 COA 契约 |
| RET | 确实退役 | 有证据证明无消费者且被 COA 实现完全覆盖；仅限路由绑定或明确死代码 |
| TOOL | 工具/测试/造数 | 不进运行时，迁 tools/tests |

## 4.2 逐模块结论

> 下表覆盖与 B 类边界相邻的主要模块；行数不等于 80 号的 16,404（B 的逐文件归属未发布，见 §3.3 账本校准）。标 L/AD/EXT/RET/TOOL 是对「整合方式」的判定，不是对原 A/B/C 分组改名。

| 模块 | 行数 | 档 | 结论 |
|---|---:|---|---|
| `api.py` | 5,891 | 拆分：AD + internal | 见第五部分；不整文件重写 |
| `catalog.py` | 1,199 | AD | 映射 COA `GraphSearch`/`GetGraphClass`/`GetGraph*Property`/`GetOntologyOverview`/`DescribeSchema`；复用约 60% |
| `bundle.py` | 1,843 | AD | 映射 `DownloadOntology`/`UploadOntology`；TTL 打包留 ext |
| `importer.py` | 892 | AD | 映射 `IngestOntologyFromS3`/proposal accept；本体导入解析复用 |
| `documents.py` | 509 | EXT | COA 无文档摄取契约；作为 Tier3 本地语料源，经 `IndexProjector` 入向量 |
| `extraction.py` | 649 | EXT | 文档抽取供 documents；不对外契约 |
| `entity_view.py` | 685 | EXT | UI 读模型 |
| `reasoning.py` | 594 | EXT | COA 无推理 operation；可作为校验门禁，不冒充契约 |
| `impact.py` | 593 | EXT | COA 无影响面 operation |
| `metrics.py` | 410 | AD | `MetricRepository` 的本地实现；契约投影只对可诚实填字段的指标 |
| `metric_loader.py` | 427 | AD | 映射 `ImportOsi`/`ExportOsi`；CSV 路径降为本地扩展 |
| `metric_compiler.py` | 330 | L | 本地 SQL 方言编译器，挂到指标校验/执行接口后 |
| `metric_facts.py` | 628 | EXT | 观测/事实计算，Tier1 执行后端 |
| `metric_backfill.py` | 353 | EXT | 回填任务，走 `JobQueue` |
| `facts.py` | 1,344 | AD | 包装为 `StructuredQueryStrategy`，或作为 Tier2 本地后端 |
| `context.py` | 542 | AD | `Query` 编排的本地实现；tier 映射见语义对齐 |
| `answerable.py` | 313 | EXT | 可回答性判定，不属 COA 契约 |
| `search.py` | 612 | L | `VectorClient` 的 hybrid 本地实现 |
| `prov.py` | 789 | AD | 映射 `QueryResult.trace`/`dataSources`；PROV-O 图留 ext |
| `source_ref.py` | 580 | AD/EXT | 值级溯源；`trace.detail` 可放摘要，结构化留在 ext 路由 |
| `termgate.py` | 350 | AD | 术语门禁结论写入 T-Box；门禁流程留 ext |
| `termgov.py` | 623 | AD/EXT | SKOS 物化为本体；治理工作流留 ext |
| `termlex.py` | 274 | AD | 词法别名投影到 `aiContext.synonyms` |
| `ontology_lifecycle.py` | 187 | AD | 发布/回滚映射为 ontology status；版本链留 ext |
| `healthboard.py` | 832 | EXT | 运维看板 |
| `canvas_*` | 2,218 | EXT | 平台独有；默认 off，配置开启 |
| `webui.py` | 358 | RET（条件） | 若采用 COA UI 则退役；否则 EXT |
| `datagen*` | 2,828 | TOOL | 造数工具，不进运行时 |
| `cli.py` | 858 | TOOL | 运维 CLI |
| `smoke*.py` | 4,610 | TOOL | 证据/冒烟脚本，移 tests/tools |

**确实该退役的无条件项**：`api.py` 中与 COA 契约重复的对外路由绑定（不是 handler 逻辑）；`canvas_disabled` 这类占位适配器可并入 provider 的 `unsupported` 实现。**条件退役**：`webui.py`、`metric_loader.py` 的 CSV 路径；必须先有替代并通过验收，不得先删。

---

# 第五部分 `api.py` 5,891 行怎么处理

## 5.1 三个选项

| 选项 | 做法 | 优点 | 致命问题 |
|---|---|---|---|
| A | 把 `api.py` 改写成严格 COA 契约适配层 | 一个进程 | 137 条路由中约 49 条无 COA 对应；要同时承担契约映射、扩展路由、旧 8080 兼容，5,891 行会变成两套语义的缝合怪 |
| B | 废弃 `api.py`，完全由 COA 接口层路由 | 契约最纯 | 丢掉 137 条路由中的平台独有能力与 8080 现网兼容；等于重写，不符合「尽量整合」 |
| C（推荐） | 退成**内部服务**，COA 契约由 `platform-gateway` 统一对外 | 单一对外契约；业务 handler 复用；8080 可平滑过渡 | 需要一个 gateway 门面与路由映射表；过渡期存在双入口 |

**推荐 C。理由**：
1. `api.py` 的职责是平台组合与路由，不是 COA 契约本身；它是接口，但是**平台内部接口**，不应成为第二套对外契约。
2. 137 条路由 vs Smithy 88 个 operation：差额说明大量能力是平台扩展；用一层 gateway 区分「契约面」与「扩展面」最清晰。
3. handler 逻辑可以按能力抽成 `AnswerService`/`MetricService`/`OntologyService`/`SourceService`，gateway 直接调用，不需要复制业务代码。
4. 8080 现网契约在过渡期保持不动；gateway 达到对等后再做反向代理/路由映射，避免一次性切换失败。

## 5.2 具体落法

- `platform-internal` 保留 FastAPI app 与现有路由，仅监听内网/localhost，不由公网直接暴露。
- 抽出四个 capability service（函数级复用，不动算法）：
  - `AnswerService`：`/answer`、`/answerable`、`/context/resolve`、`/search`
  - `MetricService`：`/metrics*`
  - `OntologyService`：`/ontology/*`、`/browse/*`
  - `SourceService`：`/documents`、`/imports`、`/facts` 的来源侧
- `platform-gateway` 按 Smithy operation 路由，调用上述 service 或 core provider。
- 平台独有路由统一加 `/ext` 前缀，由 gateway 或 internal 暴露；不混入 COA 路径。
- 过渡期：8080 继续跑原镜像；新 gateway 用独立端口验证；对等后由部署侧反代切换，不改 8080 容器。

---

# 第六部分 语义对齐清单

| # | 差异点 | 现状 | 处理 | 改谁 |
|---|---|---|---|---|
| S1 | 指标 name 模式 | COA `^[a-zA-Z][a-zA-Z0-9_]{0,127}$`；平台存在 `FIN-INS-022-v1` 这类带连字符 ID | 平台增加 `contractName` 归一化映射；只投影能生成合法 name 的指标，其余 ext-only | platform |
| S2 | `sourceTable` 必填 | COA 要求单一源表；平台指标常是多表/事实绑定 | 仅单源可诚实填写的指标进契约；多绑定指标 ext-only，不伪造 sourceTable | platform |
| S3 | `expression.dialects` | 平台实际只有 PostgreSQL | 只声明 `POSTGRESQL`；不声明未验证方言 | platform |
| S4 | `publishable/executable` | COA 无此字段 | 作为 ext readiness 资源；不塞进 `MetricDefinition` | platform/ext |
| S5 | `aiContext.synonyms` | 平台词法别名在 TermLex/SKOS | 物化 SKOS 后投影 synonyms；单一真相 | platform |
| S6 | 指标执行 | COA Tier1 按源表 SQL；平台按观测/事实表计算 | 只对「可执行」指标提供 Tier1；不可执行返回无结果，不硬算 | platform |
| S7 | 命名空间 | COA UUIDv4 多命名空间；平台单全局 | P1 固定一个 UUIDv4 默认命名空间；第二命名空间明确拒绝，不假装多租户 | platform + gateway |
| S8 | 本体身份 | COA 一个命名空间多个 ontology；平台一条全局版本链 | import/ontology → ontologyId；版本链留 ext；不用版本冒充本体 | platform |
| S9 | 发布可见性 | COA 只返回已发布；平台有 draft/publish | 仅已发布 T-Box 进契约；草稿 ext-only | platform |
| S10 | 术语治理 | COA 无治理操作，只有 SKOS 语义 | 治理流程 ext；结论必须落成 SKOS 进 T-Box | platform |
| S11 | 问答分层 | COA tier1/2/3 + confidence/trace；平台 layers/coverage/citations | 层映射 tier；P1 仅 Tier1 精确指标：执行成功且返回单条指标结果时 `confidence=1.0`，无结果不构造 `QueryResult`；Tier2/3 在 P3 用有定义的覆盖率规则，规则未定前不暴露 | platform |
| S12 | 溯源 | COA `trace`/`supportingContent`；平台 PROV-O + source_ref | trace 步骤进契约；source_ref 结构化留 ext；不塞进无 metadata 字段的 `SupportingContent` | platform |
| S13 | 错误形状 | COA 统一 error + code；平台 HTTP 4xx/5xx 文本 | gateway 统一映射；未知错误不伪装成成功 | gateway |
| S14 | 鉴权 | COA bearer/authorizer；本地无实现 | 设计阶段不做；若启用而本地无策略引擎则 fail-closed，不默认放行 | 以后 |
| S15 | 向量 score 语义 | `VectorStore.search_nearest` 要求 cosine `[-1,1]`；`base.py:137-144` 自述 `OpenSearchVectorStore` 返回 `[0,1]` 原始 `_score`，尚未换算 | 本地 `pgvector` 必须直接返回 `[-1,1]`；AOSS provider 必须在 adapter 内换算 `cos = 2*_score - 1`，或在 `capabilities` 标 `score_contract="capped"` 并禁止与本地混用未换算的分数 | platform（adapter）+ 可选 COA 修复 |

**原则**：契约字段不能诚实填写时，选择「不暴露/扩展资源」，而不是「填近似值」。这与项目既有「不许编数据」约束一致。

---

# 第七部分 分期方案

## P0 接口冻结与账本（第一交付物）

- 交付：本文件第一部分的接口清单定稿；`81-ledger.csv` 逐文件 A/B/C/脚手架台账；provider registry 接口与配置键冻结；G1–G8 改动清单评审通过。
- 验证：清单中每个接口都有定义位置、签名、错误语义、混搭策略、默认实现；台账求和 43,775；无「待补接口」。
- 不做：不写实现、不改 COA 代码。

## P1 全本地最小可跑（V1）

- 交付：
  - `platform-core` / `platform-ext` / `platform-gateway` / `platform-internal` 四包骨架。
  - 本地 provider：oxigraph、pgvector、openai、tei、postgres metadata、fs、env secret、inline dispatch、local observability；`DataSourceLookup` 直接复用 S1 的 `JsonDataSourceLookup`，不重写。
  - `platform-gateway` 实现 13 个 operation：`HealthCheck`、`GetSystemHealth`、`CreateNamespace`/`GetNamespace`/`ListNamespaces`、`ListOntologies`/`GetOntology`、`ListMetrics`/`GetMetric`/`ValidateMetric`、`GraphSearch`、`DescribeSchema`、`Query`（仅 Tier1 精确指标；`confidence=1.0` 规则见 S11）。
  - `providerz`：展示每个接口选择、capabilities、verified、reload。
- 验证：
  - 单机 compose：PG + Oxigraph + gateway，端口不占 8080；无 AWS SDK 调用、无 AWS 环境变量也能启动。
  - 契约一致性：本地静态解析 Smithy 得到 operation manifest，与 gateway 路由逐项比对。
  - 录放证明：同一组请求分别走 `graph=oxigraph` 与 `graph=neptune_replay`（录制响应回放，不联网），断言 gateway 调用链/span 树一致，仅 provider 标签不同；响应归一化后一致。
  - 数据诚实性：不可执行指标返回无结果；不伪造 confidence；不伪造 sourceTable。
  - 证据落 `doc/_evidence-coa-integration/p1/`，不写 `doc/_qa`。

## P2 仅换 graph 为 AWS（V2）

- 交付：`graph=neptune` provider；G1 改动；`IndexProjector` 同步模式；SPARQL 共同子集守卫。
- 验证：
  - 同一请求集在 V1/V2 下调用链一致（gateway span 树同形）。
  - Neptune 只读实测：query/ask/search 与本地结果在共同子集上一致；差异必须解释为引擎差异，不得静默忽略。
  - 图/向量一致性：`IndexProjector.verify` 差异集为空；切换后 `reindex` 幂等。
  - 其余接口仍本地，证明「只换一个接口」可行。

## P3 契约面补齐与 B 类整合

- 交付：指标 CRUD/OSI、正文上传/摄取、Graph class/property/overview、Tier2/3、会话与记忆、溯源映射、术语 SKOS 物化；G6/G7/G8；B 类 AD 模块逐个挂接。
- 验证：契约 operation 覆盖率 ≥ 80%；每个 B 模块有「挂到哪个接口、适配行数、测试用例」；未挂接的明确 ext。
- 退役：仅退役重复路由绑定与已证死代码。

## P4 全 AWS 与上游合并

- 交付：V4 全 AWS；第三方 provider 示例；上游合并补丁清单与 CI。
- 验证：V4 与 V1 同一套契约测试通过（允许语义差异项显式标注）；G1–G8 补丁可重放；`make` 上游同步走查通过。

---

# 第八部分 风险

| 风险 | 触发 | 应对 |
|---|---|---|
| pydantic 冲突 | COA 要求 `>=2.13.4`，平台当前 `>=2.10.4` | P0 先升平台依赖并跑 54 个测试文件（12,841 行）回归；若失败，gateway 与 internal 走进程边界（HTTP），不共享 venv。上限 `<3` |
| `platform/` 改名 | `git mv` 到 `packages/platform-core`，compose/脚本/8080 config_files 引旧路径 | 改名单独提交；保留旧镜像运行；更新 compose/脚本清单；8080 不重建。Windows 不用符号链接，改显式路径 |
| 8080 契约失效 | gateway 未对等就切路由 | 过渡期 8080 原样；gateway 独立端口；对等由验收清单门禁；切换前备份旧容器信息；失败回滚旧镜像 |
| 上游升级冲突 | G2/G6/G7 触及 factory/handler | G1/G3/G4/G5 先行；G6/G7 延到 P3；补丁全部 `LOCAL-SEAM` 标记；每次升级按补丁清单重放；G4 固定补丁 |
| 异步/同步边界 | COA Protocol 多为 async，平台 port 同步 | adapter 用 `asyncio.to_thread`；线程池有界；禁止在事件循环直接跑阻塞 PG |
| 图/向量不一致 | 两实现独立切换 | `IndexProjector` + `verify` + `reindex`；不承诺跨库事务；差异必须可见 |
| ID/命名空间语义 | 平台 ID 不符合 COA pattern；单租户 | 映射层 + 只投影合法项；默认命名空间固定 UUIDv4；多命名空间明确拒绝 |
| 契约字段无法诚实填写 | sourceTable/confidence 等 | ext-only 或不暴露；禁止填近似值（S2/S11） |
| 组合爆炸 | 任意混搭 | 只承诺 V1–V4；能力声明 + 启动校验；未知组合 fail-closed；`/providerz` 标注 |
| 测试污染生产库 | 平台测试默认 DSN | 沿用项目规则：无 `TEST_PG_DSN` 一律跳过，不回落默认口令/库 |
| 秘钥泄露 | 本地 env 凭证 | `SecretProvider` 不日志；扫描 pre-commit；凭证只走环境/外部密钥源 |

---

# 第九部分 工作量重估

| 阶段 | 内容 | 人日（±30%） | 依据 |
|---|---|---:|---|
| P0 | 接口清单、台账、registry 契约、G1–G8 评审 | 5–8 | 纯设计/核对，不含实现 |
| P1 | 四包骨架、本地 provider、13 个 operation、录放证明 | 15–22 | 复用 A 组约 7–9k 行；新增 gateway 与适配 |
| P2 | Neptune provider、G1、IndexProjector、一致性测试 | 8–12 | 单接口切换，范围可控 |
| P3 | 契约补齐、B 类 AD、G6/G7/G8、会话/溯源/术语 | 20–30 | 约 10–14 个 B 模块适配 + 8 个 operation |
| P4 | 全 AWS、第三方 provider、上游合并 CI | 12–18 | provider 补齐与流程化 |
| **合计** | | **60–88** | 不含硬件/AWS 环境等待 |

**与旧估算的关系**：旧区间 1.5–5× 是在「上游零改动」约束下得出；本版允许 250–410 行装配缝改动，取消了「绕开写死点」的大量重复实现，因此总工作量显著下降。此处是估算，不是承诺；P0 完成台账后应按模块行数重算一次。

---

# 第十部分 未验证项与证据边界

1. **B 类逐文件台账未复现**：79/80 未给出逐文件归属；本文件只给模块级判定。P0 必须产出 CSV 并对齐 8,659/16,404/14,102/4,610。
2. **80 号「验收脚手架 4,810」与实际 `smoke*.py` 4,610 差 200 行**：80 四项相加 43,975，比实际 43,775 多 200；已记录，不擅自改数。
3. **AWS provider 未实跑**：本设计未调用 AWS；P2 才做 Neptune 实测。P1 用录放证明调用链，不等价于真实 AWS 行为验证。
4. **行数估计均为估算**：G1–G8 的 250–410 行是按现有函数范围估算，±30%。
5. **COA operation 数**：`models/src/main/smithy` 共 88 个 `operation`、2 个 `service`（ControlPlane + DataLayer），已只读核对。
6. **平台路由数**：`api.py` 137 个 `@app.*` 装饰器，5,891 行，已核对。
7. **未触碰**：8080、8082、`doc/_qa*`、`doc/_evidence-audit`；未启动长期服务。

---

# 附：与 78/79/80 的关系

- 78 提供单机可运行性与硬编码点证据；本文件把硬编码点转为 G1–G8 可注入改动。
- 79 提供 A/B/C 三分与「platform 对上游零 import」；本文件把三分改为「按接口整合 + 按判据处置」，B 不再一律废弃。
- 80 提供整合可行性与风险；本文件把「可行性」落实为接口清单、四包落位与 V1–V4 组合。
- 本文件取代 80 中「`api.py` 整体改造/废弃」的二选一，改为内部服务 + gateway 门面。

---

# 附录 A：GraphStore / VectorStore 方法签名

## A.1 `GraphStore`（17 个同步方法，`stores/base.py:192-488`）

| # | 方法 | 输入 | 输出 / 错误语义 |
|---|---|---|---|
| 1 | `create_ontology(data: dict) -> dict` | 本体属性字典 | 返回创建后的字典 |
| 2 | `get_ontology(oid: str) -> dict \| None` | ontology id | 不存在返回 `None` |
| 3 | `get_ontology_by_uri(uri: str) -> dict \| None` | 本体 URI | 不存在返回 `None` |
| 4 | `update_ontology(uri: str, updates: dict) -> dict \| None` | URI + 更新字典 | 不存在返回 `None` |
| 5 | `delete_ontology(uri: str) -> bool` | URI | 返回是否存在 |
| 6 | `store_class(ontology_uri, class_uri, labels, comments, super_classes, is_mapped, query_backend, data_source_id) -> dict` | 类属性 | 返回存储结果；`is_mapped` 表示 Tier2 可回答 |
| 7 | `store_property(ontology_uri, prop_uri, label, comment, domains, ranges) -> dict` | 属性定义 | 返回存储结果 |
| 8 | `supersede_annotations(ontology_uri, subject_uris, predicates) -> int` | 主体集合 + 谓词→历史谓词映射 | 返回退休三元组数；无可退休返回 `0` |
| 9 | `load_turtle(ontology_uri, turtle, graph_uri=None) -> dict` | Turtle 字符串 | 至少返回 `graph_uri`、`bytes_loaded`；不支持时返回 `{"status":"skipped"}` 而非抛 |
| 10 | `get_graph_turtle(ontology_id) -> str \| None` | ontology id | 无图或不支持 RDF 往返返回 `None` |
| 11 | `count_classes_and_properties(ontology_id) -> dict \| None` | ontology id | `{"classes": int, "properties": int}`；不可计算返回 `None` |
| 12 | `get_vertex(vertex_uri, namespace=None, *, label_preference=None) -> dict \| None` | 顶点 URI | 返回 uri/graph_uris/types/labels/comments/edges；无出边返回 `None` |
| 13 | `search_entities(query, namespace=None, kind=None, ontology_id=None, exclude_ontology_id=None, limit=50, offset=0, *, label_preference=None) -> list[dict]` | 子串 + 过滤 + 分页 | 稳定全序；返回 uri/label/kind/graph_uris |
| 14 | `count_entities(query, namespace=None, kind=None, ontology_id=None, exclude_ontology_id=None) -> int` | 同匹配集 | 返回总数，与分页无关 |
| 15 | `get_ontology_overview(ontology_id, namespace=None, *, sample=False, label_preference=None) -> dict \| None` | ontology id | 返回 classes/object_properties/datatype_properties；不可枚举返回 `None`（上层映射 501） |
| 16 | `get_namespace_schema(namespace, *, max_results=100, include_properties=True, label_preference=None, class_prefix=None) -> dict` | 命名空间 | 返回 classes/namespace/ontologyVersion；`class_prefix` 先过滤再截断 |
| 17 | `health_check() -> dict` | 无 | 永不抛 |

## A.2 `VectorStore`（`dimensions: int` + 10 个同步方法，`stores/base.py:45-185`）

| # | 方法 | 输入 | 输出 / 错误语义 |
|---|---|---|---|
| 1 | `store_embedding(data: dict) -> dict` | entity_uri/ontology_id/entity_type/embedding_type/model_id/vector | upsert 单条 |
| 2 | `store_embeddings_batch(items: list[dict]) -> list[dict]` | 同上批量 | upsert 批量 |
| 3 | `get_embeddings_for_entity(entity_uri, entity_type=None, embedding_type=None, namespace=None) -> list[dict]` | 实体 | 返回该实体全部向量 |
| 4 | `list_embeddings_for_ontology(ontology_id, entity_type=None, embedding_type=None, namespace=None, limit=None) -> list[dict]` | ontology id | `limit` 必须在传输前生效 |
| 5 | `list_searchable_entity_uris(ontology_id, namespace=None) -> list[str]` | ontology id | 只返回 URI，不返回向量 |
| 6 | `search_nearest(vector, embedding_type, model_id, entity_type=None, ontology_id=None, top_k=10, namespace=None) -> list[EmbeddingHit]` | 向量 + 模型/类型 | `score` 必须为 cosine `[-1,1]`；见 S15 |
| 7 | `delete_embeddings_for_ontology(ontology_id, namespace=None) -> int` | ontology id | 返回删除数 |
| 8 | `delete_embeddings_for_entities(entity_uris: Iterable[str], ontology_id, namespace=None) -> int` | 实体集合 + ontology | 不能全删时抛；`ontology_id` 作用域必需 |
| 9 | `delete_index(namespace=None) -> bool` | 命名空间 | 返回索引是否存在 |
| 10 | `health_check() -> dict` | 无 | 永不抛 |

## A.3 版本与证据

- `GraphStore` / `VectorStore` 的方法签名取自 2026-11-08 只读代码。
- `VectorStore` 文档明确记载 `OpenSearchVectorStore` 的 score 尚未符合 `[-1,1]` 契约（`base.py:137-144`），这是本地/ AWS 混搭时必须先修的语义差，不因换实现而消失。
