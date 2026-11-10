-- V49: supporting index for the namespace-scoped ingestion failure feed.
--
-- Why: F17 (ListIngestionRuns) returns an inline failure feed built from
--     SELECT i.batch_id, i.rel_path, i.attempts, i.failure_code, ...
--       FROM platform.import_item i
--       JOIN platform.import_batch b ON b.batch_id = i.batch_id
--      WHERE i.status = 'failed'
--        AND b.namespace_id = $1
--      ORDER BY i.updated_at DESC
--      LIMIT 20
--
-- import_item is only indexed by
--   * PRIMARY KEY (batch_id, rel_path)
--   * import_item_status_idx (batch_id, status)
--   * import_item_sha_idx (batch_id, sha256)
-- so "the newest failed items across every batch" cannot use an index and
-- degrades into a full scan plus sort as the import history grows.
--
-- A partial index keeps the cost proportional to failures only; healthy
-- imports (pending/parsing/chunked/indexed) never enter it. No column, data,
-- or constraint change: the namespace filter still comes from the join to
-- platform.import_batch, which V47 already indexed by
-- (namespace_id, updated_at DESC, batch_id).

CREATE INDEX IF NOT EXISTS import_item_failed_updated_idx
  ON platform.import_item (updated_at DESC, batch_id, rel_path)
  WHERE status = 'failed';
