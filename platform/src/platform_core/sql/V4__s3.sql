-- V4: S3 retrieval. Vector (pgvector) + lexical (FTS + pg_trgm) indexes.
-- Note: the migration runner splits statements on semicolons, so comments must
-- not contain semicolons.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Generated column keeps tokenization inside PostgreSQL (D18), plus a GIN index.
ALTER TABLE platform.document_chunk
  ADD COLUMN IF NOT EXISTS text_search tsvector
  GENERATED ALWAYS AS (to_tsvector('simple', text)) STORED;

CREATE INDEX IF NOT EXISTS document_chunk_text_search_idx
  ON platform.document_chunk USING gin (text_search);

-- pg_trgm covers Chinese text where the `simple` parser has no word segmentation.
CREATE INDEX IF NOT EXISTS document_chunk_text_trgm_idx
  ON platform.document_chunk USING gin (text gin_trgm_ops);

CREATE TABLE IF NOT EXISTS platform.chunk_embedding (
  chunk_id   text NOT NULL REFERENCES platform.document_chunk(chunk_id) ON DELETE CASCADE,
  model      text NOT NULL,
  dimensions integer NOT NULL CHECK (dimensions > 0),
  embedding  vector(1024) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chunk_id, model)
);

CREATE INDEX IF NOT EXISTS chunk_embedding_model_idx
  ON platform.chunk_embedding (model);

CREATE INDEX IF NOT EXISTS chunk_embedding_hnsw
  ON platform.chunk_embedding USING hnsw (embedding vector_cosine_ops);
