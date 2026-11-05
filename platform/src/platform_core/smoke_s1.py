"""S1 acceptance: normal path, idempotency, two failure paths, rollback, capability match."""

from __future__ import annotations

import logging
from pathlib import Path

from .adapters.graph_oxigraph import OxigraphHttpStore
from .adapters.ontology_pg import OntologyRegistry
from .assembly import Runtime
from .capabilities import run_probe
from .errors import PlatformError, PortError

log = logging.getLogger(__name__)

TESTS = Path("/app/tests/ontology")


class _Case:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def ok(self, name: str, detail: str = "") -> None:
        self.results.append((name, True, detail))

    def fail(self, name: str, detail: str) -> None:
        self.results.append((name, False, detail))

    def run(self, name: str, func) -> object | None:
        try:
            value = func()
            self.ok(name, value if isinstance(value, str) else "")
            return value
        except Exception as exc:  # noqa: BLE001 - the suite reports every failure
            detail = getattr(exc, "detail", None) or getattr(exc, "message", None) or str(exc)
            code = getattr(exc, "provider_code", None) or getattr(exc, "code", "")
            self.fail(name, f"{code} {detail}".strip())
            return None

    def expect_error(self, name: str, func, allowed: tuple[str, ...]) -> bool:
        try:
            func()
        except Exception as exc:  # noqa: BLE001 - expected failure
            code = getattr(exc, "provider_code", None) or getattr(exc, "code", "")
            detail = getattr(exc, "detail", None) or getattr(exc, "message", None) or str(exc)
            matched = code in allowed
            self.results.append((name, matched, f"{code} {detail} (expected)".strip()))
            return matched
        self.fail(name, "expected failure but the call succeeded")
        return False


def _count(registry: OntologyRegistry, version_id: str) -> int:
    return registry.graph_count(version_id)


def run_smoke_s1(runtime: Runtime) -> int:
    suite = _Case()
    registry = runtime.ontology
    # S14H-16: this suite publishes v1/v2 and rolls back, which moves the real
    # production pointer. Snapshot every pointer so the run leaves no pollution.
    initial_pointers = runtime.metadata.query(
        "SELECT name, version_id FROM platform.graph_pointer"
    )
    # S14H-17: snapshot version rows + graph IRIs so the run can delete only the
    # artifacts it creates (never a version that existed before the run).
    initial_versions = {
        row["version_id"]
        for row in runtime.metadata.query("SELECT version_id FROM platform.ontology_version")
    }
    initial_graphs = {
        row["graph_iri"]
        for row in runtime.metadata.query("SELECT DISTINCT graph_iri FROM platform.ontology_version")
    }

    # 1. normal path: import v1 -> publish -> pointer + graph count
    v1 = suite.run(
        "import.v1",
        lambda: registry.import_source(str(TESTS / "tbox_v1.ttl"), "1.0.0", "smoke v1"),
    )
    if v1:
        published = suite.run(
            "publish.v1",
            lambda: registry.publish(v1["versionId"], acknowledge_breaking=True),
        )
        if published:
            pointer = registry.current()
            if pointer and pointer["versionId"] == v1["versionId"]:
                if _count(registry, v1["versionId"]) == v1["tripleCount"]:
                    suite.ok("pointer.v1", f"{pointer['versionId']} triples={v1['tripleCount']}")
                else:
                    suite.fail("pointer.v1", "graph triple count mismatch")
            else:
                suite.fail("pointer.v1", f"pointer is {pointer}")
    else:
        suite.fail("publish.v1", "import failed")

    # 2. v2 becomes current; v1 graph is still readable
    v2 = suite.run(
        "import.v2",
        lambda: registry.import_source(str(TESTS / "tbox_v2.ttl"), "2.0.0", "smoke v2"),
    )
    if v2:
        suite.run(
            "publish.v2",
            lambda: registry.publish(v2["versionId"], acknowledge_breaking=True),
        )
        pointer = registry.current()
        if pointer and pointer["versionId"] == v2["versionId"]:
            suite.ok("pointer.v2", pointer["versionId"])
        else:
            suite.fail("pointer.v2", f"pointer is {pointer}")
        if v1 and _count(registry, v1["versionId"]) == v1["tripleCount"]:
            suite.ok("history.v1_readable", f"triples={v1['tripleCount']}")
        else:
            suite.fail("history.v1_readable", "v1 graph changed or unreadable")
    else:
        suite.fail("publish.v2", "import failed")

    # 3. idempotent re-import
    if v1:
        again = suite.run(
            "import.idempotent",
            lambda: registry.import_source(str(TESTS / "tbox_v1.ttl"), "1.0.0", "again"),
        )
        if again and again.get("skipped") and again["versionId"] == v1["versionId"]:
            suite.ok("import.idempotent", f"reused {again['versionId']}")
        else:
            suite.fail("import.idempotent", f"result={again}")

    # 4. failure path A: invalid Turtle must not create a version or move the pointer
    before = len(registry.list_versions())
    pointer_before = registry.current()
    suite.expect_error(
        "invalid_turtle_failfast",
        lambda: registry.import_source(str(TESTS / "bad.ttl"), "9.9.9"),
        ("E_ONTOLOGY_PARSE",),
    )
    after = len(registry.list_versions())
    pointer_after = registry.current()
    if after != before or pointer_after != pointer_before:
        suite.fail("invalid_turtle_side_effects", f"versions {before}->{after}, pointer moved")
    else:
        suite.ok("invalid_turtle_side_effects", "no version created, pointer unchanged")

    # 5. failure path B: unreachable graph must not move the pointer
    bad_graph = OxigraphHttpStore("http://127.0.0.1:1", timeout_ms=2000)
    bad_registry = OntologyRegistry(
        runtime.metadata, bad_graph, runtime.objects, runtime.config.ontology
    )
    pointer_before = registry.current()
    suite.expect_error(
        "graph_unavailable_failfast",
        lambda: bad_registry.publish(v2["versionId"]) if v2 else None,
        ("E_GRAPH_UNAVAILABLE", "Unavailable", "DeadlineExceeded"),
    )
    pointer_after = registry.current()
    bad_graph.close()
    if pointer_after != pointer_before:
        suite.fail("graph_unavailable_side_effects", f"pointer moved to {pointer_after}")
    else:
        suite.ok("graph_unavailable_side_effects", "pointer unchanged")

    # 6. rollback: new version row, old content, pointer switches
    if v1:
        rolled = suite.run("rollback", lambda: registry.rollback(v1["versionId"]))
        if rolled:
            pointer = registry.current()
            v1_hash = registry.get(v1["versionId"])["contentHash"]
            if (
                pointer
                and pointer["versionId"] == rolled["id"]
                and rolled["contentHash"] == v1_hash
                and registry.get(rolled["id"])["status"] == "published"
            ):
                suite.ok("rollback.pointer", f"new={rolled['id']} content=v1")
            else:
                suite.fail("rollback.pointer", f"pointer={pointer}")
            if v2 and _count(registry, v2["versionId"]) == v2["tripleCount"]:
                suite.ok("rollback.v2_still_readable", f"triples={v2['tripleCount']}")
            else:
                suite.fail("rollback.v2_still_readable", "v2 graph unreadable")
        else:
            suite.fail("rollback.pointer", "rollback failed")

    # 7. measured capability value must match the manifest
    report = run_probe(runtime.config.graph.endpoint)
    measured = report["gsp"]["support"]
    declared = (
        runtime.graph.manifest().notes.get("gsp_backend_support")
        or runtime.graph.manifest().notes.get("gsp_support")
    )
    if measured == declared:
        suite.ok("capabilities.manifest", f"GSP_SUPPORT={measured}")
    else:
        suite.fail("capabilities.manifest", f"measured={measured} manifest={declared}")

    # S14H-16: restore the pointers (and the published status of their targets)
    # captured before the smoke run, so acceptance never rewrites production state.
    for pointer in initial_pointers:
        runtime.metadata.execute(
            "UPDATE platform.graph_pointer SET version_id = %s, updated_at = now(), "
            "updated_by = 'smoke-restore' WHERE name = %s",
            (pointer["version_id"], pointer["name"]),
        )
        runtime.metadata.execute(
            "UPDATE platform.ontology_version SET status = 'published' WHERE version_id = %s",
            (pointer["version_id"],),
        )

    # S14H-17: delete the version rows this run created (ids absent from the
    # snapshot). Graphs already referenced by pre-run versions are kept, so a
    # rollback row pointing at real content never destroys it.
    created = [
        row
        for row in runtime.metadata.query(
            "SELECT version_id, graph_iri FROM platform.ontology_version"
        )
        if row["version_id"] not in initial_versions
    ]
    for row in created:
        if row["graph_iri"] in initial_graphs:
            continue
        try:
            runtime.graph.clear_graph(row["graph_iri"])
        except PortError as exc:
            log.warning(
                "smoke cleanup: graph drop failed",
                extra={
                    "event": {
                        "event": "smoke_cleanup_graph_failed",
                        "graph": row["graph_iri"],
                        "code": exc.provider_code,
                    }
                },
            )
    for row in created:
        try:
            runtime.metadata.execute(
                "DELETE FROM platform.ontology_version WHERE version_id = %s",
                (row["version_id"],),
            )
        except Exception as exc:  # noqa: BLE001 - FK references keep history intact
            log.warning(
                "smoke cleanup: version delete skipped",
                extra={
                    "event": {
                        "event": "smoke_cleanup_version_skipped",
                        "versionId": row["version_id"],
                        "error": str(exc)[:160],
                    }
                },
            )

    total = len(suite.results)
    passed = sum(1 for _, ok, _ in suite.results if ok)
    for name, ok, detail in suite.results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    print(f"S1 SMOKE {passed}/{total}")
    return 0 if passed == total else 1
