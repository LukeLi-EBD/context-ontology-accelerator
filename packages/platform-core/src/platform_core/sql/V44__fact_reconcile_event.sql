-- Reconciliation is part of the audit chain.
-- `reconcile_fact_ledger.py --fix` appends one `reconciled` event per repaired
-- fact, so a repair is visible in the same hash chain as every other change.
-- NOTE: the migration runner splits on semicolons, so comments must not contain one.

ALTER TABLE platform.fact_event
    DROP CONSTRAINT IF EXISTS fact_event_action_check;

ALTER TABLE platform.fact_event
    ADD CONSTRAINT fact_event_action_check
    CHECK (action IN (
        'asserted', 'retracted', 'restored', 'batch_retracted',
        'conflict_kept', 'conflict_accepted', 'merged', 'merge_superseded',
        'unmerged', 'resolution_undo', 'purged_test_graph', 'reconciled'
    ));
