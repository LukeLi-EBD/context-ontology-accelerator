"""Run the platform kernel locally for the ontology lifecycle (no AWS, no compose).

The acceptance stack owns 8080/8082.  Those instances are not touched here:
this process is a third kernel instance on 8093 that shares the *local* stack
dependencies only:

    PostgreSQL 127.0.0.1:5444/serve_local   (the same DB the 8091 context-manager uses)
    Oxigraph   127.0.0.1:7878
    object FS  %TEMP%/coa-local-stack/kernel-8093

Why a separate process instead of extending the 8099 bridge or 8101 engine:
the T-Box lifecycle (version registry, proposals, publish, rollback) only
exists in ``platform_core``.  Re-implementing it elsewhere would duplicate the
state machine in ``adapters/ontology_pg.py`` and let the two copies drift.

The startup self-check is intentionally skipped: it probes the reasoner and
embedding services, which are unrelated to the lifecycle chain.  Assembly
still fails closed on a bad configuration (``load_config``/``assemble``).

Usage (from the repo root)::

    .venv-coa-local\\Scripts\\python.exe doc\\coa-x\\tools\\coa_kernel_local.py --port 8093
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from fastapi import Request

REPO = Path(__file__).resolve().parents[3]
CONFIG = REPO / "packages/platform-core/config/authoritative-8080.yaml"

_SRC = (
    "packages/platform-core/src",
    "libs/common/src",
    "packages/coa-ports/src",
)
for _rel in reversed(_SRC):
    _path = REPO / _rel
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


def _configure(port: int) -> None:
    run_dir = Path(os.environ.get("TEMP") or os.environ.get("TMP") or ".") / "coa-local-stack"
    kernel_dir = run_dir / "kernel-8093"
    defaults = {
        "PLATFORM__HTTP__BIND": "127.0.0.1",
        "PLATFORM__HTTP__PORT": str(port),
        "PLATFORM__DATA_DIR": str(kernel_dir),
        "PLATFORM__DATABASE__URL": "postgresql://platform:platform_dev@127.0.0.1:5444/serve_local",
        "PLATFORM__GRAPH__ENDPOINT": "http://127.0.0.1:7878",
        "PLATFORM__STORAGE__ROOT": str(kernel_dir / "storage"),
        "PLATFORM__STORAGE__TMP_DIR": str(kernel_dir / "tmp"),
        # The acceptance default (10%% free) rejects registration on this dev
        # machine (9.9%% free); a local box is not the production guard.
        "PLATFORM__STORAGE__MIN_FREE_PCT": "2",
        # No bootstrap ontology: a `watch` mode would mint a version at startup
        # and make the first real registration ambiguous.
        # Quoted because the config loader parses env values as YAML: bare
        # `off` would arrive as boolean False, not the string "off".
        "PLATFORM__ONTOLOGY__INIT_MODE": '"off"',
        # The consistency gate is fail-closed: registration marks the import
        # unusable when no reasoner answers, so point it at the shared local
        # reasoner (7879) instead of disabling the gate.
        "PLATFORM__REASONING__ENDPOINT": "http://127.0.0.1:7879",
        "PLATFORM__EMBEDDING__ENDPOINT": "http://127.0.0.1:8081/v1",
        # Import validates against `<shapes_dir>/<namespace>/*.ttl`; the image
        # default (/data) does not exist on Windows.  The file itself is local
        # seed data (see the report), not something this runner invents.
        "PLATFORM__REASONING__SHAPES_DIR": str(kernel_dir / "shapes"),
        "PLATFORM__CANVAS__PROVIDER": '"off"',
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)
    kernel_dir.mkdir(parents=True, exist_ok=True)
    (kernel_dir / "storage").mkdir(parents=True, exist_ok=True)
    (kernel_dir / "tmp").mkdir(parents=True, exist_ok=True)


def _add_register_route(app: object, runtime: object, kernel_dir: Path) -> None:
    """Add the local "version registration" endpoint.

    The kernel's HTTP import (`/ontology/import` + `/ontology/imports/{id}/publish`)
    ends in a *published* pointer switch, and the only path that creates a
    `status='draft'` row is `OntologyRegistry.import_source` (file based, used
    by the CLI).  The contract's `ImportOntology` needs the draft row without a
    publish, so this route adapts the CLI call to HTTP.  It lives in this local
    composition root, not in `platform_core.api`, so 8080/8082 are unchanged.
    """
    import base64
    import uuid

    @app.post("/local/ontology/register")  # type: ignore[attr-defined]
    async def register(request: Request) -> dict[str, object]:
        body = await request.json()
        raw = body.get("content")
        if isinstance(raw, str):
            data = raw.encode("utf-8")
        elif body.get("contentBase64"):
            data = base64.b64decode(body["contentBase64"])
        else:
            return {"error": "content or contentBase64 is required"}
        rdf_format = str(body.get("format") or "turtle")
        suffix = "trig" if rdf_format == "trig" else "ttl"
        namespace = body.get("targetNamespace") or body.get("namespace")
        existing = runtime.ontology.list_versions()  # type: ignore[attr-defined]
        semver = str(body.get("semver") or f"0.{len(existing) + 1}.0")
        path = kernel_dir / f"register-{uuid.uuid4().hex[:8]}.{suffix}"
        path.write_bytes(data)
        try:
            result = runtime.ontology.import_source(  # type: ignore[attr-defined]
                str(path), semver, label=namespace, rdf_format=rdf_format
            )
        finally:
            path.unlink(missing_ok=True)
        return {**result, "targetNamespace": namespace}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8093)
    args = parser.parse_args()

    _configure(args.port)

    import uvicorn

    from platform_core.api import create_app
    from platform_core.assembly import assemble
    from platform_core.config import load_config
    from platform_core.ontology_init import start as start_ontology, stop as stop_ontology

    bundle = load_config(CONFIG)
    runtime = assemble(bundle)
    # `run_self_check` (skipped above) is what normally opens the metadata
    # pool; without it every DB-backed route answers 503 E_DB_UNAVAILABLE.
    runtime.metadata.open(retry_seconds=30.0)
    start_ontology(runtime)
    app = create_app(runtime, [])
    _add_register_route(app, runtime, Path(os.environ["PLATFORM__DATA_DIR"]))
    try:
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_config=None,
            access_log=False,
        )
    finally:
        stop_ontology()
        runtime.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
