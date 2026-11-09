"""Change-feed port (replaces DynamoDB Streams).

A change feed returns opaque cursors. Consumers compare ``ChangeBatch.next_cursor``
with the cursor they hold; they never parse it.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..dto import ChangeBatch
from ..language import Cursor


@runtime_checkable
class ChangeFeedPort(Protocol):
    """Read ordered change records from one stream."""

    async def read(
        self,
        stream: str,
        *,
        cursor: Cursor | None = None,
        limit: int = 100,
    ) -> ChangeBatch:
        """Read up to ``limit`` records after ``cursor``.

        ``cursor=None`` means "from the oldest retained record". A provider
        that cannot honour the cursor raises ``invalid_argument``; it never
        silently restarts from the beginning.
        """
        ...

    async def checkpoint(self, stream: str, cursor: Cursor) -> None:
        """Persist the consumer's progress for ``stream``."""
        ...
