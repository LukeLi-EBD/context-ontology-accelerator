# FIN-BANK-032 · 额度使用率〔推测〕

> 来源档：**inferred**（provenance_label=推测｜evidence_basis=industry）
> publishable：**false**｜inference：**true**｜formula_disabled：false｜domain：bank
> 数据声明：本卡只登记口径，不含任何业务数值；平台出数结论一律为**合成数据、非业务结论**。
> 来源：`_fsldm/10-definitions-v5.seed.json`（v5，2026-11-06）；判定见 `_fsldm/10-口径判定-三项open.md` §4.2；基准见 `_fsldm/00-口径基准-v5.md` §3.5。

## 1. 定义

同一时点已用授信额度（提款未还本金）占已批复且状态有效的授信额度总额的比例，反映额度动用程度。

## 2. 公式与分母（唯一分母）

| 项 | 内容 |
| --- | --- |
| formula | `numerator / denominator * 100` |
| numerator | 已用额度 = 提款未还本金余额；不含已结清、已核销、已转出；不含利息、费用、罚息；按额度协议号去重；单位 元 |
| denominator | 同一时点已批复且状态有效的授信额度；按额度协议号去重；循环额度按全额计入；剔除未批复申请、已拒绝、已撤销、已过期未续、已冻结、已注销、内部往来、测试额度；多币种按同一汇率折算；单位 元 |
| observationPeriod | point-in-time（月末/季末；分子分母同一时点） |
| granularity | agreement/customer，可按 product/institution |
| unit | % |

**为什么分母不是“可用额度”**：使用率衡量“已提用/已批复”，不是“已用/可用”。用可用额度会把未提用部分重复计入，且随额度调增而漂移；只取有效批复额度，剔除已过期/冻结/注销，避免把“僵尸额度”当分母；分子只用本金，避免利息/费用把使用率推高。

## 3. 排除项（固定）

- 未批复申请、已拒绝、已撤销、已过期未续、已冻结、已注销的额度；
- 内部往来、测试额度；
- 已结清、已核销、已转出的提款；
- 利息、费用、罚息不计入已用额度；
- 多币种按同一时点汇率折算，不得混币种直接相加。

## 4. 证据与缺口

| 项 | 内容 |
| --- | --- |
| evidence_status | `EVIDENCE_MISSING` |
| missing | `regulatory_source` |
| 依据类型 | 行业通行额度管理实践（未成文）+ 本轮业务合理性拍板 |
| 关键缺口 | `credit_limit_agreement`（`approved_limit`、`status`、`effective_from/to`、`limit_type`、`currency`、`freeze_flag`、`internal_flag`）、`drawn_principal`、`fx_rate`；当前无额度协议实体 |

## 5. 平台可出数现状

**不可出数**：口径已完整，但缺额度协议事实表与四元组；不得标成“可算”。

## 6. 风险与复查触发

- 循环额度与定期额度混合时需分产品披露；
- 额度期内调增/调减需取同一时点快照；
- 多币种汇率需锁定；
- 已核销但仍有提款的账户处理需业务确认；
- 业务书面签字到位后可评估 `publishable` 提升。
