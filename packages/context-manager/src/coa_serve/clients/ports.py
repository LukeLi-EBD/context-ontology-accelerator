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


class PortEmbedding:
    """The single-text ``embed`` COA's clients call, over the ``Embedding`` port.

    The port's ``embed`` is batch-shaped (``list[str] -> list[list[float]]``),
    while every call site here embeds one query or one document chunk. This
    adapter is that shape conversion and nothing else.
    """

    provider = "catalog"

    def __init__(self, inner: Any) -> None:
        self._inner = inner

    @property
    def model(self) -> str:
        """The provider's model name, when it publishes one (for ``kbSearch``)."""
        return str(getattr(self._inner, "model", "") or "")

    async def embed(self, text: str) -> list[float]:
        vectors = await self._inner.embed([text])
        if not vectors:
            raise ValueError("embedding provider returned no vector")
        return list(vectors[0])


class ChatWithPortEmbedding:
    """Chat stays on its client; ``embed`` is served by the embedding port.

    ``converse``/``converse_stream``/``health_check``/``model_id``/``close``
    delegate to the chat client, so every existing call site is unchanged. Only
    the embedding call is redirected — the two Bedrock surfaces are separate
    port shapes and are injected separately.
    """

    def __init__(self, chat: Any, embedding: Any) -> None:
        self._chat = chat
        self._embedding = embedding

    def __getattr__(self, name: str) -> Any:
        return getattr(self._chat, name)

    @property
    def embedding_model(self) -> str:
        """Model that produced the query vector (the embedding port's, not chat's)."""
        return str(getattr(self._embedding, "model", "") or "")

    async def embed(self, text: str) -> list[float]:
        return await self._embedding.embed(text)


def resolve_chat_client(config: Any) -> Any:
    """``COA_PROVIDER_LLM`` -> the chat client, else the legacy Bedrock client.

    A configured key wins even when it names ``openai-compatible``/``openai-http``;
    an unresolvable key raises at init. With no key the Bedrock client is kept, so
    existing deployments are unchanged until they opt in.
    """
    from coa_runtime.settings import Settings

    if Settings.from_environ().get("COA_PROVIDER_LLM") is not None:
        return _resolve("LLMClient")
    from .bedrock import BedrockLLMClient

    return BedrockLLMClient(
        model_id=config.bedrock_model_id, region=config.bedrock_region
    )


def resolve_query_executor() -> Any | None:
    """``COA_PROVIDER_QUERY_EXECUTOR`` -> the SQL executor, else ``None``.

    ``None`` keeps the legacy Athena/JDBC/Redshift composite, which is what an
    AWS deployment without the key still needs. A configured key resolves through
    the catalog and never falls back: ``athena``/``redshift`` are registered but
    unimplemented there and raise ``ProviderNotAvailableError`` instead of
    quietly building an AWS client.
    """
    from coa_runtime.settings import Settings

    if Settings.from_environ().get("COA_PROVIDER_QUERY_EXECUTOR") is not None:
        return _resolve("QueryExecutor")
    return None


def resolve_embedding_client() -> PortEmbedding:
    """``COA_PROVIDER_EMBEDDING`` -> the single-text embedding adapter.

    Required: a missing key or an unknown provider raises at init, exactly like
    the graph/vector keys. There is no fallback to Bedrock embeddings.
    """
    return PortEmbedding(_resolve("Embedding"))


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


def resolve_session_metadata(config: Any) -> Any | None:
    """``COA_PROVIDER_SESSION_METADATA`` -> the session discovery index.

    ``None`` only when nothing is configured at all (the index is optional and
    was already off in that case): no provider key and no
    ``SESSION_METADATA_TABLE``. With the key unset but the table configured, the
    legacy DynamoDB store is kept. A key that is set but cannot be resolved
    raises, so a typo or a missing DSN never silently disables the index.
    """
    from coa_runtime.settings import Settings

    if Settings.from_environ().get("COA_PROVIDER_SESSION_METADATA") is not None:
        return _resolve("SessionMetadata")
    if not config.session_metadata_table:
        return None
    from ..session_metadata import SessionMetadataStore

    return SessionMetadataStore(
        table_name=config.session_metadata_table,
        region=config.bedrock_region,
    )


__all__ = [
    "ChatWithPortEmbedding",
    "GraphClientAdapter",
    "PortEmbedding",
    "resolve_authorization_port",
    "resolve_chat_client",
    "resolve_embedding_client",
    "resolve_graph_client",
    "resolve_query_executor",
    "resolve_session_metadata",
    "resolve_vector_client",
]
