-- V53: index for reverse lookup on platform.graph_pointer. P1-03.
--
-- The pointer table already exists (V2) and is keyed by name. Its only index is
-- the primary key on name, so "which pointers reference this version?" and the
-- FK check on delete both scan the whole table. The data line's 1,645-pointer
-- write/reconcile path looks rows up by version, so add the missing index here.
--
-- Scope is the index only: no table, no data, no NOT NULL. The pointer rows
-- themselves are written by the data line (their 'current' semantics depend on
-- version status and cannot be fixed inside a migration).
--
-- Rollback: scripts/v53_graph_pointer_version_idx_rollback.sql.

CREATE INDEX IF NOT EXISTS graph_pointer_version_idx
  ON platform.graph_pointer (version_id);

COMMENT ON INDEX platform.graph_pointer_version_idx IS
  'Reverse lookup / FK support for graph_pointer.version_id (V53).';
