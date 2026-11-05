# COA（Context Ontology Accelerator）识别报告

> **一句话结论**：AWS 官方的 **Context Ontology Accelerator** 是一个 **Apache-2.0 的可部署参考实现 / 解决方案骨架**（CDK + Neptune + OpenSearch Serverless + Bedrock + AgentCore），不是可直接 pip 安装的库。它的**本体建模、诱导、审批、校验逻辑**适合当"本体层内核"的参考骨架；但**运行时后端已写死 AWS**，要变成"云中立"需要替换 4 个后端（图、向量、LLM、元数据）并重写 IaC，工作量以周计而非小时计。
>
> 判断把握度：**≥95%**。仓库属 `aws` 官方组织，AWS What's New 与官方博客直接引用该地址。

---

## 1. 识别结果与来源

| 项 | 值 |
|---|---|
| 仓库 | `https://github.com/aws/context-ontology-accelerator` |
| 组织归属 | `aws`（AWS 官方组织，非 aws-samples / awslabs） |
| Star / Fork | 1,076 / 140 |
| 主语言 | Python（3.12）+ TypeScript |
| License | Apache-2.0（根目录 `LICENSE` 为 Apache License 2.0 原文） |
| 创建时间 | 2026-07-28 |
| 最近提交 | 2026-10-31（API `pushed_at`）；克隆到的 HEAD `bacd1aa` 为 2026-10-29 |
| 最新 Release | `v0.3.8`（2026-10-29） |
| Open Issues | 67 |
| 官方说明 | "An open-source, ontology-based semantic context accelerator that enables AI agents to make more accurate, consistent, and explainable decisions." |

官方发布渠道：

- AWS What's New：`https://aws.amazon.com/about-aws/whats-new/2026/07/aws-context--ontology-accelarator-generally-available/`
  - 明示 "available today on GitHub under Apache 2.0"，初次发布使用 **Neptune 图存储 + OpenSearch Serverless 向量存储 + Bedrock 基础模型**。
- AWS Database Blog 也直接链接 `github.com/aws/context-ontology-accelerator`。

**同名干扰项**（均非官方，勿混用）：

- `dashjim/context-ontology-accelerator-china`（1 star，中国区改造版，基于上游 v0.3.5，自述"非 AWS 官方发布"）
- `logesh-cuedo/context-ontology-accelerator`、`-og`（0 star，个人 fork）
- `ChihiroNishioka/local-context-ontology-accelerator`（0 star，本地化实验）
- `yama3133/fortune-ontology`（1 star，复刻 COA store 契约的第三方项目）

> 另：早期检索到的 "Cloud Operations Accelerator (COA)" 是 AWS 合作伙伴的**线下工作坊计划**（Control Tower Landing Zone 交付），无开源仓库，与本次目标无关。

---

## 2. Clone 结果

| 项 | 值 |
|---|---|
| 命令 | `git clone --depth 1 https://github.com/aws/context-ontology-accelerator.git D:\agentABC\_refs\coa` |
| 结果 | **成功** |
| 路径 | `D:\agentABC\_refs\coa` |
| HEAD | `bacd1aa393e31cf2bdbff1bb12186df99479cf71` (`Mirror sync f9161083`, 2026-10-29) |
| 分支 | `main`（浅克隆，仅 1 个提交历史） |
| 体积 | 工作树 1,863 个文件 / 约 24.4 MB；**无 submodule、无 LFS** |

注意：README 建议"用 release tag 而不是 main tip"，`main` 跟踪开发中状态。若要做二次开发，建议 `git fetch --depth 1 origin tag v0.3.8` 后基于 tag 建分支。

---

## 3. 形态判断

**结论：可部署的完整解决方案 / 参考实现（Reference Implementation），不是可复用库，也不是纯 IaC 示例。**

依据：

1. `infra/` 是完整 AWS CDK（TypeScript）应用，`infra/bin/app.ts` 装配 foundation + services 多层 Stack，`scripts/deploy.sh` / `destroy.sh` / `preflight-deploy.sh` 是真实部署入口。
2. 运行面不是"一个进程"：control-plane（Lambda/API Gateway）、data-layer（Lambda）、sources（Lambda + Step Functions）、ontology-engine（FastAPI on ECS/Lambda）、context-manager（**Bedrock AgentCore Runtime**）、mcp-server（AgentCore Runtime + FastMCP）、vkg（ECS + Ontop Java 容器）、web-app（CloudFront + React）。
3. 根 `pyproject.toml` 声明 `uv workspace`，成员是 9 个内部包；**没有任何包发布到 PyPI**，`packages/*/pyproject.toml` 只服务于 monorepo 构建。
4. 状态是"通用加速器"，不是某客户定制：命名空间隔离、角色授权（Cedar）、平台角色均已产品化。
5. 但它并非空壳模板：`packages/ontology-engine` 有完整本体诱导、SHACL/HermiT 校验、embedding 流水线，可作为代码级参考。

---

## 4. 技术栈与依赖

| 层 | 技术 |
|---|---|
| 语言 | Python 3.12、TypeScript（Node 22）、Java 17–24（Smithy codegen、Ontop） |
| API 契约 | Smithy → OpenAPI + Python server interface + TS client（`models/` 为真源） |
| IaC | AWS CDK v2（TypeScript），cdk-nag 风格的合成测试 |
| 计算 | Lambda、ECS（VKG）、Bedrock **AgentCore Runtime**（serve / MCP） |
| 图存储 | Amazon **Neptune DB**（RDF/SPARQL）或 **Neptune Analytics**（property graph） |
| 向量存储 | **OpenSearch Serverless**（AOSS，k-NN + BM25 混合检索） |
| LLM / Embedding | **Amazon Bedrock**（Converse API、Guardrails、Titan/Cohere embedding） |
| 元数据 | **DynamoDB**（`DatastoreDAO` 唯一实现） |
| 对象存储 | **S3**（ontology.ttl / mappings.obda / schema.sql；导入导出） |
| 数据源联接 | Glue Catalog、Athena（跨源联邦）、Redshift Data API、JDBC（asyncpg/PostgreSQL、Databricks connector） |
| 本体引擎 | OWL 2 QL、RDF/Turtle、R2RML、Ontop 5.x、owlready2 + HermiT、pyshacl |
| 前端 | React + Cloudscape Design System |
| 测试 | pytest（单元 + 集成 + 安全）、Vitest/Playwright；ruff、mypy strict |
| 编排 | Nx + uv + pnpm |

**AWS 服务写死程度（源码 `packages/*/src` + `libs/*/src`，共 404 个 .py，按 occurrence 计数）**

| 关键词 | 命中 | 含义 |
|---|---:|---|
| neptune | 819 | 图后端、SigV4 签名、`neptune-db://` URI、图查询 |
| athena | 767 | 跨源联邦执行器、Glue 目录 |
| bedrock | 698 | LLM、embedding、guardrail、模型 ID 常量 |
| glue | 642 | 数据源发现与元数据 |
| dynamodb | 510 | 元数据/作业/会话存储 |
| opensearch | 355 | 向量索引、混合检索、AOSS 代理 Lambda |
| boto3 | 269 | AWS SDK 直接调用 |
| sqs | 103 | 异步导入/删除任务 |
| `s3.` | 40 | 对象读写 |

全仓（含测试与文档）总量：boto3 1,873 次/285 文件；neptune 3,014 次/255 文件；bedrock 3,915 次/271 文件。**测试也被 AWS mock 深度覆盖**（moto、boto3-stubs），说明 AWS 耦合是设计前提而非疏漏。

---

## 5. 核心机制

### 5.1 本体如何定义

- 形式：**OWL 2 QL 的 T-Box**，以 RDF 三元组 / Turtle 序列化，每个 ontology 独立 named graph（`packages/ontology-engine/docs/ontology-data-model.md` 有完整术语说明）。
- **只生成 T-Box，不物化 A-Box**：实例数据留在源 SQL 表中，查询期通过 R2RML + Ontop 虚拟化（VKG）。
- 关系型 → 本体的映射：`inducer/strategies/table_to_ontology.py::_build_proposal_ontology`（T-Box 构造）；`inducer/strategies/base.py::InductionStrategy.build_r2rml`（R2RML 映射）。
- 约束：`validation/shapes/config.py::compile_to_shacl` 编译 SHACL；校验器 `validation/validators/tier1.py` 用 owlready2 + HermiT 做一致性检查、pyshacl 做 shape 校验。
- 元模型存 `proposals.py`（提案、审批、版本、supersede 注解历史）。

### 5.2 如何抽取

LLM 驱动、双通道、人工审批闭环：

- 结构化：读 Glue/Athena 采样 → 推断表/列/FK → 生成类与属性 → 提案（`inducer/strategies/table_to_ontology.py`）。
- 非结构化：文档切分 + 抽取（`inducer/unstructured/services/pipeline.py`、`class_grounding.py`、`class_normalizer.py`、`description_generator.py`），向量落 OpenSearch。
- LLM 调用封装：`inducer/services/llm.py`（Bedrock）；同步封装 `libs/common/src/coa_common/bedrock.py::BedrockClient`（默认模型 `us.anthropic.claude-haiku-4-5-20251001-v1:0`，可用 `BEDROCK_CHAT_MODEL_ID` 覆盖）。
- 人工在环：proposal → steward 审阅 → `catalog/ingest.py` 接受入库；append 模式用 `supersede_annotations` 退休旧值而非叠加。

### 5.3 如何存储

- 图：`NeptuneDBGraphStore`（SPARQL + GSP，`stores/neptune_db_graph.py`，自实现 SigV4 `_sign`），或 `NeptuneAnalyticsGraphStore`（`stores/na_graph.py`，无 SPARQL 面）。
- 向量：`OpenSearchVectorStore`（`stores/opensearch_vector.py`），索引按 namespace 切分。
- 元数据：`DynamoDBDAO`（`libs/common/src/coa_common/dao/dynamodb.py`，唯一实现）。
- 制品：S3 `ontologies/{namespace}/{version}/{ontology.ttl,mappings.obda,schema.sql}`，VKG 容器启动时下载（`packages/vkg/entrypoint.sh`）。

### 5.4 如何查询与服务上层

三层解析（`packages/context-manager/src/coa_serve/`）：

- **Tier 1**：预定义指标 SQL，执行器 `clients/athena.py::AthenaQueryExecutor`、`clients/redshift_data.py`、`clients/source_db.py::SourceDBQueryExecutor`（asyncpg/PostgreSQL、JDBC）。
- **Tier 2**：VKG，SPARQL → Ontop → SQL；`tier2/ontop/strategy.py`、`nl_to_sparql.py`、`vkg_translator.py`、`clients/vkg.py`。
- **Tier 3**：图遍历 + 向量检索 + agentic 规划（`tier3/graph_traverser.py`、`vector_retriever.py`、`agentic/planner.py`、`synthesizer.py`）；可选 graphrag-toolkit 词法基线（`lexical/baseline_retriever.py`）。
- 对外：`clients/factory.py` 组装 `ClientSet`；MCP 暴露 6 个工具（`packages/mcp-server/src/coa_mcp/server.py`，FastMCP，list_metrics / describe_schema / query / translate_sparql / rag_retrieval / graph_traversal）。
- 授权：namespace + 角色（owner / maintainer / data-steward / data-analyst）+ 平台角色，Cedar 策略（`tier2/cedar_authorizer.py`）。

---

## 6. 已有抽象程度（重要）

**已经是插件式、可直接挂新实现的点：**

| 位置 | 契约 | 现有实现 | 是否易扩展 |
|---|---|---|---|
| `packages/ontology-engine/src/coa_ontology/stores/base.py` | `GraphStore` / `VectorStore`（`typing.Protocol`） | Neptune DB、Neptune Analytics、OpenSearch | **是**，契约清晰，`build_stores` 只需加分支 |
| `stores/factory.py::build_stores` | `WORKBENCH_BACKEND` 环境变量选后端 | `opensearch_neptune` / `na_only` | **是**，但需新增实现类 |
| `packages/context-manager/src/coa_serve/clients/base.py` | `GraphClient` / `VectorClient` / `LLMClient` / `QueryExecutor` | Neptune / AOSS / Bedrock / Athena+Redshift+JDBC | **部分**，工厂是硬编码默认集 |
| `clients/factory.py::_build_default_clients` | 组装 `ClientSet` | 四个 AWS 实现 | 需改这一处（单点） |
| `libs/common/src/coa_common/dao/base.py` | `DatastoreDAO` | 仅 `DynamoDBDAO` | 契约在，缺第二实现 |
| `packages/vkg` | Ontop 5.x + OBDA/R2RML | JDBC 数据源（含 PostgreSQL）可复用 | **较好**，换连接串即可；但制品从 S3 拉取 |

**写死、无法靠配置绕开的点：**

1. `neptune_db_graph.py` 内置 SigV4 签名、`_resolve_graph_base()` 读 Neptune endpoint、SPARQL/GSP 语义；换 PG 不能只改连接串。
2. `clients/neptune.py::NeptuneGraphClient` 同样 SigV4 + `:8182` SPARQL HTTP。
3. `lexical/store_factory.py::build_graph_store/build_vector_store` 直接把 `neptune-db://` / `aoss://` 交给 graphrag-toolkit 的 `GraphStoreFactory` / `VectorStoreFactory`，第三方 toolkit 只认这两种 URI。
4. Bedrock Guardrails 语义渗入 `clients/bedrock.py::_classify_guardrail`、`GuardrailOutcome`、`coa_common/guardrail_screener.py`；非 Bedrock LLM 无法等价映射。
5. 元数据表、SQS 队列、EventBridge、Step Functions、Cognito、IAM 全部由 CDK 创建（`infra/lib/stacks/**`），无 SQL migration / 无 compose 清单。
6. 部署面强绑 AgentCore Runtime（`main.py::BedrockAgentCoreApp`、`@app.entrypoint`；`mcp-stack.ts` 用 `bedrockagentcore.Runtime`）。

---

## 7. 成熟度

| 维度 | 事实 |
|---|---|
| 代码规模 | 960 个 .py / ≈287,510 行（含测试）；542 个 .ts/.tsx / ≈112,458 行 |
| 测试 | 482 个 `test_*.py` + 142 个 `*.test.ts`/`*.spec.ts`；pytest 有 unit/integ/security/slow 标记 |
| CI | `.github/workflows/pr.yml`：Smithy codegen → version drift → `nx affected lint` → `nx affected test` → CDK synth → full test suite；另有 `pages.yml`、`ai-pr-review.yml` |
| 发布 | 版本 `0.3.8`，有 release 流程；`make version` 校验版本一致性 |
| 治理 | **只读镜像，不接受 PR**（`CONTRIBUTING.md` / README），只能 fork 或提 Issue |
| 质量约束 | ruff、mypy strict、cdk-nag 式安全测试（TLS/静态加密回归）、供应链 NOTICE 自动生成 |
| 风险 | 项目仅 3 个月大，67 个 open issue，API 仍会变（README 明示 main 不稳定） |
| 许可风险 | 自身 Apache-2.0 可改可商用；但运行时依赖 **owlready2 = LGPL-3.0**（NOTICE 已列），闭源分发需评估 |

---

## 8. 三个必答结论

### (a) 能否作为"云中立平台"的本体层内核？

**分层回答：**

- **本体层语义内核（推荐复用）**：可以。OWL 2 QL T-Box + R2RML 映射 + 提案/审批/supersede + SHACL/HermiT 校验 + 版本与命名空间隔离，这套设计是**领域无关**的，和 AWS 无关，可作为你平台"本体层"的规格与代码骨架。
- **运行时内核（不建议直接复用）**：不可以。图/向量/LLM/元数据 + IAM/AgentCore/CDK 全部 AWS 绑定，直接部署等于把"云中立"目标反向实现。
- **现实路径**：fork 后**只保留 `packages/ontology-engine` 的领域层 + `stores/base.py` 契约 + `libs/common` 的纯逻辑部分**，另写 PG 版存储与 OpenAI/Ollama 版 LLM；把 `context-manager`、`infra`、`vkg`、`web-app` 当作"参考架构"而非运行代码。

### (b) 改成可切换底层（Neptune ↔ PG、OpenSearch ↔ pgvector、Bedrock ↔ 本地 LLM）要动的具体位置

| # | 目标 | 文件 | 符号 / 改法 |
|---|---|---|---|
| 1 | 图后端 | `packages/ontology-engine/src/coa_ontology/stores/factory.py` | `build_stores()` 增加 `pg_rdf` 分支；新增 `stores/pg_graph.py` 实现 `GraphStore`（`base.py`） |
| 2 | 图后端（必须解决 SPARQL） | `stores/neptune_db_graph.py` | 参照 `NeptuneDBGraphStore`：`load_turtle`/`get_graph_turtle`/`get_vertex`/`search_entities` 依赖 SPARQL/GSP；PG 无 SPARQL → 需叠 Oxigraph / Jena / rdflib+pgsql，**不能只写 SQL 适配器** |
| 3 | 图客户端（serve） | `packages/context-manager/src/coa_serve/clients/neptune.py`、`clients/factory.py::_build_default_clients` | 用新 `GraphClient` 替换 `NeptuneGraphClient`；保留 `GraphClient` 契约（`clients/base.py`） |
| 4 | 向量后端 | `stores/opensearch_vector.py`、`stores/factory.py` | 新增 `PgVectorStore` 实现 `VectorStore`；注意 `search_nearest` 的余弦分数换算契约（`base.py` 明确 `cos = 2*score-1` / `1-l2²/2`）与 `delete_index`、`list_searchable_entity_uris` |
| 5 | 向量客户端（serve） | `clients/opensearch.py::OpenSearchVectorClient`、`clients/factory.py` | 换 `VectorClient` 实现；`hybrid_search`（BM25）需用 PG `tsvector` 重写，不能直接等价 |
| 6 | Embedding | `packages/ontology-engine/src/coa_ontology/bedrock_embeddings.py::BedrockEmbeddingClient`、`libs/common/src/coa_common/embeddings.py::BedrockEmbedder` | 抽 `Embedder` 接口，新增 OpenAI-compatible / Ollama 实现；`store_embedding` 的 `model_id` 需保持可区分 |
| 7 | LLM（serve） | `clients/bedrock.py::BedrockLLMClient`、`clients/base.py::LLMClient` | 新实现 `converse` / `converse_stream` / `embed`；`GuardrailOutcome`、`_classify_guardrail` 属 Bedrock 专有，改为可选装饰层 |
| 8 | LLM（同步） | `libs/common/src/coa_common/bedrock.py::BedrockClient`、`inducer/services/llm.py` | 统一走 7 的抽象；`FALLBACK_CHAT_MODEL_ID`、`resolve_chat_model_id()` 改为配置化 |
| 9 | 元数据 | `libs/common/src/coa_common/dao/dynamodb.py::DynamoDBDAO` | 新增 `PgDAO` 实现 `dao/base.py::DatastoreDAO`；表结构需自建（原表由 `infra/lib/stacks/foundation/storage-stack.ts` 创建） |
| 10 | 词法/Tier3 基线 | `packages/context-manager/src/coa_serve/lexical/store_factory.py::build_graph_store/build_vector_store` | 只认 `neptune-db://` / `aoss://`；改为可注入，或直接旁路 `baseline_retriever.py` |
| 11 | VKG 制品源 | `packages/vkg/entrypoint.sh`、`packages/vkg/translate-server.py` | 启动时 `aws s3 cp` → 改本地卷/PG 表；Ontop JDBC 目标可保留 PostgreSQL |
| 12 | 部署面 | `infra/lib/stacks/foundation/storage-stack.ts`（`neptune.CfnDBCluster`、`opensearchserverless.CfnCollection`）、`network-stack.ts`、`serve-stack.ts`、`infra/bin/app.ts` | 自建版另写 compose/K8s；仓库**无 docker-compose、无 Helm、无 TF**，等于从零补部署层 |

**最小可行改造顺序建议**：`stores/base.py` 契约不动 → 先做向量（pgvector 最易）→ 再做 LLM/Embedding → 再做元数据 PG → 最后做图（SPARQL 是硬骨头，或保留 Neptune 作为 first-class，自建版用 Oxigraph）。

### (c) 若只能借鉴不能复用，可借鉴清单

1. **数据模型**：`packages/ontology-engine/docs/ontology-data-model.md`（T-Box / A-Box / named graph / OWL 2 QL / R2RML 的取舍说明）——可直接作为你平台的规格输入。
2. **接口契约**：`stores/base.py::GraphStore/VectorStore`、`clients/base.py::ClientSet`——按它们设计你的 SPI，尤其 `search_nearest` 的分数归一化、`supersede_annotations` 的历史语义。
3. **人机闭环**：proposal → steward 审批 → accept 入库 → append 时 supersede——这是本体类产品最容易忽略、COA 做对了的部分。
4. **分层查询**：Tier 1 指标 SQL / Tier 2 VKG / Tier 3 图+向量+agentic 的路由与 trace 结构（`coa_serve/orchestrator.py`、`step_ids.py`）。
5. **校验流水线**：tier1（HermiT + pyshacl）/ 约束编译 `compile_to_shacl`。
6. **MCP 工具面**：6 个工具的入参出参与 `describe_schema` 契约，可直接抄成你的 MCP 层。
7. **权限模型**：namespace + 角色 + 平台角色的双层授权（Cedar 可替换为 OPA/Casbin）。

---

## 9. 风险与建议

1. **版本风险**：3 个月新项目、0.3.x、67 open issues、只读不接受 PR；建议锁 `v0.3.8` tag，不跟 main。
2. **改造量风险**：真正的成本在图后端 SPARQL 语义与 AgentCore 运行时，而非"换个连接串"。若团队目标只是"抽象 AWS 依赖"，COA 的**契约层**价值大于其实现层。
3. **依赖许可**：owlready2（LGPL-3.0）随本体校验进入依赖链，商业闭源分发需法务确认。
4. **定位建议（呼应用户"aws 做本体、自建做替代"）**：把 COA 当 **AWS first-class 实现的参考规范 + 契约来源**；自建实现按同一 `GraphStore/VectorStore/LLMClient` 契约落地。这样 AWS 与自建共享本体模型与 MCP 出口，只是后端不同——正是"可切换底层"的最短路径。

---

## 10. 来源

- AWS What's New: <https://aws.amazon.com/about-aws/whats-new/2026/07/aws-context--ontology-accelarator-generally-available/>
- GitHub: <https://github.com/aws/context-ontology-accelerator>
- 本地代码：`D:\agentABC\_refs\coa`（HEAD `bacd1aa`，v0.3.8）
