# `_qa` 验收报告 reason 与证据一致性审计

- 审计对象：`D:\agentABC\coa\doc\_qa\run_qa.py` 中 37 条用例的 `verdict`/`reason`，与 `evidence/q_<编号>.txt` 的采集响应对照
- 审计方式：严格只读；未修改/删除/重命名 `doc/_qa/` 下任何文件
- 采集时间：全部证据为 2026-11-06 23:5x 前后的快照
- 判定口径：
  - **一致**：决定 `verdict` 的运行时断言都能在证据中找到对应值且相符
  - **不一致**：reason 中有具体数值/状态/错误码/布尔值被证据直接反证
  - **无法核实**：reason 的关键断言在证据文件中没有对应查询输出，或输出被截断而无法核对（不按“一致”计）
  - reason 中附带的历史叙述、源码/文档引述若无对应输出，在行内以“附：无法核实”标注，不计入该条主分类

## 结论数字

| 分类 | 数量 |
| --- | --- |
| 一致 | **22** |
| 不一致 | **14** |
| 无法核实 | **1** |
| 合计 | **37** |

已知两条（`q_O05`、`q_R01`/`q_R02`）全部复现；另发现 11 条同类问题。

## 逐条清单

| 编号 | 现 verdict | reason 的关键断言 | 证据文件中的实际值 | 判定 | verdict 建议 |
| --- | --- | --- | --- | --- | --- |
| q_S00 | PASS | 三项健康端点均 200，database/graph/storage 全 ok；providers 声明 metadata=postgres、graph=oxigraph-http，与 compose 一致 | `/readyz` 200，checks 三项均 ok；`/status` 200，providers 为 postgres、oxigraph-http | 一致（“与 compose 一致”附：无法核实，未采集 compose 输出） | 不变 |
| q_S01 | PARTIAL | 版本枚举为千条量级、审计链 ok=true；graph_pointer 被 smoke-restore 反复改写，且与 `/reasoning/status`、`/ontology/terms/coverage` 使用的版本不同（见 q_P02） | `/ontology/verify` ok=true、checked=10020、prov.ok=true(373)；graph_pointer source=smoke-restore、updatedAt=23:51:26；但 q_P02 显示 reasoning pointer 与 terms graph 均为 `ont-11f92ebb3326`，与 tbox/current **相同** | 不一致（核心“版本漂移”断言被 q_P02 反证；“反复改写”单次快照无法证实；版本响应 211969 bytes 仅存 200001，可见 560 条） | 应改：PARTIAL → **PASS**（或保留“版本数量未证实”备注） |
| q_S02 | PASS | 三层计数同量级、`/documents` total 与库一致、向量覆盖率接近 100% | document=3039、chunk=15191、embedding=15120；`/documents` total=3039；覆盖率 15120/15191=99.53% | 一致 | 不变 |
| q_S03 | PASS | 双路召回与 RRF 参数按设计返回，degraded=false，结果非空 | mode=hybrid、rrfK=60、routes=vector+lexical、degraded=false、results=3 | 一致 | 不变 |
| q_S04 | PASS | 候选表与两个端点计数一致（918 条量级），状态字段可读 | `/candidates` count=100（返回 100 条）；`/ui/api/candidates` count=50（state=pending）；DB `extraction_candidate`=942；两端点均无 total 字段 | 不一致（100 vs 50 vs 942，互不一致且均非 918） | 应改：PASS → **PARTIAL** |
| q_S05 | PARTIAL | shapes 与 reasoner 可用、SHACL conforms=true；inferenceFailures 非零，最近作业“可能为 succeeded”；aboxGraphs 仅 abox:main | `/validation/shapes` 200 files=core.ttl；reasoner available=true；conforms=true（来自 2026-11-05 导入记录，非实时）；inferenceFailures=333，lastJob.state=**failed**(E_REASONER_UNAVAILABLE)；aboxGraphs=[abox:main] | 不一致（“可能为 succeeded”与 failed 相反；conforms 为旧导入快照） | 不变（PARTIAL 仍成立） |
| q_S06 | PARTIAL | terms/entities/facts 均为空数组，chunks 有内容 | terms=0、entities=0、facts=0、chunks=7、citations=7 | 一致 | 不变 |
| q_S07 | PASS | 四个页面全部 200 且返回 HTML | 4 个端点均 200，1374/11388/2629/2439 bytes，均为 `<!doctype html>` | 一致 | 不变 |
| q_S08 | PARTIAL | fact_event 近万、fact_assertion 长期 0/个位、`/facts` 近乎为空（审计期间并行线写入了少量断言） | fact_event=10049；fact_assertion=**0**；`/facts` count=0、items=[]；conflicts=0 | 不一致（括号内“写入了少量断言”与 0 相反；其余成立） | 不变（PARTIAL 仍成立） |
| q_S09 | PASS | 导出返回完整事件集合与链信息，量级与 fact_event=10049 一致 | 响应 15040173 bytes，但留存体被截断在 200001 bytes，止于 `eventId=383` 的半个对象；可见仅 382 条，chain/snapshot 字段不可见 | **无法核实**（证据截断，无法核对完整性/量级） | PASS 证据不足；建议 **PARTIAL** 并补采完整导出摘要 |
| q_S10 | PASS | PROV 链 ok=true、T-Box/PROV 图分离 ok=true、legacy 谓词 0；本体事件链近万且 ok=true | `/prov/verify` **503** E_GRAPH_UNAVAILABLE（8057ms），无 separation/legacy 字段；`/ontology/verify` ok=true、checked=10020、prov.ok=true(373) | 不一致（分离与 legacy 未执行；仅嵌套 prov.ok=true 可核） | 应改：PASS → **PARTIAL** |
| q_S11 | PASS | 提案/事件/状态流三类治理对象均可查询，states 覆盖生命周期 | proposals/events 均 200（响应 2.87MB/601KB，留存体各截断于 200001）；flow 200，states=**["published","superseded"]**、count=24 | 不一致（states 仅 2 个，未覆盖 proposal/review/approved） | 应改：PASS → **PARTIAL** |
| q_S12 | PASS | 影响分析、导出、证据包三端点齐全且返回结构化字段 | impact 200（changeSet/affected/aggregations/verification/inputsFingerprint）；impact/export 200 2078B 文本；evidence 200 count=50，含 verdict/sha256/downloadUrl | 一致 | 不变 |
| q_S13 | PASS | 批次、条目、失败列表均可读，条目数与库一致 | batches=5 + failures 可读；`/imports/items` 返回 **50** 条；DB `import_item`=**484** | 不一致（50 vs 484，端点无 total，属分页子集） | 应改：PASS → **PARTIAL** |
| q_S14 | PARTIAL | 老 `/output?compute=true` 能出数（value/unit/版本/窗口/sampleCount/sourceRef），观测表已回填；`/compute` 默认 fixture 空 | value=61.2536 %、v3.0、window=2025-12-31、sampleCount=20、dataSource=synthetic、sourceRef rowCount=20；`/compute` 默认 rowCount=0/noData=true；synthetic rowCount=20；metric_observation=37471 | 一致 | 不变 |
| q_O01 | PASS | 375 行字典、四个视图可用、mappable_unbound 可分页；57 号文档写明 97.53%=79/81 口径 | data_dictionary=375；catalog total=375；all/unbound(339)/mappable_unbound(45，limit=20/offset=0) 均 200 | 一致（文档引述附：无法核实，证据内无文档原文） | 不变 |
| q_O02 | PARTIAL | 状态流与治理事件可读、事件量级与 `/ontology/verify` checked 一致；非法迁移只读不可触发 | flow 200 states=[published,superseded] count=24；events 200（截断）；SQL ontology_event=**10020**；q_S01 verify checked=**10020** | 一致（O02 页内无 verify 调用，靠 q_S01 跨文件核对） | 不变 |
| q_O03 | PASS | 影响分析字段完整、带 inputsFingerprint，导出端点返回文本 | impact 200 字段齐全（changeSet/affected/aggregations/dependencies/verification/fingerprint）；impact/export 200 2078B 文本 | 一致 | 不变 |
| q_O04 | PARTIAL | 证据包端点可用、非法 path 明确拒绝；每次发布生成包需写路径 | evidence 200 count=50（含 verdict/sha256/downloadUrl）；`inspect?path=__qa_probe__` 400 E_BUNDLE_MANIFEST | 一致 | 不变 |
| q_O05 | FAIL | 当前指针图 skos:Concept 为 0，coverage actual 0/85、0/18、complete=false，checks 无记录，词表只在历史图 | coverage graph=`ont-11f92ebb3326`，actual=**85/18**，coverage=1.0/1.0，complete=**true**；checks count=0；SPARQL 当前图 **180**、历史图 180 | 不一致（除 checks 为空外，其余关键数值全部相反） | 应改：FAIL → **PARTIAL**（checks 空） |
| q_O06 | PASS | 类/属性级聚合、状态流、两版本快照与空态说明按判据返回 | diff 200（counts + 四个空数组）；flow count=24；snapshot from/to/delta、empty=false、emptyReason=null；aggregations.byClass 存在 | 一致 | 不变 |
| q_M01 | FAIL | 默认参数下 8 条全部 rowCount=0/noData=true，0 条满足；synthetic 后 FIN-BANK-008 才出数；FIN-BANK-001 返回 E_METRIC_BINDING_MISSING | 8 条 `/compute` 均 rowCount=0/noData=true；synthetic rowCount=20/noData=false；FIN-BANK-001 providerCode=E_METRIC_BINDING_MISSING；事实表 data_source=synthetic 5020 | 一致 | 不变 |
| q_M02 | PASS | 85 行 100% 覆盖、字段齐全、JSON 与 CSV 同源，meta 给出 publishable/externalEligible 聚合 | count=85/items=85；meta publishable=60、industry=46、regulatory=39、externalEligible=35、industryExcludedFromExternal=0；CSV 16 列 172 行（含换行字段） | 一致（“同源”附：无法核实，只能核对两端点均存在且计数一致） | 不变 |
| q_M03 | PASS | 族索引与口径卡列表均可读，guidance 字段存在 | families count=3、guidance 含 code/message/howTo；`/browse/metrics` count=85/items=85 | 一致 | 不变 |
| q_M04 | PARTIAL | 口径卡与实体溯源字段可读且**带来源**；`/prov/decisions` 返回 0 条 | card 200；provenance total=2、withSourceRef=**0**、none=2、badge=“无”、links=[]；decisions count=0 | 不一致（“带来源”与 0/2 有 sourceRef 相反） | 不变（PARTIAL 仍成立） |
| q_M05 | PASS | 全部 industry 100% 带 internalNotice；publishable=true 的 industry 条目 externalEligible 全为 false、externalStatus=internal_baseline | industry=46，全部带 internalNotice；其中 publishable=24，externalEligible 全 false、externalStatus=internal_baseline | 一致 | 不变 |
| q_M06 | PASS | counts 与 58 号一致（16/1/3，共 20），筛选与 CSV 可用，registered_only 带原因 | counts 16/1/3、count=20；kind=rule count=11；registered_only 条目含原因；CSV 200 | 一致 | 不变 |
| q_R01 | PARTIAL | 面板可用；ontology/terms/facts 三层 coverageRate“基本为 0”，只有 metrics 非零 | ontology=**4.17%**、terms=**66.67%**、metrics=**25%**、facts=**20.83%** | 不一致（terms/facts 并非接近 0，metrics 也非唯一非零层） | 应改：PARTIAL → **PASS**（仅 ontology 层 4.17% 偏低） |
| q_R02 | FAIL | 10 例但 passed 未达 10、passRate 明显低于 1.0；citation 覆盖率与可解析率均为 1.0、断链率 0.0、regression=false | cases=10、passed=6、failed=4、passRate=0.6；citationCoverageRate=1.0；citationResolvableRate=**0.6226**；brokenLinkRate=**0.3774**；baseline=0.0；regression=**true** | 不一致（可解析率、断链率、regression 三项均相反） | 不变（FAIL 仍成立，但结论依据须重写） |
| q_R03 | PASS | 实体页、字段级溯源、src:// 解析三段链路全部 200 且字段完整；点击回源的数据结构成立 | 三段均 200；provenance total=2、withSourceRef=**0**、coverageRate=**0.0**、links=[]；source/resolve 可解析 document_chunk | 不一致（字段齐全但 0/2 字段有 sourceRef、无 links，“可点回”未落地） | 应改：PASS → **PARTIAL** |
| q_R04 | PASS | 跳转模板与稳定 URL 已注册且标记 readOnly | stable=true、readOnly=true、writeOperations=0、paths=4、templates 4 项 | 一致 | 不变 |
| q_R05 | OFF | 两次均 503 E_CANVAS_DISABLED；config.py:60 默认 provider=off | 两次 503 E_CANVAS_DISABLED（canvas is disabled: canvas.provider=off） | 一致（源码断言附：无法核实，证据内无源码输出） | 不变 |
| q_B03 | PASS | 实体页 200 且 0.1s 内返回，邻居端点正常；上轮问题已被并行线修复 | entity 200/30ms；neighbors 200/10ms、graphs=3 | 一致（“上轮已修复”附：无法核实，证据内无历史对比） | 不变 |
| q_B04 | PARTIAL | instances 数万、graphs 双图；classes.withInstances=0 / ratio=0.0；inferenceFailures 非零 | instances total=**60525**、graphs=[abox:main, abox:synthetic]；classes total=159、withInstances=**156**、ratio=**0.9811**；inferenceFailures=333、lastJob=failed | 不一致（classes 断言完全相反；“T-Box 类与实例对不上”亦不成立） | 不变（PARTIAL 仍因 inferenceFailures=333 成立） |
| q_P01 | FAIL | 推理器只读 abox:main，看板双图，实例绝大多数在 synthetic，无唯一权威，物化产物极少 | reasoning aboxGraphs=[abox:main]；dashboard total=60525 graphs 双图；SPARQL synthetic=**304919**；pointer.inferred=1171 | 一致（1171 相对 30 万实例可称极少） | 不变 |
| q_P02 | FAIL | pointer 被 smoke-restore 反复改写；reasoning pointer 名为 default 且版本与 tbox/current 不同；terms 覆盖查另一图并返回 0/85；实体页 graphs 出现多版本 | pointer source=smoke-restore、version=`ont-11f92ebb3326`；reasoning pointer name=default、version=**同一** `ont-11f92ebb3326`；terms graph=同一图、actual=**85/18**、complete=true；entity 无 `graphs` 数组，仅 tbox 单版本 | 不一致（版本相同、覆盖 85 完整、entity 无多图字段；“反复改写”单次快照不可证） | 应改：FAIL → **PARTIAL**（外部改写与命名不一致仍在，但非“版本漂移”） |
| q_P03 | PASS | 有效 obs/doc 引用均解析出 targetTable 与定位，不存在引用返回 400 E_SOURCE_REF_NOT_FOUND，PROV ok 且分离成立；更早基线返回 STALE | obs_rows=37471、obs_refs=316；obs/doc 均 200/found/rowCount（5000、1）；负向 400 E_SOURCE_REF_NOT_FOUND；`/prov/verify` 200 ok=true checked=382 separation 存在 | 一致（“更早基线”附：无法核实，证据只保存当前时刻） | 不变 |

## 单列：无法核实（1 条）

**q_S09**：reason 声称“导出端点返回完整事件集合与链信息，量级与 fact_event=10049 一致”。`evidence/q_S09.txt` 的状态行记录响应 15040173 bytes，但实际留存体在 200001 bytes 处被截断（末尾停在 `eventId=383` 的半个对象），`count/chain/snapshot/export` 等摘要字段均不可见。因此“完整集合”和“量级一致”都无法核对。按可见的 382 条与 10049 的差距，不能判定为一致；应补采完整导出或只采摘要字段后再判。

同类截断还出现在 `q_S01`（/ontology/versions，211969 bytes 存 200001）与 `q_S11`（proposals/events，2.87MB、601KB 各存 200001），但这两条的其它证据仍足以判定，故未归入本类。

## 附：reason 中无对应输出的非决定性断言

以下断言在对应证据文件里没有查询/输出，但未被证据反证，也未单独改变主分类：

- q_S00：providers“与 docker compose 实际服务一致”（无 compose 输出）
- q_S01：pointer 被“反复改写”（只有单个 updatedAt 与 source 标签）
- q_O01：57 号文档“97.53%=79/81、按 375 计 21.1%”（无文档原文；且当前库 unbound=339 ⇒ 已绑定仅 36，79 的口径无法从本页复现）
- q_M02：JSON 与 CSV“同源”（只能核对两端点存在与计数）
- q_B03：“上一轮超时问题已被并行线修复”（无上一轮基线）
- q_P03：“更早基线时刻返回 E_SOURCE_REF_STALE”（证据只保存当前时刻）
- q_R05：`config.py:60` 默认 `provider=off`（证据只采了两个 GET，未采源码）

## 需要改 verdict 的条目（9 条，另 1 条待补证）

| 编号 | 现 verdict | 建议 | 依据 |
| --- | --- | --- | --- |
| q_S01 | PARTIAL | PASS | 版本指针/推理/术语均指向 `ont-11f92ebb3326`，“版本不同”不成立 |
| q_S04 | PASS | PARTIAL | 端点 100/50 与库 942 不一致 |
| q_S10 | PASS | PARTIAL | `/prov/verify` 503，分离与 legacy 未验证 |
| q_S11 | PASS | PARTIAL | states 仅 published/superseded |
| q_S13 | PASS | PARTIAL | items=50 与库 484 不一致 |
| q_O05 | FAIL | PARTIAL | actual 85/18、complete=true，仅 checks 为空 |
| q_R01 | PARTIAL | PASS | terms 66.67%、facts 20.83%，并非“基本为 0” |
| q_R03 | PASS | PARTIAL | provenance 0/2 字段有 sourceRef、links 为空 |
| q_P02 | FAIL | PARTIAL | 三处消费者版本相同，0/85 与 complete=true 反证 |
| q_S09 | PASS | PARTIAL（待补证） | 导出证据被截断，完整性/量级不可核 |

`q_R02` 虽 reason 有三项反证，但 `passRate=0.6` 与 `regression=true` 本身已足以维持 FAIL，故 verdict 不变。
