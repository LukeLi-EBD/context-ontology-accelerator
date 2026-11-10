-- V47: every bulk import batch must declare the namespace it ingested into.
--
-- Why: the ingestion-run listing is namespace scoped. A batch without a
-- namespace cannot be authorized by Cedar (viewNamespace) and cannot be
-- filtered in a multi-namespace deployment, and the namespace registry lives
-- in the control plane (DynamoDB), so it is not a FK target in this database.
--
-- Design of the write constraint (deliberately a trigger, not a CHECK):
--   * The column is added nullable because 18 pre-namespace batches exist.
--   * `CHECK (namespace_id IS NOT NULL) NOT VALID` would still be enforced on
--     every UPDATE of a legacy row, so resuming or finishing an old batch
--     (status/updated_at updates in importer._get_or_create_batch and the
--     batch finish path) would fail forever. NOT VALID only skips the initial
--     table scan.
--   * A BEFORE INSERT trigger enforces "new batches must carry a namespace"
--     exactly, and leaves legacy rows updatable.
--   * The trigger lets a statement through when the batch already exists
--     (same root_path): importer._get_or_create_batch resumes through
--     INSERT ... ON CONFLICT (root_path) DO UPDATE, and insert-time checks run
--     before conflict arbitration. Without that exemption, resuming any
--     pre-V47 batch would fail even though no new row is created.
--
-- Backfill policy (no guessing):
--   1) A row is filled only when its own options already carry an explicit
--      namespaceId string. That value is the caller's statement, not an
--      inference, so it is safe to promote.
--   2) Every other row stays NULL. Nothing else in this database derives a
--      namespace: root_path is a filesystem directory, import_item has no
--      namespace column, and platform.document.metadata only records
--      batchId/relPath. A path is not a namespace, so no default/fallback
--      namespace is invented.
--   3) The NOTICE below reports the unattributed count into the migrate log
--      so the operator sees it instead of discovering it later.
--
-- Legacy NULL rows are intentionally left unattributed. If an operator can
-- attribute a path by hand they may run
--   UPDATE platform.import_batch SET namespace_id = '<uuid>' WHERE root_path = '<path>'
-- row by row. Until then those batches stay invisible to namespace-scoped
-- queries but keep working for resume.

ALTER TABLE platform.import_batch
  ADD COLUMN IF NOT EXISTS namespace_id uuid;

UPDATE platform.import_batch
   SET namespace_id = (options ->> 'namespaceId')::uuid
 WHERE namespace_id IS NULL
   AND options ->> 'namespaceId'
       ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';

CREATE INDEX IF NOT EXISTS import_batch_namespace_updated_idx
  ON platform.import_batch (namespace_id, updated_at DESC, batch_id);

CREATE OR REPLACE FUNCTION platform.import_batch_require_namespace()
RETURNS trigger
LANGUAGE plpgsql
AS $fn$
BEGIN
  IF NEW.namespace_id IS NULL THEN
    -- Resume path: the batch already exists and the statement below is an
    -- upsert, so no namespace-less row is created. Inherit whatever the
    -- existing row has (NULL for pre-V47 batches) and let the upsert run.
    IF EXISTS (SELECT 1 FROM platform.import_batch WHERE root_path = NEW.root_path) THEN
      RETURN NEW;
    END IF;
    RAISE EXCEPTION 'E_IMPORT_NAMESPACE_REQUIRED: import_batch.namespace_id must not be null'
      USING ERRCODE = '23502',
            HINT = 'pass the caller namespace when creating a batch (V47 and later)';
  END IF;
  RETURN NEW;
END
$fn$;

DROP TRIGGER IF EXISTS import_batch_require_namespace ON platform.import_batch;

CREATE TRIGGER import_batch_require_namespace
  BEFORE INSERT ON platform.import_batch
  FOR EACH ROW
  EXECUTE FUNCTION platform.import_batch_require_namespace();

DO $do$
DECLARE
  total_rows bigint;
  legacy_rows bigint;
BEGIN
  SELECT count(*), count(*) FILTER (WHERE namespace_id IS NULL)
    INTO total_rows, legacy_rows
    FROM platform.import_batch;
  IF legacy_rows > 0 THEN
    RAISE NOTICE 'V47: % of % import_batch row(s) have no derivable namespace and stay NULL (no default applied)', legacy_rows, total_rows;
  ELSE
    RAISE NOTICE 'V47: all % import_batch row(s) have namespace_id', total_rows;
  END IF;
END
$do$;

COMMENT ON COLUMN platform.import_batch.namespace_id IS
  'Namespace the batch ingests into. Required for new rows (enforced by trigger import_batch_require_namespace). Pre-V47 rows are NULL when the namespace is not derivable and are hidden from namespace-scoped queries.';
