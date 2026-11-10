-- P1 run ledger for `platform import` (F17/F18 follow-up).
-- import_batch is one row per root and every rerun overwrites its status,
-- options and finished_at, so per-invocation counts cannot be reconciled
-- afterwards. One row here per invocation keeps started/finished, the exact
-- counters reported on stdout, and how the run ended.
CREATE TABLE IF NOT EXISTS platform.import_run (
    run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id uuid NOT NULL REFERENCES platform.import_batch (batch_id) ON DELETE CASCADE,
    namespace_id uuid NOT NULL,
    status text NOT NULL CHECK (status IN ('running', 'completed', 'interrupted', 'failed')),
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    exit_code integer,
    options jsonb NOT NULL DEFAULT '{}'::jsonb,
    counters jsonb NOT NULL DEFAULT '{}'::jsonb,
    error_code text,
    error_message text
);

CREATE INDEX IF NOT EXISTS import_run_batch_started_idx
    ON platform.import_run (batch_id, started_at DESC);

CREATE INDEX IF NOT EXISTS import_run_namespace_started_idx
    ON platform.import_run (namespace_id, started_at DESC);

-- A run left in 'running' means the process died without a final update; the
-- partial index keeps that query cheap for the recovery/stale read paths.
CREATE INDEX IF NOT EXISTS import_run_running_idx
    ON platform.import_run (batch_id)
    WHERE status = 'running';
