-- V39: persist the 79 explicit/name_match dictionary bindings as data, not as a
-- runtime side effect. Previously these bindings only appeared after
-- POST /catalog/dictionaries/refresh, so a database that never ran refresh kept
-- the older 36 bindings (26 explicit + 10 name_match) while docs claimed 79.
--
-- Scope: 28 fact tables, 375 columns. 79 bound = 69 explicit + 10 name_match;
-- the two remaining mappable columns stay unbound on purpose (weak candidates
-- that require an operator decision):
--   bank_loan_account.period_start, cust_master.registration_date
--
-- Idempotent: INSERT ... ON CONFLICT DO NOTHING only fills missing rows; the
-- UPDATE touches a row only when its binding actually differs and never
-- overwrites binding_method = 'manual' (operator decisions are authoritative).
-- Every IRI below is typed as ObjectProperty/DatatypeProperty/AnnotationProperty
-- in the published T-Box (ont-11f92ebb3326); none is invented here.
--
-- Numbers after this migration in an environment that already has the 375-row
-- dictionary snapshot: 375 rows / 92 pre-existing pg_description comments /
-- 81 mappable / 79 bound.

INSERT INTO platform.data_dictionary
  (catalog_name, schema_name, table_name, column_name, data_type,
   is_nullable, comment, source_kind, property_iri, binding_method,
   confidence, binding_note)
SELECT 'platform', 'platform', v.table_name, v.column_name,
       c.data_type, (upper(c.is_nullable) = 'YES'), d.description, 'pg',
       v.property_iri, v.binding_method, v.confidence, v.binding_note
  FROM (VALUES
        ('bank_collection_case', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('bank_collection_case', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('bank_collection_case', 'status_as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：状态/指标截至日 status_as_of 即 observationDate'),
        ('bank_collection_recovery', 'recovery_date', 'https://w3id.org/fsldm/event#eventTimestamp', 'explicit', 0.800, '显式绑定：催收回款发生日 eventTimestamp（语义近似）'),
        ('bank_concentration_stat', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('bank_credit_application', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('bank_credit_application', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('bank_credit_facility', 'agreement_id', 'https://w3id.org/fsldm/core#agreementId', 'name_match', 0.800, '名称归一化匹配：agreement_id ≈ agreementId'),
        ('bank_credit_facility', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('bank_credit_facility', 'effective_from', 'https://w3id.org/fsldm/core#validFrom', 'explicit', 0.900, '显式绑定：额度生效起始时间 validFrom（语义近似）'),
        ('bank_credit_facility', 'effective_to', 'https://w3id.org/fsldm/core#validUntil', 'explicit', 0.900, '显式绑定：额度生效结束时间 validUntil（语义近似）'),
        ('bank_credit_facility', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('bank_credit_facility', 'status_as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：状态/指标截至日 status_as_of 即 observationDate'),
        ('bank_deposit_account', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('bank_deposit_account', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('bank_deposit_account', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('bank_disposal_event', 'asset_id', 'https://w3id.org/fsldm/core#assetId', 'explicit', 1.000, '显式绑定：处置事件指向的资产 assetId'),
        ('bank_disposal_event', 'completion_date', 'https://w3id.org/fsldm/event#eventTimestamp', 'explicit', 0.800, '显式绑定：处置完成日 eventTimestamp（语义近似）'),
        ('bank_disposal_event', 'disposal_type', 'https://w3id.org/fsldm/event#eventSubtype', 'explicit', 0.800, '显式绑定：处置方式即事件子类型 eventSubtype（语义近似）'),
        ('bank_disposal_event', 'event_id', 'https://w3id.org/fsldm/core#eventId', 'name_match', 0.800, '名称归一化匹配：event_id ≈ eventId'),
        ('bank_disposal_event', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('bank_ews_signal', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('bank_ews_signal', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('bank_loan_account', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('bank_loan_account', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('bank_loan_account', 'disbursed_date', 'https://w3id.org/fsldm/core#originationDate', 'explicit', 1.000, '显式绑定：放款日即起息日 originationDate'),
        ('bank_loan_account', 'first_payment_due_date', 'https://w3id.org/fsldm/core#firstPaymentDate', 'explicit', 1.000, '显式绑定：首期应还款日 firstPaymentDate'),
        ('bank_loan_account', 'maturity_date', 'https://w3id.org/fsldm/core#maturityDate', 'name_match', 0.800, '名称归一化匹配：maturity_date ≈ maturityDate'),
        ('bank_loan_account', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('bank_loan_repayment', 'due_date', 'https://w3id.org/fsldm/core#dueDate', 'name_match', 0.800, '名称归一化匹配：due_date ≈ dueDate'),
        ('bank_loan_repayment', 'installment_no', 'https://w3id.org/fsldm/finance#lineNumber', 'explicit', 0.800, '显式绑定：期次序号即分录行号 lineNumber（语义近似）'),
        ('bank_loan_repayment', 'paid_date', 'https://w3id.org/fsldm/event#eventTimestamp', 'explicit', 0.800, '显式绑定：还款/缴费发生日即事件时间 eventTimestamp（语义近似）'),
        ('bank_loan_repayment', 'status_as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：状态/指标截至日 status_as_of 即 observationDate'),
        ('bank_npl_snapshot', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('bank_npl_snapshot', 'asset_id', 'https://w3id.org/fsldm/core#assetId', 'name_match', 0.800, '名称归一化匹配：asset_id ≈ assetId'),
        ('bank_npl_snapshot', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('bank_provision_snapshot', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('cust_aum_snapshot', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('cust_aum_snapshot', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('cust_behavior_snapshot', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('cust_behavior_snapshot', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('cust_campaign_touch', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('cust_cohort_stat', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('cust_complaint', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('cust_master', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('cust_master', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('cust_product_holding', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('cust_product_holding', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('cust_transaction', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('cust_transaction', 'txn_date', 'https://w3id.org/fsldm/event#eventTimestamp', 'explicit', 0.900, '显式绑定：交易发生日 eventTimestamp'),
        ('cust_transaction', 'txn_type', 'https://w3id.org/fsldm/event#eventType', 'explicit', 0.800, '显式绑定：交易类型即事件类型 eventType（语义近似）'),
        ('ins_claim_case', 'policy_no', 'https://w3id.org/fsldm/core#agreementId', 'explicit', 0.900, '显式绑定：保单号按协议编号 agreementId 登记（语义近似）'),
        ('ins_claim_case', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('ins_claim_reserve_snapshot', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('ins_claim_reserve_snapshot', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('ins_payment_record', 'due_date', 'https://w3id.org/fsldm/core#dueDate', 'name_match', 0.800, '名称归一化匹配：due_date ≈ dueDate'),
        ('ins_payment_record', 'installment_no', 'https://w3id.org/fsldm/finance#lineNumber', 'explicit', 0.800, '显式绑定：期次序号即分录行号 lineNumber（语义近似）'),
        ('ins_payment_record', 'paid_date', 'https://w3id.org/fsldm/event#eventTimestamp', 'explicit', 0.800, '显式绑定：还款/缴费发生日即事件时间 eventTimestamp（语义近似）'),
        ('ins_payment_record', 'policy_no', 'https://w3id.org/fsldm/core#agreementId', 'explicit', 0.900, '显式绑定：保单号按协议编号 agreementId 登记（语义近似）'),
        ('ins_payment_record', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('ins_payment_record', 'status_as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：状态/指标截至日 status_as_of 即 observationDate'),
        ('ins_persistence_stat', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('ins_policy', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('ins_policy', 'issue_date', 'https://w3id.org/fsldm/core#originationDate', 'explicit', 0.900, '显式绑定：保单签发日按起息日 originationDate 登记（语义近似）'),
        ('ins_policy', 'policy_no', 'https://w3id.org/fsldm/core#agreementId', 'explicit', 0.900, '显式绑定：保单号按协议编号 agreementId 登记（语义近似）'),
        ('ins_policy', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('ins_policy', 'status_as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：状态/指标截至日 status_as_of 即 observationDate'),
        ('ins_policy_event', 'event_date', 'https://w3id.org/fsldm/event#eventTimestamp', 'explicit', 0.900, '显式绑定：保单事件发生日 eventTimestamp'),
        ('ins_policy_event', 'event_id', 'https://w3id.org/fsldm/core#eventId', 'name_match', 0.800, '名称归一化匹配：event_id ≈ eventId'),
        ('ins_policy_event', 'event_type', 'https://w3id.org/fsldm/event#eventType', 'name_match', 0.800, '名称归一化匹配：event_type ≈ eventType'),
        ('ins_policy_event', 'policy_no', 'https://w3id.org/fsldm/core#agreementId', 'explicit', 0.900, '显式绑定：保单号按协议编号 agreementId 登记（语义近似）'),
        ('ins_underwriting_stat', 'period_end', 'https://w3id.org/fsldm/core#validUntil', 'explicit', 0.900, '显式绑定：统计期间终点 validUntil（语义近似）'),
        ('ins_underwriting_stat', 'period_start', 'https://w3id.org/fsldm/core#validFrom', 'explicit', 0.900, '显式绑定：统计期间起点 validFrom（语义近似）'),
        ('ins_underwriting_stat', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('loan_installment_plan', 'agreement_id', 'https://w3id.org/fsldm/core#agreementId', 'name_match', 0.800, '名称归一化匹配：agreement_id ≈ agreementId'),
        ('loan_installment_plan', 'due_date', 'https://w3id.org/fsldm/core#dueDate', 'name_match', 0.800, '名称归一化匹配：due_date ≈ dueDate'),
        ('loan_installment_plan', 'installment_no', 'https://w3id.org/fsldm/finance#lineNumber', 'explicit', 0.800, '显式绑定：期次序号即分录行号 lineNumber（语义近似）'),
        ('loan_installment_plan', 'paid_date', 'https://w3id.org/fsldm/event#eventTimestamp', 'explicit', 0.800, '显式绑定：还款/缴费发生日即事件时间 eventTimestamp（语义近似）'),
        ('loan_installment_plan', 'status_as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：状态/指标截至日 status_as_of 即 observationDate')
  ) AS v (table_name, column_name, property_iri, binding_method, confidence, binding_note)
  JOIN information_schema.columns c
       ON c.table_schema = 'platform'
      AND c.table_name = v.table_name
      AND c.column_name = v.column_name
  LEFT JOIN pg_catalog.pg_namespace n ON n.nspname = c.table_schema
  LEFT JOIN pg_catalog.pg_class cl
       ON cl.relname = c.table_name AND cl.relnamespace = n.oid
  LEFT JOIN pg_catalog.pg_attribute a
       ON a.attrelid = cl.oid AND a.attname = c.column_name AND a.attnum > 0
  LEFT JOIN pg_catalog.pg_description d
       ON d.objoid = a.attrelid
      AND d.classoid = 'pg_class'::regclass
      AND d.objsubid = a.attnum
ON CONFLICT (catalog_name, schema_name, table_name, column_name) DO NOTHING;

UPDATE platform.data_dictionary AS d
   SET property_iri = v.property_iri,
       binding_method = v.binding_method,
       confidence = v.confidence,
       binding_note = v.binding_note
  FROM (VALUES
        ('bank_collection_case', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('bank_collection_case', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('bank_collection_case', 'status_as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：状态/指标截至日 status_as_of 即 observationDate'),
        ('bank_collection_recovery', 'recovery_date', 'https://w3id.org/fsldm/event#eventTimestamp', 'explicit', 0.800, '显式绑定：催收回款发生日 eventTimestamp（语义近似）'),
        ('bank_concentration_stat', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('bank_credit_application', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('bank_credit_application', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('bank_credit_facility', 'agreement_id', 'https://w3id.org/fsldm/core#agreementId', 'name_match', 0.800, '名称归一化匹配：agreement_id ≈ agreementId'),
        ('bank_credit_facility', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('bank_credit_facility', 'effective_from', 'https://w3id.org/fsldm/core#validFrom', 'explicit', 0.900, '显式绑定：额度生效起始时间 validFrom（语义近似）'),
        ('bank_credit_facility', 'effective_to', 'https://w3id.org/fsldm/core#validUntil', 'explicit', 0.900, '显式绑定：额度生效结束时间 validUntil（语义近似）'),
        ('bank_credit_facility', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('bank_credit_facility', 'status_as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：状态/指标截至日 status_as_of 即 observationDate'),
        ('bank_deposit_account', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('bank_deposit_account', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('bank_deposit_account', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('bank_disposal_event', 'asset_id', 'https://w3id.org/fsldm/core#assetId', 'explicit', 1.000, '显式绑定：处置事件指向的资产 assetId'),
        ('bank_disposal_event', 'completion_date', 'https://w3id.org/fsldm/event#eventTimestamp', 'explicit', 0.800, '显式绑定：处置完成日 eventTimestamp（语义近似）'),
        ('bank_disposal_event', 'disposal_type', 'https://w3id.org/fsldm/event#eventSubtype', 'explicit', 0.800, '显式绑定：处置方式即事件子类型 eventSubtype（语义近似）'),
        ('bank_disposal_event', 'event_id', 'https://w3id.org/fsldm/core#eventId', 'name_match', 0.800, '名称归一化匹配：event_id ≈ eventId'),
        ('bank_disposal_event', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('bank_ews_signal', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('bank_ews_signal', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('bank_loan_account', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('bank_loan_account', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('bank_loan_account', 'disbursed_date', 'https://w3id.org/fsldm/core#originationDate', 'explicit', 1.000, '显式绑定：放款日即起息日 originationDate'),
        ('bank_loan_account', 'first_payment_due_date', 'https://w3id.org/fsldm/core#firstPaymentDate', 'explicit', 1.000, '显式绑定：首期应还款日 firstPaymentDate'),
        ('bank_loan_account', 'maturity_date', 'https://w3id.org/fsldm/core#maturityDate', 'name_match', 0.800, '名称归一化匹配：maturity_date ≈ maturityDate'),
        ('bank_loan_account', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('bank_loan_repayment', 'due_date', 'https://w3id.org/fsldm/core#dueDate', 'name_match', 0.800, '名称归一化匹配：due_date ≈ dueDate'),
        ('bank_loan_repayment', 'installment_no', 'https://w3id.org/fsldm/finance#lineNumber', 'explicit', 0.800, '显式绑定：期次序号即分录行号 lineNumber（语义近似）'),
        ('bank_loan_repayment', 'paid_date', 'https://w3id.org/fsldm/event#eventTimestamp', 'explicit', 0.800, '显式绑定：还款/缴费发生日即事件时间 eventTimestamp（语义近似）'),
        ('bank_loan_repayment', 'status_as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：状态/指标截至日 status_as_of 即 observationDate'),
        ('bank_npl_snapshot', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('bank_npl_snapshot', 'asset_id', 'https://w3id.org/fsldm/core#assetId', 'name_match', 0.800, '名称归一化匹配：asset_id ≈ assetId'),
        ('bank_npl_snapshot', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('bank_provision_snapshot', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('cust_aum_snapshot', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('cust_aum_snapshot', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('cust_behavior_snapshot', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('cust_behavior_snapshot', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('cust_campaign_touch', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('cust_cohort_stat', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('cust_complaint', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('cust_master', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('cust_master', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('cust_product_holding', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('cust_product_holding', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('cust_transaction', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('cust_transaction', 'txn_date', 'https://w3id.org/fsldm/event#eventTimestamp', 'explicit', 0.900, '显式绑定：交易发生日 eventTimestamp'),
        ('cust_transaction', 'txn_type', 'https://w3id.org/fsldm/event#eventType', 'explicit', 0.800, '显式绑定：交易类型即事件类型 eventType（语义近似）'),
        ('ins_claim_case', 'policy_no', 'https://w3id.org/fsldm/core#agreementId', 'explicit', 0.900, '显式绑定：保单号按协议编号 agreementId 登记（语义近似）'),
        ('ins_claim_case', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('ins_claim_reserve_snapshot', 'as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：快照观察时点 as_of 即 observationDate'),
        ('ins_claim_reserve_snapshot', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('ins_payment_record', 'due_date', 'https://w3id.org/fsldm/core#dueDate', 'name_match', 0.800, '名称归一化匹配：due_date ≈ dueDate'),
        ('ins_payment_record', 'installment_no', 'https://w3id.org/fsldm/finance#lineNumber', 'explicit', 0.800, '显式绑定：期次序号即分录行号 lineNumber（语义近似）'),
        ('ins_payment_record', 'paid_date', 'https://w3id.org/fsldm/event#eventTimestamp', 'explicit', 0.800, '显式绑定：还款/缴费发生日即事件时间 eventTimestamp（语义近似）'),
        ('ins_payment_record', 'policy_no', 'https://w3id.org/fsldm/core#agreementId', 'explicit', 0.900, '显式绑定：保单号按协议编号 agreementId 登记（语义近似）'),
        ('ins_payment_record', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('ins_payment_record', 'status_as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：状态/指标截至日 status_as_of 即 observationDate'),
        ('ins_persistence_stat', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('ins_policy', 'customer_no', 'https://w3id.org/fsldm/core#partyId', 'explicit', 1.000, '显式绑定：客户号即当事人编号 partyId'),
        ('ins_policy', 'issue_date', 'https://w3id.org/fsldm/core#originationDate', 'explicit', 0.900, '显式绑定：保单签发日按起息日 originationDate 登记（语义近似）'),
        ('ins_policy', 'policy_no', 'https://w3id.org/fsldm/core#agreementId', 'explicit', 0.900, '显式绑定：保单号按协议编号 agreementId 登记（语义近似）'),
        ('ins_policy', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('ins_policy', 'status_as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：状态/指标截至日 status_as_of 即 observationDate'),
        ('ins_policy_event', 'event_date', 'https://w3id.org/fsldm/event#eventTimestamp', 'explicit', 0.900, '显式绑定：保单事件发生日 eventTimestamp'),
        ('ins_policy_event', 'event_id', 'https://w3id.org/fsldm/core#eventId', 'name_match', 0.800, '名称归一化匹配：event_id ≈ eventId'),
        ('ins_policy_event', 'event_type', 'https://w3id.org/fsldm/event#eventType', 'name_match', 0.800, '名称归一化匹配：event_type ≈ eventType'),
        ('ins_policy_event', 'policy_no', 'https://w3id.org/fsldm/core#agreementId', 'explicit', 0.900, '显式绑定：保单号按协议编号 agreementId 登记（语义近似）'),
        ('ins_underwriting_stat', 'period_end', 'https://w3id.org/fsldm/core#validUntil', 'explicit', 0.900, '显式绑定：统计期间终点 validUntil（语义近似）'),
        ('ins_underwriting_stat', 'period_start', 'https://w3id.org/fsldm/core#validFrom', 'explicit', 0.900, '显式绑定：统计期间起点 validFrom（语义近似）'),
        ('ins_underwriting_stat', 'product', 'https://w3id.org/fsldm/core#productId', 'explicit', 0.800, '显式绑定：产品代码即产品编号 productId（语义近似）'),
        ('loan_installment_plan', 'agreement_id', 'https://w3id.org/fsldm/core#agreementId', 'name_match', 0.800, '名称归一化匹配：agreement_id ≈ agreementId'),
        ('loan_installment_plan', 'due_date', 'https://w3id.org/fsldm/core#dueDate', 'name_match', 0.800, '名称归一化匹配：due_date ≈ dueDate'),
        ('loan_installment_plan', 'installment_no', 'https://w3id.org/fsldm/finance#lineNumber', 'explicit', 0.800, '显式绑定：期次序号即分录行号 lineNumber（语义近似）'),
        ('loan_installment_plan', 'paid_date', 'https://w3id.org/fsldm/event#eventTimestamp', 'explicit', 0.800, '显式绑定：还款/缴费发生日即事件时间 eventTimestamp（语义近似）'),
        ('loan_installment_plan', 'status_as_of', 'https://w3id.org/fsldm/core#observationDate', 'explicit', 0.900, '显式绑定：状态/指标截至日 status_as_of 即 observationDate')
  ) AS v (table_name, column_name, property_iri, binding_method, confidence, binding_note)
 WHERE d.catalog_name = 'platform'
   AND d.schema_name = 'platform'
   AND d.table_name = v.table_name
   AND d.column_name = v.column_name
   AND d.binding_method <> 'manual'
   AND (d.property_iri IS DISTINCT FROM v.property_iri
        OR d.binding_method IS DISTINCT FROM v.binding_method
        OR d.confidence IS DISTINCT FROM v.confidence
        OR d.binding_note IS DISTINCT FROM v.binding_note);
