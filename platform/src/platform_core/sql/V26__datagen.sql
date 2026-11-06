-- Datagen support: allow the synthetic provenance label on the existing fact
-- tables, and add a run ledger. No fact table is created here; the generator
-- fills the tables that already exist in the platform schema.
--
-- The source selector rewrite is idempotent: a constraint that already accepts
-- 'synthetic' is left untouched. Existing fixture/business rows all satisfy the
-- widened predicate, so validation cannot fail.
DO $$
DECLARE
  r record;
BEGIN
  FOR r IN
    SELECT n.nspname AS schema_name,
           c.relname AS table_name,
           con.conname AS constraint_name
      FROM pg_constraint con
      JOIN pg_class c ON c.oid = con.conrelid
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'platform'
       AND con.contype = 'c'
       AND c.relname IN (
         SELECT table_name
           FROM information_schema.columns
          WHERE table_schema = 'platform'
            AND column_name = 'data_source'
       )
       AND pg_get_constraintdef(con.oid) LIKE '%data_source%'
       AND pg_get_constraintdef(con.oid) NOT LIKE '%synthetic%'
  LOOP
    EXECUTE format(
      'ALTER TABLE %I.%I DROP CONSTRAINT %I',
      r.schema_name, r.table_name, r.constraint_name
    );
    EXECUTE format(
      'ALTER TABLE %I.%I ADD CONSTRAINT %I '
      'CHECK (data_source IN (''fixture'', ''business'', ''synthetic''))',
      r.schema_name, r.table_name, r.constraint_name
    );
  END LOOP;
END $$;

CREATE TABLE IF NOT EXISTS platform.datagen_run (
  run_id        text PRIMARY KEY,
  seed          integer NOT NULL,
  scale         numeric NOT NULL,
  target_schema text NOT NULL,
  status        text NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'cleaned')),
  row_counts    jsonb NOT NULL DEFAULT '{}'::jsonb,
  coverage      jsonb NOT NULL DEFAULT '{}'::jsonb,
  checks        jsonb NOT NULL DEFAULT '{}'::jsonb,
  started_at    timestamptz NOT NULL DEFAULT now(),
  finished_at   timestamptz,
  notes         text
);
