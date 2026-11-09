"""Make the source tree importable, install the Windows shim, expose a live PG DSN."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_PACKAGES = Path(__file__).resolve().parents[2]
_REPO = _PACKAGES.parent
for _path in (
    str(_PACKAGES / "local-providers" / "src"),
    str(_PACKAGES / "coa-ports" / "src"),
    str(_PACKAGES / "platform-core" / "src"),
    str(_PACKAGES / "metric-service" / "src"),
    str(_PACKAGES / "context-manager" / "src"),
    str(_REPO / "libs" / "common" / "src"),
):
    if _path not in sys.path:
        sys.path.insert(0, _path)

try:  # pragma: no cover - platform dependent
    from coa_local_providers.win_compat import ensure_resource_module

    ensure_resource_module()
except Exception:  # noqa: BLE001
    pass


# The acceptance stack publishes PostgreSQL on 5433 (see doc/_design/69). Tests
# only issue read-only statements against it; write cases skip (see
# ``pg_dsn_readwrite``). Override with ``COA_TEST_PG_DSN`` for another server.
_ACCEPTANCE_READONLY_DSN = (
    "postgresql://platform:JsxhssIpKyY28iPTiLjQwx1U@127.0.0.1:5433/platform"
)


@pytest.fixture(scope="session")
def pg_dsn() -> str:
    """DSN of a live local PostgreSQL, or a skip.

    The storage shells are tested against the real platform adapters, so they
    need a real server. Defaults to the acceptance stack (read-only use);
    ``COA_TEST_PG_DSN`` overrides it. When the server is unreachable these
    tests skip instead of silently passing on a substitute.
    """
    psycopg = pytest.importorskip("psycopg", reason="psycopg 未安装")
    dsn = os.environ.get("COA_TEST_PG_DSN") or _ACCEPTANCE_READONLY_DSN
    try:
        with psycopg.connect(dsn, connect_timeout=3) as conn:
            conn.execute("SELECT 1")
    except Exception as exc:  # noqa: BLE001 - any connection failure means "skip"
        pytest.skip(f"PostgreSQL 不可达: {type(exc).__name__}")
    return dsn


@pytest.fixture(scope="session")
def pg_dsn_readwrite(pg_dsn: str) -> str:
    """DSN for cases that write, disabled by default.

    The default acceptance connection is treated as read-only; a test that
    inserts, creates or deletes must ask for this fixture and therefore skips
    unless ``COA_TEST_PG_WRITE=1`` explicitly opts in with a writable server.
    """
    if os.environ.get("COA_TEST_PG_WRITE", "") != "1":
        pytest.skip(
            "写库用例默认跳过：验收库按只读使用；写库需设 COA_TEST_PG_WRITE=1 并指向可写库"
        )
    return pg_dsn
