-- V52 rollback: remove the ownership columns and their indexes.
--
-- Drops back to the V51 shape. Data in the columns is lost by design — the
-- backfill is owned by the data line and can be re-run after re-applying V52.

BEGIN;

DROP INDEX IF EXISTS platform.ontology_event_owner_idx;
DROP INDEX IF EXISTS platform.ontology_proposal_owner_idx;
DROP INDEX IF EXISTS platform.ontology_version_owner_idx;

ALTER TABLE platform.ontology_event
  DROP COLUMN IF EXISTS attribution_source,
  DROP COLUMN IF EXISTS namespace_id,
  DROP COLUMN IF EXISTS ontology_id;

ALTER TABLE platform.ontology_proposal
  DROP COLUMN IF EXISTS attribution_source,
  DROP COLUMN IF EXISTS namespace_id,
  DROP COLUMN IF EXISTS ontology_id;

ALTER TABLE platform.ontology_version
  DROP COLUMN IF EXISTS attribution_source,
  DROP COLUMN IF EXISTS namespace_id,
  DROP COLUMN IF EXISTS ontology_id;

COMMIT;
