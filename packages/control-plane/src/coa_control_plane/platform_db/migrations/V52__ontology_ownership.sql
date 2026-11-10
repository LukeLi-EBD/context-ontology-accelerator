-- V52: ontology ownership. P1-03.
--
-- Adds the two ownership columns that the T-Box tables never carried:
--
--   ontology_id   which ontology a row belongs to (versions of the same
--                 ontology, including rollbacks, share it)
--   namespace_id  which namespace owns that ontology
--
-- ontology_id is derived, not invented: every version's ``graph_iri`` already
-- ends in the ontology identity (``urn:platform:graph:tbox:ont-abc``), and a
-- rollback row points at the graph IRI of the version it rolled back to. Taking
-- the last IRI segment therefore groups ``ont-abc`` and its rollback rows under
-- one ownership key — no extra lookup table and no rewritten history.
--
-- namespace_id has no source anywhere in V1..V51. It is added NULLable on
-- purpose: rows authored before this migration have no namespace recorded, and
-- guessing one would be worse than leaving it NULL. The migration ends with an
-- explicit inventory of those rows (NOTICE) so the backfill operates on a
-- named list instead of an assumption. Use
-- ``scripts/v52_ontology_ownership_backfill.sql`` to attribute a namespace
-- explicitly.
--
-- Rollback: ``scripts/v52_ontology_ownership_rollback.sql``.

-- ── ontology_version ────────────────────────────────────────────────────
ALTER TABLE platform.ontology_version
  ADD COLUMN IF NOT EXISTS ontology_id text;

UPDATE platform.ontology_version
   SET ontology_id = regexp_replace(graph_iri, '^.*:', '')
 WHERE ontology_id IS NULL;

ALTER TABLE platform.ontology_version
  ALTER COLUMN ontology_id SET NOT NULL;

ALTER TABLE platform.ontology_version
  ADD COLUMN IF NOT EXISTS namespace_id uuid;

CREATE INDEX IF NOT EXISTS ontology_version_owner_idx
  ON platform.ontology_version (namespace_id, ontology_id, created_at DESC);

COMMENT ON COLUMN platform.ontology_version.ontology_id IS
  'Ontology identity shared by every version of the same ontology (rollbacks '
  'keep the rolled-back version''s identity). Derived from graph_iri at V52.';
COMMENT ON COLUMN platform.ontology_version.namespace_id IS
  'Owning namespace. NULL means "not recorded before V52"; see '
  'scripts/v52_ontology_ownership_backfill.sql. Never guess this value.';

-- ── ontology_proposal ───────────────────────────────────────────────────
ALTER TABLE platform.ontology_proposal
  ADD COLUMN IF NOT EXISTS ontology_id text;

UPDATE platform.ontology_proposal p
   SET ontology_id = v.ontology_id
  FROM platform.ontology_version v
 WHERE v.version_id = p.version_id
   AND p.ontology_id IS NULL;

ALTER TABLE platform.ontology_proposal
  ALTER COLUMN ontology_id SET NOT NULL;

ALTER TABLE platform.ontology_proposal
  ADD COLUMN IF NOT EXISTS namespace_id uuid;

CREATE INDEX IF NOT EXISTS ontology_proposal_owner_idx
  ON platform.ontology_proposal (namespace_id, ontology_id, created_at DESC);

COMMENT ON COLUMN platform.ontology_proposal.ontology_id IS
  'Ontology identity, inherited from ontology_version.version_id at V52.';
COMMENT ON COLUMN platform.ontology_proposal.namespace_id IS
  'Owning namespace. NULL means "not recorded before V52"; never guessed.';

-- ── ontology_event ──────────────────────────────────────────────────────
ALTER TABLE platform.ontology_event
  ADD COLUMN IF NOT EXISTS ontology_id text;

UPDATE platform.ontology_event e
   SET ontology_id = v.ontology_id
  FROM platform.ontology_version v
 WHERE v.version_id = e.version_id
   AND e.ontology_id IS NULL;

ALTER TABLE platform.ontology_event
  ALTER COLUMN ontology_id SET NOT NULL;

ALTER TABLE platform.ontology_event
  ADD COLUMN IF NOT EXISTS namespace_id uuid;

CREATE INDEX IF NOT EXISTS ontology_event_owner_idx
  ON platform.ontology_event (namespace_id, ontology_id, event_id DESC);

COMMENT ON COLUMN platform.ontology_event.ontology_id IS
  'Ontology identity, inherited from ontology_version.version_id at V52.';
COMMENT ON COLUMN platform.ontology_event.namespace_id IS
  'Owning namespace. NULL means "not recorded before V52"; never guessed.';

-- ── NULL namespace inventory (explicit, not silent) ─────────────────────
DO $$
DECLARE
  v_versions   bigint;
  v_proposals  bigint;
  v_events     bigint;
  n_versions   bigint;
  n_proposals  bigint;
  n_events     bigint;
BEGIN
  SELECT count(*), count(*) FILTER (WHERE namespace_id IS NULL)
    INTO v_versions, n_versions
    FROM platform.ontology_version;
  SELECT count(*), count(*) FILTER (WHERE namespace_id IS NULL)
    INTO v_proposals, n_proposals
    FROM platform.ontology_proposal;
  SELECT count(*), count(*) FILTER (WHERE namespace_id IS NULL)
    INTO v_events, n_events
    FROM platform.ontology_event;

  RAISE NOTICE 'V52: ontology_version % row(s), % without namespace_id', v_versions, n_versions;
  RAISE NOTICE 'V52: ontology_proposal % row(s), % without namespace_id', v_proposals, n_proposals;
  RAISE NOTICE 'V52: ontology_event % row(s), % without namespace_id', v_events, n_events;
  IF n_versions + n_proposals + n_events > 0 THEN
    RAISE NOTICE 'V52: attribute them with scripts/v52_ontology_ownership_backfill.sql '
                 '(explicit namespace per root path); NULL is not an error';
  END IF;
END $$;
