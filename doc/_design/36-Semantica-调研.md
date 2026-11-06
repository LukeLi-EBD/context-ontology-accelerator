# 36-Semantica 调研（原「语义卡类项目候选清单」）

- 调研日期：2026-11-06（Asia/Shanghai）
- 调研方式：仅检索公开信息，未 clone、未运行、未改平台代码
- 结论先行：**高把握度命中 `semantica-agi/semantica`（官网 getsemantica.ai）**。它是一个自称 "semantic / context layer" 的开源图原生框架，名称发音与用户听到的 "C曼tic卡 CA" 高度接近；但官方文档中**不存在 "semantic card" 这一术语**，用户听到的 "card" 很可能是 "-ca" 尾音的误听。

---

## 一、命中项逐个核对

| 待核对目标 | 核对结果 | 依据 |
|---|---|---|
| GitHub 组织 `semantica-agi` | **存在**，主仓库即 `semantica` | https://api.github.com/orgs/semantica-agi/repos?per_page=100 |
| 仓库 `semantica-agi/semantica` | **命中** | https://github.com/semantica-agi/semantica |
| 官网 `getsemantica.ai` | **命中**（GitHub `homepage` 字段指向它） | https://api.github.com/repos/semantica-agi/semantica ；https://getsemantica.ai/ |
| 文档站 `docs.getsemantica.ai` | **命中** | https://docs.getsemantica.ai/ |
| PyPI `semantica` | **命中**，最新 0.7.0 | https://pypi.org/project/semantica/ |
| `semantica.io` | 未命中：域名正在出售 | https://semantica.io/ |
| `semantica.dev` | 未命中：仅 "Launching Soon" 占位页 | https://semantica.dev/ |
| `semantica.ai` | 未命中：维特根斯坦《逻辑哲学论》数字人文项目 | https://semantica.ai/ |
| GitHub `semantica-io` / `semantica-org` | 未命中：API 返回 404 | https://api.github.com/users/semantica-io ；https://api.github.com/users/semantica-org |
| GitHub `semantica`（旧组织） | 未命中：2013 年创建，0 个公开仓库，与本次目标无关 | https://api.github.com/users/semantica |

**命中判定：唯一主线命中为 `semantica-agi/semantica`。**

---

## 二、事实卡（官方仓库/官网/文档自述）

| 项目 | 事实 | 来源 |
|---|---|---|
| 名称 | Semantica（中文暂无官方译名；中文博客多直译为"语义层/上下文层"） | https://docs.getsemantica.ai/ |
| 仓库 | https://github.com/semantica-agi/semantica | GitHub API |
| 官网 | https://getsemantica.ai/ | GitHub `homepage` |
| 一句话定位（官方仓库描述） | "Graph-Native Infrastructure for Context and Accountable AI Systems" | https://api.github.com/repos/semantica-agi/semantica |
| 官网定位（官方自述） | "Governed Context and Semantic Layer with Decision Intelligence"；位于 LLM、向量库与 Agent 之下的语义/上下文层 | https://getsemantica.ai/ |
| 开源协议 | MIT | https://api.github.com/repos/semantica-agi/semantica |
| 创建时间 | 2025-06-25T10:41:00Z | https://api.github.com/repos/semantica-agi/semantica |
| 最近提交 | 2026-11-06T03:30:43Z（pushed_at） | https://api.github.com/repos/semantica-agi/semantica |
| Star 数 | **14,450**（2026-11-06 查询；fork 1,703） | https://api.github.com/repos/semantica-agi/semantica |
| 主语言 | Python | https://api.github.com/repos/semantica-agi/semantica |
| 最新版本 | PyPI 显示 **0.7.0**；FAQ 称 v0.7.0 于 2026-09 发布 | https://pypi.org/project/semantica/ ；https://docs.getsemantica.ai/faq/ |
| Python 版本 | 3.11–3.13（3.10 支持在 0.8.0 终止） | https://docs.getsemantica.ai/faq/ |
| 是否有 Web UI | **有**：`semantica.explorer`，FastAPI 浏览器工作台，含 Knowledge Explorer、Ontology Hub、SHACL Studio、决策/时间线/谱系等视图 | https://docs.getsemantica.ai/reference/explorer ；https://docs.getsemantica.ai/faq/ |
| 是否有 MCP/API | **有**：MCP server（stdio，15 个工具）、REST API、CLI、Python SDK | https://docs.getsemantica.ai/reference/mcp_server |
| 部署方式 | `pip install semantica`；可选 extras（`[all]`、`[explorer]`、`[neo4j]`、`[pinecone]` 等）；存储可换用 RDF 三元组库、LPG、向量库 | https://pypi.org/project/semantica/ ；https://docs.getsemantica.ai/ |
| 官方宣称的客户/场景 | BDT & MSD Partners、Ausgrid 等（官网自述，**未经独立验证**） | https://getsemantica.ai/ |
| 运营主体/公司实体 | **无法确认**（仓库属 `semantica-agi` 组织，未查到明确法人信息） | — |

> 版本口径备注：FAQ 的 Quick Answers 写"最新 v0.7.0（2026-09）"，同页正文又提到"0.8.0 终止 Python 3.10 支持"；PyPI 当日展示为 0.7.0。两处存在轻微不一致，按"0.7.0 已发布、0.8.x 可能已在准备"记录。

---

## 三、核心机制（官方文档可核实的 5 条）

1. **本体/词表治理（定义层）**
   - 用 OWL 表达类与属性、SKOS 表达受控词表、SHACL 表达约束；支持导入已有 OWL/RDF/Turtle。
   - 提供 5 阶段本体自动生成流水线（Semantic Network → YAML → Types → Hierarchy → TTL），LLM 生成为可选能力。
   - 提供 SHACL shapes 生成、图校验、违规报告、OWL/RDF 导出、命名空间管理。
   - 来源：https://docs.getsemantica.ai/reference/ontology

2. **确定性知识图谱构建（数据层）**
   - 流水线：Ingest → Parse → Normalize → Split → Extract（NER/关系/事件/三元组）→ 冲突检测 → 去重/实体解析 → 建图。
   - 冲突"被标记后再合并"，不做静默覆盖；事实带双时间（bi-temporal）与来源。
   - 来源：https://pypi.org/project/semantica/ （Architecture 段）

3. **可解释推理（推理层）**
   - 前向链、Rete 网络、Datalog、SPARQL、时间区间推理（Allen interval algebra），每条推导可输出 derivation path。
   - 注意：这是 Rete/Datalog/SPARQL 路线，**不是 OWL DL 的 ELK/HermiT 路线**。
   - 来源：https://docs.getsemantica.ai/guides/reasoning/

4. **决策智能 + 全链路溯源（审计层）**
   - `record_decision()` 把决策建成一等图节点，支持因果链（CAUSED / INFLUENCED / PRECEDENT_FOR）、先例检索、影响面分析、规则门禁。
   - 每个事实挂 W3C PROV-O 血统，可导出 RDF/JSON-LD/CSV，面向 GDPR、EU AI Act、HIPAA 等审计场景。
   - 来源：https://pypi.org/project/semantica/ ；https://getsemantica.ai/

5. **多形态交付与可替换存储**
   - 交付：Python SDK / REST / MCP（15 tools）/ CLI / Explorer Web UI。
   - 存储：RDF（嵌入式 Oxigraph、Blazegraph、Jena、RDF4J）+ LPG（Neo4j、FalkorDB、AGE、Neptune）+ 向量库（FAISS、Pinecone、Weaviate、Qdrant、Milvus、pgvector）。
   - 来源：https://pypi.org/project/semantica/ ；https://docs.getsemantica.ai/reference/explorer

---

## 四、与"本体 / 语义层 / 指标口径"的关系

| 维度 | Semantica 的位置 | 说明 |
|---|---|---|
| 本体 | **定义层**（强） | OWL/SKOS/SHACL 治理、本体生成、SHACL 校验、版本 diff（Ontology Hub 自述含 "version-controlled diffs"） |
| 语义层 | **上下文/语义层**（强） | 官方自称 "semantic / context layer"，面向 Agent 的结构化上下文与 GraphRAG |
| 指标口径 | **不覆盖**（弱/无） | 模块清单与术语表中没有 metric 定义、公式、聚合、窗口、维度连接等指标 DSL；示例里 "Metric" 仅作为图节点标签出现，不构成口径定义 |
| 缓存/加速层 | **不是** | 定位是确定性语义基础设施，不是查询缓存或指标加速层 |

### 与 dbt Semantic Layer / MetricFlow 的区别（回应用户前一问）

| 对比项 | dbt Semantic Layer / MetricFlow | Semantica |
|---|---|---|
| 核心对象 | semantic model、metric、measure、dimension、entity | 实体、关系、本体类/属性、决策、事实、来源 |
| 定义方式 | YAML 声明式指标定义，编译为 SQL | OWL/SKOS/SHACL + 图构建，无指标 DSL |
| 主要消费者 | BI 工具、仓库查询、指标一致性 | AI Agent、GraphRAG、合规审计 |
| 是否计算指标 | 是（生成 SQL / 聚合） | 否（不做指标聚合与窗口计算） |
| 关系 | 指标口径层 | 本体/上下文/溯源层，二者互补而非替代 |

> 结论：**Semantica 不能替代 dbt Semantic Layer / MetricFlow，也不能替代我们的 85 行指标口径表**；它更接近"本体治理 + Agent 上下文 + 审计溯源"的底座。

---

## 五、能否用在我们的平台（RDF+OWL+SHACL+SPARQL、Oxigraph、PG 口径表 85 行、MetricFlow 风格字段映射在建）

### 5.1 可接的层

| 层 | 可接性 | 说明 |
|---|---|---|
| 本体治理 | **可参考/可局部接入** | OWL/SHACL/SKOS 导入导出、SHACL 校验报告、Ontology Hub 的健康看板与版本 diff，和我们的 T-Box 治理方向同构 |
| 溯源与审计 | **可参考** | PROV-O 导出、决策节点/因果链/先例检索，可映射到我们的冲突裁决与审计事件链 |
| Agent 接口 | **可薄层接入** | 它的 MCP server 形态可作为我们只读工具面的参考；我们现有 REST 之上加 MCP facade 成本低 |
| 图存储 | **同族可对照** | 它支持嵌入式 Oxigraph，与我们当前主存储同族；但它是"可替换多后端"，我们是"单机单后端"，不应照搬多后端抽象 |
| 指标口径 | **不可接** | 没有 metric 定义/计算公式/聚合窗口语义，无法驱动 `metric_definition` 85 行，也无法承接 MetricFlow 风格字段映射 |
| 推理门禁 | **不可接** | Rete/Datalog/SPARQL 不能替代 ROBOT/ELK 的 OWL DL 一致性门禁，不能进我们的三道发布门禁 |

### 5.2 可借鉴（3 条）

1. **Ontology Hub 的信息架构**：类/属性可视化编辑 + SHACL Studio + 本体对齐 + 健康看板（覆盖率、一致性、违规）+ 版本 diff。我们治理台已有版本列表/提案/diff/发布回滚，可补"健康看板"这一块，且不引入前端框架。
2. **决策作为一等节点**：把 `keep A / keep both / merge` 裁决建模为 decision 节点，挂因果/先例/证据，并以 PROV-O 形式导出。我们已有审计链，这层是"视图与导出格式"的增量，不动现有语义。
3. **MCP 只读工具面**：参考其 15 个工具的组织方式，在我们现有 API 上包一层 MCP（查询本体版本、读指标定义卡、跑 SPARQL 只读查询），不改核心逻辑。

### 5.3 不可借鉴（3 条）

1. **不能拿它的推理器当门禁**：Rete/Datalog/SPARQL 不是 OWL DL，替代不了 ROBOT/ELK 的一致性检查，也无法满足我们"SHACL + 一致性 + breaking ack"的三道门禁。
2. **不能拿它做指标层**：没有 measure/aggregation/window/维度连接的定义与计算，无法承接 85 行口径表与 MetricFlow 风格字段映射；硬接只会造出第二套口径。
3. **不宜作为运行时依赖整体引入**：Python 3.11+、核心依赖约 22 个、自带 FastAPI/Explorer，与我们的"最小依赖 + 原生 HTML + 单 Web 外壳"约束重叠；且其 LPG/RDF 多后端抽象会与我们的单机 Oxigraph 路线冲突。

---

## 六、音近程度与匹配理由

| 维度 | 判断 |
|---|---|
| 读音 | "Semantica" ≈ /sɛˈmæntɪkə/，中文听感"塞-曼-提-卡"，与用户说的"C曼tic卡 CA（semantic + ca）"高度吻合 |
| 语义 | 用户说"语义层"，Semantica 官方自称 "semantic / context layer"，吻合 |
| 时间 | 2025-06 创建、2026 年持续高频提交（最近提交 2026-11-06）、v0.7.0 于 2026-09 发布，符合"最近发布/活跃" |
| 体量 | 14,450 stars、1,703 forks，符合"最近很火的开源项目" |
| 唯一不吻合点 | 官方文档/术语表中**没有 "semantic card" 概念**；若用户记忆里确有"卡片"实体，则不是 Semantica 的官方术语，可能是把词尾 "-ca" 听成了"卡" |
| 旁证 | 中文技术社区确有 2026 年的 Semantica 解读文章（媒体转述，如"开源版 Palantir"——该说法**未在官方 README 中核实**） |

**判定：最可能项 = Semantica（`semantica-agi/semantica`），把握度：高。**
备选：若用户坚持"项目里真的有 card 这个概念"，则见附录中的 Toss Topic / CodeSemanticCard、llmnav、SemNav，但它们都不是"最近发布的语义层开源项目"，把握度低。

---

## 七、附录 A：原始候选清单（降级为附录，宁少不滥）

| 名称 | URL | 创建 / 最近提交（查询日 2026-11-06） | Star | 一句话定位 | 与"语义卡"的关系 | 匹配度 |
|---|---|---|---|---|---|---|
| **Semantica** | https://github.com/semantica-agi/semantica | 2025-06-25 / 2026-11-06 | 14,450 | 面向 Agent 的图原生上下文与语义层，带决策溯源 | 名称音近；无 card 术语；属定义层+上下文层 | **高（主目标）** |
| **Apache Ossie (Incubating)**（前身 Open Semantic Interchange / OSI） | https://ossie.apache.org/ ；https://github.com/apache/ossie | 2025-11-18 / 2026-11-06；2026-06 进入 Apache 孵化 | 2,637 | 厂商中立的语义元数据交换规范：用声明式 YAML 定义 metrics、dimensions、joins | 是"指标语义层"标准，不是 card；与我们的指标口径最相关 | 中（概念相关，名称不音近） |
| **Toss Topic / CodeSemanticCard** | https://toss.tech/article/51745 | 文章 2026-07-30；无公开仓库 | 无法确认（非开源项目） | 韩国 Toss 内部"可信上下文"系统；用 CodeSemanticCard 描述代码语义 | 字面含 "Semantic Card"，但是内部系统/博客，不是开源语义层 | 低（字面像，形态不像） |
| **llmnav** | https://github.com/0disoft/llmnav | 2026-08-09 / 2026-11-01 | 1 | 给 LLM 编码 Agent 的确定性语义代码导航，源码旁嵌 "semantic card" | 字面含 semantic card，但属代码导航工具，非语义层 | 低 |
| **SemNav（论文）** | https://arxiv.org/html/2609.31176v1 | arXiv 编号 2609（2026-09，具体日期无法确认） | 无法确认（论文） | 用按需生成的 "Semantic Cards" 做仓库级 issue 定位 | 字面含 Semantic Cards，但是研究论文/方法，非发布项目 | 低 |
| ~~dbt Semantic Layer / MetricFlow / Cube~~ | — | — | — | 老牌语义层 | 按用户要求排除 | 排除 |

### 附录 B：仅名称撞车的项（不作为候选）

- `TsinghuaDatabaseGroup/SemanticCardinalityEstimation`：做的是"非结构化数据语义查询的基数估计"，与语义卡/语义层无关，仅名称含 Semantic + Cardinality。来源：GitHub 搜索 API `q="semantic card"`。

---

## 八、检索记录（关键词 / 渠道 / 失败通道）

### 8.1 渠道

| 渠道 | 用途 | 结果 |
|---|---|---|
| GitHub REST API | 仓库元数据（star/创建/提交/协议）、组织仓库列表、仓库搜索 | 主证据来源 |
| 官方站点/文档站 | 定位、机制、UI、MCP、部署 | 官方自述来源 |
| PyPI | 版本、README 镜像、依赖/架构 | 官方发布物来源 |
| WebSearch | 发现候选、中文社区旁证 | 发现层 |
| Apache Incubator / ossie.apache.org | 附录候选核对 | 官方来源 |
| arXiv | SemNav 论文核对 | 研究来源 |
| 中文技术社区（JOTO AI、个人博客"阿超"） | 旁证/媒体转述 | 仅作旁证，未作为事实主证据 |

### 8.2 关键词

`semantic card`、`semantic cards`、`semantic layer`、`semantic catalog`、`semantic model`、`ontology-driven semantic layer`、`knowledge card`、`AI semantic layer`、`Semantica`、`semantica-agi`、`getsemantica`、`语义层 开源 语义卡`、`Open Semantic Interchange`、`Apache Ossie`。

### 8.3 失败通道记录

| 现象 | 处理 |
|---|---|
| `WebFetch` 抓取 github.com 仓库 HTML 返回空 | 改用 GitHub REST API 与 PyPI README 镜像 |
| `raw.githubusercontent.com/.../README.md` 抓取返回空 | 改用 PyPI 项目页（README 镜像）核对 |
| 文档页内容过大被截断 | 仅引用已读到的明确段落，未补写未见内容 |
| `semantica.io` 域名出售、`semantica.dev` 占位页、`semantica.ai` 无关项目 | 已逐个记录为未命中 |
| `semantica-io` / `semantica-org` GitHub 404 | 已记录为未命中 |
| 官方文档无 "semantic card" 词条 | 如实写"官方无此术语"，不硬凑 |
| 中文博客称"开源版 Palantir" | 标为媒体转述，未在官方 README 核实 |

---

## 九、事实来源清单

1. https://api.github.com/repos/semantica-agi/semantica — 描述、协议、创建/提交时间、star/fork、语言
2. https://github.com/semantica-agi/semantica — 仓库主页
3. https://getsemantica.ai/ — 官网定位、平台导览、客户自述
4. https://docs.getsemantica.ai/ — 语义/上下文层定义、模块清单
5. https://docs.getsemantica.ai/faq/ — 协议、Python 版本、v0.7.0、Ontology Hub 能力
6. https://docs.getsemantica.ai/reference/ontology — OWL/SHACL/SKOS、本体生成、校验、导出
7. https://docs.getsemantica.ai/reference/explorer — Web UI、Ontology Hub、SHACL Studio
8. https://docs.getsemantica.ai/reference/mcp_server — MCP 15 tools
9. https://docs.getsemantica.ai/guides/reasoning/ — 前向链/Rete/Datalog/SPARQL
10. https://docs.getsemantica.ai/glossary/ — 术语表（无 "semantic card"）
11. https://pypi.org/project/semantica/ — 0.7.0、架构、存储与集成
12. https://ossie.apache.org/ — Ossie 定位与改名
13. https://github.com/apache/ossie + https://api.github.com/repos/apache/ossie — 附录候选事实
14. https://incubator.apache.org/projects/ossie — 进入孵化时间
15. https://github.com/0disoft/llmnav + https://api.github.com/repos/0disoft/llmnav — 附录候选事实
16. https://toss.tech/article/51745 — CodeSemanticCard 旁证
17. https://arxiv.org/html/2609.31176v1 — SemNav / Semantic Cards 论文
18. https://ai.jotoai.com/blog/news-e1d1d96e2d8bc82417 、https://vampireachao.github.io/2026/08/11/semantica/index.html — 中文社区旁证（媒体转述）

---

## 十、结论

- **命中**：`semantica-agi/semantica`（官网 https://getsemantica.ai/），把握度 **高**。
- **定性**：图原生的语义/上下文层，强在本体治理、确定性建图、可解释推理、PROV-O 溯源与决策节点；弱在指标口径（无 metric DSL、无指标计算）。
- **对我们**：可借鉴其本体治理 UI 信息架构、决策节点/PROV-O 审计模型、MCP 只读工具面；不可将其推理器当 OWL DL 门禁、不可当其替代指标层、不宜整体作为依赖引入。
- **关于"semantic card"**：官方无此术语；若用户坚持"项目里有 card"，则当前无"最近发布 + 音近 + 语义层"三项同时满足的项目，附录中的字面候选均不吻合。
