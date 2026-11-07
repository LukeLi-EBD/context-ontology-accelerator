# `_qa` 验收报告 verdict 重判对照（证据推导版）

- 文档性质：**独立重判**，不修改、不覆盖 `doc/_qa/` 下任何原始报告与证据。
- 原始对象：`doc/_qa/run_qa.py` 及 `doc/_qa/evidence/q_<编号>.txt`（采集时间均为 **2026-11-06 23:5x +08**）。
- 上游审计：`doc/_evidence-audit/qa_reason_audit.md`（只核对 reason 与证据，结论 一致 22 / 不一致 14 / 无法核实 1）。
- 本文关系：
  - 上游审计回答的是“reason 有没有说错”；
  - 本文回答的是“**verdict 该不该这么判**”，并按用户要求把 15 条问题条目定性为文案错 / 判定逻辑错 / 已修复 / 不可采信；
  - 两者冲突时，以本文的“由证据字段重新推导”结果为准；原始 `verdict`/`reason` 仅作为历史记录引用。
- 本文没有沿用任何一条原始 `verdict`/`reason` 作为结论；`reason` 只作为“待核对的断言”列出。

---

## 0. 结论先行（分布）

| 新分类 | 数量 | 含义 |
| --- | --- | --- |
| 一致 | **22** | 原始 verdict 与 reason 的关键断言均能被证据字段支持 |
| 文案错 | **5** | verdict 方向仍成立，但 reason 描述的具体数值/状态与证据相反（采集正确、描述错误） |
| 判定逻辑错 | **6** | reason 的取值/对比口径错误，且**直接导致 verdict 判错**（verdict 需改） |
| 已修复 | **1** | 采集时确实失败（verdict 原判 PASS 不成立），在 `8b3f36f` 基线上复测已恢复 |
| 不可采信 | **3** | 证据被 200KB 静默截断，关键断言不可核对；**不给通过判定** |
| 合计 | **37** | |

与上游审计的映射：`14 条不一致` = 文案错 5 + 判定逻辑错 6 + 已修复 1 + 不可采信 2（`q_S01`、`q_S11`）；`1 条无法核实`（`q_S09`）→ 不可采信。合计 15 条问题条目，其中不可采信共 3 条。

---

## 1. 基线声明（当前状态部分以此为准）

### 1.1 代码基线

| 项 | 值 | 证据 |
| --- | --- | --- |
| 远端 | `luke` = `git@github.com:LukeLi-EBD/context-ontology-accelerator.git` | `git remote -v` |
| HEAD | `8b3f36f898c701c56e1901c5af4925c99db22ce9` | 本地仓库 `D:\agentABC\coa` |
| 提交时间 | 2026-11-07 05:54:15 +08 | `git show 8b3f36f` |
| 改动范围 | 仅 `scripts/push-queue.ps1`（+27 行误报豁免），**无产品代码** | `git show --stat 8b3f36f` |
| 代码等价点 | `5386a04`（2026-11-07 05:41:24 +08）；两者之间的 `4172e7c` 仅新增验收日志与文档 | `git show --stat 4172e7c` |

因此：验收镜像虽在 05:45:09 构建，但代码内容等价于 `8b3f36f`。

### 1.2 验证栈

| 项 | 值 |
| --- | --- |
| 栈 | `platform-acceptance`（独立验收栈），API `127.0.0.1:8082` |
| 镜像 | `agent-platform:0.1-s5`，Created **2026-11-06T21:45:09Z = 2026-11-07 05:45:09 +08** |
| 容器 | `platform-acceptance-api` Started **2026-11-07 05:45:36 +08**，本次复测期间未重启 |
| 健康 | `/readyz` 200：database/graph/storage 全 ok；tbox/current = `ont-6e81732555e5`，3340 triples，updatedBy=`smoke-restore`，updatedAt=`2026-11-07T05:51:38+08` |
| 图库 | `/prov/verify` 200，`checked=12`，`separation.ok=true`，`provTriples=319`，`tboxProvTriples=0`，`provTboxTriples=0`，`tboxLegacyProvPredicateTriples=0` |
| 422/422 | `doc/evidence/acceptance-s14-platform-acceptance-20261107-055018-5386a04.log:481`：discovered 422 / executed 422 / passed 422 / failed 0 / skipped 0，时间 **2026-11-07 05:50 +08** |
| S0–S13 套件 | `acceptance-s0s13-platform-acceptance-20261107-054610-5386a04.log:1024`：passed=44 failed=0 skipped=0，时间 **2026-11-07 05:49 +08** |

**是否空库**：建栈与验收运行是全新库（`747804f` 明确“去掉对共享栈历史状态的依赖，全新库可全绿”）；但 422/422 跑完后留下了本轮测试数据，因此本次复测读到的是“**验收后残留小库，不是字面空库**”：

| 表 | 行数 | 表 | 行数 |
| --- | --- | --- | --- |
| document | 39 | metric_definition | 85 |
| document_chunk | 41 | metric_observation | **0** |
| chunk_embedding | 34 | fact_event | 97 |
| extraction_candidate | 8 | fact_assertion | **0** |
| import_item | 0 | term_import | **0** |
| data_dictionary | 79 | ontology_event | 103 |

**数据栈 `agent-platform`（8080）不作为当前状态依据**：其镜像 `715d59e8f286` Created **2026-11-07 00:53:14 +08**，早于本轮 `01:06–05:41` 的修复提交；它只用于解释“原始证据采集时的旧环境”，不能用于证明 `8b3f36f` 的行为。

### 1.3 判定口径（本文自定义，先定义再使用）

| 分类 | 判定条件 |
| --- | --- |
| 一致 | 原始 verdict 的成立/不成立方向，能被证据文件中的字段直接支持；reason 的关键数值/状态也与之一致 |
| 文案错 | 证据本身正确，verdict 方向也仍成立；但 reason 中的具体数值/状态被同一份证据反证（含停留在旧版本、提前写成修复后的值两种情况） |
| 判定逻辑错 | reason 所用的取值路径/对比口径错误（读错图、错层、错端点、把分页子集当全量、把不同版本混为一谈），且**按证据重推会改变 verdict** |
| 已修复 | 采集时证据确实显示失败，原 verdict 不成立；在 `8b3f36f` 基线上按同一端点复测已恢复 |
| 不可采信 | 响应体超过 200KB 被采集器静默截断，关键字段/全量不可见，无法判定；**不给通过判定** |

---

## 2. 37 条逐条重判

> “新判定”一律指**按采集证据重新推导**的结果；“与原始判定是否一致”比较的是 verdict 方向，不是 reason 文字。
> 证据值均来自 `doc/_qa/evidence/q_<编号>.txt`；当前复测值另标时间与栈，见第 4 节。

### 2.1 A 组：新判定与原始一致（22 条）

| # | 编号 | 原始 verdict | 原始 reason（原文） | 证据实际值（关键字段） | 新判定 | 与原始一致？ |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | q_S00 | PASS | 三项健康端点均为 200，database/graph/storage 全 ok；providers 声明 metadata=postgres、graph=oxigraph-http，与 docker compose 实际服务一致。 | `/readyz` 200 三项 ok；`/status` 200 providers=postgres、oxigraph-http | PASS | 一致 |
| 2 | q_S02 | PASS | 三层计数同量级、/documents 的 total 与库一致，向量覆盖率接近 100%（具体数值见本页真实输出）。 | document=3039、chunk=15191、embedding=15120；`/documents` total=3039；覆盖率 99.53% | PASS | 一致 |
| 3 | q_S03 | PASS | 双路召回与 RRF 参数均按设计返回，degraded=false，结果非空。 | mode=hybrid、rrfK=60、routes=vector+lexical、degraded=false、results=3 | PASS | 一致 |
| 4 | q_S06 | PARTIAL | 端点 200 并返回完整包结构，但 terms / entities / facts 均为空数组，chunks 有内容；即当前组装主要靠检索片段，本体与事实层未参与。 | terms=0、entities=0、facts=0、chunks=7、citations=7 | PARTIAL | 一致 |
| 5 | q_S07 | PASS | 四个原生页面全部 200 并返回 HTML 内容。 | 4 个端点均 200，1374/11388/2629/2439 bytes，均 `<!doctype html>` | PASS | 一致 |
| 6 | q_S12 | PASS | 影响分析、导出、证据包三端点齐全且返回结构化字段。 | impact 200（changeSet/affected/aggregations/verification/inputsFingerprint）；export 200 2078B；evidence 200 count=50 | PASS | 一致 |
| 7 | q_S14 | PARTIAL | 老的 /output?compute=true 主路径确实能出数：返回 value、unit、口径版本、窗口、sampleCount、dataSource=synthetic 与可解析的 sourceRef；观测表在审计期间被并行开发线回填，不再是空表。但 G2 新增的 /compute 端点默认 dataSource=fixture，默认调用仍 rows=[] / noData=true，必须显式传 dataSource=synthetic 才出数。同一指标存在两条出数路径且默认参数互不兼容。 | value=61.2536 %、v3.0、window=2025-12-31、sampleCount=20、dataSource=synthetic、sourceRef rowCount=20；`/compute` 默认 rowCount=0/noData=true；synthetic rowCount=20；metric_observation=37471 | PARTIAL | 一致 |
| 8 | q_O01 | PASS | 375 行字典、四个视图可用，mappable_unbound 视图存在且可分页；57 号文档主动写明「97.53% 是 79/81 可映射列口径，按 375 总列计仅 21.1%，未为达标扩大分母」，口径诚实。 | data_dictionary=375；catalog total=375；all/unbound(339)/mappable_unbound(45) 均 200 | PASS | 一致（文档引述无原文，附注） |
| 9 | q_O02 | PARTIAL | 状态流与治理事件可读、事件量级与 /ontology/verify 的 checked 一致；但「非法迁移被拒」「每状态 actor/reason/time」属于写路径判定，只读验证无法触发，只能确认结构存在。 | flow count=24；ontology_event=10020；q_S01 `/ontology/verify` checked=10020 | PARTIAL | 一致 |
| 10 | q_O03 | PASS | 影响分析字段完整、带 inputsFingerprint，导出端点返回文本。 | impact 200 字段齐全；export 200 2078B | PASS | 一致 |
| 11 | q_O04 | PARTIAL | 证据包端点可用且对非法路径给出明确拒绝；但「每次发布都生成含 3 项 verdict 与 hash 的包」需触发发布写路径，只读侧只能确认结构。 | evidence 200 count=50；`inspect?path=__qa_probe__` 400 E_BUNDLE_MANIFEST | PARTIAL | 一致 |
| 12 | q_O06 | PASS | 类/属性级聚合、状态流、两版本快照与空态说明均按判据返回。 | diff 200 counts + 四次空数组；flow count=24；snapshot from/to/delta；aggregations.byClass 存在 | PASS | 一致 |
| 13 | q_M01 | FAIL | 默认参数下 8 条全部 rowCount=0 / noData=true，0 条满足「非空且可复算」；换成 dataSource=synthetic 后 FIN-BANK-008 才返回非空 rows（见本页真实输出）。FIN-BANK-001 正确返回 E_METRIC_BINDING_MISSING（这一条符合「不冒充可算」的要求）。 | 8 条 `/compute` 均 rowCount=0/noData=true；synthetic 008 rowCount=20；FIN-BANK-001 返回 E_METRIC_BINDING_MISSING；事实表 data_source=synthetic 5020 | FAIL | 一致（**现状已在 8b3f36f 修复**，见 4.2） |
| 14 | q_M02 | PASS | 85 行 100% 覆盖、字段齐全，JSON 与 CSV 同源，meta 明确给出 publishable / externalEligible 等聚合口径（数值见本页真实输出）。 | count=85/items=85；meta publishable=60、industry=46、regulatory=39、externalEligible=35；CSV 16 列 172 行 | PASS | 一致（“同源”附注） |
| 15 | q_M03 | PASS | 族索引与口径卡列表均可读，guidance 字段存在。 | families count=3，guidance 含 code/message/howTo；`/browse/metrics` count=85 | PASS | 一致 |
| 16 | q_M05 | PASS | 全部 industry 口径 100% 带 internalNotice；其中 publishable=true 的那部分 externalEligible 全为 false、externalStatus=internal_baseline，确实被排除在对外清单之外（分组计数见本页真实输出）。 | industry=46 全部带 internalNotice；publishable=24 的 externalEligible 全 false | PASS | 一致 |
| 17 | q_M06 | PASS | counts 与 58 号完全一致（16/1/3，共 20），筛选与 CSV 导出均可用，registered_only 条目带具体原因说明。 | counts 16/1/3、count=20；kind=rule count=11；CSV 200 | PASS | 一致 |
| 18 | q_R04 | PASS | 跳转模板与稳定 URL 已注册且标记 readOnly。 | stable=true、readOnly=true、writeOperations=0、paths=4、templates 4 | PASS | 一致 |
| 19 | q_R05 | OFF | 两次均返回 503 E_CANVAS_DISABLED（canvas is disabled: canvas.provider=off）。源码 config.py:60 确认 CanvasConfig.provider 默认 'off'，53 号文档允许「同一接口、两个实现、配置切换」，因此这是设计内的默认关闭，不是功能缺失。 | 两次 503 E_CANVAS_DISABLED（canvas.provider=off） | OFF | 一致（源码断言附注） |
| 20 | q_B03 | PASS | 实体页 200 且 0.1s 内返回，邻居端点正常：上一轮「B-03 未重建镜像 / 实体页超时」的问题已被并行开发线修复。 | entity 200/30ms；neighbors 200/10ms、graphs=3 | PASS | 一致（“上轮已修复”附注） |
| 21 | q_P01 | FAIL | 推理器只读 urn:platform:graph:abox:main，看板同时读 abox:main + abox:synthetic，而真实实例绝大多数在 abox:synthetic。三方对「哪个图是 A-Box」没有唯一权威，物化产物数量极少（见 q_S05 的 pointer.inferred）。 | reasoning aboxGraphs=[abox:main]；dashboard instances=60525、graphs 双图；synthetic=304919；pointer.inferred=1171 | FAIL | 一致 |
| 22 | q_P03 | PASS | 有效 obs/doc 引用均解析出 targetTable 与行定位，不存在的引用返回 400 E_SOURCE_REF_NOT_FOUND，PROV 哈希链 ok=true 且 T-Box/PROV 图分离成立。更早的基线时刻（观测表为 0 行、注册表残留 src://obs* 引用）同一 obs 引用返回 E_SOURCE_REF_STALE「ref was issued but its source row is gone」，即失效与不存在被区分成两种错误码。 | obs_rows=37471、obs_refs=316；obs/doc 均 200/found；负向 400 E_SOURCE_REF_NOT_FOUND；`/prov/verify` 200 ok=true checked=382、separation 存在 | PASS | 一致（“更早基线”附注） |

### 2.2 B 组：需定性（15 条）

| # | 编号 | 原始 verdict | 原始 reason（原文） | 证据实际值（关键字段） | 新判定（按采集证据） | 与原始一致？ | 定性 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 23 | q_S01 | PARTIAL | 版本枚举为千条量级、审计链 ok=true 均成立；但审计期间 graph_pointer 的 tbox/current 被外部 smoke-restore 反复改写，且与 /reasoning/status、/ontology/terms/coverage 使用的版本不同，见 q_P02。 | `/ontology/versions` 状态行 211969 bytes，留存体仅 200001（截断）；`/ontology/verify` ok=true checked=10020 prov.ok=true(373)；graph_pointer source=smoke-restore updatedAt=23:51:26；q_P02 显示 reasoning pointer 与 terms graph **同为** `ont-11f92ebb3326` | **不可采信**（证据不完整） | 无法判定 | 不可采信（可见部分已反证“版本不同”，但版本枚举主体被截断） |
| 24 | q_S04 | PASS | 候选表与两个端点计数一致（918 条量级），状态字段可读。 | `/candidates` count=100；`/ui/api/candidates` count=50（state=pending）；DB `extraction_candidate`=942；两端点均无 total | **PARTIAL** | **不一致** | 判定逻辑错 |
| 25 | q_S05 | PARTIAL | shapes 与 reasoner 服务可用、SHACL conforms=true；但 inferenceFailures 历史累计非零（见本页真实输出，最近一次作业状态可能为 succeeded），且 reasoning 的 aboxGraphs 只有 urn:platform:graph:abox:main，未包含真实数据所在的 abox:synthetic。 | `lastJob.state=failed`（E_REASONER_UNAVAILABLE）；inferenceFailures=333；conforms=true 来自 2025-11-05T22:10:54 的导入记录；aboxGraphs=[abox:main] | PARTIAL | 一致（verdict） | **文案错**（“可能 succeeded”与 failed 相反） |
| 26 | q_S08 | PARTIAL | 事件账本有近万条历史、端点与冲突结构可读；但 fact_assertion 长期为 0 / 个位数、/facts items 近乎为空（审计期间并行线写入了少量断言），断言层基本处于空库状态，撤回/冲突能力难以在当前数据上演示。 | fact_event=10049；fact_assertion=**0**；`/facts` count=0、items=[]；conflicts=0 | PARTIAL | 一致（verdict） | **文案错**（“写入了少量断言”与 0 相反） |
| 27 | q_S10 | PASS | PROV 链 ok=true、T-Box/PROV 图分离 ok=true、legacy 谓词 0；本体事件链 checked 为近万量级且 ok=true。 | `/prov/verify` **503 E_GRAPH_UNAVAILABLE**（8057ms，“Temporary failure in name resolution”），无 separation/legacy 字段；`/ontology/verify` 200 ok=true checked=10020 | **PARTIAL**（采集时） | **不一致** | **已修复**（当前 200，见 4.1） |
| 28 | q_S11 | PASS | 提案/事件/状态流三类治理对象均可查询，states 覆盖生命周期。 | flow 200：count=24、`states=["published","superseded"]`；proposals 2.87MB、events 601KB，各截断于 200001 | **不可采信**（证据不完整） | 无法判定 | 不可采信（可见 flow 已反证“覆盖生命周期”，但两类主体被截断） |
| 29 | q_S13 | PASS | 批次、条目、失败列表均可读，条目数与库一致。 | `/imports/items` 返回 **50** 条（无 total）；DB `import_item`=**484** | **PARTIAL** | **不一致** | 判定逻辑错（分页子集当全量） |
| 30 | q_O05 | FAIL | 当前指针指向的 T-Box 图（graph 字段见本页真实输出，审计期间被反复改写）内 skos:Concept 为 0，coverage 返回 actual 0/85、0/18、complete=false，checks 无任何核对记录。词表实际只存在于历史版本图（本页 SPARQL 结果里每个含 95~180 个概念），未随当前版本一起发布。 | actual concepts=**85**、aliases=**18**、aliasesWithTarget=18、conceptRatio=**1.0**、aliasRatio=**1.0**、missingAliases=0、**complete=true**；`/ontology/terms/checks` count=0；conflicts 含 blocking | **PARTIAL** | **不一致** | 判定逻辑错（FLIP：FAIL→PARTIAL） |
| 31 | q_M04 | PARTIAL | 口径卡与实体溯源字段可读且带来源；但 /prov/decisions 对该指标返回 0 条判定记录，说明「判定链可点」在多数指标上暂无可点内容。 | provenance summary：total=2、**withSourceRef=0**、none=2、coverageRate=0.0、links=[]、badge=“无”；decisions count=0 | PARTIAL | 一致（verdict） | **文案错**（“带来源”与 0/2 相反） |
| 32 | q_R01 | PARTIAL | 面板本身可用，四层计数、missing 分布、误判下钻字段齐全；但 ontology / terms / facts 三层 coverageRate 基本为 0，只有 metrics 层有非零覆盖（具体数值见本页真实输出）。面板如实暴露了语义层未生效，而非把它藏起来。 | ontology=**4.17%**、terms=**66.67%**、metrics=**25%**、facts=**20.83%** | **PASS** | **不一致** | 判定逻辑错（误读层值，PARTIAL→PASS） |
| 33 | q_R02 | FAIL | 平台自报的 golden set 为 10 例，但 passed 未达 10、passRate 明显低于 1.0（具体 passed/failed 见本页真实输出），未达到判据的「10 例通过」。可取的是 citation 覆盖率与可解析率均为 1.0、断链率 0.0、regression=false。 | cases=10、passed=6、failed=4、passRate=0.6；citationCoverageRate=1.0；citationResolvableRate=**0.6226**；brokenLinkRate=**0.3774**；baseline=0.0；regression=**true** | FAIL | 一致（verdict） | **文案错**（三项“可取”数值与证据相反） |
| 34 | q_R03 | PASS | 实体页、字段级溯源、src:// 引用解析三段链路全部 200 且字段完整；点击回源的数据结构成立。 | 三段均 200；provenance total=2、**withSourceRef=0**、coverageRate=0.0、links=[]；source/resolve 可解析 document_chunk | **PARTIAL** | **不一致** | 判定逻辑错（字段存在≠有来源，PASS→PARTIAL） |
| 35 | q_B04 | PARTIAL | 看板已修复：instances.total 已达数万量级，graphs 同时包含 abox:main 与 abox:synthetic，不再显示 0 实例。但仍有两个未闭合信号：classes.withInstances=0 / ratio=0.0，inferenceFailures 历史累计非零（数值见本页真实输出）。 | instances total=**60525**、graphs=[abox:main, abox:synthetic]；classes total=**159**、withInstances=**156**、ratio=**0.9811**；inferenceFailures=333、lastJob=failed | PARTIAL | 一致（verdict） | **文案错**（classes 0/0.0 与证据相反；文案停在旧版） |
| 36 | q_P02 | FAIL | graph_pointer 的 tbox/current 在审计期间被 smoke-restore 反复改写；推理器 pointer 名为 default 且版本与 tbox/current 不同；术语覆盖固定查另一个 T-Box 图且返回 0/85；实体页 graphs 里同时出现 T-Box、inferred、A-Box 多个版本。多消费者没有共享同一个版本解析函数。 | pointer source=smoke-restore、version=`ont-11f92ebb3326`；reasoning pointer version=**同一** `ont-11f92ebb3326`；terms graph=同一图、actual=**85/18**、complete=true；entity 无 `graphs` 数组 | **PARTIAL** | **不一致** | 判定逻辑错（“版本漂移”被同文件证据反证；FAIL→PARTIAL） |
| 37 | q_S09 | PASS | 导出端点返回完整事件集合与链信息，量级与 fact_event 计数一致。 | `/facts/events/export` 状态行 **15040173 bytes**，留存体仅 200001，止于 `eventId=383` 的半个对象；可见约 382 条，`fact_event`=10049 | **不可采信**（证据不完整） | 无法判定 | 不可采信 |

---

## 3. 14 条不一致 + 1 条无法核实：逐条定性

> 这一节只回答“为什么错”，不重复第 2 节的数值。
> 计数关系：5 文案错 + 6 判定逻辑错 + 1 已修复 + 3 不可采信 = 15。

### 3.1 文案错（5 条）：采集正确、描述错误，verdict 方向仍成立

| 编号 | 原 verdict | 错在哪（证据反证点） | 为什么 verdict 不用改 |
| --- | --- | --- | --- |
| q_S05 | PARTIAL | “最近一次作业状态可能为 succeeded”；证据 `lastJob.state=failed` | 推理失败、aboxGraphs 仅 main、conforms 来自旧导入记录——PARTIAL 仍成立 |
| q_S08 | PARTIAL | “审计期间并行线写入了少量断言”；证据 `fact_assertion=0`、`/facts count=0` | 断言层空库、撤回/冲突无法演示——PARTIAL 仍成立 |
| q_M04 | PARTIAL | “实体溯源字段可读且带来源”；证据 `withSourceRef=0/2`、`badge=无`、`links=[]` | 口径卡可读、判定链无可点内容——PARTIAL 仍成立 |
| q_R02 | FAIL | “citation 覆盖率与可解析率均为 1.0、断链率 0.0、regression=false”；证据 `0.6226 / 0.3774 / true` | `passRate=0.6` 本身已足以 FAIL；只是“可取项”写反了 |
| q_B04 | PARTIAL | “classes.withInstances=0 / ratio=0.0”；证据 `156 / 0.9811`，instances=60525、双图 | `inferenceFailures=333`、lastJob=failed 仍使 PARTIAL 成立 |

**共同机制**：这 5 条的 `reason` 是写死字符串，与采集快照不同步。`q_B04` 是**文案停留在修复前**（修复提交 `94fe29e` 于 23:38:58，采集 23:52:55，采集时已是修复后）；`q_R02` 是**文案提前写成修复后的期望值**（采集时断链率仍 0.3774，当前 8b3f36f 才变为 0.0）。

### 3.2 判定逻辑错（6 条）：取值路径/口径错，verdict 必须改

| 编号 | 原 → 新 | 具体逻辑错误 |
| --- | --- | --- |
| q_S04 | PASS → PARTIAL | 把 `/candidates=100`、`/ui/api/candidates=50`、DB `942` 三个不同口径说成“一致（918 量级）”；两端点均无 `total`，50 只是分页子集 |
| q_S13 | PASS → PARTIAL | 把 `/imports/items` 的 50 条分页结果当成全量，与 DB `import_item=484` 不一致；端点无 `total` |
| q_R03 | PASS → PARTIAL | 把“字段存在”当成“字段有来源”；`withSourceRef=0/2`、`coverageRate=0.0`、`links=[]`，“点击回源”并未落地 |
| q_R01 | PARTIAL → PASS | 误读四层覆盖率：实际 `4.17% / 66.67% / 25% / 20.83%`，并非“terms/facts 基本为 0、只有 metrics 非零” |
| q_P02 | FAIL → PARTIAL | 断言“版本不同”，但同一份证据里 reasoning pointer 与 tbox/current 均为 `ont-11f92ebb3326`；terms 覆盖为 `85/18`、`complete=true`，不是 0/85 |
| q_O05 | FAIL → PARTIAL | 断言“当前图 0 概念、actual 0/85、complete=false”，证据为 `85/18`、`1.0/1.0`、`complete=true`；只有 `/ontology/terms/checks count=0` 支撑“核对记录缺失” |

**与文案错的界线**：这 6 条的错值直接决定 verdict 方向（PASS/FAIL/PARTIAL 必须翻转）；只改文字、不改 verdict 仍然不可信。

### 3.3 当时确实失败、现已修复（1 条）

| 编号 | 采集时（2026-11-06 23:52:21，8080） | 当前（2026-11-07 06:02:59，8082） | 来源与时间 |
| --- | --- | --- | --- |
| q_S10 | `/prov/verify` **503** `E_GRAPH_UNAVAILABLE`（8057ms，`oxigraph is unreachable ... Temporary failure in name resolution`），无 `separation`/`legacy` 字段 | `/prov/verify` **200**，`ok=true`、`checked=12`、`lastHash=aa0bed...`、`separation.ok=true`、`provTriples=319`、`tboxProvTriples=0`、`provTboxTriples=0`、`tboxLegacyProvPredicateTriples=0` | 采集：`doc/_qa/evidence/q_S10.txt`；复测：本文作者对 `127.0.0.1:8082` 的只读 GET，2026-11-07 06:02:59 +08 |

**性质**：不是代码修复，而是**图库可达性恢复**。原始证据显示 `oxigraph` 在 23:52 处于不可解析窗口；容器记录显示 Oxigraph 最后稳定恢复于 **2026-11-06 23:57:32 +08**，此后无重启。`checked=12` 小于原始 10020，是因为验收库只有 12 条 PROV 事件，不是能力退化；关键是此前缺失的 `separation` 与 `legacy` 字段现在都有值且为 0。

### 3.4 不可采信（3 条）：证据不完整，判定不可采信

| 编号 | 截断事实 | 为什么不能判定 |
| --- | --- | --- |
| q_S01 | `/ontology/versions` 响应 211969 bytes，留存体 200001 | 版本枚举完整性与 `count` 不可见；“版本为千条量级”只能看到截断前的一部分 |
| q_S09 | `/facts/events/export` 响应 15040173 bytes，留存体 200001 | 只能看到约 382 条（止于 `eventId=383` 的半对象），无法核对“完整事件集合”及与 `fact_event=10049` 的量级一致性 |
| q_S11 | proposals 2.87MB、events 601KB，各留存 200001 | 两类治理对象主体均丢失；虽然 flow 响应完整且 `states=["published","superseded"]` 反证“覆盖生命周期”，但整体证据不足以给通过判定 |

---

## 4. 修复后实测对照

### 4.1 S10（唯一“已修复”条目）

见 3.3。补充：当前 `/readyz` 200，graph 项 ok；tbox/current 指针 `ok=true`、`status=published`、`versionId=ont-6e81732555e5`、`tripleCount=3340`、`updatedBy=smoke-restore`、`updatedAt=2026-11-07T05:51:38+08`。这说明图库与指针均已可用，503 不再复现。

### 4.2 附：判定一致但现状已变化的条目（不计入 37 条分布，避免重复计数）

这些条目的原始 verdict 在采集时是**正确**的，因此不属于“判定不可信”；但修复清单涉及它们，单独给出对照值。

| 条目 | 采集时（2026-11-06 23:52 +08，8080） | 8b3f36f 复测（2026-11-07 06:03–06:05 +08，8082） | 说明 |
| --- | --- | --- | --- |
| q_M01 | 默认参数 8/8 `rowCount=0/noData=true`；`FIN-BANK-001` 返回 `E_METRIC_BINDING_MISSING` | 缺 `dataSource` → **400** `E_METRIC_DATA_SOURCE_REQUIRED`；`dataSource=synthetic` 后 8/8 非空：008=20、013=20、014=4、015=4、016=4、026=20、INS-002=5、INS-018=4 行；period 指标只给 `asOf` → **400** `E_METRIC_WINDOW_INSUFFICIENT`，给 `periodStart/periodEnd` 全窗口 → 200；`FIN-BANK-001` 仍 `E_METRIC_BINDING_MISSING` | 对应提交 `bc5c01b`、`82244bb`、`eb423bf`、`d623697`；**“可算”成立，但仍有一条确实不可算** |
| q_S14 | `/output?compute=true` 出数：value=61.2536、sampleCount=20、sourceRef rowCount=20；`metric_observation=37471` | `/output` 无 compute → 200（仅 metricId/unit）；`/output?compute=true&dataSource=synthetic` → **400** `E_METRIC_NO_DATA`；验收库 `metric_observation=0` | 代码侧已强制显式 `dataSource`（`9d75bcf`）；当前无观测数据，**不能把“代码修好”当成“端到端出数可用”** |
| q_R02 | `citationResolvableRate=0.6226`、`brokenLinkRate=0.3774`、`regression=true`、passRate=0.6 | `citations=39`、`resolvableCitations=39`、`citationResolvableRate=1.0`、`brokenLinkRate=0.0`、`baseline=0.0`、`regression=false`、**passRate 仍 0.6** | 断链与回归已修复（`51d3d76` `R-03-fix: make /answer/quality truly read-only`、`0046bc5`）；但 10 例仍只过 6 例，**FAIL 结论仍成立** |
| q_B04 | 看板：instances=60525、graphs 双图、classes 156/159（0.9811）、inferenceFailures=333 | 看板：instances=0、graphs=[abox:main]、classes 156、withInstances=0（0.0）、inferenceFailures=3 | 当前 0 是因为验收库 **A-Box 为空**，不是回归；原始采集（23:52:55）已在修复提交 `94fe29e`（23:38:58）之后，故“156/0.9811”才是修复后证据 |
| q_O05 | coverage actual 85/18、complete=true；checks=0 | coverage concepts=85、aliases=0、aliasRatio=0、missingAliases=18、complete=false、blocking=5；`/ontology/terms/gate`：`last.verdict=blocked`、`blocked=true`、`blocking=2`，即使 `configuredGate=warn` | 别名=0 是因为验收库 `term_import=0`（数据缺失），不可与数据栈的 18 直接比较；**零术语硬阻断已实测生效**（`5f92809`/`5665313`） |

---

## 5. 200KB 静默截断：机制与影响

采集器在 `doc/_qa/run_qa.py:976` 写证据时使用：

```python
f"$ {r.label}\n-> {r.status}  {r.ms}ms  {len(r.text)}bytes\n{r.text[:200000]}"
```

- HTTP 层是完整 `r.read()`；**只有写盘时截到前 200000 个字符**；
- 状态行打印的是**完整响应长度**（`len(r.text)`），但单位写成 `bytes`，与随后保存的 200000 字符正文不一致；
- 没有 `truncated=true`、没有截断后缀、没有单独摘要；
- `_short(...).replace(" ...(截断)")` 只用于 md/终端视图，不作用于原始 `evidence/q_*.txt`。

因此 `q_S01`、`q_S09`、`q_S11` 的“看起来完整”具有误导性。本文按用户要求，将它们标为“**证据不完整，判定不可采信**”，不给通过判定，也不以可见片段反推通过。

---

## 6. 最重要的五条结论

1. **原报告 37 条中，判定文本真正与证据自洽的只有 22 条。** 其余 15 条里，10 条判定不可信（6 条 verdict 判错 + 1 条采集时实际失败 + 3 条证据不完整），5 条 verdict 方向对但理由写反。问题比“通过率偏低”更严重，因为它让通过/失败都失去可核对性。
2. **根因不是数据噪声，而是两类系统性错误。** 一类是写死 `reason` 与采集快照不同步（`q_B04` 停在修复前，`q_R02` 提前写成修复后）；另一类是取值路径错（`q_S04`/`q_S13` 把分页子集当全量，`q_O05`/`q_P02` 读错图或错版本，`q_R01` 误读层值，`q_R03` 把“字段存在”当成“有来源”）。
3. **只有 `q_S10` 属于“当时真失败、现已恢复”。** 原因是图库可达性（`oxigraph` 23:52 不可解析，23:57:32 恢复），不是代码缺陷；当前 `200 + separation.ok=true + legacy=0` 可复核。不要把 422/422 当作“37 条 QA 全部通过”的证据——那是另一套验收套件，不是这 37 条的重跑。
4. **`q_S01`/`q_S09`/`q_S11` 的结论不可采信。** 15MB 的导出只留下 382/10049 条，2.87MB/601KB 的治理对象主体丢失，211969 bytes 的版本枚举只剩 200001；采集器 `r.text[:200000]` 无任何截断标记，这是采集缺陷，不是被测系统缺陷。
5. **`8b3f36f` 上“代码已修”与“端到端可用”要分开说。** `M01` 8/8 指标在显式 `dataSource` + 完整 period 窗口下均可算出（20/20/4/4/4/20/5/4 行），`R02` 断链率已从 0.3774 降到 0.0；但验收库 `metric_observation=0`，`/output?compute=true` 仍返回 `E_METRIC_NO_DATA`，`FIN-BANK-001` 仍 `E_METRIC_BINDING_MISSING`。这两条不能算“通过”。
