"""Read-only precheck: what happens to 8099 if `platform_core` disappears?

M3 deletes `packages/platform-core`.  This script answers "then what?" without
deleting anything and without binding a port:

* blocks `platform_core` (and its submodules) in this process only;
* imports the bridge module by path (no server, no seed, no writes);
* checks that the non-lifecycle routes still resolve;
* builds the Starlette app and calls the lifecycle path in-process, expecting a
  diagnosable 503 instead of an import-time crash.

Exit code 0 means "degrades to 503, stack still starts"; 1 means the bridge
cannot even be imported or cannot build an app without platform_core.

Usage (from the repo root)::

    .venv-coa-local\\Scripts\\python.exe doc\\coa-x\\tools\\precheck-platform-core.py
"""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path

import httpx

BRIDGE = Path(__file__).resolve().parent / "coa_api_local.py"
NS = "precheck-namespace"


class _BlockPlatformCore:
    """Meta path finder that pretends `platform_core` is not installed."""

    BLOCKED = ("platform_core", "platform_core.")

    def find_spec(self, fullname, path=None, target=None):  # noqa: ANN001
        if fullname == self.BLOCKED[0] or fullname.startswith(self.BLOCKED[1]):
            raise ModuleNotFoundError(f"blocked by precheck: {fullname}")
        return None


def load_bridge():
    for name in [m for m in sys.modules if m.split(".")[0] == "platform_core"]:
        del sys.modules[name]
    sys.meta_path.insert(0, _BlockPlatformCore())
    spec = importlib.util.spec_from_file_location("coa_api_local_precheck", BRIDGE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


async def probe(bridge):
    app = bridge._make_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://precheck") as client:
        lifecycle = await client.get(
            f"/namespaces/{NS}/ontologies/fsldm-local/versions",
            headers={"authority": "http://LOCAL-dev-bypass.invalid"},
        )
        sources = await client.get(
            f"/namespaces/{NS}/sources/platform-demo",
            headers={"authority": "http://LOCAL-dev-bypass.invalid"},
        )
    return lifecycle, sources


def main() -> int:
    failures: list[str] = []

    bridge = load_bridge()
    # Same env the real process sets, so the probe reflects a real start rather
    # than a missing-variable error from the Lambda handlers.
    bridge._configure_environment()

    match = bridge._match(f"/namespaces/{NS}/ontologies/fsldm-local/versions")
    if not match or match[2] != bridge.KERNEL:
        failures.append("lifecycle path no longer resolves to KERNEL")
    match = bridge._match(f"/namespaces/{NS}/sources/platform-demo")
    if not match or match[2] != bridge.SOURCES:
        failures.append("sources path no longer resolves to the sources handler")

    try:
        bridge._lifecycle_app()
    except ModuleNotFoundError as exc:
        print(f"[ok] lifecycle import fails loudly: {exc}")
    except Exception as exc:  # noqa: BLE001 - the type matters, not the detail
        print(f"[warn] lifecycle import failed as {type(exc).__name__}: {exc}")
    else:
        failures.append("lifecycle app built without platform_core (unexpected)")

    lifecycle, sources = asyncio.run(probe(bridge))
    print(f"[probe] lifecycle route -> {lifecycle.status_code} {lifecycle.text[:160]}")
    print(f"[probe] sources route   -> {sources.status_code}")
    if lifecycle.status_code != 503:
        failures.append(f"lifecycle route answered {lifecycle.status_code}, expected 503")
    # The sources handler may still answer 500 here (the probe skips the DB store
    # install); what matters is that it did not crash and did not degrade into
    # the lifecycle's 503.
    if sources.status_code == 503:
        failures.append("sources route degraded with the lifecycle route")

    if failures:
        for item in failures:
            print(f"[fail] {item}")
        return 1
    print("[ok] 8099 starts and serves without platform_core; lifecycle degrades to 503")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
