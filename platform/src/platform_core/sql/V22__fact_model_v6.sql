-- V22: fact model v6 (bank / insurance / customer) + 7 newly computable metrics
-- + machine-readable EWS rule specs for FIN-BANK-034.
--
-- Design contract (same as V20): every fact table is independent and carries
-- (data_source, fixture) provenance. The calculator never reads these tables;
-- the projector aggregates them through platform.metric_fact_* functions named
-- by metric_definition.fact_function and upserts one observation per entity.
--
-- Re-entrant: CREATE TABLE IF NOT EXISTS, ALTER ADD COLUMN IF NOT EXISTS,
-- CREATE INDEX IF NOT EXISTS, CREATE OR REPLACE FUNCTION, plain UPDATE seeds.
-- No business values live here; only schema and definition bindings.

-- =====================================================================
-- 1. BANK
-- =====================================================================

CREATE TABLE IF NOT EXISTS platform.bank_loan_account (
  account_id      text NOT NULL,
  customer_no     text NOT NULL,
  product         text NOT NULL,
  industry        text,
  region          text,
  guarantee_type  text,
  risk_class      text NOT NULL
    CHECK (risk_class IN ('normal', 'special', 'substandard', 'doubtful', 'loss')),
  principal_balance numeric NOT NULL DEFAULT 0 CHECK (principal_balance >= 0),
  disbursed_date  date,
  maturity_date   date,
  account_status  text NOT NULL
    CHECK (account_status IN ('active', 'closed', 'written_off', 'transferred')),
  as_of           date NOT NULL,
  institution     text,
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT bank_loan_account_key UNIQUE (account_id, as_of, data_source)
);
COMMENT ON TABLE platform.bank_loan_account IS
  '贷款账户（时点快照事实）：一行=一个账户在一个观察日的余额/五级分类/担保方式；'
  '来源字段映射：LOAN ACCOUNT(账户号/客户号/险种/行业/区域/担保方式/五级分类/'
  '本金余额/放款日/到期日/状态/机构)。业务时间列 as_of。';

-- 既有 ins_payment_record 的期次模型在本表复用；新增字段是 v5 判定缺口
-- （宽限期、期交/趸交、保单年度、复效），全部可空，不破坏既有行。
CREATE TABLE IF NOT EXISTS platform.bank_loan_repayment (
  repayment_id    bigserial PRIMARY KEY,
  account_id      text NOT NULL,
  installment_no  integer NOT NULL CHECK (installment_no > 0),
  due_date        date NOT NULL,
  paid_date       date,
  due_amount      numeric NOT NULL CHECK (due_amount >= 0),
  paid_amount     numeric NOT NULL DEFAULT 0 CHECK (paid_amount >= 0),
  principal_paid  numeric NOT NULL DEFAULT 0 CHECK (principal_paid >= 0),
  interest_paid   numeric NOT NULL DEFAULT 0 CHECK (interest_paid >= 0),
  penalty_paid    numeric NOT NULL DEFAULT 0 CHECK (penalty_paid >= 0),
  overdue_days    integer CHECK (overdue_days IS NULL OR overdue_days >= 0),
  is_partial      boolean NOT NULL DEFAULT false,
  status_as_of    date NOT NULL,
  institution     text,
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT bank_loan_repayment_key
    UNIQUE (account_id, installment_no, status_as_of, data_source)
);
COMMENT ON TABLE platform.bank_loan_repayment IS
  '还款计划与实还流水（期次级）：一行=一笔账户一个期数在一个状态观察日的应还/实还/'
  '本金实还/逾期天数/部分还款标识；用 status_as_of 取时点，用 due_date 落窗。';

CREATE TABLE IF NOT EXISTS platform.bank_credit_facility (
  agreement_id    text NOT NULL,
  customer_no     text NOT NULL,
  product         text,
  institution     text,
  approved_limit  numeric NOT NULL CHECK (approved_limit >= 0),
  drawn_principal numeric NOT NULL DEFAULT 0 CHECK (drawn_principal >= 0),
  currency        text NOT NULL DEFAULT 'CNY',
  fx_rate         numeric NOT NULL DEFAULT 1 CHECK (fx_rate > 0),
  limit_type      text NOT NULL DEFAULT 'revolving'
    CHECK (limit_type IN ('revolving', 'term', 'overdraft')),
  facility_status text NOT NULL
    CHECK (facility_status IN ('active', 'frozen', 'expired', 'cancelled')),
  effective_from  date,
  effective_to    date,
  internal_flag   boolean NOT NULL DEFAULT false,
  test_flag       boolean NOT NULL DEFAULT false,
  status_as_of    date NOT NULL,
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT bank_credit_facility_key
    UNIQUE (agreement_id, status_as_of, data_source)
);
COMMENT ON TABLE platform.bank_credit_facility IS
  '授信合同/额度协议（时点快照）：一行=一个额度协议在一个观察日的批复额度/已用额度/'
  '状态/期限/币种/汇率；额度使用率分母=有效额度合计，分子=提款未还本金合计。';

CREATE TABLE IF NOT EXISTS platform.bank_credit_application (
  application_id  text NOT NULL,
  customer_no     text NOT NULL,
  product         text NOT NULL,
  channel         text,
  institution     text,
  accept_date     date NOT NULL,
  decision_date   date,
  decision_status text NOT NULL
    CHECK (decision_status IN ('approved', 'rejected', 'pending', 'withdrawn', 'voided')),
  requested_amount numeric NOT NULL DEFAULT 0 CHECK (requested_amount >= 0),
  duplicate_group_id text,
  first_flag      boolean NOT NULL DEFAULT true,
  test_flag       boolean NOT NULL DEFAULT false,
  internal_flag   boolean NOT NULL DEFAULT false,
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT bank_credit_application_key UNIQUE (application_id, data_source)
);
COMMENT ON TABLE platform.bank_credit_application IS
  '申请受理与审批（事件事实）：一行=一笔申请；业务时间=accept_date，审批时点='
  'decision_date；通过率分母=统计期首次受理笔数（重复组只算首笔，剔除撤销/'
  '作废/测试/内部），分子=期末+30 天内结论为 approved 的笔数。';

CREATE TABLE IF NOT EXISTS platform.bank_collection_case (
  case_id         text NOT NULL,
  account_id      text NOT NULL,
  customer_no     text NOT NULL,
  product         text,
  institution     text,
  outstanding_principal numeric NOT NULL CHECK (outstanding_principal >= 0),
  case_status     text NOT NULL
    CHECK (case_status IN ('collecting', 'written_off', 'transferred', 'restructured', 'closed')),
  status_as_of    date NOT NULL,
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT bank_collection_case_key UNIQUE (case_id, status_as_of, data_source)
);
COMMENT ON TABLE platform.bank_collection_case IS
  '催收案件（时点快照）：一行=一个账户在一个观察日是否在催/已核销/已转出/已重组；'
  '催收回收率分母=期初 status=collecting 且逾期本金>0 的账户余额。';

CREATE TABLE IF NOT EXISTS platform.bank_collection_recovery (
  recovery_id     bigserial PRIMARY KEY,
  case_id         text NOT NULL,
  recovery_date   date NOT NULL,
  principal_recovered numeric NOT NULL DEFAULT 0 CHECK (principal_recovered >= 0),
  interest_recovered  numeric NOT NULL DEFAULT 0 CHECK (interest_recovered >= 0),
  fee_recovered   numeric NOT NULL DEFAULT 0 CHECK (fee_recovered >= 0),
  recovery_channel text,
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT bank_collection_recovery_key
    UNIQUE (case_id, recovery_date, recovery_channel, data_source)
);
COMMENT ON TABLE platform.bank_collection_recovery IS
  '催收回收流水（事件事实）：一行=一个案件一次回收；本金/利息/费用拆分留存，'
  '回收率分子只取 principal_recovered（现金口径）。';

CREATE TABLE IF NOT EXISTS platform.bank_npl_snapshot (
  asset_id        text NOT NULL,
  institution     text,
  product         text,
  risk_class      text NOT NULL
    CHECK (risk_class IN ('substandard', 'doubtful', 'loss')),
  npl_balance     numeric NOT NULL CHECK (npl_balance >= 0),
  as_of           date NOT NULL,
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT bank_npl_snapshot_key UNIQUE (asset_id, as_of, data_source)
);
COMMENT ON TABLE platform.bank_npl_snapshot IS
  '不良资产时点快照：一行=一个资产在一个观察日的次级/可疑/损失余额；'
  '处置率分母=期初不良余额合计（按资产去重）。';

CREATE TABLE IF NOT EXISTS platform.bank_disposal_event (
  event_id        text NOT NULL,
  asset_id        text NOT NULL,
  institution     text,
  product         text,
  disposal_type   text NOT NULL
    CHECK (disposal_type IN ('cash', 'transfer', 'asset_swap', 'judicial', 'write_off')),
  completion_date date NOT NULL,
  gross_amount    numeric NOT NULL CHECK (gross_amount >= 0),
  recovery_cash   numeric NOT NULL DEFAULT 0 CHECK (recovery_cash >= 0),
  recovery_noncash_fv numeric NOT NULL DEFAULT 0 CHECK (recovery_noncash_fv >= 0),
  disposal_fee    numeric NOT NULL DEFAULT 0 CHECK (disposal_fee >= 0),
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT bank_disposal_event_key UNIQUE (event_id, data_source)
);
COMMENT ON TABLE platform.bank_disposal_event IS
  '不良处置事件：一行=一个资产一次完成的处置；disposal_type 区分现金清收/转让/'
  '以物抵债/司法裁定/纯核销；回收率分子=现金+非现金公允价值-处置费用，纯核销不进分母。';

CREATE TABLE IF NOT EXISTS platform.bank_deposit_account (
  deposit_id      text NOT NULL,
  customer_no     text NOT NULL,
  product         text NOT NULL,
  balance         numeric NOT NULL DEFAULT 0 CHECK (balance >= 0),
  account_status  text NOT NULL CHECK (account_status IN ('active', 'closed')),
  as_of           date NOT NULL,
  institution     text,
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT bank_deposit_account_key UNIQUE (deposit_id, as_of, data_source)
);
COMMENT ON TABLE platform.bank_deposit_account IS
  '存款账户（时点快照）：一行=一个存款账户在一个观察日的余额；用于 AUM/'
  '产品持有数等客户经营指标。';

CREATE TABLE IF NOT EXISTS platform.bank_ews_signal (
  customer_no     text NOT NULL,
  as_of           date NOT NULL,
  dpd             integer,
  dpd_start       integer,
  dpd_end         integer,
  risk_class_prev text,
  risk_class_curr text,
  rating_notch_prev integer,
  rating_notch_curr integer,
  drawn_principal numeric,
  approved_limit  numeric,
  monthly_inflow  numeric,
  inflow_12m_avg  numeric,
  consecutive_partial_count integer,
  paid_amount     numeric,
  due_amount      numeric,
  collateral_ratio_prev numeric,
  collateral_ratio_curr numeric,
  guarantee_status text,
  other_facility_dpd_90plus boolean NOT NULL DEFAULT false,
  default_flag    boolean NOT NULL DEFAULT false,
  institution     text,
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT bank_ews_signal_key UNIQUE (customer_no, as_of, data_source)
);
COMMENT ON TABLE platform.bank_ews_signal IS
  'EWS 信号快照：一行=一个客户在一个观测日的一期信号；同时保存当前值与上一期/'
  '12 个月均值等比较值，规则执行器只读这一张表即可判定，不需要在 Python 里再推算历史。';

-- =====================================================================
-- 2. INSURANCE
-- =====================================================================

CREATE TABLE IF NOT EXISTS platform.ins_policy (
  policy_no       text NOT NULL,
  product         text NOT NULL,
  channel         text,
  institution     text,
  customer_no     text,
  issue_date      date NOT NULL,
  policy_year     integer NOT NULL DEFAULT 1 CHECK (policy_year >= 1),
  premium_type    text NOT NULL CHECK (premium_type IN ('single', 'regular')),
  premium_amount  numeric NOT NULL CHECK (premium_amount >= 0),
  first_year_premium numeric,
  is_investment_linked boolean NOT NULL DEFAULT false,
  reversal_amount numeric NOT NULL DEFAULT 0 CHECK (reversal_amount >= 0),
  policy_status   text NOT NULL
    CHECK (policy_status IN ('in_force', 'lapsed', 'surrendered', 'cancelled')),
  status_as_of    date NOT NULL,
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ins_policy_key UNIQUE (policy_no, status_as_of, data_source)
);
COMMENT ON TABLE platform.ins_policy IS
  '保单主档（时点快照）：一行=一张保单在一个观察日的险种/渠道/承保日/保单年度/'
  '期交趸交/保费/投资款标识/批退冲减/状态；原保险保费收入按 issue_date 落窗，'
  '剔除投连独立账户，批退冲减。';

CREATE TABLE IF NOT EXISTS platform.ins_claim_case (
  claim_no        text NOT NULL,
  policy_no       text NOT NULL,
  product         text,
  institution     text,
  report_date     date NOT NULL,
  decision_date   date,
  claim_amount    numeric NOT NULL DEFAULT 0 CHECK (claim_amount >= 0),
  paid_amount     numeric NOT NULL DEFAULT 0 CHECK (paid_amount >= 0),
  claim_status    text NOT NULL
    CHECK (claim_status IN ('reported', 'approved', 'paid', 'rejected', 'withdrawn')),
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ins_claim_case_key UNIQUE (claim_no, data_source)
);
COMMENT ON TABLE platform.ins_claim_case IS
  '理赔案件（事件事实）：一行=一个赔案；业务时间=report_date，已决时点=decision_date；'
  '用于赔付率、案均金额、报案率类指标。';

CREATE TABLE IF NOT EXISTS platform.ins_policy_event (
  event_id        text NOT NULL,
  policy_no       text NOT NULL,
  event_type      text NOT NULL
    CHECK (event_type IN ('lapse', 'surrender', 'reinstatement', 'termination')),
  event_date      date NOT NULL,
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ins_policy_event_key
    UNIQUE (policy_no, event_type, event_date, data_source)
);
COMMENT ON TABLE platform.ins_policy_event IS
  '保单事件（失效/退保/复效/终止）：一行=一张保单一次状态事件；'
  '继续率与退保率类指标的分子窗口与状态序列来源。';

ALTER TABLE platform.ins_payment_record
  ADD COLUMN IF NOT EXISTS grace_end_date date;
ALTER TABLE platform.ins_payment_record
  ADD COLUMN IF NOT EXISTS payment_type text;
ALTER TABLE platform.ins_payment_record
  ADD COLUMN IF NOT EXISTS policy_year integer;
ALTER TABLE platform.ins_payment_record
  ADD COLUMN IF NOT EXISTS reinstatement_flag boolean NOT NULL DEFAULT false;
COMMENT ON COLUMN platform.ins_payment_record.grace_end_date IS
  '第 1/2 个保单年度结束后的缴费宽限期截止日（v5 判定缺口，宽限期口径用）。';
COMMENT ON COLUMN platform.ins_payment_record.payment_type IS
  'payment_type: current 当期续期 / reinstatement 复效补缴 / arrears 以前年度欠费补缴。';

-- =====================================================================
-- 3. CUSTOMER
-- =====================================================================

CREATE TABLE IF NOT EXISTS platform.cust_master (
  customer_no     text NOT NULL,
  registration_date date NOT NULL,
  channel         text,
  segment         text,
  institution     text,
  customer_status text NOT NULL CHECK (customer_status IN ('active', 'closed')),
  as_of           date NOT NULL,
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT cust_master_key UNIQUE (customer_no, as_of, data_source)
);
COMMENT ON TABLE platform.cust_master IS
  '客户主档（时点快照）：一行=一个客户在一个观察日的获客日/渠道/分层/状态；'
  '来源字段映射：PARTY(客户号/注册时间/渠道/分层/销户状态)。';

CREATE TABLE IF NOT EXISTS platform.cust_transaction (
  txn_id          text NOT NULL,
  customer_no     text NOT NULL,
  txn_date        date NOT NULL,
  txn_type        text NOT NULL CHECK (txn_type IN ('purchase', 'refund', 'transfer')),
  amount          numeric NOT NULL CHECK (amount >= 0),
  product_category text,
  channel         text,
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT cust_transaction_key UNIQUE (txn_id, data_source)
);
COMMENT ON TABLE platform.cust_transaction IS
  '客户交易事件：一行=一笔交易；业务时间=txn_date；退款/取消单独类型，'
  'RFM/留存/活跃判定需剔除 refund。';

CREATE TABLE IF NOT EXISTS platform.cust_campaign_touch (
  touch_id        text NOT NULL,
  customer_no     text NOT NULL,
  campaign_id     text NOT NULL,
  touch_date      date NOT NULL,
  channel         text,
  response_flag   boolean NOT NULL DEFAULT false,
  response_date   date,
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT cust_campaign_touch_key UNIQUE (touch_id, data_source)
);
COMMENT ON TABLE platform.cust_campaign_touch IS
  '营销触达与响应：一行=一次触达；response_flag/response_date 记录客户响应；'
  '用于触达响应率与活动归因。';

CREATE TABLE IF NOT EXISTS platform.cust_complaint (
  ticket_id       text NOT NULL,
  customer_no     text NOT NULL,
  opened_date     date NOT NULL,
  closed_date     date,
  category        text,
  ticket_status   text NOT NULL
    CHECK (ticket_status IN ('open', 'closed', 'escalated')),
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT cust_complaint_key UNIQUE (ticket_id, data_source)
);
COMMENT ON TABLE platform.cust_complaint IS
  '投诉工单：一行=一个投诉；业务时间=opened_date；用于投诉率/关闭时效类指标。';

CREATE TABLE IF NOT EXISTS platform.cust_product_holding (
  holding_id      text NOT NULL,
  customer_no     text NOT NULL,
  product_category text NOT NULL
    CHECK (product_category IN ('deposit', 'loan', 'insurance', 'wealth', 'card')),
  holding_status  text NOT NULL CHECK (holding_status IN ('active', 'closed')),
  as_of           date NOT NULL,
  institution     text,
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT cust_product_holding_key UNIQUE (holding_id, as_of, data_source)
);
COMMENT ON TABLE platform.cust_product_holding IS
  '客户产品持有（时点快照）：一行=一个客户在一个观察日持有一类产品；'
  '产品持有数/人均产品数的分子来源，按客户号+产品大类去重。';

-- =====================================================================
-- 4. Projection functions (window -> observation rows)
-- =====================================================================

-- FIN-BANK-031: period cohort by accept_date; approvals observed to end+30d.
CREATE OR REPLACE FUNCTION platform.metric_fact_fin_bank_031(
  p_start date, p_end date, p_data_source text
) RETURNS TABLE (
  entity_key text, institution text, product text,
  window_start date, window_end date,
  numerator numeric, denominator numeric, data_source text, fixture boolean
) LANGUAGE sql STABLE AS $$
  WITH first_accept AS (
    SELECT DISTINCT ON (COALESCE(a.duplicate_group_id, a.application_id))
           a.application_id, a.institution, a.decision_status, a.decision_date,
           a.data_source, a.fixture
      FROM platform.bank_credit_application a
     WHERE a.accept_date >= p_start AND a.accept_date <= p_end
       AND a.data_source = p_data_source
       AND a.first_flag
       AND NOT a.test_flag AND NOT a.internal_flag
       AND a.decision_status NOT IN ('withdrawn', 'voided')
     ORDER BY COALESCE(a.duplicate_group_id, a.application_id), a.accept_date, a.application_id
  )
  SELECT COALESCE(institution, 'ALL') AS entity_key,
         MIN(institution) AS institution, NULL::text AS product,
         p_start, p_end,
         COUNT(*) FILTER (WHERE decision_status = 'approved'
                            AND decision_date <= p_end + 30)::numeric AS numerator,
         COUNT(*)::numeric AS denominator,
         MIN(data_source) AS data_source, BOOL_OR(fixture) AS fixture
    FROM first_accept
   GROUP BY COALESCE(institution, 'ALL')
$$;

-- FIN-BANK-032: instant; effective facilities only, same as-of.
CREATE OR REPLACE FUNCTION platform.metric_fact_fin_bank_032(
  p_start date, p_end date, p_data_source text
) RETURNS TABLE (
  entity_key text, institution text, product text,
  window_start date, window_end date,
  numerator numeric, denominator numeric, data_source text, fixture boolean
) LANGUAGE sql STABLE AS $$
  SELECT COALESCE(f.institution, 'ALL') AS entity_key,
         MIN(f.institution) AS institution, NULL::text AS product,
         p_start, p_end,
         SUM(f.drawn_principal * f.fx_rate)::numeric AS numerator,
         SUM(f.approved_limit * f.fx_rate)::numeric AS denominator,
         MIN(f.data_source) AS data_source, BOOL_OR(f.fixture) AS fixture
    FROM platform.bank_credit_facility f
   WHERE f.status_as_of = p_start AND p_start = p_end
     AND f.facility_status = 'active'
     AND NOT f.internal_flag AND NOT f.test_flag
     AND f.data_source = p_data_source
   GROUP BY COALESCE(f.institution, 'ALL')
$$;

-- FIN-BANK-035: T0 cohort of collecting cases; cash principal recovered inside window.
CREATE OR REPLACE FUNCTION platform.metric_fact_fin_bank_035(
  p_start date, p_end date, p_data_source text
) RETURNS TABLE (
  entity_key text, institution text, product text,
  window_start date, window_end date,
  numerator numeric, denominator numeric, data_source text, fixture boolean
) LANGUAGE sql STABLE AS $$
  WITH cohort AS (
    SELECT c.case_id, c.institution, c.outstanding_principal, c.data_source, c.fixture
      FROM platform.bank_collection_case c
     WHERE c.status_as_of = p_start
       AND c.case_status = 'collecting'
       AND c.outstanding_principal > 0
       AND c.data_source = p_data_source
  )
  SELECT COALESCE(c.institution, 'ALL') AS entity_key,
         MIN(c.institution) AS institution, NULL::text AS product,
         p_start, p_end,
         COALESCE(SUM(r.principal_recovered), 0)::numeric AS numerator,
         SUM(c.outstanding_principal)::numeric AS denominator,
         MIN(c.data_source) AS data_source, BOOL_OR(c.fixture) AS fixture
    FROM cohort c
    LEFT JOIN platform.bank_collection_recovery r
      ON r.case_id = c.case_id
     AND r.recovery_date >= p_start AND r.recovery_date <= p_end
     AND r.data_source = p_data_source
   GROUP BY COALESCE(c.institution, 'ALL')
$$;

-- FIN-BANK-036-v1: disposed gross / opening NPL balance.
CREATE OR REPLACE FUNCTION platform.metric_fact_fin_bank_036_v1(
  p_start date, p_end date, p_data_source text
) RETURNS TABLE (
  entity_key text, institution text, product text,
  window_start date, window_end date,
  numerator numeric, denominator numeric, data_source text, fixture boolean
) LANGUAGE sql STABLE AS $$
  WITH opening AS (
    SELECT COALESCE(n.institution, 'ALL') AS grp,
           SUM(n.npl_balance)::numeric AS npl,
           MIN(n.data_source) AS data_source, BOOL_OR(n.fixture) AS fixture
      FROM platform.bank_npl_snapshot n
     WHERE n.as_of = p_start AND n.data_source = p_data_source
     GROUP BY COALESCE(n.institution, 'ALL')
  ), disposed AS (
    SELECT COALESCE(d.institution, 'ALL') AS grp,
           SUM(d.gross_amount)::numeric AS gross
      FROM platform.bank_disposal_event d
     WHERE d.completion_date >= p_start AND d.completion_date <= p_end
       AND d.data_source = p_data_source
     GROUP BY COALESCE(d.institution, 'ALL')
  )
  SELECT o.grp AS entity_key, NULLIF(o.grp, 'ALL') AS institution, NULL::text AS product,
         p_start, p_end,
         COALESCE(x.gross, 0)::numeric AS numerator,
         o.npl AS denominator,
         o.data_source, o.fixture
    FROM opening o LEFT JOIN disposed x ON x.grp = o.grp
$$;

-- FIN-BANK-036-v2: recovery proceeds / disposed gross with a recovery method.
CREATE OR REPLACE FUNCTION platform.metric_fact_fin_bank_036_v2(
  p_start date, p_end date, p_data_source text
) RETURNS TABLE (
  entity_key text, institution text, product text,
  window_start date, window_end date,
  numerator numeric, denominator numeric, data_source text, fixture boolean
) LANGUAGE sql STABLE AS $$
  SELECT COALESCE(d.institution, 'ALL') AS entity_key,
         MIN(d.institution) AS institution, NULL::text AS product,
         p_start, p_end,
         SUM(d.recovery_cash + d.recovery_noncash_fv - d.disposal_fee)::numeric AS numerator,
         SUM(d.gross_amount)::numeric AS denominator,
         MIN(d.data_source) AS data_source, BOOL_OR(d.fixture) AS fixture
    FROM platform.bank_disposal_event d
   WHERE d.completion_date >= p_start AND d.completion_date <= p_end
     AND d.disposal_type IN ('cash', 'transfer', 'asset_swap', 'judicial')
     AND d.data_source = p_data_source
   GROUP BY COALESCE(d.institution, 'ALL')
$$;

-- FIN-INS-001: additive premium (no ratio); investment-linked and reversals excluded.
CREATE OR REPLACE FUNCTION platform.metric_fact_fin_ins_001(
  p_start date, p_end date, p_data_source text
) RETURNS TABLE (
  entity_key text, institution text, product text,
  window_start date, window_end date,
  numerator numeric, denominator numeric, data_source text, fixture boolean
) LANGUAGE sql STABLE AS $$
  SELECT p.product AS entity_key,
         MIN(p.institution) AS institution, p.product,
         p_start, p_end,
         SUM(p.premium_amount - p.reversal_amount)::numeric AS numerator,
         NULL::numeric AS denominator,
         MIN(p.data_source) AS data_source, BOOL_OR(p.fixture) AS fixture
    FROM platform.ins_policy p
   WHERE p.issue_date >= p_start AND p.issue_date <= p_end
     AND NOT p.is_investment_linked
     AND p.data_source = p_data_source
   GROUP BY p.product
$$;

-- CUST-010: products per customer at an instant, by segment.
CREATE OR REPLACE FUNCTION platform.metric_fact_cust_010(
  p_start date, p_end date, p_data_source text
) RETURNS TABLE (
  entity_key text, institution text, product text,
  window_start date, window_end date,
  numerator numeric, denominator numeric, data_source text, fixture boolean
) LANGUAGE sql STABLE AS $$
  SELECT COALESCE(m.segment, 'ALL') AS entity_key,
         MIN(m.institution) AS institution, NULL::text AS product,
         p_start, p_end,
         COUNT(*)::numeric AS numerator,
         COUNT(DISTINCT m.customer_no)::numeric AS denominator,
         MIN(m.data_source) AS data_source, BOOL_OR(m.fixture) AS fixture
    FROM platform.cust_master m
    JOIN platform.cust_product_holding h
      ON h.customer_no = m.customer_no
     AND h.as_of = p_start
     AND h.holding_status = 'active'
     AND h.data_source = p_data_source
   WHERE m.as_of = p_start AND p_start = p_end
     AND m.customer_status = 'active'
     AND m.data_source = p_data_source
   GROUP BY COALESCE(m.segment, 'ALL')
$$;

-- =====================================================================
-- 5. Bind 7 definitions to projections (quartet unchanged elsewhere)
-- =====================================================================

UPDATE platform.metric_definition SET
  metric_kind = 'ratio', formula_expr = 'numerator / denominator * 100',
  numerator_agg = 'sum', denominator_agg = 'sum', window_kind = 'period',
  min_window_days = 1, grain = 'institution', unit = '%',
  fact_function = 'platform.metric_fact_fin_bank_031'
 WHERE metric_id = 'FIN-BANK-031';

UPDATE platform.metric_definition SET
  metric_kind = 'ratio', formula_expr = 'numerator / denominator * 100',
  numerator_agg = 'sum', denominator_agg = 'sum', window_kind = 'instant',
  min_window_days = 0, grain = 'institution', unit = '%',
  fact_function = 'platform.metric_fact_fin_bank_032'
 WHERE metric_id = 'FIN-BANK-032';

UPDATE platform.metric_definition SET
  metric_kind = 'ratio', formula_expr = 'numerator / denominator * 100',
  numerator_agg = 'sum', denominator_agg = 'sum', window_kind = 'period',
  min_window_days = 90, grain = 'institution', unit = '%',
  fact_function = 'platform.metric_fact_fin_bank_035'
 WHERE metric_id = 'FIN-BANK-035';

UPDATE platform.metric_definition SET
  metric_kind = 'ratio', formula_expr = 'numerator / denominator * 100',
  numerator_agg = 'sum', denominator_agg = 'sum', window_kind = 'period',
  min_window_days = 90, grain = 'institution', unit = '%',
  fact_function = 'platform.metric_fact_fin_bank_036_v1'
 WHERE metric_id = 'FIN-BANK-036-v1';

UPDATE platform.metric_definition SET
  metric_kind = 'ratio', formula_expr = 'numerator / denominator * 100',
  numerator_agg = 'sum', denominator_agg = 'sum', window_kind = 'period',
  min_window_days = 90, grain = 'institution', unit = '%',
  fact_function = 'platform.metric_fact_fin_bank_036_v2'
 WHERE metric_id = 'FIN-BANK-036-v2';

UPDATE platform.metric_definition SET
  metric_kind = 'sum', formula_expr = 'numerator',
  numerator_agg = 'sum', denominator_agg = NULL, window_kind = 'period',
  min_window_days = 1, grain = 'product', unit = '元',
  fact_function = 'platform.metric_fact_fin_ins_001'
 WHERE metric_id = 'FIN-INS-001';

UPDATE platform.metric_definition SET
  metric_kind = 'ratio', formula_expr = 'numerator / denominator',
  numerator_agg = 'sum', denominator_agg = 'sum', window_kind = 'instant',
  min_window_days = 0, grain = 'segment', unit = '个/户',
  fact_function = 'platform.metric_fact_cust_010'
 WHERE metric_id = 'CUST-010';

-- =====================================================================
-- 6. FIN-BANK-034: machine-readable spec beside the human rule text
-- =====================================================================
-- The human wording stays exactly as seeded by V21. Each rule gains a
-- "spec" object the executor can evaluate without parsing Chinese text.
UPDATE platform.metric_definition
   SET rule_set_json = '[
  {"id":"R01","level":"L1","signal":"逾期进入关注","window":"日","debounce":"连续 2 个观测日","threshold":">=30 天","suppression":"已核销/已结清/已进入不良处置的不重复告警","trigger_fields":["dpd"],"spec":{"op":"gte","field":"dpd","value":30}},
  {"id":"R02","level":"L3","signal":"逾期进入不良","window":"日","debounce":"即时","threshold":">=90 天","suppression":"同一对象 30 天内已 L3 的合并；不抑制首次 90+","trigger_fields":["dpd"],"spec":{"op":"gte","field":"dpd","value":90}},
  {"id":"R03","level":"L2","signal":"逾期迁徙恶化","window":"30 天","debounce":"事件触发 1 次","threshold":"30→60 天（跨 1 档）","suppression":"已获批展期/重组观察期内抑制","trigger_fields":["dpd_start","dpd_end"],"spec":{"op":"band_cross","start":"dpd_start","end":"dpd_end","from":30,"to":60}},
  {"id":"R04","level":"L2","signal":"五级分类下迁","window":"90 天","debounce":"事件触发 1 次","threshold":"下调 >=1 档","suppression":"30 天内回调则撤销本次告警（滞回）","trigger_fields":["risk_class_prev","risk_class_curr"],"spec":{"op":"downgrade","prev":"risk_class_prev","curr":"risk_class_curr","scale":["normal","special","substandard","doubtful","loss"],"value":1}},
  {"id":"R05","level":"L2","signal":"外部评级下调","window":"180 天","debounce":"事件触发 1 次","threshold":"下调 >=2 个 notch","suppression":"评级观察名单已告警的 90 天内合并","trigger_fields":["rating_notch_prev","rating_notch_curr"],"spec":{"op":"downgrade","prev":"rating_notch_prev","curr":"rating_notch_curr","value":2}},
  {"id":"R06","level":"L1","signal":"额度高占用","window":"连续 30 天","debounce":"连续 30 天","threshold":"使用率 >=90%","suppression":"额度已冻结/已过期/已注销的不告警","trigger_fields":["drawn_principal","approved_limit"],"spec":{"op":"ratio_gte","numerator":"drawn_principal","denominator":"approved_limit","value":0.9}},
  {"id":"R07","level":"L3","signal":"交叉违约","window":"90 天","debounce":"即时","threshold":"任一其他债项 90+ 或违约","suppression":"同一债务人 30 天内已 L3 的合并","trigger_fields":["other_facility_dpd_90plus","default_flag"],"spec":{"op":"any_true","fields":["other_facility_dpd_90plus","default_flag"]}},
  {"id":"R08","level":"L2","signal":"现金流异动","window":"连续 2 个月","debounce":"连续 2 个月","threshold":"较过去 12 个月均值下降 >=50%","suppression":"同比同月也下降 >=50% 的视为季节性，降为 L1 观察","trigger_fields":["monthly_inflow"],"spec":{"op":"drop_gte","field":"monthly_inflow","baseline":"inflow_12m_avg","value":0.5}},
  {"id":"R09","level":"L1","signal":"还款行为异动","window":"2 个还款期","debounce":"连续 2 期","threshold":"连续 2 期仅最低/部分还款，或还款额下降 >=30%","suppression":"因利率调整/展期导致应还额变化的，先还原再判断","trigger_fields":["paid_amount","due_amount"],"spec":{"op":"any_of","clauses":[{"op":"gte","field":"consecutive_partial_count","value":2},{"op":"ratio_lte","numerator":"paid_amount","denominator":"due_amount","value":0.7}]}},
  {"id":"R10","level":"L2","signal":"押品/担保弱化","window":"90 天","debounce":"事件触发 1 次","threshold":"押品覆盖率下降 >=20%，或担保撤销","suppression":"已安排重估/已批准替换担保的 30 天内抑制","trigger_fields":["collateral_value","loan_balance","guarantee_status"],"spec":{"op":"any_of","clauses":[{"op":"drop_gte","field":"collateral_ratio_curr","baseline":"collateral_ratio_prev","value":0.2},{"op":"equals","field":"guarantee_status","value":"revoked"}]}}
]'::jsonb
 WHERE metric_id = 'FIN-BANK-034';
