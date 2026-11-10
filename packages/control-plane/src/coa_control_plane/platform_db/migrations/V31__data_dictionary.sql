-- V31: B-06 data dictionary — read-only introspection snapshot of fact tables.
--
-- Re-entrant: CREATE TABLE IF NOT EXISTS plus ADD COLUMN IF NOT EXISTS on every
-- attribute, so a partially created table converges without dropping data.
-- The dictionary is descriptive only: it never feeds publish gates, and
-- property_iri is a binding hint, not an ontology authority.

CREATE TABLE IF NOT EXISTS platform.data_dictionary (
    catalog_name   text        NOT NULL,
    schema_name    text        NOT NULL,
    table_name     text        NOT NULL,
    column_name    text        NOT NULL,
    data_type      text        NOT NULL,
    is_nullable    boolean     NOT NULL DEFAULT true,
    comment        text,
    source_kind    text        NOT NULL CHECK (source_kind IN ('pg', 'mysql', 'glue')),
    property_iri   text,
    binding_method text        NOT NULL DEFAULT 'none'
                                CHECK (binding_method IN ('explicit', 'name_match', 'manual', 'none')),
    confidence     numeric(4,3),
    binding_note   text,
    observed_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (catalog_name, schema_name, table_name, column_name)
);

ALTER TABLE platform.data_dictionary ADD COLUMN IF NOT EXISTS catalog_name text;
ALTER TABLE platform.data_dictionary ADD COLUMN IF NOT EXISTS schema_name text;
ALTER TABLE platform.data_dictionary ADD COLUMN IF NOT EXISTS table_name text;
ALTER TABLE platform.data_dictionary ADD COLUMN IF NOT EXISTS column_name text;
ALTER TABLE platform.data_dictionary ADD COLUMN IF NOT EXISTS data_type text;
ALTER TABLE platform.data_dictionary ADD COLUMN IF NOT EXISTS is_nullable boolean DEFAULT true;
ALTER TABLE platform.data_dictionary ADD COLUMN IF NOT EXISTS comment text;
ALTER TABLE platform.data_dictionary ADD COLUMN IF NOT EXISTS source_kind text;
ALTER TABLE platform.data_dictionary ADD COLUMN IF NOT EXISTS property_iri text;
ALTER TABLE platform.data_dictionary ADD COLUMN IF NOT EXISTS binding_method text DEFAULT 'none';
ALTER TABLE platform.data_dictionary ADD COLUMN IF NOT EXISTS confidence numeric(4,3);
ALTER TABLE platform.data_dictionary ADD COLUMN IF NOT EXISTS binding_note text;
ALTER TABLE platform.data_dictionary ADD COLUMN IF NOT EXISTS observed_at timestamptz DEFAULT now();

CREATE INDEX IF NOT EXISTS data_dictionary_table_idx
    ON platform.data_dictionary (schema_name, table_name);
CREATE INDEX IF NOT EXISTS data_dictionary_binding_idx
    ON platform.data_dictionary (binding_method);
