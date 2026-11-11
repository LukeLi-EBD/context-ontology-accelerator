"""MetadataStore adapter: PostgreSQL (psycopg 3 + pool).

Since R2 the connection management (pool, ``query``/``execute``, ``tx``,
``advisory_lock``, ``migrate`` plumbing) lives in
``coa_control_plane.platform_db.connection`` and exists only once. This module
is the platform-core face of that implementation: it keeps the historical
import path, adds the ``MetadataStore`` manifest, and maps the platform_db
errors onto ``platform_core.errors`` so existing callers are unaffected.
"""

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
from coa_control_plane.platform_db import migration_gap_versions as _migration_gap_versions
from coa_control_plane.platform_db.connection import PgPool, PgUnavailableError, Tx

from ..errors import EXIT_CONFIG, PlatformError, PortError
from ..ports import Manifest

log = logging.getLogger(__name__)

__all__ = [
    "MIGRATION_GAP_HINT",
    "MIGRATIONS",
    "RETIRED_MIGRATION_VERSIONS",
    "SUPPORTED_SCHEMA_VERSION",
    "MetadataPg",
    "Tx",
    "migration_gap_versions",
]


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


def _port_error(exc: PgUnavailableError) -> PortError:
    """Translate the platform_db connection error into the platform error."""
    return PortError(
        code=exc.code,
        message=str(exc),
        provider="postgres",
        provider_code=exc.provider_code,
        retryable=exc.retryable,
    )


@contextmanager
def _translated() -> Iterator[None]:
    """Map ``PgUnavailableError`` raised inside the block (incl. ``__enter__``)."""
    try:
        yield
    except PgUnavailableError as exc:
        raise _port_error(exc) from exc


class MetadataPg:
    port = "MetadataStore"

    def __init__(
        self,
        url: str,
        pool_max: int = 10,
        statement_timeout_ms: int | None = None,
        trgm_word_similarity_threshold: float | None = None,
    ) -> None:
        self._pool = PgPool(
            url,
            pool_max=pool_max,
            statement_timeout_ms=statement_timeout_ms,
            trgm_word_similarity_threshold=trgm_word_similarity_threshold,
        )

    def manifest(self) -> Manifest:
        return Manifest(
            provider="postgres",
            port=self.port,
            capabilities=["db.tx", "db.query", "db.advisory_lock", "db.migrate"],
            provider_version="pg18",
            notes={"client": "psycopg3"},
        )

    def open(self, retry_seconds: float = 60.0) -> None:
        with _translated():
            self._pool.open(retry_seconds=retry_seconds)

    def close(self) -> None:
        self._pool.close()

    def query(self, sql: str, params: tuple | list = ()) -> list[dict[str, Any]]:
        with _translated():
            return self._pool.query(sql, params)

    def execute(self, sql: str, params: tuple | list = ()) -> int:
        with _translated():
            return self._pool.execute(sql, params)

    @contextmanager
    def tx(self) -> Iterator[Tx]:
        with _translated():
            with self._pool.tx() as tx:
                yield tx

    @contextmanager
    def advisory_lock(self, key: str, blocking: bool = False) -> Iterator[bool]:
        """Session-scoped advisory lock. Yields True when acquired."""
        with _translated():
            with self._pool.advisory_lock(key, blocking=blocking) as acquired:
                yield acquired

    def migrate(self) -> dict[str, Any]:
        """Apply forward migrations idempotently; refuses a newer schema.

        The chain and the pool live in ``coa_control_plane.platform_db``; this
        method only supplies the legacy registry binding (so callers patching
        ``MIGRATIONS`` keep working), the post-migration binding replay, which
        is still platform-core code, and the platform error mapping.
        """
        try:
            with _translated():
                return self._pool.migrate(
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
