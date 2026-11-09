"""Session metadata port (replaces the SESSION_METADATA DynamoDB table).

The serve layer keeps a small discovery index per user: which sessions exist,
which one was active last, and in which namespace. Message content is not here
(it stays in AgentCore Memory).

Every method is async and mirrors ``SessionMetadataStore``'s DynamoDB contract,
including the opaque ``page_token`` strings, so switching the backing store does
not change the call sites in ``session_actions``.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..dto import SessionMetadataRecord


@runtime_checkable
class SessionMetadataPort(Protocol):
    async def create(
        self,
        user_id: str,
        *,
        namespace_id: str = "",
        session_id: str | None = None,
        title: str = "",
    ) -> SessionMetadataRecord: ...

    async def get_recent(self, user_id: str) -> SessionMetadataRecord | None: ...

    async def get_recent_for_namespace(
        self, user_id: str, namespace_id: str
    ) -> SessionMetadataRecord | None: ...

    async def list_for_namespace(
        self,
        user_id: str,
        namespace_id: str,
        *,
        limit: int = 20,
        page_token: str | None = None,
    ) -> tuple[list[SessionMetadataRecord], str | None]: ...

    async def update_activity(self, user_id: str, session_id: str, namespace_id: str = "") -> None: ...

    async def update_title(self, user_id: str, session_id: str, title: str) -> None: ...

    async def get_session_namespace(self, user_id: str, session_id: str) -> str | None: ...

    async def validate_ownership(self, user_id: str, session_id: str) -> bool: ...

    async def delete(self, user_id: str, session_id: str) -> None: ...

    async def list_sessions(
        self,
        user_id: str,
        *,
        page_token: str | None = None,
        limit: int = 50,
    ) -> tuple[list[SessionMetadataRecord], str | None]: ...
