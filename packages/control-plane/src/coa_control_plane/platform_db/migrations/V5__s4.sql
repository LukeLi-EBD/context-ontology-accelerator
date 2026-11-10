-- V5: S4 extraction candidates (approval queue).
-- Note: the migration runner splits statements on semicolons.
CREATE TABLE IF NOT EXISTS platform.extraction_candidate (
  candidate_id      text PRIMARY KEY,
  document_id       text NOT NULL REFERENCES platform.document(document_id) ON DELETE CASCADE,
  chunk_id          text NOT NULL REFERENCES platform.document_chunk(chunk_id) ON DELETE CASCADE,
  extractor         text NOT NULL CHECK (extractor IN ('rules', 'llm')),
  extractor_version text NOT NULL,
  subject_iri       text NOT NULL,
  predicate_iri     text NOT NULL,
  object_kind       text NOT NULL CHECK (object_kind IN ('iri', 'literal')),
  object_value      text NOT NULL,
  confidence        real NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  state             text NOT NULL CHECK (state IN ('pending', 'approved', 'rejected')),
  dedupe_key        char(64) NOT NULL UNIQUE,
  evidence          jsonb NOT NULL DEFAULT '{}'::jsonb,
  graph_iri         text,
  created_at        timestamptz NOT NULL DEFAULT now(),
  decided_at        timestamptz,
  reject_reason     text
);

CREATE INDEX IF NOT EXISTS extraction_candidate_state_idx
  ON platform.extraction_candidate (state, created_at);

CREATE INDEX IF NOT EXISTS extraction_candidate_document_idx
  ON platform.extraction_candidate (document_id);
