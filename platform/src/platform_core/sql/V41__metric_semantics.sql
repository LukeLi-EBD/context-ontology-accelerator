-- V41 · M-02 观测聚合语义标记 + 口径修订（2026-11-07）
--
-- 编号约束（硬）：V35 / V36 已永久退休，任何情况下不得复用、不得改写、不得引用。
-- 本迁移包含三部分：
--   1) metric_definition.aggregation_semantics：声明观测值能否跨观测相加；
--   2) 库级校验：distinct_count 必须有去重来源（binding 的 count_distinct 或 fact_function）；
--   3) FIN-INS-015/016/018：denominator_agg 由 count_distinct 改为 sum
--      （观测粒度不变，仍按 grain 预聚合；供给端必须写 COUNT(DISTINCT entity)）。
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

-- 3. 库级校验：distinct_count 必须有去重来源 -------------------------------------
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
