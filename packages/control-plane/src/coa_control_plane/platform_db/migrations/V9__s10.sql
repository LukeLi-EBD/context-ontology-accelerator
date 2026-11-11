-- S10: reversible adjudication + audit replay
-- Only extends the event action vocabulary. Undo is derived from existing ledger
-- resolution fields, so no new assertion columns are needed.
-- NOTE: the migration runner splits on semicolons, so comments must not contain one.

ALTER TABLE platform.fact_event
    DROP CONSTRAINT IF EXISTS fact_event_action_check;

ALTER TABLE platform.fact_event
    ADD CONSTRAINT fact_event_action_check
    CHECK (action IN (
        'asserted', 'retracted', 'restored', 'batch_retracted',
        'conflict_kept', 'conflict_accepted', 'merged', 'merge_superseded',
        'unmerged', 'resolution_undo'
    ));

CREATE INDEX IF NOT EXISTS fact_assertion_resolution_idx
    ON platform.fact_assertion (subject_iri, predicate_iri, resolved_at DESC)
    WHERE resolution IS NOT NULL;
