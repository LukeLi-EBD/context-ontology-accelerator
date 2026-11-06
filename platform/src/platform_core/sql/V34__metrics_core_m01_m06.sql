-- M-01 指标可算性补齐第一批（8 条）。
-- 选型与理由见 doc/_design/53-M01-M06-指标可算性补齐与规则核对.md。
-- 迁移号固定 V34；可重入（UPDATE）。

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
