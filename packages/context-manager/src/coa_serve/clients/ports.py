"""Resolve the context-manager's upstream clients through the runtime catalog.

Each client used to be constructed against an AWS endpoint unconditionally.
Now each one comes from exactly one ``COA_PROVIDER_*`` key (graph, vector, ...),
and a missing or unknown value raises :class:`ConfigurationError` at init. There
is no fallback to ``NEPTUNE_ENDPOINT`` / ``OPENSEARCH_ENDPOINT``: an unconfigured
backend must be visible, not silently replaced by an AWS call.
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


def _resolve(interface: str) -> Any:
    from coa_runtime.registry import resolve
    from coa_runtime.settings import Settings

    resolution = resolve(interface, Settings.from_environ())
    logger.info("upstream_client_resolved", interface=interface, provider=resolution.provider)
    return resolution.instance


class GraphClientAdapter:
    """The pipeline's ``GraphClient`` view over a catalog-resolved provider.

    ``MetricResolver`` passes ``max_results=`` to ``query``; the catalog's graph
    providers expose the port's ``query(sparql)`` and apply their own row cap, so
    the keyword is accepted here and dropped.
    """

    def __init__(self, inner: Any) -> None:
        self._inner = inner

    async def query(
        self, sparql: str, *, max_results: int | None = None
    ) -> list[dict[str, Any]]:
        del max_results  # the provider's store enforces its own row cap
        return await self._inner.query(sparql)

    async def ask(self, sparql: str) -> bool:
        return await self._inner.ask(sparql)

    async def health_check(self) -> dict[str, Any]:
        return await self._inner.health_check()

    async def close(self) -> None:
        close = getattr(self._inner, "close", None)
        if close is not None:
            await close()


def resolve_graph_client() -> GraphClientAdapter:
    """``COA_PROVIDER_GRAPH`` -> the async graph client the pipeline uses."""
    return GraphClientAdapter(_resolve("GraphClient"))


def resolve_vector_client() -> Any:
    """``COA_PROVIDER_VECTOR`` -> the async vector client the pipeline uses."""
    return _resolve("VectorClient")


def resolve_authorization_port() -> Any | None:
    """``COA_PROVIDER_AUTHORIZATION`` -> the policy/grant source, or ``None``.

    ``None`` means the key is absent: the caller keeps its legacy behaviour (the
    Roles table when ``ROLES_TABLE_NAME`` is set, otherwise a fail-closed deny).
    A key that IS set but cannot be resolved raises, so a typo or a missing
    ``COA_AUTHORIZATION_FILE`` is loud instead of silently disabling policy
    loading.
    """
    from coa_runtime.settings import Settings

    if Settings.from_environ().get("COA_PROVIDER_AUTHORIZATION") is None:
        return None
    return _resolve("AuthorizationPolicies")


__all__ = [
    "GraphClientAdapter",
    "resolve_authorization_port",
    "resolve_graph_client",
    "resolve_vector_client",
]
