-- V10: S11 T-Box change governance.
-- Lifecycle: draft -> proposed -> approved -> published -> superseded.
-- Proposals and the audit chain are append-only. Versions are never deleted.

ALTER TABLE platform.ontology_version
  DROP CONSTRAINT IF EXISTS ontology_version_status_check;

ALTER TABLE platform.ontology_version
  ADD CONSTRAINT ontology_version_status_check
  CHECK (status IN ('draft', 'proposed', 'approved', 'published', 'superseded',
                    'deprecated', 'rejected'));

CREATE TABLE IF NOT EXISTS platform.ontology_proposal (
  proposal_id          text PRIMARY KEY,
  version_id           text NOT NULL REFERENCES platform.ontology_version(version_id),
  against_version      text,
  change_summary       text NOT NULL,
  status               text NOT NULL CHECK (status IN ('proposed', 'approved', 'published')),
  breaking             boolean NOT NULL DEFAULT false,
  acknowledged_breaking boolean NOT NULL DEFAULT false,
  diff                 jsonb NOT NULL DEFAULT '{}'::jsonb,
  impact               jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_by           text NOT NULL DEFAULT 'operator',
  created_at           timestamptz NOT NULL DEFAULT now(),
  approved_by          text,
  approved_at          timestamptz,
  published_at         timestamptz
);

CREATE INDEX IF NOT EXISTS ontology_proposal_version_idx
  ON platform.ontology_proposal (version_id, created_at);
CREATE INDEX IF NOT EXISTS ontology_proposal_status_idx
  ON platform.ontology_proposal (status);

-- Same hash-chain idea as platform.fact_event (S9/S10), one chain for T-Box.
CREATE TABLE IF NOT EXISTS platform.ontology_event (
  event_id     bigserial PRIMARY KEY,
  version_id   text NOT NULL,
  proposal_id  text,
  action       text NOT NULL,
  actor        text,
  reason       text,
  payload      jsonb NOT NULL DEFAULT '{}'::jsonb,
  prev_event   bigint,
  hash         char(64),
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ontology_event_version_idx
  ON platform.ontology_event (version_id, event_id);
