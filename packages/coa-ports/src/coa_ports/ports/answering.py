"""Port to the Answering & Retrieval context (replaces AgentCore Runtime HTTP).

This is a transport port: it carries a contract envelope, not domain objects.
The data layer uses it for ``Query`` / ``Translate`` / ``KBSearch`` /
``GraphTraverse``; ``ANSWER`` carries the extension ``GetAnswer`` call.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from ..dto import ContextRequest, ContextResponse, MetricHit, MetricRecord


@runtime_checkable
class ContextManagerPort(Protocol):
    """Async request/response boundary to the Answering & Retrieval context.

    Implementations raise :class:`coa_ports.errors.PortError`:
    ``unavailable`` for transport failure, ``timeout`` for a deadline
    overrun, ``invalid_argument`` when the remote rejects the request,
    ``not_found`` when the namespace or resource does not exist.
    """

    async def invoke(self, request: ContextRequest) -> ContextResponse:
        """Send one contract request and return the shaped response."""
        ...

    async def health_check(self) -> Mapping[str, Any]:
        """Probe reachability; never raises (COA contract requirement)."""
        ...


@runtime_checkable
class MetricIndexPort(Protocol):
    """Searchable index of metric definitions (replaces the metric-service AOSS index).

    Deliberately separate from ``VectorClient``: the metric index is searched by
    description over metric records and returns ``MetricHit``, while
    ``VectorClient`` returns document-chunk ``VectorHit``. Mapping one to the
    other would be a business rewrite, not a thin shell.

    ``index`` / ``remove`` maintain a derived index. A provider that answers
    ``search`` from the system of record (the local PostgreSQL provider reads
    ``platform.metric_definition`` directly) implements them as documented
    no-ops; that is not a fallback, because there is no stale copy to update.
    """

    async def index(self, record: MetricRecord) -> None:
        """Make ``record`` findable; re-indexing the same name replaces it."""
        ...

    async def remove(self, namespace: str, name: str) -> None:
        """Drop ``record`` from the index; removing an absent name is a no-op."""
        ...

    async def search(self, namespace: str, query: str, *, top_k: int = 5) -> tuple[MetricHit, ...]:
        """Return the best matches inside ``namespace``, best first."""
        ...

    async def probe(self) -> Mapping[str, Any]:
        """Reachability snapshot; never raises."""
        ...
