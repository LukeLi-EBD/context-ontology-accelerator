-- V20: the two time-series fact tables two v3 metrics were missing.
--
-- Relation to metric_observation: these are independent fact tables, not
-- dimensions of the observation table. One row is one contract period
-- (insurance payment installment / loan repayment installment) at one
-- status date. They are never read by the calculator directly. The projector
-- in metric_facts.py aggregates them through the per-definition function
-- named in metric_definition.fact_function, then upserts one observation row
-- per (entity_key, observation window) into platform.metric_observation.
-- The calculator therefore still reads only metric_observation, and every
-- value keeps the fixture/business provenance of its source rows.
--
-- Re-entrant: tables use IF NOT EXISTS, functions use CREATE OR REPLACE,
-- indexes use IF NOT EXISTS, and the seed is a plain UPDATE.
ALTER TABLE platform.metric_definition
  ADD COLUMN IF NOT EXISTS fact_function text;

CREATE TABLE IF NOT EXISTS platform.ins_payment_record (
  payment_id      bigserial PRIMARY KEY,
  policy_no       text NOT NULL,
  product         text NOT NULL,
  installment_no  integer NOT NULL CHECK (installment_no > 0),
  due_date        date NOT NULL,
  due_amount      numeric NOT NULL CHECK (due_amount >= 0),
  paid_amount     numeric NOT NULL DEFAULT 0 CHECK (paid_amount >= 0),
  paid_date       date,
  payment_status  text NOT NULL
    CHECK (payment_status IN ('paid', 'unpaid', 'waived')),
  policy_status   text NOT NULL
    CHECK (policy_status IN ('in_force', 'lapsed', 'surrendered', 'cancelled')),
  status_as_of    date NOT NULL,
  institution     text,
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ins_payment_record_key
    UNIQUE (policy_no, installment_no, status_as_of, data_source)
);
CREATE INDEX IF NOT EXISTS ins_payment_record_window_idx
  ON platform.ins_payment_record (due_date, installment_no, data_source);
COMMENT ON TABLE platform.ins_payment_record IS
  '缴费记录/状态历史（期次级事实）：一行=一张保单一个期次在一个状态观察日的状态；'
  '按 due_date 进入观察窗，按 status_as_of 取最新状态。';

CREATE TABLE IF NOT EXISTS platform.loan_installment_plan (
  plan_id         bigserial PRIMARY KEY,
  agreement_id    text NOT NULL,
  installment_no  integer NOT NULL CHECK (installment_no > 0),
  due_date        date NOT NULL,
  due_amount      numeric NOT NULL CHECK (due_amount >= 0),
  paid_amount     numeric NOT NULL DEFAULT 0 CHECK (paid_amount >= 0),
  paid_date       date,
  overdue_days    integer CHECK (overdue_days IS NULL OR overdue_days >= 0),
  status_as_of    date NOT NULL,
  institution     text,
  data_source     text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture         boolean NOT NULL DEFAULT false,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT loan_installment_plan_key
    UNIQUE (agreement_id, installment_no, status_as_of, data_source)
);
CREATE INDEX IF NOT EXISTS loan_installment_plan_lookup_idx
  ON platform.loan_installment_plan (status_as_of, agreement_id, data_source);
COMMENT ON TABLE platform.loan_installment_plan IS
  '分期计划条目（期次级事实）：一行=一笔协议一个期数在一个状态观察日的应还/实还/逾期天数；'
  '时点口径只取 status_as_of = 观察日，不把其它时点值混入。';

-- FIN-INS-021: the period window is the 13th-installment due window. Only
-- policies whose installment 13 falls inside [p_start, p_end] enter the
-- denominator; per policy the latest status snapshot wins. A point-in-time
-- snapshot is never treated as a period value.
CREATE OR REPLACE FUNCTION platform.metric_fact_fin_ins_021(
  p_start date,
  p_end date,
  p_data_source text
)
RETURNS TABLE (
  entity_key text,
  institution text,
  product text,
  window_start date,
  window_end date,
  numerator numeric,
  denominator numeric,
  data_source text,
  fixture boolean
)
LANGUAGE sql
STABLE
AS $$
  WITH due AS (
    SELECT DISTINCT ON (r.policy_no)
           r.policy_no,
           r.product,
           r.institution,
           r.payment_status,
           r.policy_status,
           r.data_source,
           r.fixture
      FROM platform.ins_payment_record r
     WHERE r.installment_no = 13
       AND r.due_date >= p_start
       AND r.due_date <= p_end
       AND r.data_source = p_data_source
     ORDER BY r.policy_no, r.status_as_of DESC, r.payment_id DESC
  )
  SELECT due.product AS entity_key,
         MIN(due.institution) AS institution,
         due.product AS product,
         p_start AS window_start,
         p_end AS window_end,
         COUNT(*) FILTER (
           WHERE due.payment_status = 'paid' AND due.policy_status = 'in_force'
         )::numeric AS numerator,
         COUNT(*)::numeric AS denominator,
         MIN(due.data_source) AS data_source,
         BOOL_OR(due.fixture) AS fixture
    FROM due
   GROUP BY due.product
$$;

-- FIN-BANK-001: instant window. One observation per agreement at p_start;
-- overdue_days is the installment-level fact, MAX per agreement, and the
-- definition-level MAX picks the worst agreement. p_start = p_end is enforced
-- here as well so an instant metric can never be fed a period window.
CREATE OR REPLACE FUNCTION platform.metric_fact_fin_bank_001(
  p_start date,
  p_end date,
  p_data_source text
)
RETURNS TABLE (
  entity_key text,
  institution text,
  product text,
  window_start date,
  window_end date,
  numerator numeric,
  denominator numeric,
  data_source text,
  fixture boolean
)
LANGUAGE sql
STABLE
AS $$
  SELECT p.agreement_id AS entity_key,
         MIN(p.institution) AS institution,
         NULL::text AS product,
         p_start AS window_start,
         p_end AS window_end,
         MAX(COALESCE(p.overdue_days, 0))::numeric AS numerator,
         NULL::numeric AS denominator,
         MIN(p.data_source) AS data_source,
         BOOL_OR(p.fixture) AS fixture
    FROM platform.loan_installment_plan p
   WHERE p.status_as_of = p_start
     AND p_start = p_end
     AND p.data_source = p_data_source
   GROUP BY p.agreement_id
$$;

-- Bind the two definitions to their fact functions. No formula, aggregate,
-- window kind or unit is touched: basis v3 stays exactly as seeded by V19.
UPDATE platform.metric_definition
   SET fact_function = 'platform.metric_fact_fin_ins_021'
 WHERE metric_id = 'FIN-INS-021';

UPDATE platform.metric_definition
   SET fact_function = 'platform.metric_fact_fin_bank_001'
 WHERE metric_id = 'FIN-BANK-001';
