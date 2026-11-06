# FIN-INS-022 · 13 个月保费继续率（口径族·索引）〔推测〕

> 来源档：**inferred**（provenance_label=推测｜evidence_basis=industry）
> publishable：**false**｜inference：**true**｜formula_disabled：true（仅族索引）｜domain：insurance
> 数据声明：本卡只登记口径，不含任何业务数值；平台出数结论一律为**合成数据、非业务结论**。
> 来源：`_fsldm/10-definitions-v5.seed.json`（v5，2026-11-06）；判定见 `_fsldm/10-口径判定-三项open.md` §2；基准见 `_fsldm/00-口径基准-v5.md` §3.1。

## 1. 族索引定义

原 `FIN-INS-022` 保留为口径族索引，**不单独出数**。13 个月保费继续率拆为两个并列变体：

- `FIN-INS-022-v1`：宽限期口径（协会原文可解释口径）
- `FIN-INS-022-v2`：自然月口径（公司月度管理口径）

两个变体分母相同、分子到账窗口不同，**不可混算、不可平均**。原 `formula_disabled=true` 保留在族索引行，防止平台把族入口当默认口径。

## 2. 变体对照

| 项 | FIN-INS-022-v1（宽限期） | FIN-INS-022-v2（自然月） |
| --- | --- | --- |
| definition | 评价期前溯 12 个月承保的期交新单，在第 1 个保单年度结束后的缴费宽限期内实收第 2 个保单年度首期规模保费，占该批新单首个保单年度实收规模保费的比例 | 评价期前溯 12 个月承保的期交新单，在第 13 个保单月（按保单周年日对齐）所在自然月内实收第 2 个保单年度首期规模保费，占该批新单首个保单年度实收规模保费的比例 |
| formula | `numerator / denominator * 100` | `numerator / denominator * 100` |
| numerator | 第 2 个保单年度首期应缴、且在第 1 个保单年度结束后宽限期截止日前实收的规模保费；按保单号去重；仅当期，不含复效补缴/以前年度欠费 | 第 13 个保单月所在自然月内实收的第 2 个保单年度首期规模保费；按保单号去重；不含宽限期跨月到账、不含复效补缴/以前年度欠费 |
| denominator | 该批新单首个保单年度实收规模保费；剔除趸交、犹豫期撤单、理赔终止、免缴、注销、迁出、效力中止、转换终止；单位 元 | 同 v1；单位 元 |
| observationPeriod | period（12 个月承保 cohort；观察至第 1 个保单年度结束后宽限期截止日；宽限期默认 60 天可配置） | period（12 个月承保 cohort；观察至第 13 个保单月所在自然月最后一日） |
| granularity | product（长期寿险期交新单） | product（长期寿险期交新单） |
| unit | % | % |
| 来源档 | inferred | inferred |
| publishable | false | false |
| formula_disabled | false | false |
| 生效日期 | 2026-11-06 | 2026-11-06 |

## 3. 为什么不能只有一个口径

- v1 按“宽限期”到账，容忍跨月到账，口径更宽；v2 按“自然月”到账，切齐财务月结，口径更严。
- 同一批保单在 v1 中可能计入宽限期内跨月到账，在 v2 中不计入；两者数值不可互换，也不可平均。
- 月度趋势、财务对账用 v2；协会/同业比较、合同宽限期解释用 v1。两个都保留，报表必须带 variant 后缀。

## 4. 证据与缺口

| 项 | 内容 |
| --- | --- |
| evidence_status | `EVIDENCE_MISSING` |
| missing | `regulatory_source` |
| 依据类型 | 行业/协会评价实践（非监管原文）+ 原文表述可解释推断 |
| 关键缺口 | 协会清晰版原文/条款截图；宽限期长度与复效补缴是否计入需配置；保单状态码（中止/失效/复效）定义需统一 |

**原文事实**：协会原文对 13/25 个月分子均写“首个保单年度宽限期内实收的规模保费”。13 个月可自洽；25 个月与锚点矛盾（见 FIN-INS-023）。本轮不虚构原文，只按业务合理性判定。

## 5. 平台可出数现状

- 族索引 `FIN-INS-022`：不可出数，`E_METRIC_FORMULA_DISABLED`（保留停用，防误用）。
- 变体 `FIN-INS-022-v1/v2`：口径完整，但**平台仍不可出数**；缺 `metric_kind/formula_expr/numerator_agg/denominator_agg/window_kind` 四元组，缺 `grace_end_date`、`premium_type`、`issue_date` 等字段，且无 `metric_observation`。不得标成“可算”。

## 6. 解除 `formulaDisabled` 建议

| 行 | 建议 |
| --- | --- |
| FIN-INS-022-v1 / v2 | `false`（本卡已按 false 登记） |
| FIN-INS-022（族索引） | 保留 `true`；如平台要求原 ID 可调用，必须显式重定向到默认变体（建议 v1），不得静默选口径 |
