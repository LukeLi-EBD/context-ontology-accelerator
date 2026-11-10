-- V52: ontology ownership columns. P1-03.
--
-- Scope is deliberately columns + indexes only. There is NO backfill here:
-- the 1,908 versions / 1,313 proposals / 10,134 events live in the real corpus,
-- and running the derivation inside the migration would make an empty database
-- and a populated database take different paths. The data line backfills on the
-- 5944 clone and reconciles the counts there.
--
-- Columns (all three T-Box tables):
--
--   ontology_id        which ontology the row belongs to
--   namespace_id       owning namespace; NULL is expected and valid
--   attribution_source how the row was attributed ('platform', 'legacy_unmapped',
--                      ...); NULL means "not attributed yet"
--
-- No NOT NULL is added to any column: most of the corpus cannot derive a
-- namespace (24号 conclusion), so a NOT NULL would reject the real data. Rows
-- that the backfill cannot map stay NULL with attribution_source =
-- 'legacy_unmapped' and are listed by the data line, not by this migration.
--
-- Rollback: scripts/v52_ontology_ownership_rollback.sql.

-- ── ontology_version ────────────────────────────────────────────────────
ALTER TABLE platform.ontology_version
  ADD COLUMN IF NOT EXISTS ontology_id text,
  ADD COLUMN IF NOT EXISTS namespace_id uuid,
  ADD COLUMN IF NOT EXISTS attribution_source text;

CREATE INDEX IF NOT EXISTS ontology_version_owner_idx
  ON platform.ontology_version (namespace_id, ontology_id);

COMMENT ON COLUMN platform.ontology_version.ontology_id IS
  'Ontology identity shared by every version of the same ontology. NULL until '
  'the data-line backfill attributes it; not derived in the migration.';
COMMENT ON COLUMN platform.ontology_version.namespace_id IS
  'Owning namespace. NULL is expected and valid (not derivable for most rows).';
COMMENT ON COLUMN platform.ontology_version.attribution_source IS
  'How ownership was resolved (platform / legacy_unmapped / ...); NULL = not attributed yet.';

-- ── ontology_proposal ───────────────────────────────────────────────────
ALTER TABLE platform.ontology_proposal
  ADD COLUMN IF NOT EXISTS ontology_id text,
  ADD COLUMN IF NOT EXISTS namespace_id uuid,
  ADD COLUMN IF NOT EXISTS attribution_source text;

CREATE INDEX IF NOT EXISTS ontology_proposal_owner_idx
  ON platform.ontology_proposal (namespace_id, ontology_id);

COMMENT ON COLUMN platform.ontology_proposal.ontology_id IS
  'Ontology identity. NULL until the data-line backfill attributes it.';
COMMENT ON COLUMN platform.ontology_proposal.namespace_id IS
  'Owning namespace. NULL is expected and valid.';
COMMENT ON COLUMN platform.ontology_proposal.attribution_source IS
  'How ownership was resolved; NULL = not attributed yet.';

-- ── ontology_event ──────────────────────────────────────────────────────
ALTER TABLE platform.ontology_event
  ADD COLUMN IF NOT EXISTS ontology_id text,
  ADD COLUMN IF NOT EXISTS namespace_id uuid,
  ADD COLUMN IF NOT EXISTS attribution_source text;

CREATE INDEX IF NOT EXISTS ontology_event_owner_idx
  ON platform.ontology_event (namespace_id, ontology_id);

COMMENT ON COLUMN platform.ontology_event.ontology_id IS
  'Ontology identity. NULL until the data-line backfill attributes it.';
COMMENT ON COLUMN platform.ontology_event.namespace_id IS
  'Owning namespace. NULL is expected and valid.';
COMMENT ON COLUMN platform.ontology_event.attribution_source IS
  'How ownership was resolved; NULL = not attributed yet.';
