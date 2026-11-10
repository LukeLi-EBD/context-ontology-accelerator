-- V19: metric observations (fixture-or-business numerator/denominator facts) and
-- the definition fields a generic calculator needs. Re-entrant: every DDL uses
-- IF NOT EXISTS / a guarded DO block and the seeds are plain UPDATEs.
ALTER TABLE platform.metric_definition
  ADD COLUMN IF NOT EXISTS definition_version text NOT NULL DEFAULT 'v3.0';
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS metric_kind text;
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS formula_expr text;
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS numerator_agg text;
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS denominator_agg text;
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS window_kind text;
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS min_window_days integer;
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS grain text;
ALTER TABLE platform.metric_definition ADD COLUMN IF NOT EXISTS unit text;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
     WHERE conname = 'metric_definition_metric_version_key'
       AND conrelid = 'platform.metric_definition'::regclass
  ) THEN
    ALTER TABLE platform.metric_definition
      ADD CONSTRAINT metric_definition_metric_version_key
      UNIQUE (metric_id, definition_version);
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS platform.metric_observation (
  observation_id     bigserial PRIMARY KEY,
  metric_id          text NOT NULL,
  definition_version text NOT NULL DEFAULT 'v3.0',
  institution        text,
  product            text,
  entity_key         text NOT NULL,
  as_of              date,
  period_start       date,
  period_end         date,
  numerator          numeric NOT NULL,
  denominator        numeric,
  window_start       date NOT NULL,
  window_end         date NOT NULL,
  data_source        text NOT NULL CHECK (data_source IN ('fixture', 'business')),
  fixture            boolean NOT NULL DEFAULT false,
  computed_at        timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT metric_observation_definition_fk
    FOREIGN KEY (metric_id, definition_version)
    REFERENCES platform.metric_definition (metric_id, definition_version),
  CONSTRAINT metric_observation_window_key
    UNIQUE (metric_id, definition_version, entity_key, window_start, window_end)
);
CREATE INDEX IF NOT EXISTS metric_observation_lookup_idx
  ON platform.metric_observation (metric_id, definition_version, window_start, window_end);

-- Four matrix metrics that pass regulatory + publishable + 4/4. The calculator
-- reads these fields verbatim; no per-metric formula lives in Python.
UPDATE platform.metric_definition SET
  metric_kind = 'duration', formula_expr = 'numerator', numerator_agg = 'max',
  denominator_agg = NULL, window_kind = 'instant', min_window_days = 0,
  grain = 'agreement', unit = '天'
 WHERE metric_id = 'FIN-BANK-001';

UPDATE platform.metric_definition SET
  metric_kind = 'ratio', formula_expr = 'numerator / denominator * 100',
  numerator_agg = 'max', denominator_agg = 'max', window_kind = 'instant',
  min_window_days = 0, grain = 'customer', unit = '%'
 WHERE metric_id = 'FIN-BANK-025';

UPDATE platform.metric_definition SET
  metric_kind = 'ratio', formula_expr = 'numerator / denominator * 100',
  numerator_agg = 'sum', denominator_agg = 'max', window_kind = 'instant',
  min_window_days = 0, grain = 'customer', unit = '%'
 WHERE metric_id = 'FIN-BANK-030';

UPDATE platform.metric_definition SET
  metric_kind = 'ratio', formula_expr = 'numerator / denominator * 100',
  numerator_agg = 'sum', denominator_agg = 'sum', window_kind = 'period',
  min_window_days = 365, grain = 'product', unit = '%'
 WHERE metric_id = 'FIN-INS-021';
