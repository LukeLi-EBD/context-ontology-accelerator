-- SYNTHETIC TEST FIXTURE — not real customer data.
-- F92 verification: makes the metric from synthetic-metric-entity-binding.yaml
-- reachable from the entity detail page, which reads related metrics from
-- platform.metric_definition joined with platform.metric_field_binding.
--
-- Apply against the local platform database (port 5444, database "platform"):
--   psql "$COA_METADATA_PG_DSN" -f synthetic-metric-entity-binding.platform-db.sql
-- Remove with:
--   DELETE FROM platform.metric_field_binding WHERE metric_id = 'synthetic_agreement_exposure';
--   DELETE FROM platform.metric_definition   WHERE metric_id = 'synthetic_agreement_exposure';

INSERT INTO platform.metric_definition (
    metric_id, name_zh, domain, evidence_basis, publishable, inference,
    formula_disabled, evidence_status, definition_version, metric_kind,
    grain, unit, display_name, aggregation_semantics
) VALUES (
    'synthetic_agreement_exposure',
    '合成协议敞口',
    'bank',
    'none',
    false,
    false,
    false,
    'NO_SOURCE',
    'v3.0',
    'simple',
    'agreement',
    'currency',
    'Synthetic agreement exposure (SYNTHETIC TEST FIXTURE)',
    'sum'
)
ON CONFLICT (metric_id) DO NOTHING;

INSERT INTO platform.metric_field_binding (
    metric_id, definition_version, role, fact_table, entity_column,
    value_expr, agg, window_column, window_mode
) VALUES (
    'synthetic_agreement_exposure',
    'v3.0',
    'numerator',
    'platform.bank_loan_account',
    'agreement_id',
    'amount',
    'sum',
    'origination_date',
    'instant'
)
ON CONFLICT (metric_id, definition_version, role) DO NOTHING;
