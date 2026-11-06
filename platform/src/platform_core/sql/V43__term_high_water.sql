-- O-05 vocab guard: high-water mark of the *effective* term set.
--
-- The guard must survive the future decoupling of the term layer from the
-- T-Box version graph, so it is stored here as a pointer-independent count
-- (and not inferred from the current version graph at check time). Publish
-- only raises the mark; it never lowers it.
CREATE TABLE IF NOT EXISTS platform.term_high_water (
    scope text PRIMARY KEY,
    concepts_in_scheme integer NOT NULL,
    aliases integer NOT NULL,
    version_id text,
    graph_iri text,
    updated_at timestamptz NOT NULL DEFAULT now()
);
