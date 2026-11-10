-- V52 rollback: remove the ownership columns and their indexes.
--
-- Run only when the V52 migration must be undone. Dropping a column also
-- drops its index and comment, so this returns the three tables to their
-- V51 shape. Rows are not touched; namespace attribution is data, not schema,
-- and is intentionally left to the caller (see the backfill script).

BEGIN;

DROP INDEX IF EXISTS platform.ontology_event_owner_idx;
DROP INDEX IF EXISTS platform.ontology_proposal_owner_idx;
DROP INDEX IF EXISTS platform.ontology_version_owner_idx;

ALTER TABLE platform.ontology_event
  DROP COLUMN IF EXISTS namespace_id,
  DROP COLUMN IF EXISTS ontology_id;

ALTER TABLE platform.ontology_proposal
  DROP COLUMN IF EXISTS namespace_id,
  DROP COLUMN IF EXISTS ontology_id;

ALTER TABLE platform.ontology_version
  DROP COLUMN IF EXISTS namespace_id,
  DROP COLUMN IF EXISTS ontology_id;

COMMIT;
