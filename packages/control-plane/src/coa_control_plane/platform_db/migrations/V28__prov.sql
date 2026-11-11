-- V28: B-02 PROV-O judgement provenance.
--
-- Three judgement kinds share one append-only, hash-chained ledger:
--   decision     口径判定 (decision_recommendation / inference / publishable)
--   rule_trigger 规则触发 (rule id, threshold, spec field, observed value)
--   refusal      拒答 (which layer/item is missing + retrieval parameters)
--
-- The RDF representation lives in the dedicated named graph
-- ``urn:platform:prov``. This table is the query/audit surface; it never
-- stores T-Box or fact A-Box content.
--
-- Append-only is enforced physically: the trigger refuses DELETE, and refuses
-- UPDATE of every field except ``hash`` (the chain writer sets that once, in
-- the same transaction as the INSERT).

CREATE TABLE IF NOT EXISTS platform.prov_event (
  event_id    bigserial PRIMARY KEY,
  activity_id text NOT NULL,
  kind        text NOT NULL,
  metric_id   text,
  subject_key text NOT NULL,
  actor       text NOT NULL,
  actor_kind  text NOT NULL,
  conclusion  jsonb NOT NULL DEFAULT '{}'::jsonb,
  evidence    jsonb NOT NULL DEFAULT '[]'::jsonb,
  payload     jsonb NOT NULL DEFAULT '{}'::jsonb,
  prev_event  bigint,
  hash        text NOT NULL DEFAULT '',
  created_at  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT prov_event_kind_ck CHECK (kind IN ('decision', 'rule_trigger', 'refusal')),
  CONSTRAINT prov_event_actor_kind_ck CHECK (actor_kind IN ('human', 'system'))
);

CREATE UNIQUE INDEX IF NOT EXISTS prov_event_activity_uk
  ON platform.prov_event (activity_id);

CREATE INDEX IF NOT EXISTS prov_event_subject_idx
  ON platform.prov_event (kind, subject_key, event_id);

CREATE INDEX IF NOT EXISTS prov_event_metric_idx
  ON platform.prov_event (metric_id, event_id);

COMMENT ON TABLE platform.prov_event IS
  'B-02: append-only PROV-O judgement ledger; hash chain mirrors fact_event';

CREATE OR REPLACE FUNCTION platform.prov_event_append_only() RETURNS trigger AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'platform.prov_event is append-only: physical delete refused';
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF OLD.activity_id IS DISTINCT FROM NEW.activity_id
       OR OLD.kind IS DISTINCT FROM NEW.kind
       OR OLD.metric_id IS DISTINCT FROM NEW.metric_id
       OR OLD.subject_key IS DISTINCT FROM NEW.subject_key
       OR OLD.actor IS DISTINCT FROM NEW.actor
       OR OLD.actor_kind IS DISTINCT FROM NEW.actor_kind
       OR OLD.conclusion IS DISTINCT FROM NEW.conclusion
       OR OLD.evidence IS DISTINCT FROM NEW.evidence
       OR OLD.payload IS DISTINCT FROM NEW.payload
       OR OLD.prev_event IS DISTINCT FROM NEW.prev_event
       OR OLD.created_at IS DISTINCT FROM NEW.created_at THEN
      RAISE EXCEPTION 'platform.prov_event is append-only: mutation refused';
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS prov_event_append_only_trg ON platform.prov_event;
CREATE TRIGGER prov_event_append_only_trg
  BEFORE UPDATE OR DELETE ON platform.prov_event
  FOR EACH ROW EXECUTE FUNCTION platform.prov_event_append_only();
