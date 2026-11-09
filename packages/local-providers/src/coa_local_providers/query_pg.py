"""COA ``QueryExecutor`` backed by platform_core's PostgreSQL AD (PF-0010).

``MetadataPg`` is the platform's psycopg 3 pool + ``dict_row`` wrapper. This
module exposes it as the async COA ``QueryExecutor``.

Honest limits, stated rather than hidden:

- ``namespace`` / ``data_source_id`` are accepted for contract parity but do not
  partition the connection: the DSN selects the database.
- per-call ``timeout_seconds`` is not enforced; the pool-level
  ``statement_timeout_ms`` applies to every statement.
- row limiting happens after fetch (``truncated`` is set), because the platform
  adapter does not rewrite SQL.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from platform_core.adapters.metadata_pg import MetadataPg

from .contracts import QueryExecutor, QueryResult  # noqa: F401 - runtime contract


class PostgresQueryExecutor:
    """``QueryExecutor`` over the platform PostgreSQL adapter."""

    engine = "postgres"

    def __init__(
        self,
        dsn: str,
        *,
        pool_max: int = 4,
        max_rows: int = 1000,
        statement_timeout_ms: int | None = None,
        open_timeout_seconds: float = 10.0,
    ) -> None:
        self._max_rows = max_rows
        self._meta = MetadataPg(
            dsn,
            pool_max=pool_max,
            statement_timeout_ms=statement_timeout_ms,
        )
        self._meta.open(retry_seconds=open_timeout_seconds)

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
        limit = min(max_rows, self._max_rows)
        started = time.perf_counter()
        rows = await asyncio.to_thread(self._meta.query, sql, params or ())
        truncated = len(rows) > limit
        rows = rows[:limit]
        return QueryResult(
            rows=rows,
            columns=list(rows[0].keys()) if rows else [],
            row_count=len(rows),
            truncated=truncated,
            duration_ms=int((time.perf_counter() - started) * 1000),
            engine=self.engine,
        )

    async def health_check(self) -> dict[str, Any]:
        """Probe reachability; never raises (COA contract requirement)."""
        try:
            rows = await asyncio.to_thread(self._meta.query, "SELECT 1 AS ok")
            return {"ok": bool(rows), "engine": self.engine}
        except Exception as exc:  # noqa: BLE001 - health_check must not raise
            return {"ok": False, "engine": self.engine, "error": f"{type(exc).__name__}: {exc}"}

    async def close(self) -> None:
        await asyncio.to_thread(self._meta.close)


__all__ = ["PostgresQueryExecutor"]
