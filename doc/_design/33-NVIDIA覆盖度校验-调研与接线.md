# NVIDIA Auto Ontology 覆盖度校验：调研与接线

- 调研对象：`NVIDIA/auto-ontology`（`main`，API tree sha `2a24f5d34ef6b6e168a7f22d308504d3ab36a198`，2026-11-05 pushed）
- 调研时间：2026-11-06 13:06（Asia/Shanghai）
- 调研方式：**未 clone，仅读文件**。仓库 `git clone` 失败 1 次（SSL timeout），`raw.githubusercontent.com` 失败 1 次（连接被重置）；实际用通通道为 `api.github.com`（git tree + contents API，`Accept: application/vnd.github.raw`），并以 `cdn.jsdelivr.net` 复核 1 个文件成功（8338 bytes）。
- 证据口径：下文行号取自 `main` 分支原始文件；URL 一律指向 `github.com/NVIDIA/auto-ontology/blob/main/...`。
- 结论先行：**NVIDIA 有完整 Web UI（Next.js），但覆盖度没有专属可视化面板**；`check_answerable` 是"LLM 抽实体 + 向量检索 + 距离阈值 + 1/n 实体计数"的**连续覆盖率**，不是布尔判定；它覆盖的是**关系目录中的列/关系/SQL 表达式**，不覆盖指标定义与文档。

## 1. 事实清单

### F1 `check_answerable` 的输入、匹配逻辑、返回结构

**入口链路**：MCP 工具 `check_answerable` → `POST /api/question-entity-coverage` → LangGraph 实体覆盖管线。

| 要素 | 事实 | 出处 |
| --- | --- | --- |
| 工具映射 | `ToolSpec(method="POST", path="/api/question-entity-coverage", name="check_answerable")` | [mcp/auto_ontology_mcp/tools.py#L123-L133](https://github.com/NVIDIA/auto-ontology/blob/main/mcp/auto_ontology_mcp/tools.py#L123-L133) |
| HTTP 请求体 | `EntityCoverageRequest`：`question: string`（必填、minLength 1）、`max_distance: number`（默认 `0.75`，`exclusiveMinimum 0`，注释为"Maximum L2 vector distance for a candidate to count (lower score = closer match)"） | `mcp/auto_ontology_mcp/auto-ontology-api.json` → `components.schemas.EntityCoverageRequest`；路径 `/api/question-entity-coverage` |
| HTTP 返回体 | `EntityCoverageResult`：`coverage: number`（必填）、`candidates: array<EntityCoverageCandidate>`、`uncovered_entities: string[] \| null`（"only present when the flow was asked for it"） | 同上，`EntityCoverageResult`；候选字段为 `label / attribute / term / id`，见 `EntityCoverageCandidate` |
| 管线内部输入 | `EntityCoveragePayload`：`question`、`data_retriever`、可选 `semantic_retriever`、`connectors`、`acronyms`、`target_db`、`max_distance`、`return_uncovered_entities` | [auto_ontology/retrieval/entity_coverage/state.py#L20-L33](https://github.com/NVIDIA/auto-ontology/blob/main/auto_ontology/retrieval/entity_coverage/state.py#L20-L33) |

**匹配逻辑（三步，非纯规则）**：

1. **LLM 抽实体**：`question_extraction` 节点用结构化输出一次性产出 `sanitized_question` + `required_entity_name`（1–5 个短语，默认上限 5，可由 `CLARIFICATION_MAX_ENTITIES` 覆盖）。提示词明确要求实体"对应数据库表、列或关系"，并排除数字、日期、裸动词、聚合词。[question_extraction.py#L52-L164](https://github.com/NVIDIA/auto-ontology/blob/main/auto_ontology/retrieval/entity_coverage/agents/question_extraction.py#L52-L164)、[prompts.py#L90-L151](https://github.com/NVIDIA/auto-ontology/blob/main/auto_ontology/retrieval/entity_coverage/prompts.py#L90-L151)、[prompts.py#L14-L19](https://github.com/NVIDIA/auto-ontology/blob/main/auto_ontology/retrieval/entity_coverage/prompts.py#L14-L19)
   - 无 LLM 时直接抛 `RuntimeError("LLM client is not configured.")`；抽不出实体时退化为"整句当 1 个实体"。[main.py#L86-L101](https://github.com/NVIDIA/auto-ontology/blob/main/auto_ontology/retrieval/entity_coverage/main.py#L86-L101)、[question_extraction.py#L114-L119](https://github.com/NVIDIA/auto-ontology/blob/main/auto_ontology/retrieval/entity_coverage/agents/question_extraction.py#L114-L119)
2. **向量检索候选**：`retrieve_candidates` 复用 text-to-SQL 的候选检索，对语义目录做向量检索，候选包括 ColumnAttribute、SqlAttribute、CustomAnalysis（pgvector，返回带 `score`）。[graph.py#L26-L46](https://github.com/NVIDIA/auto-ontology/blob/main/auto_ontology/retrieval/entity_coverage/graph.py#L26-L46)、[coverage.py#L177-L200](https://github.com/NVIDIA/auto-ontology/blob/main/auto_ontology/retrieval/entity_coverage/agents/coverage.py#L177-L200)
3. **确定性评分**：先用 L2 距离阈值过滤（`score <= max_distance`，默认 0.75）；覆盖度 = 被 ColumnAttribute 命中覆盖的实体数 / 实体总数（`1/n`）；候选按 score 升序并回查名称/术语。[coverage.py#L24-L66](https://github.com/NVIDIA/auto-ontology/blob/main/auto_ontology/retrieval/entity_coverage/agents/coverage.py#L24-L66)、[coverage.py#L146-L160](https://github.com/NVIDIA/auto-ontology/blob/main/auto_ontology/retrieval/entity_coverage/agents/coverage.py#L146-L160)

**返回结构**：`{coverage: 0..1, candidates: [{label, attribute, term, id}], uncovered_entities?: string[]}`；覆盖度为 0 时会返回 `{coverage: 0.0, candidates: []}`，与"管线失败"无法区分。[main.py#L94-L101](https://github.com/NVIDIA/auto-ontology/blob/main/auto_ontology/retrieval/entity_coverage/main.py#L94-L101)、[models.py#L60-L73](https://github.com/NVIDIA/auto-ontology/blob/main/auto_ontology/retrieval/entity_coverage/models.py#L60-L73)

**如实说明**：
- 它**不返回布尔"能不能答"**，只给 0–1 的覆盖率；阈值判断由调用方（agent）自己下结论。
- HTTP 请求 schema 里**没有** `return_uncovered_entities`，所以走 MCP/HTTP 默认拿不到"缺哪些实体"；只有 `coverage` + 候选列表。README 里 agent 说的"no term covers ad spend"是模型对候选列表的解读，不是接口字段。[README.md#L174-L183](https://github.com/NVIDIA/auto-ontology/blob/main/README.md#L174-L183)
- 覆盖度只由 **ColumnAttribute 命中**计算，SqlAttribute / CustomAnalysis 只进候选、不进分子。[coverage.py#L50-L66](https://github.com/NVIDIA/auto-ontology/blob/main/auto_ontology/retrieval/entity_coverage/agents/coverage.py#L50-L66)

### F2 9 个只读 MCP 工具

`tools.py` 的 curated 列表 7 个 + 手写的 `ask_question`、`check_readiness` 共 **9 个**；服务端明确声明"Every tool reads"。[tools.py#L60-L134](https://github.com/NVIDIA/auto-ontology/blob/main/mcp/auto_ontology_mcp/tools.py#L60-L134)、[server.py#L48-L84](https://github.com/NVIDIA/auto-ontology/blob/main/mcp/auto_ontology_mcp/server.py#L48-L84)

| # | 工具名 | 作用 | 出处 |
| --- | --- | --- | --- |
| 1 | `search_terms` | 搜索业务术语表 | tools.py L61-L72 |
| 2 | `get_term` | 取单个术语（描述、同义词、相关术语） | tools.py L74-L83 |
| 3 | `get_term_columns` | 术语映射到的物理列 | tools.py L84-L92 |
| 4 | `get_term_sql_attributes` | 术语下已评审的 SQL 表达式 | tools.py L93-L103 |
| 5 | `get_sql_attribute` | 单个 SQL 表达式的定义与用途 | tools.py L104-L112 |
| 6 | `describe_table` | 一张表的列 + 相关术语 + SQL 属性 | tools.py L113-L122 |
| 7 | `check_answerable` | 覆盖度预检（本调研主角） | tools.py L123-L133 |
| 8 | `ask_question` | 跑完整 text-to-SQL，返回答案/SQL/行 | [chat.py#L149-L171](https://github.com/NVIDIA/auto-ontology/blob/main/mcp/auto_ontology_mcp/chat.py#L149-L171) |
| 9 | `check_readiness` | 部署级就绪：语义层 + 可执行 SQL + 数据，输出 `ready/blockers/unverified` | [readiness.py#L51-L101](https://github.com/NVIDIA/auto-ontology/blob/main/mcp/auto_ontology_mcp/readiness.py#L51-L101) |

工具清单口径在文档中同样写为 9 个（Readiness 1 + Terms 6 + Answerability 1 + Questions 1）。[docs/mcp.md#L127-L137](https://github.com/NVIDIA/auto-ontology/blob/main/docs/mcp.md#L127-L137)、[README.md#L284-L289](https://github.com/NVIDIA/auto-ontology/blob/main/README.md#L284-L289)

### F3 有没有 UI

**有，且是完整的产品级 Web UI，不是 demo。**

| 证据 | 事实 | 出处 |
| --- | --- | --- |
| 技术栈 | Next.js 16（React 19、TypeScript、Tailwind CSS 4）、Better Auth、Prisma；端口 3000，承担"Web UI, authentication, API gateway" | [README.md#L45-L53](https://github.com/NVIDIA/auto-ontology/blob/main/README.md#L45-L53) |
| 页面 | `chat`、`analysis`、`analytics`、`data`、`discovery`、`exploration`、`terms`、`settings`（agent-settings/connections/pii/rules/import-export）、`login`、`account/api-tokens`、`admin`、`invite`、`oauth` | 仓库 tree：[frontend/app/...](https://github.com/NVIDIA/auto-ontology/tree/main/frontend/app)；入口文件见 `frontend/app/*/page.tsx` |
| 组件 | `chatPage`（ChatView/MessageList/ThinkingMessage/…）、`termsPage`、`dataPage`、`discoveryPage`、`explorationPage`（含图可视化 GraphCanvas）、`ResultChart`、`settings` | [frontend/components](https://github.com/NVIDIA/auto-ontology/tree/main/frontend/components) |

**覆盖度在 UI 中的实际形态**：**没有专属页面或面板**。前端只有一条代理路由 `POST /api/question-entity-coverage`，鉴权挂在 `chat: ['use']`，正文注释写"Same retrieval capability as chat"，即它只是把请求转发给后端。[frontend/app/api/question-entity-coverage/route.ts#L8-L12](https://github.com/NVIDIA/auto-ontology/blob/main/frontend/app/api/question-entity-coverage/route.ts#L8-L12)

已逐个检索 chat 相关前端文件（`useChat.ts`、`ChatView.tsx`、`ThinkingMessage.tsx`、`MessageBubble.tsx`、`answerMessages.ts`），**`coverage` / `answerable` 命中数为 0**；README 中的覆盖度示例发生在"agent 通过 MCP 调用"的对话里，不是 Web UI 面板。[README.md#L171-L183](https://github.com/NVIDIA/auto-ontology/blob/main/README.md#L171-L183)

**结论**：有 UI；UI 覆盖 chat、分析、数据目录、术语、图谱探索、设置与治理类页面；**覆盖度只以 MCP 工具 + API 的形式存在，没有可视化面板**。未 clone，无法对全部前端文件做全量 grep，故只声明"在已检索范围内未找到证据"，不宣称绝对不存在。

### F4 "覆盖度"的概念边界

| 层 | 是否覆盖 | 证据 |
| --- | --- | --- |
| 关系表字段 | **是**（核心） | 实体定义为"tables, columns, or relationships"（[prompts.py#L92-L94](https://github.com/NVIDIA/auto-ontology/blob/main/auto_ontology/retrieval/entity_coverage/prompts.py#L92-L94)）；覆盖度由 ColumnAttribute 命中计算（coverage.py L50-L66） |
| SQL 表达式 | **部分**：进候选、不进覆盖度分子 | SqlAttribute 只在 `candidates` 里（coverage.py L196-L199） |
| 自定义分析 | **部分**：同上 | CustomAnalysis 只在候选里（coverage.py L198-L199） |
| 业务术语 | **部分**：Glossary 只用于在抽取阶段消解缩写/行话，不作为被覆盖对象计数 | [prompts.py#L99-L105](https://github.com/NVIDIA/auto-ontology/blob/main/auto_ontology/retrieval/entity_coverage/prompts.py#L99-L105)、[main.py#L53-L54](https://github.com/NVIDIA/auto-ontology/blob/main/auto_ontology/retrieval/entity_coverage/main.py#L53-L54) |
| 指标定义 | **否**（未找到证据）：仓库有 SQL attribute / custom analysis，但没有"指标定义（窗口、可发布、版本、变体）"这一层参与覆盖度 | 目录文件树与 OpenAPI 中均无 metric-definition 相关模型 |
| 文档 | **否**（本接口不覆盖）。另一条 `clarify` 路径有 external-KB coverage，但那是"LLM 对每个术语判 YES/NO + 回查真实 KB 条目"，不是文档检索覆盖率 | [kb_coverage.py#L5-L11](https://github.com/NVIDIA/auto-ontology/blob/main/auto_ontology/retrieval/interactive/kb_coverage.py#L5-L11)、[kb_coverage.py#L106-L322](https://github.com/NVIDIA/auto-ontology/blob/main/auto_ontology/retrieval/interactive/kb_coverage.py#L106-L322) |
| 部署可答性 | **单独一层**：`check_readiness` 判"语义层是否编译 + 能否执行 SQL + 有没有库"，与"问句覆盖"分开 | [readiness.py#L51-L101](https://github.com/NVIDIA/auto-ontology/blob/main/mcp/auto_ontology_mcp/readiness.py#L51-L101) |

一句话：**它把"覆盖度"定义为"问句里的实体能否在关系目录里找到对应的列属性"，不覆盖指标口径、不覆盖文档。**

## 2. 与我们的 `check_answerable` 逐项对比

我们的事实来源：`coa/platform/src/platform_core/answerable.py`、`api.py`（`GET/POST /answerable`）、`config.py`（默认阈值 0.6）、`tests/test_q4_answerable.py`。

| 维度 | NVIDIA `check_answerable` | 我们 `AnswerabilityService.check` | 差距判断 |
| --- | --- | --- | --- |
| 输入 | 自然语言 `question` + `max_distance`（默认 0.75） | 自然语言 `query`（≤2000 字符）+ `ontologyVersion` + `minCoverage`（默认 0.6） | 基本同构；我们多版本参数 |
| 匹配 | LLM 抽 1–5 个实体 → 向量检索（L2）→ 距离过滤 → 1/n 实体覆盖 | 纯确定性词法：SKOS prefLabel/altLabel + rdfs:label 做最长子串匹配；按"内容字符"算覆盖 | **算法路线不同**：我们无 LLM/向量；他们无字符口径 |
| 返回 | `coverage` + `candidates[]` + 可选 `uncovered_entities` | `answerable` 布尔 + `coverage` + `coverageChars` + `matchedTerms` + `missing[]`（含 `nearbyTerms`）+ `reasonCode` + `hint` | 我们"缺什么"表达更完整；他们候选列表更完整 |
| 缺项表达 | 默认**不给**缺项（HTTP schema 无开关）；候选即线索 | 默认给 `missing` 片段 + 最相似术语建议 | 我们更强 |
| 覆盖层 | 关系目录：列属性（计入）/SQL 属性/自定义分析（仅候选）+ Glossary 消歧 | 仅 T-Box 标签（类/属性/术语） | **我们缺指标层、事实层、字段层** |
| 确定性 | 抽取依赖 LLM；评分为确定性 | 全链路确定性、无 LLM | 我们更强、可回归 |
| 失败降级 | LLM 未配置直接抛错；无结果时 `{coverage:0,candidates:[]}`，与"未覆盖"不可分 | 图/版本不可用给明确 `E_ANSWER_*`；空内容给 `E_ANSWER_QUERY_EMPTY` | 我们的错误码更清晰 |
| 规模上限 | 实体上限 5；问题长度未限 | 2000 字符；无实体数概念 | 各有取舍 |
| UI 暴露 | 无面板，仅 API+MCP | 无面板（`browse.html` 五 tab 无 answerable） | 双方都缺；我们更容易补 |

**可比项计数：8 项**（输入、匹配、返回、缺项、覆盖层、确定性、降级、UI）。

## 3. 我们的缺口（本轮不改代码）

| ID | 缺口 | 具体表现 | 改法方向 |
| --- | --- | --- | --- |
| G1 | 只判 T-Box 标签，**不判指标定义** | 问"缴费率/分期履约率"时，本体里没有该词，`answerable=false`，但 `metric_definition` 85 行里有定义 | 给 `answerable.py` 增加 metric 词表（`metric_id/name/variant_of`） |
| G2 | **不判事实层可算性** | "有定义、无数据/窗口不足"会被误判为可答；我们没有 NVIDIA 那种 `check_readiness` 分层 | 增加 `facts` 层：查 `metric_observation` 窗口与 `fact_function` 绑定 |
| G3 | 覆盖是**字符级**，不是实体级 | 长问句里零散命中会虚高；无法回答"缺 2/4 个概念" | 保留字符口径作为兼容，另加 `entities` 口径 |
| G4 | **无候选列表** | 只有 `missing` + `nearbyTerms`，不能让用户点选确认 | 返回按相似度排序的 `candidates`（指标/术语/字段） |
| G5 | **指标别名/变体未接入** | 术语层 18 别名只覆盖本体锚点类，指标名/变体不参与匹配 | 建指标别名索引（读 `metric_definition`，不新增表） |
| G6 | **无 UI 暴露** | `browse.html` 五 tab（口径/本体/术语/triples/sparql）没有可答性入口 | 加第六个只读 tab 或口径 tab 内嵌面板 |

**缺口数：6**（G1–G6）。

## 4. 可直接接线的落点清单

> 约束：本轮只出方案，不改代码。下列每条都按 ≤30 分钟可验证切片设计，验收命令以现有 `unittest` / `acceptance.ps1` 为准。

### P0（先做，收益明确、改动小）

**P0-1 分层覆盖度（`layers`）**
- 改：`src/platform_core/answerable.py`（`check()` 增加 `layers` 字段；新增 `_metric_terms()`、`_fact_terms()` 两个私有方法）
- 加字段：`layers: {ontology: {covered, missing}, terms: {...}, metrics: {...}, facts: {...}}`；保留现有顶层字段不变（向后兼容）
- 加参数：`GET/POST /answerable` 增加 `includeLayers`（默认 `true`；为 `false` 时返回体与现状逐字节一致）
- 验收：`tests/test_q4_answerable_layers.py` 断言 ①现有 3 条用例字段不变；②`layers.ontology.coverage` 与顶层 `coverage` 一致；③只命中指标的问句 `layers.metrics.covered=true`；④不存在的指标 `covered=false` 且 `missing` 带名字

**P0-2 指标词表接入（只读）**
- 改：`src/platform_core/answerable.py`；数据读取复用 `src/platform_core/metrics.py`（`platform.metric_definition`），不新增迁移、不新增依赖
- 加逻辑：指标匹配词 = `metric_id` + `name` + `variant_of`（大小写/去空白归一），命中即计入 `metrics.covered`
- 验收：单测断言"缴费率"命中 `FIN-INS-021`、"不存在的指标名" `covered=false`；连跑两次结果一致（确定性）

**P0-3 事实层可算性（降级优先）**
- 改：`src/platform_core/answerable.py`，复用 `src/platform_core/metric_facts.py` 的窗口/绑定查询
- 加语义：`facts.status ∈ {covered, window_insufficient, no_observation, unavailable}`；`unavailable`（表缺失/查询失败）只置 `degraded=true`，**不返回 500**
- 加错误码：`E_ANSWER_FACT_WINDOW`（窗口不足）、`E_ANSWER_FACT_EMPTY`（无观察值）；`unavailable` 不进 `reasonCode`，进 `reasons[]`
- 验收：单测覆盖 4 种状态；缺表时 HTTP 仍 200 且 `degraded=true`；现有 acceptance 全绿

**P0-4 UI 只读入口**
- 改：`web/browse.html`、`web/browse.js`、`web/browse.css`
- 加：第六个 tab「可答性」——输入框 + 请求 `GET /answerable?includeLayers=true`，渲染四层徽章（已覆盖/缺什么），空态显示"请输入问题"，**不触发任何推理或重建**
- 验收：`browse.html` 直接打开可交互；网络面板仅 1 个 GET；空数据有空态、无假数据；写操作 0 次

### P1（补齐体验与回归）

**P1-1 候选列表**
- 改：`src/platform_core/answerable.py`
- 加字段：`candidates: [{layer, id, name, similarity, matchedBy}]`，每层 top 3；相似度沿用现有 `SequenceMatcher`，不引入向量阈值
- 验收：近似但未命中的问句能给出候选；候选按相似度降序；结果可复现

**P1-2 回归基线**
- 改：`tests/test_q4_answerable.py`（只加用例，不改旧断言）
- 加：用现有 24 条术语层查询集跑 `layers.metrics` / `layers.facts` 的命中率快照，断言不低于本轮基线；快照写入测试常量并注明日期
- 验收：全量 `unittest` 通过；`acceptance.ps1` `passed=43 failed=0`

### P2（可选，不做也行）

**P2-1 治理台/浏览页联动**
- 改：`web/browse.html`（仅在可答性 tab 内加"查看最接近的指标定义"深链到口径 tab），不改 `governance.html`
- 验收：点击跳转带 `metricId`，口径 tab 正确过滤

**P2-2 向量匹配（不建议现在做）**
- 若未来要做，复用现有 chunk embedding 会对齐到"文档块"而非"目录实体"，语义错位；需先建指标/字段级向量，成本高。**本轮不排期**。

## 5. 明确"不值得学"的点

1. **不要把"1/n 实体覆盖 + 0.75 L2 阈值"搬进来**。0.75 是它自己 pgvector 的 L2 距离经验值，和我们的 BGE-M3/余弦口径不可换算；阈值会变成不可解释的魔数。
2. **不要为了覆盖度引入 LLM 抽实体**。我们现有 `check_answerable` 是全确定性、可回归的；改成 LLM 会引入抖动、成本和"抽错实体导致误判"的新失败模式。
3. **不要搬 87 操作的 allow-list / FastMCP 装配**。我们没有 MCP 面，也没有"工具选择退化"的问题；照搬只会增加维护面。
4. **不要搬 Next.js 前端**。我们是原生 HTML + 少量 JS 的只读界面，覆盖度只需一个只读面板。
5. **不要学它"默认不返回缺什么"**。我们现有的 `missing + nearbyTerms + hint` 是更好的契约，应保留。
6. **不要把它当"指标覆盖"**。它的 SQL attribute 是表达式级候选，不是带窗口/可发布/变体的指标定义；把两者等同会掩盖 G1/G2。

## 6. 未确认项（如实登记）

| 项 | 状态 |
| --- | --- |
| Web UI 是否存在未以 `coverage` 命名的覆盖度组件 | **无法确认**：未 clone，无法全量 grep；已检索的 chat 相关 5 个文件命中 0 |
| `uncovered_entities` 是否被某个后端路由显式打开 | **未找到证据**：HTTP schema 未暴露该开关；`EntityCoveragePayload` 有该字段 |
| NVIDIA 是否另有指标/文档覆盖层 | **未找到证据**：文件树与 OpenAPI 中无对应模型 |
| 前端是否直接调用 `/api/question-entity-coverage` | **未找到证据**：除代理路由本身外，已检索前端文件无调用 |

## 7. 变更记录

- 2026-11-06 13:06：首版。未 clone；证据来自 `api.github.com` + `cdn.jsdelivr.net` 复核。事实 4 组、工具 9 个、可比项 8 项、缺口 6 项、接线 7 条（P0×4 / P1×2 / P2×1）。
