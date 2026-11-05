-- V2: S1 ontology storage and versions. Only tables this slice needs.
CREATE TABLE IF NOT EXISTS platform.ontology_version (
  version_id    text PRIMARY KEY,
  semver        text NOT NULL,
  status        text NOT NULL CHECK (status IN ('draft', 'published', 'superseded', 'deprecated', 'rejected')),
  content_hash  char(64) NOT NULL,
  triple_count  bigint NOT NULL CHECK (triple_count >= 0),
  source_format text NOT NULL CHECK (source_format IN ('turtle', 'trig')),
  source_key    text NOT NULL,
  graph_iri     text NOT NULL,
  rollback_of   text REFERENCES platform.ontology_version(version_id),
  label         text,
  created_at    timestamptz NOT NULL DEFAULT now(),
  published_at  timestamptz
);

CREATE INDEX IF NOT EXISTS ontology_version_hash_idx
  ON platform.ontology_version (content_hash);

CREATE INDEX IF NOT EXISTS ontology_version_status_idx
  ON platform.ontology_version (status);

CREATE TABLE IF NOT EXISTS platform.graph_pointer (
  name       text PRIMARY KEY,
  version_id text NOT NULL REFERENCES platform.ontology_version(version_id),
  updated_at timestamptz NOT NULL DEFAULT now(),
  updated_by text NOT NULL DEFAULT 'local'
);

CREATE TABLE IF NOT EXISTS platform.ontology_job (
  job_id      text PRIMARY KEY,
  kind        text NOT NULL,
  status      text NOT NULL CHECK (status IN ('running', 'done', 'failed', 'skipped')),
  detail      jsonb NOT NULL DEFAULT '{}'::jsonb,
  error       text,
  started_at  timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz
);
