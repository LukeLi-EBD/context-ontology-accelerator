"""B-02 PROV-O judgement provenance.

Every judgement action becomes one ``prov:Activity``; its conclusion and the
text it relied on become ``prov:Entity`` nodes; the human/system behind it is a
``prov:Agent``. Relations are ``prov:used`` / ``prov:wasGeneratedBy`` /
``prov:wasDerivedFrom`` / ``prov:wasAttributedTo``.

Two stores, deliberately separated:

* ``platform.prov_event``: append-only hash chain (same canonical-body +
  ``prev_hash`` + sha256 rule as ``fact_event``/``ontology_event``). Reverse
  queries are answered from here; ``/ontology/verify`` returns this chain as a
  sibling block.
* ``urn:platform:prov``: the only RDF graph this module writes to. T-Box
  (``urn:platform:graph:tbox:*``) and fact A-Box graphs are never touched, and
  ``assert_graph`` rejects any other target with ``E_PROV_GRAPH_MIXING``.

Nothing here updates or deletes an event. A re-judgement creates a new
Activity whose conclusion ``prov:wasDerivedFrom`` the previous conclusion.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from psycopg.types.json import Jsonb
from rdflib import Literal, XSD

from .errors import PortError
from .facts import event_hash

PROV = "http://www.w3.org/ns/prov#"
PROV_GRAPH = "urn:platform:prov"
NS = "urn:platform:prov:"
TBOX_PREFIX = "urn:platform:graph:tbox:"
FSLDM = "https://w3id.org/fsldm/"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"

APPEND_ONLY = "E_PROV_APPEND_ONLY"
GRAPH_MIXING = "E_PROV_GRAPH_MIXING"
NOT_FOUND = "E_PROV_NOT_FOUND"
SUBJECT_NOT_FOUND = "E_PROV_SUBJECT_NOT_FOUND"
LOOKUP_REQUIRED = "E_PROV_LOOKUP_REQUIRED"

KINDS = ("decision", "rule_trigger", "refusal")
_DECISION_BOOK = "_design/37-指标口径判定书-v8.md"


def _err(code: str, message: str, **details: Any) -> PortError:
    http = {
        APPEND_ONLY: "PolicyRejected",
        GRAPH_MIXING: "PolicyRejected",
        NOT_FOUND: "NotFound",
        SUBJECT_NOT_FOUND: "NotFound",
        LOOKUP_REQUIRED: "InvalidArgument",
    }[code]
    return PortError(
        code=http,
        message=message,
        provider="platform",
        provider_code=code,
        details=details,
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str,
                      separators=(",", ":"))


def _iri(value: str) -> str:
    return f"<{value}>"


def _lit(value: Any) -> str:
    return Literal(str(value)).n3()


def _dt(value: str) -> str:
    return Literal(value, datatype=XSD.dateTime).n3()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "unknown"


def agent_iri(actor: str) -> str:
    return f"{NS}agent/{_slug(actor)}"


def activity_iri(activity_id: str) -> str:
    return f"{NS}activity/{activity_id}"


def conclusion_iri(activity_id: str) -> str:
    return f"{NS}conclusion/{activity_id}"


def evidence_iri(entry: dict[str, Any]) -> str:
    digest = hashlib.sha256(
        _json(
            {
                "kind": entry.get("kind"),
                "ref": entry.get("ref"),
                "text": entry.get("text"),
            }
        ).encode("utf-8")
    ).hexdigest()[:16]
    return f"{NS}evidence/{digest}"


def actor_kind(actor: str) -> str:
    probes = ("system", "svc", "robot", "agent", "engine", "executor", "pipeline")
    return "system" if any(p in actor.lower() for p in probes) else "human"


def event_body(
    event_id: int,
    activity_id: str,
    kind: str,
    metric_id: str | None,
    subject_key: str,
    actor: str,
    kind_actor: str,
    conclusion: dict[str, Any],
    evidence: list[dict[str, Any]],
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Canonical body: timestamps excluded, exactly like fact_event."""
    return {
        "eventId": int(event_id),
        "activityId": activity_id,
        "kind": kind,
        "metricId": metric_id,
        "subjectKey": subject_key,
        "actor": actor,
        "actorKind": kind_actor,
        "conclusion": conclusion or {},
        "evidence": evidence or [],
        "payload": payload or {},
    }


def _triples(
    *,
    activity_id: str,
    kind: str,
    actor: str,
    kind_actor: str,
    started: str,
    ended: str,
    subject_iris: list[str],
    evidence: list[dict[str, Any]],
    conclusion: dict[str, Any],
    derived_from: str | None,
) -> list[str]:
    act = activity_iri(activity_id)
    conc = conclusion_iri(activity_id)
    agent = agent_iri(actor)
    triples = [
        f"{_iri(act)} a <{PROV}Activity>",
        f"{_iri(act)} <{PROV}startedAtTime> {_dt(started)}",
        f"{_iri(act)} <{PROV}endedAtTime> {_dt(ended)}",
        f"{_iri(act)} <{PROV}wasAssociatedWith> {_iri(agent)}",
        f"{_iri(act)} <{PROV}generated> {_iri(conc)}",
        f"{_iri(act)} <{PROV}type> {_iri(NS + 'term/' + kind)}",
        f"{_iri(act)} <{RDFS}label> {_lit(kind + ' ' + str(conclusion.get('subject') or '') )}",
        f"{_iri(conc)} a <{PROV}Entity>",
        f"{_iri(conc)} <{PROV}value> {_lit(_json(conclusion))}",
        f"{_iri(conc)} <{PROV}wasGeneratedBy> {_iri(act)}",
        f"{_iri(conc)} <{PROV}wasAttributedTo> {_iri(agent)}",
        f"{_iri(agent)} a <{PROV}Agent>",
        (
            f"{_iri(agent)} <{PROV}type> <{PROV}SoftwareAgent>"
            if kind_actor == "system"
            else f"{_iri(agent)} <{PROV}type> <{PROV}Person>"
        ),
        f"{_iri(agent)} <{RDFS}label> {_lit(actor)}",
    ]
    for subject in subject_iris:
        triples.append(f"{_iri(act)} <{PROV}used> {_iri(subject)}")
        triples.append(f"{_iri(subject)} a <{PROV}Entity>")
    for entry in evidence:
        ev = evidence_iri(entry)
        triples.append(f"{_iri(act)} <{PROV}used> {_iri(ev)}")
        triples.append(f"{_iri(ev)} a <{PROV}Entity>")
        triples.append(f"{_iri(ev)} <{PROV}type> {_iri(NS + 'term/evidence')}")
        triples.append(f"{_iri(ev)} <{RDFS}label> {_lit(str(entry.get('kind') or 'evidence'))}")
        if entry.get("ref"):
            triples.append(f"{_iri(ev)} <{RDFS}seeAlso> {_lit(str(entry['ref']))}")
        triples.append(f"{_iri(ev)} <{PROV}value> {_lit(str(entry.get('text') or ''))}")
    if derived_from:
        triples.append(f"{_iri(conc)} <{PROV}wasDerivedFrom> {_iri(derived_from)}")
    return triples


class ProvService:
    port = "ProvLedger"

    def __init__(self, metadata: Any, graph: Any) -> None:
        self._meta = metadata
        self._graph = graph

    # ---- guards ---------------------------------------------------------

    def assert_graph(self, graph_iri: str) -> None:
        """Only the dedicated PROV graph may be written; anything else is mixing."""
        if graph_iri != PROV_GRAPH:
            raise _err(
                GRAPH_MIXING,
                f"PROV writes are confined to <{PROV_GRAPH}>",
                graph=graph_iri,
                allowed=[PROV_GRAPH],
            )

    def guard(self, graph_iri: str | None) -> dict[str, Any]:
        target = graph_iri or PROV_GRAPH
        self.assert_graph(target)
        return {"graph": target, "allowed": True, "allowedGraphs": [PROV_GRAPH]}

    def write_triples(self, graph_iri: str, triples: list[str]) -> int:
        self.assert_graph(graph_iri)
        if not triples:
            return 0
        body = "\n".join(f"{triple} ." for triple in triples)
        self._graph.update(f"INSERT DATA {{\nGRAPH <{PROV_GRAPH}> {{\n{body}\n}}\n}}")
        return len(triples)

    def refuse_delete(self, activity_id: str) -> None:
        raise _err(
            APPEND_ONLY,
            "PROV events are append-only; physical delete refused",
            activityId=activity_id,
            howToFix="issue a new judgement activity; it will derive from the previous one",
        )

    # ---- append ---------------------------------------------------------

    def _append(
        self,
        *,
        activity_id: str,
        kind: str,
        metric_id: str | None,
        subject_key: str,
        actor: str,
        kind_actor: str,
        conclusion: dict[str, Any],
        evidence: list[dict[str, Any]],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        with self._meta.tx() as tx:
            tx.execute("SELECT pg_advisory_xact_lock(hashtext('platform:prov:event'))")
            last = tx.query(
                "SELECT event_id, hash FROM platform.prov_event "
                "ORDER BY event_id DESC LIMIT 1"
            )
            prev_id = int(last[0]["event_id"]) if last else None
            prev_hash = last[0]["hash"] if last else ""
            rows = tx.execute_returning(
                """
                INSERT INTO platform.prov_event
                  (activity_id, kind, metric_id, subject_key, actor, actor_kind,
                   conclusion, evidence, payload, prev_event)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING event_id
                """,
                (
                    activity_id, kind, metric_id, subject_key, actor, kind_actor,
                    Jsonb(conclusion), Jsonb(evidence), Jsonb(payload), prev_id,
                ),
            )
            event_id = int(rows[0]["event_id"])
            body = event_body(
                event_id, activity_id, kind, metric_id, subject_key, actor,
                kind_actor, conclusion, evidence, payload,
            )
            digest = event_hash(prev_hash, body)
            tx.execute(
                "UPDATE platform.prov_event SET hash = %s WHERE event_id = %s",
                (digest, event_id),
            )
        return {
            "eventId": event_id,
            "activityId": activity_id,
            "activityIri": activity_iri(activity_id),
            "conclusionIri": conclusion_iri(activity_id),
            "graph": PROV_GRAPH,
            "hash": digest,
            "prevEvent": prev_id,
        }

    # ---- records --------------------------------------------------------

    def member(self) -> dict[str, Any]:
        return {
            "port": self.port,
            "graph": PROV_GRAPH,
            "kinds": list(KINDS),
            "appendOnly": True,
        }

    def record_decision(
        self,
        metric_id: str,
        *,
        actor: str = "system:answer-engine",
        reason: str | None = None,
        request_id: str | None = None,
        kind_actor: str | None = None,
    ) -> dict[str, Any]:
        rows = self._meta.query(
            """
            SELECT metric_id, name_zh, definition_version, publishable, inference,
                   decision_recommendation, decision_owner, evidence_basis,
                   formula_text, definition, formula_expr, output_mode,
                   metric_kind, computability_tier
              FROM platform.metric_definition WHERE metric_id = %s
            """,
            (metric_id,),
        )
        if not rows:
            raise _err(
                SUBJECT_NOT_FOUND, f"unknown metric: {metric_id}", metricId=metric_id
            )
        row = rows[0]
        previous = self._latest("decision", metric_id)
        before = (previous or {}).get("conclusion")
        recommendation = row["decision_recommendation"] or {}
        evidence: list[dict[str, Any]] = []
        definition_text = (
            row.get("formula_text") or row.get("definition") or row.get("formula_expr") or ""
        )
        if definition_text:
            evidence.append(
                {
                    "kind": "metric-definition",
                    "ref": f"platform.metric_definition#{metric_id}@{row['definition_version']}",
                    "text": str(definition_text),
                }
            )
        evidence.append(
            {
                "kind": "decision-book",
                "ref": f"{_DECISION_BOOK}#{metric_id}",
                "text": str(
                    recommendation.get("reason")
                    or recommendation.get("status")
                    or f"{metric_id} 判定书条目"
                ),
            }
        )
        if recommendation.get("impact"):
            evidence.append(
                {
                    "kind": "decision-impact",
                    "ref": f"platform.metric_definition.decision_recommendation#{metric_id}.impact",
                    "text": str(recommendation["impact"]),
                }
            )
        conclusion = {
            "subject": metric_id,
            "metricId": metric_id,
            "definitionVersion": row["definition_version"],
            "publishable": bool(row["publishable"]),
            "inference": bool(row["inference"]),
            "decisionRecommendation": recommendation,
            "decisionOwner": row["decision_owner"],
            "evidenceBasis": row["evidence_basis"],
            "outputMode": row["output_mode"],
            "metricKind": row["metric_kind"],
            "computabilityTier": row["computability_tier"],
        }
        activity_id = f"act-{uuid.uuid4().hex[:16]}"
        started = _now()
        triples = _triples(
            activity_id=activity_id,
            kind="decision",
            actor=actor,
            kind_actor=kind_actor or actor_kind(actor),
            started=started,
            ended=_now(),
            subject_iris=[f"urn:platform:metric/{metric_id}"],
            evidence=evidence,
            conclusion=conclusion,
            derived_from=(previous or {}).get("conclusionIri"),
        )
        self.write_triples(PROV_GRAPH, triples)
        payload = {
            "reason": reason,
            "requestId": request_id,
            "before": before,
            "derivedFrom": (previous or {}).get("conclusionIri"),
            "evidence": evidence,
        }
        record = self._append(
            activity_id=activity_id,
            kind="decision",
            metric_id=metric_id,
            subject_key=metric_id,
            actor=actor,
            kind_actor=kind_actor or actor_kind(actor),
            conclusion=conclusion,
            evidence=evidence,
            payload=payload,
        )
        return {
            **record,
            "kind": "decision",
            "metricId": metric_id,
            "actor": actor,
            "actorKind": kind_actor or actor_kind(actor),
            "at": started,
            "conclusion": conclusion,
            "before": before,
            "evidence": evidence,
            "derivedFrom": (previous or {}).get("conclusionIri"),
        }

    def record_rule_execution(
        self,
        metric_id: str,
        result: dict[str, Any],
        *,
        actor: str = "system:rule-executor",
        reason: str | None = None,
        request_id: str | None = None,
        kind_actor: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = self._meta.query(
            "SELECT rule_set_json, definition_version, name_zh "
            "FROM platform.metric_definition WHERE metric_id = %s",
            (metric_id,),
        )
        if not rows:
            raise _err(
                SUBJECT_NOT_FOUND, f"unknown metric: {metric_id}", metricId=metric_id
            )
        rules = {
            str(rule.get("id")): rule
            for rule in (rows[0]["rule_set_json"] or [])
            if isinstance(rule, dict)
        }
        version = rows[0]["definition_version"]
        written: list[dict[str, Any]] = []
        for hit in result.get("hits") or []:
            rule_id = str(hit.get("ruleId") or "")
            rule = rules.get(rule_id) or {}
            spec = rule.get("spec") or {}
            evidence = [
                {
                    "kind": "rule-spec",
                    "ref": f"platform.metric_definition#{metric_id}@{version}.rule_set_json.{rule_id}.spec",
                    "text": _json(spec),
                },
                {
                    "kind": "rule-threshold",
                    "ref": f"platform.metric_definition#{metric_id}@{version}.rule_set_json.{rule_id}.threshold",
                    "text": str(rule.get("threshold") or ""),
                },
                {
                    "kind": "observed-values",
                    "ref": (
                        f"{request_id or 'rule-run'}#customer={hit.get('customerId')}"
                    ),
                    "text": _json(hit.get("fields") or {}),
                },
            ]
            if rule.get("threshold_source"):
                evidence.append(
                    {
                        "kind": "threshold-source",
                        "ref": f"platform.metric_definition#{metric_id}@{version}.rule_set_json.{rule_id}.threshold_source",
                        "text": (
                            f"threshold_source={rule.get('threshold_source')}; "
                            f"evidence_basis={rule.get('evidence_basis')}"
                        ),
                    }
                )
            conclusion = {
                "subject": f"{metric_id}#{rule_id}",
                "metricId": metric_id,
                "definitionVersion": version,
                "ruleId": rule_id,
                "level": hit.get("level") or rule.get("level"),
                "signal": hit.get("signal") or rule.get("signal"),
                "threshold": rule.get("threshold"),
                "spec": spec,
                "customerId": hit.get("customerId"),
                "observed": hit.get("fields") or {},
                "asOf": result.get("asOf"),
            }
            activity_id = f"act-{uuid.uuid4().hex[:16]}"
            started = _now()
            triples = _triples(
                activity_id=activity_id,
                kind="rule_trigger",
                actor=actor,
                kind_actor=kind_actor or actor_kind(actor),
                started=started,
                ended=_now(),
                subject_iris=[
                    f"urn:platform:metric/{metric_id}",
                    f"urn:platform:customer/{hit.get('customerId')}",
                ],
                evidence=evidence,
                conclusion=conclusion,
                derived_from=evidence_iri(evidence[2]),
            )
            self.write_triples(PROV_GRAPH, triples)
            record = self._append(
                activity_id=activity_id,
                kind="rule_trigger",
                metric_id=metric_id,
                subject_key=rule_id,
                actor=actor,
                kind_actor=kind_actor or actor_kind(actor),
                conclusion=conclusion,
                evidence=evidence,
                payload={
                    "reason": reason,
                    "requestId": request_id,
                    "metricId": metric_id,
                    "ruleId": rule_id,
                    "evidence": evidence,
                },
            )
            written.append(
                {
                    **record,
                    "kind": "rule_trigger",
                    "metricId": metric_id,
                    "ruleId": rule_id,
                    "actor": actor,
                    "actorKind": kind_actor or actor_kind(actor),
                    "at": started,
                    "conclusion": conclusion,
                    "evidence": evidence,
                }
            )
        return written

    def record_refusal(
        self,
        *,
        query: str,
        coverage: dict[str, Any],
        retrieve: dict[str, Any] | None = None,
        request_id: str | None = None,
        actor: str = "system:answer-engine",
        strategy: str | None = None,
        top_k: int | None = None,
        kind_actor: str | None = None,
    ) -> dict[str, Any]:
        request_id = request_id or f"req-{uuid.uuid4().hex[:12]}"
        missing = list(coverage.get("missing") or [])
        layers = [
            item.get("layer")
            for item in coverage.get("layers") or []
            if item.get("status") in ("missing", "degraded", "unavailable")
        ]
        evidence = [
            {
                "kind": "answer-gap",
                "ref": f"answerable.missing#{item.get('layer')}/{item.get('code')}",
                "text": str(item.get("what") or item.get("text") or item.get("code") or ""),
            }
            for item in missing
        ] or [
            {
                "kind": "answer-gap",
                "ref": "answerable.missing#none",
                "text": "coverage gate refused without a typed gap",
            }
        ]
        retrieval = {
            "query": query,
            "strategy": strategy,
            "topK": top_k,
            "chunks": (retrieve or {}).get("chunks"),
            "facts": (retrieve or {}).get("facts"),
            "packId": (retrieve or {}).get("packId"),
        }
        conclusion = {
            "subject": request_id,
            "requestId": request_id,
            "query": query,
            "refused": bool(coverage.get("refused")),
            "reasonCode": coverage.get("reasonCode"),
            "missing": missing,
            "layers": layers,
            "retrieval": retrieval,
        }
        activity_id = f"act-{uuid.uuid4().hex[:16]}"
        started = _now()
        triples = _triples(
            activity_id=activity_id,
            kind="refusal",
            actor=actor,
            kind_actor=kind_actor or actor_kind(actor),
            started=started,
            ended=_now(),
            subject_iris=[f"urn:platform:request/{request_id}"],
            evidence=evidence,
            conclusion=conclusion,
            derived_from=None,
        )
        self.write_triples(PROV_GRAPH, triples)
        record = self._append(
            activity_id=activity_id,
            kind="refusal",
            metric_id=None,
            subject_key=request_id,
            actor=actor,
            kind_actor=kind_actor or actor_kind(actor),
            conclusion=conclusion,
            evidence=evidence,
            payload={
                "requestId": request_id,
                "query": query,
                "request": retrieval,
                "evidence": evidence,
            },
        )
        return {
            **record,
            "kind": "refusal",
            "requestId": request_id,
            "actor": actor,
            "actorKind": kind_actor or actor_kind(actor),
            "at": started,
            "conclusion": conclusion,
            "missing": missing,
            "evidence": evidence,
        }

    # ---- reverse queries ------------------------------------------------

    def _latest(self, kind: str, subject_key: str) -> dict[str, Any] | None:
        rows = self._meta.query(
            "SELECT * FROM platform.prov_event WHERE kind = %s AND subject_key = %s "
            "ORDER BY event_id DESC LIMIT 1",
            (kind, subject_key),
        )
        return self._item(rows[0]) if rows else None

    def _item(self, row: dict[str, Any]) -> dict[str, Any]:
        payload = row["payload"] or {}
        return {
            "eventId": int(row["event_id"]),
            "activityId": row["activity_id"],
            "activityIri": activity_iri(row["activity_id"]),
            "conclusionIri": conclusion_iri(row["activity_id"]),
            "kind": row["kind"],
            "metricId": row["metric_id"],
            "subjectKey": row["subject_key"],
            "actor": row["actor"],
            "actorKind": row["actor_kind"],
            "at": row["created_at"].isoformat(),
            "evidence": row["evidence"] or [],
            "conclusion": row["conclusion"] or {},
            "before": payload.get("before"),
            "derivedFrom": payload.get("derivedFrom"),
            "request": payload.get("request"),
            "reason": payload.get("reason"),
            "prevEvent": int(row["prev_event"]) if row["prev_event"] else None,
            "hash": row["hash"],
            "graph": PROV_GRAPH,
        }

    def decision_history(self, metric_id: str, limit: int = 50) -> dict[str, Any]:
        exists = self._meta.query(
            "SELECT 1 AS ok FROM platform.metric_definition WHERE metric_id = %s",
            (metric_id,),
        )
        if not exists:
            raise _err(
                SUBJECT_NOT_FOUND, f"unknown metric: {metric_id}", metricId=metric_id
            )
        rows = self._meta.query(
            "SELECT * FROM platform.prov_event WHERE kind = 'decision' "
            "AND subject_key = %s ORDER BY event_id DESC LIMIT %s",
            (metric_id, limit),
        )
        return {
            "metricId": metric_id,
            "items": [self._item(row) for row in rows],
            "count": len(rows),
            "graph": PROV_GRAPH,
        }

    def rule_triggers(self, rule_id: str, limit: int = 50) -> dict[str, Any]:
        rows = self._meta.query(
            "SELECT * FROM platform.prov_event WHERE kind = 'rule_trigger' "
            "AND subject_key = %s ORDER BY event_id DESC LIMIT %s",
            (rule_id, limit),
        )
        return {
            "ruleId": rule_id,
            "items": [self._item(row) for row in rows],
            "count": len(rows),
            "graph": PROV_GRAPH,
        }

    def refusal(
        self,
        *,
        request_id: str | None = None,
        query: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        if request_id:
            rows = self._meta.query(
                "SELECT * FROM platform.prov_event WHERE kind = 'refusal' "
                "AND subject_key = %s ORDER BY event_id DESC LIMIT %s",
                (request_id, limit),
            )
        elif query:
            rows = self._meta.query(
                "SELECT * FROM platform.prov_event WHERE kind = 'refusal' "
                "AND payload->>'query' = %s ORDER BY event_id DESC LIMIT %s",
                (query, limit),
            )
        else:
            raise _err(
                LOOKUP_REQUIRED,
                "refusal lookup requires requestId or query",
                fields=["requestId", "query"],
            )
        if not rows:
            raise _err(
                NOT_FOUND,
                "no refusal judgement matches the lookup",
                requestId=request_id,
                query=query,
            )
        return {
            "requestId": request_id or rows[0]["subject_key"],
            "query": query,
            "items": [self._item(row) for row in rows],
            "count": len(rows),
            "graph": PROV_GRAPH,
        }

    # ---- audit ----------------------------------------------------------

    def verify(self) -> dict[str, Any]:
        rows = self._meta.query("SELECT * FROM platform.prov_event ORDER BY event_id")
        prev_id: int | None = None
        prev_hash = ""
        checked = 0
        for index, row in enumerate(rows):
            event_id = int(row["event_id"])
            if index and int(row["prev_event"] or 0) != prev_id:
                return {
                    "ok": False,
                    "checked": index,
                    "error": (
                        f"event {event_id} prevEvent={row['prev_event']} "
                        f"expected={prev_id}"
                    ),
                    "graph": PROV_GRAPH,
                }
            body = event_body(
                event_id, row["activity_id"], row["kind"], row["metric_id"],
                row["subject_key"], row["actor"], row["actor_kind"],
                row["conclusion"] or {}, row["evidence"] or [],
                row["payload"] or {},
            )
            digest = event_hash(prev_hash, body)
            if digest != row["hash"]:
                return {
                    "ok": False,
                    "checked": index,
                    "error": f"event {event_id} hash mismatch",
                    "graph": PROV_GRAPH,
                }
            prev_id = event_id
            prev_hash = digest
            checked += 1
        return {
            "ok": True,
            "checked": checked,
            "error": None,
            "lastHash": prev_hash or None,
            "graph": PROV_GRAPH,
        }

    def _tbox_graph(self) -> str | None:
        rows = self._meta.query(
            """
            SELECT v.graph_iri
              FROM platform.graph_pointer p
              JOIN platform.ontology_version v ON v.version_id = p.version_id
             WHERE p.name = 'tbox/current'
            """
        )
        return rows[0]["graph_iri"] if rows else None

    def separation(self) -> dict[str, Any]:
        """Zero-mixing in both directions.

        T-Box already carries ``prov:`` predicates for ontology-entry source
        provenance (subjects under ``https://w3id.org/fsldm/terms#``). That is
        pre-existing, immutable T-Box content, not judgement provenance. The
        assertion here is therefore: no judgement PROV node (subject under
        ``urn:platform:prov:``) lives in the T-Box graph, and no T-Box subject
        lives in the PROV graph. The legacy predicate count is reported for
        transparency and does not fail the gate.
        """
        tbox = self._tbox_graph()
        prov_count = self._graph.count_graph(PROV_GRAPH)
        tbox_prov = 0
        tbox_legacy = 0
        prov_foreign = 0
        if tbox:
            tbox_prov = self._count(
                f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{tbox}> {{ ?s ?p ?o . "
                f'FILTER(STRSTARTS(STR(?s), "{NS}")) }} }}'
            )
            tbox_legacy = self._count(
                f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{tbox}> {{ ?s ?p ?o . "
                f'FILTER(STRSTARTS(STR(?p), "{PROV}")) }} }}'
            )
        prov_foreign = self._count(
            f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{PROV_GRAPH}> {{ ?s ?p ?o . "
            f'FILTER(STRSTARTS(STR(?s), "{FSLDM}") || '
            f'STRSTARTS(STR(?s), "{TBOX_PREFIX}") || '
            f'STRSTARTS(STR(?p), "{FSLDM}")) }} }}'
        )
        return {
            "ok": tbox_prov == 0 and prov_foreign == 0,
            "provGraph": PROV_GRAPH,
            "tboxGraph": tbox,
            "provTriples": prov_count,
            "tboxProvTriples": tbox_prov,
            "provTboxTriples": prov_foreign,
            "tboxLegacyProvPredicateTriples": tbox_legacy,
        }

    def _count(self, sparql: str) -> int:
        payload = self._graph.query(sparql)
        bindings = payload.get("bindings") or []
        if not bindings:
            return 0
        return int(bindings[0]["values"]["n"]["value"])
