# 12 · A-Box 接入实测 与 写/归纳链路本地化评估

- 日期：2026-11-09
- 性质：**只在读路径上动手**（导出 + 灌图 + 校验）；写/归纳链路**只评估、不实现**
- 边界：不写 8080/8082、不动其容器与端口、不写密钥、不新增契约外路由
- 相关：`09-platform整合评估.md` §14（需扩展清单）、`10-本地起栈.ps1`、`doc/coa-x/tools/coa_abox_local.py`

---

## 第一部分 · A-Box 实测

### 1. 结论先说

1. **模型对得上，不是重大不一致。** 8080 的 A-Box 用了 156 个类，`fsldm-merged.ttl` 里正好 156 个 `owl:Class`，逐个比对**缺失 0 个**；实例的 `rdf:type` 直接就是 COA T-Box 的类 IRI。
2. **契约对不上。** COA 契约没有「查某个类下实例」的 operation，`GraphVertexKind` 也没有 `individual`。按第一原则不发明私活路由，已写入 `09` §14 的需扩展清单。
3. **现有唯一的实例可读通道（`GraphSearch` 不带 kind）在实例量级上跑不通**：同一条 where，count 0.7 s，search 101.8 s，经 8099 直接 500。详见 `09` §14.3。**这是本轮最硬的发现**，比「没有 operation」更影响设计。

### 2. 源端事实（只读）

| 项 | 实测值 | 取法 |
|---|---|---|
| 文档数 | 3,066 | `platform.document` |
| A-Box 命名图 | `urn:platform:graph:abox:synthetic` | 8080 Oxigraph |
| A-Box 三元组 | 304,919 | 同上 |
| A-Box 主语数 | 60,525（含 104 个 `skos:Concept` + 1 个 `ConceptScheme`） | 同上 |
| 领域实例数 | 60,420 | 同上 |
| 领域类数 | 156 | 同上，按 `?s a ?c` 去重 |
| 实例 URI 形状 | `urn:platform:synthetic/{小写表名}_{类名}-{序号}` | 例：`urn:platform:synthetic/agreement_Policy-05819` |

**命名空间这条如实报**：源库的实例层**没有** namespace/tenant 字段（`information_schema` 全库只有 `ontology_import.target_namespace`、`shapes_registry.namespace` 两处，且都不落在实例上）。实例 URI 里也没有命名空间段。因此「按命名空间取子集」在源端无法以 namespace 为键，只能退化为「按类取」；本次按 FSLDM 的 `agreement` 命名空间（IRI 前缀）取类，落到 COA 的演示命名空间 UUID 下。**没有为了凑出「按命名空间」而编造一个字段。**

### 3. 取了哪个子集、为什么是这四个类

选 `https://w3id.org/fsldm/agreement#` 下四个类，理由只有一个：**它们的实例数能和平台自己的 PostgreSQL 表一行对一行地核**。其余类（`ins:*`、`bank:*` 等）在合成数据里与表不是 1:1，核不上，不做。

| A-Box 类 | 源实例数 | 对照表 | 表行数 | 一致 |
|---|---|---|---|---|
| `agreement#Policy` | 6,000 | `platform.ins_policy` | 6,000 | ✅ |
| `agreement#CreditAgreement` | 5,020 | `platform.bank_loan_account` | 5,020 | ✅ |
| `agreement#Account` | 5,000 | `platform.bank_deposit_account` | 5,000 | ✅ |
| `agreement#Application` | 2,000 | `platform.bank_credit_application` | 2,000 | ✅ |
| 合计 | **18,020** | | **18,020** | ✅ |

导入量：**18,020 实例 / 121,130 三元组**。

### 4. 落到哪里

```
命名空间  ed70a15c-2d42-4dc9-8c61-33b2584f05fd
图 URI    https://coa.local/graph/ed70a15c-2d42-4dc9-8c61-33b2584f05fd/urn%3Acoa%3Aabox%3Aplatform-synthetic
ontology_id（仅作图选择键） urn:coa:abox:platform-synthetic
```

- 独立命名图，**不混** T-Box 图（`…/https%3A%2F%2Fw3id.org%2Ffsldm%2Fcodes`，2,675 三元组）和指标图（`urn:coa-metrics:`）。
- **没有**给它写 registry 行：它不是本体，不冒充 `ListOntologies` 的一条。`ontology_id` 只用于 `GraphSearch?ontology_id=` 选中这张图。

### 5. 校验链（工具：`doc/coa-x/tools/coa_abox_local.py`）

三道闸门，任何一道不等即 `SystemExit`，不继续写：

1. **源图 vs 平台 PG**：四个类的源图实例数 == 对应表行数（上表），另与写死的 2026-11-09 基线比对。
2. **导出 TTL vs 源图**：本地 rdflib 解析 CONSTRUCT 结果，按类计数与三元组总数必须与源图完全相等（运行时 121,130 == 121,130）。
3. **COA 存储回读 vs 导出 TTL**：GSP PUT 后用 SPARQL `COUNT(DISTINCT ?s)` 与 `COUNT(*)` 回读，按类计数与总三元组必须相等。

可复现：

```powershell
.\.venv-coa-local\Scripts\python.exe doc/coa-x/tools/coa_abox_local.py --namespace ed70a15c-2d42-4dc9-8c61-33b2584f05fd --dry-run   # 只导出+校验
```

### 6. 交叉证据

| 证据 | 命令 | 结果 |
|---|---|---|
| 8080 自报实例总数 | `GET http://127.0.0.1:8080/browse/ontology/instances?class=https://w3id.org/fsldm/agreement%23Policy&limit=2` | `total: 6000`，首两条 `Policy-00000/00001` |
| COA 认得这个类 | `GET :8099/namespaces/<ns>/graph/class?uri=…agreement%23Policy` | `kind: class`，label `保单`，`isMapped` 空，7 条边 |
| COA 图里有实例 | 直连 Oxigraph `GRAPH <…abox…> { ?s a <…#Policy> }` | 6,000 |

### 7. 如实记录的三个局限

1. **对象引用指向切片外。** 切片只取「主语属于这四个类」的三元组；`core#hasParty`、`core#hasMetric`、`core#hasStatus` 指向的实例在源库存在、本次**未加载**，读出来是悬空 IRI。没有为了让图「看起来完整」去补造对象。
2. **`isMapped` 为空。** 这四个类没有 R2RML 映射标记，结构化 Tier-2（NL→SQL/Ontop）这条路对它们也还没铺，所以「类下实例」在 COA 里目前**没有一条能用的服务端路径**（图扫描超时、结构化路径未映射）。
3. **性能地雷已生效。** 因为 A-Box 在同一个命名空间前缀下，任何「不带 kind、不带 ontology_id」的 `/graph/search` 都会命中 100 s 级查询。5173 的 Explorer 固定传 `kind=class`（`use-graph-classes.ts:62`、`MetricForm.tsx:206`），所以界面不受影响；但这是**要么修查询形状、要么把 A-Box 挪出该命名空间**的欠账，不能装看不见。

---

## 第二部分 · 写/归纳链路本地化评估（不动手）

前提：本地已有 `coa-local-pg`（**pgvector 扩展已装**）、`coa-local-oxigraph`、8099 桥、8101 引擎、以及 8081 的 `text-embeddings-inference`（`bge-m3`，1024 维，max_input 2048）。以下「工时」为单人估算，含联调，不含契约改动。

| # | 依赖点 | 现在卡在哪 | 本地最小可行替代 | 需要新增什么 | 工时 |
|---|---|---|---|---|---|
| 1 | `POST /ontologies/{id}/upload`（`catalog/routers/ontologies.py:825`） | 落盘与注册已是本地（`ONTOLOGY_STORAGE_PATH` + PG registry），**卡在 `ingest_ontology_and_wait` 必须写向量索引并等其可检索** | 8081 的 bge-m3 出向量 + 5444 的 pgvector 存向量；或先上 `COA_PROVIDER_ONTOLOGY_VECTOR=none`（只入图+注册，检索不可用，必须显式选择、缺省拒绝启动） | ① VectorStore 的 pgvector 实现；② embedding provider（HTTP→8081，维度 1024）；③ 把「等 AOSS 最终一致」改成同步写完即返回 | 3–5（no-op 路线 0.5，但检索丢失） |
| 2 | induction job（`induce_catalog.py:1205`，`POST /induce/`） | ① LLM 走 `coa_common.bedrock`（列→类定义）；② embedder 走 Bedrock；③ job 表仍走 DynamoDB（`ontology_registry_pg` 只 patch 了 catalog 读函数）；④ 数据源需本地目录快照 | LLM 用 OpenAI 兼容本地端点（`platform-core/adapters/llm_openai.py` 可搬）；embedder 走 8081；图写 Oxigraph；job 状态进 PG | ① `dynamo_store` 的 job/proposal 函数 PG 适配（含 `active-jobs`、终态清扫）；② `coa_common.bedrock` 的 LLM 抽象加本地 provider（无键拒绝启动）；③ embedder provider 与 #1 共用 | 5–8 |
| 3 | proposal（`proposals.py`，含 accept / validate / infer-constraints / repair-datatypes） | ① 产物走 S3 + presign；② `ObjectStorePort` 由 platform-core 的 `resolve` 提供；③ 匹配/去重依赖向量；④ 写图 | 文件落本地目录（`object_fs` 适配器已有），presign 换成「带过期与一次性 token 的本地下载/上传端点」；向量复用 #1 | ① 本地对象存储 provider + 令牌校验；② 与 #1 共用的向量索引；③ accept 流水线在本地图上的回归用例 | 3–5 |
| 4 | S3 产物（`dynamo_store.presign_proposal_artifact*`、`write_and_presign_ontology_download`） | 全部 `boto3` + `generate_presigned_url`，且 STS 取账号用于拼 bucket | 本地对象目录 + 直传/直下端点；`ONTOLOGY_ARTIFACTS_BUCKET` 这类只需占位、不再取 STS | ① 对象存储 provider（含 content-type、大小上限、过期）；② **需要改契约或加一个明确的本地豁免**：现有 `GetProposalUploadUrls` 返回的是 S3 预签名语义，本地端点必须严格不改语义才能不破契约 | 1–2 |
| 5 | Bedrock 嵌入（`bedrock_embeddings.py`） | `InvokeModel` + `amazon.titan-embed-text-v2` 类模型，维度由 `BEDROCK_EMBED_DIMENSIONS=1024` 决定 | 8081 `bge-m3`（1024 维，已运行）；对齐「查询侧/文档侧同一模型、同一维度、同一归一化」 | ① provider 开关（`COA_PROVIDER_EMBEDDING=bedrock|http`，缺省拒绝启动）；② 维度与模型 ID 的启动期断言（不等即拒绝启动） | 1–2 |
| 6 | OpenSearch 向量（`stores/opensearch_vector.py` + `coa_common.opensearch`） | AOSS `opensearchserverless` 客户端、索引生命周期、`cosinesimil` 分数口径 | **pgvector**（5444 已装扩展），少一个组件、与 registry 同库；索引按命名空间一表 | ① 实现 `VectorStore` 协议：`ensure_index/upsert/query/delete_by_doc/probe`；② 余弦分数口径对齐（代码注释已承认 OpenSearch 侧 `_score` 与 [-1,1] 不一致，必须在实现里拉平）；③ 迁移/重建索引脚本 | 2–4 |

**合计约 15–26 人日**（与 `09` §8 的 ontology 相关估算同量级，不重复计入搬迁）。

落地顺序（依赖决定）：

1. **#5 + #6 + #1** 一起做：没有向量就没有 upload 成功路径，三者是一个最小闭环（约 6–11 人日）。
2. **#2**：induction job 还额外要 job 表 PG 化，且必须先把「数据源只能靠本地目录快照注入」的验收陷阱写进文档（已在 `11-复盘与规划.md`/台账留痕）。
3. **#3 + #4**：proposal 与产物是最后一块，且 #4 可能触发契约讨论（presign 语义），不要先动手。

**本部分不改任何代码。** 这份表就是后续派活的依据。
