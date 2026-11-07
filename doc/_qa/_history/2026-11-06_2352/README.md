# COA 本体平台 · 逐特性只读验收总报告

> 终端汇报报告 / 技术尽调第二轮 · 含高级架构师整体结论
> 采集时间：2026-11-06 23:33–23:53 (+0800)　|　对象：`D:\agentABC\coa` · 分支 `luke`
> 前置报告：`audit/COA_技术尽调报告_2026-11-06.md`（工作区，第一轮尽调）

---

## 0 这份报告怎么读

| 目录 | 内容 |
| --- | --- |
| `q_<编号>_<特性名>.md` | **每个特性一个独立用例**，固定五段：测试目标 / 输入 / 期待输出 / 真实输出 / 结论 |
| `screenshots/q_<编号>.png` | 该用例真实终端输出的证据截图（Edge headless 渲染，非伪造界面） |
| `evidence/q_<编号>.txt` | 该用例完整原始响应（未截断） |
| `evidence/q_<编号>.html` | 截图源 |
| `run_qa.py` / `render_shots.py` | 只读采集器与截图渲染器，可复跑 |
| `evidence/_summary.tsv` | 37 条用例的结论机器可读汇总 |

**每个特性都有单独叫法**：`S00–S14` 为路线图切片、`O/M/R` 为本轮 17 条特性编号、`B03/B04` 为前置交付、`P01–P03` 为本体原理专项。编号与 `_design` 文档里的特性代号一一对应。

---

## 1 验收方法与零污染声明

**方法**：静态核对文档判据 → 在运行中的 Docker 实例上逐条实测 → 用只读 SQL / 只读 SPARQL 交叉验证 → 记录输入、期待输出、真实输出、结论 → 渲染截图 → 前后基线对比。

**只读约束（全程遵守）**：

- 只发送 `HTTP GET`、只读 `SQL SELECT`、只读 `SPARQL SELECT`，以及一个经源码确认不写库的纯读 `POST /context/resolve`。
- **未调用** `/answer`（会写 PROV 拒答事件）、**未运行** `smoke` / `acceptance`（会写主库）、**未触发** `seed` / `refresh` / `import` / `materialize` / `approve` / `publish` / `reindex` / `rollback` 任何写入路径。
- 未修改 `platform/` 下任何代码或配置；只在 `doc/_qa/` 下新增测试记录。

**运行环境**（采集时）：`docker compose` 6 个服务在跑，`/readyz=200`（database / graph / storage 全 ok），OpenAPI **127 个路径**（87 GET / 44 POST），`schema_version=34` 与容器内迁移头 `V34` 一致。

> ⚠️ **重要**：审计期间并行开发线仍在写同一个库，环境并非冻结状态。前后计数差异全部来自外部并发写入，不是本轮用例造成的。详见 §5。

---

## 2 结论统计

| 结论 | 数量 | 含义 |
| --- | --- | --- |
| **PASS** | **21** | 文档判据在运行实例上成立 |
| **PARTIAL** | **10** | 能力存在但有缺口（需非默认参数 / 数据稀疏 / 部分成立 / 只能验证结构） |
| **FAIL** | **5** | 判据明确不成立 |
| **OFF** | **1** | 代码存在但按设计默认关闭，运行实例不可复现 |
| 合计 | **37** | |

若把 `PARTIAL` 按「不算达标」计，**完全达标率 21/37 ≈ 57%**；若把「结构存在、只是数据/配置未就位」也算可用，则约 84%。两种口径都不能读成「全绿」。

---

## 3 逐用例总表

| 编号 | 特性 / 工作流 | 结论 | 一句话结论 |
| --- | --- | --- | --- |
| [q_S00](<q_S00_平台就绪与运行时契约.md>) | S0 平台就绪与运行时契约 | PASS | 三项健康端点 200，provider 声明与实际组件一致 |
| [q_S01](<q_S01_T-Box 本体存储与版本治理.md>) | S1 T-Box 版本治理 | PARTIAL | 版本枚举与审计链可用，但指针被 smoke 反复改写 |
| [q_S02](<q_S02_文档入库与切块.md>) | S2 文档入库与切块 | PASS | 文档 / 片段 / 向量三层计数一致，向量覆盖近 100% |
| [q_S03](<q_S03_混合检索与 RRF 融合.md>) | S3 混合检索 | PASS | hybrid + RRF(k=60) 双路召回，degraded=false |
| [q_S04](<q_S04_抽取候选与审批留痕.md>) | S4 抽取候选 | PASS | 候选表与两个端点计数一致 |
| [q_S05](<q_S05_SHACL 校验与推理物化.md>) | S5 SHACL / 推理物化 | PARTIAL | shapes 与 reasoner 可用，但推理只读 `abox:main`，历史失败非零 |
| [q_S06](<q_S06_Context 组装 API.md>) | S6 Context 组装 | PARTIAL | 包结构完整，但 terms / entities / facts 全空，只靠检索片段 |
| [q_S07](<q_S07_最小 Web UI 页面.md>) | S7 最小 Web UI | PASS | 四个原生 HTML 页面全部 200 |
| [q_S08](<q_S08_A-Box 事实治理与撤回.md>) | S8 A-Box 事实治理 | PARTIAL | 事件账本近万条，但 `fact_assertion` 近乎空库 |
| [q_S09](<q_S09_冲突裁决与审计导出.md>) | S9 审计导出 | PASS | 事件可导出 NDJSON，自带链信息 |
| [q_S10](<q_S10_可逆裁决与事件链重放校验.md>) | S10 事件链重放 | PASS | PROV 链 ok=true，PROV / T-Box 图严格分离 |
| [q_S11](<q_S11_T-Box 变更治理与提案-事件.md>) | S11 T-Box 变更治理 | PASS | 提案 / 事件 / 状态流三类治理对象可查 |
| [q_S12](<q_S12_完整性收口·影响分析与门禁证据.md>) | S12 完整性收口 | PASS | 影响分析带输入指纹，证据包可枚举 |
| [q_S13](<q_S13_批量入库与断点续跑证据.md>) | S13 批量入库 | PASS | 批次 / 条目 / 失败隔离信息可读 |
| [q_S14](<q_S14_平台验证·指标可发布出数.md>) | S14 可发布出数 | PARTIAL | `/output?compute=true` 能出数且带溯源，但 `/compute` 默认恒空，两条路径参数不兼容 |
| [q_O01](<q_O01_O-01 数据字典收尾（列内省与列↔属性绑定）.md>) | O-01 数据字典收尾 | PASS | 375 行字典、四视图可用；绑定率 79/81 口径诚实，未扩大分母 |
| [q_O02](<q_O02_O-02 T-Box 提案-审批-supersede 状态机.md>) | O-02 状态机 | PARTIAL | 状态流与事件可读，写路径判定无法只读触发 |
| [q_O03](<q_O03_O-03 变更影响分析.md>) | O-03 影响分析 | PASS | 字段完整、带指纹、可导出 |
| [q_O04](<q_O04_O-04 发布门禁证据包.md>) | O-04 证据包 | PARTIAL | 结构可用且非法输入被拒，生成动作需写路径 |
| [q_O05](<q_O05_O-05 术语核对与 SKOS 导入 diff.md>) | O-05 术语核对 | **FAIL** | 当前指针图 0/85 概念、0/18 别名、无核对记录；词表只在历史版本图 |
| [q_O06](<q_O06_O-06 健康与 diff 类-属性级汇总.md>) | O-06 diff 汇总 | PASS | 类/属性聚合、两版本快照、空态说明齐全 |
| [q_M01](<q_M01_M-01 可算性补齐第一批（8 条高价值指标）.md>) | M-01 可算性补齐 | **FAIL** | 8 条 `/compute` 默认调用 0 条出数，单测自插自算 |
| [q_M02](<q_M02_M-02 对外出数清单与 publishable 治理.md>) | M-02 出数清单 | PASS | 85 行 100% 覆盖，JSON / CSV 同源 |
| [q_M03](<q_M03_M-03 多口径并列与族索引.md>) | M-03 族索引 | PASS | 族索引与口径卡列表可用 |
| [q_M04](<q_M04_M-04 口径卡与判定溯源进浏览台.md>) | M-04 口径卡溯源 | PARTIAL | 卡与溯源字段可读，但多数指标无判定链可点 |
| [q_M05](<q_M05_M-05 行业公式监管原文标注.md>) | M-05 行业口径标注 | PASS | industry 条目 100% 标「内部基线、不外报」且被排除出对外清单 |
| [q_M06](<q_M06_M-06 partial 判定与规则登记-可执行核对.md>) | M-06 登记/可执行核对 | PASS | 16 已执行 / 1 仅登记 / 3 不可执行，与文档一致 |
| [q_R01](<q_R01_R-01 -answerable 分层覆盖度面板.md>) | R-01 覆盖度面板 | PARTIAL | 面板可用，但本体/术语/事实三层覆盖基本为 0 |
| [q_R02](<q_R02_R-02 引用与拒答质量闭环（10 例 golden set）.md>) | R-02 问答质量闭环 | **FAIL** | 平台自报 10 例仅 5 例通过（passRate 0.5），引用链路本身健康 |
| [q_R03](<q_R03_R-03 实体页溯源徽标.md>) | R-03 溯源徽标 | PASS | 实体页 / 字段溯源 / src:// 解析三段链路全通 |
| [q_R04](<q_R04_R-04 -browse 六 tab 交叉跳转.md>) | R-04 交叉跳转 | PASS | 跳转模板与稳定 URL 已注册且标记只读 |
| [q_R05](<q_R05_R-05 D1-1 轻量多跳 -browse-path.md>) | R-05 轻量多跳 | OFF | `canvas.provider` 默认 `off`，端点 503；设计允许但文档标「已完成」易误读 |
| [q_B03](<q_B03_B-03 实体页（上一轮缺陷复测）.md>) | B-03 实体页复测 | PASS | 上一轮两次 15s 超时已修复，现 0.1s 返回 |
| [q_B04](<q_B04_B-04 健康看板（上一轮缺陷复测）.md>) | B-04 看板复测 | PARTIAL | 「查空图显示 0 实例」已修复；类覆盖 0、推理失败累计仍非零 |
| [q_P01](<q_P01_本体原理·T-Box-A-Box 命名图分布与推理输入一致性.md>) | 本体原理·命名图 | **FAIL** | 推理器 / 看板 / 实体页对「哪个图是 A-Box」无唯一权威 |
| [q_P02](<q_P02_本体原理·版本指针一致性与跨消费者漂移.md>) | 本体原理·版本指针 | **FAIL** | 多指针、多消费者解析到不同本体版本，切换非原子 |
| [q_P03](<q_P03_本体原理·溯源引用完整性与失效检测.md>) | 本体原理·溯源引用 | PASS | 有效引用可解析，失效/不存在引用分级报错，PROV 链自洽 |

> 表中链接均为相对路径；部分文件名含空格或全角括号，Markdown 用尖括号包裹。

---

## 4 最值得向决策层汇报的 6 个发现

按严重度排序：

1. **语义内核没有闭合**（`q_S05`/`q_S06`/`q_R01`/`q_P01`）：推理器只读 `abox:main`，真实 A-Box 在 `abox:synthetic`；Context 包里 `terms/entities/facts` 全空；`/answerable/panel` 四层里三层覆盖率 0。检索层能召回，语义层基本没参与。
2. **T-Box 版本切换不是原子的**（`q_O05`/`q_P02`）：B-05 的 180 个 SKOS 概念确实写进了图库，但只存在于历史版本图；当前指针指向的图里 0 个概念、术语覆盖 0/85、`checks` 无记录。指针切了，词表 / shapes / 推理输入没跟着切。
3. **两套出数路径并存且默认参数不通**（`q_S14`/`q_M01`）：老的 `/output?compute=true` 能返回 61.25%、20 个样本、完整 `sourceRef`；G2 新增 `/compute` 默认 `dataSource=fixture`，而事实表/观测表都是 `synthetic`，默认调用恒返回 `rows=[]`。`metric_compiler.py` 的 CTE 固定追加 `data_source = %s` 是根因。
4. **单测绿 ≠ 运行态可用**：58 号的 19 项单测用 `data_source='fixture'` 的固定行「自插自算」，所以判据「≥6 条返回非空」在单测里成立、在运行实例上 0 条成立。同类问题还有 `-k` 过滤（上一轮发现 305 条只跑 189 条）。
5. **R-02 与文档状态直接冲突**（`q_R02`）：平台自己算出的 golden set 是 10 例过 5 例，而 `52` 号把 R-02 标为「已完成」。可取的是 citation 覆盖率 1.0、断链率 0.0。
6. **文档状态与运行态脱节**：`/status` 仍自报 `slice=S13`；`R-05` 标「已完成」但默认 `provider=off`；`45/46/48` 曾写 `schema_version=28`（现 34）；`doc/README` 索引是 65 篇快照（现 200+ 篇）。注意：`52` 号文末的「验收口径」写 `acceptance-s14.ps1 212/0/0`、全量单测 366 例 OK，但本轮未在仓库内找到对应一手日志（`.log` 被 `.gitignore` 排除）。

**同时必须讲清楚的好消息**（避免过度否定）：

- PROV 哈希链、PROV/T-Box 图分离、`E_*` 分级错误码、`E_SOURCE_REF_STALE`/`NOT_FOUND` 失效检测都是扎实设计，没有为了指标好看去伪造源行。
- `57` 号主动写明「97.53% 是 79/81 可映射列口径，按 375 总列计仅 21.1%，未为达标扩大分母」；`M-06` 明确区分「已执行 / 仅登记 / 不可执行」。口径诚实，不是弄虚作假。
- 上一轮尽调发现的实体页超时、看板查空图两个缺陷**已被并行开发线修复**（`q_B03`/`q_B04`），团队响应能力在线。
- 结论：**没有发现凭空编造功能或数据**；问题是「已交付 / 全绿 / 收口」的叙述口径偏松，以及语义内核的闭环没做完。

---

## 5 环境并发变更记录（重要，关系到零污染判断）

审计期间并行开发线（G1–G6，已合并进 `luke`）持续写同一个库，并批量回写文档。前后对比：

| 表 / 指标 | 23:33 基线 | 23:53 交付前 | 变化来源 |
| --- | --- | --- | --- |
| `metric_observation` | **0** | **37,471** | 并行线回填观测数据（55 个指标，`data_source=synthetic`） |
| `source_ref_registry` | 76 | 337 | 随观测回填新增引用 |
| `fact_assertion` | 0 | 0（中途曾到 6） | 少量断言写入后又归零 |
| `prov_event` | 313 | 382 | 外部写入，PROV 链仍 `ok=true` |
| `document` / `document_chunk` / `chunk_embedding` | 2958 / 15110 / 15042 | 3040 / 约 15200 / 约 15100 | 批量导入持续追加 |
| `ontology_version` | 1844 | 1881+ | smoke / 版本发布 |
| `schema_version` | 34 | 34 | **未变**（容器内迁移头同为 V34） |
| `metric_definition` / `data_dictionary` | 85 / 375 | 85 / 375 | **未变** |
| `graph_pointer` | `tbox/current` 反复被 `smoke-restore` 改写 | 同左 | 外部 smoke |
| git 工作树 | 干净（1 个未跟踪文件） | 多份 `doc/_design/*.md` 显示 `M` | 并行线回写文档 |

**归因证据**：`graph_pointer` 的备注是 `smoke-restore`；`git log` 显示 `integrate: G1..G6 all lines`、`M-01 rework` 等合并提交；本轮采集器源码里没有任何 `INSERT/UPDATE/DELETE` 或写接口。

**影响与处理**：这次变更直接推翻了本轮初稿里的两条结论（`metric_observation=0` → 已回填；obs 引用悬空 → 已可解析）。我们做了二次复测，把 `q_S14` 从 `FAIL` 修正为 `PARTIAL`、重写 `q_P03`，并重新采集全部 37 个用例。**报告内所有数值均为采集时刻快照**；判据冲突点（`/compute` 默认恒空、术语 0/85、问答 5/10、多指针漂移）在复测后依然成立。

> 这本身也是一条尽调结论：在没有冻结环境的前提下，任何「当前可出数 / 当前覆盖度」的验收数字都不具备可复现性。第一轮报告建议「先冻结环境」并未被采纳。

---

## 6 零污染复核

- `/prov/verify`：`ok=true`，T-Box/PROV 图分离 `ok=true`，`tboxProvTriples=0`，链未被破坏（我们**没有删除**任何外部写入的事件，删了才会破坏哈希链）。
- `schema_version`、容器内迁移头、`graph_pointer` 结构、容器状态：未被本轮用例改动。
- 未在 `platform/` 下修改任何代码 / 配置 / 业务表；未在 `doc/_design/`、`doc/README.md` 下改动任何既有文档。
- 唯一新增文件均位于 `doc/_qa/`。

---

# 7 高级架构师整体结论

> 视角：需求 × 实现 × 本体原理三方对齐；判断开发路径与架构走向是否合理、项目是否走偏、如何改善。

## 7.1 三方对齐分析

| 维度 | 实际内容 | 判断 |
| --- | --- | --- |
| **需求** | `52` 把范围收窄到「本体治理 / 口径与指标 / 检索问答」三个域；`30` 与 `N-03~N-17` 明确放掉观测运维、CI、备份、多用户、鉴权、真实数据源、性能调优；`64` 把多轮问答评估为后置。本质是**单机、合成数据、口径治理优先、可演示可审计**。 | 边界守得住：没有膨胀成多租户云化平台。 |
| **实现** | S0–S14 共 15 切片 + 本轮 17 条 O/M/R + 前置 B-03~B-06；127 个端点、V1–V34 迁移、6 条并行开发线、200+ 篇文档。 | 工程量真实、模块齐全、可审计性扎实；**但横向铺得远快于纵向闭环**。 |
| **本体原理** | 一个本体系系统的价值不在端点数量，而在 **T-Box（概念/约束）→ A-Box（实例/事实）→ 推理（隐含知识）→ 溯源（可引用结论）** 这条链是否闭合，以及**版本切换是否原子**。 | 实测这条链**断在四个位置**（见 7.2），版本切换不原子。 |

## 7.2 语义内核的四处断点（均有本轮实证）

1. **版本切换非原子**：指针 `tbox/current` 被切到新版本，词表、shapes、推理输入、术语覆盖各自记着自己的版本 → `q_O05` 当前图 0/85 概念、`q_P02` 多消费者解析到不同版本。发布新版本反而让术语与覆盖度集体失效。
2. **命名图缺一等公民注册表**：推理器读 `abox:main`、看板读 `abox:main + abox:synthetic`、真实数据绝大多数在 `abox:synthetic`（`q_P01`/`q_S05`/`q_B04`）。每个模块各写各的图名常量，物化产物极少。`O-01` 给物理列做了绑定注册表，图命名空间却没有等价物。
3. **定义层与实例层脱节，且出现两个实例层**：85 条指标定义、95 条字段绑定、53 个指标有绑定，但 `fact_assertion` 近乎空库；`metric_observation` 是否被回填决定「能否出数」；`fact` 表计算与 `observation` 表出数是两条独立通路，默认值互不兼容（`q_S14`/`q_M01`/`q_S08`/`q_P03`）。
4. **推理与 Context 的语义层空转**：推理历史失败非零、Context 包 `terms/entities/facts` 全空、可答性面板三层覆盖 0、golden set 10 例过 5 例（`q_S05`/`q_S06`/`q_R01`/`q_R02`）。检索能召回片段，但本体没有真正参与答案生成与校验。

一句话：**平台建了一个很完整的「本体元数据治理平台」，但还不是一个「能工作的本体系系统」。**

## 7.3 开发路径与架构走向是否合理

**分段看，前段合理、后段偏移。**

- **S0–S13 是合理的**。用切片 + smoke 快速立起依赖可替换、可审计、可回放的骨架：文档入库、混合检索、版本治理、SHACL、PROV 链、可逆裁决。这一阶段做对了顺序，也留下了真正扎实的工程资产（PROV 哈希链、错误码体系、图分离）。
- **S14 之后路径发生了偏移**。17 条本轮特性里，**14 条是只读台账 / 面板 / 清单 / 状态机**（O-01~O-06、M-02~M-06、R-01、R-03、R-04、R-05），只有 M-01 触及「真的算出数」——而 M-01 恰好是 FAIL。每一条单独看都合理，合起来却系统性地绕开了最难也最核心的一件事：**让一条指标从定义走到真实数值，并让这个数值能被本体约束与溯源链验证**。这是排期取向的结果，不是偶然。
- **验收方式强化了偏移**。判据偏「HTTP 200 / 计数 / 结构存在」，不偏「语义正确性」；`-k` 过滤让 305 条单测只跑 189 条；单测自插自算；`passed=0` 靠脚本容错；一手日志被 `.gitignore` 排除。于是绿灯越来越多，闭环却没推进。
- **流程复杂度超过了产品复杂度**。单机、合成数据、无并发用户的演示阶段，却上了 6 条并行 worktree、迁移号预分配、集成契约、专职推送线。本轮审计直接观察到后果：主库被并发写、指针被 smoke 反复改、`schema`/代码/图版本漂移、文档批量回写中。对当前阶段这是**过早引入分布式协作成本**。

## 7.4 整体结论：项目是否走偏

**方向没有走偏，层次走偏了；是局部走偏，而且可逆。**

- 没有跑去做多租户、云化、真实数据源、鉴权（那些被明确列为不做），**边界是守住的**，这比很多同类项目强。
- 但「把口径治理做成了口径台账」是实质偏移。判断依据很朴素：对外最有价值的一句话本应是「**我们能算出 X，并说清它为什么可信**」，现在只能说「**我们有 85 行清单，说明哪些理论上能算**」。
- 还有一处**叙事与实现分离**必须点破：仓库外壳是 AWS COA（`Scan → Model → Serve`，给 Agent 提供语义上下文层），README 讲的是 Agent 上下文；实际交付物是金融指标口径治理 + 演示型数据资产。两边都占着，会让后续所有架构决策失去判据。**这是 CEO 视角最该先问清的一件事**，比任何单个 bug 都重要。

**可信度评级**：代码与数据 **B+**（真实、有工程纪律）；验收与叙述口径 **C**（偏松、证据链不完整）；语义内核完整性 **C-**（未闭合）；整体「生产可用」按 `52` 号自己的口径仍是 **0 项**，本轮无证据推翻。

## 7.5 改善方案（按优先级，每阶段带可验收判据）

**阶段 0 · 冻结与止血（最先做）**

- 冻结并行写入，指定唯一可写环境；验收期间禁止 smoke 改主库指针。
- 把 `metric_compiler` 的默认 `dataSource` 对齐运行库（或按事实表实际来源解析），消除 `/compute` 默认恒空。
- 全量跑一次不带 `-k` 的 acceptance，把日志与测试结果纳入仓库；文档状态回写：`R-05` 改为「已实现 / 默认未启用」，`/status.slice` 改为真实值，`45/46/48` 的 `schema_version` 统一。
- 判据：同一时刻 `schema_version` = 迁移头 = 容器内代码 = 图指针四方一致；`doc/README` 索引篇数 = 实际篇数。

**阶段 1 · 打通一条纵向闭环（最高优先，其余都排在它后面）**

选 `FIN-BANK-008` 一条，端到端跑通：

`定义 → 字段绑定 → 事实行 → compute 出非空数值 → metric_observation 落一行 → source_ref 可解析 → PROV 链可回溯 → SHACL 校验通过`

- 判据：**不带任何非默认参数**即可出数；人为改动一条事实后数值可复算且变化可解释；`/output` 与 `/compute` 两条路径结果一致或明确声明各自语义。
- 打通 1 条后再复制到 8 条、再到 79 条。**不要用「再补 20 条定义」代替这一步**。

**阶段 2 · 修本体架构（把版本与图变成一等公民）**

- 引入 **Named Graph Registry**：所有图 IRI 从注册表读，禁止模块内常量；推理、看板、实体页、术语覆盖统一从注册表取图集合。
- 引入 **Version Resolution Service**：单一函数解析「当前版本 → T-Box 图 / shapes / 词表 / 推理输入 / A-Box 校验规则」，版本切换原子化；启动与发布时 fail-fast 校验四方一致。
- 判据：切换版本后 `/ontology/terms/coverage` 仍 ≥95%、`/reasoning/status` 的 `aboxGraphs` 与真实 A-Box 一致、`/ui/api/entity` 与推理器解析到同一 `ontologyVersion`。

**阶段 3 · 验收体系从「结构存在」改为「语义产出」**

- 把语义断言加入验收：推理产物可查、SHACL 命中、溯源链端到端、指标数值可复算、Context 包本体层非空。
- 去掉 `-k` 过滤；`skipped` 不得静默算通过；`failed>0` 必须非零退出。
- 重新定义「可出数」为**三条件同时满足**：默认调用返回非空数值 + 存在观测行 + 存在可解析 `source_ref`。当前 85 行清单只满足第一条的一部分。

**阶段 4 · 流程减重**

单机演示阶段暂停 6 条并行线，回到单线闭环；等阶段 1–2 完成、产品定位明确后再决定是否恢复。当前并行流程带来的漂移成本已大于并行收益。

**阶段 5 · 产品定位二选一（决策项，不是工程项）**

| 选项 | 含义 | 代价 |
| --- | --- | --- |
| A · 承认是「指标口径治理 / 元数据平台」 | 砍掉 Agent 上下文层的外壳叙事，问答/Context 定位为附属查询界面 | 小；主要改文档与产品表达 |
| B · 回到上游 COA 的「Agent 上下文层」 | 必须做 MCP 工具面、真实数据源、鉴权、可观测（正是 `30` 号明确不做的那些） | 大，量级接近重做 |

**建议选 A**：现有工程资产的强项正是口径治理与可审计性，强行往 B 走会浪费已完成的工作。选定后再回头砍掉不匹配的外围端点，比继续横向加功能更有价值。

## 7.6 给决策层的三句话

1. **不是造假，是没闭环**：代码、数据、PROV 链都是真的，问题在于「T-Box → A-Box → 推理 → 溯源」这条链没打通，而验收方式只看结构不看语义。
2. **最急的不是补功能，是冻结环境 + 打通一条**：现在 6 条并行线还在写同一个库，任何验收数字都不可复现；先把一条指标从定义算到可引用的数值，比再补 20 条台账有价值得多。
3. **先定产品定位**：是「口径治理平台」还是「Agent 上下文层」，二选一。这个决定不做，后面每个架构选择都会左右摇摆。

---

## 8 如何复跑

```bash
cd D:/agentABC/coa/platform && docker compose up -d     # 若未运行
cd D:/agentABC/coa
python doc/_qa/run_qa.py          # 只读采集 37 个用例，刷新 md / evidence
python doc/_qa/render_shots.py   # 重新渲染 37 张 PNG（需要本机 Edge）
```

- 采集器不含任何写接口；复跑前建议先冻结并行写入，否则各用例之间的计数可能不一致（本轮已实际遇到，见 §5）。
- 结论字段（`verdict` / `reason`）是审计员依据证据的人工判定，写死在 `run_qa.py` 的用例表里；复跑只刷新「真实输出」与截图。若运行态发生实质变化，需同步复核结论。
- 截图是真实终端/接口输出的 HTML 渲染位图，不是伪造的 GUI 界面；完整原始响应一律以 `evidence/*.txt` 为准。

---

## 9 观测落库后端到端问答复测（2026-11-07）

> **测量时点**：2026-11-07 00:08–00:18 (+0800)，核心读数 00:11:12。
> **与旧快照的关系**：§0–§8 是 2026-11-06 23:33–23:55 的快照，本节原文不改、不覆盖、不重算旧数据。本节是 `platform.metric_observation` 回填 37,471 行之后的独立复测。
> **新增证据**：`evidence/recheck_obs_*.json`、`evidence/recheck_outputs_2026-11-07.json`、`evidence/recheck_publishable_sweep_2026-11-07.json`。
> **新增脚本**：`recheck_obs_2026-11-07.py`、`recheck_outputs_2026-11-07.py`、`recheck_publishable_sweep.py`。旧 `run_qa.py` 与 §0–§8 的记录未被改动。

### 9.1 环境与“51 条”前提复核

| 项目 | 复测读数 | 说明 |
| --- | --- | --- |
| `/readyz` | 200；database / graph / storage 全 ok；`disk_free_pct=32.89` | 运行态可用 |
| `metric_observation` | **37,471 行 / 55 个指标 / `data_source=synthetic` 37,471 / `fixture=true` 0** | 与用户给定前提一致 |
| 对外可出数 | **41 数值 + 10 规则 = 51** | 复算方法见下 |
| 仍有定义但无观测 | 4 条 `structurally_computable`：`FIN-BANK-035`、`FIN-BANK-036-v1`、`FIN-INS-021`、`FIN-INS-025`；另有 4 条 `blocked_semantics` 本就不应出数 | 回填未覆盖全部指标 |

“41 数值”的复算口径：全部 `publishable=true` 且有观测的非规则口径共 42 条，按观测窗口逐条调用 `GET /metrics/{id}/output?compute=true&dataSource=synthetic`；41 条返回数值，唯一失败是 `FIN-INS-017`（`E_METRIC_EVIDENCE_MISSING`）。“10 规则”是 `publishable=true AND output_mode='rule_set'` 的声明条数（本轮未逐条执行规则引擎，见 9.6 的 G03）。

### 9.2 R-01 覆盖度面板（新读数，旧结论保留）

| 层 | evaluated | covered | missing | coverageRate |
| --- | --- | --- | --- | --- |
| ontology | 24 | 1 | 18 | 0.0417 |
| terms | 24 | 16 | 8 | 0.6667 |
| metrics | 24 | 6 | 7 | 0.2500 |
| facts | 24 | 5 | 1 | 0.2083 |

`missing` 总数 55：ontology 43、metrics 7、terms 4、facts 1（`E_FACTS_NOT_SCALAR`，C7/CUST-012）。

**重要更正**：旧 `q_R01_*.md` 的结论文字写“ontology / terms / facts 三层 coverageRate 基本为 0”，但该文件自己保存的真实输出（采集于 23:52:53）已经是 ontology 0.0417、terms 0.6667、facts 0.2083，与本表**数值完全相同**。也就是说：旧结论文字与旧证据自相矛盾；按证据看，观测回填在 23:52 之前已经生效，R-01 的读数到本时点没有继续变化。本次不是“从 0 变成 66.7%”，而是“旧文字误写成 0”。

新增发现（判定噪声）：ontology 层 43 条缺口里包含“今年”“查”“这张”“们这”“里对”等时间词/停用词/错误切分（如 A5“价值发生巨大变化时银行”），并非 43 个真实本体概念缺口。这个计数会系统性高估本体缺口。

### 9.3 R-02 引用与拒答质量闭环（新读数，旧结论保留）

| 指标 | 新读数 |
| --- | --- |
| cases / passed | 10 / **6**，passRate **0.6** |
| citationCoverageRate | 1.0 |
| citations / resolvable | 53 / 33，可解析率 **0.6226** |
| brokenLinkRate | **0.3774**（baseline 0.0，`regression=true`） |
| 拒答原因 | definition：`E_ANSWER_NOT_COVERED`×2；value：`E_ANSWER_METRIC_NOT_FOUND`×4 |

- 判据仍为 **FAIL**（10 例只过 6 例）。
- 4 条失败归因：**G02 数据问题**（`FIN-INS-021` 0 行观测，`E_FACTS_NO_OBSERVATION`）；**G03 数据/规则问题**（`FIN-BANK-002` 规则执行 `E_METRIC_NO_DATA`）；**G05/G06 检索/本体覆盖问题**（G05“当事人关系历史记录保留多久”、G06“抵押物价值发生巨大变化时银行如何处理”，本体/术语层未覆盖，`E_ANSWER_NOT_COVERED`）。
- 20 条“断链”**全部是 `triple` 类型引用**（`resolveUrl=null`），没有一条是文档/观测引用悬空。`_G4_CITATION_KINDS` 未登记 `triple`，所以它们被构造性地计为不可解析——这是**度量口径缺陷**，不是数据断链。
- 同样地，旧 `q_R02_*.md` 结论文字写“可解析率 1.0、断链率 0.0”，而它的真实输出（23:52:55）已经是 0.6226 / 0.3774。旧文字与旧证据矛盾，旧结论需按证据修正，但本次不改写原文。

### 9.4 端到端 `/answer`（旧快照未覆盖的部分）

旧 `run_qa.py` 为保持零污染明确排除了 `/answer`，因此“问答到底能不能出数”在旧快照里从未被直接测过。本轮用 `GET /answer` 实测 15 条问题（12 条数值题 + 3 条同题钉 `metricId`），结果：

- **13/15 选中了指标**；其中 **12 条事实层 `covered` 并引用了真实观测行**（`obsDbRows` 与 DB 计数一致，`/source/resolve` 全部 200）。剩余 2 条未选中任何指标（V05/V08）。
- **0/15 给出数值**。12 条返回 `answerType=definition`、`reasonCode=E_ANSWER_VALUE_DEGRADED`，答案原文是“事实层 covered，不给出数值”；V12 返回 `E_ANSWER_FACTS_MISSING`（`amount` 非标量）。
- 3 条未出数且不是窗口传递问题的：V05“不良率是多少？”、V08“今年案均赔款是多少？”→ `E_ANSWER_METRIC_NOT_FOUND`（**检索问题**，术语/别名未命中）；V12“本年客户AUM”→ CUST-012 `metricKind=amount` 非标量且 `E_METRIC_NOT_PUBLISHABLE`（**口径策略问题**，不是数据缺失，该指标本就不对外发布）。

**根因（生成问题，非数据/检索）**：运行中的 `_qa_answer` 调用 `metrics_port.compute(metric_id, internal=False)` 时没有传 `asOf` / `periodStart` / `periodEnd`；metrics 服务对 instant 与 period 指标都要求窗口，于是 compute step 统一失败 `E_METRIC_WINDOW_INSUFFICIENT`。而事实层其实已经从观测行拿到了窗口（见 9.5 的 citation locator），只是没有传给 compute。

**为什么这不是“数据问题”**：同一批指标直接调用 `GET /metrics/{id}/output?compute=true&dataSource=synthetic` 全部能出数（9.5）。同一批指标也全部 `factsStatus=covered`、`observationRows>0`。数据已经到了，缺口在答案生成层的时间窗口传递。

### 9.5 引用值 vs 直接 compute（三条抽查）

先说明一个结构性事实：**本轮 15 次 `/answer` 里没有任何 `value-source` 引用，`value` 字段全部为 null**，所以“引用里带出的数值”与 compute 的直接比对在当前运行态**无法成立**——不是数值对不上，而是根本没有数值引用。

| 指标 | `/answer` 观测引用 | `/output?compute=true` | 观测表聚合 | G2 `/compute` |
| --- | --- | --- | --- | --- |
| FIN-BANK-001 | 5,000 行；resolve 200；`src://obs-set/FIN-BANK-001@v3.0?...` | **333.0**（`dataSource=synthetic`，n=5,000） | `max(numerator)=333` | **400 `E_METRIC_BINDING_MISSING`** |
| FIN-BANK-017 | 15 行；resolve 200 | **40.0384061449832** | `834/2083×100=40.038406` | 200，15 行按机构 `0–50.2994`，无单一汇总值 |
| FIN-INS-018 | 4 行；resolve 200 | **100.0** | `1600/1600×100=100` | 200，4 行按险种各 `100.0` |

结论：

1. **观测 → `/output` 出数完全一致**：三条抽查与观测表聚合逐位吻合；另外 6 条也一致（BANK-008 61.2536%、BANK-022 90.0%、BANK-025 19.814%、INS-008 28.9474%、BANK-013 47.8055%、BANK-028 1.8%）。
2. **`/answer` 引用与 `/output` 无法比对**：前者没有数值。
3. **两条 compute 路径语义不同**：`/output` 是观测缓存上的汇总值；G2 `/compute` 是事实表直算、返回按实体的行。BANK-001 在 G2 路径直接不可算（字段绑定缺失）；BANK-017 在 G2 是 15 个机构行，和汇总值 40.038 不是一个粒度。若把 G2 `/compute` 当作“直接调 compute”，当前不能证明它与引用一致，因为两者连输出形态都不同。

### 9.6 新错误类型 / 新问题清单

| 类型 | 出现次数 | 归类 | 说明 |
| --- | --- | --- | --- |
| `E_METRIC_WINDOW_INSUFFICIENT` | 12 | **生成问题** | `/answer` 未把已知窗口传给 compute |
| `E_ANSWER_METRIC_NOT_FOUND` | 2 | **检索问题** | “不良率”“今年案均赔款”无术语/别名命中 |
| `E_ANSWER_FACTS_MISSING` | 1 | 检索/策略 | CUST-012 `amount` 非标量且非对外可发布 |
| `E_METRIC_EVIDENCE_MISSING` | 1 | 数据/配置 | FIN-INS-017 缺证据绑定，是 42 条里唯一出数失败 |
| `E_FACTS_NO_OBSERVATION` | 1 | **数据问题** | G02 `FIN-INS-021` 无观测行 |
| `E_FACTS_RULE_INPUTS` + `E_METRIC_NO_DATA` | 1 | **数据问题** | G03 `FIN-BANK-002` 规则输入无数据 |
| `triple` 引用不可解析 | 20 | **度量缺陷** | 全部无 `resolveUrl`，被计为断链（37.74%） |
| `dataSource` 标为 `business` | 13 | **数据标注问题** | 实际 DB 为 `synthetic`、`fixture=false`；citation 与 facts step 都写成 `business` |
| 观测引用悬空 | **0** | — | 13/13 resolve 200 且行数与 DB 一致，未出现新悬空引用 |

另外两处一致性小问题：

- instant 指标（FIN-BANK-001）的观测 citation locator 用 `periodStart=periodEnd=2025-12-31`，而 `/output` 与 G2 用 `asOf`；resolve 仍可用，但同一事实存在两套时间字段表达。
- 规则型 10 条口径中，实测 G03（`FIN-BANK-002`）执行返回 `E_METRIC_NO_DATA`，因此“10 规则可出数”目前只是声明层面的计数，未经逐条执行验证。

### 9.7 修好 / 没修好 / 归因

| 问题 | 状态 | 归因 |
| --- | --- | --- |
| 有指标定义但没有数 | **已修**（55/85 有观测；41 条对外数值可算） | 数据 |
| 问答引用真实观测行 | **已修**（13/13 可解析、行数一致） | 数据/引用 |
| 问答给出数值 | **未修**（12 条数值题 0 条出数） | **生成问题**（窗口未传递） |
| 数值引用与观测对上 | 不适用（无 `value-source` 引用） | 生成问题 |
| “不良率”“案均赔款”类提问 | 未修（仍拒答） | **检索问题**（术语/别名） |
| R-02 golden 10 例 | 未修（6/10，仍 FAIL） | 2 数据 + 2 检索 |
| R-02 断链率 | 表现退化（0 → 37.74%） | **度量口径缺陷**（triple 无 resolveUrl），非数据断链 |
| 剩余 4 条结构性可算指标无观测 | 未修 | 数据（FIN-BANK-035 / 036-v1 / FIN-INS-021 / FIN-INS-025） |

一句话：**“数据能出数”这件事修好了；“问答能出数”没修好，卡在生成层，不在数据层和检索层。**

### 9.8 副作用与复跑说明

- 本节复测调用 `/answer`（GET）共 18 次（1 次预探测 + 15 次用例 + 2 次 G02/G03 定向探测），`/answer/quality` 1 次（其内部会再跑 10 次 golden 的 `_qa_answer`）。`prov_event` 从 **385**（本次复测开始前）增至 **443**（结束后），净增 **58**。因此：
  - **本次不是零污染采集**；§1 的零污染声明只适用于旧的 `run_qa.py` 37 用例，不适用于 §9。
  - `/answer/quality` 虽然返回 `readOnly=true`，但内部调用 `_qa_answer`，仍会写 PROV 拒答事件，不能按只读接口对待。
- 复跑：`python doc/_qa/recheck_obs_2026-11-07.py` 会刷新 `evidence/recheck_obs_*.json`；`recheck_outputs_2026-11-07.py` 与 `recheck_publishable_sweep.py` 为纯 GET/SELECT。**不要**直接跑 `run_qa.py`，它会覆盖 §0–§8 的 md 与 evidence。

## 10 修复后复测：窗口传递 / triple 登记 / quality 只读 / dataSource（2026-11-07 00:33）

测量时点 **2026-11-07 00:33:07 +0800**（§9 为 00:08–00:18，§0–§9 原文未改）。证据 `evidence/recheck_obs_20261107T003307.json`，修复前对照 `evidence/recheck_obs_20261107T001112.json`。

### 10.1 四处修复与部署方式

| 编号 | 修复内容 | commit | 改动文件 |
| --- | --- | --- | --- |
| R-01-fix | `_qa_answer` 把事实层窗口（`asOf` 或 `periodStart/periodEnd`）与 `data_source` 传给 `metrics_port.compute` | `0a30ed5` | `platform_core/api.py`、`platform_core/metrics.py` |
| R-02-fix | `_G4_CITATION_KINDS` 登记 `triple` | `fcf5747` | `platform_core/api.py`、`tests/test_g4_retrieval.py` |
| R-03-fix | `/answer/quality` 内部调用 `persist=False`，PROV 写入块加 `and persist` | `42c4cf5` | 同上 |
| R-04-fix | `dataSource` 取观测行 / `MIN(data_source)` 实际值，不再按 `fixture` 推断 | `36aa745` | `api.py`、`metrics.py`、测试 |

**部署方式**：本次验证是 hot-patch 运行容器后 `docker restart agent-platform-api`（未重建镜像）。容器 `Created` 未变、仅 `Started` 更新，补丁位于容器可写层，**容器一旦被 recreate 会回退**；权威代码是 worktree 的四个 commit。不要用 `docker compose restart`——本环境曾出现补丁刚写入即被并行 `up` 重建丢失的情况。

另需注意：运行镜像的 `api.py`/`metrics.py` 比 `feat/r-qa` worktree **多出 D 线改动**（`METRIC_DATA_SOURCES` 必填校验、`DRIVABLE_KINDS` 扩展到 count/amount/period_value、period 窗口要求非同日、`_record_computation` 审计等）。本节四个 commit 只含本线修复，合并时需与 D 线并轨；用源码对比（`worktree` vs `live`）可确认差异仅为上述 D 线部分。

**`dataSource` 显式传递（已按 D 线新约束验证）**：运行镜像已含 D 线“取消默认值”的改动——实测 `GET /metrics/{id}/compute?asOf=2025-12-31` 不带 `dataSource` 直接返回 **400 `E_METRIC_DATA_SOURCE_REQUIRED`**（`/output` 仍可省略，实测 200）。R-01-fix 的 `compute_kwargs` 显式带上事实层的 `data_source`（观测行 `string_agg(DISTINCT data_source, ',')` 单值时，即 `synthetic`），因此不依赖默认值；`/output` 调用也始终显式 `dataSource=synthetic`。事实层无观测时该指标不会进入 compute 分支。

### 10.2 15 条 `/answer`：修复前 0 条出数，修复后 12 条出数

| ID | 问题 | 修复前 | 修复后 |
| --- | --- | --- | --- |
| V01 | 逾期天数（DPD） | 0 / `E_METRIC_WINDOW_INSUFFICIENT` | **333.0** |
| V02 | 逾期迁徙率 30→60 | 0 / 同上 | **40.0384061449832** |
| V03 | 报案立案率 | 0 / 同上 | **100.0** |
| V04 | 不良贷款率 | 0 / 同上 | **61.253601136133085** |
| V05 | 不良率 | 拒答 `E_ANSWER_METRIC_NOT_FOUND` | 不变（检索问题，见下） |
| V06 | 拨备覆盖率 | 0 / 窗口 | **90.0** |
| V07 | 单一客户贷款集中度 | 0 / 窗口 | **19.81402214311094** |
| V08 | 今年案均赔款 | 拒答 `E_ANSWER_METRIC_NOT_FOUND` | 不变（数据问题，见下） |
| V09 | 综合赔付率 | 0 / 窗口 | **28.947368421052634** |
| V10 | 正常类贷款迁徙率 | 0 / 窗口 | **47.8055012816739** |
| V11 | 单一集团客户授信集中度 | 0 / 窗口 | **1.8000000000000003** |
| V12 | 本年客户 AUM | `E_ANSWER_FACTS_MISSING` | 仍无数：`E_ANSWER_VALUE_DEGRADED`（口径说明） |
| P01 | V01 同题钉 `FIN-BANK-001` | 0 / 窗口 | **333.0** |
| P02 | V02 同题钉 `FIN-BANK-017` | 0 / 窗口 | **40.0384061449832** |
| P03 | V03 同题钉 `FIN-INS-018` | 0 / 窗口 | **100.0** |

计数：**修复前 0/15，修复后 12/15**（9 条自由检索 + 3 条钉指标）；compute step 从 12 条 `E_METRIC_WINDOW_INSUFFICIENT` 变为 12 条 `ok`。12 条均引用真实观测行（`obsDbRows` 与 DB 计数一致，`/source/resolve` 全部 200）。

剩余 3 条逐条归因：

- **V05 检索问题**：本体未声明“不良率”，SKOS 无别名命中；最近项“不良贷款率”相似度仅 0.75。同义表述 V04 已出数（61.2536），数据与生成均正常；修法是给 `FIN-BANK-008` 注册“不良率”别名/术语。
- **V08 数据问题（口径定义缺失）**：`platform.metric_definition` 中不存在“案均赔款”指标（含“赔款”的只有未决赔款准备金 `FIN-INS-014`）。没有可检索目标，不是检索算法失败；需补指标定义与观测。
- **V12 生成/策略问题**：已选中 `CUST-012`，事实层 `covered`（5,000 行、resolve 200、`synthetic`），但该指标 `publishable=false` 且 `metric_kind=amount`，答案降级为口径说明、不给数值。**数据在，不出数属发布策略限制**。

### 10.3 triple 登记后：真实断链 0 条（原 37.74% 是度量缺陷）

| 指标 | 修复前 | 修复后 |
| --- | --- | --- |
| citations / resolvable | 53 / 33 | **53 / 53** |
| citationResolvableRate | 0.6226 | **1.0** |
| brokenLinks | 20 | **0** |
| brokenLinkRate | 0.3774（`regression=true`） | **0.0**（`regression=false`） |
| passRate | 0.6（6/10） | 0.6（不变） |

**真实断链 = 0 条**。修复前的 20 条全部是 `kind=triple`（按 `citation.kind` 统计 20/20），`ref` 是真实三元组字符串（如 `<https://w3id.org/fsldm/terms#M-FIN-BANK-001> skos:altLabel "逾期天数"`），只是该 kind 未登记而被构造性计为不可解析。登记后 53 条全部可解析。golden set 仍 6/10，那 4 条失败与 triple 无关（G02/G03 数据、G05/G06 检索）。

### 10.4 `/answer/quality`：选择「真正只读」

两个选项里选后者：保留 `readOnly=true`，改实现。`_qa_answer` 新增 `persist: bool = True`，`/answer/quality` 的 10 次内部调用一律 `persist=False`，PROV 写入条件改为 `if recorder is not None and persist`。

隔离实测（单独调用 `/answer/quality` 两次，前后各查 `platform.prov_event`）：**482 → 482 → 482，写入 0 条**，`readOnly=true` 现在名副其实。

原来会写什么：内部每次 `_qa_answer` 在拒答或口径判定时追加 1 条 PROV activity（refusal / decision）。§9 的 +58 里包含 18 次 `/answer` 与 quality 内部 10 次；本次 15 次 `/answer` 净增 15 条（这是 `/answer` 的正常行为，不受影响），quality 为 0。

### 10.5 `dataSource` 按 DB 实际值输出

- 事实层 13/13 条 covered 记录 `dataSource=synthetic`（修复前这 13 条均标为 `business`）。
- `steps.facts.output.dataSource`、`fact-observation` citation 的 `dataSource`、`compute` 输出三处均为 `synthetic`。
- DB 侧 37,471 行全部 `data_source='synthetic'`、`fixture=false`。
- `metrics.py` 的 `dataSource` 改为 `MIN(data_source) AS data_source`，不再按 `fixture` 推断 `business`。

### 10.6 引用数值与直接 `/output` 一致

`value` 与 `GET /metrics/{id}/output?compute=true&dataSource=synthetic`（正确窗口）逐位一致：

| 指标 | `/answer` 数值 | `/output` | 观测窗口 / 行数 |
| --- | --- | --- | --- |
| FIN-BANK-001 | 333.0 | 333.0 | instant 2025-12-31 / 5,000 |
| FIN-BANK-017 | 40.0384061449832 | 40.0384061449832 | 2025-01-01~2025-12-31 / 15 |
| FIN-INS-018 | 100.0 | 100.0 | 2025-01-01~2025-12-31 / 4 |

P01/P02/P03 与 V01/V02/V03 完全相同。修复后新增 `value-source` 引用（§9 时无），其 locator 与观测行一致、resolve 200。G2 `/metrics/{id}/compute` 仍是事实表直算、按实体出行：BANK-001 400 `E_METRIC_BINDING_MISSING`，BANK-017 15 个机构行（0–50.2994），INS-018 4 个险种行（各 100.0）。**一致性结论只对 `/output` 汇总口径成立**。

补记一个采集脚本缺陷（不影响结论）：`recheck_obs_2026-11-07.py` 原先给 FIN-BANK-017 的 COMPARE 窗口写成 `2025-12-31~2025-12-31`，该窗口 DB 无行，故 00:33 证据里该行 COMPARE 是 `None`/0 行。脚本已改为 `2025-01-01~2025-12-31`；正确读数见上表。

### 10.7 明确更正：旧 `q_R01` / `q_R02` 是哪两句写错了

以下两句**指名更正**。旧 md 原文保留不改；第三方报告引用的是这两句，应按本小节修正。

1. `q_R01_R-01 -answerable 分层覆盖度面板.md` 结论行原文：
   > “但 ontology / terms / facts 三层 coverageRate 基本为 0，只有 metrics 层有非零覆盖（具体数值见本页真实输出）。”

   **该句错误。** 同一文件保存的真实输出（23:52:53）已是 ontology 0.0417、terms 0.6667、facts 0.2083、metrics 0.2500。只有 ontology 接近 0；“terms 基本为 0”“facts 基本为 0”“只有 metrics 有非零覆盖”均不成立。

2. `q_R02_R-02 引用与拒答质量闭环（10 例 golden set）.md` 结论行原文：
   > “可取的是 citation 覆盖率与可解析率均为 1.0、断链率 0.0、regression=false。”

   **该句错误。** 同一文件保存的真实输出（23:52:55）已是 `citationResolvableRate=0.6226`、`brokenLinkRate=0.3774`、`regression=true`；只有 `citationCoverageRate` 是 1.0。

**生效时点**：这两份旧结论的底层数据在 **23:52 之前已经生效**（q_R01 证据 23:52:53、q_R02 证据 23:52:55），不是“之后才变”。本次 00:33 复测的 R-01 四层读数（0.0417 / 0.6667 / 0.2500 / 0.2083）与旧证据完全相同；R-02 的 0.6226 / 0.3774 也与旧证据相同。00:33 出现 0.0 断链率是 R-02-fix 登记 `triple` 后的代码结果，不是数据变化。

### 10.8 仍未修 / 仍存在的问题

- golden set passRate 0.6（6/10）不变：2 条数据（G02 `FIN-INS-021` 无观测、G03 `FIN-BANK-002` 规则无数据）+ 2 条检索/本体（G05/G06）。
- 4 条结构性可算指标仍无观测：`FIN-BANK-035`、`FIN-BANK-036-v1`、`FIN-INS-021`、`FIN-INS-025`。
- `FIN-INS-017` 仍 `E_METRIC_EVIDENCE_MISSING`（42 条唯一出数失败）。
- 10 条规则口径仍只是声明层面可出数（G03 实测 `E_METRIC_NO_DATA`）。
- instant 观测 citation 的 locator 用 `periodStart=periodEnd`，`/output` 用 `asOf`；resolve 可用但两套时间字段表达仍在。

### 10.9 复跑与单测

- 复测：`python doc/_qa/recheck_obs_2026-11-07.py`（15 条 `/answer` + 三条 COMPARE；每次会写 15 条 PROV）。
- 单测：`.venv\Scripts\python.exe -m pytest platform/tests/test_g4_retrieval.py -q` → **15 passed**（本次新增 3 条：triple 可解析、quality 不写 PROV、facts dataSource 取观测行）。

## 11 收尾复测：golden 4 条归因 + 镜像并轨重建（2026-11-07 00:47）

测量时点 **2026-11-07 00:47:35 +0800**，证据 `evidence/recheck_obs_20261107T004735.json`。§10 原文保留；其中 §10.8 的粗分类与 §10.6 关于 `/output` 的表述按本节更正。

### 11.1 集成分支与镜像重建（不再依赖 hot-patch）

- 新分支 **`feat/r-qa-integration`**：以 `luke`（`ea7c94f`，已含 D 线 `bc5c01b`/`82244bb` 的 dataSource 必填、退化窗口拒绝、computation 审计）为基，cherry-pick 四个修复：
  `9e4ca12`（R-01）、`34d8f85`（R-02）、`51d3d76`（R-03）、`5464b5c`（R-04，HEAD）。
- 唯一冲突在 `metrics.py` 的 `dataSource` 回退：D 线是 `stats["data_source"] or ("fixture" if fixture else "business")`，本线要“按 DB 实际值、不推断”，解决为 `stats["data_source"] or None`。
- 工作树 `D:\agentABC\wt\r-qa-integration` 构建时干净（无未提交改动）；单测 **15 passed**。
- 镜像 `agent-platform:0.1-s5` 重建为 `sha256:ad7732d367e3…`（首次用 `pypi.org` 拉 pydantic 失败，改用 `PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple` 成功）。
- `docker compose up -d platform` **重建**容器（Recreated，`Created=2026-11-07 00:47:20`），不是 restart。容器内四项标记核验通过：`persist` 在 `_qa_answer` 签名、`_qa_fact_eval` 用 `ds`、`MetricService.compute` 有 `data_source`、`METRIC_DATA_SOURCES` 存在。

### 11.2 新镜像复跑：12/15 与 00:33 完全一致

| 检查 | 00:33（hot-patch） | 00:47（重建镜像） |
| --- | --- | --- |
| `/answer` 出数 | 12/15 | **12/15（逐位同值）** |
| V01/V02/V03 | 333.0 / 40.0384061449832 / 100.0 | 相同 |
| V04/V05/V06 | 61.253601136133085 / 拒答 / 90.0 | 相同 |
| V07/V08/V09 | 19.81402214311094 / 拒答 / 28.947368421052634 | 相同 |
| V10/V11/V12 | 47.8055012816739 / 1.8000000000000003 / 口径说明 | 相同 |
| quality 引用 | 53/53、断链 0、passRate 0.6 | 相同 |
| `readOnly` | true | true |
| PROV（15 次 `/answer`） | +15 | +15（512→527） |
| 隔离调用 quality ×2 | 0 写入 | **0 写入（527→527）** |

结论：00:33 的结论**不依赖**容器可写层的临时修改，重建后完全可复现。

### 11.3 golden set 4 条逐条归因

四条都**不是引用问题**（53/53 可解析）。断点如下：

| ID | 问题 | 断在哪一步 | 期望 vs 实际 | 归类 |
| --- | --- | --- | --- | --- |
| G02 | 13个月继续率（有效保单件数）的口径是什么 | 检索**选中** `FIN-INS-021`（0.98），定义/公式引用齐全；facts 层 `E_FACTS_NO_OBSERVATION`（该指标 0 观测行） | 期望“非 degraded 的完整口径”；实际口径内容正确，但 `degraded=true` | **生成问题**（定义题被事实缺失连带标 degraded）+ 数据缺口（不影响定义正确性） |
| G03 | 逾期分档（M0–M6）是什么 | 检索**选中** `FIN-BANK-002`（0.98），rule-set 引用齐全（6 条规则）；facts 层 `E_FACTS_RULE_INPUTS`（无客户/账户事实输入） | 期望“非 degraded 的规则集说明”；实际说明正确，但 `degraded=true` | **生成问题**（同上）+ 数据缺口 |
| G05 | 当事人关系历史记录保留多久 | 检索命中 `Party`，但问句 span「历史记录保留多久」在本体无术语；文档 chunks=0；生成拒答 | 期望“不拒答 + ontology-version 引用”；实际 `E_ANSWER_NOT_COVERED` | **golden 期望本身不对**：本体没有“保留时长”知识，拒答是正确行为 |
| G06 | 抵押物价值发生巨大变化时银行如何处理 | 检索命中 `CollateralItem`，但「巨大变化」「处理」无术语（“处理”只出现在注释里）；文档 chunks=0；生成拒答 | 期望“不拒答 + ontology-version 引用”；实际 `E_ANSWER_NOT_COVERED` | **golden 期望本身不对**：本体不建模业务流程/处置规则，拒答是正确行为 |

补充：G02 还有一个噪声项——问句里的“口径”被当成本体缺口（`E_LAYER_ONTOLOGY_GAP`），出现在 `missing` 里，但不是本条失败的直接原因（失败只由 facts degraded 触发）。

**对 §10.8 的更正**：那里写的“2 条数据（G02/G03）+ 2 条检索/本体（G05/G06）”是粗分类，不准确。准确说法是：G02/G03 的**检索与生成内容都正确**，失败仅因 `degraded` 判定把定义题依赖事实；G05/G06 是**期望值超出本体知识范围**，拒答合理。

**没有改 golden set 期望值**。若要让 G05/G06 通过，需要补本体/文档知识（保留时长、处置流程），不是调高期望或放宽判定。

### 11.4 `/output` 与 `/compute` 的 dataSource 契约：是漏改，不是有意

> 本节是 00:47 时点的发现记录；R-05 已于 00:53 修复，当前行为见 §11.6。

- `/metrics/{id}/compute`（G2，D 线）：`dataSource` 声明为必填（`Query(...)`），缺失由校验异常映射为 400 `E_METRIC_DATA_SOURCE_REQUIRED`。
- `/metrics/{id}/output?compute=true`（**修复前**）：**签名里根本没有 `dataSource` 参数**，FastAPI 会静默忽略多余的 query；内部调 `runtime.metrics.compute(...)` 时不传 `data_source`，SQL 不过滤来源 → **跨来源汇总**。
- 实测证据：`/output?compute=true&asOf=2025-12-31&dataSource=fixture` 仍返回 `333.0` 且 `dataSource=synthetic`（参数被忽略）；同一指标 `/compute?...&dataSource=fixture` 返回 400 `E_METRIC_BINDING_MISSING`（真正按 fixture 过滤）。
- 影响：当前 DB 37,471 行全是 `synthetic`，所以两种调用读数恰好一致；一旦同一指标/窗口出现 fixture 或 business 行，`/output` 会把多来源混算，而 `/compute` 不会。这是**契约不一致的漏改**，不是设计取舍。
- 修正 §10.6 的表述：当时“`/output?...&dataSource=synthetic`”里的参数并未生效，只是 DB 全 synthetic 使结果相同。`/answer` 自身走 `MetricService.compute` 并**显式传** `data_source`，不受此问题影响。
- 建议二选一（未擅自改）：给 `/output?compute=true` 增加必填 `dataSource` 并与 `/compute` 共用枚举；或明确把 `/output` 定义为“跨来源汇总”并写进 OpenAPI 描述。需要我补的话，按 R-05 单独提交。
- **已按选项一修复（R-05）**：`/output?compute=true` 现在要求显式 `dataSource`，缺失同码 400，且真正下传过滤。见 §11.6。

### 11.5 复跑

- `docker compose up -d platform`（重建后）→ `python doc/_qa/recheck_obs_2026-11-07.py`。
- 集成分支单测：`pytest platform/tests/test_g4_retrieval.py -q` → 15 passed。

### 11.6 R-05：`/output?compute=true` 的 dataSource 契约对齐（2026-11-07 00:53）

**实现**（`feat/r-qa-integration`，commit `R-05`）：

- `GET /metrics/{id}/output` 新增 `dataSource` query（`alias="dataSource"`，OpenAPI 可见；描述写明 `compute=true` 时必填、`compute=false` 时忽略）。
- `compute=true` 且缺失时，主动抛 `PortError`：400 `E_METRIC_DATA_SOURCE_REQUIRED`，`message` 与 `/compute` 同为 `dataSource is required; allowed: fixture, business, synthetic`，`details={metricId, field:"dataSource", allowedDataSources:["fixture","business","synthetic"]}`。
- 传入值真正下传 `runtime.metrics.compute(..., data_source=data_source)`，`MetricService.compute` 的 SQL 追加 `AND data_source = %s`；`metric_computation` 审计行也记录显式传入的 `dataSource`。
- `compute=false` 分支提前返回定义卡，不读 `dataSource`，行为与之前完全一致。

**受影响调用方清单**：

| 位置 | 影响 | 处理 |
| --- | --- | --- |
| `doc/_qa/recheck_obs_2026-11-07.py`（COMPARE） | `/output?compute=true` 已带 `dataSource=synthetic` | 无需改 |
| `doc/_qa/recheck_outputs_2026-11-07.py` | 已带 `dataSource=synthetic` | 无需改 |
| `platform/web/browse_urls.js` 的 `/output` 链接 | 不带 `compute=true`，走定义卡 | 无需改 |
| `platform/tests/test_g2_metrics_core.py` | 只走 `/compute`，不走 `/output?compute=true` | 无需改 |
| `doc/_design/46`、`48`、`58`、`68` | 示例/错误码/参数说明缺 `dataSource` | 已补 `&dataSource=synthetic`，错误码与契约行已更新 |

**自测**：

- 单测：`pytest platform/tests/test_g4_retrieval.py -q` → **16 passed**（新增 1 条：缺失 400 + details、传入值下传、`compute=false` 走定义卡且不调 compute）。
- 重建镜像 `sha256:715d59e8f286…`，`docker compose up -d platform` 重建容器（`Created 00:53:19`）。
- 实测：
  - `GET /metrics/FIN-BANK-001/output?compute=true&asOf=2025-12-31` → **400**，`providerCode=E_METRIC_DATA_SOURCE_REQUIRED`，`allowedDataSources=["fixture","business","synthetic"]`。
  - 同请求 + `dataSource=synthetic` → **200**，`value=333.0`，`dataSource=synthetic`，`computationRef` 有值。
  - 同请求 + `dataSource=fixture` → **400 `E_METRIC_NO_DATA`**（证明过滤真实生效，不再是跨来源汇总）。
  - `GET /metrics/FIN-BANK-001/output`（不带 compute，带不带 `dataSource` 都一样）→ **200 定义卡，无 `value`**。
  - OpenAPI 的 `/metrics/{metric_id}/output` 已出现 `dataSource` 参数。
- 回归：15 条 `/answer` 复跑 → **12/15 逐位同值**（证据 `evidence/recheck_obs_20261107T005340.json`，`provEvent 527→542`，仅 15 次 `/answer` 写入）。
- 未改 G02/G03 的 `degraded` 生成逻辑（仅记录，按指示不动）。
