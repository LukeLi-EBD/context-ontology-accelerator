"""Provider registry: interface + provider name -> concrete local client.

``none`` disables an interface. An unknown name or a missing endpoint raises out
of :mod:`coa_gateway.settings`; nothing in this module substitutes one provider
for another.
"""

from __future__ import annotations

from typing import Any, Callable

from .graph_fuseki import FusekiGraphClient
from .graph_neptune import NeptuneGraphClient
from .graph_oxigraph import OxigraphGraphClient
from .gateway import LocalGateway
from .settings import (
    ProviderConfigError,
    ProviderNotConfigured,
    ProviderSettings,
    UnknownProviderError,
)
from .vector_memory import InMemoryVectorClient

Factory = Callable[[ProviderSettings], Any]


def _oxigraph(settings: ProviderSettings) -> OxigraphGraphClient:
    return OxigraphGraphClient(settings.optional("COA_GRAPH_OXIGRAPH_URL", "http://oxigraph:7878"))


def _fuseki(settings: ProviderSettings) -> FusekiGraphClient:
    return FusekiGraphClient(
        settings.require("COA_GRAPH_FUSEKI_URL", interface="graph"),
        dataset=settings.optional("COA_GRAPH_FUSEKI_DATASET", "ds"),
    )


def _platform_oxigraph(settings: ProviderSettings) -> Any:
    from coa_local_providers.graph_oxigraph import OxigraphGraphClient as PlatformOxigraphClient

    return PlatformOxigraphClient(
        settings.optional("COA_GRAPH_OXIGRAPH_URL", "http://oxigraph:7878"),
        timeout_ms=int(settings.optional("COA_GRAPH_OXIGRAPH_TIMEOUT_MS", "30000")),
        max_rows=int(settings.optional("COA_GRAPH_OXIGRAPH_MAX_ROWS", "10000")),
    )


def _platform_fuseki(settings: ProviderSettings) -> Any:
    from coa_local_providers.graph_fuseki import FusekiGraphClient as PlatformFusekiClient

    return PlatformFusekiClient(
        settings.require("COA_GRAPH_FUSEKI_SERVER_URL", interface="graph"),
        dataset=settings.optional("COA_GRAPH_FUSEKI_DATASET", "ds"),
        timeout_ms=int(settings.optional("COA_GRAPH_FUSEKI_TIMEOUT_MS", "30000")),
        max_rows=int(settings.optional("COA_GRAPH_FUSEKI_MAX_ROWS", "10000")),
    )


def _neptune(settings: ProviderSettings) -> NeptuneGraphClient:
    return NeptuneGraphClient(
        settings.require("COA_GRAPH_NEPTUNE_ENDPOINT", interface="graph"),
        region=settings.require("AWS_REGION", interface="graph"),
        access_key=settings.require("COA_GRAPH_NEPTUNE_ACCESS_KEY_ID", interface="graph"),
        secret_key=settings.require("COA_GRAPH_NEPTUNE_SECRET_ACCESS_KEY", interface="graph"),
        session_token=(settings.values.get("COA_GRAPH_NEPTUNE_SESSION_TOKEN") or "").strip() or None,
    )


def _llama_cpp(settings: ProviderSettings) -> Any:
    from .llm_llama_cpp import LlamaCppLLMClient

    threads = (settings.values.get("COA_LLM_LLAMA_CPP_N_THREADS") or "").strip()
    return LlamaCppLLMClient(
        settings.require("COA_LLM_LLAMA_CPP_MODEL_PATH", interface="llm"),
        n_ctx=int(settings.optional("COA_LLM_LLAMA_CPP_N_CTX", "2048")),
        n_threads=int(threads) if threads else None,
        n_batch=int(settings.optional("COA_LLM_LLAMA_CPP_N_BATCH", "512")),
    )


def _in_memory(settings: ProviderSettings) -> InMemoryVectorClient:
    return InMemoryVectorClient(settings.require("COA_VECTOR_IN_MEMORY_PATH", interface="vector"))


def _bge_local(settings: ProviderSettings) -> Any:
    from coa_local_providers.embedding_bge import BgeLocalEmbedding

    return BgeLocalEmbedding(
        settings.optional("COA_EMBEDDING_BGE_ENDPOINT", "http://embedding:80/v1"),
        model=settings.optional("COA_EMBEDDING_BGE_MODEL", "BAAI/bge-m3"),
        dimensions=int(settings.optional("COA_EMBEDDING_BGE_DIMENSIONS", "1024")),
        timeout_ms=int(settings.optional("COA_EMBEDDING_BGE_TIMEOUT_MS", "30000")),
        batch_size=int(settings.optional("COA_EMBEDDING_BGE_BATCH_SIZE", "2")),
        max_chunks_per_sec=float(settings.optional("COA_EMBEDDING_BGE_MAX_CHUNKS_PER_SEC", "1.0")),
    )


def _external_http(settings: ProviderSettings) -> Any:
    from coa_local_providers.embedding_http import ExternalHttpEmbedding

    return ExternalHttpEmbedding(
        endpoint=settings.require("COA_EMBEDDING_HTTP_ENDPOINT", interface="embedding"),
        model=settings.require("COA_EMBEDDING_HTTP_MODEL", interface="embedding"),
        api_key=settings.require("COA_EMBEDDING_HTTP_API_KEY", interface="embedding"),
        dimensions=int(settings.require("COA_EMBEDDING_HTTP_DIMENSIONS", interface="embedding")),
        timeout_s=float(settings.optional("COA_EMBEDDING_HTTP_TIMEOUT_S", "30")),
    )


def _platform_pgvector(settings: ProviderSettings) -> Any:
    from coa_local_providers.vector_pg import PgVectorClient

    return PgVectorClient(
        settings.require("COA_VECTOR_PG_DSN", interface="vector"),
        model=settings.optional("COA_VECTOR_PG_MODEL", "BAAI/bge-m3"),
        dimensions=int(settings.optional("COA_VECTOR_PG_DIMENSIONS", "1024")),
        pool_max=int(settings.optional("COA_VECTOR_PG_POOL_MAX", "4")),
    )


def _aoss(settings: ProviderSettings) -> Any:
    raise ProviderNotConfigured(
        "COA_PROVIDER_VECTOR=aoss is declared but not wired in this build (no AWS OpenSearch access); "
        "use in-memory or wire Amazon OpenSearch Serverless deliberately"
    )


def _postgres_executor(settings: ProviderSettings) -> Any:
    from .query_postgres import PostgresQueryExecutor

    return PostgresQueryExecutor(
        settings.require("COA_EXECUTOR_POSTGRES_DSN", interface="query_executor"),
        max_concurrency=int(settings.optional("COA_EXECUTOR_MAX_CONCURRENCY", "4")),
        connect_timeout_s=float(settings.optional("COA_EXECUTOR_CONNECT_TIMEOUT_S", "5")),
    )


def _platform_pg_executor(settings: ProviderSettings) -> Any:
    from coa_local_providers.query_pg import PostgresQueryExecutor as PlatformPostgresExecutor

    timeout = (settings.values.get("COA_EXECUTOR_STATEMENT_TIMEOUT_MS") or "").strip()
    return PlatformPostgresExecutor(
        settings.require("COA_EXECUTOR_POSTGRES_DSN", interface="query_executor"),
        pool_max=int(settings.optional("COA_EXECUTOR_POOL_MAX", "4")),
        max_rows=int(settings.optional("COA_EXECUTOR_MAX_ROWS", "1000")),
        statement_timeout_ms=int(timeout) if timeout else None,
    )


def _athena(settings: ProviderSettings) -> Any:
    raise ProviderNotConfigured(
        "COA_PROVIDER_QUERY_EXECUTOR=athena is declared but not wired in this build (no AWS access); "
        "use postgres or wire Athena deliberately"
    )


def _json_catalog(settings: ProviderSettings) -> Any:
    from .catalog import build_json_source_catalog

    return build_json_source_catalog(
        settings.require("COA_SOURCE_CATALOG_JSON_PATH", interface="source_catalog")
    )


def _smus(settings: ProviderSettings) -> Any:
    raise ProviderNotConfigured(
        "COA_PROVIDER_SOURCE_CATALOG=smus is declared but not wired in this build (no AWS access); "
        "use json or wire SageMaker Unified Studio deliberately"
    )


def _sqlite_conversation(settings: ProviderSettings) -> Any:
    from .conversation_store import SqliteConversationStore

    return SqliteConversationStore(settings.require("COA_CONVERSATION_SQLITE_PATH", interface="conversation"))


def _sqlite_memory(settings: ProviderSettings) -> Any:
    from .memory_store import SqliteMemoryStore

    return SqliteMemoryStore(settings.require("COA_MEMORY_SQLITE_PATH", interface="memory"))


def _fs_object_store(settings: ProviderSettings) -> Any:
    from .object_store import FsObjectStore

    return FsObjectStore(
        settings.require("COA_OBJECT_STORE_ROOT", interface="object_store"),
        max_bytes=int(settings.optional("COA_OBJECT_STORE_MAX_BYTES", str(64 * 1024 * 1024))),
    )


def _dynamo_conversation(settings: ProviderSettings) -> Any:
    raise ProviderNotConfigured(
        "COA_PROVIDER_CONVERSATION=dynamodb is declared but not wired in this build (no AWS access); "
        "use sqlite or wire DynamoDB deliberately"
    )


def _s3_object_store(settings: ProviderSettings) -> Any:
    raise ProviderNotConfigured(
        "COA_PROVIDER_OBJECT_STORE=s3 is declared but not wired in this build (no AWS access); "
        "use fs or wire S3 deliberately"
    )


# interface -> provider name -> factory. Only wired providers appear here, so a
# missing entry is "unknown", never "defaults to something local".
PROVIDERS: dict[str, dict[str, Factory]] = {
    "graph": {
        "oxigraph": _oxigraph,
        "fuseki": _fuseki,
        "neptune": _neptune,
        "platform-oxigraph": _platform_oxigraph,
        "platform-fuseki": _platform_fuseki,
    },
    "vector": {
        "in-memory": _in_memory,
        "aoss": _aoss,
        "platform-pgvector": _platform_pgvector,
    },
    "embedding": {
        "bge-local": _bge_local,
        "external-http": _external_http,
    },
    "llm": {"llama-cpp": _llama_cpp},
    "query_executor": {
        "postgres": _postgres_executor,
        "athena": _athena,
        "platform-pg": _platform_pg_executor,
    },
    "source_catalog": {"json": _json_catalog, "smus": _smus},
    "conversation": {"sqlite": _sqlite_conversation, "dynamodb": _dynamo_conversation},
    "memory": {"sqlite": _sqlite_memory},
    "object_store": {"fs": _fs_object_store, "s3": _s3_object_store},
}


def build_client(interface: str, settings: ProviderSettings) -> Any | None:
    """Build one interface's client, or ``None`` when it is explicitly ``none``."""
    if interface not in PROVIDERS:
        raise UnknownProviderError(f"unknown COA interface {interface!r}; known: {', '.join(PROVIDERS)}")
    name = settings.provider(interface)
    if name == "none":
        return None
    factory = PROVIDERS[interface].get(name)
    if factory is None:
        supported = ", ".join(sorted({"none", *PROVIDERS[interface]}))
        raise UnknownProviderError(
            f"COA_PROVIDER_{interface.upper()}={name} is not a known provider; supported: {supported}"
        )
    return factory(settings)


def build_gateway(settings: ProviderSettings) -> LocalGateway:
    """Assemble every configured interface into one gateway (single process)."""
    return LocalGateway(
        graph=build_client("graph", settings),
        vector=build_client("vector", settings),
        embedding=build_client("embedding", settings),
        llm=build_client("llm", settings),
        catalog=build_client("source_catalog", settings),
        query_executor=build_client("query_executor", settings),
        conversation=build_client("conversation", settings),
        memory=build_client("memory", settings),
        object_store=build_client("object_store", settings),
    )


__all__ = ["PROVIDERS", "build_client", "build_gateway", "ProviderConfigError"]
