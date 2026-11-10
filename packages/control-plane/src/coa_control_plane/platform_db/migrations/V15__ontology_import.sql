-- V15: G-01 import records. One row per parsed import attempt that reached
-- persistence. The merged graph lives in a staging graph (never a published
-- T-Box pointer); usable/reason are stored verbatim so the record answers
-- "which version, who, when, and why it was (not) usable" later.
CREATE TABLE IF NOT EXISTS platform.ontology_import (
  import_id         text PRIMARY KEY,
  version_id        text NOT NULL,
  target_namespace  text,
  author            text NOT NULL,
  change_summary    text,
  base_triples      integer NOT NULL CHECK (base_triples >= 0),
  total_triples     integer NOT NULL CHECK (total_triples >= 0),
  classes           integer NOT NULL CHECK (classes >= 0),
  object_properties integer NOT NULL CHECK (object_properties >= 0),
  data_properties   integer NOT NULL CHECK (data_properties >= 0),
  shapes_id         text,
  shapes_version    text,
  conforms          boolean,
  violation_count   integer NOT NULL DEFAULT 0 CHECK (violation_count >= 0),
  usable            boolean NOT NULL,
  reason            text,
  source_sha256     text NOT NULL,
  staging_graph     text NOT NULL,
  payload           jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ontology_import_namespace_idx
  ON platform.ontology_import (target_namespace, created_at DESC);
