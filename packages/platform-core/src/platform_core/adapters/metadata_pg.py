"""MetadataStore adapter: PostgreSQL (psycopg 3 + pool)."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator

from coa_control_plane.platform_db import (
    MIGRATION_GAP_HINT,
    MIGRATIONS,
    RETIRED_MIGRATION_VERSIONS,
    SUPPORTED_SCHEMA_VERSION,
    MigrationGateError,
)
from coa_control_plane.platform_db import apply_migrations as _apply_migrations
from coa_control_plane.platform_db import migration_gap_versions as _migration_gap_versions
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from ..errors import EXIT_CONFIG, PlatformError, PortError
from ..ports import Manifest

log = logging.getLogger(__name__)


def migration_gap_versions(
    current: int,
    history: set[int] | None,
    registry: list[tuple[int, str, str]] | None = None,
) -> list[int]:
    """Legacy entry point; the implementation lives in platform_db.

    Reads this module's ``MIGRATIONS`` so callers that inject a registry by
    patching ``metadata_pg.MIGRATIONS`` keep the old behaviour.
    """
    return _migration_gap_versions(
        current, history, MIGRATIONS if registry is None else registry
    )


class Tx:
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


class MetadataPg:
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

    def manifest(self) -> Manifest:
        return Manifest(
            provider="postgres",
            port=self.port,
            capabilities=["db.tx", "db.query", "db.advisory_lock", "db.migrate"],
            provider_version="pg18",
            notes={"client": "psycopg3"},
        )

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
            raise PortError(
                code="Unavailable",
                message=f"cannot connect to PostgreSQL: {exc}",
                provider="postgres",
                provider_code="E_DB_UNAVAILABLE",
                retryable=True,
            ) from exc

    def close(self) -> None:
        if self._pool is not None:
            self._pool.close()
            self._pool = None

    def _require_pool(self) -> ConnectionPool:
        if self._pool is None:
            raise PortError(
                code="Unavailable",
                message="metadata pool is not open",
                provider="postgres",
                provider_code="E_DB_UNAVAILABLE",
                retryable=True,
            )
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

    def migrate(self) -> dict[str, Any]:
        """Apply forward migrations idempotently; refuses a newer schema.

        The chain itself lives in ``coa_control_plane.platform_db``; this method
        only supplies the pool connection, the legacy registry binding (so
        callers patching ``MIGRATIONS`` keep working) and the post-migration
        binding replay, which is still platform-core code.
        """
        applied: list[str] = []
        with self._require_pool().connection() as conn:
            try:
                applied = _apply_migrations(
                    conn,
                    registry=MIGRATIONS,
                    supported_version=SUPPORTED_SCHEMA_VERSION,
                    retired_versions=RETIRED_MIGRATION_VERSIONS,
                    gap_hint=MIGRATION_GAP_HINT,
                    after_apply=self._replay_published_bindings,
                )
            except MigrationGateError as exc:
                raise PlatformError(
                    code=exc.code,
                    detail=exc.detail,
                    stage="db",
                    key="schema_version",
                    provider="postgres",
                    hint=exc.hint,
                    exit_code=EXIT_CONFIG,
                ) from exc
        log.info("migration applied", extra={"event": {"event": "migrate", "to": applied}})
        return {"to": str(SUPPORTED_SCHEMA_VERSION), "applied": applied}

    @staticmethod
    def _replay_published_bindings(conn: Any) -> None:
        # Seed scripts (V25 ON CONFLICT DO UPDATE) can rewind later binding fixes.
        # Replay the published registry on every migrate(), including no-op runs.
        reg = conn.execute("SELECT to_regclass('platform.metric_field_binding') AS reg").fetchone()
        if reg and reg["reg"]:
            from ..metric_binding_overrides import replay_binding_overrides

            replay_binding_overrides(conn)

    def health(self) -> None:
        self.query("SELECT 1 AS ok")

    def count_blobs(self) -> int:
        rows = self.query("SELECT COUNT(*) AS n FROM platform.blob WHERE state = 'committed'")
        return int(rows[0]["n"]) if rows else 0

    def count_refs(self) -> int:
        rows = self.query("SELECT COUNT(*) AS n FROM platform.blob_ref")
        return int(rows[0]["n"]) if rows else 0
