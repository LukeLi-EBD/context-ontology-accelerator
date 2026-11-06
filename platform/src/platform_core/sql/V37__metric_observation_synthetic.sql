-- V41: 让 metric_observation 明确承载 synthetic 合成事实的观测行。
--
-- 背景：V19 把 data_source 限制为 fixture|business；V26 为了 datagen 已把
-- “所有带 data_source 列的表”统一扩成 fixture|business|synthetic。因此在本
-- 迁移之前建成的库，metric_observation 的 CHECK 通常已经包含 synthetic。
-- 本迁移做三件事，且全部幂等：
--   1) 若 metric_observation 的 data_source CHECK 仍缺 synthetic，则就地替换；
--   2) 在表/列注释里写明“观测行是分子/分母输入，不是指标结果缓存”；
--   3) 不改任何指标定义、不写任何数据。
--
-- 注意：本分支只提交迁移文件，不在本地/共享库执行。集成方须在 V35-V40 之后
-- 按顺序应用本迁移并登记到 metadata_pg.MIGRATIONS。

DO $$
DECLARE
  con record;
BEGIN
  SELECT con.conname AS constraint_name,
         pg_get_constraintdef(con.oid) AS definition
    INTO con
    FROM pg_constraint con
   WHERE con.conrelid = 'platform.metric_observation'::regclass
     AND con.contype = 'c'
     AND pg_get_constraintdef(con.oid) LIKE '%data_source%'
   LIMIT 1;

  IF con.constraint_name IS NULL THEN
    ALTER TABLE platform.metric_observation
      ADD CONSTRAINT metric_observation_data_source_check
      CHECK (data_source IN ('fixture', 'business', 'synthetic'));
  ELSIF con.definition NOT LIKE '%synthetic%' THEN
    EXECUTE format(
      'ALTER TABLE platform.metric_observation DROP CONSTRAINT %I',
      con.constraint_name
    );
    EXECUTE format(
      'ALTER TABLE platform.metric_observation ADD CONSTRAINT %I '
      'CHECK (data_source IN (''fixture'', ''business'', ''synthetic''))',
      con.constraint_name
    );
  END IF;
END $$;

COMMENT ON COLUMN platform.metric_observation.data_source IS
  '观测行来源：fixture=测试夹具，synthetic=合成数据生成器，business=真实业务。合成数据不得标为 fixture。';

COMMENT ON TABLE platform.metric_observation IS
  '按实体/窗口存储分子、分母观测值；指标值在读取时由 metric_definition.formula_expr 现算，本表不是结果缓存。';
