"""``postgres``: session metadata in a local PG table.

Drop-in replacement for ``coa_serve.session_metadata.SessionMetadataStore``
(the DynamoDB table). The discovery semantics are preserved:

* ordering is ``lastActiveAt`` descending, with ``sessionId`` as the
  deterministic tie-break DynamoDB gets from its composite sort key;
* ``page_token`` stays an opaque JSON string (``lastActiveAt`` + ``sessionId``)
  so callers never learn which store is behind it;
* ``update_title`` is first-message-wins;
* ``create`` overwrites an existing ``(userId, sessionId)`` like ``put_item``.

The table is created on first connect (``CREATE TABLE IF NOT EXISTS``). This is
a local provider: schema churn belongs to the platform migration runner, not
here, but the DDL is idempotent so a fresh container is ready on startup.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import time
from datetime import UTC, datetime
from typing import Any

import structlog
from coa_ports.dto import SessionMetadataRecord
from platform_core.adapters.metadata_pg import MetadataPg
from ulid import ULID

logger = structlog.get_logger(__name__)

_DEFAULT_TTL_DAYS = 30

_COLUMNS = (
    "user_id, session_id, namespace_id, created_at, last_active_at, "
    "status, message_count, title, ttl"
)

_SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS public.coa_session_metadata (
        user_id      text        NOT NULL,
        session_id   text        NOT NULL,
        namespace_id text        NOT NULL DEFAULT '',
        created_at   timestamptz NOT NULL,
        last_active_at timestamptz NOT NULL,
        status       text        NOT NULL DEFAULT 'active',
        message_count integer    NOT NULL DEFAULT 0,
        title        text        NOT NULL DEFAULT '',
        ttl          bigint      NOT NULL DEFAULT 0,
        PRIMARY KEY (user_id, session_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS coa_session_metadata_recent
        ON public.coa_session_metadata (user_id, last_active_at DESC, session_id DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS coa_session_metadata_ns_recent
        ON public.coa_session_metadata (user_id, namespace_id, last_active_at DESC, session_id DESC)
    """,
)

_SELECT = f"SELECT {_COLUMNS} FROM public.coa_session_metadata"


class SessionMetadataPg:
    """``SessionMetadataPort`` over the platform PG pool."""

    provider = "postgres"

    def __init__(
        self,
        dsn: str,
        *,
        ttl_days: int = _DEFAULT_TTL_DAYS,
        pool_max: int = 4,
        open_timeout_seconds: float = 10.0,
    ) -> None:
        self._ttl_days = ttl_days
        self._meta = MetadataPg(dsn, pool_max=pool_max)
        self._meta.open(retry_seconds=open_timeout_seconds)
        with self._meta.tx() as tx:
            for statement in _SCHEMA:
                tx.execute(statement)

    # ── helpers ─────────────────────────────────────────────────────────────

    def _ttl(self) -> int:
        return int(time.time()) + (self._ttl_days * 86400)

    async def _query(self, sql: str, params: tuple | list = ()) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._meta.query, sql, params)

    async def _execute(self, sql: str, params: tuple | list = ()) -> int:
        return await asyncio.to_thread(self._meta.execute, sql, params)

    @staticmethod
    def _decode_token(page_token: str | None) -> tuple[str | None, str | None]:
        if not page_token:
            return None, None
        try:
            token = json.loads(page_token)
            return token["lastActiveAt"], token["sessionId"]
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            raise ValueError("Invalid page token format") from exc

    async def _page(
        self, sql: str, params: tuple | list, page_token: str | None, limit: int
    ) -> tuple[list[SessionMetadataRecord], str | None]:
        last_active, session_id = self._decode_token(page_token)
        rows = await self._query(sql, (*params, last_active, last_active, session_id, limit))
        sessions = [_row_to_record(row) for row in rows]
        next_token = None
        if len(sessions) == limit and sessions:
            last = sessions[-1]
            next_token = json.dumps({"lastActiveAt": last.last_active_at, "sessionId": last.session_id})
        return sessions, next_token

    # ── port ────────────────────────────────────────────────────────────────

    async def create(
        self,
        user_id: str,
        *,
        namespace_id: str = "",
        session_id: str | None = None,
        title: str = "",
    ) -> SessionMetadataRecord:
        session_id = session_id or str(ULID())
        now = datetime.now(UTC).isoformat()
        ttl = self._ttl()
        await self._execute(
            f"""
            INSERT INTO public.coa_session_metadata ({_COLUMNS})
            VALUES (%s, %s, %s, %s::timestamptz, %s::timestamptz, 'active', 0, %s, %s)
            ON CONFLICT (user_id, session_id) DO UPDATE SET
                namespace_id = EXCLUDED.namespace_id,
                created_at = EXCLUDED.created_at,
                last_active_at = EXCLUDED.last_active_at,
                status = EXCLUDED.status,
                message_count = EXCLUDED.message_count,
                title = EXCLUDED.title,
                ttl = EXCLUDED.ttl
            """,
            (user_id, session_id, namespace_id, now, now, title[:100], ttl),
        )
        logger.info("session_metadata_created", user_id=user_id, session_id=session_id, namespace_id=namespace_id)
        return SessionMetadataRecord(
            user_id=user_id,
            session_id=session_id,
            created_at=now,
            last_active_at=now,
            status="active",
            message_count=0,
            ttl=ttl,
            namespace_id=namespace_id,
            title=title[:100],
        )

    async def get_recent(self, user_id: str) -> SessionMetadataRecord | None:
        rows = await self._query(
            f"{_SELECT} WHERE user_id = %s ORDER BY last_active_at DESC, session_id DESC LIMIT 1",
            (user_id,),
        )
        return _row_to_record(rows[0]) if rows else None

    async def get_recent_for_namespace(self, user_id: str, namespace_id: str) -> SessionMetadataRecord | None:
        rows = await self._query(
            f"{_SELECT} WHERE user_id = %s AND namespace_id = %s "
            "ORDER BY last_active_at DESC, session_id DESC LIMIT 1",
            (user_id, namespace_id),
        )
        return _row_to_record(rows[0]) if rows else None

    async def list_for_namespace(
        self, user_id: str, namespace_id: str, *, limit: int = 20, page_token: str | None = None
    ) -> tuple[list[SessionMetadataRecord], str | None]:
        sql = (
            f"{_SELECT} WHERE user_id = %s AND namespace_id = %s "
            "AND (%s::timestamptz IS NULL OR (last_active_at, session_id) < (%s::timestamptz, %s)) "
            "ORDER BY last_active_at DESC, session_id DESC LIMIT %s"
        )
        return await self._page(sql, (user_id, namespace_id), page_token, limit)

    async def list_sessions(
        self, user_id: str, *, page_token: str | None = None, limit: int = 50
    ) -> tuple[list[SessionMetadataRecord], str | None]:
        sql = (
            f"{_SELECT} WHERE user_id = %s "
            "AND (%s::timestamptz IS NULL OR (last_active_at, session_id) < (%s::timestamptz, %s)) "
            "ORDER BY last_active_at DESC, session_id DESC LIMIT %s"
        )
        return await self._page(sql, (user_id,), page_token, limit)

    async def update_activity(self, user_id: str, session_id: str, namespace_id: str = "") -> None:
        now = datetime.now(UTC).isoformat()
        ttl = self._ttl()
        await self._execute(
            """
            UPDATE public.coa_session_metadata
            SET last_active_at = %s::timestamptz,
                ttl = %s,
                message_count = message_count + 1,
                namespace_id = CASE WHEN %s <> '' THEN %s ELSE namespace_id END
            WHERE user_id = %s AND session_id = %s
            """,
            (now, ttl, namespace_id, namespace_id, user_id, session_id),
        )

    async def update_title(self, user_id: str, session_id: str, title: str) -> None:
        """Set the title only when it is still empty (first-message-wins)."""
        with contextlib.suppress(Exception):
            await self._execute(
                """
                UPDATE public.coa_session_metadata SET title = %s
                WHERE user_id = %s AND session_id = %s AND (title = '' OR title IS NULL)
                """,
                (title[:100], user_id, session_id),
            )

    async def get_session_namespace(self, user_id: str, session_id: str) -> str | None:
        rows = await self._query(
            "SELECT namespace_id FROM public.coa_session_metadata WHERE user_id = %s AND session_id = %s",
            (user_id, session_id),
        )
        return rows[0]["namespace_id"] if rows else None

    async def validate_ownership(self, user_id: str, session_id: str) -> bool:
        rows = await self._query(
            "SELECT 1 AS ok FROM public.coa_session_metadata WHERE user_id = %s AND session_id = %s",
            (user_id, session_id),
        )
        return bool(rows)

    async def delete(self, user_id: str, session_id: str) -> None:
        await self._execute(
            "DELETE FROM public.coa_session_metadata WHERE user_id = %s AND session_id = %s",
            (user_id, session_id),
        )
        logger.info("session_metadata_deleted", user_id=user_id, session_id=session_id)


def _row_to_record(row: dict[str, Any]) -> SessionMetadataRecord:
    return SessionMetadataRecord(
        user_id=row["user_id"],
        session_id=row["session_id"],
        created_at=_iso(row["created_at"]),
        last_active_at=_iso(row["last_active_at"]),
        status=row["status"],
        message_count=int(row["message_count"]),
        ttl=int(row["ttl"]),
        namespace_id=row["namespace_id"],
        title=row["title"],
    )


def _iso(value: Any) -> str:
    return value.isoformat() if isinstance(value, datetime) else str(value)


__all__ = ["SessionMetadataPg"]
