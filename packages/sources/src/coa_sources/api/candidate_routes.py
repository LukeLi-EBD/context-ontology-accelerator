# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Fact-candidate review routes.

    GET  /namespaces/{namespaceId}/candidates                              ListFactCandidates
    POST /namespaces/{namespaceId}/candidates/{candidateId}/approve      ApproveFactCandidate
    POST /namespaces/{namespaceId}/candidates/{candidateId}/reject       RejectFactCandidate

Approval has two effects, deliberately separated in the code:

* the **ledger** row (``facts`` table) records the assertion with its
  provenance (candidate, document, chunk, reviewer);
* the **materialisation** step projects that assertion as one triple into the
  namespace A-Box graph, so graph queries see it.

The projection is idempotent: the fact id is derived from the candidate id, and
RDF set semantics make a repeated ``INSERT DATA`` a no-op.
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any
from urllib.parse import quote

import httpx
import structlog
from coa_common.constants import validate_id
from coa_common.response import api_response, get_caller_identity

from ..documents import store

logger = structlog.get_logger(__name__)

_STATUSES = {"PENDING", "APPROVED", "REJECTED"}
_MAX_CANDIDATES = 200
_FACT_NAMESPACE = uuid.UUID("6f9619ff-8b86-d011-b42d-00c04fc964ff")


def _now() -> str:
    from . import sources_handler

    return sources_handler._now_iso()


def _body(event: dict[str, Any]) -> dict[str, Any]:
    try:
        body = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}
    return body if isinstance(body, dict) else {}


def _candidate_response(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidateId": item.get("candidateId"),
        "subject": item.get("subject"),
        "predicate": item.get("predicate"),
        "object": item.get("object"),
        "confidence": float(item.get("confidence") or 0.0),
        "status": item.get("status"),
        "documentId": item.get("documentId"),
        "chunkId": item.get("chunkId"),
        "evidence": item.get("evidence"),
    }


def handle_list_candidates(event: dict[str, Any], namespace_id: str) -> dict[str, Any]:
    query = event.get("queryStringParameters") or {}
    status = query.get("status")
    if status and status not in _STATUSES:
        return api_response(400, {"error": f"status must be one of {', '.join(sorted(_STATUSES))}"})
    document_id = query.get("documentId")
    if document_id:
        try:
            validate_id(document_id, "documentId")
        except ValueError as exc:
            return api_response(400, {"error": str(exc)})
    try:
        max_results = int(query.get("maxResults") or 100)
    except (TypeError, ValueError):
        return api_response(400, {"error": "maxResults must be an integer"})
    if max_results < 1 or max_results > _MAX_CANDIDATES:
        return api_response(400, {"error": f"maxResults must be between 1 and {_MAX_CANDIDATES}"})

    items = store.list_candidate_items(namespace_id, document_id=document_id, status=status)
    try:
        page, next_token = store.paginate(items, namespace_id, max_results, query.get("nextToken"))
    except ValueError as exc:
        return api_response(400, {"error": str(exc)})

    body: dict[str, Any] = {"items": [_candidate_response(item) for item in page]}
    if next_token:
        body["nextToken"] = next_token
    return api_response(200, body)


def handle_approve_candidate(event: dict[str, Any], namespace_id: str, candidate_id: str) -> dict[str, Any]:
    try:
        validate_id(candidate_id, "candidateId")
    except ValueError as exc:
        return api_response(400, {"error": str(exc)})

    candidate = store.get_candidate(namespace_id, candidate_id)
    if candidate is None:
        return api_response(404, {"error": f"Candidate {candidate_id} not found"})
    if candidate.get("status") == "REJECTED":
        return api_response(409, {"error": "Candidate was already rejected"})
    if candidate.get("status") == "APPROVED":
        return api_response(
            409,
            {"error": "Candidate was already approved", "factId": candidate.get("factId")},
        )

    body = _body(event)
    overrides = body.get("factOverrides")
    if overrides is not None and not isinstance(overrides, dict):
        return api_response(400, {"error": "factOverrides must be an object"})
    overrides = overrides or {}
    subject = str(overrides.get("subject") or candidate.get("subject") or "").strip()
    predicate = str(overrides.get("predicate") or candidate.get("predicate") or "").strip()
    obj = str(overrides.get("object") or candidate.get("object") or "").strip()
    if not subject or not predicate or not obj:
        return api_response(400, {"error": "subject, predicate and object must be non-empty"})

    fact_id = str(uuid.uuid5(_FACT_NAMESPACE, f"{namespace_id}:{candidate_id}"))
    graph_uri = _abox_graph_uri(namespace_id)
    triple = _triple(subject, predicate, obj)
    try:
        _project(graph_uri, triple)
    except httpx.HTTPError as exc:
        logger.exception("abox_projection_failed", candidate_id=candidate_id)
        return api_response(502, {"error": f"A-Box projection failed: {exc}"})

    now = _now()
    actor = str(body.get("actor") or get_caller_identity(event) or "local").strip()
    store.put_fact(
        {
            "PK": store.pk(namespace_id),
            "SK": f"FACT#{fact_id}",
            "factId": fact_id,
            "namespaceId": namespace_id,
            "candidateId": candidate_id,
            "documentId": candidate.get("documentId"),
            "chunkId": candidate.get("chunkId"),
            "subject": subject,
            "predicate": predicate,
            "object": obj,
            "status": "ACTIVE",
            "graphUri": graph_uri,
            "triple": triple,
            "reviewedBy": actor,
            "createdAt": now,
        }
    )
    store.update_candidate(
        namespace_id,
        candidate_id,
        {
            "status": "APPROVED",
            "factId": fact_id,
            "reviewedBy": actor,
            "reviewedAt": now,
            "materializedAt": now,
        },
    )
    logger.info(
        "fact_candidate_approved",
        namespace_id=namespace_id,
        candidate_id=candidate_id,
        fact_id=fact_id,
    )
    return api_response(200, {"factId": fact_id, "status": "APPROVED"})


def handle_reject_candidate(event: dict[str, Any], namespace_id: str, candidate_id: str) -> dict[str, Any]:
    try:
        validate_id(candidate_id, "candidateId")
    except ValueError as exc:
        return api_response(400, {"error": str(exc)})

    candidate = store.get_candidate(namespace_id, candidate_id)
    if candidate is None:
        return api_response(404, {"error": f"Candidate {candidate_id} not found"})
    if candidate.get("status") == "APPROVED":
        return api_response(409, {"error": "Candidate was already approved"})
    if candidate.get("status") == "REJECTED":
        return api_response(200, {"status": "REJECTED"})

    body = _body(event)
    reason = str(body.get("reason") or "").strip()
    if not reason:
        return api_response(400, {"error": "reason is required"})
    actor = str(body.get("actor") or get_caller_identity(event) or "local").strip()
    store.update_candidate(
        namespace_id,
        candidate_id,
        {
            "status": "REJECTED",
            "rejectReason": reason[:1024],
            "reviewedBy": actor,
            "reviewedAt": _now(),
        },
    )
    logger.info("fact_candidate_rejected", namespace_id=namespace_id, candidate_id=candidate_id)
    return api_response(200, {"status": "REJECTED"})


# ── A-Box projection ───────────────────────────────────────────────────────


def _abox_graph_uri(namespace_id: str) -> str:
    base = (os.environ.get("NDB_GRAPH_URI_BASE") or "https://coa.local/graph").rstrip("/")
    return f"{base}/{namespace_id}/{quote('urn:coa:abox:documents', safe='')}"


def _oxigraph_url() -> str:
    return (
        os.environ.get("COA_GRAPH_OXIGRAPH_URL")
        or os.environ.get("OXIGRAPH_URL")
        or "http://127.0.0.1:7878"
    ).rstrip("/")


def _is_iri(value: str) -> bool:
    if any(ch.isspace() for ch in value):
        return False
    if value.startswith("rdf:"):
        return True
    return "://" in value or (":" in value and not value.startswith(":"))


_PREFIXES = {
    "rdf:type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
    "rdfs:label": "http://www.w3.org/2000/01/rdf-schema#label",
}


def _iri(value: str, kind: str) -> str:
    if value in _PREFIXES:
        return f"<{_PREFIXES[value]}>"
    if _is_iri(value):
        return f"<{value}>"
    if kind == "predicate":
        return f"<urn:coa:predicate:{quote(value, safe='')}>"
    if kind == "subject":
        return f"<urn:coa:entity:{quote(value, safe='')}>"
    return json.dumps(value, ensure_ascii=False)


def _triple(subject: str, predicate: str, obj: str) -> str:
    return f"{_iri(subject, 'subject')} {_iri(predicate, 'predicate')} {_iri(obj, 'object')} ."


def _project(graph_uri: str, triple: str) -> None:
    update = f"INSERT DATA {{ GRAPH <{graph_uri}> {{ {triple} }} }}"
    response = httpx.post(
        f"{_oxigraph_url()}/update",
        content=update.encode("utf-8"),
        headers={"Content-Type": "application/sparql-update"},
        timeout=15.0,
    )
    response.raise_for_status()
