-- C2-1 daily budget ledger (design 87). SimpleQuota is the only writer.
-- One row per (UTC day, scope); increments are atomic upserts so a process
-- restart never loses the count. cost_units stays 0 in C2-1; C2-2 turns it
-- into money using the configured per-1k-token price.
CREATE TABLE IF NOT EXISTS platform.quota_usage (
    quota_day date NOT NULL,
    scope text NOT NULL,
    tokens bigint NOT NULL DEFAULT 0 CHECK (tokens >= 0),
    requests bigint NOT NULL DEFAULT 0 CHECK (requests >= 0),
    cost_units numeric(18, 6) NOT NULL DEFAULT 0 CHECK (cost_units >= 0),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (quota_day, scope)
);
