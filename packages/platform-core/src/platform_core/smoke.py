"""S0 smoke suite. Run inside the platform container: `platform smoke`."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import uuid
from typing import Any, Callable

import httpx

from .assembly import Runtime, assemble
from .config import ConfigBundle
from .errors import PortError

SMALL_DATA = b"S" * 4096
LARGE_DATA = b"0123456789abcdef" * (11 * 1024 * 1024 // 16)


class Smoke:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.results: list[dict[str, Any]] = []

    def check(self, name: str, fn: Callable[[], str]) -> None:
        try:
            detail = fn()
            self.passed += 1
            self.results.append({"name": name, "status": "pass", "detail": detail})
            print(f"[PASS] {name}: {detail}")
        except Exception as exc:  # noqa: BLE001 - smoke must report every failure
            self.failed += 1
            detail = f"{type(exc).__name__}: {exc}"
            self.results.append({"name": name, "status": "fail", "detail": detail})
            print(f"[FAIL] {name}: {detail}")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _expect_not_found(objects: Any, bucket: str, key: str) -> None:
    try:
        objects.head(bucket, key)
    except PortError as exc:
        if exc.code == "NotFound":
            return
        raise
    raise AssertionError("object is still visible after delete")


def run_smoke(bundle: ConfigBundle, base_url: str, bad_configs: list[str]) -> int:
    runtime: Runtime = assemble(bundle)
    suite = Smoke()
    client = httpx.Client(base_url=base_url.rstrip("/"), timeout=10.0)

    try:
        runtime.metadata.open(retry_seconds=10)

        def healthz() -> str:
            response = client.get("/healthz")
            assert response.status_code == 200, f"HTTP {response.status_code}: {response.text}"
            assert response.json().get("status") == "ok"
            return "http=200"

        def readyz() -> str:
            response = client.get("/readyz")
            assert response.status_code == 200, f"HTTP {response.status_code}: {response.text}"
            payload = response.json()
            assert payload.get("status") == "ok", payload
            for name, item in payload["checks"].items():
                assert item["status"] == "ok", (name, item)
            return "database=ok graph=ok storage=ok"

        suite.check("healthz", healthz)
        suite.check("readyz", readyz)

        graph_iri = f"urn:platform:smoke:{uuid.uuid4().hex}"
        subject = f"{graph_iri}:s"
        predicate = f"{graph_iri}:p"

        def graph_roundtrip() -> str:
            runtime.graph.update(
                f'INSERT DATA {{ GRAPH <{graph_iri}> {{ <{subject}> <{predicate}> "smoke" }} }}'
            )
            assert runtime.graph.ask(
                f"ASK {{ GRAPH <{graph_iri}> {{ <{subject}> <{predicate}> ?o }} }}"
            ), "ASK returned false after INSERT"
            result = runtime.graph.query(
                f"SELECT ?o WHERE {{ GRAPH <{graph_iri}> {{ <{subject}> <{predicate}> ?o }} }}"
            )
            assert len(result["bindings"]) == 1, result
            assert result["bindings"][0]["values"]["o"]["value"] == "smoke"
            runtime.graph.clear_graph(graph_iri)
            assert not runtime.graph.ask(
                f"ASK {{ GRAPH <{graph_iri}> {{ <{subject}> <{predicate}> ?o }} }}"
            ), "graph still has data after DROP"
            return "insert=1 select=1 drop=ok"

        suite.check("graph_roundtrip", graph_roundtrip)

        small_tier = "pg" if bundle.config.storage.small_object_provider == "pg" else "fs"

        def small_object_roundtrip() -> str:
            key = f"smoke-small-{uuid.uuid4().hex}"
            ref = runtime.objects.put("smoke", key, SMALL_DATA, "application/octet-stream", {"probe": "small"})
            assert ref["tier"] == small_tier, ref
            meta = runtime.objects.head("smoke", key)
            body, meta2 = runtime.objects.get("smoke", key)
            assert _sha(body) == _sha(SMALL_DATA), "sha256 mismatch"
            assert meta2["ref"]["size"] == len(SMALL_DATA)
            assert meta["ref"]["etag"] == _sha(SMALL_DATA)
            runtime.objects.delete("smoke", key)
            _expect_not_found(runtime.objects, "smoke", key)
            return f"tier={ref['tier']} size={len(SMALL_DATA)} sha256=ok"

        suite.check("small_object_roundtrip", small_object_roundtrip)

        def cas_roundtrip() -> str:
            key = f"smoke-large-{uuid.uuid4().hex}"
            ref = runtime.objects.put("smoke", key, LARGE_DATA, "application/octet-stream")
            assert ref["tier"] == "fs", ref
            meta = runtime.objects.head("smoke", key)
            body, meta2 = runtime.objects.get("smoke", key)
            assert len(body) == len(LARGE_DATA), (len(body), len(LARGE_DATA))
            assert _sha(body) == _sha(LARGE_DATA) == meta["ref"]["etag"]
            runtime.objects.delete("smoke", key)
            _expect_not_found(runtime.objects, "smoke", key)
            return f"tier=fs size={len(LARGE_DATA)} sha256=ok"

        suite.check("cas_roundtrip", cas_roundtrip)

        for path in bad_configs:
            name = f"config_failfast:{path.rsplit('/', 1)[-1]}"

            def failfast(config_path: str = path) -> str:
                proc = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "platform_core.cli",
                        "check-config",
                        "--config",
                        config_path,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                output = proc.stdout + proc.stderr
                assert proc.returncode == 78, f"expected exit 78, got {proc.returncode}: {output}"
                assert "stage=config" in output and "E_" in output, f"missing config error code: {output}"
                return "exit=78 stage=config"

            suite.check(name, failfast)

    finally:
        client.close()
        runtime.close()

    total = suite.passed + suite.failed
    print(f"SUMMARY passed={suite.passed} failed={suite.failed} total={total}")
    return 0 if suite.failed == 0 else 1
