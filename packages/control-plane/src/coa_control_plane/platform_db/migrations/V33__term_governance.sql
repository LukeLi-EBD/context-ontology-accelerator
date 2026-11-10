-- V33: O-05 term-layer governance registry.
--
-- term_check stores every SKOS coverage/diff check (pass or fail) so the
-- import registration can be audited; term_import stores the token that a new
-- term batch obtains only after a passing diff. Neither table writes to the
-- published graph: the T-Box import path is unchanged.

CREATE TABLE IF NOT EXISTS platform.term_check (
  check_id     text PRIMARY KEY,
  source_kind  text NOT NULL CHECK (source_kind IN ('graph', 'import')),
  version_id   text,
  status       text NOT NULL CHECK (status IN ('pass', 'fail')),
  diff_hash    char(64) NOT NULL,
  report       jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_by   text NOT NULL DEFAULT 'operator',
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS term_check_version_idx
  ON platform.term_check (version_id, created_at);
CREATE INDEX IF NOT EXISTS term_check_status_idx
  ON platform.term_check (status, created_at);

CREATE TABLE IF NOT EXISTS platform.term_import (
  import_id     text PRIMARY KEY,
  source_name   text,
  content_hash  char(64) NOT NULL,
  status        text NOT NULL CHECK (status IN ('checked', 'rejected')),
  diff          jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_by    text NOT NULL DEFAULT 'operator',
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS term_import_hash_idx
  ON platform.term_import (content_hash, created_at);
