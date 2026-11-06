"""S8 acceptance: A-Box assertion ledger, single/batch retraction, rollback,
conflict visibility, context filtering, re-materialization and append-only audit.

Every fact lives in an isolated ``urn:platform:test:<nonce>:s8`` graph so the
demo A-Box stays pure (OQ-31).
"""

from __future__ import annotations

import uuid
from pathlib import Path

import httpx

from . import termgate
from .assembly import Runtime
from .errors import PortError

RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
LOCATED_IN = "urn:platform:rel:locatedIn"


class _Case:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def check(self, name: str, condition: bool, detail: str = "") -> bool:
        self.results.append((name, bool(condition), detail))
        return bool(condition)

    def fail(self, name: str, detail: str) -> None:
        self.results.append((name, False, detail))


def _tbox(prefix: str) -> str:
    return f"""
@prefix owl: <{OWL}> .
@prefix rdfs: <{RDFS}> .
<urn:platform:smoke:{prefix}:onto> a owl:Ontology .
<urn:platform:smoke:{prefix}:Facility> a owl:Class ; rdfs:label "S8设施{prefix}" .
<urn:platform:smoke:{prefix}:Site> a owl:Class ;
    rdfs:label "S8监测点{prefix}" ;
    rdfs:subClassOf <urn:platform:smoke:{prefix}:Facility> .
<urn:platform:smoke:{prefix}:Region> a owl:Class ; rdfs:label "S8行政区{prefix}" .
<{LOCATED_IN}> a owl:ObjectProperty ;
    rdfs:label "S8位于{prefix}" ;
    rdfs:domain <urn:platform:smoke:{prefix}:Site> ;
    rdfs:range <urn:platform:smoke:{prefix}:Region> .
"""


def _write(tmp_dir: Path, name: str, text: str) -> Path:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    path = tmp_dir / name
    path.write_text(text, encoding="utf-8")
    return path


def run_smoke_s8(runtime: Runtime, base_url: str) -> int:
    suite = _Case()
    base = base_url.rstrip("/")
    tmp_dir = Path(runtime.config.storage.tmp_dir)
    nonce = uuid.uuid4().hex[:8]
    test_graph = f"urn:platform:test:{uuid.uuid4().hex[:10]}:s8"
    site_a = f"urn:platform:smoke:{nonce}:siteA"
    site_b = f"urn:platform:smoke:{nonce}:siteB"
    site_c = f"urn:platform:smoke:{nonce}:siteC"
    region_a = f"urn:platform:smoke:{nonce}:regionA"
    region_x = f"urn:platform:smoke:{nonce}:regionX"
    region_y = f"urn:platform:smoke:{nonce}:regionY"
    site_cls = f"urn:platform:smoke:{nonce}:Site"
    facility_cls = f"urn:platform:smoke:{nonce}:Facility"
    fake_label = f"old-label-{nonce}"
    doc_a = f"doc-a-{nonce}"
    doc_b = f"doc-b-{nonce}"
    doc_c = f"doc-c-{nonce}"
    doc_e = f"doc-e-{nonce}"
    doc_f = f"doc-f-{nonce}"
    inferred: str | None = None
    f1: str | None = None
    cleaned = False

    def ask(triple: str) -> bool:
        return runtime.graph.ask(f"ASK {{ GRAPH <{test_graph}> {{ {triple} }} }}")

    def inferred_ask(triple: str) -> bool:
        return bool(inferred) and runtime.graph.ask(
            f"ASK {{ GRAPH <{inferred}> {{ {triple} }} }}"
        )

    with httpx.Client(base_url=base, timeout=60.0) as client:
        try:
            runtime.metadata.open(retry_seconds=10.0)
            runtime.metadata.migrate()

            # 1. publish a T-Box with subclass + domain/range for entailment
            path = _write(tmp_dir, f"s8-{nonce}.ttl", _tbox(nonce))
            version = runtime.ontology.import_source(
                str(path), "1.0.0", on_conflict="new_version"
            )
            runtime.ontology.publish(
                version["versionId"], acknowledge_breaking=True, purpose="smoke",
                **termgate.smoke_env_context("smoke"),
            )
            inferred = f"urn:platform:inferred:{version['versionId']}"

            # 2. assert six A-Box facts from four different sources
            payloads = [
                {
                    "subject": site_a, "predicate": RDF + "type", "object": site_cls,
                    "graph": test_graph, "sourceKind": "extraction",
                    "sourceDocumentId": doc_a,
                },
                {
                    "subject": site_a, "predicate": LOCATED_IN, "object": region_a,
                    "graph": test_graph, "sourceKind": "extraction",
                    "sourceDocumentId": doc_a,
                },
                {
                    "subject": site_b, "predicate": RDF + "type", "object": site_cls,
                    "graph": test_graph, "sourceKind": "extraction",
                    "sourceDocumentId": doc_b,
                },
                {
                    "subject": site_a, "predicate": RDFS + "label", "object": fake_label,
                    "objectKind": "literal", "graph": test_graph,
                    "sourceKind": "manual", "sourceDocumentId": doc_c,
                },
                {
                    "subject": site_c, "predicate": LOCATED_IN, "object": region_x,
                    "graph": test_graph, "sourceKind": "extraction",
                    "sourceDocumentId": doc_e,
                },
                {
                    "subject": site_c, "predicate": LOCATED_IN, "object": region_y,
                    "graph": test_graph, "sourceKind": "extraction",
                    "sourceDocumentId": doc_f,
                },
            ]
            facts = []
            for payload in payloads:
                response = client.post("/facts", json=payload)
                facts.append(response.json() if response.status_code == 200 else {})
            f1 = facts[0].get("factId")
            f4 = facts[3].get("factId")
            suite.check(
                "facts.assert",
                all(item.get("factId") and item.get("state") == "active" for item in facts)
                and ask(f"<{site_a}> a <{site_cls}>"),
                f"asserted={sum(1 for item in facts if item.get('factId'))}",
            )
            listed = client.get(
                "/facts", params={"state": "active", "subject": site_a, "limit": 50}
            ).json()
            suite.check(
                "facts.list.active",
                any(item["factId"] == f1 for item in listed.get("items", []))
                and any(item["source"]["documentId"] == doc_c for item in listed.get("items", [])),
                f"items={len(listed.get('items', []))}",
            )

            # 3. materialize before retraction: both sites get the superclass type
            pre = client.post(
                "/reasoning/materialize", json={"force": True, "aboxGraphs": [test_graph]}
            )
            suite.check(
                "facts.materialize.pre",
                pre.status_code == 200
                and inferred_ask(f"<{site_a}> a <{facility_cls}>")
                and inferred_ask(f"<{site_b}> a <{facility_cls}>"),
                f"status={pre.status_code} graph={inferred}",
            )

            # 4. single retraction: triple gone, context no longer recalls it
            retracted = client.post(f"/facts/{f4}/retract", json={"reason": "wrong label"})
            body = retracted.json() if retracted.status_code == 200 else {}
            events = client.get(f"/facts/{f4}/events").json().get("events", [])
            suite.check(
                "facts.retract.single",
                retracted.status_code == 200
                and body.get("state") == "retracted"
                and not ask(f'<{site_a}> <{RDFS}label> "{fake_label}"'),
                f"status={retracted.status_code} state={body.get('state')}",
            )
            suite.check(
                "facts.retract.audit",
                {event["action"] for event in events} >= {"asserted", "retracted"},
                f"actions={[event['action'] for event in events]}",
            )
            pack = runtime.context.resolve(
                {"query": "S8 context", "entityHints": [site_a], "graphs": [test_graph]}
            )
            labels = [f for f in pack["facts"] if f["predicate"] == RDFS + "label"]
            suite.check(
                "facts.context.no_retracted",
                labels == [],
                f"labels={len(labels)}",
            )

            # 5. batch by source: doc-a has two facts, doc-b must be untouched
            batch = client.post(
                "/facts/retract", json={"sourceDocumentId": doc_a, "reason": "bad extraction"}
            ).json()
            suite.check(
                "facts.retract.batch",
                batch.get("retracted") == 2 and len(batch.get("factIds", [])) == 2,
                f"retracted={batch.get('retracted')} batch={batch.get('batchId')}",
            )
            after_doc_a = client.get(
                "/facts", params={"state": "active", "sourceDocumentId": doc_a}
            ).json()
            other = client.get(
                "/facts", params={"state": "active", "subject": site_b}
            ).json()
            suite.check(
                "facts.retract.batch_scope",
                after_doc_a.get("count") == 0
                and other.get("count") == 1
                and not ask(f"<{site_a}> a <{site_cls}>")
                and not ask(f"<{site_a}> <{LOCATED_IN}> <{region_a}>"),
                f"doc_a={after_doc_a.get('count')} site_b={other.get('count')}",
            )
            batch_events = client.get(f"/facts/{f1}/events").json().get("events", [])
            suite.check(
                "facts.batch.audit",
                any(event["action"] == "batch_retracted" and event.get("batchId")
                    for event in batch_events),
                f"actions={[event['action'] for event in batch_events]}",
            )

            # 6. re-materialize: no entailment from the retracted facts survives
            post = client.post(
                "/reasoning/materialize", json={"force": True, "aboxGraphs": [test_graph]}
            )
            suite.check(
                "facts.materialize.no_retracted",
                post.status_code == 200
                and not inferred_ask(f"<{site_a}> a <{facility_cls}>")
                and inferred_ask(f"<{site_b}> a <{facility_cls}>"),
                f"status={post.status_code}",
            )

            # 7. restore: state, triple and context return to the pre-retraction view
            restored = client.post(f"/facts/{f1}/restore", json={"actor": "api"})
            restored_body = restored.json() if restored.status_code == 200 else {}
            suite.check(
                "facts.restore",
                restored.status_code == 200
                and restored_body.get("state") == "active"
                and ask(f"<{site_a}> a <{site_cls}>"),
                f"status={restored.status_code} state={restored_body.get('state')}",
            )
            back = runtime.context.resolve(
                {
                    "query": "S8 restore",
                    "entityHints": [site_a],
                    "graphs": [test_graph],
                    # Chunks are cut before facts, so a corpus filled by earlier
                    # smoke/bench runs can starve facts out of the default budget.
                    # This assertion is about ledger restore, not truncation,
                    # hence an explicit budget.
                    "tokenBudget": 4096,
                }
            )
            suite.check(
                "facts.restore.context",
                any(f["predicate"] == RDF + "type"
                    and (f["object"].get("iri") or f["object"].get("value")) == site_cls
                    for f in back["facts"]),
                f"facts={len(back['facts'])} omitted={back.get('omitted')}",
            )
            again = client.post(
                "/reasoning/materialize", json={"force": True, "aboxGraphs": [test_graph]}
            )
            suite.check(
                "facts.restore.materialize",
                again.status_code == 200
                and inferred_ask(f"<{site_a}> a <{facility_cls}>"),
                f"status={again.status_code}",
            )
            restore_events = client.get(f"/facts/{f1}/events").json().get("events", [])
            suite.check(
                "facts.audit.chain",
                {"asserted", "batch_retracted", "restored"}
                <= {event["action"] for event in restore_events},
                f"actions={[event['action'] for event in restore_events]}",
            )

            # 8. conflict: two active values for one (s, p), both stay visible
            conflict_list = client.get(
                "/facts", params={"state": "active", "subject": site_c}
            ).json()
            conflict_items = conflict_list.get("items", [])
            suite.check(
                "facts.conflict.visible",
                len(conflict_items) == 2
                and all(item.get("conflict") is True for item in conflict_items)
                and all(len(item.get("conflictValues", [])) == 2 for item in conflict_items),
                f"items={len(conflict_items)} values={[i.get('conflictValues') for i in conflict_items]}",
            )
            conflicts = client.get("/facts/conflicts").json()
            suite.check(
                "facts.conflict.endpoint",
                any(item["subject"] == site_c
                    and set(item["values"]) == {region_x, region_y}
                    for item in conflicts.get("conflicts", [])),
                f"conflicts={conflicts.get('count')}",
            )
            pack_conflict = runtime.context.resolve(
                {"query": "S8 conflict", "entityHints": [site_c], "graphs": [test_graph]}
            )
            located = [f for f in pack_conflict["facts"] if f["predicate"] == LOCATED_IN]
            suite.check(
                "facts.conflict.context",
                len(located) == 2
                and all(f.get("conflict") is True for f in located)
                and len(located[0].get("conflictValues", [])) == 2,
                f"facts={len(located)}",
            )

            # 9. cleanup the test graph, then prove the audit survived the purge
            runtime.graph.update(f"DROP GRAPH <{test_graph}>")
            purged = runtime.facts.purge_test(test_graph)
            cleaned = True
            audit_rows = runtime.metadata.query(
                "SELECT COUNT(*) AS n FROM platform.fact_event WHERE fact_id = %s", (f1,)
            )
            leftover = runtime.graph.query(
                'SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } '
                'FILTER(STRSTARTS(STR(?g), "urn:platform:test:")) }'
            )
            suite.check(
                "facts.audit.survives_purge",
                purged >= 1 and int(audit_rows[0]["n"]) >= 3,
                f"purged={purged} events={audit_rows[0]['n']}",
            )
            suite.check(
                "facts.cleanup.test_graph",
                len(leftover.get("bindings", [])) == 0,
                f"leftover={len(leftover.get('bindings', []))}",
            )

            status = client.get("/status").json()
            suite.check(
                "http.status",
                status.get("slice") in {"S7", "S8", "S9", "S10", "S11", "S12", "S13"}
                and "facts" in status.get("providers", {}),
                f"slice={status.get('slice')}",
            )
        except PortError as exc:
            suite.fail("runtime", f"{exc.code}/{exc.provider_code}: {exc.message}")
        except httpx.HTTPError as exc:
            suite.fail("http", str(exc))
        finally:
            if not cleaned:
                try:
                    runtime.graph.update(f"DROP GRAPH <{test_graph}>")
                except PortError:
                    pass
                try:
                    runtime.facts.purge_test(test_graph)
                except Exception as exc:  # noqa: BLE001 - cleanup must not mask results
                    suite.fail("cleanup.facts", str(exc))

    passed = sum(1 for _, ok, _ in suite.results if ok)
    total = len(suite.results)
    print(f"SMOKE-S8 {passed}/{total}")
    for name, ok, detail in suite.results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}")
    return 0 if passed == total else 1
