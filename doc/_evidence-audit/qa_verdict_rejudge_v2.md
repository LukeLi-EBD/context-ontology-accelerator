# 基于 `_qa-v2` 新证据的 37 条独立重判

> 本文只依据 `doc/_qa-v2/evidence/` 的 2026-11-07 08:06:47 采集批次重推。
> 旧采集器里写死的 `verdict` / `reason` 只作为「原始判定」列展示，**不参与本轮判定推导**；
> 上一轮 `qa_verdict_recheck.md` 只用于第 2、3 节的分类对照，**不作为任何一条结论的依据**。

## 0 判定基准

| 项 | 值 |
| --- | --- |
| 代码基线 | `HEAD a833367`（仅 4 个 docs/evidence 文件，无代码改动）；代码等价 `5386a04`（镜像构建提交 `8b3f36f`，`8b3f36f` 仅 `scripts/push-queue.ps1`） |
| 验收栈 | `127.0.0.1:8082`，镜像 `agent-platform:0.1-s5`（2026-11-07 05:45:09 +08） |
| 数据库容器 | `platform-acceptance-postgres`；SPARQL 走 `platform-acceptance-api` → `http://oxigraph:7878/query` |
| 证据批次 | `doc/_qa-v2/evidence/`，采集 2026-11-07 08:06:47 +08 |
| 证据状态 | `ADMISSIBLE_FOR_REJUDGE`；37/37 `truncated=false`；`limitBytes=20000000`；扫描 37 份，无 unmarked |
| 静默基线 | 07:58:54 / 08:04:25 两次快照，间隔 331s，五表计数与 `tbox/current` 完全一致 |
| 库内计数 | `document 39`、`metric_definition 85`、`metric_observation 37,471`（55 个指标）、`fact_event 97`、`import_item 0` |
| 补充实测 | 第 5 节的 `dataSource=synthetic` 探针均为只读 GET，未写入任何表，未改采集器 |

判定尺度：只判该用例 `exp` 里的可观测断言是否被本批证据支持；不引入新阈值，不为凑结论放行。
`PASS` = 断言全部成立；`PARTIAL` = 结构/部分断言成立、关键断言不成立；`FAIL` = 关键断言不成立；
`OFF` = 功能被配置关闭，不构成代码缺陷；`证据完整但不足以下判` = 证据无损坏，但输入前提在该栈不存在，无法支持任一方。

## 1 新分布

| 新判定 | 条数 | 编号 |
| --- | --- | --- |
| PASS | 16 | S00 S01 S02 S03 S07 S09 S10 S11 O04 M01 M02 M03 M05 M06 R01 R04 |
| PARTIAL | 16 | S04 S05 S06 S08 S12 S13 S14 O01 O02 O03 O05 O06 M04 P02 P03 B04 |
| FAIL | 1 | R02 |
| OFF | 1 | R05 |
| 证据完整但不足以下判 | 3 | B03 R03 P01 |

与原始判定同向 21 条，翻转 16 条（S01 S04 S12 S13 O01 O03 O04 O05 O06 M01 R01 R03 B03 P01 P02 P03）。

## 2 与上一轮分类对照

| 类别 | 上一轮 | 本轮 | 本轮编号 |
| --- | --- | --- | --- |
| 一致 | 22 | 13 | S00 S03 S06 S07 S09 S11 O02 M03 M05 M06 R02 R04 R05 |
| 文案错 | 5 | 7 | S02 S05 S08 S14 M02 M04 B04 |
| 判定逻辑错 | 6 | 12 | S01 S04 S12 S13 O01 O03 O04 O05 O06 R01 P02 P03 |
| 已修复 | 1 | 2 | S10 M01 |
| 不可采信 | 3 | 0 | —（上一轮的 S01/S09/S11 本批已完整可判） |
| 证据完整但不足以下判 | 0 | 3 | B03 R03 P01（新增类别） |

相对上一轮的**判定变化共 12 条**：S01 无法判定→PASS；S09 无法判定→PASS；S11 无法判定→PASS；S12 PASS→PARTIAL；O01 PASS→PARTIAL；O03 PASS→PARTIAL；O06 PASS→PARTIAL；O04 PARTIAL→PASS；M01 FAIL→PASS；R03 PARTIAL→证据完整但不足以下判；B03 PASS→证据完整但不足以下判；P01 FAIL→证据完整但不足以下判。
其余 25 条判定方向不变；其中 S02/M02/R02/S14 四条的**理由类别**变了（数值/失败形态与旧文案不符），S05/S08/M04/B04 仍是文案错。

### 2.1 相对上一轮的变化清单（17 条分类变化）

| 编号 | 上一轮类别 | 本轮类别 | 上一轮判定 → 本轮判定 | 归因 |
| --- | --- | --- | --- | --- |
| S01 | 不可采信 | 判定逻辑错 | 无法判定 → PASS | E+S：截断消除 + 版本统一 |
| S02 | 一致 | 文案错 | PASS → PASS | N：82.9% ≠ 旧文案 100% |
| S09 | 不可采信 | 一致 | 无法判定 → PASS | E：截断消除（97 事件规模） |
| S11 | 不可采信 | 一致 | 无法判定 → PASS | E：截断消除 |
| S12 | 一致 | 判定逻辑错 | PASS → PARTIAL | D2：无基线，指纹为 null |
| S14 | 一致 | 文案错 | PARTIAL → PARTIAL | C+D1：noData 改为显式 400 |
| O01 | 一致 | 判定逻辑错 | PASS → PARTIAL | D2：字典 79 行 |
| O03 | 一致 | 判定逻辑错 | PASS → PARTIAL | D2：无基线 |
| O04 | 一致 | 判定逻辑错 | PARTIAL → PASS | E：50 条中含 2 条 fail 包 |
| O06 | 一致 | 判定逻辑错 | PASS → PARTIAL | D2：无基线，diff 409 |
| M01 | 一致 | 已修复 | FAIL → PASS | C+D1：显式参数 + synthetic 数据 |
| M02 | 一致 | 文案错 | PASS → PASS | N：CSV 86 行 ≠ 旧文案 172 行 |
| R02 | 文案错 | 一致 | FAIL → FAIL | C：1.0/1.0/0.0/false 现在成立 |
| R03 | 判定逻辑错 | 证据完整但不足以下判 | PARTIAL → 不足下判 | D2：输入全部缺失 |
| B03 | 一致 | 证据完整但不足以下判 | PASS → 不足下判 | D2：A-Box 为空 |
| P01 | 一致 | 证据完整但不足以下判 | FAIL → 不足下判 | D2：A-Box 为空 |
| P03 | 一致 | 判定逻辑错 | PASS → PARTIAL | D2：DOC_REF 未注册 |

其余 20 条分类与上一轮相同（其中 S04/S08/M04/B04 的数值被本批证据反证，但仍分别落在「判定逻辑错/文案错」同一类别）。


## 3 37 条逐条重判

### 3.1 S 组（平台与数据链路）

| 编号 | 原始 | 新证据实际数据（本批） | 新判定 | 与原始一致 | 差异原因与归因 |
| --- | --- | --- | --- | --- | --- |
| q_S00 | PASS | `/readyz` 200（database/graph/storage 全 ok，disk 32.64%）；`/status` 200：version 0.1.0、slice S13、mode single、providers metadata=postgres、graph=oxigraph-http | PASS | 一致 | 三项元信息均可读；数值随栈变化，结论未变（N） |
| q_S01 | PARTIAL | `ontology_version` 21 条；`/ontology/verify` ok、checked=104；`graph_pointer` 唯一 `tbox/current → ont-6e81732555e5`（updatedAt 07:53:51，contentHash 9417…）；`schema_version` max=40 | PASS | **不一致** | 版本数只有 21、非「千条」，但枚举/发布指针/审计三项硬断言成立；旧理由的「指针被反复改写、与 reasoning/terms 不同」在本批不成立（E+S） |
| q_S02 | PASS | `document=39`、`document_chunk=41`、`chunk_embedding=34`；`/documents` total=39、39 条 item | PASS | 一致 | 三层同量级、total 与库一致；旧理由「向量覆盖率接近 100%」在本栈是 34/41=82.93%，数值不成立（文案错，N） |
| q_S03 | PASS | `/search`：mode=hybrid、rrfK=60、routes=[vector,lexical]、degraded=false、results=3；`/ui/api/search` 每个 chunk 带 `chunkId` 与 `citationId` | PASS | 一致 | 双路召回/融合参数/定位信息均被证据支持（N） |
| q_S04 | PASS | `/candidates` count=8；`/ui/api/candidates` count=4 且响应固定 `state=pending`；库内 candidates=8 | PARTIAL | **不一致** | 两个端点计数 8≠4；UI 端点默认只取 pending 子集，判据「计数与库一致」不成立，且只读侧无法区分设计/缺陷（D2+N） |
| q_S05 | PARTIAL | `shacl/shapes` 200 非空；reasoner available=true；`aboxGraphs=[abox:main]`；`inferenceFailures=3`，lastJob failed `E_REASONER_UNAVAILABLE`（05:48）；`conforms=null` | PARTIAL | 一致 | 结构与可用性成立；失败计数非 0、`abox:synthetic` 不在图集；旧理由「lastJob 可能 succeeded」被反证（文案错，N） |
| q_S06 | PARTIAL | `/context/resolve` 200：terms=0、entities=0、facts=0、chunks=10、citations=10；tokenBudget=2048、tokenEstimate=875、degraded=false | PARTIAL | 一致 | 上下文包能组装且预算生效，但术语/实体/事实三层为空，语义层未参与（N） |
| q_S07 | PASS | 4 个页面均 200，返回 HTML（本体/指标/问答/治理） | PASS | 一致 | 断言成立（N） |
| q_S08 | PARTIAL | `/facts` count=0；`fact_assertion=0`；`/facts/conflicts` count=0；`fact_event=97` | PARTIAL | 一致 | 端点结构与账本可读，但当前断言表为空；旧理由「事件账本近万条」在本栈为 97（文案错，N） |
| q_S09 | PASS | `/facts/events/export`：count=97、items=97、chain.ok=true/checked=97、export `verified_prefix=true`、ndjson 有样例；响应体 145,278B | PASS | 一致 | 97 事件规模下字段与哈希链完整；**本批只证明该规模**。15MB 场景在 8080（此前只读探测 15,195,251B，未落盘为证据），不能据此宣称大响应截断已解决（E+N） |
| q_S10 | PASS | `/prov/verify` 200：ok=true、checked=48、separation.ok=true、provTriples=916、tboxProv/provTbox/legacy 均为 0；`/ontology/verify` ok、checked=104 | PASS | 一致 | 采集时 503 的问题在本批为 200，分离约束实测成立（已修复；旧理由「近万量级」数值不成立） |
| q_S11 | PASS | `/governance/proposals` 15 条；`/governance/events` 104 条；flow count=39、states=[proposed,review,approved,published,draft,superseded] | PASS | 一致 | 三类端点 200 且字段完整；旧「不可采信」仅因截断，本批完整（E） |
| q_S12 | PASS | `/governance/impact` 200 但 `empty=true`、`emptyReason=no baseline`、`inputsFingerprint=null`；export 有文本；evidence 50 条 | PARTIAL | **不一致** | 键存在但内容为空、无输入指纹，判据「带 inputsFingerprint」不成立；根因是该栈无基线版本（D2） |
| q_S13 | PASS | `/imports/batches` batches=[]、failures=[]；`/imports/items` items=[]（响应无 count 字段）；库内 `import_item=0` | PARTIAL | **不一致** | 端点与空态可读，但判据要求 items 非空、与 import_item 一致；本栈无导入数据（D2） |
| q_S14 | PARTIAL | `/metrics` 85 条；output 定义 200；`/output?compute=true` 400 `E_METRIC_DATA_SOURCE_REQUIRED`；`/compute` 默认 400；`/compute?dataSource=synthetic` 200、rowCount=20、noData=false；`/output?compute=true&dataSource=synthetic` 200、value=61.2536、sampleCount=20、sourceRef→`platform.metric_observation`；库内观测 37,471 | PARTIAL | 一致 | 主路径在显式 synthetic 下可出数；默认路径 400，旧理由「默认 rows=[]/noData=true」已被代码改为显式参数错误（文案错，C+D1） |

### 3.2 O 组（本体与治理）

| 编号 | 原始 | 新证据实际数据（本批） | 新判定 | 与原始一致 | 差异原因与归因 |
| --- | --- | --- | --- | --- | --- |
| q_O01 | PASS | `data_dictionary=79`；`/catalog/dictionaries/views/unbound` total=79、unbound=0、`mappable_unbound=0`；四视图均 200 | PARTIAL | **不一致** | 四视图可读且无未绑定，但 79 行 ≠ 判据的 375 行/81-79-2 口径，无法核对 97.53% 覆盖率（D2） |
| q_O02 | PARTIAL | `/governance/flow` count=39、states=6；`ontology_events=104`；`/ontology/verify` checked=104；状态项含 actor/at/reason（reason 可为 null） | PARTIAL | 一致 | 六状态覆盖 proposed→superseded，字段可读；非法迁移与回滚写入只读侧不可验证（N） |
| q_O03 | PASS | `/governance/impact` 200、empty=true、`inputsFingerprint=null`；export 文本可用 | PARTIAL | **不一致** | 同 S12：无基线导致影响面为空，判据「带输入指纹」不成立（D2） |
| q_O04 | PARTIAL | `/governance/evidence` 50 条：48 条 verdict=pass、2 条 fail，均带 sha256/downloadUrl；非法 path 400 `E_BUNDLE_MANIFEST` | PASS | **不一致** | 「失败也有包」已被 2 条 fail 证据直接支持，非法引用有明确错误码；「每次发布都生成」仍不可只读验证（E，附注） |
| q_O05 | FAIL | 覆盖率 actual concepts=85/85（ratio 1.0）、aliases=0/18、`complete=false`、missingAliases=18、blocking=5；`/terms/checks` count=0（emptyReason=尚无术语核对记录）；gate entries=[]、anchorClasses/altLabels/evidenced/inferred 均为 0；conflicts 5 条全为 blocking；当前 T-Box 图含 180 个 skos:Concept | PARTIAL | **不一致** | 概念层已随当前版本发布（85 个），旧「当前图 0 概念」不成立；别名 0/18、checks 0、complete=false 仍未达标（D1+C） |
| q_O06 | PASS | `/health/ontology-diff` 409 `E_DIFF_NO_PREVIOUS_BASELINE`；flow 200（39/6）；snapshot 200 但 from=null、empty=true、有 emptyReason | PARTIAL | **不一致** | diff 不能返回 added/removed 计数；snapshot 无基线，只有空态说明（D2） |

### 3.3 M 组（指标）

| 编号 | 原始 | 新证据实际数据（本批） | 新判定 | 与原始一致 | 差异原因与归因 |
| --- | --- | --- | --- | --- | --- |
| q_M01 | FAIL | 默认 8/8 均 400（`E_METRIC_DATA_SOURCE_REQUIRED`，期间型另加 `E_METRIC_WINDOW_INSUFFICIENT`）；补充实测 `dataSource=synthetic`：008=20、013=20、014=4、015=4、016=4、026=20、INS-002=5、INS-018=4 行，均 noData=false；FIN-BANK-001 仍 `E_METRIC_BINDING_MISSING`；`bank_loan_account` 5020 行全为 synthetic | PASS | **不一致** | 判据「≥6 条非空可复算、其余给错误码」成立（8/8 可算，1 条绑定缺失）；但必须显式 dataSource，期间型必须给完整窗口。旧「默认 0 条满足」已因代码契约+灌数据改变（若只看默认调用仍不成立，本判定按 synthetic 实测口径） |
| q_M02 | PASS | manifest 200：count=85、`meta.total=85`、publishable=true 60、industry 46、externalEligible 35；CSV 16 列、85 数据行（86 物理行） | PASS | 一致 | 同源与字段成立；旧理由「CSV 172 行」在本栈为 86 行（文案错，N） |
| q_M03 | PASS | `/metrics/families` 200、families=3、每族带 guidance；`/browse/metrics` count=85 且 filters 可读 | PASS | 一致 | 断言成立（N） |
| q_M04 | PARTIAL | `/ui/api/metric-card` 200（formula/evidenceBasis/unit）；`/entity/provenance` 404 `entity not found in any configured graph`；`/metric/decisions` count=0 | PARTIAL | 一致 | 卡片与决策结构可读；实体溯源因 A-Box 为空不可验证；旧理由「溯源带来源字段」被 404 反证（文案错，D2） |
| q_M05 | PASS | manifest 85 条；industry 46 条（其中 publishable 24）全部有 `industryBaseline` 与 `internalNotice`；industry+publishable 中 `externalEligible=true` 为 0 | PASS | 一致 | 判据逐项成立（N） |
| q_M06 | PASS | `/metrics/computability` counts：executed=16、registered_only=1、not_executable=3（总 20）；CSV 200、每行含状态与原因 | PASS | 一致 | 计数与明细一致（N） |

### 3.4 R 组（评测/回归/安全/画布）

| 编号 | 原始 | 新证据实际数据（本批） | 新判定 | 与原始一致 | 差异原因与归因 |
| --- | --- | --- | --- | --- | --- |
| q_R01 | PARTIAL | panel evaluated=24；layers：ontology 1/24=4.17%、terms 7/24=29.17%、metrics 6/24=25%、facts 6/24=25%；missing=56（各层 18/16/7/0）；misjudgments=7/24=29.17%；`/answerable` 青岛=false 且给缺层说明 | PASS | **不一致** | 面板/缺层/趋势/误判结构齐备且四层 evaluated=24，覆盖率已非 0，判据成立（D1） |
| q_R02 | FAIL | golden 10、passed 6、failed 4、passRate=0.6；citation=1.0、resolvable=1.0、broken=0.0、regression=false；`refusalsWithoutLayers=[]` | FAIL | 一致 | 「10 例通过」不成立；旧理由的 1.0/1.0/0.0/false 在本批成立（R02 自身仍未达标）。归因：C（此前版本已修复引用/回归，但通过率仍 0.6） |
| q_R03 | PASS | `/ui/api/entity` 404；`/entity/provenance` 404；`/source/resolve?doc-ref` 400 `E_SOURCE_REF_NOT_FOUND` | 证据完整但不足以下判 | **不一致** | 三个输入（实体、溯源、指定 doc 引用）在该栈都不存在，证据无法支持 PASS 或 FAIL（D2） |
| q_R04 | PASS | `/security/audit`：stable=true、readOnly=true、writeOperations=0；paths=4、templates=4、artifacts=4 | PASS | 一致 | 断言成立（N） |
| q_R05 | OFF | `/graph/canvas?maxHops=1/4` 均 503 `E_CANVAS_DISABLED` | OFF | 一致 | 功能被配置关闭，非代码缺陷；旧判定同为 OFF（N） |

### 3.5 B / P 组（本体原理专项）

| 编号 | 原始 | 新证据实际数据（本批） | 新判定 | 与原始一致 | 差异原因与归因 |
| --- | --- | --- | --- | --- | --- |
| q_B03 | PASS | `/ui/api/entity?iri=...` 404 `entity not found in any configured graph`；neighbors 200：graphs=[tbox:ont-6e8173, abox:main]、nodes=1（裸 IRI stub）、edges=0 | 证据完整但不足以下判 | **不一致** | 该栈 A-Box 实例总数为 0，判据要求的「真实 A-Box IRI」不存在；404 不能证明实体页能力缺失，也不能证明可用（D2） |
| q_B04 | PARTIAL | dashboard `instances.total=0`、graphs=[abox:main]；classes 156（withInstances=0）、properties 135（withValues=0）；inferenceFailures=3（last failed 05:48）；shacl conforms=null | PARTIAL | 一致 | 0 实例与空 A-Box 自洽；但 `abox:synthetic` 不在图集、推理失败非 0，旧理由「数万实例/双图」被反证（文案错，D2） |
| q_P01 | FAIL | SPARQL 8 个命名图：tbox 当前 3340、inferred 当前 995、prov 916、3 个旧 inferred（18/14/14）、2 个旧 tbox（12/12），**无 A-Box 图有三元组**；reasoning `aboxGraphs=[abox:main]`、pointer ont-6e8173、lastJob failed；dashboard graphs=[abox:main]、instances=0 | 证据完整但不足以下判 | **不一致** | 两个端点现已一致（都是 main），但 A-Box 为空，无法判断「推理输入是否等于真实数据图」；旧 FAIL 的 synthetic 不一致在本栈无法复现（D2） |
| q_P02 | FAIL | `tbox/current=ont-6e8173`（07:53:51，smoke-restore）；reasoning pointer `ontologyVersion=ont-6e8173`；terms coverage graph=`tbox:ont-6e8173`；`/ui/api/entity` 404 | PARTIAL | **不一致** | SQL/推理/术语/API 四路已解析到同一版本，旧「版本漂移」不成立；切换版本时的迁移行为只读不可验证（S+C） |
| q_P03 | PASS | `metric_observation=37,471`、`source_ref_registry=252`；obs 有效引用 200、rowCount=5000、targetTable=`metric_observation`；DOC_REF 400 `E_SOURCE_REF_NOT_FOUND`；伪造引用 400 同码；`/prov/verify` separation.ok=true | PARTIAL | **不一致** | 观测引用可解析、伪造引用有错误码；但用例给定的 DOC_REF 在该栈未注册，且 STALE 与 NOT_FOUND 未区分（D2） |

## 4 归因汇总

| 归因（可叠加） | 涉及条数 | 编号 | 说明 |
| --- | --- | --- | --- |
| D1 灌数据 / 词表发布 | 3 | M01 R01 O05 | synthetic 37,471 观测/55 指标使指标可算；当前 T-Box 已含 85 概念，覆盖率非 0 |
| D2 验收栈数据边界 | 13 | S04 S08 S12 S13 O01 O03 O06 M04 B03 B04 P01 R03 P03 | A-Box 为空（B03/B04/P01/M04）、无基线（S12/O03/O06）、import_item=0（S13）、字典 79 行（O01）、doc 引用未注册（R03/P03）、UI 默认 pending 过滤（S04）、fact_event 97（S08） |
| C 代码契约 / 修复 | 4 | S10 M01 S14 R02 | 采集时 503→200；指标默认空结果改为显式 400；引用/回归指标已按修复值生效 |
| E 证据完整化 | 4 | S01 S09 S11 O04 | 200KB 截断消除后，版本审计链、97 事件导出链、治理三类端点、48 pass + 2 fail 证据包可判 |
| S 环境版本统一 | 2 | S01 P02 | `smoke-restore` 把 `tbox/current` 与推理/术语解析统一到 `ont-6e8173` |
| N 数值随栈变化、结论未变 | 13 | S00 S02 S03 S05 S06 S07 O02 M02 M03 M05 M06 R04 R05 | 计数/行数与数据栈不同，判定方向不变；其中 S02/S05/M02 属旧文案数值不成立 |

> 叠加归因：M01 同时计入 D1 与 C，S01 同时计入 E 与 S；因此各桶相加不等于 37。

> D2 条目里，S04/S08/M04/B04 判定方向与原判定一致但理由数值被反证；其余 9 条因栈数据缺失而**降级或无法判**，不代表 8b3f36f 代码退化。

## 5 证据边界（必须与结论一起读）

1. **q_S09 不是 15MB 场景**：本批该栈 `fact_event=97`，导出响应 145,278B；15MB 量级在 8080（此前只读探测为 15,195,251B，未作为证据落盘）。本批只能证明 97 事件规模的导出与哈希链完整，**不能宣称「截断问题已解决」**；20MB 上限内未出现第二次截断。
2. **A-Box 为空**：`instances.total=0`、SPARQL 无 A-Box 图三元组。所有依赖真实实体的断言（B03/R03/M04 溯源/P01）只能判「证据完整但不足以下判/部分成立」。
3. **无基线版本**：`graph_pointer` 只有当前版本；impact/diff 返回空或 409。O03/O06/S12 的降级来自此边界，不是代码退化。
4. **默认出数不成立**：`/metrics/*/compute` 与 `/output?compute=true` 缺 `dataSource` 均 400；显式 `dataSource=synthetic` 才出数（008 为 20 行，输出 value=61.2536）。S14 判 PARTIAL 正是为此。
5. **本批未采 8080**：所有数据来自 8082；8080 仅用于第 1 条的一次性只读尺寸探测，不构成 37 条判定依据。

## 6 与原始报告、上一轮重判的关系

- **原始报告（R1）**：`doc/_qa/` 的 37 篇 `q_*.md` + `README.md`，采集 2026-11-06 23:52:21 +08、数据栈 8080；其活跃证据已被另一条线的 `run_qa_r2.py` 覆盖，原件归档在 `doc/_qa/_history/2026-11-06_2352/`（82 个 evidence 文件、37 张截图、41 个根文件；0 零字节、0 缺页；内容首行仍为 23:52:21）。
- **上一轮重判**：`doc/_evidence-audit/qa_verdict_recheck.md`，依据 R1 证据 + 8b3f36f 复测，给出 22 一致 / 5 文案 / 6 逻辑 / 1 已修复 / 3 不可采信。本文只在第 2、3 节引用它的分类用于对照。
- **本文**：`qa_verdict_rejudge_v2.md`，依据 `_qa-v2` 2026-11-07 08:06:47 批次独立重推；与原始报告不同栈、不同证据批次；与上一轮重判相比 25 条方向不变、12 条变化。三者不是替代关系：原始报告是 R1 现场记录，上一轮是 R1 证据的复核，本文是 8b3f36f + 灌数据后的新现场判定。

## 7 三条最重要的结论

1. **本轮唯一 FAIL 仍是 R-02**：golden 10 例 passed 6、passRate 0.6，引用/可解析/坏链/回归四项已达标；这不是本轮修复引入的问题。
2. **灌数据确实把三条翻了正，但「能出数」仍是有条件的**：M-01 8/8 指标在 `dataSource=synthetic` 下非空（20/20/4/4/4/20/5/4 行），R-01 四层覆盖从 ~0 变为 4.17%/29.17%/25%/25%，O-05 当前 T-Box 已有 85 概念（别名仍 0/18）。与此同时默认调用改为 400，S-14 默认主路径仍不出数——不能把「代码已修」说成「端到端默认可用」。
3. **16 条翻转中，9 条是验收栈数据边界造成的降级或无法判，而不是代码退化**：A-Box 为空（B03/R03/P01/B04）、无基线（S12/O03/O06）、import_item=0（S13）、字典 79 行（O01）。因此本批证据适合判「代码行为」，不适合判「端到端业务效果」；`q_S09` 的 PASS 也只覆盖 97 事件规模。
