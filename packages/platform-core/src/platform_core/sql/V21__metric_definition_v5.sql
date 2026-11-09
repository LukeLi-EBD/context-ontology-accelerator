-- V21: metric definition v5. Lands the 13-row verdict in
-- _fsldm/10-口径判定-三项open.md (basis _fsldm/00-口径基准-v5.md):
--   * 3 family index rows stay formula_disabled=true (output_mode=index)
--   * 6 executable variants (-v1/-v2) become formula_disabled=false
--   * FIN-BANK-034 becomes a rule_set metric (10 rules in rule_set_json)
--   * 4 new v5 columns: effective_date / variant_of / output_mode / rule_set_json
-- The 7 text columns were declared as "待迁移补列" by the v4 seed header but were
-- never migrated; they are added here so the verdict text is stored instead of
-- being dropped. v4 mapping applies: formula -> formula_text, denominator -> denominator_text.
-- Re-entrant: ADD COLUMN IF NOT EXISTS + INSERT ... ON CONFLICT (metric_id) DO UPDATE.

ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS display_name text;
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS definition text;
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS formula_text text;
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS denominator_text text;
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS observation_period text;
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS granularity text;
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS provenance_label text;
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS effective_date date;
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS variant_of text;
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS output_mode text;
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS rule_set_json jsonb;
-- 10-definitions-v5.seed.sql
-- 仅包含相对 v4 的变更条目（13 行：10 个可执行定义 + 3 个族索引）
-- 形式：INSERT ... ON CONFLICT (metric_id) DO UPDATE
-- 说明：本文件不执行 DDL。执行前需先为 platform.metric_definition 增加以下列：
--   effective_date  date
--   variant_of      text
--   output_mode     text   -- value / index / rule_set
--   rule_set_json   jsonb  -- 仅规则型指标使用
-- 字段命名与 v4 种子保持一致；新增列已逐条注明。未执行、未写库。

-- 1) FIN-INS-022 族索引（原 formulaDisabled=true 保留，防误用）
INSERT INTO platform.metric_definition (
  metric_id, name_zh, display_name, definition, formula_text, denominator_text,
  observation_period, granularity, unit, evidence_basis, provenance_label,
  inference, publishable, domain, formula_disabled, evidence_status, missing,
  note, effective_date, variant_of, output_mode, rule_set_json
) VALUES (
  'FIN-INS-022',
  '13 个月保费继续率',
  '13 个月保费继续率（口径族·索引）〔推测〕',
  '口径族索引：13 个月保费继续率按宽限期口径（FIN-INS-022-v1）与自然月口径（FIN-INS-022-v2）并列；本行不单独出数。',
  '不适用（族索引；见 FIN-INS-022-v1 / FIN-INS-022-v2）',
  '不适用（族索引；变体分母均为该批期交新单首个保单年度实收规模保费）',
  '不适用（族索引；变体观察期见 v1/v2）',
  '不适用（族索引）',
  '%',
  'industry',
  '推测',
  TRUE,
  FALSE,
  'insurance',
  TRUE,
  'EVIDENCE_MISSING',
  'regulatory_source',
  'v5 拆为 FIN-INS-022-v1（宽限期口径）与 -v2（自然月口径）；本行保留为族索引，formula_disabled=true 防误用；协会原文清晰版到位后按复查触发重审；内部使用变体，不对外发布',
  '2026-11-06',
  NULL,
  'index',
  NULL
)
ON CONFLICT (metric_id) DO UPDATE SET
  name_zh = EXCLUDED.name_zh,
  display_name = EXCLUDED.display_name,
  definition = EXCLUDED.definition,
  formula_text = EXCLUDED.formula_text,
  denominator_text = EXCLUDED.denominator_text,
  observation_period = EXCLUDED.observation_period,
  granularity = EXCLUDED.granularity,
  unit = EXCLUDED.unit,
  evidence_basis = EXCLUDED.evidence_basis,
  provenance_label = EXCLUDED.provenance_label,
  inference = EXCLUDED.inference,
  publishable = EXCLUDED.publishable,
  domain = EXCLUDED.domain,
  formula_disabled = EXCLUDED.formula_disabled,
  evidence_status = EXCLUDED.evidence_status,
  missing = EXCLUDED.missing,
  note = EXCLUDED.note,
  effective_date = EXCLUDED.effective_date,
  variant_of = EXCLUDED.variant_of,
  output_mode = EXCLUDED.output_mode,
  rule_set_json = EXCLUDED.rule_set_json,
  updated_at = now();

-- 2) FIN-INS-022-v1 13 个月 · 宽限期口径
INSERT INTO platform.metric_definition (
  metric_id, name_zh, display_name, definition, formula_text, denominator_text,
  observation_period, granularity, unit, evidence_basis, provenance_label,
  inference, publishable, domain, formula_disabled, evidence_status, missing,
  note, effective_date, variant_of, output_mode, rule_set_json
) VALUES (
  'FIN-INS-022-v1',
  '13 个月保费继续率（宽限期口径）',
  '13 个月保费继续率（宽限期口径）〔推测〕',
  '评价期前溯 12 个月承保的个人期交新单，在第 1 个保单年度结束后的缴费宽限期内实收的第 2 个保单年度首期规模保费，占该批新单首个保单年度实收规模保费的比例。',
  'numerator / denominator * 100（分子=该批期交新单在第 2 个保单年度首期应缴、且在第 1 个保单年度结束后宽限期截止日前实收的规模保费；分母=该批新单首个保单年度实收规模保费）',
  '该批期交新单首个保单年度实收规模保费；按保单号去重；剔除趸交、犹豫期撤单、理赔终止、免缴、注销、迁出、效力中止、转换终止；单位 元',
  'period（评价期前溯 12 个月承保 cohort；逐单观察至第 1 个保单年度结束后宽限期截止日；宽限期默认 60 天，可配置）',
  'product（长期寿险期交新单），可下钻 channel/institution',
  '%',
  'industry',
  '推测',
  TRUE,
  FALSE,
  'insurance',
  FALSE,
  'EVIDENCE_MISSING',
  'regulatory_source',
  '协会原文“首个保单年度宽限期”在 13 个月锚点上可自洽；按实收现金口径；与 v2 只差分子到账窗口，分母相同；内部出数须标 source=INDUSTRY + inference=true；不对外发布',
  '2026-11-06',
  'FIN-INS-022',
  'value',
  NULL
)
ON CONFLICT (metric_id) DO UPDATE SET
  name_zh = EXCLUDED.name_zh,
  display_name = EXCLUDED.display_name,
  definition = EXCLUDED.definition,
  formula_text = EXCLUDED.formula_text,
  denominator_text = EXCLUDED.denominator_text,
  observation_period = EXCLUDED.observation_period,
  granularity = EXCLUDED.granularity,
  unit = EXCLUDED.unit,
  evidence_basis = EXCLUDED.evidence_basis,
  provenance_label = EXCLUDED.provenance_label,
  inference = EXCLUDED.inference,
  publishable = EXCLUDED.publishable,
  domain = EXCLUDED.domain,
  formula_disabled = EXCLUDED.formula_disabled,
  evidence_status = EXCLUDED.evidence_status,
  missing = EXCLUDED.missing,
  note = EXCLUDED.note,
  effective_date = EXCLUDED.effective_date,
  variant_of = EXCLUDED.variant_of,
  output_mode = EXCLUDED.output_mode,
  rule_set_json = EXCLUDED.rule_set_json,
  updated_at = now();

-- 3) FIN-INS-022-v2 13 个月 · 自然月口径
INSERT INTO platform.metric_definition (
  metric_id, name_zh, display_name, definition, formula_text, denominator_text,
  observation_period, granularity, unit, evidence_basis, provenance_label,
  inference, publishable, domain, formula_disabled, evidence_status, missing,
  note, effective_date, variant_of, output_mode, rule_set_json
) VALUES (
  'FIN-INS-022-v2',
  '13 个月保费继续率（自然月口径）',
  '13 个月保费继续率（自然月口径）〔推测〕',
  '评价期前溯 12 个月承保的个人期交新单，在保单进入第 13 个保单月（第 2 个保单年度首月，按保单周年日对齐）所在自然月内实收的第 2 个保单年度首期规模保费，占该批新单首个保单年度实收规模保费的比例。',
  'numerator / denominator * 100（分子=该批期交新单在第 13 个保单月所在自然月内实收的第 2 个保单年度首期规模保费；分母=该批新单首个保单年度实收规模保费）',
  '该批期交新单首个保单年度实收规模保费；按保单号去重；剔除趸交、犹豫期撤单、理赔终止、免缴、注销、迁出、效力中止、转换终止；单位 元',
  'period（评价期前溯 12 个月承保 cohort；锚点=每张保单周年日 + 12 个月的自然月；观察至该自然月最后一日）',
  'product（长期寿险期交新单），可下钻 channel/institution',
  '%',
  'industry',
  '推测',
  TRUE,
  FALSE,
  'insurance',
  FALSE,
  'EVIDENCE_MISSING',
  'regulatory_source',
  '公司月度管理口径；自然月窗便于月结与月度趋势；不含宽限期跨月到账、不含复效补缴；与 v1 不可混算；内部出数须标 source=INDUSTRY + inference=true；不对外发布',
  '2026-11-06',
  'FIN-INS-022',
  'value',
  NULL
)
ON CONFLICT (metric_id) DO UPDATE SET
  name_zh = EXCLUDED.name_zh,
  display_name = EXCLUDED.display_name,
  definition = EXCLUDED.definition,
  formula_text = EXCLUDED.formula_text,
  denominator_text = EXCLUDED.denominator_text,
  observation_period = EXCLUDED.observation_period,
  granularity = EXCLUDED.granularity,
  unit = EXCLUDED.unit,
  evidence_basis = EXCLUDED.evidence_basis,
  provenance_label = EXCLUDED.provenance_label,
  inference = EXCLUDED.inference,
  publishable = EXCLUDED.publishable,
  domain = EXCLUDED.domain,
  formula_disabled = EXCLUDED.formula_disabled,
  evidence_status = EXCLUDED.evidence_status,
  missing = EXCLUDED.missing,
  note = EXCLUDED.note,
  effective_date = EXCLUDED.effective_date,
  variant_of = EXCLUDED.variant_of,
  output_mode = EXCLUDED.output_mode,
  rule_set_json = EXCLUDED.rule_set_json,
  updated_at = now();

-- 4) FIN-INS-023 族索引（原 formulaDisabled=true 保留，防误用）
INSERT INTO platform.metric_definition (
  metric_id, name_zh, display_name, definition, formula_text, denominator_text,
  observation_period, granularity, unit, evidence_basis, provenance_label,
  inference, publishable, domain, formula_disabled, evidence_status, missing,
  note, effective_date, variant_of, output_mode, rule_set_json
) VALUES (
  'FIN-INS-023',
  '25 个月继续率',
  '25 个月继续率（口径族·索引）〔推测〕',
  '口径族索引：25 个月继续率按宽限期口径（FIN-INS-023-v1）与自然月口径（FIN-INS-023-v2）并列；本行不单独出数。',
  '不适用（族索引；见 FIN-INS-023-v1 / FIN-INS-023-v2）',
  '不适用（族索引；变体分母均为该批期交新单首个保单年度实收规模保费）',
  '不适用（族索引；变体观察期见 v1/v2）',
  '不适用（族索引）',
  '%',
  'industry',
  '推测',
  TRUE,
  FALSE,
  'insurance',
  TRUE,
  'EVIDENCE_MISSING',
  'regulatory_source',
  'v5 拆为 FIN-INS-023-v1（宽限期口径，原文修正）与 -v2（自然月口径）；本行保留为族索引，formula_disabled=true 防误用；25 个月原文复制错误已按第 2 个保单年度宽限期修正并标 inferred；内部使用变体，不对外发布',
  '2026-11-06',
  NULL,
  'index',
  NULL
)
ON CONFLICT (metric_id) DO UPDATE SET
  name_zh = EXCLUDED.name_zh,
  display_name = EXCLUDED.display_name,
  definition = EXCLUDED.definition,
  formula_text = EXCLUDED.formula_text,
  denominator_text = EXCLUDED.denominator_text,
  observation_period = EXCLUDED.observation_period,
  granularity = EXCLUDED.granularity,
  unit = EXCLUDED.unit,
  evidence_basis = EXCLUDED.evidence_basis,
  provenance_label = EXCLUDED.provenance_label,
  inference = EXCLUDED.inference,
  publishable = EXCLUDED.publishable,
  domain = EXCLUDED.domain,
  formula_disabled = EXCLUDED.formula_disabled,
  evidence_status = EXCLUDED.evidence_status,
  missing = EXCLUDED.missing,
  note = EXCLUDED.note,
  effective_date = EXCLUDED.effective_date,
  variant_of = EXCLUDED.variant_of,
  output_mode = EXCLUDED.output_mode,
  rule_set_json = EXCLUDED.rule_set_json,
  updated_at = now();

-- 5) FIN-INS-023-v1 25 个月 · 宽限期口径（原文修正）
INSERT INTO platform.metric_definition (
  metric_id, name_zh, display_name, definition, formula_text, denominator_text,
  observation_period, granularity, unit, evidence_basis, provenance_label,
  inference, publishable, domain, formula_disabled, evidence_status, missing,
  note, effective_date, variant_of, output_mode, rule_set_json
) VALUES (
  'FIN-INS-023-v1',
  '25 个月保费继续率（宽限期口径）',
  '25 个月保费继续率（宽限期口径）〔推测〕',
  '评价期前溯 24 个月承保的个人期交新单，在第 2 个保单年度结束后的缴费宽限期内实收的第 3 个保单年度首期规模保费，占该批新单首个保单年度实收规模保费的比例。',
  'numerator / denominator * 100（分子=该批期交新单在第 3 个保单年度首期应缴、且在第 2 个保单年度结束后宽限期截止日前实收的规模保费；分母=该批新单首个保单年度实收规模保费）',
  '该批期交新单首个保单年度实收规模保费；按保单号去重；剔除趸交、犹豫期撤单、理赔终止、免缴、注销、迁出、效力中止、转换终止；单位 元',
  'period（评价期前溯 24 个月承保 cohort；逐单观察至第 2 个保单年度结束后宽限期截止日；宽限期默认 60 天，可配置）',
  'product（长期寿险期交新单），可下钻 channel/institution',
  '%',
  'industry',
  '推测',
  TRUE,
  FALSE,
  'insurance',
  FALSE,
  'EVIDENCE_MISSING',
  'regulatory_source',
  '协会 25 个月原文写“首个保单年度宽限期”，与 25 个月锚点矛盾，判定为复制错误；本变体按“第 2 个保单年度结束后宽限期”修正，修正部分为 inferred，不冒充原文；内部出数须标 source=INDUSTRY + inference=true；不对外发布',
  '2026-11-06',
  'FIN-INS-023',
  'value',
  NULL
)
ON CONFLICT (metric_id) DO UPDATE SET
  name_zh = EXCLUDED.name_zh,
  display_name = EXCLUDED.display_name,
  definition = EXCLUDED.definition,
  formula_text = EXCLUDED.formula_text,
  denominator_text = EXCLUDED.denominator_text,
  observation_period = EXCLUDED.observation_period,
  granularity = EXCLUDED.granularity,
  unit = EXCLUDED.unit,
  evidence_basis = EXCLUDED.evidence_basis,
  provenance_label = EXCLUDED.provenance_label,
  inference = EXCLUDED.inference,
  publishable = EXCLUDED.publishable,
  domain = EXCLUDED.domain,
  formula_disabled = EXCLUDED.formula_disabled,
  evidence_status = EXCLUDED.evidence_status,
  missing = EXCLUDED.missing,
  note = EXCLUDED.note,
  effective_date = EXCLUDED.effective_date,
  variant_of = EXCLUDED.variant_of,
  output_mode = EXCLUDED.output_mode,
  rule_set_json = EXCLUDED.rule_set_json,
  updated_at = now();

-- 6) FIN-INS-023-v2 25 个月 · 自然月口径
INSERT INTO platform.metric_definition (
  metric_id, name_zh, display_name, definition, formula_text, denominator_text,
  observation_period, granularity, unit, evidence_basis, provenance_label,
  inference, publishable, domain, formula_disabled, evidence_status, missing,
  note, effective_date, variant_of, output_mode, rule_set_json
) VALUES (
  'FIN-INS-023-v2',
  '25 个月保费继续率（自然月口径）',
  '25 个月保费继续率（自然月口径）〔推测〕',
  '评价期前溯 24 个月承保的个人期交新单，在保单进入第 25 个保单月（第 3 个保单年度首月，按保单周年日对齐）所在自然月内实收的第 3 个保单年度首期规模保费，占该批新单首个保单年度实收规模保费的比例。',
  'numerator / denominator * 100（分子=该批期交新单在第 25 个保单月所在自然月内实收的第 3 个保单年度首期规模保费；分母=该批新单首个保单年度实收规模保费）',
  '该批期交新单首个保单年度实收规模保费；按保单号去重；剔除趸交、犹豫期撤单、理赔终止、免缴、注销、迁出、效力中止、转换终止；单位 元',
  'period（评价期前溯 24 个月承保 cohort；锚点=每张保单周年日 + 24 个月的自然月；观察至该自然月最后一日）',
  'product（长期寿险期交新单），可下钻 channel/institution',
  '%',
  'industry',
  '推测',
  TRUE,
  FALSE,
  'insurance',
  FALSE,
  'EVIDENCE_MISSING',
  'regulatory_source',
  '公司月度管理口径；自然月窗便于月结与月度趋势；不含宽限期跨月到账、不含复效补缴；与 v1 不可混算；内部出数须标 source=INDUSTRY + inference=true；不对外发布',
  '2026-11-06',
  'FIN-INS-023',
  'value',
  NULL
)
ON CONFLICT (metric_id) DO UPDATE SET
  name_zh = EXCLUDED.name_zh,
  display_name = EXCLUDED.display_name,
  definition = EXCLUDED.definition,
  formula_text = EXCLUDED.formula_text,
  denominator_text = EXCLUDED.denominator_text,
  observation_period = EXCLUDED.observation_period,
  granularity = EXCLUDED.granularity,
  unit = EXCLUDED.unit,
  evidence_basis = EXCLUDED.evidence_basis,
  provenance_label = EXCLUDED.provenance_label,
  inference = EXCLUDED.inference,
  publishable = EXCLUDED.publishable,
  domain = EXCLUDED.domain,
  formula_disabled = EXCLUDED.formula_disabled,
  evidence_status = EXCLUDED.evidence_status,
  missing = EXCLUDED.missing,
  note = EXCLUDED.note,
  effective_date = EXCLUDED.effective_date,
  variant_of = EXCLUDED.variant_of,
  output_mode = EXCLUDED.output_mode,
  rule_set_json = EXCLUDED.rule_set_json,
  updated_at = now();

-- 7) FIN-BANK-034 EWS 规则型
INSERT INTO platform.metric_definition (
  metric_id, name_zh, display_name, definition, formula_text, denominator_text,
  observation_period, granularity, unit, evidence_basis, provenance_label,
  inference, publishable, domain, formula_disabled, evidence_status, missing,
  note, effective_date, variant_of, output_mode, rule_set_json
) VALUES (
  'FIN-BANK-034',
  '早期预警（EWS）',
  '早期预警（EWS）〔推测〕',
  '对资产质量恶化信号按可配置规则集进行监测，命中规则的对象进入预警清单，并按规则严重度与命中数量分档 L1–L3。',
  'rule_set：R01–R10；预警等级 = f(命中规则集合)；不输出单一比率',
  '不适用（规则型；无单一分母）',
  'point-in-time（监测日；日/周频，按规则各自观察窗）',
  'customer/agreement，可按 institution/product 汇总',
  '等级（L1–L3）+ 规则命中清单',
  'industry',
  '推测',
  TRUE,
  FALSE,
  'bank',
  FALSE,
  'EVIDENCE_MISSING',
  'regulatory_source',
  '规则型指标；10 条规则阈值可配置（ews.rule.<id>.threshold）；等级聚合见判定书 §3.3；平台 metric_kind 需新增 rule_set 枚举，未实现前 compute 返回 E_METRIC_NOT_DRIVABLE，不返回假成功；内部可用，不对外发布',
  '2026-11-06',
  NULL,
  'rule_set',
  $rulejson$[
    {"id":"R01","signal":"逾期进入关注","trigger_fields":["dpd"],"threshold":">=30 天","window":"日","level":"L1","debounce":"连续 2 个观测日","suppression":"已核销/已结清/已进入不良处置的不重复告警"},
    {"id":"R02","signal":"逾期进入不良","trigger_fields":["dpd"],"threshold":">=90 天","window":"日","level":"L3","debounce":"即时","suppression":"同一对象 30 天内已 L3 的合并；不抑制首次 90+"},
    {"id":"R03","signal":"逾期迁徙恶化","trigger_fields":["dpd_start","dpd_end"],"threshold":"30→60 天（跨 1 档）","window":"30 天","level":"L2","debounce":"事件触发 1 次","suppression":"已获批展期/重组观察期内抑制"},
    {"id":"R04","signal":"五级分类下迁","trigger_fields":["risk_class_prev","risk_class_curr"],"threshold":"下调 >=1 档","window":"90 天","level":"L2","debounce":"事件触发 1 次","suppression":"30 天内回调则撤销本次告警（滞回）"},
    {"id":"R05","signal":"外部评级下调","trigger_fields":["external_rating_prev","external_rating_curr"],"threshold":"下调 >=2 个 notch","window":"180 天","level":"L2","debounce":"事件触发 1 次","suppression":"评级观察名单已告警的 90 天内合并"},
    {"id":"R06","signal":"额度高占用","trigger_fields":["drawn_principal","approved_limit"],"threshold":"使用率 >=90%","window":"连续 30 天","level":"L1","debounce":"连续 30 天","suppression":"额度已冻结/已过期/已注销的不告警"},
    {"id":"R07","signal":"交叉违约","trigger_fields":["other_facility_dpd_90plus","default_flag"],"threshold":"任一其他债项 90+ 或违约","window":"90 天","level":"L3","debounce":"即时","suppression":"同一债务人 30 天内已 L3 的合并"},
    {"id":"R08","signal":"现金流异动","trigger_fields":["monthly_inflow"],"threshold":"较过去 12 个月均值下降 >=50%","window":"连续 2 个月","level":"L2","debounce":"连续 2 个月","suppression":"同比同月也下降 >=50% 的视为季节性，降为 L1 观察"},
    {"id":"R09","signal":"还款行为异动","trigger_fields":["paid_amount","due_amount"],"threshold":"连续 2 期仅最低/部分还款，或还款额下降 >=30%","window":"2 个还款期","level":"L1","debounce":"连续 2 期","suppression":"因利率调整/展期导致应还额变化的，先还原再判断"},
    {"id":"R10","signal":"押品/担保弱化","trigger_fields":["collateral_value","loan_balance","guarantee_status"],"threshold":"押品覆盖率下降 >=20%，或担保撤销","window":"90 天","level":"L2","debounce":"事件触发 1 次","suppression":"已安排重估/已批准替换担保的 30 天内抑制"}
  ]$rulejson$::jsonb
)
ON CONFLICT (metric_id) DO UPDATE SET
  name_zh = EXCLUDED.name_zh,
  display_name = EXCLUDED.display_name,
  definition = EXCLUDED.definition,
  formula_text = EXCLUDED.formula_text,
  denominator_text = EXCLUDED.denominator_text,
  observation_period = EXCLUDED.observation_period,
  granularity = EXCLUDED.granularity,
  unit = EXCLUDED.unit,
  evidence_basis = EXCLUDED.evidence_basis,
  provenance_label = EXCLUDED.provenance_label,
  inference = EXCLUDED.inference,
  publishable = EXCLUDED.publishable,
  domain = EXCLUDED.domain,
  formula_disabled = EXCLUDED.formula_disabled,
  evidence_status = EXCLUDED.evidence_status,
  missing = EXCLUDED.missing,
  note = EXCLUDED.note,
  effective_date = EXCLUDED.effective_date,
  variant_of = EXCLUDED.variant_of,
  output_mode = EXCLUDED.output_mode,
  rule_set_json = EXCLUDED.rule_set_json,
  updated_at = now();

-- 8) FIN-BANK-031 申请通过率（分母唯一化）
INSERT INTO platform.metric_definition (
  metric_id, name_zh, display_name, definition, formula_text, denominator_text,
  observation_period, granularity, unit, evidence_basis, provenance_label,
  inference, publishable, domain, formula_disabled, evidence_status, missing,
  note, effective_date, variant_of, output_mode, rule_set_json
) VALUES (
  'FIN-BANK-031',
  '申请通过率',
  '申请通过率〔推测〕',
  '统计期内首次受理的信贷申请中，在观察截止日（期末 + 30 天）前完成审批且结论为通过的申请笔数，占统计期内首次受理申请笔数的比例。',
  'numerator / denominator * 100',
  '统计期内首次受理的信贷申请笔数；按申请号去重；以受理日期落窗；剔除同一客户+同一产品+金额±10% 在 30 天内的重复提交（只算首笔）、客户撤销、系统作废、测试/内部申请、纯咨询未形成申请；单位 笔',
  'period（月度；cohort=受理日期在统计期；审批观察截止=期末 + 30 天；未决率单独披露）',
  'institution/channel（机构/渠道），可按 product',
  '%',
  'industry',
  '推测',
  TRUE,
  FALSE,
  'bank',
  FALSE,
  'EVIDENCE_MISSING',
  'regulatory_source',
  '分母唯一化为统计期内首次受理申请笔数（intake cohort），不是审批完成笔数；期末+30天观察；未决率>5% 标记 incomplete；行业通行管理实践（未成文）+ 本轮业务合理性拍板；内部可用，不对外发布',
  '2026-11-06',
  NULL,
  'value',
  NULL
)
ON CONFLICT (metric_id) DO UPDATE SET
  name_zh = EXCLUDED.name_zh,
  display_name = EXCLUDED.display_name,
  definition = EXCLUDED.definition,
  formula_text = EXCLUDED.formula_text,
  denominator_text = EXCLUDED.denominator_text,
  observation_period = EXCLUDED.observation_period,
  granularity = EXCLUDED.granularity,
  unit = EXCLUDED.unit,
  evidence_basis = EXCLUDED.evidence_basis,
  provenance_label = EXCLUDED.provenance_label,
  inference = EXCLUDED.inference,
  publishable = EXCLUDED.publishable,
  domain = EXCLUDED.domain,
  formula_disabled = EXCLUDED.formula_disabled,
  evidence_status = EXCLUDED.evidence_status,
  missing = EXCLUDED.missing,
  note = EXCLUDED.note,
  effective_date = EXCLUDED.effective_date,
  variant_of = EXCLUDED.variant_of,
  output_mode = EXCLUDED.output_mode,
  rule_set_json = EXCLUDED.rule_set_json,
  updated_at = now();

-- 9) FIN-BANK-032 额度使用率（分母唯一化）
INSERT INTO platform.metric_definition (
  metric_id, name_zh, display_name, definition, formula_text, denominator_text,
  observation_period, granularity, unit, evidence_basis, provenance_label,
  inference, publishable, domain, formula_disabled, evidence_status, missing,
  note, effective_date, variant_of, output_mode, rule_set_json
) VALUES (
  'FIN-BANK-032',
  '额度使用率',
  '额度使用率〔推测〕',
  '同一时点已用授信额度（提款未还本金）占已批复且状态有效的授信额度总额的比例，反映额度动用程度。',
  'numerator / denominator * 100',
  '同一时点已批复且状态有效的授信额度；按额度协议号去重；循环额度按全额计入；剔除未批复申请、已拒绝、已撤销、已过期未续、已冻结、已注销、内部往来、测试额度；多币种按同一汇率折算；单位 元',
  'point-in-time（月末/季末；分子分母同一时点）',
  'agreement/customer，可按 product/institution',
  '%',
  'industry',
  '推测',
  TRUE,
  FALSE,
  'bank',
  FALSE,
  'EVIDENCE_MISSING',
  'regulatory_source',
  '分母唯一化为同一时点已批复有效授信额度；分子只用提款未还本金，不含利息/费用/罚息；循环额度全额计入分母；行业通行管理实践（未成文）+ 本轮业务合理性拍板；内部可用，不对外发布',
  '2026-11-06',
  NULL,
  'value',
  NULL
)
ON CONFLICT (metric_id) DO UPDATE SET
  name_zh = EXCLUDED.name_zh,
  display_name = EXCLUDED.display_name,
  definition = EXCLUDED.definition,
  formula_text = EXCLUDED.formula_text,
  denominator_text = EXCLUDED.denominator_text,
  observation_period = EXCLUDED.observation_period,
  granularity = EXCLUDED.granularity,
  unit = EXCLUDED.unit,
  evidence_basis = EXCLUDED.evidence_basis,
  provenance_label = EXCLUDED.provenance_label,
  inference = EXCLUDED.inference,
  publishable = EXCLUDED.publishable,
  domain = EXCLUDED.domain,
  formula_disabled = EXCLUDED.formula_disabled,
  evidence_status = EXCLUDED.evidence_status,
  missing = EXCLUDED.missing,
  note = EXCLUDED.note,
  effective_date = EXCLUDED.effective_date,
  variant_of = EXCLUDED.variant_of,
  output_mode = EXCLUDED.output_mode,
  rule_set_json = EXCLUDED.rule_set_json,
  updated_at = now();

-- 10) FIN-BANK-035 催收回收率（分母唯一化）
INSERT INTO platform.metric_definition (
  metric_id, name_zh, display_name, definition, formula_text, denominator_text,
  observation_period, granularity, unit, evidence_basis, provenance_label,
  inference, publishable, domain, formula_disabled, evidence_status, missing,
  note, effective_date, variant_of, output_mode, rule_set_json
) VALUES (
  'FIN-BANK-035',
  '催收回收率',
  '催收回收率〔推测〕',
  '观察期初已进入催收的逾期资产，在观察期内以现金方式回收的本金占期初应催收本金余额的比例。',
  'numerator / denominator * 100',
  '观察期初（T0 日终）状态=催收中且逾期本金>0 的账户本金余额；按账户去重；剔除已核销、已转出、已重组退出催收、内部往来、测试账户、已结清；单位 元',
  'period（3/6/12 个月；cohort=期初在催账户；期末观察）',
  'institution/product，可按催收渠道',
  '%',
  'industry',
  '推测',
  TRUE,
  FALSE,
  'bank',
  FALSE,
  'EVIDENCE_MISSING',
  'regulatory_source',
  '分母唯一化为期初在催账户本金余额；本金对本金、现金回收；核销后回收另设 memo；行业通行管理实践（未成文）+ 本轮业务合理性拍板；内部可用，不对外发布',
  '2026-11-06',
  NULL,
  'value',
  NULL
)
ON CONFLICT (metric_id) DO UPDATE SET
  name_zh = EXCLUDED.name_zh,
  display_name = EXCLUDED.display_name,
  definition = EXCLUDED.definition,
  formula_text = EXCLUDED.formula_text,
  denominator_text = EXCLUDED.denominator_text,
  observation_period = EXCLUDED.observation_period,
  granularity = EXCLUDED.granularity,
  unit = EXCLUDED.unit,
  evidence_basis = EXCLUDED.evidence_basis,
  provenance_label = EXCLUDED.provenance_label,
  inference = EXCLUDED.inference,
  publishable = EXCLUDED.publishable,
  domain = EXCLUDED.domain,
  formula_disabled = EXCLUDED.formula_disabled,
  evidence_status = EXCLUDED.evidence_status,
  missing = EXCLUDED.missing,
  note = EXCLUDED.note,
  effective_date = EXCLUDED.effective_date,
  variant_of = EXCLUDED.variant_of,
  output_mode = EXCLUDED.output_mode,
  rule_set_json = EXCLUDED.rule_set_json,
  updated_at = now();

-- 11) FIN-BANK-036 族索引（原行转为索引并停用）
INSERT INTO platform.metric_definition (
  metric_id, name_zh, display_name, definition, formula_text, denominator_text,
  observation_period, granularity, unit, evidence_basis, provenance_label,
  inference, publishable, domain, formula_disabled, evidence_status, missing,
  note, effective_date, variant_of, output_mode, rule_set_json
) VALUES (
  'FIN-BANK-036',
  '不良处置率/处置回收率',
  '不良处置率/处置回收率（口径族·索引）〔推测〕',
  '口径族索引：不良处置率（FIN-BANK-036-v1）与处置回收率（FIN-BANK-036-v2）并列；本行不单独出数。',
  '不适用（族索引；见 FIN-BANK-036-v1 / FIN-BANK-036-v2）',
  '不适用（族索引；v1 分母=期初不良资产余额；v2 分母=期内完成处置不良账面金额）',
  '不适用（族索引；变体观察期见 v1/v2）',
  '不适用（族索引）',
  '%',
  'industry',
  '推测',
  TRUE,
  FALSE,
  'bank',
  TRUE,
  'EVIDENCE_MISSING',
  'regulatory_source',
  'v5 拆为 FIN-BANK-036-v1（不良处置率）与 -v2（处置回收率）；本行保留为族索引，formula_disabled=true 防误用；纯核销只在 v1 分子体现，不进 v2 分母；内部使用变体，不对外发布',
  '2026-11-06',
  NULL,
  'index',
  NULL
)
ON CONFLICT (metric_id) DO UPDATE SET
  name_zh = EXCLUDED.name_zh,
  display_name = EXCLUDED.display_name,
  definition = EXCLUDED.definition,
  formula_text = EXCLUDED.formula_text,
  denominator_text = EXCLUDED.denominator_text,
  observation_period = EXCLUDED.observation_period,
  granularity = EXCLUDED.granularity,
  unit = EXCLUDED.unit,
  evidence_basis = EXCLUDED.evidence_basis,
  provenance_label = EXCLUDED.provenance_label,
  inference = EXCLUDED.inference,
  publishable = EXCLUDED.publishable,
  domain = EXCLUDED.domain,
  formula_disabled = EXCLUDED.formula_disabled,
  evidence_status = EXCLUDED.evidence_status,
  missing = EXCLUDED.missing,
  note = EXCLUDED.note,
  effective_date = EXCLUDED.effective_date,
  variant_of = EXCLUDED.variant_of,
  output_mode = EXCLUDED.output_mode,
  rule_set_json = EXCLUDED.rule_set_json,
  updated_at = now();

-- 12) FIN-BANK-036-v1 不良处置率
INSERT INTO platform.metric_definition (
  metric_id, name_zh, display_name, definition, formula_text, denominator_text,
  observation_period, granularity, unit, evidence_basis, provenance_label,
  inference, publishable, domain, formula_disabled, evidence_status, missing,
  note, effective_date, variant_of, output_mode, rule_set_json
) VALUES (
  'FIN-BANK-036-v1',
  '不良处置率',
  '不良处置率〔推测〕',
  '报告期内完成处置的不良资产账面金额占期初不良资产余额的比例，衡量不良存量消化进度。',
  'numerator / denominator * 100（分子=期内完成处置的不良资产账面金额；分母=期初不良资产余额）',
  '期初不良资产余额=次级+可疑+损失；按资产去重；剔除已核销、已转出、内部往来、测试资产；含重组后仍分类为不良的资产；单位 元',
  'period（季度/年度）',
  'institution，可按 product',
  '%',
  'industry',
  '推测',
  TRUE,
  FALSE,
  'bank',
  FALSE,
  'EVIDENCE_MISSING',
  'regulatory_source',
  '处置完成事件=现金清收、核销、转让、以物抵债、司法裁定等；不含重组/展期/借新还旧；不含仅启动未完成；分子分母同尺度（账面金额）；内部出数须标 source=INDUSTRY + inference=true；不对外发布',
  '2026-11-06',
  'FIN-BANK-036',
  'value',
  NULL
)
ON CONFLICT (metric_id) DO UPDATE SET
  name_zh = EXCLUDED.name_zh,
  display_name = EXCLUDED.display_name,
  definition = EXCLUDED.definition,
  formula_text = EXCLUDED.formula_text,
  denominator_text = EXCLUDED.denominator_text,
  observation_period = EXCLUDED.observation_period,
  granularity = EXCLUDED.granularity,
  unit = EXCLUDED.unit,
  evidence_basis = EXCLUDED.evidence_basis,
  provenance_label = EXCLUDED.provenance_label,
  inference = EXCLUDED.inference,
  publishable = EXCLUDED.publishable,
  domain = EXCLUDED.domain,
  formula_disabled = EXCLUDED.formula_disabled,
  evidence_status = EXCLUDED.evidence_status,
  missing = EXCLUDED.missing,
  note = EXCLUDED.note,
  effective_date = EXCLUDED.effective_date,
  variant_of = EXCLUDED.variant_of,
  output_mode = EXCLUDED.output_mode,
  rule_set_json = EXCLUDED.rule_set_json,
  updated_at = now();

-- 13) FIN-BANK-036-v2 处置回收率
INSERT INTO platform.metric_definition (
  metric_id, name_zh, display_name, definition, formula_text, denominator_text,
  observation_period, granularity, unit, evidence_basis, provenance_label,
  inference, publishable, domain, formula_disabled, evidence_status, missing,
  note, effective_date, variant_of, output_mode, rule_set_json
) VALUES (
  'FIN-BANK-036-v2',
  '处置回收率',
  '处置回收率〔推测〕',
  '报告期内完成处置的不良资产实际回收金额占期内处置标的账面金额的比例，衡量处置回收效率。',
  'numerator / denominator * 100（分子=期内处置实际回收金额；分母=期内完成处置不良账面金额（有回收方式））',
  '期内完成处置的不良资产账面金额；仅含现金清收、转让、以物抵债、司法裁定等有回收的处置方式；纯核销不计入；按资产/处置事件去重；不含仅启动未完成、内部往来、测试资产；单位 元',
  'period（季度/年度；与 v1 同一报告期）',
  'institution，可按 product/处置方式',
  '%',
  'industry',
  '推测',
  TRUE,
  FALSE,
  'bank',
  FALSE,
  'EVIDENCE_MISSING',
  'regulatory_source',
  '分子=现金回收 + 非现金资产公允价值 − 处置费用；纯核销无回收，不进 v2 分母；核销量在 v1 分子体现；回收金额 > 账面金额时可能 >100%，不截断，标记溢价/数据异常；内部出数须标 source=INDUSTRY + inference=true；不对外发布',
  '2026-11-06',
  'FIN-BANK-036',
  'value',
  NULL
)
ON CONFLICT (metric_id) DO UPDATE SET
  name_zh = EXCLUDED.name_zh,
  display_name = EXCLUDED.display_name,
  definition = EXCLUDED.definition,
  formula_text = EXCLUDED.formula_text,
  denominator_text = EXCLUDED.denominator_text,
  observation_period = EXCLUDED.observation_period,
  granularity = EXCLUDED.granularity,
  unit = EXCLUDED.unit,
  evidence_basis = EXCLUDED.evidence_basis,
  provenance_label = EXCLUDED.provenance_label,
  inference = EXCLUDED.inference,
  publishable = EXCLUDED.publishable,
  domain = EXCLUDED.domain,
  formula_disabled = EXCLUDED.formula_disabled,
  evidence_status = EXCLUDED.evidence_status,
  missing = EXCLUDED.missing,
  note = EXCLUDED.note,
  effective_date = EXCLUDED.effective_date,
  variant_of = EXCLUDED.variant_of,
  output_mode = EXCLUDED.output_mode,
  rule_set_json = EXCLUDED.rule_set_json,
  updated_at = now();
