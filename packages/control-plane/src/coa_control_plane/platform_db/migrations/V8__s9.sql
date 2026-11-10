-- S9: conflict adjudication + hash-chained audit export
-- Adds resolution fields to the ledger and chain linkage to fact_event.
-- NOTE: the migration runner splits on semicolons, so comments must not contain one.

ALTER TABLE platform.fact_assertion
    ADD COLUMN IF NOT EXISTS accepted_conflict boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS resolved_by text,
    ADD COLUMN IF NOT EXISTS resolved_at timestamptz,
    ADD COLUMN IF NOT EXISTS resolution text,
    ADD COLUMN IF NOT EXISTS merged_from jsonb;

ALTER TABLE platform.fact_event
    ADD COLUMN IF NOT EXISTS prev_event bigint,
    ADD COLUMN IF NOT EXISTS hash text;

ALTER TABLE platform.fact_event
    DROP CONSTRAINT IF EXISTS fact_event_action_check;

ALTER TABLE platform.fact_event
    ADD CONSTRAINT fact_event_action_check
    CHECK (action IN (
        'asserted', 'retracted', 'restored', 'batch_retracted',
        'conflict_kept', 'conflict_accepted', 'merged', 'merge_superseded'
    ));

CREATE INDEX IF NOT EXISTS fact_event_created_idx
    ON platform.fact_event (event_id);
