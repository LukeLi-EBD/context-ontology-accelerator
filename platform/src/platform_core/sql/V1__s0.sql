-- V1: S0 skeleton. Only tables needed by the current slice (no full schema upfront).
CREATE SCHEMA IF NOT EXISTS platform;

CREATE TABLE IF NOT EXISTS platform.schema_version (
  version      integer PRIMARY KEY,
  description  text NOT NULL,
  applied_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS platform.blob (
  hash             char(64) PRIMARY KEY,
  size             bigint NOT NULL CHECK (size >= 0),
  mime             text NOT NULL DEFAULT 'application/octet-stream',
  tier             text NOT NULL CHECK (tier IN ('pg', 'fs')),
  path             text,
  state            text NOT NULL CHECK (state IN ('staging', 'committed', 'missing', 'deleting')),
  metadata         jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at       timestamptz NOT NULL DEFAULT now(),
  deleted_at       timestamptz,
  refcount         integer NOT NULL DEFAULT 0 CHECK (refcount >= 0),
  last_verified_at timestamptz,
  verified_ok      boolean
);

CREATE TABLE IF NOT EXISTS platform.blob_ref (
  hash        char(64) NOT NULL REFERENCES platform.blob(hash) ON DELETE RESTRICT,
  owner_type  text NOT NULL,
  owner_id    text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (hash, owner_type, owner_id)
);

CREATE INDEX IF NOT EXISTS blob_ref_owner_idx
  ON platform.blob_ref (owner_type, owner_id text_pattern_ops);

CREATE TABLE IF NOT EXISTS platform.blob_bytea (
  hash    char(64) PRIMARY KEY REFERENCES platform.blob(hash) ON DELETE CASCADE,
  content bytea NOT NULL
);
