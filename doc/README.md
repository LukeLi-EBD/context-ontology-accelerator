# COA 文档汇总

本目录汇总 `D:\agentABC` 下所有以 `_` 开头的目录中的 Markdown 文档，保留原始相对目录结构。`_impl` 的运行时数据（`_impl/data` 下的测试语料与导出产物）不在汇总范围内。原始文件未做任何修改；密钥类内容仅在本副本中脱敏。

- 汇总时间：2026-11-05 16:33:43（**快照**）
- 文档数：65（**本索引仅覆盖首批 65 篇，不代表当前全量**）
- 已脱敏文档数：2
- 跳过 md 数：74

> **索引范围声明（2026-11-06 回写）**：`coa/doc/` 下实际 Markdown 于 2026-11-06 首次抽查为 **211 篇**（含本 README），同日晚复核为 **249 篇**（其他会话持续新增）；下表 65 条是 2026-11-05 16:33 的首批快照，**未覆盖其余 184 篇**。查全路径：`Get-ChildItem doc -Recurse -Filter *.md`，或按目录查看 `_design/`、`_fsldm/`、`_arch/`、`_impl/`、`evidence/`。原文“文档数 65”保留为历史快照值，不回写为全量。

## 索引

| 序号 | 来源路径 | 标题 | 行数 | 备注 |
| --- | --- | --- | --- | --- |
| 1 | `_arch/01-airflow-架构.md` | [Apache Airflow 架构笔记](_arch/01-airflow-架构.md) | 575 |  |
| 2 | `_arch/02-dolphinscheduler-架构.md` | [Apache DolphinScheduler 架构笔记](_arch/02-dolphinscheduler-架构.md) | 477 |  |
| 3 | `_arch/03-Taier-架构.md` | [袋鼠云 Taier（Dtstack）架构笔记](_arch/03-Taier-架构.md) | 521 |  |
| 4 | `_arch/04-seatunnel-架构.md` | [Apache SeaTunnel 架构笔记](_arch/04-seatunnel-架构.md) | 537 |  |
| 5 | `_arch/05-canal-架构.md` | [阿里巴巴 Canal 架构笔记](_arch/05-canal-架构.md) | 547 |  |
| 6 | `_arch/06-dbt-架构.md` | [dbt v2.0（Fusion 引擎）架构笔记](_arch/06-dbt-架构.md) | 564 |  |
| 7 | `_arch/07-metricflow-架构.md` | [MetricFlow 架构笔记](_arch/07-metricflow-架构.md) | 507 |  |
| 8 | `_arch/08-debezium-架构.md` | [Debezium 架构笔记](_arch/08-debezium-架构.md) | 551 |  |
| 9 | `_arch/09-parser-架构.md` | [bytebase/parser 架构笔记（多方言 SQL 解析器集合）](_arch/09-parser-架构.md) | 393 |  |
| 10 | `_arch/10-altimate-code-架构.md` | [Altimate Code 架构笔记](_arch/10-altimate-code-架构.md) | 641 |  |
| 11 | `_arch/11-QwenPaw-Data-架构.md` | [QwenPaw-Data 架构笔记](_arch/11-QwenPaw-Data-架构.md) | 493 |  |
| 12 | `_arch/12-hermes-agent-架构.md` | [hermes-agent 架构笔记](_arch/12-hermes-agent-架构.md) | 739 |  |
| 13 | `_arch/13-deepseek-harness-架构.md` | [deepseek-harness 架构笔记](_arch/13-deepseek-harness-架构.md) | 755 |  |
| 14 | `_arch/14-dsh-superagent-prototype-架构.md` | [dsh-superagent 原型架构](_arch/14-dsh-superagent-prototype-架构.md) | 636 |  |
| 15 | `_arch/15-nanobot-架构.md` | [nanobot 架构笔记](_arch/15-nanobot-架构.md) | 428 |  |
| 16 | `_arch/16-pi-架构.md` | [pi（coding-agent）架构笔记](_arch/16-pi-架构.md) | 646 |  |
| 17 | `_arch/17-redshift-parser-架构.md` | [Redshift Parser 架构笔记（单方言 ANTLR4 SQL 解析器）](_arch/17-redshift-parser-架构.md) | 533 |  |
| 18 | `_arch/18-sutskever-30-implementations-架构.md` | [sutskever-30-implementations 架构笔记](_arch/18-sutskever-30-implementations-架构.md) | 289 |  |
| 19 | `_arch/19-wx2kb-架构.md` | [wx2kb 架构笔记](_arch/19-wx2kb-架构.md) | 196 |  |
| 20 | `_arch/REVIEW-已有文档-审查报告.md` | [`_arch` 已有架构文档审查报告（源码核验版）](_arch/REVIEW-已有文档-审查报告.md) | 250 |  |
| 21 | `_design/01-云中立架构方案.md` | [云中立平台架构方案（AWS 优先 / 可自建）](_design/01-云中立架构方案.md) | 1491 | ⚠ 已脱敏 |
| 22 | `_design/02-接口契约清单.md` | [接口契约清单（端口 / IDL / 能力矩阵）](_design/02-接口契约清单.md) | 1331 |  |
| 23 | `_design/03-单机架构方案.md` | [单机架构方案（Single-Box First）](_design/03-单机架构方案.md) | 1612 |  |
| 24 | `_design/04-单机接口契约.md` | [单机接口契约（端口 / IDL / 能力矩阵）](_design/04-单机接口契约.md) | 1532 |  |
| 25 | `_design/05-运行形态与推理选型.md` | [运行形态与推理选型](_design/05-运行形态与推理选型.md) | 311 |  |
| 26 | `_design/06-实现候选矩阵.md` | [本机实现候选矩阵](_design/06-实现候选矩阵.md) | 235 |  |
| 27 | `_design/07-存储分层实现方案.md` | [存储分层实现方案](_design/07-存储分层实现方案.md) | 491 |  |
| 28 | `_design/08-云中立方案复评.md` | [云中立方案复评（对照 03–07 单机方案）](_design/08-云中立方案复评.md) | 92 |  |
| 29 | `_design/09-需求对照与一致性复查.md` | [需求对照与一致性复查](_design/09-需求对照与一致性复查.md) | 131 |  |
| 30 | `_design/10-实施路线图.md` | [实施路线图（S0–S13）](_design/10-实施路线图.md) | 222 |  |
| 31 | `_design/18-burst窗口-计划.md` | [18-burst 窗口 · 立即执行版（S14H-BURST）](_design/18-burst窗口-计划.md) | 134 |  |
| 32 | `_design/19-burst窗口-复盘.md` | [19-burst 窗口 · 复盘（S14H-BURST）](_design/19-burst窗口-复盘.md) | 110 |  |
| 33 | `_design/a_progress.md` | [平台实施进度看板](_design/a_progress.md) | 174 |  |
| 34 | `_design/ark-embedding-probe.md` | [火山方舟 Coding Plan Embedding 接口探测报告](_design/ark-embedding-probe.md) | 242 |  |
| 35 | `_design/impl/S0-骨架-设计.md` | [S0 骨架设计（可启动的最小单机内核）](_design/impl/S0-骨架-设计.md) | 371 |  |
| 36 | `_design/impl/S10-可逆裁决与审计回放-设计.md` | [S10 可逆裁决与审计回放 · 设计](_design/impl/S10-可逆裁决与审计回放-设计.md) | 171 |  |
| 37 | `_design/impl/S11-T-Box变更治理-设计.md` | [S11 T-Box 变更治理 · 设计](_design/impl/S11-T-Box变更治理-设计.md) | 200 |  |
| 38 | `_design/impl/S12-完整性收口-设计.md` | [S12 · 完整性收口（设计）](_design/impl/S12-完整性收口-设计.md) | 136 |  |
| 39 | `_design/impl/S13-批量入库-设计.md` | [S13 · 批量入库（目录导入）（设计）](_design/impl/S13-批量入库-设计.md) | 259 |  |
| 40 | `_design/impl/S1-本体存储与版本-设计.md` | [S1 本体存储与版本 · 设计](_design/impl/S1-本体存储与版本-设计.md) | 284 |  |
| 41 | `_design/impl/S2-文档入库-设计.md` | [S2 文档入库 · 设计](_design/impl/S2-文档入库-设计.md) | 344 |  |
| 42 | `_design/impl/S3-检索-设计.md` | [S3 检索 · 设计](_design/impl/S3-检索-设计.md) | 283 |  |
| 43 | `_design/impl/S4-抽取到实例-设计.md` | [S4 抽取到实例 · 设计](_design/impl/S4-抽取到实例-设计.md) | 301 |  |
| 44 | `_design/impl/S5-校验与物化-设计.md` | [S5 校验与推理物化 · 设计](_design/impl/S5-校验与物化-设计.md) | 387 |  |
| 45 | `_design/impl/S6-Context组装-设计.md` | [S6 Context 组装 · 设计](_design/impl/S6-Context组装-设计.md) | 200 |  |
| 46 | `_design/impl/S7-最小WebUI-设计.md` | [S7 最小 Web UI · 设计](_design/impl/S7-最小WebUI-设计.md) | 161 |  |
| 47 | `_design/impl/S8-ABox撤回与事实治理-设计.md` | [S8 A-Box 撤回与事实治理 · 设计](_design/impl/S8-ABox撤回与事实治理-设计.md) | 145 |  |
| 48 | `_design/impl/S9-冲突裁决与审计导出-设计.md` | [S9 冲突裁决与审计导出 · 设计](_design/impl/S9-冲突裁决与审计导出-设计.md) | 115 |  |
| 49 | `_design/res-health-1138.md` | [实时资源体检报告（res-health-1139）](_design/res-health-1138.md) | 284 |  |
| 50 | `_design/外部算力-BGE-M3-可行性.md` | [外部算力跑自建 BGE-M3 可行性（"只借算力、不借模型"）](_design/外部算力-BGE-M3-可行性.md) | 129 |  |
| 51 | `_digest/AI-Agent核心摘要.md` | [D:\AgentABC 里的 AI 项目：核心代码摘要 + 最简版内核](_digest/AI-Agent核心摘要.md) | 469 | ⚠ 已脱敏 |
| 52 | `_digest/SuperAgent-原型对照分析.md` | [DeepSeek Super-agent 原型：代码 vs 文章 对照分析](_digest/SuperAgent-原型对照分析.md) | 371 |  |
| 53 | `_fsldm/00-口径基准-v1.md` | [口径基准 v1](_fsldm/00-口径基准-v1.md) | 359 |  |
| 54 | `_fsldm/01-指标卡/_research/A-银行信贷监管口径.md` | [中国银行业信贷类监管口径调研（来源可核查版）](_fsldm/01-指标卡/_research/A-银行信贷监管口径.md) | 472 |  |
| 55 | `_fsldm/01-指标卡/_research/B-保险与客户经营口径.md` | [B-保险与客户经营口径调研（来源可核查版）](_fsldm/01-指标卡/_research/B-保险与客户经营口径.md) | 904 |  |
| 56 | `_fsldm/01-指标卡/_research/C-OneData方法论.md` | [C - 阿里巴巴 OneData 方法论（面向指标口径治理的抽取）](_fsldm/01-指标卡/_research/C-OneData方法论.md) | 410 |  |
| 57 | `_fsldm/02-导入验证/S14-阶段一-报告.md` | [S14 阶段一报告：FS-LDM 本体导入与口径自洽](_fsldm/02-导入验证/S14-阶段一-报告.md) | 297 |  |
| 58 | `_fsldm/02-导入验证/指标可计算性矩阵.md` | [指标可计算性矩阵（S14 阶段一 · 第三步）](_fsldm/02-导入验证/指标可计算性矩阵.md) | 131 |  |
| 59 | `_fsldm/03-口径验证/S14-H-02-报告.md` | [S14-H-02 报告：指标口径可计算性验证（三轮）](_fsldm/03-口径验证/S14-H-02-报告.md) | 120 |  |
| 60 | `_fsldm/04-决策与争议.md` | [决策与争议](_fsldm/04-决策与争议.md) | 97 |  |
| 61 | `_impl/OPEN-QUESTIONS.md` | [开放问题台账（S0–S11）](_impl/OPEN-QUESTIONS.md) | 107 |  |
| 62 | `_impl/README.md` | [本体平台 · 上手指南](_impl/README.md) | 240 |  |
| 63 | `_impl/WORKLOG.md` | [WORKLOG · 实施留痕账本](_impl/WORKLOG.md) | 603 |  |
| 64 | `_refs/fsldm-inventory.md` | [FS-LDM 资产清点与导入可行性初判（只读盘点）](_refs/fsldm-inventory.md) | 295 |  |
| 65 | `_refs/tika-coa-核查.md` | [Tika 与 COA 文档解析链路核查（2026-11-04）](_refs/tika-coa-核查.md) | 52 |  |

## 脱敏清单

以下文件的副本已脱敏，原始文件未改动；表中不列出密钥原文。

| 文档 | 命中模式 | 命中行数 |
| --- | --- | --- |
| [_design/01-云中立架构方案.md](_design/01-云中立架构方案.md) | postgres:// 密码段×1 | 1 |
| [_digest/AI-Agent核心摘要.md](_digest/AI-Agent核心摘要.md) | password/token/secret/api_key 赋值×1 | 1 |

## 40 位十六进制命中（经核对为 commit SHA / 哈希 / 请求 id，非密钥，未脱敏）

扫描器按 40 位十六进制规则命中以下位置，经逐条核对均为 git commit SHA、cutoff hash 或请求 id，不构成密钥，因此保留原样。

| 来源路径 | 行数 |
| --- | --- |
| `_arch/01-airflow-架构.md` | 5 |
| `_arch/02-dolphinscheduler-架构.md` | 7 |
| `_arch/03-Taier-架构.md` | 7、497 |
| `_arch/04-seatunnel-架构.md` | 7、531 |
| `_arch/05-canal-架构.md` | 7 |
| `_arch/06-dbt-架构.md` | 7、549 |
| `_arch/07-metricflow-架构.md` | 7 |
| `_arch/08-debezium-架构.md` | 7 |
| `_arch/09-parser-架构.md` | 7 |
| `_arch/11-QwenPaw-Data-架构.md` | 7 |
| `_arch/12-hermes-agent-架构.md` | 6、703、732 |
| `_arch/13-deepseek-harness-架构.md` | 6 |
| `_arch/15-nanobot-架构.md` | 6 |
| `_arch/17-redshift-parser-架构.md` | 8 |
| `_arch/18-sutskever-30-implementations-架构.md` | 6 |
| `_design/ark-embedding-probe.md` | 102 |

## 跳过文件

以下 md 未纳入汇总。

| 来源路径 | 原因 |
| --- | --- |
| `_impl/data/corpus-s13/generated/renamed-copy-1.md` | 位于 `_impl/data`，属于运行时测试语料与导出产物，按要求不触碰 `_impl` 运行时数据 |
| `_impl/data/corpus-s13/generated/renamed-copy-2.md` | 位于 `_impl/data`，属于运行时测试语料与导出产物，按要求不触碰 `_impl` 运行时数据 |
| `_impl/data/corpus-s13/generated/renamed-copy-3.md` | 位于 `_impl/data`，属于运行时测试语料与导出产物，按要求不触碰 `_impl` 运行时数据 |
| `_impl/data/corpus-s13/generated/renamed-copy-4.md` | 位于 `_impl/data`，属于运行时测试语料与导出产物，按要求不触碰 `_impl` 运行时数据 |
| `_impl/data/corpus-s13/generated/renamed-copy-5.md` | 位于 `_impl/data`，属于运行时测试语料与导出产物，按要求不触碰 `_impl` 运行时数据 |
| （同类共 74 个，仅列前 5 个） | 位于 `_impl/data`，属于运行时测试语料与导出产物，按要求不触碰 `_impl` 运行时数据 |
