-- V41 · M-02 观测聚合语义标记 + 口径修订（2026-11-07）
--
-- 编号约束（硬）：V35 / V36 已永久退休，任何情况下不得复用、不得改写、不得引用。
-- 编号口径（2026-11-07 定）：V41 = 指标观测聚合语义（本文件）；字典列注释
-- （feat/dict-comments，旧号 V37）改挂 V42。集成契约 §2.2 的登记行由集成线维护，
-- 本分支不改主仓文档。
-- 本迁移包含以下几部分：
--   1) metric_definition.aggregation_semantics：声明观测值能否跨观测相加；
--   2) 库级校验：distinct_count 必须有去重来源（binding 的 count_distinct 或 fact_function）；
--   3) FIN-INS-015/016/018：denominator_agg 由 count_distinct 改为 sum
--      （观测粒度不变，仍按 grain 预聚合；供给端必须写 COUNT(DISTINCT entity)）。
--   4) FIN-INS-021：fact function 改为 issue_date + 13 个月锚点 + 期末保单状态，
--      脱离 ins_payment_record（不再依赖 installment_no=13 的缴费行）。
--   5) FIN-INS-025：新增 fact function；渠道词表差异（绑定写 individual_agent，
--      事实表写 agent）在函数内桥接，待业务确认后收窄。
--
-- aggregation_semantics 取值：
--   sum            观测值可跨观测相加（金额、天数、件数等）；
--   distinct_count 观测分母是"已按分区去重的件数"；只允许在互斥分区之间相加，
--                  供给端必须写 COUNT(DISTINCT entity)，写 COUNT(*) 会被投影校验拒绝。

-- 1. 语义标记字段 ---------------------------------------------------------------
ALTER TABLE platform.metric_definition
  ADD COLUMN IF NOT EXISTS aggregation_semantics text NOT NULL DEFAULT 'sum';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
     WHERE conname = 'metric_definition_agg_semantics_check'
       AND conrelid = 'platform.metric_definition'::regclass
  ) THEN
    ALTER TABLE platform.metric_definition
      ADD CONSTRAINT metric_definition_agg_semantics_check
      CHECK (aggregation_semantics IN ('sum', 'distinct_count'));
  END IF;
END $$;

COMMENT ON COLUMN platform.metric_definition.aggregation_semantics IS
  '观测聚合语义：sum=可跨观测相加；distinct_count=分母为去重件数，仅可跨互斥分区相加，供给端必须写去重值（2026-11-07, V41）';

-- 2. 015 / 016 / 018：观测粒度不动，分母声明的聚合改为 sum -----------------------
UPDATE platform.metric_definition
   SET aggregation_semantics = 'distinct_count',
       denominator_agg = 'sum'
 WHERE metric_id IN ('FIN-INS-015', 'FIN-INS-016');

-- FIN-INS-018 的分子也是去重件数（count_distinct），同样改为 sum 汇总。
UPDATE platform.metric_definition
   SET aggregation_semantics = 'distinct_count',
       numerator_agg = 'sum',
       denominator_agg = 'sum'
 WHERE metric_id = 'FIN-INS-018';

-- 3. FIN-INS-021：13 个月锚点 + 期末保单状态，脱离 ins_payment_record -------------
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
  WITH cohort AS (
    SELECT DISTINCT ON (p.policy_no)
           p.policy_no,
           p.product,
           p.institution,
           p.policy_status,
           p.data_source,
           p.fixture
      FROM platform.ins_policy p
     WHERE (p.issue_date + INTERVAL '13 months')::date >= p_start
       AND (p.issue_date + INTERVAL '13 months')::date <= p_end
       AND p.status_as_of <= p_end
       AND p.data_source = p_data_source
     ORDER BY p.policy_no, p.status_as_of DESC
  )
  SELECT cohort.product AS entity_key,
         MIN(cohort.institution) AS institution,
         cohort.product AS product,
         p_start AS window_start,
         p_end AS window_end,
         COUNT(*) FILTER (WHERE cohort.policy_status = 'in_force')::numeric AS numerator,
         COUNT(*)::numeric AS denominator,
         MIN(cohort.data_source) AS data_source,
         BOOL_OR(cohort.fixture) AS fixture
    FROM cohort
   GROUP BY cohort.product
$$;

UPDATE platform.metric_definition
   SET aggregation_semantics = 'distinct_count'
 WHERE metric_id = 'FIN-INS-021';

-- 4. FIN-INS-025：新增 fact function（渠道词表桥接） ---------------------------
-- 绑定里分母是 count_distinct(policy_no)、分子是保费 sum；观测粒度是渠道。
-- 渠道：绑定写 'individual_agent'，事实表写 'agent'，此处桥接两者；
-- 这是临时口径，业务确认渠道词表后应收窄为单一枚举。
CREATE OR REPLACE FUNCTION platform.metric_fact_fin_ins_025(
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
  WITH base AS (
    SELECT p.policy_no,
           p.channel,
           p.institution,
           p.data_source,
           p.fixture,
           CASE WHEN p.premium_type = 'single'
                THEN p.premium_amount
                ELSE COALESCE(p.first_year_premium, p.premium_amount) END AS premium
      FROM platform.ins_policy p
     WHERE p.issue_date >= p_start
       AND p.issue_date <= p_end
       AND p.channel IN ('individual_agent', 'agent')
       AND p.data_source = p_data_source
  )
  SELECT base.channel AS entity_key,
         MIN(base.institution) AS institution,
         base.channel AS product,
         p_start AS window_start,
         p_end AS window_end,
         SUM(base.premium)::numeric AS numerator,
         COUNT(DISTINCT base.policy_no)::numeric AS denominator,
         MIN(base.data_source) AS data_source,
         BOOL_OR(base.fixture) AS fixture
    FROM base
   GROUP BY base.channel
$$;

UPDATE platform.metric_definition
   SET fact_function = 'platform.metric_fact_fin_ins_025',
       aggregation_semantics = 'distinct_count',
       denominator_agg = 'sum'
 WHERE metric_id = 'FIN-INS-025';

-- 5. 库级校验：distinct_count 必须有去重来源 -------------------------------------
DO $$
DECLARE bad text;
BEGIN
  SELECT string_agg(d.metric_id, ',' ORDER BY d.metric_id) INTO bad
    FROM platform.metric_definition d
   WHERE d.aggregation_semantics = 'distinct_count'
     AND d.fact_function IS NULL
     AND NOT EXISTS (
       SELECT 1 FROM platform.metric_field_binding b
        WHERE b.metric_id = d.metric_id
          AND b.role = 'denominator'
          AND b.agg = 'count_distinct'
     );
  IF bad IS NOT NULL THEN
    RAISE EXCEPTION USING MESSAGE =
      'E_METRIC_SEMANTICS_UNSUPPORTED: distinct_count 口径缺少去重来源: ' || bad;
  END IF;
END $$;
