-- S12: cleanup is part of the audit chain (OQ-45).
-- purge_test now appends one purged_test_graph event per removed assertion so a
-- replay reproduces the post-purge state instead of resurrecting deleted facts.
-- NOTE: the migration runner splits on semicolons, so comments must not contain one.

ALTER TABLE platform.fact_event
    DROP CONSTRAINT IF EXISTS fact_event_action_check;

ALTER TABLE platform.fact_event
    ADD CONSTRAINT fact_event_action_check
    CHECK (action IN (
        'asserted', 'retracted', 'restored', 'batch_retracted',
        'conflict_kept', 'conflict_accepted', 'merged', 'merge_superseded',
        'unmerged', 'resolution_undo', 'purged_test_graph'
    ));
