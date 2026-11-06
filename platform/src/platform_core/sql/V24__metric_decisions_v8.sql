-- V24: auditable decisions for the 9 partial quartets and machine-readable specs
-- for the 11 blocked_rule metrics. Everything here is either derived from the
-- existing definition text or explicitly marked as a recommended default that
-- still needs business sign-off. No new business values are invented.

ALTER TABLE platform.metric_definition
  ADD COLUMN IF NOT EXISTS decision_owner text;
ALTER TABLE platform.metric_definition
  ADD COLUMN IF NOT EXISTS decision_recommendation jsonb;
COMMENT ON COLUMN platform.metric_definition.decision_owner IS
  '口径裁定的责任人；业务待签 = 平台给出推荐值但尚未获业务签字。';
COMMENT ON COLUMN platform.metric_definition.decision_recommendation IS
  '推荐取值、理由、影响与改动点；与 quartet_derivation 的推导依据分离，避免把推荐写成原文。';

-- ---- 9 partial quartets -------------------------------------------------
-- FIN-BANK-002: formula text is executable once the M6 cap and M0 boundary are
-- fixed. 0 = M0; 1-30 = M1 ... 151+ = M6.
UPDATE platform.metric_definition SET
  formula_expr = 'band(dpd, 30, 6)',
  numerator_agg = 'max',
  denominator_agg = NULL,
  missing = NULL,
  inference = true,
  publishable = false,
  decision_owner = '业务待签',
  decision_recommendation = $json${
    "decisionId": "D-2026-11-06-FIN-BANK-002",
    "status": "recommended_pending_business_signoff",
    "missingBefore": "formula_expr：中文伪代码，且未写 M6 上限与 M0 边界",
    "recommendation": {
      "formulaExpr": "band(dpd, 30, 6)",
      "numeratorAgg": "max",
      "boundaries": {"M0": "dpd=0", "M1": "1-30", "M2": "31-60", "M3": "61-90", "M4": "91-120", "M5": "121-150", "M6": ">=151（封顶）"}
    },
    "reason": "定义原文已给出 floor((max(观察日-应还款日,0)-1)/30)+1，且写明未逾期记 M0；只补写原文缺失的 M6 封顶，未新增阈值。",
    "alternatives": ["不封顶（会出现 M7+，与指标的 M0-M6 名称冲突）"],
    "impact": "M6 口径固定为 151 天及以上；不封顶会让分档名称与取值域不一致。",
    "changePoint": "platform.metric_definition.formula_expr 与 rule_set_json.R01-R06 的阈值；无需改代码。",
    "configurable": true
  }$json$::jsonb,
  quartet_derivation = $json${
    "status": "resolved_by_recommendation",
    "source": "09-definitions-v4.seed.sql / V21 / V23",
    "fields": {
      "metric_kind": {"value": "band", "basis": "formula_text 为分档表达式（floor）"},
      "formula_expr": {"value": "band(dpd, 30, 6)", "basis": "原文 floor((dpd-1)/30)+1；补 M6 上限 151 天，见 decision_recommendation"},
      "window_kind": {"value": "instant", "basis": "observation_period 前缀 point-in-time"},
      "numerator_agg": {"value": "max", "basis": "分档输入为账户级 DPD，取观测日时点值"},
      "denominator_agg": {"value": null, "basis": "分档非比率，无分母"}
    }
  }$json$::jsonb,
  computability_tier = 'blocked_semantics'
 WHERE metric_id = 'FIN-BANK-002';

-- FIN-BANK-017/018: retail defaults to account count; corporate balance is the
-- documented alternative. No account-level DPD fact exists yet, so the tier
-- stays blocked_semantics until a binding can be registered.
UPDATE platform.metric_definition SET
  numerator_agg = 'count_distinct',
  denominator_agg = 'count_distinct',
  missing = NULL,
  inference = true,
  publishable = false,
  decision_owner = '业务待签',
  decision_recommendation = $json${
    "decisionId": "D-2026-11-06-FIN-BANK-017",
    "status": "recommended_pending_business_signoff",
    "missingBefore": "numerator_agg / denominator_agg：文本把零售户数和对公余额并列，未裁定",
    "recommendation": {"numeratorAgg": "count_distinct", "denominatorAgg": "count_distinct", "entity": "account_id", "portfolio": "retail"},
    "reason": "指标名为零售 DPD roll rate；行业通行以账户数（户数）为权重，避免大额账户掩盖小额账户的迁徙。对公余额口径保留为可切换配置。",
    "alternatives": ["sum(principal_balance)：对公余额加权；换用需同时改两个 agg 与字段绑定 value_expr"],
    "impact": "零售户数口径下，单户多账户按账户去重；对公余额口径会显著改变分母量级。",
    "changePoint": "platform.metric_definition.numerator_agg/denominator_agg + metric_field_binding.value_expr；无需改代码。",
    "blockedBy": "事实模型没有账户级 DPD 时点表；bank_ews_signal 只有客户级 dpd，不能冒充账户口径。",
    "configurable": true
  }$json$::jsonb,
  quartet_derivation = $json${
    "status": "resolved_by_recommendation",
    "source": "09-definitions-v4.seed.sql / V21 / V23",
    "fields": {
      "metric_kind": {"value": "ratio", "basis": "unit=% 且 formula_text 为分子/分母比值"},
      "formula_expr": {"value": "numerator / denominator * 100", "basis": "formula_text 原文"},
      "window_kind": {"value": "period", "basis": "observation_period 前缀 period"},
      "numerator_agg": {"value": "count_distinct", "basis": "推荐零售账户数口径，见 decision_recommendation"},
      "denominator_agg": {"value": "count_distinct", "basis": "推荐零售账户数口径，见 decision_recommendation"}
    }
  }$json$::jsonb,
  computability_tier = 'blocked_semantics'
 WHERE metric_id = 'FIN-BANK-017';

UPDATE platform.metric_definition SET
  numerator_agg = 'count_distinct',
  denominator_agg = 'count_distinct',
  missing = NULL,
  inference = true,
  publishable = false,
  decision_owner = '业务待签',
  decision_recommendation = $json${
    "decisionId": "D-2026-11-06-FIN-BANK-018",
    "status": "recommended_pending_business_signoff",
    "missingBefore": "numerator_agg / denominator_agg：文本把零售户数和对公余额并列，未裁定",
    "recommendation": {"numeratorAgg": "count_distinct", "denominatorAgg": "count_distinct", "entity": "account_id", "portfolio": "retail"},
    "reason": "与 FIN-BANK-017 同一口径族；行业通行以账户数为权重，保持两期迁徙率可比。",
    "alternatives": ["sum(principal_balance)：对公余额加权"],
    "impact": "分母为 60-89 天账户数；换余额口径会改变比率含义。",
    "changePoint": "platform.metric_definition.numerator_agg/denominator_agg + metric_field_binding.value_expr；无需改代码。",
    "blockedBy": "事实模型没有账户级 DPD 时点表。",
    "configurable": true
  }$json$::jsonb,
  quartet_derivation = $json${
    "status": "resolved_by_recommendation",
    "source": "09-definitions-v4.seed.sql / V21 / V23",
    "fields": {
      "metric_kind": {"value": "ratio", "basis": "unit=% 且 formula_text 为分子/分母比值"},
      "formula_expr": {"value": "numerator / denominator * 100", "basis": "formula_text 原文"},
      "window_kind": {"value": "period", "basis": "observation_period 前缀 period"},
      "numerator_agg": {"value": "count_distinct", "basis": "推荐零售账户数口径，见 decision_recommendation"},
      "denominator_agg": {"value": "count_distinct", "basis": "推荐零售账户数口径，见 decision_recommendation"}
    }
  }$json$::jsonb,
  computability_tier = 'blocked_semantics'
 WHERE metric_id = 'FIN-BANK-018';

-- FIN-BANK-019: product of two adjacent roll rates. Declared as a derived
-- expression; the scalar compiler rejects the metric-reference syntax on
-- purpose and no derived executor exists yet.
UPDATE platform.metric_definition SET
  metric_kind = 'derived_rate',
  formula_expr = 'metric_fin_bank_017 * metric_fin_bank_018',
  numerator_agg = NULL,
  denominator_agg = NULL,
  missing = NULL,
  inference = true,
  publishable = false,
  decision_owner = '业务待签',
  decision_recommendation = $json${
    "decisionId": "D-2026-11-06-FIN-BANK-019",
    "status": "recommended_pending_business_signoff",
    "missingBefore": "formula_expr：原文写 r(30→60)×r(60→90)，不是 numerator/denominator 表达式",
    "recommendation": {"formulaExpr": "metric_fin_bank_017 * metric_fin_bank_018", "derivedFrom": ["FIN-BANK-017", "FIN-BANK-018"]},
    "reason": "原文已明确两期迁徙率乘积近似；用指标引用表达，避免把两段公式复制成不可审计的文本。",
    "alternatives": ["同批账户严格口径：按期初 30-59 天账户集合跟踪到 90+，需要两期快照 join；当前事实模型未提供"],
    "impact": "乘积近似在无新增/退出时严格成立；有新增/退出时略高估。",
    "changePoint": "platform.metric_definition.formula_expr；接入派生执行器后改 derived_rate 分支。",
    "configurable": true
  }$json$::jsonb,
  quartet_derivation = $json${
    "status": "resolved_by_recommendation",
    "source": "09-definitions-v4.seed.sql / V21 / V23",
    "fields": {
      "metric_kind": {"value": "derived_rate", "basis": "formula_text 为另两条指标的乘积"},
      "formula_expr": {"value": "metric_fin_bank_017 * metric_fin_bank_018", "basis": "原文 r(30→60)×r(60→90)，映射到两条指标引用"},
      "window_kind": {"value": "period", "basis": "observation_period 前缀 period"},
      "numerator_agg": {"value": null, "basis": "派生指标无独立分子聚合；分量口径见 FIN-BANK-017"},
      "denominator_agg": {"value": null, "basis": "派生指标无独立分母聚合；分量口径见 FIN-BANK-018"}
    }
  }$json$::jsonb,
  computability_tier = 'blocked_semantics'
 WHERE metric_id = 'FIN-BANK-019';

-- FIN-INS-009: numerator is paid claim amount (sum). Denominator (earned
-- premium net of reinsurance) has no fact column, so no binding is invented.
UPDATE platform.metric_definition SET
  numerator_agg = 'sum',
  missing = NULL,
  inference = true,
  publishable = false,
  decision_owner = '业务待签',
  decision_recommendation = $json${
    "decisionId": "D-2026-11-06-FIN-INS-009",
    "status": "recommended_pending_business_signoff",
    "missingBefore": "numerator_agg：未说明分子是可加总金额还是去重计数",
    "recommendation": {"numeratorAgg": "sum", "numeratorField": "paid_amount"},
    "reason": "综合赔付率的分子是赔款支出，金额必须可加总；去重计数会变成案件频次，口径不成立。",
    "alternatives": ["count_distinct(claim_no)：仅适用于案均/频次类指标，不适用于赔付率"],
    "impact": "只补分子聚合；再保后已赚保费仍无事实字段，指标保持不可绑定。",
    "changePoint": "platform.metric_definition.numerator_agg；补分母事实后再加 metric_field_binding。",
    "blockedBy": "再保后已赚保费 = 已赚保费 − 分出保费分摊 + 摊回责任准备金变动，事实模型无此三列。",
    "configurable": true
  }$json$::jsonb,
  quartet_derivation = $json${
    "status": "resolved_by_recommendation",
    "source": "09-definitions-v4.seed.sql / V21 / V23",
    "fields": {
      "metric_kind": {"value": "ratio", "basis": "unit=% 且 formula_text 为分子/分母比值"},
      "formula_expr": {"value": "numerator / denominator * 100", "basis": "formula_text 原文"},
      "window_kind": {"value": "period", "basis": "observation_period 前缀 period"},
      "numerator_agg": {"value": "sum", "basis": "赔款支出为可加总金额，见 decision_recommendation"},
      "denominator_agg": {"value": "sum", "basis": "分母为保费口径；V23 已由 denominator_text 推出 sum"}
    }
  }$json$::jsonb,
  computability_tier = 'blocked_semantics'
 WHERE metric_id = 'FIN-INS-009';

-- FIN-INS-012: two-year combined ratio = two-year expense ratio + two-year
-- claim ratio. FIN-INS-013 is the two-year claim ratio; FIN-INS-027 is the
-- expense ratio evaluated on the same two-year window.
UPDATE platform.metric_definition SET
  metric_kind = 'derived_rate',
  formula_expr = 'metric_fin_ins_027 + metric_fin_ins_013',
  numerator_agg = NULL,
  denominator_agg = NULL,
  missing = NULL,
  inference = true,
  publishable = false,
  decision_owner = '业务待签',
  decision_recommendation = $json${
    "decisionId": "D-2026-11-06-FIN-INS-012",
    "status": "recommended_pending_business_signoff",
    "missingBefore": "formula_expr：原文为两项比率相加，引用其他指标结果",
    "recommendation": {"formulaExpr": "metric_fin_ins_027 + metric_fin_ins_013", "derivedFrom": ["FIN-INS-027", "FIN-INS-013"], "window": "两年合计"},
    "reason": "FIN-INS-013 是定义内的两年赔付率；费用项没有独立的两年指标，按同一两年窗口取 FIN-INS-027 的综合费用率。",
    "alternatives": ["新增 FIN-INS-027-2y 变体，专表两年费用率；可避免借用当期指标"],
    "impact": "若 FIN-INS-027 实际按当期窗口取数，结果会偏低/偏高；必须在派生执行时强制两年窗口。",
    "changePoint": "platform.metric_definition.formula_expr 与 derivedFrom；执行器需按 window=两年。",
    "configurable": true
  }$json$::jsonb,
  quartet_derivation = $json${
    "status": "resolved_by_recommendation",
    "source": "09-definitions-v4.seed.sql / V21 / V23",
    "fields": {
      "metric_kind": {"value": "derived_rate", "basis": "formula_text 为费用率与赔付率相加"},
      "formula_expr": {"value": "metric_fin_ins_027 + metric_fin_ins_013", "basis": "原文两项均为两年合计口径，映射到费用率与两年赔付率指标"},
      "window_kind": {"value": "period", "basis": "observation_period 前缀 period（两年滚动）"},
      "numerator_agg": {"value": null, "basis": "派生指标无独立分子聚合"},
      "denominator_agg": {"value": null, "basis": "派生指标无独立分母聚合"}
    }
  }$json$::jsonb,
  computability_tier = 'blocked_semantics'
 WHERE metric_id = 'FIN-INS-012';

-- CUST-002: same-day merge is the recommended default (RFM frequency counts
-- active days). Binding uses txn_date, so count_distinct counts distinct days.
UPDATE platform.metric_definition SET
  numerator_agg = 'count_distinct',
  missing = NULL,
  inference = true,
  publishable = false,
  decision_owner = '业务待签',
  decision_recommendation = $json${
    "decisionId": "D-2026-11-06-CUST-002",
    "status": "recommended_pending_business_signoff",
    "missingBefore": "numerator_agg：文本要求固定同日多笔是否合并，业务未裁定",
    "recommendation": {"numeratorAgg": "count_distinct", "dedupeKey": "txn_date", "filters": "txn_type <> 'refund' AND amount > 0"},
    "reason": "RFM-F 的行业通行口径是有效交易天数；同日拆单合并可避免频次虚高。按流水号去重则会把同日多笔计为多次。",
    "alternatives": ["count_distinct(txn_id)：按笔计频；换用需把绑定 value_expr 改为 txn_id，其余不变"],
    "impact": "默认值把同一天的多笔交易计 1 次；客服/缴费场景下更稳定。",
    "changePoint": "platform.metric_definition.numerator_agg 与 metric_field_binding.value_expr（txn_date ↔ txn_id）；无需改代码。",
    "configurable": true
  }$json$::jsonb,
  quartet_derivation = $json${
    "status": "resolved_by_recommendation",
    "source": "09-definitions-v4.seed.sql / V21 / V23",
    "fields": {
      "metric_kind": {"value": "count", "basis": "unit=次"},
      "formula_expr": {"value": "numerator", "basis": "可加总/计数/时长型，无分母"},
      "window_kind": {"value": "period", "basis": "observation_period 前缀 period（滚动 12 个月）"},
      "numerator_agg": {"value": "count_distinct", "basis": "推荐同日合并口径，见 decision_recommendation"},
      "denominator_agg": {"value": null, "basis": "计数型无分母"}
    }
  }$json$::jsonb,
  computability_tier = 'blocked_semantics'
 WHERE metric_id = 'CUST-002';

-- CUST-004: NTILE(5) per dimension. Non-scalar output; no score executor yet.
UPDATE platform.metric_definition SET
  metric_kind = 'score',
  formula_expr = 'score(ntile, rfm_code, 5)',
  missing = NULL,
  inference = true,
  publishable = false,
  decision_owner = '业务待签',
  decision_recommendation = $json${
    "decisionId": "D-2026-11-06-CUST-004",
    "status": "recommended_pending_business_signoff",
    "missingBefore": "formula_expr：NTILE(5) 分位打分需先确定 RFM 三项输入口径与分位边界",
    "recommendation": {
      "formulaExpr": "score(ntile, rfm_code, 5)",
      "scoreDirection": {"R": "最近优先，5 分最好", "F": "频次高者 5 分", "M": "金额高者 5 分"},
      "tieBreak": "customer_no（禁止 RANDOM，保证可复算）",
      "groups": "同客群、同窗口、NULL 客户不参与切分"
    },
    "reason": "分位打分只能确定算法族；输入字段与并列处理必须固定，否则同一批客户每次结果不同。",
    "alternatives": ["按固定阈值打分：需要业务给出各维阈值，当前文本未提供"],
    "impact": "NTILE 在并列值处依赖排序稳定性；固定 customer_no 避免结果漂移。",
    "changePoint": "platform.metric_definition.formula_expr 与未来 score 执行器的排序键；当前无执行器。",
    "blockedBy": "score 为非标量输出，单方言编译器只接受 numerator/denominator 算术表达式。",
    "configurable": true
  }$json$::jsonb,
  quartet_derivation = $json${
    "status": "resolved_by_recommendation",
    "source": "09-definitions-v4.seed.sql / V21 / V23",
    "fields": {
      "metric_kind": {"value": "score", "basis": "formula_text 为 NTILE(5) 分位打分"},
      "formula_expr": {"value": "score(ntile, rfm_code, 5)", "basis": "原文 NTILE(5) + RFM 三维；补齐排序方向与并列键，见 decision_recommendation"},
      "window_kind": {"value": "instant", "basis": "observation_period 前缀 point-in-time"},
      "numerator_agg": {"value": null, "basis": "非标量打分，无分子聚合"},
      "denominator_agg": {"value": null, "basis": "非标量打分，无分母聚合"}
    }
  }$json$::jsonb,
  computability_tier = 'blocked_semantics'
 WHERE metric_id = 'CUST-004';

-- CUST-005: proxy event priority. Registration date is the default proxy; no
-- event yields NULL, never 0.
UPDATE platform.metric_definition SET
  formula_expr = 'numerator',
  numerator_agg = 'max',
  denominator_agg = NULL,
  missing = NULL,
  inference = true,
  publishable = false,
  decision_owner = '业务待签',
  decision_recommendation = $json${
    "decisionId": "D-2026-11-06-CUST-005",
    "status": "recommended_pending_business_signoff",
    "missingBefore": "formula_expr：代理事件未定义，且无事件时 R 的处理未裁定",
    "recommendation": {
      "formulaExpr": "numerator",
      "numeratorAgg": "max",
      "proxyPriority": ["registration_date", "first_holding_date", "first_txn_date", "policy_issue_date"],
      "noEvent": "NULL（不置 0，不参与分档）"
    },
    "reason": "原文写明用注册/开卡/首单/保单生效日作为代理；按可获得性排序，注册日最普遍且不依赖交易。",
    "alternatives": ["固定单一代理事件（如只认首单）：会漏掉未交易客户，覆盖下降"],
    "impact": "不同代理事件会改变 R 值；无事件置 NULL 保持分档分母干净。",
    "changePoint": "metric_field_binding.value_expr/filter_sql（接入事实字段时按 proxyPriority 实现 COALESCE）；无需改指标定义。",
    "blockedBy": "事实模型没有统一的客户代理事件日，且编译器 value_expr 不支持按请求 asOf 求天数差。",
    "configurable": true
  }$json$::jsonb,
  quartet_derivation = $json${
    "status": "resolved_by_recommendation",
    "source": "09-definitions-v4.seed.sql / V21 / V23",
    "fields": {
      "metric_kind": {"value": "duration", "basis": "unit=天"},
      "formula_expr": {"value": "numerator", "basis": "原文 max(基准日-代理事件日,0)，非比率"},
      "window_kind": {"value": "instant", "basis": "observation_period 前缀 point-in-time"},
      "numerator_agg": {"value": "max", "basis": "取最近一次代理事件，不求和"},
      "denominator_agg": {"value": null, "basis": "时长型无分母"}
    }
  }$json$::jsonb,
  computability_tier = 'blocked_semantics'
 WHERE metric_id = 'CUST-005';

-- ---- bindings added by the decisions --------------------------------
-- CUST-002 counts distinct transaction days per customer (same-day merge).
INSERT INTO platform.metric_field_binding
  (metric_id, definition_version, role, fact_table, entity_column, value_expr,
   agg, filter_sql, window_column, window_mode) VALUES
  ('CUST-002', 'v3.0', 'numerator', 'platform.cust_transaction', 'customer_no',
   'txn_date', 'count_distinct', 'txn_type <> ''refund'' AND amount > 0',
   'txn_date', 'period')
ON CONFLICT (metric_id, definition_version, role) DO UPDATE SET
  fact_table = EXCLUDED.fact_table, entity_column = EXCLUDED.entity_column,
  value_expr = EXCLUDED.value_expr, agg = EXCLUDED.agg,
  filter_sql = EXCLUDED.filter_sql, window_column = EXCLUDED.window_column,
  window_mode = EXCLUDED.window_mode;
UPDATE platform.metric_definition SET grain = 'customer', min_window_days = 365
 WHERE metric_id = 'CUST-002';

-- ---- 11 blocked_rule metrics: machine-readable rule specs -------------
-- Each rule carries: id, trigger fields, comparison/threshold, window, level,
-- debounce, suppression. Defaults are industry/operational values and stay
-- configurable; they are not presented as new regulatory text.
UPDATE platform.metric_definition SET
  output_mode = 'rule_set',
  rule_set_json = $json$[
    {"id":"R01","signal":"逾期进入 M1（1-30 天）","level":"L1","window":"日","threshold":">=1 天","debounce":"连续 2 个观测日","suppression":"已核销/已结清/已进入不良处置的不重复告警","trigger_fields":["dpd"],"configurable":true,"evidence_basis":"industry","threshold_source":"definition_text","disclaimer":"默认值为行业通行配置，非监管阈值，需业务确认后调整","spec":{"op":"gte","field":"dpd","value":1}},
    {"id":"R02","signal":"逾期进入 M2（31-60 天）","level":"L1","window":"日","threshold":">=31 天","debounce":"连续 2 个观测日","suppression":"同上；观察期内分类不得上调","trigger_fields":["dpd"],"configurable":true,"evidence_basis":"industry","threshold_source":"definition_text","disclaimer":"默认值为行业通行配置，非监管阈值，需业务确认后调整","spec":{"op":"gte","field":"dpd","value":31}},
    {"id":"R03","signal":"逾期进入 M3（61-90 天）","level":"L2","window":"日","threshold":">=61 天","debounce":"即时","suppression":"已重组/已展期的观察期内按重组口径","trigger_fields":["dpd"],"configurable":true,"evidence_basis":"industry","threshold_source":"definition_text","disclaimer":"默认值为行业通行配置，非监管阈值，需业务确认后调整","spec":{"op":"gte","field":"dpd","value":61}},
    {"id":"R04","signal":"逾期进入 M4（91-120 天）","level":"L2","window":"日","threshold":">=91 天","debounce":"即时","suppression":"同上","trigger_fields":["dpd"],"configurable":true,"evidence_basis":"industry","threshold_source":"definition_text","disclaimer":"默认值为行业通行配置，非监管阈值，需业务确认后调整","spec":{"op":"gte","field":"dpd","value":91}},
    {"id":"R05","signal":"逾期进入 M5（121-150 天）","level":"L2","window":"日","threshold":">=121 天","debounce":"即时","suppression":"同上","trigger_fields":["dpd"],"configurable":true,"evidence_basis":"industry","threshold_source":"definition_text","disclaimer":"默认值为行业通行配置，非监管阈值，需业务确认后调整","spec":{"op":"gte","field":"dpd","value":121}},
    {"id":"R06","signal":"逾期进入 M6（151 天及以上）","level":"L3","window":"日","threshold":">=151 天","debounce":"即时","suppression":"同一对象 30 天内已 L3 的合并","trigger_fields":["dpd"],"configurable":true,"evidence_basis":"industry","threshold_source":"definition_text","disclaimer":"默认值为行业通行配置，非监管阈值，需业务确认后调整","spec":{"op":"gte","field":"dpd","value":151}}
  ]$json$::jsonb
 WHERE metric_id = 'FIN-BANK-002';

UPDATE platform.metric_definition SET
  output_mode = 'rule_set',
  rule_set_json = $json$[
    {"id":"R01","signal":"逾期超过 90 天，分类下限至少次级","level":"L3","window":"日","threshold":">90 天","debounce":"即时","suppression":"同对象 30 天内已 L3 的合并；已下调分类的不重复告警","trigger_fields":["dpd"],"configurable":true,"evidence_basis":"regulatory","threshold_source":"definition_text","change_control":"90 天为定义原文阈值，调整需风险管理部/监管口径负责人签字","spec":{"op":"gte","field":"dpd","value":91}}
  ]$json$::jsonb
 WHERE metric_id = 'FIN-BANK-003';

UPDATE platform.metric_definition SET
  output_mode = 'rule_set',
  rule_set_json = $json$[
    {"id":"R01","signal":"逾期超过 90 天，划入 IFRS 9 Stage 3","level":"L3","window":"报告日","threshold":">90 天","debounce":"即时","suppression":"同对象 30 天内已 Stage 3 的合并","trigger_fields":["dpd"],"configurable":true,"evidence_basis":"industry","threshold_source":"definition_text","disclaimer":"默认值为行业通行配置，非监管阈值，需业务确认后调整","spec":{"op":"gte","field":"dpd","value":91}}
  ]$json$::jsonb
 WHERE metric_id = 'FIN-BANK-004';

UPDATE platform.metric_definition SET
  output_mode = 'rule_set',
  rule_set_json = $json$[
    {"id":"R01","signal":"逾期 30 天以上且未发生信用减值，划入 Stage 2","level":"L2","window":"报告日","threshold":">30 天 且 credit_impaired=false","debounce":"即时","suppression":"有定量/定性证据推翻显著增加的，人工抑制并留痕","trigger_fields":["dpd","credit_impaired"],"configurable":true,"evidence_basis":"industry","threshold_source":"industry_default","disclaimer":"30 天为可推翻假设，默认值非监管阈值，需业务确认后调整","spec":{"op":"all_of","clauses":[{"op":"gte","field":"dpd","value":31},{"op":"equals","field":"credit_impaired","value":false}]}}
  ]$json$::jsonb
 WHERE metric_id = 'FIN-BANK-005';

UPDATE platform.metric_definition SET
  output_mode = 'rule_set',
  rule_set_json = $json$[
    {"id":"R01","signal":"实还金额低于当期应还，判定该期逾期","level":"L1","window":"应还款日后逐日","threshold":"paid_amount/due_amount < 1","debounce":"当期首次触发","suppression":"宽限期内、已批准展期的不告警","trigger_fields":["paid_amount","due_amount"],"configurable":true,"evidence_basis":"industry","threshold_source":"definition_text","disclaimer":"默认值为行业通行配置，非监管阈值，需业务确认后调整","spec":{"op":"ratio_lt","numerator":"paid_amount","denominator":"due_amount","value":1.0}}
  ]$json$::jsonb
 WHERE metric_id = 'FIN-BANK-006';

UPDATE platform.metric_definition SET
  output_mode = 'rule_set',
  rule_set_json = $json$[
    {"id":"R01","signal":"分类为次级（不良）","level":"L3","window":"分类日","threshold":"risk_class=substandard","debounce":"即时","suppression":"同一对象 30 天内已 L3 的合并","trigger_fields":["risk_class"],"configurable":true,"evidence_basis":"regulatory","threshold_source":"definition_text","spec":{"op":"equals","field":"risk_class","value":"substandard"}},
    {"id":"R02","signal":"分类为可疑（不良）","level":"L3","window":"分类日","threshold":"risk_class=doubtful","debounce":"即时","suppression":"同上","trigger_fields":["risk_class"],"configurable":true,"evidence_basis":"regulatory","threshold_source":"definition_text","spec":{"op":"equals","field":"risk_class","value":"doubtful"}},
    {"id":"R03","signal":"分类为损失（不良）","level":"L3","window":"分类日","threshold":"risk_class=loss","debounce":"即时","suppression":"同上","trigger_fields":["risk_class"],"configurable":true,"evidence_basis":"regulatory","threshold_source":"definition_text","spec":{"op":"equals","field":"risk_class","value":"loss"}},
    {"id":"R04","signal":"分类为关注","level":"L1","window":"分类日","threshold":"risk_class=special","debounce":"即时","suppression":"已按重组/展期规则处理的按相应规则合并","trigger_fields":["risk_class"],"configurable":true,"evidence_basis":"regulatory","threshold_source":"definition_text","spec":{"op":"equals","field":"risk_class","value":"special"}}
  ]$json$::jsonb
 WHERE metric_id = 'FIN-BANK-007';

UPDATE platform.metric_definition SET
  output_mode = 'rule_set',
  rule_set_json = $json$[
    {"id":"R01","signal":"同一债务人不良债权占比超过 10%，全部债权归为不良","level":"L3","window":"分类日","threshold":">10%","debounce":"即时","suppression":"同一债务人 30 天内已 L3 的合并","trigger_fields":["npl_balance","total_balance"],"configurable":true,"evidence_basis":"regulatory","threshold_source":"definition_text","change_control":"10% 为定义原文阈值，调整需风险管理部签字","spec":{"op":"ratio_gte","numerator":"npl_balance","denominator":"total_balance","value":0.10}}
  ]$json$::jsonb
 WHERE metric_id = 'FIN-BANK-009';

UPDATE platform.metric_definition SET
  output_mode = 'rule_set',
  rule_set_json = $json$[
    {"id":"R01","signal":"财务困难且合同调整，计入重组，分类下限至少关注","level":"L2","window":"观察期 >=365 天且 >=连续 2 个还款期","threshold":"financial_difficulty=true 且 contract_modified=true","debounce":"观察期内持续","suppression":"观察期内不得上调分类；再次重组升级为 L3","trigger_fields":["financial_difficulty","contract_modified"],"configurable":true,"evidence_basis":"regulatory","threshold_source":"definition_text","change_control":"观察期 365 天为定义原文，调整需合规审批","spec":{"op":"all_of","clauses":[{"op":"equals","field":"financial_difficulty","value":true},{"op":"equals","field":"contract_modified","value":true}]}}
  ]$json$::jsonb
 WHERE metric_id = 'FIN-BANK-010';

UPDATE platform.metric_definition SET
  output_mode = 'rule_set',
  rule_set_json = $json$[
    {"id":"R01","signal":"重组观察期已满 180 天，分类下限次级（旧规）","level":"L2","window":"观察期 >=180 天","threshold":"restructuring_flag=true 且 days_since_restructure>=180","debounce":"观察期内持续","suppression":"观察期内不得上调分类；仅历史对照口径","trigger_fields":["restructuring_flag","days_since_restructure"],"configurable":true,"evidence_basis":"regulatory","threshold_source":"definition_text","change_control":"180 天为旧规原文，调整需合规审批","spec":{"op":"all_of","clauses":[{"op":"equals","field":"restructuring_flag","value":true},{"op":"gte","field":"days_since_restructure","value":180}]}}
  ]$json$::jsonb
 WHERE metric_id = 'FIN-BANK-011';

UPDATE platform.metric_definition SET
  output_mode = 'rule_set',
  rule_set_json = $json$[
    {"id":"R01","signal":"展期获批或借新还旧，分类下限至少关注","level":"L1","window":"合同调整日","threshold":"extension_approved=true 或 refinanced=true","debounce":"事件触发 1 次","suppression":"满足财务困难则转 FIN-BANK-010 重组口径并升级","trigger_fields":["extension_approved","refinanced"],"configurable":true,"evidence_basis":"regulatory","threshold_source":"definition_text","spec":{"op":"any_true","fields":["extension_approved","refinanced"]}}
  ]$json$::jsonb
 WHERE metric_id = 'FIN-BANK-012';

UPDATE platform.metric_definition SET
  output_mode = 'rule_set',
  rule_set_json = $json$[
    {"id":"R01","signal":"已发生信用减值或逾期 90 天以上，划入 Stage 3","level":"L3","window":"报告日","threshold":"credit_impaired=true 或 dpd>=91","debounce":"即时","suppression":"同一对象 30 天内已 Stage 3 的合并","trigger_fields":["credit_impaired","dpd"],"configurable":true,"evidence_basis":"regulatory","threshold_source":"definition_text","spec":{"op":"any_of","clauses":[{"op":"any_true","fields":["credit_impaired"]},{"op":"gte","field":"dpd","value":91}]}},
    {"id":"R02","signal":"信用风险显著增加且未减值，划入 Stage 2","level":"L2","window":"报告日","threshold":"significant_increase=true 且 credit_impaired=false","debounce":"即时","suppression":"有定量/定性证据推翻的，人工抑制并留痕","trigger_fields":["significant_increase","credit_impaired"],"configurable":true,"evidence_basis":"regulatory","threshold_source":"industry_default","disclaimer":"显著增加的判定因子需业务确认，默认值非监管阈值","spec":{"op":"all_of","clauses":[{"op":"equals","field":"significant_increase","value":true},{"op":"equals","field":"credit_impaired","value":false}]}}
  ]$json$::jsonb
 WHERE metric_id = 'FIN-BANK-024';

-- ---- four-tier distribution after the decisions ----------------------
UPDATE platform.metric_definition SET computability_tier = 'blocked_semantics'
 WHERE metric_id IN ('FIN-BANK-017','FIN-BANK-018','FIN-BANK-019','FIN-INS-009',
                     'FIN-INS-012','CUST-004','CUST-005');
UPDATE platform.metric_definition SET computability_tier = 'structurally_computable'
 WHERE metric_id IN ('FIN-BANK-002','FIN-BANK-003','FIN-BANK-004','FIN-BANK-005',
                     'FIN-BANK-006','FIN-BANK-007','FIN-BANK-009','FIN-BANK-010',
                     'FIN-BANK-011','FIN-BANK-012','FIN-BANK-024','CUST-002');
