-- V3: S2 document ingest. Only tables this slice needs.
CREATE TABLE IF NOT EXISTS platform.document (
  document_id    char(64) PRIMARY KEY,          -- canonical id = sha256 of the source bytes
  sha256         char(64) NOT NULL UNIQUE,
  bucket         text NOT NULL,
  object_key     text NOT NULL,
  filename       text NOT NULL,
  mime_type      text NOT NULL,
  size_bytes     bigint NOT NULL CHECK (size_bytes >= 0),
  status         text NOT NULL CHECK (status IN ('parsed', 'degraded')),
  page_count     integer NOT NULL DEFAULT 0 CHECK (page_count >= 0),
  char_count     bigint NOT NULL DEFAULT 0 CHECK (char_count >= 0),
  chunk_count    integer NOT NULL DEFAULT 0 CHECK (chunk_count >= 0),
  parser         text NOT NULL,
  parser_version text NOT NULL,
  warnings       jsonb NOT NULL DEFAULT '[]'::jsonb,
  manifest       jsonb NOT NULL DEFAULT '{}'::jsonb,
  metadata       jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at     timestamptz NOT NULL DEFAULT now(),
  parsed_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS document_created_idx
  ON platform.document (created_at DESC);

CREATE TABLE IF NOT EXISTS platform.document_page (
  document_id char(64) NOT NULL REFERENCES platform.document(document_id) ON DELETE CASCADE,
  page_number integer NOT NULL CHECK (page_number >= 1),
  text        text NOT NULL,
  char_count  integer NOT NULL CHECK (char_count >= 0),
  PRIMARY KEY (document_id, page_number)
);

CREATE TABLE IF NOT EXISTS platform.document_chunk (
  chunk_id       text PRIMARY KEY,
  document_id    char(64) NOT NULL REFERENCES platform.document(document_id) ON DELETE CASCADE,
  seq            integer NOT NULL CHECK (seq >= 0),
  page_from      integer NOT NULL CHECK (page_from >= 1),
  page_to        integer NOT NULL CHECK (page_to >= 1),
  char_start     integer NOT NULL CHECK (char_start >= 0),
  char_end       integer NOT NULL CHECK (char_end >= 0),
  text           text NOT NULL,
  token_estimate integer NOT NULL CHECK (token_estimate >= 1),
  created_at     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (document_id, seq)
);

CREATE INDEX IF NOT EXISTS document_chunk_document_idx
  ON platform.document_chunk (document_id, seq);
