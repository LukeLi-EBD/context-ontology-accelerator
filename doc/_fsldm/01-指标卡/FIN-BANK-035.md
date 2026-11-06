# FIN-BANK-035 · 催收回收率〔推测〕

> 来源档：**inferred**（provenance_label=推测｜evidence_basis=industry）
> publishable：**false**｜inference：**true**｜formula_disabled：false｜domain：bank
> 数据声明：本卡只登记口径，不含任何业务数值；平台出数结论一律为**合成数据、非业务结论**。
> 来源：`_fsldm/10-definitions-v5.seed.json`（v5，2026-11-06）；判定见 `_fsldm/10-口径判定-三项open.md` §4.3；基准见 `_fsldm/00-口径基准-v5.md` §3.6。

## 1. 定义

观察期初已进入催收的逾期资产，在观察期内以现金方式回收的本金占期初应催收本金余额的比例。

## 2. 公式与分母（唯一分母）

| 项 | 内容 |
| --- | --- |
| formula | `numerator / denominator * 100` |
| numerator | 观察期内该期初 cohort 的现金回收本金；不含利息、费用、罚息；不含核销后回收；不含以物抵债/重组；按收款流水去重；单位 元 |
| denominator | 观察期初（T0 日终）状态=催收中且逾期本金>0 的账户本金余额；按账户去重；剔除已核销、已转出、已重组退出催收、内部往来、测试账户、已结清；单位 元 |
| observationPeriod | period（3/6/12 个月；cohort=期初在催账户；期末观察） |
| granularity | institution/product，可按催收渠道 |
| unit | % |

**为什么分母是“期初在催 cohort”而不是“期内累计应催金额”**：用期内累计会把新进案件、核销转出混进分母，导致分母漂移、口径不可比；用期初 cohort 可以回答“这批存量案件在观察期内回收了多少”。本金对本金，避免利息/费用导致回收率 >100%；现金回收才是可验证的回收能力，以物抵债/重组另设口径。

## 3. 排除项（固定）

- 已核销、已转出、已重组退出催收的账户；
- 内部往来、测试账户、已结清账户；
- 利息、费用、罚息不计入分子；
- 核销后回收单列 memo，不计入本指标；
- 期初 cohort 之后新进入催收的案件不计入分母。

## 4. 证据与缺口

| 项 | 内容 |
| --- | --- |
| evidence_status | `EVIDENCE_MISSING` |
| missing | `regulatory_source` |
| 依据类型 | 行业通行催收管理实践（未成文）+ 本轮业务合理性拍板 |
| 关键缺口 | `collection_case`（`case_id`、`account_id`、`enter_date`、`exit_date`、`status`、`principal`）、`recovery_cash`（`receipt_date`、`principal_component`、`interest_component`、`fee_component`）、`writeoff`、`restructure_flag`；当前无催收案件/回收流水实体 |

## 5. 平台可出数现状

**不可出数**：口径已完整，但缺催收事实表与四元组；不得标成“可算”。

## 6. 风险与复查触发

- 期初 cohort 只反映存量案件，不是全期催收绩效；若业务要全期回收率，另设指标；
- 核销后回收单列 memo；
- 催收状态定义（M1/M2/M3、委外/自催）需统一；
- 已重组退出案件的回收需排除；
- 业务书面签字到位后可评估 `publishable` 提升。
