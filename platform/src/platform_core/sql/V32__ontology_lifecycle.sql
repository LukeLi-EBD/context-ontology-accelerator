-- V32: O-02 T-Box lifecycle state machine + O-04 publish evidence registry.
--
-- Re-entrant: constraints are dropped by name before being re-added and all
-- tables use IF NOT EXISTS. The transition table is append-only; no row is
-- ever updated or deleted by the application.

ALTER TABLE platform.ontology_version
  DROP CONSTRAINT IF EXISTS ontology_version_status_check;
ALTER TABLE platform.ontology_version
  ADD CONSTRAINT ontology_version_status_check
  CHECK (status IN ('draft', 'proposed', 'review', 'approved', 'published',
                    'superseded', 'deprecated', 'rejected'));

ALTER TABLE platform.ontology_proposal
  DROP CONSTRAINT IF EXISTS ontology_proposal_status_check;
ALTER TABLE platform.ontology_proposal
  ADD CONSTRAINT ontology_proposal_status_check
  CHECK (status IN ('proposed', 'review', 'approved', 'published', 'superseded', 'rejected'));

CREATE TABLE IF NOT EXISTS platform.ontology_lifecycle_transition (
  seq          bigserial PRIMARY KEY,
  entity_kind  text NOT NULL CHECK (entity_kind IN ('proposal', 'version')),
  entity_id    text NOT NULL,
  version_id   text NOT NULL,
  proposal_id  text,
  from_status  text,
  to_status    text NOT NULL,
  actor        text NOT NULL,
  reason       text,
  payload      jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ontology_lifecycle_version_idx
  ON platform.ontology_lifecycle_transition (version_id, seq);
CREATE INDEX IF NOT EXISTS ontology_lifecycle_proposal_idx
  ON platform.ontology_lifecycle_transition (proposal_id, seq);
CREATE INDEX IF NOT EXISTS ontology_lifecycle_entity_idx
  ON platform.ontology_lifecycle_transition (entity_kind, entity_id, seq);

-- O-04: every publish (success or gate failure) writes one evidence pack. The
-- pack body lives in payload; `path` is filled when the download endpoint
-- materializes it under storage.root/evidence/<version>.
CREATE TABLE IF NOT EXISTS platform.ontology_evidence (
  evidence_id  text PRIMARY KEY,
  version_id   text NOT NULL,
  proposal_id  text,
  verdict      text NOT NULL CHECK (verdict IN ('pass', 'fail')),
  path         text,
  sha256       char(64) NOT NULL,
  payload      jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_by   text NOT NULL DEFAULT 'operator',
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ontology_evidence_version_idx
  ON platform.ontology_evidence (version_id, created_at);
CREATE INDEX IF NOT EXISTS ontology_evidence_verdict_idx
  ON platform.ontology_evidence (verdict, created_at);
