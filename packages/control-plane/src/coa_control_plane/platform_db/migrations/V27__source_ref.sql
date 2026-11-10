-- V27: B-01 value-level provenance (source_ref).
--
-- Two small tables, no duplicated rendered refs:
--   * fact_source_key  -- the natural key of every business fact table. A
--     fact-row ref must name exactly these columns, so an arbitrary table or
--     an arbitrary column cannot be addressed (E_SOURCE_REF_FORBIDDEN).
--   * source_ref_registry -- every ref an API response has handed out. It is
--     audit storage only; resolution always re-reads the live table, which is
--     how a ref to a deleted row becomes E_SOURCE_REF_STALE instead of being
--     indistinguishable from a never-existing ref.
--
-- The metric_observation and document_chunk natural keys already exist
-- (metric_observation_window_key and document_chunk(document_id, seq)), so no
-- column is added there: a rendered ref column would duplicate those keys and
-- start drifting the day one side is renamed.

CREATE TABLE IF NOT EXISTS platform.fact_source_key (
  table_name  text PRIMARY KEY,
  key_columns text[] NOT NULL,
  grain_note  text,
  added_at    timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE platform.fact_source_key IS
  'B-01: natural key of each fact table; fact-row source_refs must match it';

INSERT INTO platform.fact_source_key (table_name, key_columns, grain_note) VALUES
  ('platform.bank_collection_case',
   ARRAY['case_id','status_as_of','data_source'], 'collection case snapshot'),
  ('platform.bank_collection_recovery',
   ARRAY['case_id','recovery_date','recovery_channel','data_source'], 'recovery event'),
  ('platform.bank_concentration_stat',
   ARRAY['institution','as_of','data_source'], 'institution concentration snapshot'),
  ('platform.bank_credit_application',
   ARRAY['application_id','data_source'], 'credit application'),
  ('platform.bank_credit_facility',
   ARRAY['agreement_id','status_as_of','data_source'], 'facility snapshot'),
  ('platform.bank_deposit_account',
   ARRAY['deposit_id','as_of','data_source'], 'deposit account snapshot'),
  ('platform.bank_disposal_event',
   ARRAY['event_id','data_source'], 'disposal event'),
  ('platform.bank_ews_signal',
   ARRAY['customer_no','as_of','data_source'], 'early-warning signal snapshot'),
  ('platform.bank_loan_account',
   ARRAY['account_id','as_of','data_source'], 'loan account snapshot'),
  ('platform.bank_loan_repayment',
   ARRAY['account_id','installment_no','status_as_of','data_source'], 'repayment status'),
  ('platform.bank_npl_snapshot',
   ARRAY['asset_id','as_of','data_source'], 'NPL asset snapshot'),
  ('platform.bank_provision_snapshot',
   ARRAY['institution','as_of','data_source'], 'provision snapshot'),
  ('platform.cust_aum_snapshot',
   ARRAY['customer_no','product_type','as_of','data_source'], 'customer AUM snapshot'),
  ('platform.cust_behavior_snapshot',
   ARRAY['customer_no','as_of','data_source'], 'customer behavior snapshot'),
  ('platform.cust_campaign_touch',
   ARRAY['touch_id','data_source'], 'campaign touch'),
  ('platform.cust_cohort_stat',
   ARRAY['cohort_key','as_of','data_source'], 'cohort statistic'),
  ('platform.cust_complaint',
   ARRAY['ticket_id','data_source'], 'complaint ticket'),
  ('platform.cust_master',
   ARRAY['customer_no','as_of','data_source'], 'customer master snapshot'),
  ('platform.cust_product_holding',
   ARRAY['holding_id','as_of','data_source'], 'product holding snapshot'),
  ('platform.cust_transaction',
   ARRAY['txn_id','data_source'], 'transaction event'),
  ('platform.ins_claim_case',
   ARRAY['claim_no','data_source'], 'claim case'),
  ('platform.ins_claim_reserve_snapshot',
   ARRAY['claim_no','as_of','data_source'], 'claim reserve snapshot'),
  ('platform.ins_payment_record',
   ARRAY['policy_no','installment_no','status_as_of','data_source'], 'installment payment status'),
  ('platform.ins_persistence_stat',
   ARRAY['institution','product','channel','cohort_period','valuation_basis','renewal_year','data_source'], 'persistency statistic'),
  ('platform.ins_policy',
   ARRAY['policy_no','status_as_of','data_source'], 'policy snapshot'),
  ('platform.ins_policy_event',
   ARRAY['policy_no','event_type','event_date','data_source'], 'policy event'),
  ('platform.ins_underwriting_stat',
   ARRAY['institution','product','channel','business_line','period_start','period_end','data_source'], 'underwriting statistic'),
  ('platform.loan_installment_plan',
   ARRAY['agreement_id','installment_no','status_as_of','data_source'], 'installment plan')
ON CONFLICT (table_name) DO NOTHING;

CREATE TABLE IF NOT EXISTS platform.source_ref_registry (
  source_ref    text PRIMARY KEY,
  ref_kind      text NOT NULL,
  target_table  text NOT NULL,
  locator       jsonb NOT NULL DEFAULT '{}'::jsonb,
  issued_at     timestamptz NOT NULL DEFAULT now(),
  resolve_count bigint NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS source_ref_registry_target_idx
  ON platform.source_ref_registry (target_table);

COMMENT ON TABLE platform.source_ref_registry IS
  'B-01: refs issued by API responses; used only to tell stale refs from unknown refs';
