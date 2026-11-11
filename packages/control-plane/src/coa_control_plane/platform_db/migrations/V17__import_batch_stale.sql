-- V17: lease/timeout convergence for bulk import batches. A batch left in
-- 'running' by a dead process must become 'stale' (not silently "running"
-- forever). Items stay untouched except orphaned 'parsing' rows, which go back
-- to 'pending' so the next run resumes without losing completed items.
ALTER TABLE platform.import_batch DROP CONSTRAINT IF EXISTS import_batch_status_check;
ALTER TABLE platform.import_batch
  ADD CONSTRAINT import_batch_status_check
  CHECK (status IN ('running', 'completed', 'interrupted', 'stale'));

CREATE INDEX IF NOT EXISTS import_batch_status_updated_idx
  ON platform.import_batch (status, updated_at);
