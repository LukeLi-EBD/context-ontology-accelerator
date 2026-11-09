"""Local SQLite implementation of the COA ``ConversationStore`` (N5).

Contract source: ``doc/_design/81-COA契约与platform_core整合方案-2026-11-08.md`` N5 —
``create / validate_ownership / update_activity / list_sessions / get_history / delete``
with ``SessionNotFound`` and ``SessionForbidden``.

Turns are written by ``MemoryStore`` (N6, ``COA_PROVIDER_MEMORY=sqlite``) into
the same ``session_turn`` table, so ``get_history`` returns real turns once a
memory store shares this file. Everything session-side is real: rows are
persisted in SQLite and survive process restarts.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class SessionNotFound(LookupError):
    """No live session with that id (deleted and expired read as missing)."""


class SessionForbidden(PermissionError):
    """The user does not own the session."""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create the session tables once; shared by ConversationStore and MemoryStore."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS session_metadata (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            namespace TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_activity_at TEXT NOT NULL,
            deleted_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS session_turn (
            turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )


@dataclass(frozen=True)
class SessionRecord:
    session_id: str
    user_id: str
    namespace: str
    title: str
    created_at: str
    last_activity_at: str


class SqliteConversationStore:
    """``ConversationStore`` backed by one SQLite file (no server, no AWS)."""

    TABLE = "session_metadata"

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    @property
    def backend(self) -> str:
        return "sqlite"

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            ensure_schema(conn)

    @staticmethod
    def _record(row: sqlite3.Row) -> SessionRecord:
        return SessionRecord(
            session_id=row["session_id"],
            user_id=row["user_id"],
            namespace=row["namespace"],
            title=row["title"],
            created_at=row["created_at"],
            last_activity_at=row["last_activity_at"],
        )

    def _live(self, conn: sqlite3.Connection, session_id: str) -> sqlite3.Row:
        row = conn.execute(
            f"SELECT * FROM {self.TABLE} WHERE session_id = ? AND deleted_at IS NULL", (session_id,)
        ).fetchone()
        if row is None:
            raise SessionNotFound(session_id)
        return row

    # -- N5 ------------------------------------------------------------
    def create(self, user_id: str, namespace: str, title: str) -> SessionRecord:
        session_id = str(uuid.uuid4())
        stamp = _now()
        with self._connect() as conn:
            conn.execute(
                f"INSERT INTO {self.TABLE} (session_id, user_id, namespace, title, created_at, last_activity_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, user_id, namespace, title, stamp, stamp),
            )
        return SessionRecord(session_id, user_id, namespace, title, stamp, stamp)

    def validate_ownership(self, user_id: str, session_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT user_id FROM {self.TABLE} WHERE session_id = ? AND deleted_at IS NULL", (session_id,)
            ).fetchone()
        return row is not None and row["user_id"] == user_id

    def update_activity(self, session_id: str, *, at: str | None = None) -> SessionRecord:
        stamp = at or _now()
        with self._connect() as conn:
            row = self._live(conn, session_id)
            conn.execute(
                f"UPDATE {self.TABLE} SET last_activity_at = ? WHERE session_id = ?", (stamp, session_id)
            )
        return SessionRecord(
            session_id=row["session_id"],
            user_id=row["user_id"],
            namespace=row["namespace"],
            title=row["title"],
            created_at=row["created_at"],
            last_activity_at=stamp,
        )

    def list_sessions(
        self, user_id: str, *, namespace: str | None = None, limit: int = 50
    ) -> list[SessionRecord]:
        sql = f"SELECT * FROM {self.TABLE} WHERE user_id = ? AND deleted_at IS NULL"
        params: list[Any] = [user_id]
        if namespace:
            sql += " AND namespace = ?"
            params.append(namespace)
        sql += " ORDER BY last_activity_at DESC LIMIT ?"
        params.append(max(limit, 0))
        with self._connect() as conn:
            return [self._record(row) for row in conn.execute(sql, params).fetchall()]

    def get_history(
        self, session_id: str, *, limit: int = 50, before: str | None = None
    ) -> list[dict[str, Any]]:
        sql = "SELECT turn_id, role, content, created_at FROM session_turn WHERE session_id = ?"
        params: list[Any] = [session_id]
        if before:
            sql += " AND created_at < ?"
            params.append(before)
        sql += " ORDER BY turn_id DESC LIMIT ?"
        params.append(max(limit, 0))
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in reversed(rows)]

    def delete(self, session_id: str) -> None:
        with self._connect() as conn:
            self._live(conn, session_id)
            conn.execute(f"UPDATE {self.TABLE} SET deleted_at = ? WHERE session_id = ?", (_now(), session_id))

    # -- ops -----------------------------------------------------------
    def health_check(self) -> dict[str, Any]:
        try:
            with self._connect() as conn:
                live = conn.execute(
                    f"SELECT count(*) AS n FROM {self.TABLE} WHERE deleted_at IS NULL"
                ).fetchone()["n"]
            return {"ok": True, "backend": self.backend, "path": str(self._path), "sessions": int(live)}
        except Exception as exc:  # noqa: BLE001 - health_check must not raise
            return {"ok": False, "backend": self.backend, "path": str(self._path), "error": f"{type(exc).__name__}: {exc}"}

    def to_dict(self, record: SessionRecord) -> dict[str, Any]:
        return asdict(record)


__all__ = [
    "SessionForbidden",
    "SessionNotFound",
    "SessionRecord",
    "SqliteConversationStore",
]
