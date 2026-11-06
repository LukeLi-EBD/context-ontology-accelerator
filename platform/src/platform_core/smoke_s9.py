"""S9 acceptance: operator conflict adjudication (keep / keep both / merge),
re-materialization after adjudication, NDJSON audit export and chain verification
(including tamper detection). All A-Box writes live in a test graph (OQ-31).
"""

from __future__ import annotations

import uuid
from pathlib import Path

import httpx

from .assembly import Runtime
from .errors import PortError
from .facts import verify_records

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
<urn:platform:smoke:{prefix}:Facility> a owl:Class .
<urn:platform:smoke:{prefix}:Site> a owl:Class ;
    rdfs:subClassOf <urn:platform:smoke:{prefix}:Facility> .
<urn:platform:smoke:{prefix}:Region> a owl:Class .
<{LOCATED_IN}> a owl:ObjectProperty ;
    rdfs:domain <urn:platform:smoke:{prefix}:Site> ;
    rdfs:range <urn:platform:smoke:{prefix}:Region> .
"""


def _write(tmp_dir: Path, name: str, text: str) -> Path:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    path = tmp_dir / name
    path.write_text(text, encoding="utf-8")
    return path


def run_smoke_s9(runtime: Runtime, base_url: str) -> int:
    suite = _Case()
    base = base_url.rstrip("/")
    tmp_dir = Path(runtime.config.storage.tmp_dir)
    nonce = uuid.uuid4().hex[:8]
    test_graph = f"urn:platform:test:{uuid.uuid4().hex[:10]}:s9"
    site_a = f"urn:platform:smoke:{nonce}:siteA"
    site_b = f"urn:platform:smoke:{nonce}:siteB"
    site_c = f"urn:platform:smoke:{nonce}:siteC"
    region_x = f"urn:platform:smoke:{nonce}:regionX"
    region_y = f"urn:platform:smoke:{nonce}:regionY"
    region_p = f"urn:platform:smoke:{nonce}:regionP"
    region_q = f"urn:platform:smoke:{nonce}:regionQ"
    region_m = f"urn:platform:smoke:{nonce}:regionM"
    region_n = f"urn:platform:smoke:{nonce}:regionN"
    merged_region = f"urn:platform:smoke:{nonce}:regionMerged"
    site_cls = f"urn:platform:smoke:{nonce}:Site"
    region_cls = f"urn:platform:smoke:{nonce}:Region"
    inferred: str | None = None
    cleaned = False

    def ask(graph: str, triple: str) -> bool:
        return runtime.graph.ask(f"ASK {{ GRAPH <{graph}> {{ {triple} }} }}")

    def materialize(client: httpx.Client, graph: str) -> bool:
        response = client.post(
            "/reasoning/materialize", json={"force": True, "aboxGraphs": [graph]}
        )
        return response.status_code == 200

    def context_located(client: httpx.Client, iri: str) -> list[dict]:
        pack = runtime.context.resolve(
            {"query": "S9", "entityHints": [iri], "graphs": [test_graph]}
        )
        return [f for f in pack["facts"] if f["predicate"] == LOCATED_IN]

    with httpx.Client(base_url=base, timeout=60.0) as client:
        try:
            runtime.metadata.open(retry_seconds=10.0)
            runtime.metadata.migrate()

            version = runtime.ontology.import_source(
                str(_write(tmp_dir, f"s9-{nonce}.ttl", _tbox(nonce))), "1.0.0",
                on_conflict="new_version",
            )
            runtime.ontology.publish(
                version["versionId"], acknowledge_breaking=True, purpose="smoke"
            )
            inferred = f"urn:platform:inferred:{version['versionId']}"

            payloads = [
                (site_a, region_x, f"doc-a1-{nonce}"),
                (site_a, region_y, f"doc-a2-{nonce}"),
                (site_b, region_p, f"doc-b1-{nonce}"),
                (site_b, region_q, f"doc-b2-{nonce}"),
                (site_c, region_m, f"doc-c1-{nonce}"),
                (site_c, region_n, f"doc-c2-{nonce}"),
            ]
            fact_ids: dict[str, str] = {}
            for subject, obj, document in payloads:
                response = client.post("/facts", json={
                    "subject": subject, "predicate": LOCATED_IN, "object": obj,
                    "graph": test_graph, "sourceKind": "extraction",
                    "sourceDocumentId": document,
                })
                if response.status_code != 200:
                    suite.fail("facts.assert", f"{subject} -> {response.status_code}")
                else:
                    fact_ids[obj] = response.json()["factId"]
            client.post("/facts", json={
                "subject": site_a, "predicate": RDF + "type", "object": site_cls,
                "graph": test_graph, "sourceKind": "manual",
            })
            suite.check(
                "conflict.setup",
                len(fact_ids) == 6,
                f"facts={len(fact_ids)}",
            )

            # 1. conflicts are visible before adjudication; B's range inference exists
            pre = materialize(client, test_graph)
            pending = client.get("/facts/conflicts").json()
            suite.check(
                "conflict.pre",
                pre
                and pending.get("pending") == 3
                and ask(inferred or "", f"<{region_y}> a <{region_cls}>"),
                f"pending={pending.get('pending')}",
            )

            # 2. keep region_x: region_y retracted, audit keeps the previous value
            kept = client.post("/facts/conflicts/resolve", json={
                "subject": site_a, "predicate": LOCATED_IN, "action": "keep",
                "keep": region_x, "actor": "operator", "reason": "source A wins",
            })
            kept_body = kept.json() if kept.status_code == 200 else {}
            retired = fact_ids[region_y]
            events = client.get(f"/facts/{retired}/events").json().get("events", [])
            suite.check(
                "keep.retracted",
                kept.status_code == 200
                and kept_body.get("retired") == 1
                and not ask(test_graph, f"<{site_a}> <{LOCATED_IN}> <{region_y}>")
                and ask(test_graph, f"<{site_a}> <{LOCATED_IN}> <{region_x}>"),
                f"retired={kept_body.get('retired')}",
            )
            suite.check(
                "keep.audit",
                any(
                    event["action"] == "conflict_kept"
                    and (event.get("payload") or {}).get("role") == "retired"
                    and (event.get("payload") or {}).get("previousState") == "active"
                    for event in events
                ),
                f"actions={[event['action'] for event in events]}",
            )
            located = context_located(client, site_a)
            suite.check(
                "keep.context",
                len(located) == 1
                and (located[0]["object"].get("iri") or located[0]["object"].get("value"))
                == region_x,
                f"facts={len(located)}",
            )

            # 3. re-materialize: the retired value no longer entails anything
            post = materialize(client, test_graph)
            suite.check(
                "keep.materialize",
                post
                and not ask(inferred or "", f"<{region_y}> a <{region_cls}>")
                and ask(inferred or "", f"<{region_x}> a <{region_cls}>"),
                f"graph={inferred}",
            )

            # 4. keep both: both values stay, flagged accepted and out of the queue
            both = client.post("/facts/conflicts/resolve", json={
                "subject": site_b, "predicate": LOCATED_IN, "action": "keep_both",
                "actor": "operator", "reason": "sources disagree, keep both",
            })
            both_body = both.json() if both.status_code == 200 else {}
            active = client.get(
                "/facts", params={"state": "active", "subject": site_b}
            ).json().get("items", [])
            suite.check(
                "keepboth.active",
                both.status_code == 200
                and (both_body.get("values") or []) == sorted([region_p, region_q])
                and len(active) == 2
                and ask(test_graph, f"<{site_b}> <{LOCATED_IN}> <{region_p}>")
                and ask(test_graph, f"<{site_b}> <{LOCATED_IN}> <{region_q}>"),
                f"values={both_body.get('values')}",
            )
            suite.check(
                "keepboth.accepted",
                all(item.get("conflict") is True and item.get("acceptedConflict") is True
                    for item in active),
                f"accepted={[item.get('acceptedConflict') for item in active]}",
            )
            default_conflicts = client.get("/facts/conflicts").json()
            all_conflicts = client.get(
                "/facts/conflicts", params={"includeAccepted": True}
            ).json()
            suite.check(
                "keepboth.not_pending",
                not any(entry["subject"] == site_b
                        for entry in default_conflicts.get("conflicts", []))
                and any(entry["subject"] == site_b and entry["accepted"] is True
                        for entry in all_conflicts.get("conflicts", [])),
                f"pending={default_conflicts.get('pending')} total={all_conflicts.get('count')}",
            )

            # 5. merge: a new active assertion, originals retracted and mutually linked
            merged = client.post("/facts/conflicts/resolve", json={
                "subject": site_c, "predicate": LOCATED_IN, "action": "merge",
                "mergedObject": merged_region, "actor": "operator",
                "reason": "same place, two labels", "graph": test_graph,
                "sourceDocumentId": f"doc-c-{nonce}",
            })
            merged_body = merged.json() if merged.status_code == 200 else {}
            new_fact = merged_body.get("newFact") or {}
            originals = [fact_ids[region_m], fact_ids[region_n]]
            original_rows = [
                client.get(f"/facts/{fact_id}").json() for fact_id in originals
            ]
            suite.check(
                "merge.new",
                merged.status_code == 200
                and new_fact.get("state") == "active"
                and (new_fact.get("object") or {}).get("iri") == merged_region
                and new_fact.get("mergedFrom") == originals
                and ask(test_graph, f"<{site_c}> <{LOCATED_IN}> <{merged_region}>"),
                f"new={new_fact.get('factId')} from={new_fact.get('mergedFrom')}",
            )
            suite.check(
                "merge.linked",
                all(row["state"] == "retracted"
                    and row.get("supersededBy") == new_fact.get("factId")
                    for row in original_rows)
                and not ask(test_graph, f"<{site_c}> <{LOCATED_IN}> <{region_m}>"),
                f"states={[row['state'] for row in original_rows]}",
            )
            merged_located = context_located(client, site_c)
            suite.check(
                "merge.context",
                len(merged_located) == 1
                and (merged_located[0]["object"].get("iri")
                     or merged_located[0]["object"].get("value")) == merged_region,
                f"facts={len(merged_located)}",
            )

            # 6. export: count matches fact_event, chain verifies, tampering must fail
            exported = client.get("/facts/events/export").json()
            db_count = int(runtime.metadata.query(
                "SELECT COUNT(*) AS n FROM platform.fact_event"
            )[0]["n"])
            suite.check(
                "export.count",
                exported.get("count") == db_count and db_count >= 20
                and bool(exported.get("ndjson")) and "Fact audit export" in exported.get("markdown", ""),
                f"export={exported.get('count')} db={db_count}",
            )
            suite.check(
                "export.verify",
                (exported.get("chain") or {}).get("ok") is True
                and verify_records(exported.get("items", [])).get("ok") is True,
                f"chain={exported.get('chain')}",
            )
            tampered = [dict(item) for item in exported.get("items", [])]
            if tampered:
                payload = dict(tampered[0].get("payload") or {})
                payload["tampered"] = True
                tampered[0]["payload"] = payload
            suite.check(
                "export.tamper_detected",
                bool(tampered) and verify_records(tampered).get("ok") is False,
                f"verify={verify_records(tampered)}",
            )

            page = client.get("/ui/approvals.html")
            script = client.get("/ui/app.js")
            suite.check(
                "ui.conflicts_panel",
                page.status_code == 200
                and 'id="conflicts"' in page.text
                and 'id="conflicts-refresh"' in page.text
                and "loadConflicts" in script.text,
                f"page={page.status_code} script={script.status_code}",
            )

            status = client.get("/status").json()
            suite.check(
                "http.status",
                status.get("slice") in {"S9", "S10", "S11", "S12", "S13"} and "facts" in status.get("providers", {}),
                f"slice={status.get('slice')}",
            )

            # 7. cleanup the test graph; assertions purged, audit untouched
            runtime.graph.update(f"DROP GRAPH <{test_graph}>")
            purged = runtime.facts.purge_test(test_graph)
            cleaned = True
            leftover = runtime.graph.query(
                "SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } "
                "FILTER regex(str(?g), 'urn:platform:test') }"
            )
            suite.check(
                "cleanup.test_graph",
                purged >= 6 and len(leftover.get("bindings", [])) == 0,
                f"purged={purged} leftover={len(leftover.get('bindings', []))}",
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
    print(f"SMOKE-S9 {passed}/{total}")
    for name, ok, detail in suite.results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}")
    return 0 if passed == total else 1
