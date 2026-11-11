"""PostgreSQL connection management for the platform database.

R2 of the platform-core teardown: the pool, ``query``/``execute``, ``tx`` and
``advisory_lock`` used to live in ``platform_core.adapters.metadata_pg``. They
are connection plumbing, not platform business logic, and every COA provider
that touches PostgreSQL needs them. So the single implementation lives here and
``MetadataPg`` becomes a thin forwarder.

This module deliberately imports psycopg (module level) while the rest of
``platform_db`` (registry, runner, migrations) does not: importing the package
must stay cheap for callers that only need the version gate or the chain.
Anything that imports this module is already a PostgreSQL client.

Errors are this module's own type. The platform-core adapter maps them to
``platform_core.errors.PortError`` so its callers keep seeing one error family;
COA providers that move here later see ``PgUnavailableError`` directly.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from coa_control_plane.platform_db.registry import (
    MIGRATION_GAP_HINT,
    RETIRED_MIGRATION_VERSIONS,
    SUPPORTED_SCHEMA_VERSION,
)
from coa_control_plane.platform_db.runner import AfterApply, apply_migrations

log = logging.getLogger(__name__)


class PgUnavailableError(RuntimeError):
    """The pool is not open or cannot reach PostgreSQL.

    Fields mirror what ``platform_core.errors.PortError`` needs, so the legacy
    adapter translates this without re-parsing a message.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str = "Unavailable",
        provider_code: str = "E_DB_UNAVAILABLE",
        retryable: bool = True,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.provider_code = provider_code
        self.retryable = retryable


class Tx:
    """Statement helpers scoped to one transaction on one connection."""

    def __init__(self, conn: Any) -> None:
        self._conn = conn

    def query(self, sql: str, params: tuple | list = ()) -> list[dict[str, Any]]:
        return self._conn.execute(sql, params).fetchall()

    def execute(self, sql: str, params: tuple | list = ()) -> int:
        return self._conn.execute(sql, params).rowcount

    def execute_returning(self, sql: str, params: tuple | list = ()) -> list[dict[str, Any]]:
        return self._conn.execute(sql, params).fetchall()

    def executemany(self, sql: str, params: list[tuple | list]) -> int:
        """Bulk insert/update inside the caller's transaction."""
        if not params:
            return 0
        with self._conn.cursor() as cursor:
            cursor.executemany(sql, params)
            return cursor.rowcount


class PgPool:
    """psycopg 3 pool with ``dict_row`` over the platform database.

    The constructor only stores settings; ``open()`` creates the pool, so a
    provider can be built before the database is reachable (and tests can point
    at a dead port to exercise the unavailable path).
    """

    port = "MetadataStore"

    def __init__(
        self,
        url: str,
        pool_max: int = 10,
        statement_timeout_ms: int | None = None,
        trgm_word_similarity_threshold: float | None = None,
    ) -> None:
        self._url = url
        self._pool_max = pool_max
        self._statement_timeout_ms = statement_timeout_ms
        # S16: `q.raw <% c.text` (pg_trgm word similarity) is GIN-indexable only
        # at a lowered threshold. The session value must equal search.min_similarity.
        self._trgm_threshold = trgm_word_similarity_threshold
        self._pool: ConnectionPool | None = None

    def open(self, retry_seconds: float = 60.0) -> None:
        if self._pool is not None:
            return
        kwargs: dict[str, Any] = {"row_factory": dict_row}
        options: list[str] = []
        if self._statement_timeout_ms:
            options.append(f"statement_timeout={self._statement_timeout_ms}")
        if self._trgm_threshold is not None:
            options.append(f"pg_trgm.word_similarity_threshold={self._trgm_threshold}")
        if options:
            kwargs["options"] = "-c " + " -c ".join(options)
        self._pool = ConnectionPool(
            conninfo=self._url,
            min_size=1,
            max_size=self._pool_max,
            open=False,
            timeout=10,
            kwargs=kwargs,
        )
        try:
            self._pool.open(wait=True, timeout=retry_seconds)
        except Exception as exc:  # psycopg_pool.PoolTimeout / OperationalError
            self._pool = None
            raise PgUnavailableError(f"cannot connect to PostgreSQL: {exc}") from exc

    def close(self) -> None:
        if self._pool is not None:
            self._pool.close()
            self._pool = None

    def _require_pool(self) -> ConnectionPool:
        if self._pool is None:
            raise PgUnavailableError("metadata pool is not open")
        return self._pool

    def query(self, sql: str, params: tuple | list = ()) -> list[dict[str, Any]]:
        with self._require_pool().connection() as conn:
            return conn.execute(sql, params).fetchall()

    def execute(self, sql: str, params: tuple | list = ()) -> int:
        with self._require_pool().connection() as conn:
            return conn.execute(sql, params).rowcount

    @contextmanager
    def tx(self) -> Iterator[Tx]:
        with self._require_pool().connection() as conn:
            with conn.transaction():
                yield Tx(conn)

    @contextmanager
    def advisory_lock(self, key: str, blocking: bool = False) -> Iterator[bool]:
        """Session-scoped advisory lock. Yields True when acquired."""
        with self._require_pool().connection() as conn:
            fn = "pg_advisory_lock" if blocking else "pg_try_advisory_lock"
            row = conn.execute(f"SELECT {fn}(hashtext(%s)) AS ok", (key,)).fetchone()
            acquired = bool(row["ok"]) if row else False
            try:
                yield acquired
            finally:
                if acquired:
                    conn.execute("SELECT pg_advisory_unlock(hashtext(%s))", (key,))

    def migrate(
        self,
        *,
        registry: list[tuple[int, str, str]] | None = None,
        supported_version: int | None = None,
        retired_versions: tuple[int, ...] = RETIRED_MIGRATION_VERSIONS,
        gap_hint: str = MIGRATION_GAP_HINT,
        after_apply: AfterApply | None = None,
    ) -> dict[str, Any]:
        """Apply the registered migrations above the recorded version.

        Refusals raise ``MigrationGateError``; callers map it to their own error
        type. ``after_apply`` runs inside the migration transaction, so a hook
        failure rolls back the whole run.
        """
        supported = SUPPORTED_SCHEMA_VERSION if supported_version is None else supported_version
        with self._require_pool().connection() as conn:
            applied = apply_migrations(
                conn,
                registry=registry,
                supported_version=supported,
                retired_versions=retired_versions,
                gap_hint=gap_hint,
                after_apply=after_apply,
            )
        log.info("migration applied", extra={"event": {"event": "migrate", "to": applied}})
        return {"to": str(supported), "applied": applied}


__all__: list[str] = ["PgPool", "PgUnavailableError", "Tx"]
