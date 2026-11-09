"""Local ``QueryExecutor`` against PostgreSQL (psycopg 3, async).

Engine: PostgreSQL. One connection per query (no pool dependency), guarded by a
semaphore for concurrency and two independent timeouts:

* ``statement_timeout`` — server-side cancel, so a runaway plan cannot outlive the call.
* ``asyncio.timeout`` — client-side bound on connect + execute + fetch.

``namespace`` / ``data_source_id`` are accepted for contract parity but not routed:
this executor has exactly one DSN, and saying otherwise would fake a router.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import psycopg
from coa_serve.clients.base import QueryResult
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row


def _host(dsn: str) -> tuple[str | None, str | None]:
    try:
        info = conninfo_to_dict(dsn)
    except Exception:  # noqa: BLE001 - health must not raise on a malformed DSN
        return None, None
    return info.get("host"), info.get("port")


class PostgresQueryExecutor:
    """Read/write SQL executor for one local PostgreSQL database."""

    engine = "postgres"

    def __init__(
        self,
        dsn: str,
        *,
        max_concurrency: int = 4,
        connect_timeout_s: float = 5.0,
    ) -> None:
        self._dsn = dsn
        self._semaphore = asyncio.Semaphore(max(1, max_concurrency))
        self._connect_timeout_s = connect_timeout_s

    async def execute(
        self,
        sql: str,
        *,
        namespace: str,
        data_source_id: str,
        params: dict[str, Any] | None = None,
        max_rows: int = 1000,
        timeout_seconds: int = 10,
    ) -> QueryResult:
        """Run one statement; truncate at ``max_rows`` and tag the engine."""
        started = time.perf_counter()
        statement_ms = max(1, int(timeout_seconds * 1000))
        async with self._semaphore:
            connection = await psycopg.AsyncConnection.connect(
                self._dsn,
                connect_timeout=int(self._connect_timeout_s),
                row_factory=dict_row,
            )
            try:
                await connection.execute(f"SET statement_timeout = {statement_ms}")
                async with asyncio.timeout(timeout_seconds + 1.0):
                    async with connection.cursor(row_factory=dict_row) as cursor:
                        await cursor.execute(sql, params or None)
                        fetched = await cursor.fetchmany(max_rows + 1)
                        columns = [column.name for column in cursor.description or []]
            finally:
                await connection.close()
        truncated = len(fetched) > max_rows
        rows = fetched[:max_rows]
        duration_ms = int(round((time.perf_counter() - started) * 1000))
        return QueryResult(
            rows=rows,
            columns=columns,
            row_count=len(rows),
            truncated=truncated,
            duration_ms=duration_ms,
            engine=self.engine,
        )

    async def health_check(self) -> dict[str, Any]:
        """Probe connectivity; never raises (contract requirement)."""
        host, port = _host(self._dsn)
        try:
            connection = await psycopg.AsyncConnection.connect(
                self._dsn,
                connect_timeout=int(self._connect_timeout_s),
            )
            try:
                await connection.execute("SELECT 1")
            finally:
                await connection.close()
            return {"ok": True, "backend": self.engine, "host": host, "port": port}
        except Exception as exc:  # noqa: BLE001 - health_check must not raise
            return {
                "ok": False,
                "backend": self.engine,
                "host": host,
                "port": port,
                "error": f"{type(exc).__name__}: {exc}",
            }
