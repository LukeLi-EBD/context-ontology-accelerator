# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Bedrock embeddings (local) served by the existing ``bge-local`` provider.

``coa_ontology.bedrock_embeddings.BedrockEmbeddingClient`` is constructed in
four places (ingest, induce, unstructured induction, app startup) and each one
holds a ``BedrockEmbedder``. Rather than patching four imports, this module
replaces the client's constructor so every instance keeps the same public
surface (``model_id``, ``dimensions``, ``generate_lexical``, ``embed_text``,
``embed_texts``, ``set_cost_tracker``) while the embedder behind it is
``platform_core.adapters.embedding.EmbeddingClient`` — the exact adapter
``coa_local_providers.embedding_bge.BgeLocalEmbedding`` already uses, so the
local stack has one embedding implementation, not two.

Configuration (fails closed):

    COA_PROVIDER_ONTOLOGY_EMBEDDING  http | bedrock     (required)
    COA_EMBEDDING_URL                e.g. http://127.0.0.1:8081/v1  (required for http)
    COA_EMBEDDING_MODEL              default ``BAAI/bge-m3``
    COA_EMBEDDING_DIMENSIONS         default 1024

Dimension mismatches fail on the first call with the model name, never by
silently truncating or padding a vector that would then be compared against
stored vectors of a different space.
"""

from __future__ import annotations

import os
from typing import Any

_PROVIDERS = ("http", "bedrock")


def _provider() -> str:
    raw = os.environ.get("COA_PROVIDER_ONTOLOGY_EMBEDDING", "").strip().lower()
    if not raw:
        raise RuntimeError(
            "COA_PROVIDER_ONTOLOGY_EMBEDDING is required (http|bedrock); refusing to start "
            "without an explicitly selected ontology embedding provider"
        )
    if raw not in _PROVIDERS:
        raise RuntimeError(f"Unknown COA_PROVIDER_ONTOLOGY_EMBEDDING={raw!r}; expected one of {_PROVIDERS}")
    return raw


def _url() -> str:
    url = os.environ.get("COA_EMBEDDING_URL", "").strip().rstrip("/")
    if not url:
        raise RuntimeError("COA_EMBEDDING_URL is required when COA_PROVIDER_ONTOLOGY_EMBEDDING=http")
    return url


class HttpEmbedder:
    """Subset of ``BedrockEmbedder`` over the shared platform embedding adapter."""

    def __init__(self, *, url: str, model: str, dimensions: int) -> None:
        from platform_core.adapters.embedding import EmbeddingClient
        from platform_core.config import EmbeddingConfig
        from platform_core.ports import EnvSecretProvider

        self.url = url
        self.model = model
        self.dimensions = dimensions
        self._client = EmbeddingClient(
            EmbeddingConfig(
                provider="local-bge",
                model=model,
                dimensions=dimensions,
                endpoint=url,
                batch_size=1,
                batch_max=2,
                max_chunks_per_sec=0.0,  # interactive use: no indexing throttle
            ),
            EnvSecretProvider(),
        )
        self._cost_tracker: Any = None

    def set_cost_tracker(self, cost_tracker: Any) -> None:
        self._cost_tracker = cost_tracker

    def _embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        from coa_local_providers.embedding_base import check_dimensions

        vectors = self._client.embed_with("local-bge", self.model, list(texts), self.dimensions, False)
        check_dimensions(
            provider="bge-local",
            model=self.model,
            expected=self.dimensions,
            vectors=vectors,
        )
        return vectors

    def embed_document(self, text: str) -> list[float]:
        return self._embed([text])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(list(texts))

    def embed_query(self, text: str) -> list[float]:
        return self.embed_document(text)


def install_http_embeddings() -> str:
    """Replace the Bedrock client constructor; returns the selected provider."""
    provider = _provider()
    if provider == "bedrock":
        return provider

    url = _url()
    model = os.environ.get("COA_EMBEDDING_MODEL", "BAAI/bge-m3")
    dimensions = int(os.environ.get("COA_EMBEDDING_DIMENSIONS", "1024"))

    from coa_ontology import bedrock_embeddings

    def _init(
        self,
        region: str = "us-east-1",
        model_id: str | None = None,
        dimensions: int | None = None,
    ) -> None:
        # Keep the caller-visible identity but always embed with the local
        # partition: vectors from one model are only comparable to themselves.
        self.model_id = model
        self.dimensions = dimensions_env = int(
            os.environ.get("COA_EMBEDDING_DIMENSIONS", str(dimensions or 1024))
        )
        self._embedder = HttpEmbedder(url=url, model=model, dimensions=dimensions_env)

    bedrock_embeddings.BedrockEmbeddingClient.__init__ = _init  # type: ignore[method-assign]
    print(
        f"[coa-local-embedding] url={url} model={model} dimensions={dimensions}",
        flush=True,
    )
    return provider
