"""Local SQLite implementation of the COA ``MemoryStore`` (N6).

Contract source: ``doc/_design/81-COA契约与platform_core整合方案-2026-11-08.md`` N6 —
``append_turn`` / ``get_window`` / ``search`` / ``delete_session`` / ``gc``.

Retrieval scope, stated rather than hidden: no embedding model ships with this
build, so ``search`` is a case-insensitive substring match over stored text.
Every hit is tagged ``mode="lexical-approx"``; it is **not** semantic retrieval
and must not be presented as such. Turns are stored in the same SQLite file as
``ConversationStore`` (the ``session_turn`` table that N5 ``get_history`` reads).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .conversation_store import SessionNotFound, ensure_schema

SEARCH_MODE = "lexical-approx"


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class TurnRecord:
    turn_id: int
    session_id: str
    role: str
    content: str
    created_at: str


class SqliteMemoryStore:
    """``MemoryStore`` backed by the conversation SQLite file (lexical search only)."""

    backend = "sqlite"

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            ensure_schema(conn)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _record(row: sqlite3.Row) -> TurnRecord:
        return TurnRecord(
            turn_id=row["turn_id"],
            session_id=row["session_id"],
            role=row["role"],
            content=row["content"],
            created_at=row["created_at"],
        )

    # -- N6 ------------------------------------------------------------
    def append_turn(
        self, session_id: str, turn: Mapping[str, Any], *, at: str | None = None
    ) -> TurnRecord:
        """Append one ``{"role", "content"}`` turn to a live session."""
        role = str(turn["role"])
        content = str(turn["content"])
        stamp = at or _now()
        with self._connect() as conn:
            exists = conn.execute(
                "SELECT 1 FROM session_metadata WHERE session_id = ? AND deleted_at IS NULL",
                (session_id,),
            ).fetchone()
            if exists is None:
                raise SessionNotFound(session_id)
            cursor = conn.execute(
                "INSERT INTO session_turn (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (session_id, role, content, stamp),
            )
            turn_id = int(cursor.lastrowid)
        return TurnRecord(turn_id, session_id, role, content, stamp)

    def get_window(self, session_id: str, turns: int = 10) -> list[TurnRecord]:
        """The last ``turns`` turns of a session, oldest first."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT turn_id, session_id, role, content, created_at FROM session_turn "
                "WHERE session_id = ? ORDER BY turn_id DESC LIMIT ?",
                (session_id, max(turns, 0)),
            ).fetchall()
        return [self._record(row) for row in reversed(rows)]

    def search(self, namespace: str, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Lexical substring search scoped to a namespace (not semantic retrieval)."""
        if not query:
            return []
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT t.turn_id, t.session_id, t.role, t.content, t.created_at "
                "FROM session_turn AS t JOIN session_metadata AS m ON m.session_id = t.session_id "
                "WHERE m.deleted_at IS NULL AND m.namespace = ? "
                "AND t.content LIKE ? ESCAPE '\\' "
                "ORDER BY t.turn_id DESC LIMIT ?",
                (namespace, f"%{escaped}%", max(top_k, 0)),
            ).fetchall()
        return [
            {
                **self._record(row).__dict__,
                "score": 1.0,
                "mode": SEARCH_MODE,
            }
            for row in rows
        ]

    def delete_session(self, session_id: str) -> int:
        """Hard-delete every turn of a session; returns the number removed."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM session_turn WHERE session_id = ?", (session_id,))
        return int(cursor.rowcount)

    def gc(self, expires_before: str) -> int:
        """Delete turns created before an ISO timestamp; returns the number removed."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM session_turn WHERE created_at < ?", (expires_before,)
            )
        return int(cursor.rowcount)

    # -- ops -----------------------------------------------------------
    def health_check(self) -> dict[str, Any]:
        try:
            with self._connect() as conn:
                total = conn.execute("SELECT count(*) AS n FROM session_turn").fetchone()["n"]
            return {
                "ok": True,
                "backend": self.backend,
                "path": str(self._path),
                "turns": int(total),
                "search_mode": SEARCH_MODE,
            }
        except Exception as exc:  # noqa: BLE001 - health_check must not raise
            return {
                "ok": False,
                "backend": self.backend,
                "path": str(self._path),
                "error": f"{type(exc).__name__}: {exc}",
            }


__all__ = ["SEARCH_MODE", "SqliteMemoryStore", "TurnRecord"]
