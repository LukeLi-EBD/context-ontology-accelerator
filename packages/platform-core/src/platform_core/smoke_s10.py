"""S10 acceptance: reversible adjudication, batch keep with dry-run, and
audit replay into a throw-away empty database. All A-Box writes live in a
test graph (OQ-31); the audit table is never deleted.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import httpx

from .assembly import Runtime
from .errors import PortError
from .fact_export import write_export
from .facts import verify_records
from .replay import replay_file

LOCATED_IN = "urn:platform:rel:locatedIn"


class _Case:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def check(self, name: str, condition: bool, detail: str = "") -> bool:
        self.results.append((name, bool(condition), detail))
        return bool(condition)

    def fail(self, name: str, detail: str) -> None:
        self.results.append((name, False, detail))


def run_smoke_s10(runtime: Runtime, base_url: str) -> int:
    suite = _Case()
    base = base_url.rstrip("/")
    tmp_dir = Path(runtime.config.storage.tmp_dir)
    nonce = uuid.uuid4().hex[:8]
    test_graph = f"urn:platform:test:{uuid.uuid4().hex[:10]}:s10"
    bulk_pred = f"urn:platform:smoke:{nonce}:bulkLocatedIn"
    site_a = f"urn:platform:smoke:{nonce}:siteA"
    site_b = f"urn:platform:smoke:{nonce}:siteB"
    region_x = f"urn:platform:smoke:{nonce}:regionX"
    region_y = f"urn:platform:smoke:{nonce}:regionY"
    region_p = f"urn:platform:smoke:{nonce}:regionP"
    region_q = f"urn:platform:smoke:{nonce}:regionQ"
    merged_region = f"urn:platform:smoke:{nonce}:regionMerged"
    region_shared = f"urn:platform:smoke:{nonce}:regionShared"
    doc_b = f"doc-b-{nonce}"
    doc_batch = f"doc-batch-{nonce}"
    fact_ids: dict[tuple[str, str], str] = {}
    cleaned = False

    def ask(triple: str) -> bool:
        return runtime.graph.ask(f"ASK {{ GRAPH <{test_graph}> {{ {triple} }} }}")

    def located(iri: str) -> list[dict]:
        pack = runtime.context.resolve(
            {"query": "S10", "entityHints": [iri], "graphs": [test_graph]}
        )
        return [f for f in pack["facts"] if f["predicate"] == LOCATED_IN]

    def objects(iri: str, predicate: str | None = None) -> list[str]:
        pack = runtime.context.resolve(
            {"query": "S10", "entityHints": [iri], "graphs": [test_graph]}
        )
        return sorted(
            f["object"].get("iri") or f["object"].get("value")
            for f in pack["facts"]
            if predicate is None or f["predicate"] == predicate
        )

    with httpx.Client(base_url=base, timeout=60.0) as client:
        try:
            runtime.metadata.open(retry_seconds=10.0)
            runtime.metadata.migrate()

            payloads = [
                (site_a, region_x, f"doc-a1-{nonce}", LOCATED_IN),
                (site_a, region_y, f"doc-a2-{nonce}", LOCATED_IN),
                (site_b, region_p, doc_b, LOCATED_IN),
                (site_b, region_q, doc_b, LOCATED_IN),
            ]
            for index in range(1, 4):
                subject = f"urn:platform:smoke:{nonce}:bulk{index}"
                payloads.append((subject, region_shared, doc_batch, bulk_pred))
                payloads.append((
                    subject, f"urn:platform:smoke:{nonce}:regionOther{index}",
                    doc_batch, bulk_pred,
                ))
            bulk4 = f"urn:platform:smoke:{nonce}:bulk4"
            payloads.append((bulk4, f"urn:platform:smoke:{nonce}:regionAlt1", doc_batch, bulk_pred))
            payloads.append((bulk4, f"urn:platform:smoke:{nonce}:regionAlt2", doc_batch, bulk_pred))

            for subject, obj, document, predicate in payloads:
                response = client.post("/facts", json={
                    "subject": subject, "predicate": predicate, "object": obj,
                    "graph": test_graph, "sourceKind": "extraction",
                    "sourceDocumentId": document,
                })
                if response.status_code != 200:
                    suite.fail("setup.facts", f"{obj} -> {response.status_code}")
                else:
                    fact_ids[(subject, obj)] = response.json()["factId"]
            suite.check(
                "setup.facts", len(fact_ids) == len(payloads),
                f"facts={len(fact_ids)}",
            )

            # 1. merge then unmerge: the graph/context must return to the pre-merge state
            pre_conflicts = client.get("/facts/conflicts").json()
            suite.check(
                "merge.pre",
                any(entry["subject"] == site_b for entry in pre_conflicts.get("conflicts", []))
                and objects(site_b, LOCATED_IN) == sorted([region_p, region_q]),
                f"pending={pre_conflicts.get('pending')}",
            )
            merged = client.post("/facts/conflicts/resolve", json={
                "subject": site_b, "predicate": LOCATED_IN, "action": "merge",
                "mergedObject": merged_region, "actor": "operator",
                "reason": "same place", "graph": test_graph,
                "sourceDocumentId": doc_b,
            })
            merged_body = merged.json() if merged.status_code == 200 else {}
            new_fact = merged_body.get("newFact") or {}
            suite.check(
                "merge.active",
                merged.status_code == 200 and new_fact.get("state") == "active"
                and objects(site_b, LOCATED_IN) == [merged_region],
                f"new={new_fact.get('factId')}",
            )

            new_events = runtime.facts.events(new_fact.get("factId", ""))
            merge_event = next(
                (event for event in new_events if event["action"] == "merged"), None
            )
            unmerged = client.post("/facts/conflicts/unmerge", json={
                "eventId": (merge_event or {}).get("eventId"),
                "actor": "operator", "reason": "merge was wrong",
            })
            unmerged_body = unmerged.json() if unmerged.status_code == 200 else {}
            originals = [fact_ids[(site_b, region_p)], fact_ids[(site_b, region_q)]]
            restored_rows = [runtime.facts.get(fact_id) for fact_id in originals]
            suite.check(
                "unmerge.restore",
                unmerged.status_code == 200
                and runtime.facts.get(new_fact["factId"])["state"] == "retracted"
                and all(row["state"] == "active" and row["supersededBy"] is None
                        for row in restored_rows)
                and ask(f"<{site_b}> <{LOCATED_IN}> <{region_p}>")
                and ask(f"<{site_b}> <{LOCATED_IN}> <{region_q}>")
                and not ask(f"<{site_b}> <{LOCATED_IN}> <{merged_region}>"),
                f"undoOf={unmerged_body.get('undoOf')}",
            )
            suite.check(
                "unmerge.context",
                objects(site_b, LOCATED_IN) == sorted([region_p, region_q]),
                f"values={objects(site_b, LOCATED_IN)}",
            )
            suite.check(
                "unmerge.audit",
                any(event["action"] == "unmerged"
                    and (event.get("payload") or {}).get("role") == "restored"
                    for event in runtime.facts.events(originals[0]))
                and any(event["action"] == "merged"
                        for event in runtime.facts.events(new_fact["factId"]))
                and len(runtime.facts.events(new_fact["factId"])) >= 2,
                f"events={len(new_events)}",
            )

            keep_both = client.post("/facts/conflicts/resolve", json={
                "subject": site_b, "predicate": LOCATED_IN,
                "action": "keep_both", "actor": "operator", "reason": "both valid",
            })
            site_b_rows = [
                runtime.facts.get(fact_ids[(site_b, region_p)]),
                runtime.facts.get(fact_ids[(site_b, region_q)]),
            ]
            suite.check(
                "keepboth.resolve",
                keep_both.status_code == 200
                and all(row["acceptedConflict"] for row in site_b_rows)
                and all(row["state"] == "active" for row in site_b_rows)
                and all(
                    entry["subject"] != site_b
                    for entry in client.get("/facts/conflicts").json().get("conflicts", [])
                ),
                f"accepted={[row['acceptedConflict'] for row in site_b_rows]}",
            )
            keep_both_undo = client.post("/facts/conflicts/undo", json={
                "subject": site_b, "predicate": LOCATED_IN,
                "actor": "operator", "reason": "undo keep both",
            })
            keep_both_body = keep_both_undo.json() if keep_both_undo.status_code == 200 else {}
            site_b_rows = [
                runtime.facts.get(fact_ids[(site_b, region_p)]),
                runtime.facts.get(fact_ids[(site_b, region_q)]),
            ]
            suite.check(
                "keepboth.undo",
                keep_both_undo.status_code == 200
                and keep_both_body.get("undoOf") == "keep_both"
                and all(row["state"] == "active" and not row["acceptedConflict"]
                        and row["resolution"] is None for row in site_b_rows)
                and any(
                    entry["subject"] == site_b
                    for entry in client.get("/facts/conflicts").json().get("conflicts", [])
                ),
                f"undoOf={keep_both_body.get('undoOf')}",
            )

            # 2. keep then undo: the retired value becomes active again
            kept = client.post("/facts/conflicts/resolve", json={
                "subject": site_a, "predicate": LOCATED_IN, "action": "keep",
                "keep": region_x, "actor": "operator", "reason": "A wins",
            })
            suite.check(
                "keep.active",
                kept.status_code == 200
                and runtime.facts.get(fact_ids[(site_a, region_y)])["state"] == "retracted"
                and objects(site_a, LOCATED_IN) == [region_x],
                f"state={runtime.facts.get(fact_ids[(site_a, region_y)])['state']}",
            )
            undo = client.post("/facts/conflicts/undo", json={
                "subject": site_a, "predicate": LOCATED_IN,
                "actor": "operator", "reason": "undo keep",
            })
            undo_body = undo.json() if undo.status_code == 200 else {}
            restored_y = runtime.facts.get(fact_ids[(site_a, region_y)])
            suite.check(
                "keep.undo",
                undo.status_code == 200
                and restored_y["state"] == "active"
                and restored_y["resolution"] is None
                and objects(site_a, LOCATED_IN) == sorted([region_x, region_y])
                and ask(f"<{site_a}> <{LOCATED_IN}> <{region_y}>"),
                f"state={restored_y['state']} values={objects(site_a, LOCATED_IN)}",
            )
            suite.check(
                "keep.undo.audit",
                (undo_body.get("undoOf") == "keep")
                and any(event["action"] == "resolution_undo"
                        for event in runtime.facts.events(fact_ids[(site_a, region_y)]))
                and any(event["action"] == "conflict_kept"
                        for event in runtime.facts.events(fact_ids[(site_a, region_y)])),
                f"undoOf={undo_body.get('undoOf')}",
            )

            chain_export = runtime.facts.export_events()
            chain_ok = verify_records(chain_export["items"]).get("ok") is True
            actions = {item["action"] for item in chain_export["items"]}
            suite.check(
                "audit.chain",
                chain_ok and "unmerged" in actions and "resolution_undo" in actions,
                f"ok={chain_ok} actions={sorted(actions)}",
            )
            no_target = client.post("/facts/conflicts/undo", json={
                "subject": site_b, "predicate": LOCATED_IN, "dryRun": True,
            })
            suite.check(
                "undo.no_target",
                no_target.status_code == 409
                and "E_FACT_NO_RESOLUTION" in no_target.text,
                f"status={no_target.status_code}",
            )

            # 3. batch keep: dry-run first, then execute; one group has no keep value
            pending_before = client.get("/facts/conflicts").json().get("pending")
            preview = client.post("/facts/conflicts/batch", json={
                "predicate": bulk_pred, "keep": region_shared,
                "actor": "operator", "dryRun": True,
            })
            preview_body = preview.json() if preview.status_code == 200 else {}
            pending_after_preview = client.get("/facts/conflicts").json().get("pending")
            suite.check(
                "batch.dry_run",
                preview.status_code == 200
                and preview_body.get("dryRun") is True
                and preview_body.get("matched") == 4
                and preview_body.get("kept") == 3
                and preview_body.get("skipped") == 1
                and preview_body.get("affectedFacts") == 3
                and pending_after_preview == pending_before,
                f"matched={preview_body.get('matched')} kept={preview_body.get('kept')}",
            )
            executed = client.post("/facts/conflicts/batch", json={
                "predicate": bulk_pred, "keep": region_shared,
                "actor": "operator", "reason": "batch rule", "dryRun": False,
            })
            executed_body = executed.json() if executed.status_code == 200 else {}
            remaining = [
                entry for entry in client.get("/facts/conflicts").json().get("conflicts", [])
                if entry["predicate"] == bulk_pred
            ]
            suite.check(
                "batch.execute",
                executed.status_code == 200
                and executed_body.get("kept") == 3
                and executed_body.get("skipped") == 1
                and len(remaining) == 1
                and remaining[0]["subject"] == bulk4
                and all(
                    item["status"] in ("kept", "skipped")
                    for item in executed_body.get("results", [])
                ),
                f"kept={executed_body.get('kept')} remaining={len(remaining)}",
            )
            retired_other = fact_ids[(
                f"urn:platform:smoke:{nonce}:bulk1",
                f"urn:platform:smoke:{nonce}:regionOther1",
            )]
            suite.check(
                "batch.audit",
                any(event["action"] == "conflict_kept"
                    and event.get("batchId")
                    for event in runtime.facts.events(retired_other)),
                f"batch={executed_body.get('batchId')}",
            )

            # 4. replay the whole chain into an empty database and compare to snapshot
            # Export must happen after the last adjudication, otherwise the snapshot
            # (taken now) and the event chain describe different moments.
            exported = runtime.facts.export_events()
            export_dir = tmp_dir / f"s10-{nonce}-export"
            fact_ids_in_chain = [
                item["factId"] for item in exported["items"] if item.get("factId")
            ]
            snapshot = runtime.facts.snapshot(fact_ids=fact_ids_in_chain)
            written = write_export(
                exported["items"], export_dir,
                runtime.facts.conflicts(include_accepted=True), snapshot=snapshot,
            )
            dry = replay_file(
                written["ndjson"], snapshot_path=written["snapshot"], dry_run=True
            )
            suite.check(
                "replay.dry_run",
                dry.get("ok") is True
                and dry.get("dryRun") is True
                and dry.get("matched") == len(snapshot)
                and not dry.get("mismatched"),
                f"matched={dry.get('matched')} snapshot={len(snapshot)}",
            )
            real = replay_file(
                written["ndjson"], snapshot_path=written["snapshot"],
                database_url=runtime.config.database.url,
            )
            suite.check(
                "replay.empty_db",
                real.get("ok") is True
                and real.get("replayed") is True
                and real.get("matched") == len(snapshot)
                and not real.get("mismatched"),
                f"db={real.get('database')} matched={real.get('matched')} "
                f"extra={len(real.get('extra') or [])}",
            )
            tampered_path = tmp_dir / f"s10-{nonce}-tampered.ndjson"
            records = [json.loads(line) for line in
                       Path(written["ndjson"]).read_text(encoding="utf-8").splitlines()]
            records[0]["payload"] = {**(records[0].get("payload") or {}), "tampered": 1}
            tampered_path.write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in records) + "\n",
                encoding="utf-8",
            )
            refused = replay_file(tampered_path, dry_run=True)
            suite.check(
                "replay.tamper",
                refused.get("ok") is False
                and "chain" in str(refused.get("error", "")),
                f"error={refused.get('error')}",
            )

            page = client.get("/ui/approvals.html")
            script = client.get("/ui/app.js")
            suite.check(
                "ui.undo_batch",
                page.status_code == 200
                and 'id="conflict-undo"' in page.text
                and 'id="conflict-batch"' in page.text
                and "undoLastResolution" in script.text
                and "batchKeep" in script.text,
                f"page={page.status_code} script={script.status_code}",
            )

            status = client.get("/status").json()
            suite.check(
                "http.status",
                status.get("slice") in {"S10", "S11", "S12", "S13"} and "facts" in status.get("providers", {}),
                f"slice={status.get('slice')}",
            )

            runtime.graph.update(f"DROP GRAPH <{test_graph}>")
            purged = runtime.facts.purge_test(test_graph)
            cleaned = True
            leftover = runtime.graph.query(
                "SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } "
                "FILTER regex(str(?g), 'urn:platform:test') }"
            )
            suite.check(
                "cleanup.test_graph",
                purged >= len(payloads) and len(leftover.get("bindings", [])) == 0,
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
    print(f"SMOKE-S10 {passed}/{total}")
    for name, ok, detail in suite.results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}")
    return 0 if passed == total else 1
