"""Client-port adapters: single/batch embedding shape and chat/embedding split."""

from __future__ import annotations

import pytest
from coa_runtime.errors import (
    ConfigurationError,
    MissingConfigurationError,
    ProviderNotAvailableError,
)
from coa_serve.clients.ports import (
    ChatWithPortEmbedding,
    GraphClientAdapter,
    PortEmbedding,
    resolve_embedding_client,
    resolve_query_executor,
)


class _BatchEmbedding:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        return [[float(len(text))] for text in texts]


class _Chat:
    model_id = "chat-model"

    def __init__(self) -> None:
        self.conversed: list[str] = []

    async def converse(self, prompt, **kwargs):
        self.conversed.append((prompt, kwargs))
        return "answer"

    async def embed(self, text: str) -> list[float]:
        return [999.0]


@pytest.mark.unit
async def test_port_embedding_converts_batch_to_single_text():
    inner = _BatchEmbedding()
    adapter = PortEmbedding(inner)

    vector = await adapter.embed("hello")

    assert vector == [5.0]
    assert inner.calls == [["hello"]]


@pytest.mark.unit
async def test_port_embedding_rejects_an_empty_response():
    class _Empty:
        async def embed(self, texts):
            return []

    with pytest.raises(ValueError):
        await PortEmbedding(_Empty()).embed("x")


@pytest.mark.unit
async def test_chat_keeps_converse_and_routes_embed_to_the_port():
    chat = _Chat()
    inner = _BatchEmbedding()
    client = ChatWithPortEmbedding(chat, PortEmbedding(inner))

    assert await client.converse("prompt", temperature=0) == "answer"
    assert chat.conversed == [("prompt", {"temperature": 0})]
    assert client.model_id == "chat-model"
    assert await client.embed("hello") == [5.0]
    assert inner.calls == [["hello"]]


@pytest.mark.unit
def test_embedding_provider_must_be_configured(monkeypatch):
    monkeypatch.delenv("COA_PROVIDER_EMBEDDING", raising=False)
    with pytest.raises(ConfigurationError):
        resolve_embedding_client()


@pytest.mark.unit
def test_query_executor_unset_keeps_the_legacy_composite(monkeypatch):
    monkeypatch.delenv("COA_PROVIDER_QUERY_EXECUTOR", raising=False)
    assert resolve_query_executor() is None


@pytest.mark.unit
def test_query_executor_requires_its_dsn_instead_of_falling_back(monkeypatch):
    monkeypatch.setenv("COA_PROVIDER_QUERY_EXECUTOR", "postgres")
    monkeypatch.delenv("COA_EXECUTOR_POSTGRES_DSN", raising=False)
    with pytest.raises(MissingConfigurationError) as excinfo:
        resolve_query_executor()
    assert excinfo.value.key == "COA_EXECUTOR_POSTGRES_DSN"


@pytest.mark.unit
def test_query_executor_athena_is_unimplemented_not_an_aws_fallback(monkeypatch):
    monkeypatch.setenv("COA_PROVIDER_QUERY_EXECUTOR", "athena")
    with pytest.raises(ProviderNotAvailableError):
        resolve_query_executor()


@pytest.mark.unit
async def test_graph_adapter_drops_the_row_cap_keyword():
    class _Graph:
        def __init__(self):
            self.sparql = None

        async def query(self, sparql):
            self.sparql = sparql
            return [{"x": 1}]

        async def ask(self, sparql):
            return True

        async def health_check(self):
            return {"ok": True}

    inner = _Graph()
    adapter = GraphClientAdapter(inner)

    assert await adapter.query("SELECT * {}", max_results=5) == [{"x": 1}]
    assert inner.sparql == "SELECT * {}"
    assert await adapter.ask("ASK {}") is True
