<!-- 生成方式：按 2026-11-07 合并版一轮的编辑记录反向重建——以当前合并版文件为起点，逐条逆向应用本轮全部替换（doc1 14 处 / doc2 16 处），每条均唯一命中；逆向终点是当时每处编辑实际匹配到的原文，未凭印象补写。 -->
<!-- 不可逐字重建段落：无。已断言重建件不含 merged-42 / MERGED42 / 445d4ff / 10:02 字样，且 S12/O03/O06 依据行均回到 fix-o03-o06。 -->
<!-- 留痕说明：这份存档的存在本身即说明 10:05 时未在改前落档，可追溯性有缺口；它是重建件，不是完整历史，不应被包装为逐字副本。 -->

# 最终 37 条判定分布（第一批 + 第二批 + 修复版重采）

> 版本说明：本版为**修复版重采后的最终口径**，取代 2026-11-07 09:16 前的 21 PASS / 10 PARTIAL / 2 FAIL / 1 OFF / 1 不足以下判 / 2 待修复后重判。
> 改动前的版本已归档：`doc/_qa-v2/_history/2026-11-07_0916/qa_verdict_final_37.md`。
> 本文件只写 `doc/_qa-v2/`，不改 `doc/_qa/`。
> 依据：`_qa-v2/evidence/`（2026-11-07 08:06:47 批次，8082）+ `_qa-v2/evidence-envfill/`（2026-11-07 08:58 批次，克隆栈 `platform-qa-fill` 8085）+ `_qa-v2/evidence-probe/`（8082 只读探针）+ `_qa-v2/evidence-fixprobe/`（2026-11-07 09:13 批次，8082 修复版镜像，后缀 `__FIXPROBE`）。
> 修复版批次独立成批，**永不并入 `evidence/` 或 `evidence-envfill/`**；判定按批次单独引用。
> 8080/8085 未触碰；8082 只更换 api 容器（其它五个容器未动、未重启），未改数据、未跑迁移；旧证据与 `_discarded/` 保持原样。

## 1 最终分布

| 判定 | 条数 | 编号 |
| --- | --- | --- |
| PASS | 23 | S00 S01 S02 S03 S07 S08 S09 S10 S11 S12 S13 O01 O03 O04 O06 M01 M02 M03 M05 M06 R01 R04 B03 |
| PARTIAL | 10 | S04 S05 S06 S14 O02 O05 M04 P02 P03 B04 |
| FAIL | 2 | R02 P01 |
| OFF | 1 | R05 |
| 证据完整但不足以下判 | 1 | R03 |
| 待修复后重判 | 0 | — |
| **合计** | **37** | |

判定说明：
- `S12`、`O03` 已从「待修复后重判」转为 **PASS（限端点行为）**：`/ontology/impact` 与 `/ontology/impact/export` 均 200、结构完整、抽样重算一致。该判定依赖修复提交 `a6335a9` 与 8082 修复版镜像 `agent-platform:fix-o03-o06`（`sha256:417d076d…`）；只证明端点行为，不重复产品结论。
- `O06` 记 **PASS（默认路径已可用）**：修复版上无参 `/health/ontology-diff` 与 `/health/ontology-snapshot` 均 200，不再依赖显式 `from`。仍须保留说明：**显式 `from` 路径与无参默认路径两者都要覆盖，缺一不可**。默认基线会选中 `superseded` 的 smoke 版本，属产品策略缺口，见第 8 节，不影响本条判定。
- `B03` 记 PASS，**仅覆盖实体页**（200/53ms，15s 超时未复现）；`neighbors` 返回 `edges=[]` 属克隆栈图配置边界，不作通过依据。
- `P01` 记 FAIL，归因「配置未合入」：栈上 `reasoning.abox_graphs` 仍只有 `abox:main`，与看板 `[abox:main, abox:synthetic]` 不一致；不下「已修复」结论。

## 2 相对原始判定翻转的 9 条

| 编号 | 原始 | 最终 | 翻转原因 |
| --- | --- | --- | --- |
| S01 | PARTIAL | PASS | 证据完整化 + 版本统一（21 条版本、指针唯一、verify ok） |
| S04 | PASS | PARTIAL | 两候选端点默认语义不同：`/candidates` 8 ≠ `/ui/api/candidates` 4（UI 默认 `state=pending`） |
| O04 | PARTIAL | PASS | 50 条证据包中含 2 条 fail 包，非法 path 有 `E_BUNDLE_MANIFEST` |
| O05 | FAIL | PARTIAL | 当前 T-Box 已含 85 概念；别名 0/18、checks 0、complete=false 仍未达标 |
| M01 | FAIL | PASS | 显式 `dataSource=synthetic` 下 8/8 可算（20/20/4/4/4/20/5/4 行） |
| R01 | PARTIAL | PASS | 灌数据后四层覆盖率 4.17%/29.17%/25%/25%，非 0 |
| R03 | PASS | 证据完整但不足以下判 | 指定 doc 哈希在该栈未注册；不用替身引用 |
| P02 | FAIL | PARTIAL | 指针/推理/术语/API 已解析到同一版本，旧「版本漂移」不成立 |
| P03 | PASS | PARTIAL | 用例给定的 DOC_REF 未注册，STALE 与 NOT_FOUND 未区分 |

`S12`、`O03` 原判 PASS，中途因 `impact.py` 缺陷一度列为「待修复后重判」，修复版重采后回到 **PASS（限端点行为）**——方向与原始判定一致，故不计入翻转，但判据已按修复版证据重写（见第 1 节说明与第 5 节）。`O06` 原判 PASS、最终 PASS（默认路径已可用），同上不计翻转。

其余 28 条与原始判定同向。第二批把 S13、O01、B03、P01 四条拉回原判（不再计入翻转）。

## 3 37 条逐条判定与证据路径

路径前缀：`evidence/` = `doc/_qa-v2/evidence/`；`evidence-envfill/` = `doc/_qa-v2/evidence-envfill/`；`evidence-probe/` = `doc/_qa-v2/evidence-probe/`；`evidence-fixprobe/` = `doc/_qa-v2/evidence-fixprobe/`（修复版独立批次，后缀 `__FIXPROBE`，永不并入前两者）。

| 编号 | 原始 | 最终 | 证据文件 |
| --- | --- | --- | --- |
| q_S00 | PASS | PASS | evidence/q_S00.txt |
| q_S01 | PARTIAL | PASS | evidence/q_S01.txt |
| q_S02 | PASS | PASS | evidence/q_S02.txt |
| q_S03 | PASS | PASS | evidence/q_S03.txt |
| q_S04 | PASS | PARTIAL | evidence/q_S04.txt |
| q_S05 | PARTIAL | PARTIAL | evidence/q_S05.txt |
| q_S06 | PARTIAL | PARTIAL | evidence/q_S06.txt |
| q_S07 | PASS | PASS | evidence/q_S07.txt |
| q_S08 | PASS | PASS | evidence-envfill/q_S08__ENVFILL.txt |
| q_S09 | PASS | PASS | evidence/q_S09.txt（仅 97 事件规模） |
| q_S10 | PASS | PASS | evidence/q_S10.txt |
| q_S11 | PASS | PASS | evidence/q_S11.txt |
| q_S12 | PASS | PASS（限端点行为） | evidence-fixprobe/q_S12__FIXPROBE.txt |
| q_S13 | PASS | PASS | evidence-envfill/q_S13__ENVFILL.txt |
| q_S14 | PARTIAL | PARTIAL | evidence/q_S14.txt |
| q_O01 | PASS | PASS | evidence-envfill/q_O01__ENVFILL.txt |
| q_O02 | PARTIAL | PARTIAL | evidence/q_O02.txt |
| q_O03 | PASS | PASS（限端点行为） | evidence-fixprobe/q_O03__FIXPROBE.txt |
| q_O04 | PARTIAL | PASS | evidence/q_O04.txt |
| q_O05 | FAIL | PARTIAL | evidence/q_O05.txt |
| q_O06 | PASS | PASS（默认路径已可用） | evidence-fixprobe/q_O06__FIXPROBE.txt |
| q_M01 | FAIL | PASS | evidence/q_M01.txt |
| q_M02 | PASS | PASS | evidence/q_M02.txt |
| q_M03 | PASS | PASS | evidence/q_M03.txt |
| q_M04 | PARTIAL | PARTIAL | evidence-envfill/q_M04__ENVFILL.txt |
| q_M05 | PASS | PASS | evidence/q_M05.txt |
| q_M06 | PASS | PASS | evidence/q_M06.txt |
| q_R01 | PARTIAL | PASS | evidence/q_R01.txt |
| q_R02 | FAIL | FAIL | evidence/q_R02.txt |
| q_R03 | PASS | 证据完整但不足以下判 | evidence-envfill/q_R03__ENVFILL.txt |
| q_R04 | PASS | PASS | evidence/q_R04.txt |
| q_R05 | OFF | OFF | evidence/q_R05.txt |
| q_B03 | PASS | PASS（仅实体页） | evidence-envfill/q_B03__ENVFILL.txt |
| q_B04 | PARTIAL | PARTIAL | evidence/q_B04.txt |
| q_P01 | FAIL | FAIL | evidence-envfill/q_P01__ENVFILL.txt |
| q_P02 | FAIL | PARTIAL | evidence/q_P02.txt |
| q_P03 | PASS | PARTIAL | evidence/q_P03.txt |

`M04` 的 PARTIAL 结论必须与数据一起读：口径卡已生成（`cardState=built`），但 `withSourceRef=0`、`/prov/decisions` count=0，不得只写「口径卡已生成」。

## 4 维持不可下判的条目

| 编号 | 结论 | 为什么不下判 |
| --- | --- | --- |
| R03 | 证据完整但不足以下判 | 原报告指定的 doc 哈希 `src://doc/4981174b...` 在克隆栈未注册（`E_SOURCE_REF_NOT_FOUND`）；实体与溯源可读，但字段 `withSourceRef=0`。按约定不用替身引用、不用近似哈希凑 PASS。 |

此前同为「证据完整但不足以下判」的另外 2 条已有第二批证据下判：`B03` → PASS（限实体页），`P01` → FAIL（配置未合入）。因此最终只剩 `R03` 一条维持不可下判。

## 5 仍待外部动作才能复测的条目

| 编号 | 在等谁 / 等什么 | 复测动作 |
| --- | --- | --- |
| P01 | 发布线：A-Box 分支合入 + 镜像替换，使 `reasoning.abox_graphs` 与看板图集一致 | 替换镜像后复测 named graph 分布与 `/reasoning/status` |
| R03 | 证据提供方：原报告引用的 doc 哈希需可复现（注册该 doc 或提供原始文档） | 注册后重采三个端点；若永远拿不到，保持「不可补证」 |
| q_S09 规模项 | 发布线：8080 镜像替换后按 15MB 量级复采 | 补 15MB 规模证据；现有 PASS 只覆盖 97 事件 |

已移出本表：`S12`、`O03`、`O06` 于 2026-11-07 09:13 在 8082 修复版镜像上复测完成，结论分别为 PASS（限端点行为）与 PASS（默认路径已可用），证据见 `evidence-fixprobe/`。

另：`R02` 已判 FAIL（golden 10 例 passed 6，其 `passRate` 字段为 0.6），不属于「待补证」，但需产品修复后按同一 golden set 另案复测。

## 6 附记：`platform datagen --abox` 的易用性问题（不计入验收判定）

在官方事实表为空时，`platform datagen --schema synthetic --abox` 会在校验阶段抛 `E_METRIC_NO_DATA`（exit 78），导致无法只用 CLI 生成 A-Box。第二批改用 `generate_abox` 模块直接生成（304,919 triples / 60,420 instances），命令与原因记录在 `evidence-envfill/_isolation.json`。这是 CLI 易用性缺陷，单独记账，不改变任何一条验收判定。

## 7 隔离与留痕

- 克隆栈 `platform-qa-fill`：API 8085、PG 5435、reasoner 7885、embedding 8086；独立卷、独立网络；镜像 `agent-platform:0.1-s5`（`sha256:80cb274f…c605677`）。
- 8082 修复版：只替换 api 容器为 `agent-platform:fix-o03-o06`（从 `a6335a9` 构建，`sha256:417d076d…`，启动 `2026-11-07T01:09:32Z`）；postgres / reasoner / embedding / oxigraph 启动时间仍为 2026-11-06，未动；回退锚点 `D:\agentABC\_tmp\anchor-8082.txt`。
- 8082 采前采后快照完全一致：document 39、metric_definition 85、metric_observation 37,471、fact_event 97、import_item 0；`tbox/current=ont-6e81732555e5`；`/readyz=200`。
- 8080 容器未重启（旧镜像 `sha256:715d59e8…`，启动时间未变）。
- `doc/_qa/` 未写；`_qa-v2/evidence/`、`evidence-envfill/` 未并入任何后续批次产物；`evidence-fixprobe/` 独立成批；`_discarded/` 未改动。第二批与修复版批次均无打错栈事件。

## 8 产品策略缺口：默认基线会选中 `superseded` 的 smoke 版本（不计入本轮判定，不改判定结果）

事实（`evidence-fixprobe/q_O06__FIXPROBE.txt`，2026-11-07 09:13，8082 修复版）：

- 无参 `GET /health/ontology-diff` 返回 200，默认解析为 `from=ont-6fd83aa720b9`、`to=ont-6e81732555e5`。
- 默认的 `from` 为 `semver=12.0.2`、状态 `superseded`，图上只有 3 triples / 1 class（`urn:platform:smoke:s12:14c81e05:Alpha`）。
- `to` 为当前指针版本 `ont-6e81732555e5`（`semver=0.0.0`、`published`、3340 triples）。
- 因此 `counts` 为 `addedTriples=3340`、`removedTriples=3`，删除侧全部来自该 smoke 版本残留；默认路径虽 200 可用，但信息量小，容易被误读为「当前基线有 3 条真实删除」。

定性：这是**默认基线选择策略**的缺口，不是端点故障。本轮只证明「默认路径已可用」，该策略问题**不计入本轮判定，也不改动 `O06` 的 PASS**。

本轮不修。后续可选方向（仅列排期参考，非本轮动作）：默认跳过 `purpose=smoke` 的版本；或新增显式 `includeSmoke` 参数并保持默认行为向后兼容；或在响应里回显基线状态与 `warnings`。

验收口径不因此改变：**显式 `from`（`S12`/`O03` 覆盖）与无参默认路径（`O06` 覆盖）两者都要覆盖，缺一不可。**
