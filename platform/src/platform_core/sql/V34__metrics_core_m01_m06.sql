-- M-01 指标可算性补齐第一批（8 条）与 M-06 partial/规则核对台账。
-- 选型与理由见 doc/_design/53-M01-M06-指标可算性补齐与规则核对.md。
-- 迁移号固定 V34；可重入（UPDATE/ON CONFLICT）。

-- ---------------------------------------------------------------------------
-- M-01：五级迁徙率绑定修正（FIN-BANK-013/014/015/016）
-- 语义：分子=期初该类别中迁徙到更低类别的余额（扣除期内减少额）；
--       分母=期初该类别余额。原绑定分子未扣减少、分母扣减少，导致可 >100%。
-- ---------------------------------------------------------------------------
UPDATE platform.metric_field_binding
SET value_expr = 'GREATEST(balance_start - period_decrease_amount, 0)'
WHERE metric_id IN ('FIN-BANK-013', 'FIN-BANK-014', 'FIN-BANK-015', 'FIN-BANK-016')
  AND role = 'numerator';

UPDATE platform.metric_field_binding
SET value_expr = 'balance_start'
WHERE metric_id IN ('FIN-BANK-013', 'FIN-BANK-014', 'FIN-BANK-015', 'FIN-BANK-016')
  AND role = 'denominator';

-- FIN-INS-018：报案立案率必须按同一报案队列取数（以 report_date 为窗口），
-- 分子再筛 filing_date IS NOT NULL，避免用立案日窗口造成队列错位。
-- ---------------------------------------------------------------------------
UPDATE platform.metric_field_binding
SET window_column = 'report_date',
    filter_sql = 'claim_status <> ''withdrawn'' AND filing_date IS NOT NULL'
WHERE metric_id = 'FIN-INS-018'
  AND role = 'numerator';

-- ---------------------------------------------------------------------------
-- M-06：20 条（9 条 partial 判定 + 11 条规则）逐条状态台账。
-- status 只有三档：executed / registered_only / not_executable。
-- 「仅登记」不得计入可执行；导出走 GET /metrics-readiness?status=registered_only&format=csv。
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS platform.metric_readiness (
    item_kind    text NOT NULL CHECK (item_kind IN ('partial', 'rule')),
    metric_id    text NOT NULL,
    status       text NOT NULL CHECK (status IN ('executed', 'registered_only', 'not_executable')),
    reason       text NOT NULL,
    detail       jsonb NOT NULL DEFAULT '{}'::jsonb,
    evidence_ref text NOT NULL,
    checked_at   date NOT NULL,
    PRIMARY KEY (item_kind, metric_id)
);

COMMENT ON TABLE platform.metric_readiness IS
  'M-06 audit ledger: 9 partial rulings + 11 rule-set metrics; registered_only is never executable';

INSERT INTO platform.metric_readiness (item_kind, metric_id, status, reason, detail, evidence_ref, checked_at)
VALUES
  ('partial', 'FIN-BANK-002', 'executed',
   '6 条规则 spec 完整，经 /metrics/FIN-BANK-002/rules 执行器可执行',
   '{"ruleCount": 6, "specRules": 6, "executor": "/metrics/{id}/rules"}'::jsonb,
   'doc/_design/37-指标口径判定书-v8.md:§2; doc/_design/37-指标口径判定书-v8.md:§3', '2026-11-06'),
  ('partial', 'FIN-BANK-017', 'executed',
   '账户级 DPD 快照表（bank_loan_account.dpd_start/dpd_end）已具备，分子/分母绑定可执行',
   '{"bindingRoles": ["numerator", "denominator"], "factTable": "platform.bank_loan_account"}'::jsonb,
   'doc/_fsldm/02-导入验证/指标可计算性矩阵-v6.md:§6.2', '2026-11-06'),
  ('partial', 'FIN-BANK-018', 'executed',
   '同 FIN-BANK-017，60→90 天迁徙按账户数可复算',
   '{"bindingRoles": ["numerator", "denominator"], "factTable": "platform.bank_loan_account"}'::jsonb,
   'doc/_fsldm/02-导入验证/指标可计算性矩阵-v6.md:§6.2', '2026-11-06'),
  ('partial', 'FIN-BANK-019', 'not_executable',
   '派生指标（FIN-BANK-017 × FIN-BANK-018）；单方言编译器只接受 numerator/denominator 算术，缺派生执行器',
   '{"metricKind": "derived_rate", "missing": "derived_executor"}'::jsonb,
   'doc/_design/37-指标口径判定书-v8.md:§2.1', '2026-11-06'),
  ('partial', 'FIN-INS-009', 'executed',
   'V25 事实表补齐 ceded_premium / reinsurance_reserve_change 列，分子/分母绑定可执行',
   '{"bindingRoles": ["numerator", "denominator"], "factTable": "platform.ins_underwriting_stat"}'::jsonb,
   'doc/_design/37-指标口径判定书-v8.md:§2.1; 迁移 V25__fact_model_v7.sql', '2026-11-06'),
  ('partial', 'FIN-INS-012', 'not_executable',
   '派生指标（FIN-INS-027 + FIN-INS-013）；单方言编译器不支持指标引用，缺派生执行器',
   '{"metricKind": "derived_rate", "missing": "derived_executor"}'::jsonb,
   'doc/_design/37-指标口径判定书-v8.md:§2.1', '2026-11-06'),
  ('partial', 'CUST-002', 'executed',
   '按日合并的 RFM-F 频次绑定可执行（cust_transaction.txn_date，剔除 refund 且 amount>0）',
   '{"bindingRoles": ["numerator"], "factTable": "platform.cust_transaction"}'::jsonb,
   'doc/_design/37-指标口径判定书-v8.md:§2; 迁移 V25__fact_model_v7.sql', '2026-11-06'),
  ('partial', 'CUST-004', 'not_executable',
   'RFM 五分位打分是非标量 score，平台无 score 执行器，禁止用绑定冒充可执行',
   '{"metricKind": "score", "missing": "score_executor"}'::jsonb,
   'doc/_design/37-指标口径判定书-v8.md:§2.1', '2026-11-06'),
  ('partial', 'CUST-005', 'registered_only',
   '代理事件优先级仅登记在 decision_recommendation；当前绑定使用预计算 days_since_proxy_event，未按裁决的 COALESCE 优先级执行，且不支持按 asOf 求天数差',
   '{"decision": "registered", "binding": "precomputed days_since_proxy_event", "missing": "asOf day-diff + COALESCE priority executor"}'::jsonb,
   'doc/_design/37-指标口径判定书-v8.md:§2.1', '2026-11-06'),
  ('rule', 'FIN-BANK-002', 'executed',
   '6 条规则 spec 完整，/metrics/FIN-BANK-002/rules 可执行',
   '{"ruleCount": 6, "specRules": 6, "executor": "/metrics/{id}/rules"}'::jsonb,
   'doc/_design/37-指标口径判定书-v8.md:§3', '2026-11-06'),
  ('rule', 'FIN-BANK-003', 'executed',
   '1 条规则 spec 完整，/metrics/FIN-BANK-003/rules 可执行',
   '{"ruleCount": 1, "specRules": 1, "executor": "/metrics/{id}/rules"}'::jsonb,
   'doc/_design/37-指标口径判定书-v8.md:§3', '2026-11-06'),
  ('rule', 'FIN-BANK-004', 'executed',
   '1 条规则 spec 完整，/metrics/FIN-BANK-004/rules 可执行',
   '{"ruleCount": 1, "specRules": 1, "executor": "/metrics/{id}/rules"}'::jsonb,
   'doc/_design/37-指标口径判定书-v8.md:§3', '2026-11-06'),
  ('rule', 'FIN-BANK-005', 'executed',
   '1 条规则 spec 完整，/metrics/FIN-BANK-005/rules 可执行',
   '{"ruleCount": 1, "specRules": 1, "executor": "/metrics/{id}/rules"}'::jsonb,
   'doc/_design/37-指标口径判定书-v8.md:§3', '2026-11-06'),
  ('rule', 'FIN-BANK-006', 'executed',
   '1 条规则 spec 完整，/metrics/FIN-BANK-006/rules 可执行',
   '{"ruleCount": 1, "specRules": 1, "executor": "/metrics/{id}/rules"}'::jsonb,
   'doc/_design/37-指标口径判定书-v8.md:§3', '2026-11-06'),
  ('rule', 'FIN-BANK-007', 'executed',
   '4 条规则 spec 完整，/metrics/FIN-BANK-007/rules 可执行',
   '{"ruleCount": 4, "specRules": 4, "executor": "/metrics/{id}/rules"}'::jsonb,
   'doc/_design/37-指标口径判定书-v8.md:§3', '2026-11-06'),
  ('rule', 'FIN-BANK-009', 'executed',
   '1 条规则 spec 完整，/metrics/FIN-BANK-009/rules 可执行',
   '{"ruleCount": 1, "specRules": 1, "executor": "/metrics/{id}/rules"}'::jsonb,
   'doc/_design/37-指标口径判定书-v8.md:§3', '2026-11-06'),
  ('rule', 'FIN-BANK-010', 'executed',
   '1 条规则 spec 完整，/metrics/FIN-BANK-010/rules 可执行',
   '{"ruleCount": 1, "specRules": 1, "executor": "/metrics/{id}/rules"}'::jsonb,
   'doc/_design/37-指标口径判定书-v8.md:§3', '2026-11-06'),
  ('rule', 'FIN-BANK-011', 'executed',
   '1 条规则 spec 完整，/metrics/FIN-BANK-011/rules 可执行',
   '{"ruleCount": 1, "specRules": 1, "executor": "/metrics/{id}/rules"}'::jsonb,
   'doc/_design/37-指标口径判定书-v8.md:§3', '2026-11-06'),
  ('rule', 'FIN-BANK-012', 'executed',
   '1 条规则 spec 完整，/metrics/FIN-BANK-012/rules 可执行',
   '{"ruleCount": 1, "specRules": 1, "executor": "/metrics/{id}/rules"}'::jsonb,
   'doc/_design/37-指标口径判定书-v8.md:§3', '2026-11-06'),
  ('rule', 'FIN-BANK-024', 'executed',
   '2 条规则 spec 完整，/metrics/FIN-BANK-024/rules 可执行',
   '{"ruleCount": 2, "specRules": 2, "executor": "/metrics/{id}/rules"}'::jsonb,
   'doc/_design/37-指标口径判定书-v8.md:§3', '2026-11-06')
ON CONFLICT (item_kind, metric_id) DO UPDATE SET
  status = EXCLUDED.status,
  reason = EXCLUDED.reason,
  detail = EXCLUDED.detail,
  evidence_ref = EXCLUDED.evidence_ref,
  checked_at = EXCLUDED.checked_at;
