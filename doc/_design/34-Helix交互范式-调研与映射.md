# 34 · Helix Foundry 交互范式：调研与映射

> 文档编号：34 · 日期：2026-11-06 · 性质：调研结论文档（**不改平台代码**）· 关联：`22-同类项目对比-COA-NVIDIA-Helix.md`
> 一句话结论：**Helix 真正值得抄的不是"图数据库"，而是"值级溯源 + 可核验问答"的产品化闭环；交互可抄，运行时不可换。**

---

## 0. 结论先行

1. **核心优势**：不可变本体版本 + `current` 指针、每个值可回溯到行/引文、Explorer 的邻域浏览、Analyst 的"每一步查询留证 + 每个结论带引用 + 答不了就说缺口"。
2. **Explorer 不是"图数据库管理台"**：它是"标签栏 + 画布 + 搜索 + 点选展开邻域 + 右侧详情"的只读浏览界面，外加按实体页看记录/文档。
3. **Analyst 不是报表/指标探索**：它是**绑定某个 load 的问答线程**——把问题变成受限的类型化图查询（必要时裸查询），每步执行结果落成 evidence，答案逐句挂引用；答不了返回 `cannot_answer` + 原因 + 缺口，不硬编。
4. **可直接借鉴的低成本项**：步骤时间线、引用 chip、`/answerable` 前置提示、triples 溯源列、实体详情/以实体提问。
5. **不该做**：力导向画布、多跳路径探索、双 load 并排图谱、向 LLM 暴露裸查询工具。
6. **我们现状的关键事实**（已核对代码）：`web/browse.html` 实际只有 **3 个 tab**（本体/口径卡/术语别名）；`/browse/triples` 与 `/browse/sparql` 后端已就绪但**前端无入口**（与"五 tab"的既有认知不符）。

---

## 1. 调研方法与通道

- **未 clone**。全部结论来自远端只读读取；未在本地磁盘保留仓库副本。
- 用通的通道（逐条实测）：
  - `https://api.github.com/repos/HelixDB/helix-foundry/...`（仓库元数据、contents、git trees）→ 200；
  - `https://raw.githubusercontent.com/HelixDB/helix-foundry/main/...` → 200；
  - `https://cdn.jsdelivr.net/gh/HelixDB/helix-foundry@main/...` → 200（大文件备用通道）。
  - `https://github.com/...` 的 HTML 页面抓取返回空内容/被重置，未作为证据来源。
- 取样版本：`main` 树 `c7de40515f56a491d1b46af0bb1efa890f106700`；仓库 `pushed_at=2026-10-31T23:32:39Z`、`updated_at=2026-11-01`。
- 证据强度标注：**仓库文件证实** / **仅二手转述** / **无法确认**。截图只确认资产存在（`.github/assets/explorer.png`、`.github/assets/analyst.png`），未逐像素核对。

---

## 2. Helix 优势清单（12 条）

| # | 优势 | 具体内容 | 证据（文件路径 / URL） | 强度 |
|---|---|---|---|---|
| H1 | 本体版本化 + 指针 | 生成草稿 → 人工审阅/编辑 → 设为 current → load；版本不可变，load 绑定版本 | `README.md`（"review it, edit it and make a version current"）；`src/web/areas/ontology/paths.ts`（`versions`/`loads`/`generations`） | 仓库文件证实 |
| H2 | 属性图数据模型（LPG） | 节点/边带 label、属性、数字 `$id`；按 label 位图读、按属性过滤；**不是 RDF** | `README.md`（"one connected graph"）；`src/web/areas/explore/explorer/lib/queries.ts`（`$label == "User"`、`$id`、numeric db id）；`lib/types.ts` | 仓库文件证实 |
| H3 | 单机零配置部署 | `git clone` + `docker compose up -d --wait` 三行；默认 **3000**（站点）、**8333**（存储）；无账号、单 owner | `README.md` §Run it on your computer；`local/README.md`（站点/端口/数据卷） | 仓库文件证实 |
| H4 | 连接器与增量同步 | PG/MySQL/S3/Stripe/PostHog/WorkOS/GitHub/Linear/Granola/Cal.com/Slack/Notion/Google Workspace + 文档（md/txt/PDF）+ 表格文件（CSV/TSV/JSON/JSONL/Parquet）；PG/MySQL 变更捕获，其余增量读 | `README.md` §What you get | 仓库文件证实 |
| H5 | 值级溯源 + 人工复核 | 每个值保留来自"表行"或"文档引文"；文档间冲突进人工 review | `README.md`（"keep where every value came from…wait for your review"）；`src/web/areas/reviews` | 仓库文件证实 |
| H6 | Explorer（图 + 记录 + 实体页 + 双 load 对比） | 见 §3 逐项 | `README.md` 截图 alt 文本；`explorer-page.tsx`；`paths.ts` | 仓库文件证实 |
| H7 | Analyst（带引用的问答） | 见 §4 逐项 | `README.md` 截图 alt 文本；`contract/ontology_agent/ask_result.json` | 仓库文件证实 |
| H8 | 确定性检索（无 embedding） | Explorer 搜索 = 已加载节点匹配 + `$id` 精确 + 全文索引 + `contains` 扫描；问答应答 = 类型化查询/图遍历 + 读时应用规则，**未找到向量检索证据** | `ExplorerSearch.tsx` 注释；`ask_request.json`（`focus` 作为首个 handle `n1`）；`read_request.json`（读时应用规则、预算） | 仓库文件证实（"无向量"= 未找到证据） |
| H9 | 托管多租户 / 本地单用户 | 托管：workspace + 成员/角色 + grant + `visibility` 部分可见；本地：仅 `127.0.0.1`、无登录 | `backend/README.md` §Hosted Helix；`README.md` §Security model；`backend/access/*` | 仓库文件证实 |
| H10 | 治理面 | 版本 `current`、suggestions/audits、rule-breaks（约束破坏）页面 | `paths.ts`（`suggestions`/`loadRuleBreaks`）；`README.md`（rules） | 仓库文件证实 |
| H11 | 浏览器永不写库 | Explorer 侧栏固定 "Read only" 提示；查询走后端只读代理 | `ExplorerBar.tsx`（`ReadOnly` 组件注释 "Foundry never writes from the browser"）；`ask_request.json`（read-only proxy） | 仓库文件证实 |
| H12 | 可拒答 | `answered` / `cannot_answer`；拒答给 `reason` + `gap` + `gap kind` + 未覆盖部分 | `ask_result.json`；`ask.tsx`（`CANNOT_ANSWER_LABELS`/`PART_UNCOVERED_LABEL`） | 仓库文件证实 |

**相对通用知识库/语义栈的优势要点**

- 交付完整度：连接器 → 同步 → 起草本体 → 版本审阅 → load → 浏览 → 问答，一条产品链路，不需要自己拼。
- 可信度设计：值级 provenance、evidence id、逐句 citation、拒答缺口，比"LLM 直接答"可审计。
- 交互密度：Explorer 的"标签 → 搜索 → 展开 → 详情"路径短，分析师无需写查询即可看到邻域。
- 代价：LPG + MySQL + SeaweedFS 三套存储；无 RDF/SPARQL/SHACL/OWL 推理；仓库内未找到向量检索接线证据。

---

## 3. Explorer 真实交互（10 项）

使用者：本地安装为"一个人"；托管为 workspace 内具备读权限的成员（owner/member/grantee）。仓库未写死岗位画像，**"数据工程师/分析师"是按 README 工作流的合理推断**，非仓库原文。

| # | 交互 | 谁用 / 触发 | 点什么 | 看到什么 | 证据 |
|---|---|---|---|---|---|
| E1 | 标签栏（Label rail） | 进入 Explorer 即见 | 点 node/edge label 行；眼睛图标隐藏/显示；"Load more" 翻页 | 每类节点/边标签 + 计数 + 颜色；本 load 计数与"至少 ≥"标记；Foundry 内部标签默认折叠 | `LabelRail.tsx`（`LabelCount`、`hiddenLabels`、`isLabelExhausted`）；`ExplorerBar.tsx`（`atLeast` 统计） |
| E2 | 画布初视图 | 打开 `/explore/:ontologyId` | 拖拽/缩放/fit/relayout/reset | 按版本布局预置种子节点的图谱画布；节点按 label 着色 | `explorer-page.tsx`（canvas/labels/inspector）；`lib/seeding.ts` |
| E3 | 搜索框 | 键盘输入 | 输入即匹配画布已加载节点；回车/停顿后发数据库搜索 | 下拉命中：已加载节点、`$id` 精确命中、全文索引命中、`contains` 扫描命中（仅 Enter，成本随标签规模增长） | `ExplorerSearch.tsx` 注释与 `SearchOptions`；**无语义/向量搜索** |
| E4 | 节点/边详情（Inspector） | 点击节点或边 | 展开/收起面板、复制、切 caption 属性 | 属性键值（附索引徽标）、按关系标签分组的邻接列表、in/out 度、值是否"重"（heavy） | `Inspector.tsx`（`PropertyList`、`relationshipGroups`、`degreeText`） |
| E5 | 展开邻域（Expand） | 右键节点或详情动作 | 选"按关系展开"；大 hub 先探测度 | 该节点邻域加入画布；**每方向最多 50 条边**（`neighborLimit`）；超过 `degreeThreshold` 的 hub 走受控展开 | `ContextMenu.tsx`（`onExpand`/`menuRelationships`）；`lib/queries.ts`（`neighborLimit: 50`、`degreeThreshold`） |
| E6 | 画布操作 | 右键菜单/快捷键 | Focus、Hide、Pin/Unpin、Undo、Fit、Relayout、Reset view、Export PNG | 视图状态变化；可撤销 | `ContextMenu.tsx`（Pin/PinOff/Undo2/Scan/SquareArrowOutUpRight/ImageDown） |
| E7 | 按标签浏览 | 点标签栏行 | 加载该标签一页节点（50/页） | 该标签的一页节点加入画布；可继续翻页 | `LabelRail.tsx`（`onLoad`）；`Inspector.tsx` `subject: {kind:"label"}` |
| E8 | 实体页 | 从画布/详情点跳转动作（`onOpenPage`） | 打开 `/explore/:id/entities/:entityId` | 该实体的记录、关联文档、评审（records/detail） | `paths.ts`（`entity`）；`src/web/areas/records/detail.tsx` |
| E9 | 双 load 对比 | URL `?compare=<loadId>` | 两侧画布/标签联动；按 diff 聚焦 | 两个 load 并排，diff 面板列出新增/删除/变更 | `explorer-page.tsx`（`DiffPanel`/`compare-panel.tsx`）；`compare.ts`（`KeyItem`） |
| E10 | 溯源与只读 | 常驻 | 看节点徽标；复制 id/JSON/链接；看 "Read only" | 该节点来自哪个 load（徽标）、是否被后续 load 删除（状态标记，样式未逐像素核对）、`?node=<dbId>` 可分享 | `explorer-page.tsx`（load badge）；`ExplorerBar.tsx` `ReadOnly`；`model.ts`（`entityRow`） |

**Explorer 的关键限制（同样是事实）**

- 搜索是**词法**的：ID、全文索引、`contains`；没有 embedding/语义召回。
- 邻域展开是**有界**的（50/方向），不是无限 BFS；没有"两点最短路径"交互的证据。
- 没有内联编辑/写入；写操作不在 Explorer。

---

## 4. Analyst 真实交互（10 项）

使用者：同一个 workspace 的成员；本地安装是 owner 本人。问题按 workspace 限额限流（`AskFoundryQuestion` 注释：近一小时问题数、当月已结算量与单问 cap；grantee 另有自身限额）。

| # | 交互 | 触发 | 点什么 | 看到什么 | 证据 |
|---|---|---|---|---|---|
| A1 | 问答入口与线程 | 打开 `/ask/:ontologyId` | 选已有线程 / 新建线程 | 线程列表；空线程给出建议问题（来自草稿的 competency questions） | `ask.tsx`（`askSuggestions`、`threadsOf`）；`paths.ts`（`ask`） |
| A2 | 提问 | 输入框 | 输入问题（≤4000 字符）、可选 focus 实体、可带历史 | 发送后进入流式/轮询 | `api/questions.go`（`maxQuestionChars=4000`）；`ask_request.json`（`focus`/`history`） |
| A3 | 异步排队 | 发送即入队 | 无需操作 | 问题由 `foundry-ask-worker` 执行；UI 按页轮询事件（200/页） | `api/questions.go`（"queues a question … the foundry-ask-worker answers it"）；`ask_event.json` |
| A4 | 步骤时间线 | 流式事件 | 展开某一步 | `started`（模型/provider）→ `tool_call`（工具名 + 输入）→ `tool_result`（一行摘要 + evidence id）→ `finished` | `ask_event.json`；`ask-model.ts`（"folded into steps"） |
| A5 | 查询可视化 | 步骤内 | 展开 Input/Output | 类型化查询按"可读路径"渲染（位置/步骤/过滤/聚合）；输出表格或图表 | `ask-model.ts`（"a typed query as a readable path"）；`ask-chart.tsx`；`read_result.json`（`Aggregate`/`group_by`） |
| A6 | 逐句引用 | 答案出现后 | 点数字引用 chip | 跳到实体、事实/派生事实、表行、文档片段（含 section/字节 span）、rule-break，或高亮对应步骤 | `ask_result.json`（`Citation`/`CitationTarget`）；`ask-model.ts`（`citationHref`）；`ask.tsx` |
| A7 | 图表 | 答案/步骤 | 看图 | 由查询输出生成的 visual（`VisualKind`；具体图表类型未逐一核对） | `ask_result.json`（`VisualKind`）；`ontology/ask-chart.tsx` |
| A8 | 拒答与缺口 | 模型判定答不了 | 读解释 | `cannot_answer`：`reason` + `gap`（缺什么）+ `kind`（缺口类型）+ 未覆盖部分标签 | `ask_result.json`（`GapKind`/`gap`）；`ask.tsx`（`PART_UNCOVERED_LABEL`） |
| A9 | 证据链 | 每步 | 无需操作 | `tool_result` 记 `evidence_id`（如 `e17`），答案里的每个数字都指到一个 evidence | `ask_event.json`（`EvidenceId` 描述"every number the user sees cites one"） |
| A10 | 预算/模型/只读 | 常驻 | 看 badge/用量 | 模型与 provider、用量、问题预算；模型与文档文本只当纯文本（不当 HTML/链接） | `ask_result.json`（`usage`）；`ask_request.json`（`limits`）；`ask-model.ts` 文件头注释 |

**回答"Analyst 是问答还是报表/指标探索"**

- **是问答**，不是 BI/指标平台：没有指标定义、口径、报表保存、定时刷新这些对象；只有"问题 → 查询 → 证据 → 答案/图表"。
- 它把"问一句"变成可核验结果的三段：**① 类型化图查询（可含聚合）** → **② 结果落 evidence（id）** → **③ 答案块逐句 citation**。答不了就给 gap，不补故事。

---

## 5. 前端技术栈与页面结构

- 站点：**Next.js 16**（站点外壳），Foundry UI 是**客户端挂载的 SPA**（`react-router` 7 + `@tanstack/react-query`），组件库为自有 `kit`/`shell`，图标 `lucide-react`，样式为自有 CSS（`*.css`）。
- 同源 BFF：`/papi`，按显式 allowlist 转发 WFE 路由并带会话 bearer token。
- 后端：Go 模块 `backend/`（API + workers：同步、起草、load、问答、通知），状态在 MySQL，同步表与文档在 S3 兼容存储（本地为 SeaweedFS）。
- 契约：`contract/foundry.swagger.json`、`contract/wfe.swagger.json`、`contract/ontology_agent/*.json`。
- 工程命令：Node 24 + pnpm；`pnpm dev:mock`；验收 `typecheck`/`lint`/`test`/`e2e`（Playwright）。

**路由/页面清单（`src/web/areas/*/paths.ts`，仓库文件证实）**

| 路径 | 页面 |
|---|---|
| `/` | 首页/入口 |
| `/workspaces` | 选择或创建工作区 |
| `/data`、`/data/connections/:id`、`/data/connections/:id/tables/:table`、`/data/documents/:id` | 数据源、连接、同步表、文档 |
| `/ontology`、`/ontology/new`、`/ontology/sample` | 本体列表、新建、示例导览 |
| `/ontology/:id`、`/ontology/:id/versions/:versionId`、`/ontology/:id/generations/:id`、`/ontology/:id/generate` | 本体总览、版本查看/编辑、生成进度、生成表单 |
| `/ontology/:id/loads/:loadId`、`/ontology/:id/documents[/:docId]`、`/ontology/:id/suggestions` | load 详情、文档、审计建议 |
| `/explore/:ontologyId`、`/explore/:id/records`、`/explore/:id/entities/:entityId` | Explorer 画布、按类型记录、实体页 |
| `/ask/:ontologyId` | Analyst（线程 + 提问） |
| `/settings/{ai,members,access,billing,enrichment}` | 设置 |

注意：**没有独立的 `analyst/` 目录**；Analyst 实现在 `areas/ontology/ask*.tsx`，路由是 `/ask/:ontologyId`——这印证"它是本体/load 的附属问答，不是独立 BI 产品"。

---

## 6. 检索链路：有没有"先检索候选子图再回答"

**有，但不是向量检索意义上的 RAG。** 两条链路：

### 6.1 Explorer 读链路（交互式检索）

1. 按版本布局**播种**首屏节点（`lib/seeding.ts`）；
2. 标签栏按 label **分页读**（每页 50，`skip` 而非 `where`，避免全量过滤）；
3. 点节点 → **度探测**（廉价计数）→ 展开时按关系读邻域（每方向 ≤50 边）；
4. 点标签/实体 → 读该 label 一页 / 实体页记录；
5. 搜索框：已加载节点匹配 → `$id` 精确 → 全文索引 → `contains` 扫描（仅词法）。

### 6.2 Analyst 链路（retrieval → subgraph → answer）

1. 请求携带：问题、`focus`（若有，读成第一个 handle `n1`）、load、版本、`ontology.toml`/`mappings.toml`、`as_of`、预算（`facts=200000`、`instances=2000000`、`rounds=64`、`wall_ms=5000` 等）；
2. Agent 循环：规划**类型化查询**（位置/步骤/过滤/聚合）或**受限裸查询**；经**只读代理**在 HelixDB 上执行；
3. 每次 `tool_result` 落成 **evidence**（`e17` 递增），一行摘要，不回传原始大值；
4. 读到的记录构成**候选子图/证据集**；模型只基于它写答案；
5. 答案分块输出，逐句挂 citation → 指向 evidence 目标（实体/事实/表行/文档片段/rule-break）；
6. 覆盖不足 → `cannot_answer` + `reason` + `gap` + `kind`。

**结论**：Helix 的"retrieval"是**结构化图查询**（规则在读取时应用），不是 embedding 召回；"subgraph"是**证据记录集**，不是向量近邻。仓库内未找到 embedding/向量检索接线证据（HelixDB 自身能力未在本轮核实）。

---

## 7. 映射表：Helix 交互 → 我们产品环节

我们现状（代码核对）：`web/browse.html` 3 tab（本体/口径卡/术语别名）；`web/ontology.html` 有"实体搜索与邻居子图"；`web/search.html` 只展示片段/事实/引用 JSON；后端 `/browse/*` 7 个只读 GET；`/ui/api/{entities,neighbors}`；`context.resolve` 返回 `steps[]`（`graph.seed` → `graph.facts` → `search.hybrid` → `budget.cut`）；`/answerable` 已存在。

| # | Helix 交互 | 我们的环节 | 已有 / 缺失 | 建议做法 | 优先级 |
|---|---|---|---|---|---|
| M1 | 标签栏（label 计数/可见性） | `browse.html` 本体 tab + `/browse/ontology/tree`、`/browse/ontology/instances` | 部分已有：类/属性树 + 实例分页；缺**边类型计数**与可见性开关 | 在树节点旁显示 `instancesTotal`；边类型计数用一条 `COUNT` SPARQL（只读缓存）；不做显隐开关（无画布） | P2 |
| M2 | 力导向画布 | `ontology.html` 邻居面板（chips + s/p/o 表） | 缺失 | **先不做**；至少等 `/ui/api/neighbors` 支持谓词过滤 + 度数后再评估只读 SVG | P2 |
| M3 | 节点详情（属性 + 关系分组 + 度） | `/ui/api/neighbors?iri=&limit=` | 部分已有：一跳 s/p/o 平铺，limit 50；缺**按谓词分组**与 in/out 度 | 前端按 `p` 分组折叠 + 显示每谓词条数；后端加 `degree` 字段（1 条 COUNT） | P1 |
| M4 | 搜索（ID 精确 + 全文 + 包含） | `/ui/api/entities?q=` | 部分已有：label/IRI 片段；缺 IRI 精确、全文索引 | 前端加"精确 IRI"开关（`q` 以 `http`/`urn` 开头时走精确匹配）；全文索引不引入（PG tsvector 成本另评） | P1 |
| M5 | 按关系展开邻域（有界 50） | `/ui/api/neighbors` | 部分已有：只能全量一跳 | 增加可选 `predicate` 参数（SPARQL `?s <p> ?o` / `?s ?p <o>`），仍固定 1 跳；返回 `truncated` | P1 |
| M6 | hub 度数告警 | 无 | 缺失 | 邻居请求前先 COUNT；>200 条时前端提示"仅显示前 N 条" | P2 |
| M7 | 双 load 并排对比 | `/ontology/versions/{id}/diff` + `governance.html` | 部分已有：JSON/Markdown diff、breaking 标记 | 不做画布对比；在 diff 结果里加"按类/属性筛选 + 一跳差异实体列表"链接到本体 tab | P2 |
| M8 | 值级溯源徽标 | `/browse/triples`（返回 `graph/s/p/o`） | 缺失：无 `source`/`asserted_at`；前端无 triples 入口 | **P0**：新增 triples tab，列 `graph/s/p/o`，并按事实模型补 `source`/`assertedAt`（只读，不改写路径） | P0 |
| M9 | 实体页（事实/文档/评审） | 无独立实体页；`documents.html` + 邻居面板 | 部分已有：文档库、冲突审批 | 在邻居面板点实体 → 抽屉展示：一跳事实 + 命中该实体的 chunk（复用 `/context/resolve?entityHints`）+ 冲突状态 | P1 |
| M10 | 单轮问答面板 | `search.html` → `/ui/api/search` → `context.resolve` | 部分已有：检索结果 + 引用地址；无"问答"外壳、无线程 | 先做**单轮**：问题框 + 结果 + 可答性，不做多轮/线程（多轮需 LLM 编排与预算） | P1 |
| M11 | 步骤时间线（tool steps） | `context.resolve` 已返回 `steps[]`（4 段） | **数据已有，前端未渲染** | 在结果上方渲染时间线：段名/耗时/输出计数；`degraded`/`truncated` 徽标并入 | P0 |
| M12 | 逐句引用 chip | `context.resolve` 返回 `citations[]`；前端只 `JSON.stringify` 打印 | **数据已有，前端未用** | 片段/事实行挂 chip：chunk → `documents.html#chunk`，fact → 过滤后的 triples tab；保留原始 JSON 折叠 | P0 |
| M13 | 拒答与缺口 | `/answerable`（GET/POST）已实现 | 后端已有，前端未调用 | 检索前/后展示 `answerable`、`reasonCode`、`missing`、`nearbyTerms`；不通过就置灰"出数/回答" | P0 |
| M14 | 图表（查询输出可视化） | `/metrics/{id}/output?compute=true` + 口径卡 tab | 部分已有：计算接口；前端只有定义卡 | 口径卡详情加只读折叠块"计算（fixture）"，原样显示 `E_METRIC_*` 与 `publishable` 护栏；不画真实业务图 | P2 |
| M15 | 以实体提问（focus） | `context.resolve` 支持 `entityHints[]`；搜索页无入口 | 部分已有：后端支持；前端缺 | 邻居面板/实体抽屉加"以此实体检索"，跳 `search.html?entityHints=<IRI>` 并自动带入 | P1 |
| M16 | 约束破坏（rule-breaks） | `governance.html` SHACL 校验/gates；`/validation/*` | 部分已有：违规码与 focusNode；未与浏览联动 | SHACL 违规列表按 `focusNode` 链到 triples/邻居视图；不改门禁语义 | P1 |

**优先级汇总（16 项）**：P0 = 4（M8/M11/M12/M13）；P1 = 7（M3/M4/M5/M9/M10/M15/M16）；P2 = 5（M1/M2/M6/M7/M14）。

---

## 8. 我们明确**不该做**的交互

| # | 不做项 | 为什么不做 |
|---|---|---|
| N1 | 力导向画布 + 多跳路径探索 | 我们没有 path/multi-hop 读接口；先做画布只会得到"节点堆叠 + 假交互"，且与 RDF 的 IRI 寻址不匹配。等邻居 API 支持谓词过滤与度数后再评估。 |
| N2 | 双 load 并排图谱对比 | 我们已有版本 diff（JSON/Markdown + breaking）；画布并排是展示层成本，且易把"版本差异"误读为"事实差异"。 |
| N3 | LPG 的数字 `$id` 句柄与 label 位图优化 | RDF 主体是 IRI；照搬数字句柄会把存储实现泄漏到契约，且破坏可移植性。 |
| N4 | 向 LLM 暴露 `helix_query` 式裸查询工具 | 与我们的治理/只读白名单冲突（GSP 旁路已封）。若未来做 Agent，只能开放**只读 SPARQL 白名单**并复用 `/browse/sparql` 的 SELECT/ASK 限制。 |
| N5 | Explorer 内联写操作/编辑 | 我们的浏览面是只读；写入统一走治理控制台与 gates，避免双写路径。 |
| N6 | 语义/向量搜索入口 | Helix 自己也没有；我们已有 hybrid（向量+词法+RRF），照抄反而降级。 |

---

## 9. 我们 browse/检索界面的可用性缺口（本轮不改代码）

| # | 缺口 | 证据 | 最小改法 |
|---|---|---|---|
| G1 | **tab 数与认知不符**：实际只有 3 tab；`/browse/triples`、`/browse/sparql` 后端就绪但无 UI | `web/browse.html`（tab 容器与三个面板）；`api.py`（`browse_triples`/`browse_sparql` 路由） | 加两个只读 tab：triples（`subject/predicate/object/graph` 过滤 + 分页）、sparql（SELECT/ASK 输入 + 结果表）；纯原生 JS，复用现有 GET |
| G2 | **口径卡是死胡同**：详情只渲染字段，不能跳到相关类/事实/术语 | `web/browse.js`（口径详情渲染为字段平铺） | 详情加三链接：相关类 → 本体 tab 过滤；相关事实 → triples；涉及术语 → 术语 tab；映射来源先用现有 `formula/denominator` 字段做文本匹配，不新增映射表 |
| G3 | **检索页没有"过程与依据"**：steps 未渲染、citations 是 JSON 字符串、`/answerable` 未调用 | `web/app.js`（搜索结果/引用渲染）；`context.py`（`resolve` 的 `steps`/`citations`） | 纯前端：steps 时间线 + citation chips + 可答性徽标；零新端点 |
| G4 | **实体与检索断开**：邻居面板不能"以此实体检索" | `web/ontology.html`（实体搜索/邻居面板）；`context.resolve` 已支持 `entityHints` | 按钮跳 `search.html?entityHints=<IRI>`；搜索页读 query 参数并 POST 给 `/context/resolve` |
| G5 | **邻居只有全量一跳**：无谓词过滤、无度数、无截断提示 | `api.py`（`/ui/api/neighbors` 仅 `iri`/`limit`） | 后端加可选 `predicate` 与 `degree`；仍固定 1 跳；`truncated=true` 原样返回 |
| G6 | **指标出数未接线**：`/metrics/{id}/output` 无 UI，口径卡看不到可计算性结论 | `api.py`（metric output 端点）；`web/browse.js`（仅定义卡） | 详情加"计算（fixture）"折叠块，原样显示 `E_METRIC_*`、`publishable`、`definitionVersion`；不做真实业务结论 |

---

## 10. 证据与限制

**仓库文件（本轮实际读取）**
- `README.md`（根）：定位、三行启动、3000/8333、连接器、同步、本体 agent、load/provenance/review、Explorer/Analyst 截图 alt、安全模型。
- `AGENTS.md`：Next.js 16 + react-router 7 + TanStack Query + `/papi` BFF + 契约文件 + 工程命令。
- `backend/README.md`：Go 后端与 workers、MySQL、S3/SeaweedFS、托管同码复用（sign-in/roles/workspaces）。
- `src/web/areas/ontology/paths.ts`、`data/paths.ts`、`workspace/paths.ts`：路由清单。
- `src/web/areas/explore/explorer-page.tsx`、`explorer/DatabaseExplorer.tsx`、`ExplorerBar.tsx`、`ExplorerSearch.tsx`、`Inspector.tsx`、`LabelRail.tsx`、`ContextMenu.tsx`、`lib/queries.ts`：Explorer 交互与读路径。
- `src/web/areas/ontology/ask.tsx`、`ask-model.ts`、`ask-chart.tsx`：Analyst UI/步骤/引用。
- `contract/ontology_agent/ask_event.json`、`ask_result.json`、`ask_request.json`、`read_request.json`、`read_result.json`、`catalog.json`：事件、结果、请求、预算、证据、模型目录。
- `.github/assets/explorer.png`、`.github/assets/analyst.png`：截图资产存在（未逐像素核对）。

**无法确认**
- HelixDB 自身是否内建向量索引并被 Foundry 实际接线：仓库内未找到接线代码；HelixDB 外部能力本轮未核实 → **未找到证据**。
- `local/compose.yaml` 的服务清单与镜像 tag：本轮只读 `backend/README.md`/`README.md` 的转述（site/foundry/ontology-agent/MySQL/SeaweedFS/HelixDB），未逐行读 compose 文件。
- Explorer 首屏种子数、hub 阈值等具体常量：只确认 `neighborLimit=50` 与 `degreeThreshold` 存在；其余数值未逐文件核对。
- 托管角色矩阵的完整定义（owner/member/grantee 的具体权限）：只确认 `backend/access` 存在与 README 描述，未逐条读规则表。

**对本仓库 `22` 号文档的修正/补充**
1. 22 §3.3 的"是否具备独立文档导入链路（未核实）"→ **已证实**：README 明确文档（md/txt/PDF）与表格文件（CSV/TSV/JSON/JSONL/Parquet）连接器，并有文档 sets/页面。
2. 22 §3.3 的"Explorer/Analyst 四项交互（未逐条核名）"→ 本文给出 10 + 10 项逐条核名与代码位置。
3. 22 §2 表格"向量检索：无法确认"→ 本文结论：**仓库内未找到向量检索证据**；Explorer 搜索为词法，Analyst 为结构化查询。
