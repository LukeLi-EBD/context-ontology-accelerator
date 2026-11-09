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


@pytest.fixture(scope="session")
def pg_dsn() -> str:
    """DSN of a live local PostgreSQL, or a skip.

    The storage shells are tested against the real platform adapters, so they
    need a real server. ``COA_TEST_PG_DSN`` points at one; without it (or when
    the server is unreachable) these tests skip instead of silently passing on
    a substitute.
    """
    psycopg = pytest.importorskip("psycopg", reason="psycopg 未安装")
    dsn = os.environ.get("COA_TEST_PG_DSN", "")
    if not dsn:
        pytest.skip("COA_TEST_PG_DSN 未设置（真实调用测试需要本地 PostgreSQL）")
    try:
        with psycopg.connect(dsn, connect_timeout=3) as conn:
            conn.execute("SELECT 1")
    except Exception as exc:  # noqa: BLE001 - any connection failure means "skip"
        pytest.skip(f"PostgreSQL 不可达: {type(exc).__name__}")
    return dsn
