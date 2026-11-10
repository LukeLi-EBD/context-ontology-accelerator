-- V14: S14 extraction resume. One row per completed LLM batch so an
-- interrupted extraction continues from the next unfinished batch instead of
-- starting over. Rows are deleted after the document's extraction completes.
CREATE TABLE IF NOT EXISTS platform.extraction_progress (
  document_id       text NOT NULL REFERENCES platform.document(document_id) ON DELETE CASCADE,
  extractor_version text NOT NULL,
  batch_size        integer NOT NULL CHECK (batch_size > 0),
  batch_index       integer NOT NULL CHECK (batch_index >= 0),
  chunk_start       integer NOT NULL CHECK (chunk_start >= 0),
  chunk_end         integer NOT NULL CHECK (chunk_end >= chunk_start),
  candidate_count   integer NOT NULL DEFAULT 0 CHECK (candidate_count >= 0),
  candidates        jsonb NOT NULL DEFAULT '[]'::jsonb,
  status            text NOT NULL DEFAULT 'completed'
                    CHECK (status IN ('completed', 'failed')),
  failure_code      text,
  updated_at        timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (document_id, extractor_version, batch_size, batch_index)
);

CREATE INDEX IF NOT EXISTS extraction_progress_status_idx
  ON platform.extraction_progress (status, updated_at);
