-- V16: G-03 SHACL shapes deployment registry (versioned, queryable)
CREATE TABLE IF NOT EXISTS platform.shapes_registry (
  shapes_id      text NOT NULL,
  namespace      text NOT NULL,
  version        text NOT NULL,
  content_hash   char(64) NOT NULL,
  triple_count   bigint NOT NULL CHECK (triple_count >= 0),
  content        text NOT NULL,
  content_format text NOT NULL DEFAULT 'turtle',
  source         text NOT NULL DEFAULT 'api',
  actor          text NOT NULL DEFAULT 'operator',
  created_at     timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (shapes_id, version)
);

CREATE INDEX IF NOT EXISTS shapes_registry_namespace_idx
  ON platform.shapes_registry (namespace, created_at DESC);
