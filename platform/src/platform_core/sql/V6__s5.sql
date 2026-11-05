-- S5 reasoning: materialization jobs + inferred-graph pointer
-- NOTE: the migration runner splits on semicolons, so comments must not contain one.

CREATE TABLE IF NOT EXISTS platform.reasoning_job (
    job_id text PRIMARY KEY,
    kind text NOT NULL CHECK (kind IN ('materialize', 'validate')),
    ontology_version text,
    profile text,
    target_graph text,
    input_hash char(64),
    state text NOT NULL CHECK (state IN ('queued', 'running', 'succeeded', 'failed', 'skipped')),
    inferred integer,
    consistent boolean,
    error_code text,
    error_message text,
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    result_summary jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS reasoning_job_started_idx
    ON platform.reasoning_job (started_at DESC);

CREATE TABLE IF NOT EXISTS platform.inferred_pointer (
    name text PRIMARY KEY,
    ontology_version text NOT NULL,
    target_graph text NOT NULL,
    input_hash char(64) NOT NULL,
    inferred integer NOT NULL,
    job_id text NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);
