# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Persistence for ingested documents, their chunks, fact candidates and facts.

The tables follow the same single-table key convention as the rest of the
sources service (``PK = NS#<namespaceId>``), so the PostgreSQL
``DynamoDBDAO`` adapter that backs the local stack and the DynamoDB tables in
AWS behave identically:

    documents   SK = DOC#<documentId>
    chunks      SK = CHUNK#<documentId>#<seq:06d>
    candidates  SK = CAND#<candidateId>
    facts       SK = FACT#<factId>

Table names come from the environment so the local stack can give each one a
distinct partition; the defaults match ``10-本地起栈.ps1``.
"""

from __future__ import annotations

import base64
import json
import os
from typing import Any

from coa_common.config import resolve_region
from coa_common.dao import DynamoDBDAO
from coa_common.dao.base import QueryParams

_DAOS: dict[str, DynamoDBDAO] = {}


def _table(env: str, default: str) -> str:
    return os.environ.get(env, "") or default


def _dao(env: str, default: str) -> DynamoDBDAO:
    table = _table(env, default)
    dao = _DAOS.get(table)
    if dao is None:
        dao = DynamoDBDAO(table, region=resolve_region())
        _DAOS[table] = dao
    return dao


def documents_dao() -> DynamoDBDAO:
    return _dao("DOCUMENTS_TABLE", "coa-local-documents")


def chunks_dao() -> DynamoDBDAO:
    return _dao("DOCUMENT_CHUNKS_TABLE", "coa-local-document-chunks")


def candidates_dao() -> DynamoDBDAO:
    return _dao("FACT_CANDIDATES_TABLE", "coa-local-fact-candidates")


def facts_dao() -> DynamoDBDAO:
    return _dao("FACTS_TABLE", "coa-local-facts")


def pk(namespace_id: str) -> str:
    return f"NS#{namespace_id}"


def _query_all(dao: DynamoDBDAO, namespace_id: str, prefix: str) -> list[dict[str, Any]]:
    """Read every item under one namespace + SK prefix (small local volumes)."""
    items: list[dict[str, Any]] = []
    start: dict[str, Any] | None = None
    while True:
        page = dao.query(
            QueryParams(
                key_condition="#pk = :ns AND begins_with(#sk, :prefix)",
                expression_values={":ns": pk(namespace_id), ":prefix": prefix},
                expression_names={"#pk": "PK", "#sk": "SK"},
                limit=200,
                exclusive_start_key=start,
            )
        )
        items.extend(page.items)
        start = page.last_evaluated_key
        if not start:
            return items


def token_for(namespace_id: str, offset: int) -> str:
    payload = json.dumps({"n": namespace_id, "o": offset}, separators=(",", ":")).encode()
    return base64.b64encode(payload).decode()


def offset_from_token(token: str | None, namespace_id: str) -> int | None:
    """Decode an offset token; ``None`` when absent, raises ``ValueError`` when invalid."""
    if not token:
        return 0
    try:
        payload = json.loads(base64.b64decode(token.encode()))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid nextToken") from exc
    if not isinstance(payload, dict) or payload.get("n") != namespace_id:
        raise ValueError("Invalid nextToken")
    offset = payload.get("o")
    if not isinstance(offset, int) or offset < 0:
        raise ValueError("Invalid nextToken")
    return offset


def paginate(
    items: list[dict[str, Any]],
    namespace_id: str,
    max_results: int | None,
    token: str | None,
) -> tuple[list[dict[str, Any]], str | None]:
    """Slice a fully-materialised list and mint the next offset token."""
    offset = offset_from_token(token, namespace_id) or 0
    size = max_results or 100
    page = items[offset : offset + size]
    next_token = token_for(namespace_id, offset + size) if offset + size < len(items) else None
    return page, next_token


# ── documents ──────────────────────────────────────────────────────────────


def put_document(item: dict[str, Any]) -> None:
    documents_dao().put(item)


def get_document(namespace_id: str, document_id: str) -> dict[str, Any] | None:
    return documents_dao().get({"PK": pk(namespace_id), "SK": f"DOC#{document_id}"}, consistent_read=True)


def list_document_items(namespace_id: str) -> list[dict[str, Any]]:
    items = _query_all(documents_dao(), namespace_id, "DOC#")
    return sorted(items, key=lambda i: (i.get("createdAt") or "", i.get("documentId") or ""), reverse=True)


def find_document_by_hash(namespace_id: str, content_hash: str) -> dict[str, Any] | None:
    for item in list_document_items(namespace_id):
        if item.get("contentHash") == content_hash:
            return item
    return None


# ── chunks ─────────────────────────────────────────────────────────────────


def put_chunks(items: list[dict[str, Any]]) -> None:
    dao = chunks_dao()
    for item in items:
        dao.put(item)


def list_chunk_items(namespace_id: str, document_id: str) -> list[dict[str, Any]]:
    return _query_all(chunks_dao(), namespace_id, f"CHUNK#{document_id}#")


# ── fact candidates ────────────────────────────────────────────────────────


def put_candidate(item: dict[str, Any]) -> None:
    candidates_dao().put(item)


def get_candidate(namespace_id: str, candidate_id: str) -> dict[str, Any] | None:
    return candidates_dao().get({"PK": pk(namespace_id), "SK": f"CAND#{candidate_id}"}, consistent_read=True)


def update_candidate(namespace_id: str, candidate_id: str, fields: dict[str, Any]) -> bool:
    return candidates_dao().update({"PK": pk(namespace_id), "SK": f"CAND#{candidate_id}"}, fields)


def list_candidate_items(
    namespace_id: str,
    *,
    document_id: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    items = _query_all(candidates_dao(), namespace_id, "CAND#")
    if document_id:
        items = [i for i in items if i.get("documentId") == document_id]
    if status:
        items = [i for i in items if i.get("status") == status]
    return sorted(items, key=lambda i: (i.get("createdAt") or "", i.get("candidateId") or ""), reverse=True)


# ── facts (A-Box ledger) ───────────────────────────────────────────────────


def put_fact(item: dict[str, Any]) -> None:
    facts_dao().put(item)


def get_fact(namespace_id: str, fact_id: str) -> dict[str, Any] | None:
    return facts_dao().get({"PK": pk(namespace_id), "SK": f"FACT#{fact_id}"}, consistent_read=True)
