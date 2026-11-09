"""Real-call tests for the ``MetadataStorePort`` ACL shell.

No mocks: the shell wraps the real ``MetadataPg`` (psycopg pool) and talks to a
live PostgreSQL. Set ``COA_TEST_PG_DSN`` to a reachable database; without one
the tests skip. The closed-pool cases need no server and always run.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping

import pytest

from coa_local_providers.shells import MetadataStoreShell
from coa_ports import MetadataStorePort, PortError, PortErrorCode
from platform_core.adapters.metadata_pg import MetadataPg


def _open(dsn: str) -> MetadataPg:
    store = MetadataPg(dsn, pool_max=2)
    store.open(retry_seconds=5.0)
    return store


class _Minimal:
    """Shape stand-in for the isinstance/constructor checks only."""

    def query(self, sql: str, params: tuple | list = ()) -> list[dict]:
        return []

    def execute(self, sql: str, params: tuple | list = ()) -> int:
        return 0


def test_shell_is_a_metadata_store_port() -> None:
    assert isinstance(MetadataStoreShell(_Minimal()), MetadataStorePort)


def test_constructor_rejects_an_object_without_query_or_execute() -> None:
    with pytest.raises(TypeError):
        MetadataStoreShell(object())


def test_query_returns_a_tuple_of_mappings(pg_dsn: str) -> None:
    store = _open(pg_dsn)
    try:
        rows = MetadataStoreShell(store).query(
            "SELECT 1 AS one, %s::text AS echo", ("coa",)
        )
    finally:
        store.close()
    assert isinstance(rows, tuple)
    assert isinstance(rows[0], Mapping)
    assert rows[0]["one"] == 1
    assert rows[0]["echo"] == "coa"


def test_execute_returns_the_affected_row_count(pg_dsn: str) -> None:
    table = f"coa_shell_metadata_{uuid.uuid4().hex[:8]}"
    store = _open(pg_dsn)
    shell = MetadataStoreShell(store, provider="postgres")
    try:
        shell.execute(f"CREATE TABLE {table} (id integer, note text)")
        assert shell.execute(
            f"INSERT INTO {table} (id, note) VALUES (%s, %s)", (1, "x")
        ) == 1
        rows = shell.query(f"SELECT id, note FROM {table} ORDER BY id")
        assert rows == ({"id": 1, "note": "x"},)
    finally:
        store.execute(f"DROP TABLE IF EXISTS {table}")
        store.close()


def test_probe_reports_the_live_database(pg_dsn: str) -> None:
    store = _open(pg_dsn)
    try:
        snapshot = MetadataStoreShell(store).probe()
    finally:
        store.close()
    assert snapshot["status"] == "ok"
    assert snapshot["provider"] == "postgres"


def test_closed_pool_maps_to_unavailable() -> None:
    shell = MetadataStoreShell(MetadataPg("postgresql://x@127.0.0.1:1/x"))
    with pytest.raises(PortError) as excinfo:
        shell.query("SELECT 1")
    assert excinfo.value.code is PortErrorCode.UNAVAILABLE
    assert excinfo.value.provider_code == "E_DB_UNAVAILABLE"


def test_probe_never_raises_when_the_pool_is_closed() -> None:
    snapshot = MetadataStoreShell(MetadataPg("postgresql://x@127.0.0.1:1/x")).probe()
    assert snapshot["status"] == "unavailable"
    assert snapshot["provider_code"] == "E_DB_UNAVAILABLE"


def test_database_error_maps_to_internal_without_guessing(pg_dsn: str) -> None:
    store = _open(pg_dsn)
    shell = MetadataStoreShell(store)
    try:
        with pytest.raises(PortError) as excinfo:
            shell.query("SELECT * FROM platform.coa_shell_no_such_table")
    finally:
        store.close()
    assert excinfo.value.code is PortErrorCode.INTERNAL
    assert excinfo.value.provider == "postgres"
    # The driver error carries no platform code; the class name is diagnostic.
    assert excinfo.value.provider_code
