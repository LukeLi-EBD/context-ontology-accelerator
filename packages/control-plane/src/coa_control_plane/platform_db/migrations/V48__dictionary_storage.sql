-- V48: P4 dictionary storage, namespace scoped.
--
-- Originally written as V46. Main advanced to V47 (V47__import_batch_namespace)
-- before this branch merged, and V46 never landed in any database, so the file
-- was renumbered to V48 to keep the registry gapless (see the note in
-- doc/coa-x/11-D组缺口评审.md).
--
-- Two additive tables. The legacy platform.data_dictionary table is left
-- untouched: it has no namespace column and cannot be made multi-tenant
-- without inventing a namespace for its existing rows. COA dictionary reads
-- and writes go to the tables below, keyed by namespace_id.
--
-- namespace_id / source_id are references to the control-plane item store.
-- They are deliberately stored as text without a cross-schema foreign key:
-- namespaces and sources do not live in this database.

CREATE TABLE IF NOT EXISTS platform.dictionary_refresh_run (
    run_id          text        PRIMARY KEY,
    namespace_id    text        NOT NULL CHECK (btrim(namespace_id) <> ''),
    source_id       text        NOT NULL CHECK (btrim(source_id) <> ''),
    idempotency_key text        NOT NULL CHECK (btrim(idempotency_key) <> ''),
    requested_by    text,
    status          text        NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    started_at      timestamptz NOT NULL DEFAULT now(),
    finished_at     timestamptz,
    processed       integer     NOT NULL DEFAULT 0 CHECK (processed >= 0),
    inserted        integer     NOT NULL DEFAULT 0 CHECK (inserted >= 0),
    updated         integer     NOT NULL DEFAULT 0 CHECK (updated >= 0),
    unchanged       integer     NOT NULL DEFAULT 0 CHECK (unchanged >= 0),
    removed         integer     NOT NULL DEFAULT 0 CHECK (removed >= 0),
    error           text,
    CONSTRAINT dictionary_refresh_run_idempotency
        UNIQUE (namespace_id, source_id, idempotency_key),
    CONSTRAINT dictionary_refresh_run_identity
        UNIQUE (namespace_id, source_id, run_id),
    CONSTRAINT dictionary_refresh_run_finish CHECK (
        (status = 'running' AND finished_at IS NULL AND error IS NULL)
        OR (status = 'succeeded' AND finished_at IS NOT NULL AND error IS NULL)
        OR (status = 'failed' AND finished_at IS NOT NULL AND error IS NOT NULL AND btrim(error) <> '')
    )
);

CREATE INDEX IF NOT EXISTS dictionary_refresh_run_source_idx
    ON platform.dictionary_refresh_run (namespace_id, source_id, started_at DESC);

CREATE TABLE IF NOT EXISTS platform.dictionary_column (
    namespace_id   text        NOT NULL CHECK (btrim(namespace_id) <> ''),
    source_id      text        NOT NULL CHECK (btrim(source_id) <> ''),
    catalog_name   text        NOT NULL CHECK (btrim(catalog_name) <> ''),
    schema_name    text        NOT NULL CHECK (btrim(schema_name) <> ''),
    table_name     text        NOT NULL CHECK (btrim(table_name) <> ''),
    column_name    text        NOT NULL CHECK (btrim(column_name) <> ''),
    data_type      text        NOT NULL CHECK (btrim(data_type) <> ''),
    is_nullable    boolean     NOT NULL,
    comment        text,
    source_kind    text        NOT NULL CHECK (source_kind IN (
        'postgresql', 'mysql', 'redshift', 'sqlserver', 'snowflake', 'glue', 'duckdb'
    )),
    property_iri   text,
    binding_method text        NOT NULL DEFAULT 'none'
        CHECK (binding_method IN ('explicit', 'name_match', 'manual', 'none')),
    confidence     numeric(4, 3)
        CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    binding_note   text,
    observed_at    timestamptz NOT NULL DEFAULT now(),
    last_refresh_run_id text   NOT NULL,
    PRIMARY KEY (namespace_id, source_id, catalog_name, schema_name, table_name, column_name),
    CONSTRAINT dictionary_column_run_fk
        FOREIGN KEY (namespace_id, source_id, last_refresh_run_id)
        REFERENCES platform.dictionary_refresh_run (namespace_id, source_id, run_id)
);

CREATE INDEX IF NOT EXISTS dictionary_column_table_idx
    ON platform.dictionary_column (namespace_id, table_name, column_name);

CREATE INDEX IF NOT EXISTS dictionary_column_source_binding_idx
    ON platform.dictionary_column (namespace_id, source_id, source_kind, binding_method);

CREATE INDEX IF NOT EXISTS dictionary_column_missing_comment_idx
    ON platform.dictionary_column (namespace_id)
    WHERE comment IS NULL OR btrim(comment) = '';
