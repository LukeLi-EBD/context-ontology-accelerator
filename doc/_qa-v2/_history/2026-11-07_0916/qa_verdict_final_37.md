# 最终 37 条判定分布（第一批 + 第二批收口）

> 本文件只写 `doc/_qa-v2/`，不改 `doc/_qa/`。
> 依据：`_qa-v2/evidence/`（2026-11-07 08:06:47 批次，8082）+ `_qa-v2/evidence-envfill/`（2026-11-07 08:58 批次，克隆栈 `platform-qa-fill` 8085）+ `_qa-v2/evidence-probe/`（8082 只读探针）。
> 8080/8082 未重启、未改配置；旧证据与 `_discarded/` 保持原样。

## 1 最终分布

| 判定 | 条数 | 编号 |
| --- | --- | --- |
| PASS | 21 | S00 S01 S02 S03 S07 S08 S09 S10 S11 S13 O01 O04 O06 M01 M02 M03 M05 M06 R01 R04 B03 |
| PARTIAL | 10 | S04 S05 S06 S14 O02 O05 M04 P02 P03 B04 |
| FAIL | 2 | R02 P01 |
| OFF | 1 | R05 |
| 证据完整但不足以下判 | 1 | R03 |
| 待修复后重判 | 2 | S12 O03 |
| **合计** | **37** | |

判定说明：
- `S12`、`O03` 的现有证据形态为 PARTIAL（有基线即 500），按约定**不写死 PASS/FAIL**，单列为「待修复后重判」，不计入上面五类。
- `O06` 记 PASS，但该 PASS **依赖显式 `from`**；默认路径的基线选择有缺陷，修复后需复测无参调用（见第 5 节）。
- `B03` 记 PASS，**仅覆盖实体页**（200/53ms，15s 超时未复现）；`neighbors` 返回 `edges=[]` 属克隆栈图配置边界，不作通过依据。
- `P01` 记 FAIL，归因「配置未合入」：栈上 `reasoning.abox_graphs` 仍只有 `abox:main`，与看板 `[abox:main, abox:synthetic]` 不一致；不下「已修复」结论。

## 2 相对原始判定翻转的 11 条

| 编号 | 原始 | 最终 | 翻转原因 |
| --- | --- | --- | --- |
| S01 | PARTIAL | PASS | 证据完整化 + 版本统一（21 条版本、指针唯一、verify ok） |
| S04 | PASS | PARTIAL | 两候选端点默认语义不同：`/candidates` 8 ≠ `/ui/api/candidates` 4（UI 默认 `state=pending`） |
| S12 | PASS | 待修复后重判 | 有基线即 500（`impact.py` `TypeError: unhashable type: 'list'`）；无基线时为空态 |
| O03 | PASS | 待修复后重判 | 同 S12，同一 `impact.py` 缺陷 |
| O04 | PARTIAL | PASS | 50 条证据包中含 2 条 fail 包，非法 path 有 `E_BUNDLE_MANIFEST` |
| O05 | FAIL | PARTIAL | 当前 T-Box 已含 85 概念；别名 0/18、checks 0、complete=false 仍未达标 |
| M01 | FAIL | PASS | 显式 `dataSource=synthetic` 下 8/8 可算（20/20/4/4/4/20/5/4 行） |
| R01 | PARTIAL | PASS | 灌数据后四层覆盖率 4.17%/29.17%/25%/25%，非 0 |
| R03 | PASS | 证据完整但不足以下判 | 指定 doc 哈希在该栈未注册；不用替身引用 |
| P02 | FAIL | PARTIAL | 指针/推理/术语/API 已解析到同一版本，旧「版本漂移」不成立 |
| P03 | PASS | PARTIAL | 用例给定的 DOC_REF 未注册，STALE 与 NOT_FOUND 未区分 |

其余 26 条与原始判定同向。第二批把 S13、O01、B03、P01 四条拉回原判（不再计入翻转），O06 按归因修正为 PASS。

## 3 37 条逐条判定与证据路径

路径前缀：`evidence/` = `doc/_qa-v2/evidence/`；`evidence-envfill/` = `doc/_qa-v2/evidence-envfill/`；`evidence-probe/` = `doc/_qa-v2/evidence-probe/`。

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
| q_S12 | PASS | 待修复后重判 | evidence-probe/q_S12__PROBE.txt |
| q_S13 | PASS | PASS | evidence-envfill/q_S13__ENVFILL.txt |
| q_S14 | PARTIAL | PARTIAL | evidence/q_S14.txt |
| q_O01 | PASS | PASS | evidence-envfill/q_O01__ENVFILL.txt |
| q_O02 | PARTIAL | PARTIAL | evidence/q_O02.txt |
| q_O03 | PASS | 待修复后重判 | evidence-probe/q_O03__PROBE.txt |
| q_O04 | PARTIAL | PASS | evidence/q_O04.txt |
| q_O05 | FAIL | PARTIAL | evidence/q_O05.txt |
| q_O06 | PASS | PASS（依赖显式 `from`） | evidence-probe/q_O06__PROBE.txt |
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
| S12 | 代码修复线：修 `impact.py` 的 `TypeError: unhashable type: 'list'`，并给出新镜像/提交号 | 在有基线版本的栈上重采 `?from=` 只读探针，看是否仍 500 |
| O03 | 同上（与 S12 同一缺陷、同一修复） | 同上 |
| O06 | 代码修复线：修默认基线选择（`healthboard.py` 默认取 index-1，当前版本恰在首位） | 修后复测**无参** `/health/ontology-diff`，不再依赖显式 `from` |
| P01 | 发布线：A-Box 分支合入 + 镜像替换，使 `reasoning.abox_graphs` 与看板图集一致 | 替换镜像后复测 named graph 分布与 `/reasoning/status` |
| R03 | 证据提供方：原报告引用的 doc 哈希需可复现（注册该 doc 或提供原始文档） | 注册后重采三个端点；若永远拿不到，保持「不可补证」 |
| q_S09 规模项 | 发布线：8080 镜像替换后按 15MB 量级复采 | 补 15MB 规模证据；现有 PASS 只覆盖 97 事件 |

另：`R02` 已判 FAIL（golden 10 例 passed 6，其 `passRate` 字段为 0.6），不属于「待补证」，但需产品修复后按同一 golden set 另案复测。

## 6 附记：`platform datagen --abox` 的易用性问题（不计入验收判定）

在官方事实表为空时，`platform datagen --schema synthetic --abox` 会在校验阶段抛 `E_METRIC_NO_DATA`（exit 78），导致无法只用 CLI 生成 A-Box。第二批改用 `generate_abox` 模块直接生成（304,919 triples / 60,420 instances），命令与原因记录在 `evidence-envfill/_isolation.json`。这是 CLI 易用性缺陷，单独记账，不改变任何一条验收判定。

## 7 隔离与留痕

- 克隆栈 `platform-qa-fill`：API 8085、PG 5435、reasoner 7885、embedding 8086；独立卷、独立网络；镜像 `agent-platform:0.1-s5`（`sha256:80cb274f…c605677`）。
- 8082 复核未变：document 39、metric_definition 85、metric_observation 37,471、fact_event 97、import_item 0；`tbox/current=ont-6e81732555e5`；`/readyz=ok`。
- 8080 容器未重启（旧镜像 `sha256:715d59e8…`，启动时间未变）。
- `doc/_qa/` 未写；`_qa-v2/evidence/` 未并入任何第二批产物；`_discarded/` 未改动。第二批无打错栈事件。
