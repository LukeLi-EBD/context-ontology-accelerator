"""Gateway assembly point: the configured local clients, behind COA contracts."""

from __future__ import annotations

import inspect
from typing import Any

from .settings import ProviderNotConfigured


class LocalGateway:
    """Holds one local implementation per upstream COA protocol name."""

    def __init__(
        self,
        graph: Any | None = None,
        vector: Any | None = None,
        embedding: Any | None = None,
        llm: Any | None = None,
        catalog: Any | None = None,
        query_executor: Any | None = None,
        conversation: Any | None = None,
        memory: Any | None = None,
        object_store: Any | None = None,
    ) -> None:
        self._graph = graph
        self._vector = vector
        self._embedding = embedding
        self._llm = llm
        self._catalog = catalog
        self._query_executor = query_executor
        self._conversation = conversation
        self._memory = memory
        self._object_store = object_store

    def _require(self, interface: str, client: Any | None, setting: str) -> Any:
        if client is None:
            raise ProviderNotConfigured(f"{interface} interface is disabled ({setting}=none)")
        return client

    @property
    def graph_client(self) -> Any:
        return self._require("graph", self._graph, "COA_PROVIDER_GRAPH")

    @property
    def vector_client(self) -> Any:
        return self._require("vector", self._vector, "COA_PROVIDER_VECTOR")

    @property
    def embedding_client(self) -> Any:
        return self._require("embedding", self._embedding, "COA_PROVIDER_EMBEDDING")

    @property
    def llm_client(self) -> Any:
        return self._require("llm", self._llm, "COA_PROVIDER_LLM")

    @property
    def source_catalog(self) -> Any:
        return self._require("source_catalog", self._catalog, "COA_PROVIDER_SOURCE_CATALOG")

    @property
    def query_executor(self) -> Any:
        return self._require("query_executor", self._query_executor, "COA_PROVIDER_QUERY_EXECUTOR")

    @property
    def conversation_store(self) -> Any:
        return self._require("conversation", self._conversation, "COA_PROVIDER_CONVERSATION")

    @property
    def memory_store(self) -> Any:
        return self._require("memory", self._memory, "COA_PROVIDER_MEMORY")

    @property
    def object_store(self) -> Any:
        return self._require("object_store", self._object_store, "COA_PROVIDER_OBJECT_STORE")

    def capabilities(self) -> dict[str, bool]:
        return {
            "graph": self._graph is not None,
            "vector": self._vector is not None,
            "embedding": self._embedding is not None,
            "llm": self._llm is not None,
            "query_executor": self._query_executor is not None,
            "source_catalog": self._catalog is not None,
            "conversation": self._conversation is not None,
            "memory": self._memory is not None,
            "object_store": self._object_store is not None,
            "metadata": False,
        }

    async def health(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self._graph is not None:
            result["graph"] = await self._graph.health_check()
        if self._vector is not None:
            result["vector"] = await self._vector.health_check()
        if self._embedding is not None and hasattr(self._embedding, "health_check"):
            result["embedding"] = await self._embedding.health_check()
        if self._catalog is not None and hasattr(self._catalog, "health_check"):
            result["source_catalog"] = await self._catalog.health_check()
        if self._query_executor is not None:
            result["query_executor"] = await self._query_executor.health_check()
        for key, client in (
            ("llm", self._llm),
            ("conversation", self._conversation),
            ("memory", self._memory),
            ("object_store", self._object_store),
        ):
            if client is not None and hasattr(client, "health_check"):
                probe = client.health_check()
                result[key] = await probe if inspect.isawaitable(probe) else probe
        return result
