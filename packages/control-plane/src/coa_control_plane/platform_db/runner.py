"""Forward-only migration runner for the platform database schema.

The runner is connection-oriented on purpose: it does not import psycopg and
does not own a pool, so the same code runs behind ``MetadataPg``'s pool, a
one-off bootstrap connection, or a test double. The caller owns the connection
and the post-migration hooks (e.g. replaying published metric bindings, which
still lives in ``platform-core`` until R3).

Ordering and refusal semantics are unchanged from the platform-core original:
transaction-scoped advisory lock, refuse a newer schema, refuse a gap, apply
only versions above the recorded high-water mark, record each version.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from coa_control_plane.platform_db.registry import (
    MIGRATION_GAP_HINT,
    MIGRATIONS,
    RETIRED_MIGRATION_VERSIONS,
    SUPPORTED_SCHEMA_VERSION,
    migration_gap_versions,
    migration_text,
)
from coa_control_plane.platform_db.sqlsplit import split_sql_statements

AfterApply = Callable[[Any], None]


class MigrationGateError(RuntimeError):
    """A migration was refused; the caller maps it to its own error type.

    Attributes mirror what ``platform_core.errors.PlatformError`` needs so the
    legacy adapter can translate without re-parsing a string.
    """

    def __init__(self, code: str, detail: str, hint: str) -> None:
        """Store the refusal as fields so adapters can map it 1:1."""
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.hint = hint


def apply_migrations(
    conn: Any,
    *,
    registry: list[tuple[int, str, str]] | None = None,
    supported_version: int | None = None,
    retired_versions: tuple[int, ...] = RETIRED_MIGRATION_VERSIONS,
    gap_hint: str = MIGRATION_GAP_HINT,
    after_apply: AfterApply | None = None,
) -> list[str]:
    """Apply migrations above the recorded version on an open connection.

    Runs inside its own transaction (``conn.transaction()``); the advisory lock
    is transaction-scoped, so a failed run leaves no lock and no partial rows.
    Returns the applied versions in apply order, e.g. ``["V1", "V2"]``.
    """
    rows = registry if registry is not None else MIGRATIONS
    supported = SUPPORTED_SCHEMA_VERSION if supported_version is None else supported_version
    applied: list[str] = []

    with conn.transaction():
        # Transaction-scoped lock: released automatically on commit/rollback.
        conn.execute("SELECT pg_advisory_xact_lock(hashtext('platform:migrate'))")
        existing = conn.execute(
            "SELECT to_regclass('platform.schema_version') AS reg"
        ).fetchone()
        current = 0
        history: set[int] | None = None
        if existing and existing["reg"]:
            history = {
                int(row["version"])
                for row in conn.execute("SELECT version FROM platform.schema_version").fetchall()
            }
            row = conn.execute(
                "SELECT COALESCE(MAX(version), 0) AS v FROM platform.schema_version"
            ).fetchone()
            current = int(row["v"])
            if current > supported:
                raise MigrationGateError(
                    code="E_DB_MIGRATION_MISMATCH",
                    detail=(
                        f"database schema version {current} is newer than "
                        f"code version {supported}"
                    ),
                    hint="run the matching platform image; do not downgrade data",
                )
        gaps = migration_gap_versions(current, history, rows)
        if gaps:
            raise MigrationGateError(
                code="E_DB_MIGRATION_GAP",
                detail=(
                    f"registered migrations {gaps} are at or below current version "
                    f"{current} but have no row in platform.schema_version; "
                    f"retired versions {list(retired_versions)} are exempt; "
                    f"{gap_hint}"
                ),
                hint=gap_hint,
            )
        for version, filename, description in rows:
            if version <= current:
                continue
            for statement in split_sql_statements(migration_text(filename)):
                conn.execute(statement)
            conn.execute(
                "INSERT INTO platform.schema_version (version, description) VALUES (%s, %s) "
                "ON CONFLICT (version) DO NOTHING",
                (version, description),
            )
            applied.append(f"V{version}")
        if after_apply is not None:
            after_apply(conn)
    return applied


__all__: list[str] = ["AfterApply", "MigrationGateError", "apply_migrations"]
