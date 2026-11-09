"""Port to the Answering & Retrieval context (replaces AgentCore Runtime HTTP).

This is a transport port: it carries a contract envelope, not domain objects.
The data layer uses it for ``Query`` / ``Translate`` / ``KBSearch`` /
``GraphTraverse``; ``ANSWER`` carries the extension ``GetAnswer`` call.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from ..dto import ContextRequest, ContextResponse


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
