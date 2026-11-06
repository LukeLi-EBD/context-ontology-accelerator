# FIN-BANK-031 · 申请通过率〔推测〕

> 来源档：**inferred**（provenance_label=推测｜evidence_basis=industry）
> publishable：**false**｜inference：**true**｜formula_disabled：false｜domain：bank
> 数据声明：本卡只登记口径，不含任何业务数值；平台出数结论一律为**合成数据、非业务结论**。
> 来源：`_fsldm/10-definitions-v5.seed.json`（v5，2026-11-06）；判定见 `_fsldm/10-口径判定-三项open.md` §4.1；基准见 `_fsldm/00-口径基准-v5.md` §3.4。

## 1. 定义

统计期内首次受理的信贷申请中，在观察截止日（期末 + 30 天）前完成审批且结论为通过的申请笔数，占统计期内首次受理申请笔数的比例。

## 2. 公式与分母（唯一分母）

| 项 | 内容 |
| --- | --- |
| formula | `numerator / denominator * 100` |
| numerator | 该受理 cohort 中审批完成且结论=通过的申请笔数；含有条件通过；不含否决、退回未重提、客户撤销、系统作废、未决；按申请号去重；单位 笔 |
| denominator | 统计期内首次受理的信贷申请笔数；按申请号去重；以受理日期落窗；剔除同一客户+同一产品+金额±10% 在 30 天内的重复提交（只算首笔）、客户撤销、系统作废、测试/内部申请、纯咨询未形成申请；单位 笔 |
| observationPeriod | period（月度；cohort=受理日期在统计期；审批观察截止=期末 + 30 天；未决率单独披露） |
| granularity | institution/channel（机构/渠道），可按 product |
| unit | % |

**为什么分母不用“审批完成笔数”**：用完成笔数会引入幸存者偏差——积压未决的申请被排除，通过率被审批节奏左右；用受理 cohort 才能回答“进来的申请有多少被批准”，与准入漏斗管理一致。30 天观察窗保证绝大多数申请有结论，未决率单独披露，避免静默。

## 3. 排除项（固定）

- 同一客户 + 同一产品 + 金额±10% 在 30 天内重复提交，只算首笔；
- 客户主动撤销、系统作废、测试/内部申请、纯咨询未形成申请；
- 审批退回且未在观察截止前重新提交的，留在分母、不计入分子；
- 观察截止仍未决的，留在分母、不计入分子，并披露未决率。

## 4. 证据与缺口

| 项 | 内容 |
| --- | --- |
| evidence_status | `EVIDENCE_MISSING` |
| missing | `regulatory_source` |
| 依据类型 | 行业通行准入漏斗管理实践（未成文）+ 本轮业务合理性拍板 |
| 关键缺口 | `application_id`、`accept_date`、`decision_status`、`decision_date`、`withdraw_flag`、`void_flag`、`test_flag`、`duplicate_group_id`、`conditional_approval_flag`、`channel`、`product_id`；现有 `agmt:Application` 缺审批结论字段 |

## 5. 平台可出数现状

**不可出数**：口径已完整，但缺申请审批事实表与四元组；不得把“口径可表达”写成“平台可算”。

## 6. 风险与复查触发

- 30 天后仍未决比例 >5% 时标记 `incomplete=true`；
- 重复提交识别规则需业务确认；
- 附条件通过是否计入需固定；
- 受理日期与创建日期需统一；
- 业务书面签字到位后可评估 `publishable` 提升，但不改变分母口径。
