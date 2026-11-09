# coa-gateway（P1 主线网关）

把 COA 上游契约接到本地实现，用 `COA_PROVIDER_*` 选实现，并证明「同一份调用代码 + 改配置 → 走不同实现」。
已接线：**GraphClient**（Oxigraph / Fuseki / Neptune SigV4 形状）、**VectorClient**（in-memory）、
**QueryExecutor**（PostgreSQL）、**DataSourceLookup**（S1 `JsonDataSourceLookup`）、
**ConversationStore**（SQLite）、**MemoryStore**（SQLite，词法检索）、**ObjectStore**（文件系统）、
**LLMClient**（llama.cpp 本地 GGUF，CPU）。
N4 `SourceCatalog` 列表扩展仍未接线。

## 边界

- Graph 只读：仅 SELECT/ASK，不发 Update。
- 不连 AWS：Neptune / AOSS / Athena / SMUS 只有占位实现，构造即抛错，不回退本地。
  Neptune 的「真跑」只针对本地 SigV4 形状桩，不等于真 AWS 行为。
- 不暴露端口：所有 E2E 都在验收网络内跑，不发布宿主端口。
- LLM 本地：llama.cpp 在进程内加载一个 GGUF，CPU 推理，不起服务、不开端口；
  `converse` 真跑，`converse_stream` / `embed` 明确抛 `LlmCapabilityUnsupported`。
- 不依赖额外进程：vector 是内存索引，query_executor 直连验收 PG，LLM 在进程内。

## 前置条件（否则会失败，不要硬跑）

| 项 | 现状 | 后果 |
| --- | --- | --- |
| `uv >= 0.13.4` | 本机 0.12.7 | `uv lock/sync` 拒绝运行；只能直接跑 Python |
| `smithy-generated/` | 根目录缺失 | 根 workspace 成员无法解析，`uv lock` 必然失败 |
| `coa_serve` / `coa_common` / `coa_metrics` / `coa_local_providers` | 未安装，走源码 | 需 `PYTHONPATH` 指向对应 `src` |
| 验收镜像 `agent-platform:0.1-s5` | 无 `structlog`/`boto3`/`pydantic-settings`/`sqlglot` | 导入契约或 validator 会失败；用 `coa-gateway-verify:0.1` |
| `platform-core/requirements.txt` | 已加 `structlog==26.1.0` | **下次正式重建**才进镜像；本轮未重建 |
| `llama-cpp-python` | 验收镜像未内置 | 选 `COA_PROVIDER_LLM=llama-cpp` 需在运行时装 cp312 linux 轮子 |
| 本地 GGUF | 未入库 | 本轮用 `qwen2.5-0.5b-instruct-q4_k_m.gguf`（491MB），挂载进容器 |
| Windows 主机 | `coa_common` 依赖 Unix-only `resource` | 契约链路只能在 Linux/容器/WSL 跑，Windows 原生 Python 导入即失败 |
| `coa-gateway` 未装进镜像 | 以源码挂载 + `PYTHONPATH` 运行 | 要随镜像发布需在 Dockerfile/uv 里加包 |

`coa-gateway-verify:0.1` = `agent-platform:0.1-s5` + `structlog` + `boto3` + `pydantic-settings` + `sqlglot`。
平台镜像刻意不带 AWS SDK，这一层只用于网关验证，不改验收栈。

## 配置（每个接口一个选择器）

```bash
COA_PROVIDER_GRAPH=oxigraph              # oxigraph | fuseki | neptune | platform-oxigraph | platform-fuseki | none
COA_PROVIDER_VECTOR=in-memory            # in-memory | platform-pgvector | aoss | none
COA_PROVIDER_EMBEDDING=none              # bge-local | external-http | none
COA_PROVIDER_QUERY_EXECUTOR=postgres     # postgres | athena | platform-pg | none
COA_PROVIDER_SOURCE_CATALOG=json         # json | smus | none
COA_PROVIDER_CONVERSATION=sqlite         # sqlite | dynamodb | none
COA_PROVIDER_MEMORY=sqlite               # sqlite | none
COA_PROVIDER_OBJECT_STORE=fs             # fs | s3 | none
COA_PROVIDER_LLM=none                    # llama-cpp | none
```

- 默认值（未设置时）：`graph=oxigraph`、`vector=in-memory`、`embedding=none`、其余 `none`。完整样例见
  [config/gateway.env.example](config/gateway.env.example)。
- `memory` 必须与 `conversation` 指向同一个 SQLite 文件；`session_turn` 是 `get_history` 的数据源。
- `none` = 显式禁用；访问对应属性抛 `ProviderNotConfigured`，能力表返回 `False`。
- 未知名抛 `UnknownProviderError`；选中 provider 但缺端点抛 `ProviderNotConfigured`。
- **任何情况下都不静默换实现**。

## 配置矩阵（2026-11-08 实测）

| 接口（配置键） | oxigraph | fuseki | neptune | in-memory | platform-pgvector | postgres | json | aoss | athena | smus | sqlite | fs | dynamodb | s3 | llama-cpp | bge-local | external-http |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GraphClient `COA_PROVIDER_GRAPH` | 真跑 | 真跑 | 真跑（本地 SigV4 桩，非真 AWS） | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| VectorClient `COA_PROVIDER_VECTOR` | — | — | — | 真跑 | 真跑（复用 `platform.chunk_embedding`） | — | — | 占位（未实现） | — | — | — | — | — | — | — | — | — |
| EmbeddingProvider `COA_PROVIDER_EMBEDDING` | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 真跑（TEI/BGE-M3，1024 维） | 真跑（OpenAI 兼容 HTTP；本轮对本地 TEI，未连第三方云） |
| QueryExecutor `COA_PROVIDER_QUERY_EXECUTOR` | — | — | — | — | — | 真跑 | — | — | 占位（未实现） | — | — | — | — | — | — | — | — |
| DataSourceLookup `COA_PROVIDER_SOURCE_CATALOG` | — | — | — | — | — | — | 真跑 | — | — | 占位（未实现） | — | — | — | — | — | — | — |
| SourceCatalog（N4 列表扩展） | — | — | — | — | — | — | 占位（未实现） | — | — | — | — | — | — | — | — | — | — |
| ConversationStore `COA_PROVIDER_CONVERSATION` | — | — | — | — | — | — | — | — | — | — | 真跑 | — | 占位（未实现） | — | — | — | — |
| MemoryStore `COA_PROVIDER_MEMORY` | — | — | — | — | — | — | — | — | — | — | 真跑（词法检索，非语义） | — | — | — | — | — | — |
| ObjectStore `COA_PROVIDER_OBJECT_STORE` | — | — | — | — | — | — | — | — | — | — | — | 真跑 | — | 占位（未实现） | — | — | — |
| LLMClient `COA_PROVIDER_LLM` | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 真跑（仅 converse；stream/embed 抛错） | — | — |

状态口径：**真跑** = 本轮实际执行过真实调用（服务/数据库/真实数据）；**仅契约单测** = 只验证签名与
`isinstance`；**占位（未实现）** = 声明的名字，构造或首次调用即抛出清晰错误。
本轮没有「仅契约单测」的格子：所有已接线实现都至少跑过一次真实调用（详见“实测证据”）。

### AD 改造实现（2026-11-08，落包 `coa_local_providers`）

这三个 provider 不再在网关旁另写一份传输，而是把 `platform_core` 的 AD 适配器包装成 COA Protocol，
代码落在 COA 包内（`packages/local-providers/src/coa_local_providers/`）。

| 配置值 | Protocol | AD 来源 | 落包 | 额外配置键 | 状态 |
| --- | --- | --- | --- | --- | --- |
| `COA_PROVIDER_GRAPH=platform-oxigraph` | `GraphClient` | PF-0008 `adapters/graph_oxigraph.py` | `coa_local_providers/graph_oxigraph.py` | `COA_GRAPH_OXIGRAPH_URL` / `_TIMEOUT_MS` / `_MAX_ROWS` | 真跑 |
| `COA_PROVIDER_GRAPH=platform-fuseki` | `GraphClient` | PF-0007 `adapters/graph_fuseki.py` | `coa_local_providers/graph_fuseki.py` | `COA_GRAPH_FUSEKI_SERVER_URL` / `_DATASET` / `_TIMEOUT_MS` / `_MAX_ROWS` | 真跑 |
| `COA_PROVIDER_QUERY_EXECUTOR=platform-pg` | `QueryExecutor` | PF-0010 `adapters/metadata_pg.py` | `coa_local_providers/query_pg.py` | `COA_EXECUTOR_POSTGRES_DSN` / `_POOL_MAX` / `_MAX_ROWS` / `_STATEMENT_TIMEOUT_MS` | 真跑 |

注意 `platform-fuseki` 的 `COA_GRAPH_FUSEKI_SERVER_URL` 是 Fuseki **服务根**（适配器自己拼 `/{dataset}`），
不是网关原生 `fuseki` 那种 `.../ds/sparql`。`platform-pg` 的行数上限在取回后截断并置 `truncated=true`，
不重写 SQL；`namespace` / `data_source_id` 只做契约占位，不分区连接。

### 混搭规则

| 规则 | 内容 |
| --- | --- |
| 允许混搭 | graph / vector / query_executor / source_catalog 各自独立选择，互不绑定 |
| 禁止隐式回退 | 未配置或未实现一律硬错误；`none` 只整接口禁用，不做“部分禁用” |
| 图与向量 | vector 的 `metadata.ontology_ids` 必须与图里的 `ontology_id` 对齐；维度由写入侧固定 |
| 执行器与目录 | 必须同族：`postgres` + `json`（快照来自同一 platform）。混族时 validator 只能 fail-open，不得硬拒表不存在（`source_enforcement=false`） |
| 图与执行器 | 图读 T-Box、SQL 读 A-Box；须保证 `graph_pointer` 与数据快照同一版本 |
| 事务 | 一个 gateway 对象内各实现各自建连，跨实现**无事务**；失败要显式暴露，不伪装成功 |

## 内容

| 路径 | 作用 |
| --- | --- |
| `src/coa_gateway/settings.py` | `COA_PROVIDER_<INTERFACE>` 解析、默认值、三类配置错误 |
| `src/coa_gateway/registry.py` | interface × provider → 工厂；`build_gateway()` 单进程装配 |
| `src/coa_gateway/sparql_http.py` | SPARQL 1.1 只读传输（SELECT/ASK，无 Update） |
| `src/coa_gateway/graph_oxigraph.py` / `graph_fuseki.py` | 本地图实现 |
| `src/coa_gateway/graph_neptune.py` | Neptune SPARQL：SigV4 签名形状的 `POST /sparql`（非真 AWS） |
| `src/coa_gateway/vector_memory.py` | JSONL 内存索引，真实余弦排序 + 契约过滤器 |
| `src/coa_gateway/query_postgres.py` | psycopg 3 异步执行器：信号量并发 + 双超时 |
| `src/coa_gateway/catalog.py` | 直接复用 S1 `JsonDataSourceLookup`（不重写） |
| `src/coa_gateway/conversation_store.py` | N5 SQLite：会话元数据 + `get_history`（读 `session_turn`） |
| `src/coa_gateway/memory_store.py` | N6 SQLite：`append_turn` / `get_window` / `search`（词法，非语义）/ `delete_session` / `gc` |
| `src/coa_gateway/object_store.py` | N8 文件系统：bucket/key + JSON sidecar，无 presign |
| `src/coa_gateway/llm_llama_cpp.py` | 本地 GGUF：`converse` 真跑；`converse_stream` / `embed` 明确抛错 |
| `packages/local-providers/src/coa_local_providers/graph_oxigraph.py` | PF-0008 AD → COA `GraphClient`（async 薄壳，只读） |
| `packages/local-providers/src/coa_local_providers/graph_fuseki.py` | PF-0007 AD → COA `GraphClient`（async 薄壳，只读） |
| `packages/local-providers/src/coa_local_providers/query_pg.py` | PF-0010 AD → COA `QueryExecutor`（取回后截断） |
| `scripts/prove_ad_adapters.py` | 三个 AD provider 的 `isinstance` + 真实调用证明 |
| `src/coa_gateway/gateway.py` | `LocalGateway`：能力声明 + 聚合健康检查 |
| `scripts/prove_provider_switch.py` | 切换证明：同一 probe，oxigraph vs fuseki |
| `scripts/neptune_stub.py` | 本地 SigV4 桩：只校验签名形状与 `sparql` 响应 |
| `scripts/prove_neptune_shape.py` | 同一调用代码，只换配置走 oxigraph / neptune |
| `scripts/prove_catalog_validator.py` | 证明 catalog 由 `coa_metrics.validator` 消费，打印调用链与次数 |
| `scripts/prove_combined.py` | 单进程 graph → vector → query_executor 组合调用 |
| `scripts/prove_memory_roundtrip.py` | N6 写入 → N5 `get_history` 读出的往返证明 |
| `scripts/prove_local_llm.py` | 本地 LLM 契约 `isinstance` + 真实一次补全 |
| `tests/` | 43 个用例（含 4 个真契约断言 + 7 个 N6 用例） |

## 实测证据（本轮）

- 测试：`Ran 43 tests ... OK`（容器内，含真契约 `isinstance` 与 7 个 N6 用例）。
- catalog：`NO_REWRITE OK` —— class = `coa_local_providers.json_lookup.JsonDataSourceLookup`，
  consumer = `coa_metrics.validator.validate_metric`，6 次调用（`catalog_available`1 / `known_tables`1 /
  `table_exists`1 / `get_table_columns`3），调用链含 `_check_table_references` 等 5 个函数。
- 组合：`COMBINED OK` —— 同一进程四个接口就绪；graph 取到 `tbox#Department`，
  vector 命中 `doc-0`（score 1.0），executor 真实返回 `CUST-001`（`engine=postgres`，
  `truncated=true`，22 ms），catalog 应答 `platform=True`。
- 切换（上一轮，同一代码）：oxigraph → 真实 T-Box 三行；fuseki → 临时实例 `urn:coa:gateway:demo=2`。
- N6 往返：`MEMORY_ROUNDTRIP_OK` —— `append_turn` 写两条后，`ConversationStore.get_history` 返回
  `user/assistant` 两轮；`search("落盘")` 命中 1 条，`mode=lexical-approx`。
- 本地 LLM：`LOCAL_LLM_OK` —— `isinstance(client, LLMClient)=true`；
  模型 `qwen2.5-0.5b-instruct-q4_k_m.gguf`（491,400,032 字节），冷加载 2.39 秒；
  `converse` 输出「是的，本地推理可以使用。」（64 token 上限内，`stop_reason=end_turn`，364.2 ms）；
  `embed` 明确抛 `LlmCapabilityUnsupported`，未返回假向量。
- AD 改造：`AD_OXIGRAPH_OK` / `AD_FUSEKI_OK` / `AD_POSTGRES_OK` ——
  `isinstance` 全部通过；oxigraph 返回真实 T-Box 命名图与 `tbox#Department` 三条陈述；
  fuseki 临时实例 `ASK=true`、2 行、实体 1 条陈述；postgres `SELECT 1` 真跑，
  `platform` schema 68 张表，`generate_series` 在 `max_rows=5` 下 `truncated=true`。
- `GetEntity`：`COA_GET_ENTITY_OK` —— 200 返回 `Department`（`owl#Class`）与
  `rdf:type` / `rdfs:subClassOf` / `rdfs:label` 三条陈述；缺 `uri` 400、不存在 404、非 UUID 400。

## 复现

```powershell
$PP = "/repo/libs/common/src:/repo/packages/context-manager/src:/repo/packages/metric-service/src:/repo/packages/local-providers/src:/repo/packages/coa-gateway/src"
$SNAP = "/repo/doc/_evidence-coa-integration/s1-2026-11-08/snapshot/catalog.json"

# 43 个测试
docker run --rm --network platform-acceptance_default --entrypoint python -e PYTHONPATH=$PP `
  -v D:\agentABC\coa:/repo:ro coa-gateway-verify:0.1 `
  -m unittest discover -s /repo/packages/coa-gateway/tests

# catalog + validator 调用链
docker run --rm --entrypoint python -e COA_SOURCE_CATALOG_JSON_PATH=$SNAP -e PYTHONPATH=$PP `
  -v D:\agentABC\coa:/repo:ro coa-gateway-verify:0.1 `
  /repo/packages/coa-gateway/scripts/prove_catalog_validator.py

# 三接口同进程
docker run --rm --network platform-acceptance_default --entrypoint python `
  -e COA_EXECUTOR_POSTGRES_DSN='postgresql://platform:<password>@postgres:5432/platform' `
  -e COA_SOURCE_CATALOG_JSON_PATH=$SNAP -e PYTHONPATH=$PP `
  -v D:\agentABC\coa:/repo:ro coa-gateway-verify:0.1 `
  /repo/packages/coa-gateway/scripts/prove_combined.py

# 三个 AD provider（需临时 Fuseki 容器，跑完删除）
$PPAD = "$PP:/repo/packages/platform-core/src"
docker run -d --rm --name coa-ad-fuseki --network platform-acceptance_default agent-fuseki:0.1-s5
# 等待 /$/ping 就绪后：
docker run --rm --network platform-acceptance_default --entrypoint python `
  -e COA_GRAPH_OXIGRAPH_URL=http://oxigraph:7878 `
  -e COA_AD_FUSEKI_URL=http://coa-ad-fuseki:3030 `
  -e COA_EXECUTOR_POSTGRES_DSN='postgresql://platform:<password>@postgres:5432/platform' `
  -e PYTHONPATH=$PPAD -v D:\agentABC\coa:/repo:ro coa-gateway-verify:0.1 `
  /repo/packages/coa-gateway/scripts/prove_ad_adapters.py
docker rm -f coa-ad-fuseki
```

## 只读 HTTP 服务（2026-11-08 实测）

`coa_gateway.http_api:create_app`（FastAPI）。路径 = 接口名 + 契约方法名，请求/响应字段直接用契约里的参数名与返回字段名，不改写。

| 方法 | 路径 | 请求字段 | 响应字段 | 映射 |
|---|---|---|---|---|
| GET | `/healthz` | — | `capabilities`, `health` | `LocalGateway.health` |
| POST | `/graph/query` | `sparql` | `rows` | `GraphClient.query` |
| POST | `/graph/ask` | `sparql` | `result` | `GraphClient.ask` |
| POST | `/namespaces/{namespaceId}/graph/traverse` | `startUri`, `maxDepth`, `relationshipFilter`, `direction`, `maxResults` | `entities`, `relationships`, `trace` | `DataLayerService.GraphTraverse`（COA 契约；本地用 `GraphClient.query` 执行） |
| GET | `/namespaces/{namespaceId}/graph/entity` | `uri`（query） | `entity`, `statements` | `PlatformKnowledgeService.GetEntity`（扩展契约 `coa.platform.extension`；本地用 `GraphClient.query` 执行） |
| POST | `/vector/search` | `query_vector`, `namespace`, `top_k`, `index`, `entity_type`, `require_mapped`, `ontology_ids` | `hits[{id,text,score,metadata}]` | `VectorClient.search` |
| POST | `/query/execute` | `sql`, `namespace`, `data_source_id`, `params`, `max_rows`, `timeout_seconds` | `rows`, `columns`, `row_count`, `truncated`, `duration_ms`, `engine` | `QueryExecutor.execute` |
| POST | `/llm/converse` | `prompt`, `system`, `max_tokens`, `temperature`, `top_p` | `text`, `stop_reason`, `truncated` | `LLMClient.converse` |
| POST | `/conversation/create` | `user_id`, `namespace`, `title` | `SessionRecord` 字段 | `ConversationStore.create` |
| POST | `/conversation/validate_ownership` | `user_id`, `session_id` | `result` | `ConversationStore.validate_ownership` |
| POST | `/conversation/update_activity` | `session_id`, `at?` | `SessionRecord` 字段 | `ConversationStore.update_activity` |
| POST | `/conversation/list_sessions` | `user_id`, `namespace?`, `limit` | `sessions[]` | `ConversationStore.list_sessions` |
| POST | `/conversation/get_history` | `session_id`, `limit`, `before?` | `turns[]` | `ConversationStore.get_history` |
| POST | `/conversation/delete` | `session_id` | `deleted` | `ConversationStore.delete` |
| POST | `/memory/append_turn` | `session_id`, `turn{role,content}`, `at?` | `TurnRecord` 字段 | `MemoryStore.append_turn` |
| POST | `/memory/get_window` | `session_id`, `turns` | `turns[]` | `MemoryStore.get_window` |
| POST | `/memory/search` | `namespace`, `query`, `top_k` | `hits[]`, `mode` | `MemoryStore.search` |
| POST | `/memory/delete_session` | `session_id` | `deleted` | `MemoryStore.delete_session` |
| POST | `/memory/gc` | `expires_before` | `deleted` | `MemoryStore.gc` |
| GET | `/object_store/capabilities` | — | `backend/presign/range/versioning/upload_mode` | `ObjectStore.capabilities` |
| POST | `/object_store/put` | `bucket`, `key`, `body_base64`, `content_type`, `metadata` | `{bucket,key,size,sha256,content_type,metadata,updated_at}` | `ObjectStore.put` |
| POST | `/object_store/get` | `bucket`, `key` | `body_base64`, `metadata` | `ObjectStore.get` |
| POST | `/object_store/head` | `bucket`, `key` | 元数据 | `ObjectStore.head` |
| POST | `/object_store/delete` | `bucket`, `key` | `deleted` | `ObjectStore.delete` |
| POST | `/object_store/list` | `bucket`, `prefix`, `limit` | `objects[]` | `ObjectStore.list` |

只绑定 `127.0.0.1`，无鉴权；graph / vector / query 为只读，conversation / memory / object_store 有写
（落在本地 SQLite 与文件目录）。SPARQL 必须自带 `PREFIX`（Oxigraph 不内置）。N5 的 `get_history`
在 `COA_PROVIDER_MEMORY=sqlite` 且与 conversation 同库时返回真实轮次；N6 `search` 是字符串近似，
**不是语义检索**（实现选择：N6 走词法，不调 embedding）。

契约映射现状：`/namespaces/{namespaceId}/graph/traverse` 对应 COA 真实 operation
（`DataLayerService.GraphTraverse`，见 `models/src/main/smithy/serve.smithy`）；
`/namespaces/{namespaceId}/graph/entity` 对应扩展契约 `PlatformKnowledgeService.GetEntity`
（`coa.platform.extension`，草案见 `doc/_design/85-COA平台扩展契约-2026-11-08.md`，尚未落盘 smithy）。
两者的路径、字段、响应形状都对齐。`/graph/*`、`/vector/search`、`/query/execute`、
`/conversation/*`、`/memory/*`、`/object_store/*` 是网关原语，COA 没有同名 operation，
不能按 COA 契约直接调用。`KBSearch` 现在可承接：`POST /namespaces/{namespaceId}/kb/search`
（入 `query` / `topK` / `minScore`，出 `chunks` / `trace` / `queryEmbeddingModel`），内部先调
`EmbeddingProvider` 再查 `platform-pgvector`。实测（2026-11-08）返回真实 `chunks`，`trace` 两步
`embed` + `vector_search`。**剩余差异**：pgvector 是全局语料，`namespaceId` 只校验 UUID 不分区。

## 镜像重建（2026-11-08 15:12，已执行）

- `agent-platform:0.1-s5` 重建为 `sha256:55c0cf49…`，耗时 40.2 秒（apt 层缓存命中、pip 走清华镜像）。
- 旧镜像保留为 `agent-platform:0.1-s5-rollback-20261108`（`sha256:85f5bc5f…`）。
- `agent-platform:v43-746b7a0`（8080 在用）仍指向 `85f5bc5f…`，未动。
- 回滚：`docker tag agent-platform:0.1-s5-rollback-20261108 agent-platform:0.1-s5`，再 `--force-recreate` 验收栈的 `platform` 服务。
- 仍不在镜像内：`coa-gateway`（源码挂载 + `PYTHONPATH` 运行）；`uv lock` 仍等 `smithy-generated/` 补齐。

## 已知未覆盖

- `packages/platform-core/tests/test_q8_dualrun.py::test_1`（oxigraph vs fuseki 双跑）：
  未设 `TEST_FUSEKI_URL` 时显式 skip，不记为通过（`test_2`/`test_3` 只用 reasoner，正常覆盖）。
- N4 `SourceCatalog` 列表扩展未接线；AWS 侧 AOSS / Athena / SMUS / DynamoDB / S3 仍是占位，
  构造即抛 `ProviderNotConfigured`。
- Neptune 只有「本地 SigV4 形状桩」证据，未在真 AWS 验证；不证明 IAM、VPC、引擎行为与冷启动。
- N6 `search` 是 SQL `LIKE` 字符串近似，**非语义检索**；`embed` 与 `converse_stream` 明确抛
  `LlmCapabilityUnsupported`，没有返回假结果。
- N6 与 N5 必须指向同一个 SQLite 文件；跨库配置不会静默合并，`get_history` 会读不到 turn。
- `llama-cpp-python` 与 GGUF 模型未进镜像；复现要在运行时装 cp312 Linux 轮子并挂载模型。
- Windows 原生 Python 无法导入 `coa_common`（`resource` 仅 Unix），契约链路只能在 Linux/容器/WSL 跑。
- 镜像重建后才生效：`platform-core/requirements.txt` 的 `structlog==26.1.0` 已随
  `agent-platform:0.1-s5` 重建（`55c0cf49…`）进入镜像；`coa-gateway` 仍是源码挂载，未进镜像。
