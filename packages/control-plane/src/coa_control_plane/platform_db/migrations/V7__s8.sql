-- S8 fact governance: assertion ledger + append-only audit events
-- The A-Box graph is a projection of ACTIVE assertions only.
-- NOTE: the migration runner splits on semicolons, so comments must not contain one.

CREATE TABLE IF NOT EXISTS platform.fact_assertion (
    fact_id            text PRIMARY KEY,
    subject_iri        text NOT NULL,
    predicate_iri      text NOT NULL,
    object_kind        text NOT NULL CHECK (object_kind IN ('iri', 'literal')),
    object_value       text NOT NULL,
    graph_iri          text NOT NULL,
    source_kind        text NOT NULL CHECK (source_kind IN ('extraction', 'manual', 'import')),
    source_document_id text,
    source_run_id      text,
    candidate_id       text,
    state              text NOT NULL DEFAULT 'active'
                       CHECK (state IN ('active', 'retracted', 'superseded')),
    asserted_at        timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz NOT NULL DEFAULT now(),
    retracted_at       timestamptz,
    retract_reason     text,
    superseded_by      text
);

CREATE UNIQUE INDEX IF NOT EXISTS fact_assertion_active_unique
    ON platform.fact_assertion (
        subject_iri, predicate_iri, object_value,
        COALESCE(source_document_id, ''), COALESCE(source_run_id, ''), graph_iri
    )
    WHERE state = 'active';

CREATE INDEX IF NOT EXISTS fact_assertion_subject_predicate_idx
    ON platform.fact_assertion (subject_iri, predicate_iri)
    WHERE state = 'active';

CREATE INDEX IF NOT EXISTS fact_assertion_source_document_idx
    ON platform.fact_assertion (source_document_id)
    WHERE state = 'active';

CREATE TABLE IF NOT EXISTS platform.fact_event (
    event_id   bigserial PRIMARY KEY,
    fact_id    text NOT NULL,
    action     text NOT NULL
               CHECK (action IN ('asserted', 'retracted', 'restored', 'batch_retracted')),
    actor      text,
    reason     text,
    batch_id   text,
    payload    jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS fact_event_fact_idx
    ON platform.fact_event (fact_id, created_at DESC);
