# 最终 37 条判定分布（第一批 + 第二批 + 修复版重采）

> 版本说明：本版为**修复版重采后的最终口径**（S12/O03/O06 的正式依据已从补丁镜像切换为合并版 `merged-42`），并计入 2026-11-07 10:14 的 8080 只读复采（P01 由 FAIL 改判 PASS、q_S09 规模项在本栈证成）：**PASS 24 / PARTIAL 10 / FAIL 1 / OFF 1 / 证据完整但不足以下判 1 / 待修复后重判 0**。另计入 2026-11-07 10:50 在 8082 `merged-r02` 上对 `R02` 的独立复采（`passed 8/10`、`passRate 0.8`，按原判据「10 例通过」维持 FAIL，分布不变）。取代 2026-11-07 09:16 前的 21 PASS / 10 PARTIAL / 2 FAIL / 1 OFF / 1 不足以下判 / 2 待修复后重判。
> 改动前的版本已归档：`doc/_qa-v2/_history/2026-11-07_0916/qa_verdict_final_37.md`；本次改前版（P01 仍记 FAIL 的合并版口径）归档在 `doc/_qa-v2/_history/2026-11-07_1015/qa_verdict_final_37.md`（逐字副本）。另：`_history/2026-11-07_1005/` 那份是按编辑记录**反向重建的补丁依据版**，不是逐字副本。
> 本文件只写 `doc/_qa-v2/`，不改 `doc/_qa/`。
> 依据：`_qa-v2/evidence/`（2026-11-07 08:06:47 批次，8082）+ `_qa-v2/evidence-envfill/`（2026-11-07 08:58 批次，克隆栈 `platform-qa-fill` 8085）+ `_qa-v2/evidence-probe/`（8082 只读探针）+ `_qa-v2/evidence-fixprobe/`（2026-11-07 09:13 批次，补丁镜像，后缀 `__FIXPROBE`，**过程证据**）+ `_qa-v2/evidence-fixprobe-merged42/`（2026-11-07 10:02 批次，合并版镜像，后缀 `__MERGED42`，**S12/O03/O06 的正式依据**）+ `_qa-v2/evidence-8080-p01/`（2026-11-07 10:14 批次，**8080 实例**，后缀 `__8080P01`，**P01 与 q_S09 规模项的正式依据**）。
> 各批次独立成批，**永不互相并入**；判定按批次单独引用。
> 8082 只更换 api 容器（其它五个容器未动、未重启），未改数据、未跑迁移。8080 已由发布线替换为 `merged-42`，本轮只做**只读 GET / 只读 SQL / 只读 SPARQL**：未重启、未改配置、未跑迁移、未调用 `/reasoning/materialize`，采前采后快照一致。8085 克隆栈未触碰。旧证据与 `_discarded/` 保持原样。

## 1 最终分布

| 判定 | 条数 | 编号 |
| --- | --- | --- |
| PASS | 24 | S00 S01 S02 S03 S07 S08 S09 S10 S11 S12 S13 O01 O03 O04 O06 M01 M02 M03 M05 M06 R01 R04 B03 P01 |
| PARTIAL | 10 | S04 S05 S06 S14 O02 O05 M04 P02 P03 B04 |
| FAIL | 1 | R02 |
| OFF | 1 | R05 |
| 证据完整但不足以下判 | 1 | R03 |
| 待修复后重判 | 0 | — |
| **合计** | **37** | |

判定说明：
- `S12`、`O03` 已从「待修复后重判」转为 **PASS（限端点行为）**：`/ontology/impact` 与 `/ontology/impact/export` 均 200、结构完整、抽样重算一致。正式依据为合并版镜像 `agent-platform:merged-42`（`luke` `445d4ff`，schema 42，`sha256:731a4226…`）；补丁镜像 `agent-platform:fix-o03-o06`（`a6335a9`，`sha256:417d076d…`）那一轮保留为过程证据。只证明端点行为，不重复产品结论。
- `O06` 记 **PASS（默认路径已可用）**：合并版上无参 `/health/ontology-diff` 与 `/health/ontology-snapshot` 均 200，不再依赖显式 `from`。仍须保留说明：**显式 `from` 路径与无参默认路径两者都要覆盖，缺一不可**。默认基线仍会选中 `superseded` 的 smoke 版本，属产品策略缺口，见第 8 节，不影响本条判定。另记一处留痕：无参 `diff` 响应体 55398B（补丁版）→ 61894B（合并版），顶层键与各项计数相同，属**已知未解释的载荷差异，不影响判定**。
- `B03` 记 PASS，**仅覆盖实体页**（200/53ms，15s 超时未复现）；`neighbors` 返回 `edges=[]` 属克隆栈图配置边界，不作通过依据。
- `P01` 由 FAIL 改判 **PASS（限图集一致性，限 8080 实例）**：8080 上 `/reasoning/status` 的 `aboxGraphs` 与 `/health/dashboard` 的 `coverage.instances.graphs` 为同一集合 `{urn:platform:graph:abox:main, urn:platform:graph:abox:synthetic}`；`abox:main`=0、`abox:synthetic`=304,919、合计非 0、派生 `emptyAbox=false`。依据 `evidence-8080-p01/q_P01__8080P01.txt`。
  **边界一（正文级）**：`[abox:main, abox:synthetic]` 只存在于 **8080 实例的 `platform.yaml`**，**仓库默认配置未改**；换任何新栈重新部署，`reasoning.abox_graphs` 会回到 `[abox:main]`，P01 的不一致就会重现。因此这个 PASS 是「当前实例 + 当前本地配置」下的结论，**不是「产品默认行为已正确」**。
  **边界二**：`inferredTriples=1,171` 全部来自 `urn:platform:inferred:ont-11f92ebb3326` 的 T-Box materialize 作业（`lastJob=succeeded`）；**A-Box 未被推理器处理**，不得引伸为「推理已覆盖 A-Box」。
  相邻读数（不影响本条判定，但不得据此宣称推理链路无异常）：看板 `inferenceFailures.count=336` 为历史失败作业累计，与 `lastJob=succeeded` 并存；`shaclViolations.versionId=ont-draft-b814289626a0` 是旧导入记录的抽样，非当前指针 `ont-11f92ebb3326`。
- `R02` **维持 FAIL**。判据原文（逐字，出处三处同文）：「**10 例通过；拒答必带缺层；citation 覆盖按类型统计；断链率不退化**」——`doc/_design/52-后续路线图-v1.md` R-02 需求行、`doc/_qa/q_R02_R-02 引用与拒答质量闭环（10 例 golden set）.md` 第 48 行、`doc/_qa/run_qa.py` 第 706 行 `exp` 字段。判定尺度只认「10 例全部通过」，**0.8 不等于达标**。依据 `evidence-r02-rejudge/q_R02__R02REJUDGE.txt`（8082 `merged-r02`）。
  **工程侧已无剩余可修项**：`citationResolvableRate=1.0`（39/39）、`brokenLinkRate=0.0`（`regression=false`）、`refusalsWithoutLayers=[]`、`prov_event` 79→79（评估 `persist=False`，PROV 零写入）。差的两例中，**G05 卡点在知识供给；G06 为知识供给 + 门限/问法待决**（见下条注记），不得当作代码 bug 反复返工，也不得据此给豁免或加权。
  知识缺口映射（只作注释，不替代判定）：G05 → P1 的 `Q-07`～`Q-14`（缺口 KG-01，保留期限）；G06 → P1 的 `Q-15`～`Q-23`（KG-03 触发条件 `Q-15`～`Q-17` + KG-02 处置流程 `Q-18`～`Q-22` + 依据 `Q-23`）。清单见 `doc/_design/knowledge-gap/03-待业务确认问题清单-2026-11-07.md`。
  **G06 门限/问法限定（事实注记，不改判据）**：清单 `03-待业务确认问题清单-2026-11-07.md` 第 79 行自带注释——**即使 `Q-15`～`Q-23` 全部回答，G06 在当前覆盖度门限下仍可能不过线**，属 golden 问法或门限设定问题，需 A/E 决策。因此 G06 的障碍是两层：**知识缺口（KG-02/KG-03）+ 可能的门限/问法问题**；G05 只有知识缺口（KG-01，`Q-07`～`Q-14`）一层。本条注记**不构成豁免、不调整判据、不改 golden**，`R02` 维持 FAIL。

## 2 相对原始判定翻转的 10 条

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
| P01 | FAIL | PASS | 8080 实例复采：`aboxGraphs` 与看板图集同集合 `{abox:main, abox:synthetic}`、`abox:main`=0 + `abox:synthetic`=304,919、`emptyAbox=false`。**限图集一致性、限 8080 实例**：两图只写在 8080 的 `platform.yaml`，仓库默认配置未改，换新栈会重现 |

`S12`、`O03` 原判 PASS，中途因 `impact.py` 缺陷一度列为「待修复后重判」，修复版重采后回到 **PASS（限端点行为）**——方向与原始判定一致，故不计入翻转，但判据已按修复版证据重写（见第 1 节说明与第 5 节）。`O06` 原判 PASS、最终 PASS（默认路径已可用），同上不计翻转。

其余 27 条与原始判定同向。第二批把 S13、O01、B03 三条拉回原判（不再计入翻转）；P01 原判 FAIL，8080 复采后转 PASS，已计入上述翻转表。

## 3 37 条逐条判定与证据路径

路径前缀：`evidence/` = `doc/_qa-v2/evidence/`；`evidence-envfill/` = `doc/_qa-v2/evidence-envfill/`；`evidence-probe/` = `doc/_qa-v2/evidence-probe/`；`evidence-fixprobe/` = `doc/_qa-v2/evidence-fixprobe/`（补丁镜像过程证据，后缀 `__FIXPROBE`）；`evidence-fixprobe-merged42/` = `doc/_qa-v2/evidence-fixprobe-merged42/`（合并版正式依据，后缀 `__MERGED42`）；`evidence-8080-p01/` = `doc/_qa-v2/evidence-8080-p01/`（8080 实例正式依据，后缀 `__8080P01`）。各批次独立，永不并入其它批次。

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
| q_S09 | PASS | PASS（规模项已在本栈证成） | evidence-8080-p01/q_S09__8080P01.txt（原 `evidence/q_S09.txt` 仅 97 事件，降为过程证据） |
| q_S10 | PASS | PASS | evidence/q_S10.txt |
| q_S11 | PASS | PASS | evidence/q_S11.txt |
| q_S12 | PASS | PASS（限端点行为） | evidence-fixprobe-merged42/q_S12__MERGED42.txt |
| q_S13 | PASS | PASS | evidence-envfill/q_S13__ENVFILL.txt |
| q_S14 | PARTIAL | PARTIAL | evidence/q_S14.txt |
| q_O01 | PASS | PASS | evidence-envfill/q_O01__ENVFILL.txt |
| q_O02 | PARTIAL | PARTIAL | evidence/q_O02.txt |
| q_O03 | PASS | PASS（限端点行为） | evidence-fixprobe-merged42/q_O03__MERGED42.txt |
| q_O04 | PARTIAL | PASS | evidence/q_O04.txt |
| q_O05 | FAIL | PARTIAL | evidence/q_O05.txt |
| q_O06 | PASS | PASS（默认路径已可用） | evidence-fixprobe-merged42/q_O06__MERGED42.txt |
| q_M01 | FAIL | PASS | evidence/q_M01.txt |
| q_M02 | PASS | PASS | evidence/q_M02.txt |
| q_M03 | PASS | PASS | evidence/q_M03.txt |
| q_M04 | PARTIAL | PARTIAL | evidence-envfill/q_M04__ENVFILL.txt |
| q_M05 | PASS | PASS | evidence/q_M05.txt |
| q_M06 | PASS | PASS | evidence/q_M06.txt |
| q_R01 | PARTIAL | PASS | evidence/q_R01.txt |
| q_R02 | FAIL | FAIL | evidence-r02-rejudge/q_R02__R02REJUDGE.txt（原 `evidence/q_R02.txt` 为 6/10 旧读数，降为过程证据） |
| q_R03 | PASS | 证据完整但不足以下判 | evidence-envfill/q_R03__ENVFILL.txt |
| q_R04 | PASS | PASS | evidence/q_R04.txt |
| q_R05 | OFF | OFF | evidence/q_R05.txt |
| q_B03 | PASS | PASS（仅实体页） | evidence-envfill/q_B03__ENVFILL.txt |
| q_B04 | PARTIAL | PARTIAL | evidence/q_B04.txt |
| q_P01 | FAIL | PASS（限图集一致性，限 8080 实例） | evidence-8080-p01/q_P01__8080P01.txt（原 `evidence-envfill/q_P01__ENVFILL.txt` 记录的是配置未合入时的单图状态，降为过程证据） |
| q_P02 | FAIL | PARTIAL | evidence/q_P02.txt |
| q_P03 | PASS | PARTIAL | evidence/q_P03.txt |

`M04` 的 PARTIAL 结论必须与数据一起读：口径卡已生成（`cardState=built`），但 `withSourceRef=0`、`/prov/decisions` count=0，不得只写「口径卡已生成」。

## 4 维持不可下判的条目

| 编号 | 结论 | 为什么不下判 |
| --- | --- | --- |
| R03 | 证据完整但不足以下判 | 原报告指定的 doc 哈希 `src://doc/4981174b...` 在克隆栈未注册（`E_SOURCE_REF_NOT_FOUND`）；实体与溯源可读，但字段 `withSourceRef=0`。按约定不用替身引用、不用近似哈希凑 PASS。 |

此前同为「证据完整但不足以下判」的另外 2 条已有第二批证据下判：`B03` → PASS（限实体页），`P01` → PASS（限图集一致性，限 8080 实例）。因此最终只剩 `R03` 一条维持不可下判。

## 5 仍待外部动作才能复测的条目

| 编号 | 在等谁 / 等什么 | 复测动作 |
| --- | --- | --- |
| R03 | 证据提供方：原报告引用的 doc 哈希需可复现（注册该 doc 或提供原始文档） | 注册后重采三个端点；若永远拿不到，保持「不可补证」 |

已移出本表（2026-11-07 10:14，8080 只读复采，`evidence-8080-p01/`）：
- `P01`：已在 8080（`merged-42`）上完成复测，图集一致性 PASS。**但外部动作并未消失**：`[abox:main, abox:synthetic]` 只写在 8080 的 `platform.yaml`，仓库默认配置仍未合入，换新栈会重现；该缺口不再阻塞判定，仍登记为已知缺口（见第 1 节边界一）。
- `q_S09` 规模项：已在同一栈上按 15MB 量级复采证成（`declaredBytes=capturedBytes=15,195,251`、`truncated=false`、`count` 与库内 `fact_event=10,146` 一致、十进制 15.20MB），不再以 97 事件为唯一依据。

已移出本表：`S12`、`O03`、`O06` 先后在 8082 上复测两轮——2026-11-07 09:13 补丁镜像 `fix-o03-o06`（过程证据 `evidence-fixprobe/`）、10:02 合并版镜像 `merged-42`（正式依据 `evidence-fixprobe-merged42/`）；两轮结论一致，分别为 PASS（限端点行为）与 PASS（默认路径已可用）。

另：`R02` **维持 FAIL**（8082 `merged-r02` 复采：golden 10 例 `passed 8` / `passRate 0.8`，未达原判据「10 例通过」）。工程侧无剩余可修项；G05 卡点在知识供给，G06 为知识供给 + 门限/问法待决，详见第 1 节；原 `evidence/q_R02.txt`（6/10）降为过程证据，正式依据为 `evidence-r02-rejudge/q_R02__R02REJUDGE.txt`。

## 6 附记：`platform datagen --abox` 的易用性问题（不计入验收判定）

在官方事实表为空时，`platform datagen --schema synthetic --abox` 会在校验阶段抛 `E_METRIC_NO_DATA`（exit 78），导致无法只用 CLI 生成 A-Box。第二批改用 `generate_abox` 模块直接生成（304,919 triples / 60,420 instances），命令与原因记录在 `evidence-envfill/_isolation.json`。这是 CLI 易用性缺陷，单独记账，不改变任何一条验收判定。

## 7 隔离与留痕

- 克隆栈 `platform-qa-fill`：API 8085、PG 5435、reasoner 7885、embedding 8086；独立卷、独立网络；镜像 `agent-platform:0.1-s5`（`sha256:80cb274f…c605677`）。
- 8082 合并版：api 容器为 `agent-platform:merged-42`（`luke` 线、提交 `445d4ff`，`sha256:731a4226…`，启动 `2026-11-07T02:00:27Z`）；合并版读数 `SUPPORTED_SCHEMA_VERSION=42`、`MAX(schema_version.version)=42`、迁移记录 40 行（V35/V36 缺口，行数与版本号含义不同）。
- 8082 补丁版（过程证据）：api 容器 `agent-platform:fix-o03-o06`（从 `a6335a9` 构建，`sha256:417d076d…`，启动 `2026-11-07T01:09:32Z`）；回退锚点 `D:\agentABC\_tmp\anchor-8082.txt`。
- 8082 采前采后快照完全一致：document 39、metric_definition 85、metric_observation 37,471、fact_event 97、import_item 0；`tbox/current=ont-6e81732555e5`；`/readyz=200`。（合并版批次 pointer 行的 `updated_at` 为 `2026-11-07 09:49:40+08`，由栈重新部署时的指针恢复刷新，版本 id 未变，采前采后同值。）
- 8080 实例：api 容器为 `agent-platform:merged-42`（`sha256:731a4226…`，启动 `2026-11-07T02:05:29Z`）；`SUPPORTED_SCHEMA_VERSION=42`、`MAX(schema_version.version)=42`、迁移记录 40 行。指针 `tbox/current=ont-11f92ebb3326`、`semver=1.2.1`、`tripleCount=3625`、`updatedAt=2026-11-07 05:37:38+08`（`updatedBy=smoke-restore`，版本 id 未变）。本轮**只读**采集：未重启容器、未改配置、未跑迁移、未调用 `/reasoning/materialize`；采前采后快照一致（document 3,066、metric_definition 85、metric_observation 37,477、fact_event 10,146、import_item 484、指针版本 id、`/readyz=200`）。
- `doc/_qa/` 未写；`_qa-v2/evidence/`、`evidence-envfill/` 未并入任何后续批次产物；`evidence-fixprobe/`、`evidence-fixprobe-merged42/`、`evidence-8080-p01/`、`evidence-r02-rejudge/` 各自独立成批，后缀分别为 `__FIXPROBE`、`__MERGED42`、`__8080P01`、`__R02REJUDGE`，永不并入其它批次；`_discarded/` 未改动。各批次均无打错栈事件。
- `evidence-r02-rejudge/`（2026-11-07 10:50 批次，8082 `agent-platform:merged-r02`，`sha256:adf44d20…`，启动 `2026-11-07T02:46:33Z`）：仅两条只读 GET（`/answer/quality`、`/prov/refusals`），未重启、未改配置、未跑迁移；采前采后六项计数（document 39、metric_definition 85、metric_observation 37,471、fact_event 97、import_item 0、prov_event 79）与指针 `ont-6e81732555e5`、`/readyz=200` 全部一致；`persist=False`，PROV 增量为 0。

## 8 产品策略缺口：默认基线会选中 `superseded` 的 smoke 版本（不计入本轮判定，不改判定结果）

事实（`evidence-fixprobe-merged42/q_O06__MERGED42.txt`，2026-11-07 10:02，8082 合并版；补丁镜像 09:13 那一轮关键字段读数相同，但响应体大小不同，见第 1 节）：

- 无参 `GET /health/ontology-diff` 返回 200，默认解析为 `from=ont-6fd83aa720b9`、`to=ont-6e81732555e5`。
- 默认的 `from` 为 `semver=12.0.2`、状态 `superseded`，图上只有 3 triples / 1 class（`urn:platform:smoke:s12:14c81e05:Alpha`）。
- `to` 为当前指针版本 `ont-6e81732555e5`（`semver=0.0.0`、`published`、3340 triples）。
- 因此 `counts` 为 `addedTriples=3340`、`removedTriples=3`，删除侧全部来自该 smoke 版本残留；默认路径虽 200 可用，但信息量小，容易被误读为「当前基线有 3 条真实删除」。

定性：这是**默认基线选择策略**的缺口，不是端点故障。本轮只证明「默认路径已可用」，该策略问题**不计入本轮判定，也不改动 `O06` 的 PASS**。

本轮不修。后续可选方向（仅列排期参考，非本轮动作）：默认跳过 `purpose=smoke` 的版本；或新增显式 `includeSmoke` 参数并保持默认行为向后兼容；或在响应里回显基线状态与 `warnings`。

验收口径不因此改变：**显式 `from`（`S12`/`O03` 覆盖）与无参默认路径（`O06` 覆盖）两者都要覆盖，缺一不可。**
