-- V13: embedding partitions. One row per (chunk, model) already exists, but the
-- column was pinned to vector(1024), so a 2048-dim model could not coexist.
-- This migration frees the dimension, rebuilds per-dimension HNSW indexes, and
-- adds the single-row pointer that selects the active partition.
-- pgvector 0.8.7 caps `vector` HNSW at 2000 dims, so the 2048 partition is
-- indexed as halfvec (max 4000 dims) while 1024 keeps full precision.
-- NOTE: the migration runner splits statements on semicolons, so comments
-- must not contain one.
ALTER TABLE platform.chunk_embedding
  ALTER COLUMN embedding TYPE vector USING embedding::vector;
DROP INDEX IF EXISTS platform.chunk_embedding_hnsw;
CREATE INDEX IF NOT EXISTS chunk_embedding_hnsw_1024
  ON platform.chunk_embedding USING hnsw ((embedding::vector(1024)) vector_cosine_ops)
  WHERE dimensions = 1024;
CREATE INDEX IF NOT EXISTS chunk_embedding_hnsw_2048
  ON platform.chunk_embedding USING hnsw ((embedding::halfvec(2048)) halfvec_cosine_ops)
  WHERE dimensions = 2048;
CREATE TABLE IF NOT EXISTS platform.embedding_pointer (
  id         boolean PRIMARY KEY DEFAULT true CHECK (id),
  provider   text NOT NULL,
  model      text NOT NULL,
  dimensions integer NOT NULL CHECK (dimensions > 0),
  updated_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO platform.embedding_pointer (id, provider, model, dimensions)
VALUES (true, 'local-bge', 'BAAI/bge-m3', 1024)
ON CONFLICT (id) DO NOTHING;
