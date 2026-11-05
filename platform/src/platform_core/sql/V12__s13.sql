-- V12: S13 bulk import. A batch is keyed by the resolved scan root so re-running
-- the same directory resumes instead of starting over.
CREATE TABLE IF NOT EXISTS platform.import_batch (
  batch_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  root_path  text NOT NULL UNIQUE,
  status     text NOT NULL DEFAULT 'running'
             CHECK (status IN ('running', 'completed', 'interrupted')),
  options    jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz
);

CREATE TABLE IF NOT EXISTS platform.import_item (
  batch_id        uuid NOT NULL REFERENCES platform.import_batch(batch_id) ON DELETE CASCADE,
  rel_path        text NOT NULL,
  size_bytes      bigint NOT NULL CHECK (size_bytes >= 0),
  mtime_ns        bigint,
  sha256          char(64),
  document_id     char(64),
  status          text NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'parsing', 'chunked', 'indexed', 'failed')),
  deduplicated    boolean NOT NULL DEFAULT false,
  degraded        boolean NOT NULL DEFAULT false,
  attempts        integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  failure_code    text,
  failure_message text,
  updated_at      timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (batch_id, rel_path)
);

CREATE INDEX IF NOT EXISTS import_item_status_idx
  ON platform.import_item (batch_id, status);
CREATE INDEX IF NOT EXISTS import_item_sha_idx
  ON platform.import_item (batch_id, sha256);
