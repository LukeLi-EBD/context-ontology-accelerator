"""Read-only HTTP facade over the COA client contracts.

Path = interface + contract method name; body/response fields are the protocol's
own parameter and return-field names, so a caller can map one-to-one onto
``GraphClient.query`` / ``GraphClient.ask`` / ``VectorClient.search`` /
``QueryExecutor.execute`` / ``LLMClient.converse``. Nothing here renames or
reshapes a contract field.

graph / vector / query are read-only; conversation / memory / object_store
persist locally (SQLite, files). No approval, no catalog mutation.
"""

from __future__ import annotations

import base64
import dataclasses
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .registry import build_gateway
from .settings import ProviderNotConfigured, ProviderSettings


class GraphQueryRequest(BaseModel):
    """``GraphClient.query(sparql)``."""

    sparql: str


class GraphAskRequest(BaseModel):
    """``GraphClient.ask(sparql)``."""

    sparql: str


class GraphTraverseRequest(BaseModel):
    """``DataLayerService.GraphTraverse`` input, spelled as in the Smithy shape."""

    startUri: str
    maxDepth: int = 2
    relationshipFilter: list[str] | None = None
    direction: str = "both"
    maxResults: int = 100


class VectorSearchRequest(BaseModel):
    """``VectorClient.search`` keyword arguments, spelled as in the protocol.

    Either ``query_vector`` (pre-computed) or ``query`` (natural language, embedded
    by the configured ``EmbeddingProvider``) must be supplied.
    """

    query_vector: list[float] | None = None
    query: str | None = None
    namespace: str = ""
    top_k: int = 5
    index: str | None = None
    entity_type: str | None = None
    require_mapped: bool = False
    ontology_ids: list[str] | None = None


class KBSearchRequest(BaseModel):
    """``DataLayerService.KBSearch`` input, spelled as in the Smithy shape."""

    query: str
    topK: int = 5
    minScore: float = 0.0


class SqlQueryRequest(BaseModel):
    """``QueryExecutor.execute`` keyword arguments, spelled as in the protocol."""

    sql: str
    namespace: str = ""
    data_source_id: str = ""
    params: dict[str, Any] | None = None
    max_rows: int = 1000
    timeout_seconds: int = 10


class ConversationCreateRequest(BaseModel):
    """N5 ``ConversationStore.create(user_id, namespace, title)``."""

    user_id: str
    namespace: str
    title: str


class ValidateOwnershipRequest(BaseModel):
    """N5 ``ConversationStore.validate_ownership(user_id, session_id)``."""

    user_id: str
    session_id: str


class UpdateActivityRequest(BaseModel):
    """N5 ``ConversationStore.update_activity(session_id)``."""

    session_id: str
    at: str | None = None


class ListSessionsRequest(BaseModel):
    """N5 ``ConversationStore.list_sessions(user_id, namespace, limit)``."""

    user_id: str
    namespace: str | None = None
    limit: int = 50


class HistoryRequest(BaseModel):
    """N5 ``ConversationStore.get_history(session_id, limit, before)``."""

    session_id: str
    limit: int = 50
    before: str | None = None


class SessionRef(BaseModel):
    """N5 ``ConversationStore.delete(session_id)``."""

    session_id: str


class MemoryTurn(BaseModel):
    """One turn written through N6 ``MemoryStore.append_turn``."""

    role: str
    content: str


class MemoryAppendRequest(BaseModel):
    """N6 ``MemoryStore.append_turn(session_id, turn)``."""

    session_id: str
    turn: MemoryTurn
    at: str | None = None


class MemoryWindowRequest(BaseModel):
    """N6 ``MemoryStore.get_window(session_id, turns)``."""

    session_id: str
    turns: int = 10


class MemorySearchRequest(BaseModel):
    """N6 ``MemoryStore.search(namespace, query, top_k)``."""

    namespace: str
    query: str
    top_k: int = 5


class MemoryDeleteRequest(BaseModel):
    """N6 ``MemoryStore.delete_session(session_id)``."""

    session_id: str


class MemoryGcRequest(BaseModel):
    """N6 ``MemoryStore.gc(expires_before)``."""

    expires_before: str


class LlmConverseRequest(BaseModel):
    """``LLMClient.converse`` keyword arguments, spelled as in the protocol."""

    prompt: str
    system: str | None = None
    max_tokens: int = 512
    temperature: float | None = None
    top_p: float | None = None


class ObjectPutRequest(BaseModel):
    """N8 ``ObjectStore.put(bucket, key, body, content_type, metadata)``."""

    bucket: str
    key: str
    body_base64: str
    content_type: str = "application/octet-stream"
    metadata: dict[str, str] | None = None


class ObjectRef(BaseModel):
    """N8 ``get/head/delete(bucket, key)``."""

    bucket: str
    key: str


class ObjectListRequest(BaseModel):
    """N8 ``ObjectStore.list(bucket, prefix, limit)``."""

    bucket: str
    prefix: str = ""
    limit: int = 100


def _embedding_error_detail(exc: Exception) -> str | None:
    """Render a dimension/model refusal with both sides; ``None`` if unrelated."""
    try:
        from coa_local_providers.embedding_base import EmbeddingDimensionMismatch, EmbeddingModelMismatch
    except Exception:  # pragma: no cover - package absent in a stripped install
        return None
    if isinstance(exc, EmbeddingDimensionMismatch):
        return (
            f"embedding dimension mismatch: provider {exc.provider}/{exc.model} "
            f"configured {exc.expected}, returned {exc.actual}"
        )
    if isinstance(exc, EmbeddingModelMismatch):
        return f"embedding model mismatch: got {exc.got}, active partition is {exc.expected}"
    try:
        from platform_core.errors import PortError
    except Exception:  # pragma: no cover
        return None
    if isinstance(exc, PortError):
        details = exc.details or {}
        if exc.provider_code == "E_EMBED_DIM_MISMATCH":
            return (
                f"embedding dimension mismatch: got {details.get('got')}, "
                f"expected {details.get('expected')}"
            )
        if exc.provider_code == "E_EMBED_MODEL_MISMATCH":
            return (
                f"embedding model mismatch: got {details.get('got')}, "
                f"expected {details.get('expected')}"
            )
    return None


def _guard_index_dimensions(vector_client: Any, query_vector: list[float]) -> None:
    """Reject a query vector that cannot belong to the configured index."""
    detector = getattr(vector_client, "dimensions", None)
    if not callable(detector):
        return
    present = sorted({int(dim) for dim in detector()})
    if present and len(query_vector) not in present:
        raise HTTPException(
            status_code=400,
            detail=f"embedding dimension mismatch: query {len(query_vector)} vs index {present}",
        )


async def _resolve_query_vector(gateway: Any, body: VectorSearchRequest) -> tuple[list[float], str | None]:
    if body.query_vector is not None:
        return body.query_vector, None
    if not body.query:
        raise HTTPException(status_code=400, detail="query_vector or query is required")
    embedding = gateway.embedding_client
    vectors = await embedding.embed([body.query])
    _guard_index_dimensions(gateway.vector_client, vectors[0])
    return vectors[0], embedding.model


def _http_error(exc: Exception) -> HTTPException:
    """Map a provider/backend failure onto a status that never looks like success."""
    from .conversation_store import SessionForbidden, SessionNotFound
    from .object_store import ObjectNotFound, ObjectStoreError, ObjectTooLarge, PreconditionFailed, UnsupportedOperation

    if isinstance(exc, ProviderNotConfigured):
        return HTTPException(status_code=503, detail=str(exc))
    if isinstance(exc, SessionNotFound):
        return HTTPException(status_code=404, detail=f"SessionNotFound: {exc}")
    if isinstance(exc, SessionForbidden):
        return HTTPException(status_code=403, detail=f"SessionForbidden: {exc}")
    if isinstance(exc, ObjectNotFound):
        return HTTPException(status_code=404, detail=f"ObjectNotFound: {exc}")
    if isinstance(exc, ObjectTooLarge):
        return HTTPException(status_code=413, detail=f"ObjectTooLarge: {exc}")
    if isinstance(exc, UnsupportedOperation):
        return HTTPException(status_code=501, detail=f"Unsupported: {exc}")
    if isinstance(exc, PreconditionFailed):
        return HTTPException(status_code=400, detail=f"PreconditionFailed: {exc}")
    if isinstance(exc, ObjectStoreError):
        return HTTPException(status_code=400, detail=f"{type(exc).__name__}: {exc}")
    return HTTPException(status_code=503, detail=f"{type(exc).__name__}: {exc}")


def create_app(settings: ProviderSettings | None = None) -> FastAPI:
    """Build the app; one gateway, one process, every configured interface."""
    gateway = build_gateway(settings or ProviderSettings.from_env())
    app = FastAPI(title="coa-gateway", version="0.1", docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/healthz")
    async def healthz() -> dict[str, Any]:
        return {"capabilities": gateway.capabilities(), "health": await gateway.health()}

    @app.post("/graph/query")
    async def graph_query(body: GraphQueryRequest) -> dict[str, Any]:
        try:
            return {"rows": await gateway.graph_client.query(body.sparql)}
        except Exception as exc:
            raise _http_error(exc) from exc

    @app.post("/graph/ask")
    async def graph_ask(body: GraphAskRequest) -> dict[str, Any]:
        try:
            return {"result": await gateway.graph_client.ask(body.sparql)}
        except Exception as exc:
            raise _http_error(exc) from exc

    # -- COA DataLayerService operation (not a gateway primitive) ------
    @app.post("/namespaces/{namespace_id}/graph/traverse")
    async def coa_graph_traverse(namespace_id: str, body: GraphTraverseRequest):
        from .coa_operations import CoaValidationError, graph_traverse

        try:
            uuid.UUID(namespace_id)
        except ValueError:
            return JSONResponse(status_code=400, content={"message": "namespaceId must be a UUID"})
        try:
            result = await graph_traverse(
                gateway.graph_client,
                namespace_id,
                start_uri=body.startUri,
                max_depth=body.maxDepth,
                direction=body.direction,
                relationship_filter=body.relationshipFilter,
                max_results=body.maxResults,
            )
        except CoaValidationError as exc:
            return JSONResponse(status_code=400, content={"message": str(exc)})
        except Exception as exc:
            raise _http_error(exc) from exc
        return JSONResponse(content=result)

    # -- PlatformKnowledgeService operation (extension contract) --------
    @app.get("/namespaces/{namespace_id}/graph/entity")
    async def coa_get_entity(namespace_id: str, uri: str | None = None):
        from .coa_operations import CoaEntityNotFound, CoaValidationError, get_entity

        try:
            uuid.UUID(namespace_id)
        except ValueError:
            return JSONResponse(status_code=400, content={"message": "namespaceId must be a UUID"})
        if not uri:
            return JSONResponse(status_code=400, content={"message": "uri is required"})
        try:
            result = await get_entity(gateway.graph_client, uri=uri)
        except CoaValidationError as exc:
            return JSONResponse(status_code=400, content={"message": str(exc)})
        except CoaEntityNotFound as exc:
            return JSONResponse(status_code=404, content={"message": f"entity not found: {exc}"})
        except Exception as exc:
            raise _http_error(exc) from exc
        return JSONResponse(content=result)

    @app.post("/vector/search")
    async def vector_search(body: VectorSearchRequest) -> dict[str, Any]:
        try:
            query_vector, embedding_model = await _resolve_query_vector(gateway, body)
            hits = await gateway.vector_client.search(
                query_vector,
                namespace=body.namespace,
                top_k=body.top_k,
                index=body.index,
                entity_type=body.entity_type,
                require_mapped=body.require_mapped,
                ontology_ids=body.ontology_ids,
            )
        except HTTPException:
            raise
        except Exception as exc:
            detail = _embedding_error_detail(exc)
            if detail is not None:
                raise HTTPException(status_code=400, detail=detail) from exc
            raise _http_error(exc) from exc
        payload: dict[str, Any] = {"hits": [dataclasses.asdict(hit) for hit in hits]}
        if embedding_model is not None:
            payload["queryEmbeddingModel"] = embedding_model
        return payload

    @app.post("/namespaces/{namespace_id}/kb/search")
    async def coa_kb_search(namespace_id: str, body: KBSearchRequest):
        try:
            uuid.UUID(namespace_id)
        except ValueError:
            return JSONResponse(status_code=400, content={"message": "namespaceId must be a UUID"})
        if not body.query.strip():
            return JSONResponse(status_code=400, content={"message": "query is required"})
        if body.topK < 1:
            return JSONResponse(status_code=400, content={"message": "topK must be >= 1"})
        try:
            embedding = gateway.embedding_client
            vectors = await embedding.embed([body.query])
            query_vector = vectors[0]
            _guard_index_dimensions(gateway.vector_client, query_vector)
            candidates = await gateway.vector_client.search(
                query_vector,
                namespace="",
                top_k=max(body.topK * 3, body.topK),
            )
        except HTTPException:
            raise
        except Exception as exc:
            detail = _embedding_error_detail(exc)
            if detail is not None:
                raise HTTPException(status_code=400, detail=detail) from exc
            raise _http_error(exc) from exc

        chunks: list[dict[str, Any]] = []
        for hit in candidates:
            if hit.score < body.minScore:
                continue
            chunk: dict[str, Any] = {
                "chunkId": hit.id,
                "text": hit.text,
                "relevanceScore": hit.score,
            }
            metadata = hit.metadata or {}
            if metadata.get("documentId"):
                chunk["sourceDocumentId"] = metadata["documentId"]
            if metadata.get("pageFrom") is not None:
                chunk["pageFrom"] = metadata["pageFrom"]
            if metadata.get("pageTo") is not None:
                chunk["pageTo"] = metadata["pageTo"]
            chunks.append(chunk)
            if len(chunks) >= body.topK:
                break
        return {
            "chunks": chunks,
            "trace": [
                {
                    "step": "embed",
                    "status": "success",
                    "detail": f"model={embedding.model} dimensions={embedding.dimensions}",
                },
                {
                    "step": "vector_search",
                    "status": "success",
                    "detail": f"topK={body.topK} minScore={body.minScore}",
                },
            ],
            "queryEmbeddingModel": embedding.model,
        }

    @app.post("/query/execute")
    async def query_execute(body: SqlQueryRequest) -> dict[str, Any]:
        try:
            result = await gateway.query_executor.execute(
                body.sql,
                namespace=body.namespace,
                data_source_id=body.data_source_id,
                params=body.params,
                max_rows=body.max_rows,
                timeout_seconds=body.timeout_seconds,
            )
        except Exception as exc:
            raise _http_error(exc) from exc
        return dataclasses.asdict(result)

    @app.post("/llm/converse")
    async def llm_converse(body: LlmConverseRequest) -> dict[str, Any]:
        try:
            result = await gateway.llm_client.converse(
                body.prompt,
                system=body.system,
                max_tokens=body.max_tokens,
                temperature=body.temperature,
                top_p=body.top_p,
            )
        except Exception as exc:
            raise _http_error(exc) from exc
        return dataclasses.asdict(result)

    # -- ConversationStore (N5) ---------------------------------------
    @app.post("/conversation/create")
    async def conversation_create(body: ConversationCreateRequest) -> dict[str, Any]:
        try:
            return dataclasses.asdict(gateway.conversation_store.create(body.user_id, body.namespace, body.title))
        except Exception as exc:
            raise _http_error(exc) from exc

    @app.post("/conversation/validate_ownership")
    async def conversation_validate_ownership(body: ValidateOwnershipRequest) -> dict[str, Any]:
        try:
            return {"result": gateway.conversation_store.validate_ownership(body.user_id, body.session_id)}
        except Exception as exc:
            raise _http_error(exc) from exc

    @app.post("/conversation/update_activity")
    async def conversation_update_activity(body: UpdateActivityRequest) -> dict[str, Any]:
        try:
            return dataclasses.asdict(gateway.conversation_store.update_activity(body.session_id, at=body.at))
        except Exception as exc:
            raise _http_error(exc) from exc

    @app.post("/conversation/list_sessions")
    async def conversation_list_sessions(body: ListSessionsRequest) -> dict[str, Any]:
        try:
            rows = gateway.conversation_store.list_sessions(
                body.user_id, namespace=body.namespace, limit=body.limit
            )
        except Exception as exc:
            raise _http_error(exc) from exc
        return {"sessions": [dataclasses.asdict(row) for row in rows]}

    @app.post("/conversation/get_history")
    async def conversation_get_history(body: HistoryRequest) -> dict[str, Any]:
        try:
            return {"turns": gateway.conversation_store.get_history(body.session_id, limit=body.limit, before=body.before)}
        except Exception as exc:
            raise _http_error(exc) from exc

    @app.post("/conversation/delete")
    async def conversation_delete(body: SessionRef) -> dict[str, Any]:
        try:
            gateway.conversation_store.delete(body.session_id)
        except Exception as exc:
            raise _http_error(exc) from exc
        return {"deleted": body.session_id}

    # -- MemoryStore (N6) ----------------------------------------------
    @app.post("/memory/append_turn")
    async def memory_append_turn(body: MemoryAppendRequest) -> dict[str, Any]:
        try:
            record = gateway.memory_store.append_turn(
                body.session_id, body.turn.model_dump(), at=body.at
            )
        except Exception as exc:
            raise _http_error(exc) from exc
        return dataclasses.asdict(record)

    @app.post("/memory/get_window")
    async def memory_get_window(body: MemoryWindowRequest) -> dict[str, Any]:
        try:
            rows = gateway.memory_store.get_window(body.session_id, turns=body.turns)
        except Exception as exc:
            raise _http_error(exc) from exc
        return {"turns": [dataclasses.asdict(row) for row in rows]}

    @app.post("/memory/search")
    async def memory_search(body: MemorySearchRequest) -> dict[str, Any]:
        from .memory_store import SEARCH_MODE

        try:
            hits = gateway.memory_store.search(body.namespace, body.query, top_k=body.top_k)
        except Exception as exc:
            raise _http_error(exc) from exc
        return {"hits": hits, "mode": SEARCH_MODE}

    @app.post("/memory/delete_session")
    async def memory_delete_session(body: MemoryDeleteRequest) -> dict[str, Any]:
        try:
            removed = gateway.memory_store.delete_session(body.session_id)
        except Exception as exc:
            raise _http_error(exc) from exc
        return {"deleted": removed}

    @app.post("/memory/gc")
    async def memory_gc(body: MemoryGcRequest) -> dict[str, Any]:
        try:
            removed = gateway.memory_store.gc(body.expires_before)
        except Exception as exc:
            raise _http_error(exc) from exc
        return {"deleted": removed}

    # -- ObjectStore (N8) ----------------------------------------------
    @app.get("/object_store/capabilities")
    async def object_store_capabilities() -> dict[str, Any]:
        try:
            return gateway.object_store.capabilities()
        except Exception as exc:
            raise _http_error(exc) from exc

    @app.post("/object_store/put")
    async def object_store_put(body: ObjectPutRequest) -> dict[str, Any]:
        try:
            raw = base64.b64decode(body.body_base64, validate=True)
            return gateway.object_store.put(
                body.bucket, body.key, raw, body.content_type, body.metadata
            )
        except Exception as exc:
            raise _http_error(exc) from exc

    @app.post("/object_store/get")
    async def object_store_get(body: ObjectRef) -> dict[str, Any]:
        try:
            raw, meta = gateway.object_store.get(body.bucket, body.key)
        except Exception as exc:
            raise _http_error(exc) from exc
        return {"body_base64": base64.b64encode(raw).decode(), "metadata": meta}

    @app.post("/object_store/head")
    async def object_store_head(body: ObjectRef) -> dict[str, Any]:
        try:
            return gateway.object_store.head(body.bucket, body.key)
        except Exception as exc:
            raise _http_error(exc) from exc

    @app.post("/object_store/delete")
    async def object_store_delete(body: ObjectRef) -> dict[str, Any]:
        try:
            gateway.object_store.delete(body.bucket, body.key)
        except Exception as exc:
            raise _http_error(exc) from exc
        return {"deleted": f"{body.bucket}/{body.key}"}

    @app.post("/object_store/list")
    async def object_store_list(body: ObjectListRequest) -> dict[str, Any]:
        try:
            return {"objects": gateway.object_store.list(body.bucket, body.prefix, body.limit)}
        except Exception as exc:
            raise _http_error(exc) from exc

    return app


__all__ = ["create_app"]
