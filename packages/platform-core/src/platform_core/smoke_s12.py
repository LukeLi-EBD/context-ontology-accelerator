"""S12 acceptance: integrity of already-delivered behaviour.

Covers OQ-47 (no publish path can skip the gates), OQ-46 (filtered export still
ships a complete, self-verifiable prefix chain) and OQ-45 (cleanup is audited so
a replay reproduces the purged state without extra facts).
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import httpx

from . import termgate
from .assembly import Runtime
from .errors import PortError
from .fact_export import export_meta, verify_file, write_export
from .replay import replay_file


class _Case:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def check(self, name: str, condition: bool, detail: str = "") -> bool:
        self.results.append((name, bool(condition), detail))
        return bool(condition)

    def fail(self, name: str, detail: str) -> None:
        self.results.append((name, False, detail))


def _expect(code: str, action) -> PortError | None:
    try:
        action()
    except PortError as exc:
        return exc if exc.provider_code == code else exc
    return None


def _prefixes() -> str:
    return (
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
    )


def run_smoke_s12(runtime: Runtime, base_url: str) -> int:
    suite = _Case()
    base = base_url.rstrip("/")
    nonce = uuid.uuid4().hex[:8]
    ns = f"urn:platform:smoke:s12:{nonce}:"
    test_graph = f"urn:platform:test:s12:{nonce}"
    tmp_dir = Path(runtime.config.storage.tmp_dir) / f"s12-{nonce}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    alpha, beta = f"{ns}Alpha", f"{ns}Beta"
    link = f"{ns}link"

    def write(name: str, body: str) -> str:
        path = tmp_dir / f"{name}.ttl"
        path.write_text(_prefixes() + f"@prefix ex: <{ns}> .\n" + body, encoding="utf-8")
        return str(path)

    base_body = (
        "ex:Alpha a owl:Class .\n"
        "ex:Beta a owl:Class .\n"
        "ex:link a owl:ObjectProperty ; rdfs:domain ex:Alpha ; rdfs:range ex:Beta .\n"
    )
    breaking_body = (
        "ex:Alpha a owl:Class .\n"
        "ex:link a owl:ObjectProperty ; rdfs:domain ex:Alpha .\n"
    )

    initial = runtime.ontology.current() or {}
    initial_id = initial.get("versionId")
    test_versions: dict[str, str] = {}
    facts: list[dict] = []
    restored = False

    try:
        runtime.metadata.open(retry_seconds=10.0)
        runtime.metadata.migrate()

        # ---- OQ-47: direct publish is an implicit proposal behind every gate ----
        v_base = runtime.ontology.import_source(write("base", base_body), "12.0.1", "s12 base")
        test_versions["base"] = v_base["versionId"]
        # A fresh namespace replaces every class of the current pointer, so this
        # implicit publish is breaking and must carry an explicit acknowledgement.
        published = runtime.ontology.publish(
            v_base["versionId"], acknowledge_breaking=True, actor="operator",
            purpose="smoke", **termgate.smoke_env_context("smoke"),
        )
        v_base_events = runtime.ontology.events(v_base["versionId"])["items"]
        actions = {event["action"] for event in v_base_events}
        stored = runtime.ontology.get_proposal(published["proposalId"])
        suite.check(
            "legacy.implicit_gated_publish",
            published.get("implicitProposal") is True
            and published.get("governed") is True
            and (runtime.ontology.current() or {}).get("versionId") == v_base["versionId"]
            and {"proposed", "approved", "published"} <= actions
            and stored["status"] == "published",
            f"proposal={published.get('proposalId')} actions={sorted(actions)}",
        )

        v_break = runtime.ontology.import_source(
            write("breaking", breaking_body), "12.0.2", "s12 breaking",
            on_conflict="new_version",
        )
        test_versions["breaking"] = v_break["versionId"]
        pointer_before = runtime.ontology.current() or {}
        refused = _expect(
            "E_ONTOLOGY_BREAKING",
            lambda: runtime.ontology.publish(v_break["versionId"], actor="operator"),
        )
        after_row = runtime.ontology.get(v_break["versionId"])
        after_pointer = runtime.ontology.current() or {}
        suite.check(
            "legacy.breaking_rejected",
            isinstance(refused, PortError)
            and refused.provider_code == "E_ONTOLOGY_BREAKING"
            and after_row["status"] == "draft"
            and after_pointer.get("versionId") == pointer_before.get("versionId"),
            f"code={getattr(refused, 'provider_code', None)} status={after_row['status']} "
            f"pointer={after_pointer.get('versionId')}",
        )
        acked = runtime.ontology.publish(
            v_break["versionId"], acknowledge_breaking=True, actor="operator",
            purpose="smoke", **termgate.smoke_env_context("smoke"),
        )
        suite.check(
            "legacy.breaking_acknowledged",
            acked.get("implicitProposal") is True
            and (runtime.ontology.current() or {}).get("versionId") == v_break["versionId"]
            and any(event["action"] == "breaking_acknowledged"
                    for event in runtime.ontology.events(v_break["versionId"])["items"]),
            f"proposal={acked.get('proposalId')}",
        )

        # ---- OQ-46: windowed export still ships a verifiable prefix chain ----
        def assert_fact(index: int, subject: str) -> dict:
            return runtime.facts.record(
                subject, f"{ns}note", f"value-{index}", "literal", test_graph,
                source_kind="manual", actor="smoke-s12",
            )

        batch1 = [assert_fact(1, f"{ns}f1"), assert_fact(2, f"{ns}f2")]
        batch2 = [assert_fact(3, f"{ns}f3"), assert_fact(4, f"{ns}f4")]
        facts = batch1 + batch2
        start = runtime.facts.events(batch2[0]["factId"])[0]["createdAt"]

        exported = runtime.facts.export_events(start=start)
        window_ids = [item["factId"] for item in exported["windowItems"] if item.get("factId")]
        snapshot = runtime.facts.snapshot(fact_ids=window_ids)
        total = runtime.facts.assertion_count()
        meta = export_meta(
            exported, snapshot, total,
            {"from": start, "to": None, "sourceDocumentId": None},
        )
        written = write_export(
            exported["items"], tmp_dir / "window", snapshot=snapshot, meta=meta
        )
        verified = verify_file(written["ndjson"])
        suite.check(
            "export.prefix_verified",
            verified.get("ok") is True
            and verified.get("verified_prefix") is True
            and verified.get("cutoff_seq") == meta["cutoff_seq"]
            and verified.get("cutoff_hash") == meta["cutoff_hash"]
            and exported["count"] > exported["windowCount"],
            f"ok={verified.get('ok')} prefix={verified.get('verified_prefix')} "
            f"prefixEvents={exported['count']} windowEvents={exported['windowCount']}",
        )
        suite.check(
            "export.assertions_window_only",
            written["snapshotCount"] == len(batch2)
            and {item["factId"] for item in snapshot} == {item["factId"] for item in batch2}
            and meta["excluded_count"] == total - len(snapshot)
            and any(item["factId"] == batch1[0]["factId"] for item in exported["items"]),
            f"snapshot={written['snapshotCount']} total={total} "
            f"excluded={meta['excluded_count']}",
        )
        lines = Path(written["ndjson"]).read_text(encoding="utf-8").splitlines()
        drop = len(lines) // 2
        tampered = tmp_dir / "tampered.ndjson"
        tampered.write_text(
            "\n".join(line for index, line in enumerate(lines) if index != drop) + "\n",
            encoding="utf-8",
        )
        tampered_result = verify_file(tampered)
        suite.check(
            "export.tamper_fails",
            tampered_result.get("ok") is False and len(lines) >= 3,
            f"ok={tampered_result.get('ok')} error={tampered_result.get('error')}",
        )
        truncated = tmp_dir / "window" / "truncated.ndjson"
        truncated.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
        trunc_result = verify_file(truncated)
        suite.check(
            "export.truncated_fails",
            trunc_result.get("ok") is False
            and "cutoff" in str(trunc_result.get("error", "")),
            f"ok={trunc_result.get('ok')} error={trunc_result.get('error')}",
        )

        # ---- OQ-45: purge is audited and replay has no extra/missing facts ----
        purged = runtime.facts.purge_test(test_graph)
        purge_events = runtime.facts.events(batch1[0]["factId"])
        suite.check(
            "purge.audited",
            purged == len(facts)
            and any(event["action"] == "purged_test_graph" for event in purge_events),
            f"purged={purged} actions={sorted({e['action'] for e in purge_events})}",
        )

        full = runtime.facts.export_events()
        full_ids = [item["factId"] for item in full["windowItems"] if item.get("factId")]
        full_snapshot = runtime.facts.snapshot(fact_ids=full_ids)
        full_meta = export_meta(full, full_snapshot, runtime.facts.assertion_count(), {})
        full_written = write_export(
            full["items"], tmp_dir / "purged", snapshot=full_snapshot, meta=full_meta
        )
        dry = replay_file(full_written["ndjson"], full_written["snapshot"], dry_run=True)
        real = replay_file(
            full_written["ndjson"], full_written["snapshot"], dry_run=False,
            database_url=runtime.config.database.url,
        )
        suite.check(
            "replay.purge_exact",
            dry.get("ok") is True and dry.get("mismatched") == [] and dry.get("extra") == []
            and real.get("ok") is True and real.get("mismatched") == []
            and real.get("extra") == [],
            f"dry mismatched={len(dry.get('mismatched') or [])} extra={len(dry.get('extra') or [])} "
            f"replay mismatched={len(real.get('mismatched') or [])} "
            f"extra={len(real.get('extra') or [])}",
        )

        with httpx.Client(base_url=base, timeout=60.0) as client:
            status = client.get("/status").json()
            suite.check(
                "http.status",
                status.get("slice") in {"S12", "S13"} and "facts" in status.get("providers", {}),
                f"slice={status.get('slice')}",
            )

        if initial_id and initial_id != v_base["versionId"]:
            runtime.ontology.rollback_to(
                initial_id, actor="operator", reason="s12 smoke cleanup"
            )
        restored = True
        suite.check(
            "cleanup.pointer",
            (runtime.ontology.current() or {}).get("versionId") == initial_id
            or initial_id is None,
            f"initial={initial_id}",
        )
    except PortError as exc:
        suite.fail("runtime", f"{exc.code}/{exc.provider_code}: {exc.message}")
    except httpx.HTTPError as exc:
        suite.fail("http", str(exc))
    finally:
        if not restored:
            try:
                if initial_id:
                    runtime.ontology.rollback_to(
                        initial_id, actor="operator", reason="s12 smoke cleanup"
                    )
            except Exception as exc:  # noqa: BLE001 - cleanup must not mask results
                suite.fail("cleanup.pointer", str(exc))
        try:
            runtime.facts.purge_test(test_graph)
        except Exception:  # noqa: BLE001 - graph may already be empty
            pass
        try:
            runtime.graph.update(f"DROP GRAPH <{test_graph}>")
        except Exception:  # noqa: BLE001 - best effort cleanup
            pass
        shutil.rmtree(tmp_dir, ignore_errors=True)

    passed = sum(1 for _, ok, _ in suite.results if ok)
    total = len(suite.results)
    print(f"SMOKE-S12 {passed}/{total}")
    for name, ok, detail in suite.results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    return 0 if passed == total else 1
