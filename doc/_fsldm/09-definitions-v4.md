# v4 指标定义种子总表（79 条）

> **数据声明：本文件只登记口径定义，不含任何业务数值；任何验证数值均为合成数据、非业务结论。**
> 机器可读副本：`09-definitions-v4.seed.json`（snake_case，79 条）。
> 可执行副本：`09-definitions-v4.seed.sql`（`INSERT ... ON CONFLICT (metric_id) DO UPDATE`，未执行）。
> 口径说明：`00-口径基准-v4.md`。

## 结论

- 79/79 条五件套齐全；ID 集合与 v3 完全一致。
- 标注：原文 39 条 / 行业通行 29 条 / 推测 11 条。
- 补定义后**预计新增可算 0 条**，可算仍为 4 条；其余 75 条如实标“仍不可算”。
- `publishable` 与 v3 一致（true 37 / false 42），无擅自改判；唯一派生变化是 7 条 no-source 的 `inference` 由 false 置 true。



## 分层统计

| 维度 | 值 | 条数 |
| --- | --- | --- |
| provenanceLabel | 原文 | 39 |
| provenanceLabel | 行业通行 | 29 |
| provenanceLabel | 推测 | 11 |
| evidenceBasis | regulatory | 39 |
| evidenceBasis | industry | 33 |
| evidenceBasis | none | 7 |
| publishable | true | 37 |
| publishable | false | 42 |
| inference | true | 40 |
| inference | false | 39 |
| domain | bank / insurance / customer | 36 / 30 / 13 |
| formulaDisabled | true | 2 |

合计 79 条，与 v3 的 79 条一一对应（ID 集合完全相同，不删不合并）。


## 79 行总表

| # | metric_id | display_name | formula（简） | denominator（简） | observation_period | granularity | unit | 标注 | 可发布 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | FIN-BANK-001 | 逾期天数（DPD） | numerator = max(观察日 − 应还款日, 0) | 不适用（非比率；分子为天数） | point-in-time（观察日；窗长 0） | agreement（单笔贷款协议） | 天 | 原文 | true |
| 2 | FIN-BANK-002 | 逾期分档（M0–M6）〔行业〕 | M 档 = floor((max(观察日 − 应还款日, 0) − 1) / 30) + 1；未逾期记 M0 | 不适用（分档规则，非比率） | point-in-time（观察日快照，通常月末） | account（单笔贷款/信用卡账户） | 档（M0–M6） | 行业通行 | false |
| 3 | FIN-BANK-003 | 逾期90天→至少次级 | 若 max(观察日 − 应还款日, 0) > 90 → 分类下限 = 次级（可下调不可上调）；规则型 | 不适用（规则判定） | point-in-time（分类日/观察日） | asset（单笔金融资产；非零售按债务人） | 档（正常/关注/次级/可疑/损失） | 原文 | true |
| 4 | FIN-BANK-004 | 逾期90天→Stage 3〔行业〕 | 若 DPD > 90 → Stage 3；否则按信用风险显著增加判断 Stage 2/1；规则型 | 不适用（规则判定） | point-in-time（报告日） | asset（单笔金融资产） | 阶段（Stage 1/2/3） | 行业通行 | false |
| 5 | FIN-BANK-005 | Stage 2“30 天显著增加”〔行业〕 | Stage 2 = (DPD > 30) ∧ 未发生信用减值；允许以定量/定性证据推翻；规则型 | 不适用（规则判定） | point-in-time（报告日） | asset（单笔金融资产） | 阶段（Stage 1/2/3） | 行业通行 | false |
| 6 | FIN-BANK-006 | 部分还款/最低还款逾期判定〔推测〕 | 若 实还金额 < 当期应还金额（或最低还款额）→ 该期逾期标志=1，起点=应还款日次日；整期逾期口径 | 不适用（判定规则） | point-in-time（应还款日后逐日更新） | account（单笔贷款/信用卡账户） | 标志（0/1）与天 | 推测 | false |
| 7 | FIN-BANK-007 | 五级分类结果 | classification ∈ {正常, 关注, 次级, 可疑, 损失}；不良 = 次级 + 可疑 + 损失；规则型 | 不适用（分类枚举） | point-in-time（分类日/报告期末） | asset（单笔金融资产；非零售按债务人） | 档 | 原文 | true |
| 8 | FIN-BANK-008 | 不良贷款率 | numerator / denominator * 100 | 各项贷款余额（同一报告期末、同一并表范围；按贷款账户汇总，不去重客户）；单位 元 | point-in-time（报告期末） | institution（机构），可下钻 product/customer | % | 原文 | true |
| 9 | FIN-BANK-009 | 交叉违约触发不良 | 若 本行对该债务人不良余额 / 本行对该债务人全部债权余额 > 10% → 全部债权归为不良；规则型 | 本行对同一非零售债务人的全部债权余额（按债务人去重汇总）；单位 元 | point-in-time（分类日） | customer（非零售债务人） | 标志/档 | 原文 | true |
| 10 | FIN-BANK-010 | 重组贷款（现行） | 重组标志 = 财务困难 ∧ 合同调整；观察期 = max(1 年, 连续 2 个还款期)；重组后分类下限：原正常/关注→至少关注，再次重组→至少次级；规则型 | 不适用（判定规则） | period（观察期 ≥ 365 天且 ≥ 连续 2 个还款期，自调整后首次还款日起算） | agreement（单笔协议） | 标志/档 | 原文 | true |
| 11 | FIN-BANK-011 | 重组贷款（旧规） | 重组标志 = 需要重组；分类下限 = 次级；观察期 ≥ 180 天；规则型 | 不适用（判定规则） | period（观察期 ≥ 180 天，自重组日起算；旧规口径，仅历史对照） | agreement（单笔协议） | 标志/档 | 原文 | true |
| 12 | FIN-BANK-012 | 展期/借新还旧归类 | 若 展期获批 ∨ 借新还旧 → 至少关注；满足财务困难则计入重组；规则型 | 不适用（判定规则） | point-in-time（合同调整日） | agreement（单笔协议） | 标志/档 | 原文 | true |
| 13 | FIN-BANK-013 | 正常类贷款迁徙率 | numerator / denominator * 100 | 期初正常类贷款余额 − 期间减少（正常收回 + 不良处置 + 核销）；单位 元 | period（报告期，季度/年度） | institution（机构），可下钻 product | % | 原文 | true |
| 14 | FIN-BANK-014 | 关注类贷款迁徙率 | numerator / denominator * 100 | 期初关注类贷款余额 − 期间减少（正常收回 + 不良处置 + 核销）；单位 元 | period（报告期，季度/年度） | institution（机构），可下钻 product | % | 原文 | true |
| 15 | FIN-BANK-015 | 次级类贷款迁徙率 | numerator / denominator * 100 | 期初次级类贷款余额 − 期间减少（正常收回 + 不良处置 + 核销）；单位 元 | period（报告期，季度/年度） | institution（机构），可下钻 product | % | 原文 | true |
| 16 | FIN-BANK-016 | 可疑类贷款迁徙率 | numerator / denominator * 100 | 期初可疑类贷款余额 − 期间减少（正常收回 + 不良处置 + 核销）；单位 元 | period（报告期，季度/年度） | institution（机构），可下钻 product | % | 原文 | true |
| 17 | FIN-BANK-017 | 逾期迁徙率 30→60〔行业〕 | numerator / denominator * 100 | 期初 DPD 30–59 的账户数（零售）或余额（对公），按账户去重；不剔除期间结清/核销 | period（自然月；月度滚动） | account（账户），可汇总到 product | % | 行业通行 | false |
| 18 | FIN-BANK-018 | 逾期迁徙率 60→90〔行业〕 | numerator / denominator * 100 | 期初 DPD 60–89 的账户数（零售）或余额（对公），按账户去重；不剔除期间结清/核销 | period（自然月；月度滚动） | account（账户），可汇总到 product | % | 行业通行 | false |
| 19 | FIN-BANK-019 | 30→90 累计迁徙率〔行业〕 | numerator / denominator * 100 ≈ r(30→60) × r(60→90)（同一批账户、同一窗口、无新增退出时严格成立） | 期初 DPD 30–59 的账户数（同批账户，按账户去重）；单位 户 | period（连续两个月） | account（账户），可汇总到 product | % | 行业通行 | false |
| 20 | FIN-BANK-020 | 迁徙率（户数口径变体）〔推测〕 | numerator / denominator * 100 | 期初该分类户数（按客户号去重，不按账户去重）；单位 户 | period（报告期，季度） | customer/account（户数口径） | % | 推测 | false |
| 21 | FIN-BANK-021 | 迁徙率（期末余额口径变体）〔推测〕 | numerator / denominator * 100 | 期末该分类贷款余额（同一报告期末）；单位 元 | period（报告期，季度） | institution/product | % | 推测 | false |
| 22 | FIN-BANK-022 | 拨备覆盖率 | numerator / denominator * 100 | 不良贷款余额（次级 + 可疑 + 损失，同一报告期末）；单位 元 | point-in-time（报告期末） | institution/product | % | 原文 | true |
| 23 | FIN-BANK-023 | 贷款拨备率 | numerator / denominator * 100 | 各项贷款余额（含贷款、贸易融资、票据融资、融资租赁、买入返售、透支、垫款；不含一般风险准备）；单位 元 | point-in-time（报告期末） | institution/product | % | 原文 | true |
| 24 | FIN-BANK-024 | IFRS 9 三阶段划分 | Stage 1：未显著增加→12 个月 ECL；Stage 2：显著增加且未减值→存续期 ECL；Stage 3：已减值→存续期 ECL；规则型 | 不适用（分类规则） | point-in-time（报告日） | asset（单笔金融资产） | 阶段（Stage 1/2/3） | 原文 | true |
| 25 | FIN-BANK-025 | 单一客户贷款集中度 | numerator / denominator * 100 | 商业银行资本余额（时点；按法人机构一次取值，不随客户去重，不含表外）；单位 元 | point-in-time（报告期末） | customer（单一借款人） | % | 原文 | true |
| 26 | FIN-BANK-026 | 单一非同业客户风险暴露/一级资本净额 | numerator / denominator * 100 | 一级资本净额（时点；法人机构一次取值）；单位 元 | point-in-time（报告期末） | customer（非同业单一客户） | % | 原文 | true |
| 27 | FIN-BANK-027 | 非同业关联客户风险暴露集中度 | numerator / denominator * 100 | 一级资本净额（时点；法人机构一次取值）；单位 元 | point-in-time（报告期末） | group（一组非同业关联客户，按关联组去重） | % | 原文 | true |
| 28 | FIN-BANK-028 | 单一集团客户授信集中度 | numerator / denominator * 100 | 资本净额（时点；法人机构一次取值）；单位 元 | point-in-time（报告期末） | group（最大一家集团客户） | % | 原文 | true |
| 29 | FIN-BANK-029 | 全部关联度 | numerator / denominator * 100 | 资本净额（时点；法人机构一次取值）；单位 元 | point-in-time（报告期末） | institution（全部关联客户汇总） | % | 原文 | true |
| 30 | FIN-BANK-030 | 大额风险暴露认定 | numerator / denominator * 100 | 一级资本净额（时点；法人机构一次取值）；单位 元 | point-in-time（报告期末） | customer/group（单一客户或一组关联客户） | % | 原文 | true |
| 31 | FIN-BANK-031 | 申请通过率〔推测〕 | numerator / denominator * 100 | 受理申请笔数（按申请号去重，剔除重复提交与撤销）；单位 笔 | period（统计期，月度） | institution/channel（机构/渠道），可按 product | % | 推测 | false |
| 32 | FIN-BANK-032 | 额度使用率〔推测〕 | numerator / denominator * 100 | 已批复授信额度（时点有效额度，不含未批复申请）；单位 元 | point-in-time（月末） | agreement/customer | % | 推测 | false |
| 33 | FIN-BANK-033 | 首逾率（FPD）〔行业〕 | numerator / denominator * 100（变体 A：分子=首期应还且首个还款期逾期的账户数；分母=同期首期应还账户数） | 同期首期应还账户数（按账户去重，不含未到首个还款期的账户）；单位 户 | period（按放款月形成 vintage，观察至首个还款期后 30 天） | account（放款批次/vintage） | % | 行业通行 | false |
| 34 | FIN-BANK-034 | 早期预警（EWS）〔推测〕 | 预警标志 = 1 若命中任一规则（DPD > 30、评级下调 ≥ 2 级、额度使用率 > 90%、交叉违约等）；预警等级按命中规则数分档；规则型 | 不适用（规则命中） | point-in-time（监测日，通常日/周） | customer/agreement | 等级（L1–L3） | 推测 | false |
| 35 | FIN-BANK-035 | 催收回收率〔推测〕 | numerator / denominator * 100 | 观察期初进入催收的逾期本金余额（按账户去重，不含已核销转出）；单位 元 | period（观察期，通常 3/6/12 个月） | institution/product | % | 推测 | false |
| 36 | FIN-BANK-036 | 不良处置率/处置回收率〔推测〕 | 处置率 = 期内处置完成不良金额 / 期初不良余额 * 100；回收率 = 期内处置回收金额 / 期内处置标的金额 * 100 | 处置率分母=期初不良资产余额（次级+可疑+损失，按资产去重）；回收率分母=期内处置标的金额；单位 元 | period（报告期，季度/年度） | institution | % | 推测 | false |
| 37 | FIN-INS-001 | 原保险保费收入〔行业〕 | numerator = Σ统计期内按保险合同确认的保费（新单+续期，趸交全额计入承保时点，批退/批减冲减） | 不适用（可加总指标，用 sum 不用比率） | period（统计期，月/季/年） | product（险种），可按 channel/institution | 元 | 行业通行 | false |
| 38 | FIN-INS-002 | 签单保费 | numerator = Σ统计期内销售保单保费总额（含已起保与未起保；批增/批减调整；退保不冲减） | 不适用（可加总指标） | period（统计期，按销售/承保时点归集） | product（险种）/ channel（渠道） | 元 | 原文 | true |
| 39 | FIN-INS-003 | 实收保费〔行业〕 | numerator = Σ本期保费收款 − Σ本期批退/退费 | 不适用（可加总指标） | period（统计期，按收款时点） | product/channel/institution | 元 | 行业通行 | false |
| 40 | FIN-INS-004 | 续期保费（签单口径）〔行业〕 | numerator = Σ续期保单在统计期内的应收（签单）保费 | 不适用（可加总指标） | period（统计期，按保单周年日归集，报表按自然期） | product/channel | 元 | 行业通行 | false |
| 41 | FIN-INS-005 | 趸交/期交与首年保费〔行业〕 | 首年保费 = Σ新单首年期交保费 + Σ趸交保费；趸交全额计入首年，期交后续年度计入续期 | 不适用（可加总指标） | period（保单年度第 1 年） | product（险种）/ channel | 元 | 行业通行 | false |
| 42 | FIN-INS-006 | 保费达成率〔行业〕 | numerator / denominator * 100 | 计划保费（同期、同口径、锁定计划版本）；单位 元 | period（统计期/考核期，月/季/年） | institution/channel | % | 行业通行 | false |
| 43 | FIN-INS-007 | 简单赔付率〔行业〕 | numerator / denominator * 100 | 保费收入（同口径、同期；固定用原保险保费收入，不用已赚保费） | period（报告期） | product（险种） | % | 行业通行 | false |
| 44 | FIN-INS-008 | 综合赔付率（财产险·规则18） | numerator / denominator * 100 | 自留保费 − 未到期责任准备金变动额（同期）；单位 元 | period（报告期，季度/年度） | product（财产险）/ institution | % | 原文 | true |
| 45 | FIN-INS-009 | 综合赔付率（短期健康险） | numerator / denominator * 100 | 再保后已赚保费 = 已赚保费 − 分出保费分摊 + 摊回保险责任准备金变动额（同期）；单位 元 | period（报告期，季度/年度） | product（短期健康险） | % | 原文 | true |
| 46 | FIN-INS-010 | 综合赔付率（财政部）〔行业〕 | numerator / denominator * 100 | 已赚保费 = 保险业务收入 − 分出保费 − 提取未到期责任准备金（年度）；单位 元 | period（年度） | institution（保险公司） | % | 行业通行 | false |
| 47 | FIN-INS-011 | 综合成本率（财产险当期） | numerator / denominator * 100 | 自留保费 − 未到期责任准备金变动额（同期）；单位 元 | period（报告期，季度/年度） | product（财产险） | % | 原文 | true |
| 48 | FIN-INS-012 | 两年综合成本率（2003） | 两年综合成本率 = 两年费用率 + 两年赔付率（两项均为两年合计口径，*100） | 两年合计自留保费（扣未到期责任准备金提转差）；单位 元 | period（两年滚动，≥730 天） | institution（财险公司） | % | 原文 | true |
| 49 | FIN-INS-013 | 两年赔付率（2003） | numerator / denominator * 100 | 两年自留保费合计 − 未到期责任准备金提转差 − 长期财产险责任准备金提转差；单位 元 | period（两年滚动，≥730 天） | institution（财险公司） | % | 原文 | true |
| 50 | FIN-INS-014 | 未决赔款准备金 | numerator = 已发生已报案未决赔款准备金 + IBNR + 理赔费用准备金 | 不适用（可加总指标） | point-in-time（评估日/资产负债表日） | product（险种）/ claim | 元 | 原文 | true |
| 51 | FIN-INS-015 | 案均已决金额 | numerator / denominator（不做 *100，结果为元/件） | 正常结案数量（统计期内已决赔案扣除拒赔、零结案、注销后的件数，按赔案号去重）；单位 件 | period（统计期，按结案时点） | product（交强/商业） | 元/件 | 原文 | true |
| 52 | FIN-INS-016 | 案均未决金额 | numerator / denominator（不做 *100，结果为元/件） | 未决赔案件数（评估时点未结案，按赔案号去重）；单位 件 | point-in-time（评估日） | product（交强/商业） | 元/件 | 原文 | true |
| 53 | FIN-INS-017 | 报案率〔行业〕 | numerator / denominator * 100 | 有效保单件数（同期时点或期间平均，按保单号去重，剔除注销/退保）；单位 件 | period（统计期，月度/年度） | product（险种）/ institution | % | 行业通行 | false |
| 54 | FIN-INS-018 | 报案立案率 | numerator / denominator * 100 | 有效报案数量（总报案数剔除注销报案，按报案号去重）；单位 件 | period（统计期） | product（交强/商业） | % | 原文 | true |
| 55 | FIN-INS-019 | 综合退保率（现行） | numerator / denominator * 100 | 长期险责任准备金期初 + 保户储金及投资款期初 + 独立账户负债期初 + 本年度签单保费；单位 元 | period（季度/年度累计，分母含期初余额，≥90 天） | company（公司）→ product（险种）/ channel | % | 原文 | true |
| 56 | FIN-INS-020 | 退保率（2003 公式） | numerator / denominator * 100 | 上年末长期险责任准备金 + 本年长期险保费收入；单位 元 | period（年度） | institution（寿险）/ product | % | 原文 | true |
| 57 | FIN-INS-021 | 13 个月继续率（有效保单件数） | numerator / denominator * 100 | 上年可比季度末长期寿险有效保单件数（按保单号去重）；单位 件 | period（季度末对比上年可比季度末，≥365 天） | product（长期寿险） | % | 原文 | true |
| 58 | FIN-INS-022 | 13 个月保费继续率（协会·存疑）〔推测〕 | numerator / denominator * 100（分子=该批期交新单在第 13 个月缴费期实收规模保费；分母=该批新单首个保单年度实收规模保费） | 该批期交新单首个保单年度实收规模保费（剔除趸交、犹豫期撤单、理赔终止、免缴、注销、迁出、中止、转换终止；按保单号去重）；单位 元 | period（12 个月滚动，保单年度第 13 个月观察） | product（长期寿险期交新单） | % | 推测 | false |
| 59 | FIN-INS-023 | 25 个月继续率（协会·存疑）〔推测〕 | numerator / denominator * 100（分子=该批期交新单在第 25 个月缴费期实收规模保费；分母=该批新单首个保单年度实收规模保费） | 该批期交新单首个保单年度实收规模保费（剔除项同 FIN-INS-022，按保单号去重）；单位 元 | period（24 个月滚动，保单年度第 25 个月观察） | product（长期寿险期交新单） | % | 推测 | false |
| 60 | FIN-INS-024 | 续保率（车险）〔行业〕 | numerator / denominator * 100 | 到期应续保车辆数（按车辆/VIN 去重，保单止期落在统计期内，含脱保车辆）；单位 辆 | period（按保单年度/月度到期队列） | product（车险）/ channel | % | 行业通行 | false |
| 61 | FIN-INS-025 | 保单件均（个人营销渠道） | numerator / denominator（不做 *100，结果为元/件） | 新单件数（不含续期件，按保单号去重）；单位 件 | period（季度） | channel（个人营销渠道） | 元/件 | 原文 | true |
| 62 | FIN-INS-026 | 渠道费用率〔行业〕 | numerator / denominator * 100 | 该渠道签单保费（同期，且与费用口径渠道归属一致）；单位 元 | period（报告期） | channel（渠道） | % | 行业通行 | false |
| 63 | FIN-INS-027 | 综合费用率 | numerator / denominator * 100 | 自留保费 − 未到期责任准备金变动额（同期）；单位 元 | period（报告期，季度/年度） | product（财产险） | % | 原文 | true |
| 64 | FIN-INS-028 | 手续费及佣金占比 | numerator / denominator * 100 | 保费收入（同期、同口径）；单位 元 | period（报告期，季度/年度） | product/channel | % | 原文 | true |
| 65 | FIN-INS-029 | 综合偿付能力充足率 | numerator / denominator * 100 | 最低资本 = 可资本化风险最低资本 + 控制风险最低资本 + 附加资本（时点）；单位 元 | point-in-time（报告期末，季度/年度） | institution（法人公司） | % | 原文 | false |
| 66 | FIN-INS-030 | 核心偿付能力充足率 | numerator / denominator * 100 | 最低资本 = 可资本化风险最低资本 + 控制风险最低资本 + 附加资本（时点）；单位 元 | point-in-time（报告期末，季度/年度） | institution（法人公司） | % | 原文 | false |
| 67 | CUST-001 | RFM-R（最近一次行为）〔行业〕 | numerator = max(基准日 − 最近一次有效行为日, 0)（取最近一次，不求和） | 不适用（非比率） | point-in-time（月末基准日） | customer（按客户号去重，多渠道合并取最近） | 天 | 行业通行 | false |
| 68 | CUST-002 | RFM-F（频次）〔行业〕 | numerator = Σ窗口内有效交易笔数（按流水号去重，取消/退款剔除；同日多笔是否合并须固定） | 不适用（可加总指标） | period（滚动 12 个月，≥365 天） | customer（按客户号去重） | 次 | 行业通行 | false |
| 69 | CUST-003 | RFM-M（金额）〔行业〕 | numerator = Σ窗口内有效交易金额（与 F 同窗口、同口径） | 不适用（可加总指标） | period（滚动 12 个月，≥365 天） | customer（按客户号去重） | 元 | 行业通行 | false |
| 70 | CUST-004 | RFM 分档（五分位）〔行业〕 | score_d = NTILE(5) over 客户群体（R 降序、F 升序、M 升序）；rfm_code = concat(R,F,M)，每位 1–5 | 分档客户群体（同客群、同窗口的客户数，按客户号去重，NULL 客户不参与切分） | point-in-time（分档基准日） | segment（客户群）→ customer | 档/码（1–5） | 行业通行 | false |
| 71 | CUST-005 | RFM-R（无交易代理口径）〔推测〕 | numerator = max(基准日 − 代理事件日, 0)；无任何代理事件则 R=NULL（不置 0，不参与分档） | 不适用（非比率） | point-in-time（月末基准日） | customer（无交易客户单独标记） | 天 | 推测 | false |
| 72 | CUST-006 | 客户留存率（cohort）〔行业〕 | numerator / denominator * 100 | cohort 初始客户数（起始月满足激活/首单条件，按客户号去重）；单位 户 | period（cohort 起点 + N 月，按月） | cohort × customer | % | 行业通行 | false |
| 73 | CUST-007 | 客户流失率〔行业〕 | numerator / denominator * 100 | 期初客户数（同 cohort、同活跃定义，按客户号去重）；单位 户 | period（观察窗口，月/季/年） | cohort × customer | % | 行业通行 | false |
| 74 | CUST-008 | 月度滚动留存率〔行业〕 | numerator / denominator * 100 | 上月活跃客户数（按客户号去重，月末活跃口径）；单位 户 | period（月，≥30 天） | customer | % | 行业通行 | false |
| 75 | CUST-009 | 产品持有数〔行业〕 | numerator = count(distinct 产品类别) where 产品状态有效 at 观察时点（可按细类计数变体） | 不适用（计数指标） | point-in-time（月末/季末） | customer | 个 | 行业通行 | false |
| 76 | CUST-010 | 人均产品数〔行业〕 | numerator / denominator（不做 *100，结果为个/户） | 客户数（同一客群、同一观察时点，按客户号去重，剔除已销户）；单位 户 | point-in-time（月末/季末） | segment（客群）/ institution | 个/户 | 行业通行 | false |
| 77 | CUST-011 | 钱包份额（SOW）〔行业〕 | numerator / denominator * 100 | 客户在该品类的总消费/总资产（外部数据或模型估算，同期、同币种）；单位 元 | period（年度/滚动 12 个月，与时点变体分开） | customer × category | % | 行业通行 | false |
| 78 | CUST-012 | AUM（时点）〔行业〕 | numerator = Σ客户可计入资产市值 at 观察时点（按账户去重，避免双计） | 不适用（可加总指标） | point-in-time（月末） | customer × product type | 元 | 行业通行 | false |
| 79 | CUST-013 | AUM（日均）〔行业〕 | AUM_日均 = Σ期内每日 AUM / 期内天数 | 期内天数（自然日，同一期间）；单位 天 | period（月/季/年日均，≥30 天） | customer × product type | 元 | 行业通行 | false |


## 可算性预测

| 分层 | 条数 | 说明 |
| --- | --- | --- |
| 已可算可发布 | 4 | FIN-BANK-001、FIN-BANK-025、FIN-BANK-030、FIN-INS-021 |
| 规则型，仍不可算为数值指标 | 11 | FIN-BANK-003、FIN-BANK-004、FIN-BANK-005、FIN-BANK-007、FIN-BANK-009、FIN-BANK-010、FIN-BANK-011、FIN-BANK-012、FIN-BANK-024、FIN-BANK-034、CUST-004 |
| 口径齐但缺事实表/字段，仍不可算 | 61 | 其余 61 条；补实体后进入建模，publishable=false 者仍不得对外出数 |
| 缺外部数据，仍不可算 | 3 | FIN-INS-029、FIN-INS-030、CUST-011 |


## 抽查 5 条手算（算例数字仅用于验证公式可走通，非业务结论）

| 指标 | 算例输入 | 计算 | 结果 |
| --- | --- | --- | --- |
| FIN-BANK-008 不良贷款率 | 不良余额 12,000 元；各项贷款余额 400,000 元 | 12,000 / 400,000 * 100 | 3.00% |
| FIN-BANK-022 拨备覆盖率 | 贷款损失准备 18,000 元；不良贷款余额 12,000 元 | 18,000 / 12,000 * 100 | 150.00% |
| FIN-BANK-025 单一客户贷款集中度 | 单一借款人贷款 1,200 元；资本余额 10,000 元 | 1,200 / 10,000 * 100 | 12.00% |
| FIN-INS-021 13 个月继续率 | 分子 2,000 件；分母 5,000 件（上年可比季末有效保单） | 2,000 / 5,000 * 100 | 40.00% |
| FIN-INS-015 案均已决金额 | 已决赔款 600,000 元；正常结案件数 300 件 | 600,000 / 300 | 2,000 元/件 |

说明：FIN-INS-021 的算例按件数口径，与可计算性矩阵中的 `(2+2)/(5+3)*100` 属不同样本，仅验证公式结构；矩阵数字未被改动。

## 自检

- 条数：79（v3 为 79）；ID 集合与 v3 完全一致，无新增、无删除、无合并。
- 五件套：definition / formula / denominator / observation_period / granularity + unit 均非空，缺项 0。
- JSON：`09-definitions-v4.seed.json` 可被 `python -m json.tool` 解析；顶层为 79 元素数组（无包装层）。
- 约束：推测→`inference=true` 且 `evidence_basis ∈ {none, industry}`，失败 0；原文→`regulatory`，失败 0；行业通行→`industry`，失败 0。
- 后缀：`推测` 加 `〔推测〕`，`行业通行` 加 `〔行业〕`，`原文` 不加；固定三种，无自创。
- publishable 与 v3 判定一致：`true` 37 条 / `false` 42 条，无改判。
- SQL：`09-definitions-v4.seed.sql` 为单条 `INSERT ... ON CONFLICT (metric_id) DO UPDATE`，未执行；7 个新增列已用注释标注“待迁移补列”。

## Open 事项（未决，已标 open）

1. **open｜FIN-INS-022 / FIN-INS-023 协会原文表述与 13/25 个月口径不匹配**。v4 按“第 13/25 个月缴费期实收规模保费”补写，但协会原文疑为“首个保单年度宽限期内实收”，两者不等价。缺：协会文件清晰版原文或条款截图。当前 `formula_disabled=true`，不可用于出数。
2. **open｜FIN-BANK-034 早期预警（EWS）无任何权威公式**。v4 给出的规则集（DPD>30、评级下调≥2级、额度使用率>90%、交叉违约）为推测，缺：业务确认的预警规则清单与阈值。确认前不得建事实表。
3. **open｜no-source 指标的分母缺少业务确认**。FIN-BANK-031（受理笔数）、FIN-BANK-032（已批复额度）、FIN-BANK-035（应催金额）、FIN-BANK-036（处置标的）的分母均为推测口径，缺：业务口径签字与系统字段映射。


## 待迁移补列清单

| 种子字段 | 目标列 | 现状 |
| --- | --- | --- |
| name_zh（规范名，无后缀） | name_zh | 既有列，保持 v3 名称不改 |
| display_name（规范名+固定后缀） | display_name | 表结构无此列，待迁移补列 |
| definition | definition | 表结构无此列，待迁移补列 |
| formula | formula_text | 表结构无此列（既有 `formula_expr` 保留不动），待迁移补列 |
| denominator | denominator_text | 表结构无此列，待迁移补列 |
| observation_period | observation_period | 表结构无此列，待迁移补列 |
| granularity | granularity | 表结构无此列（既有 `grain` 保留不动），待迁移补列 |
| provenance_label | provenance_label | 表结构无此列，待迁移补列 |
| unit / evidence_basis / publishable / inference | 同名列 | 既有列，直接映射 |
