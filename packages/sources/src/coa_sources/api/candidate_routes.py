# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Fact-candidate review routes.

    GET  /namespaces/{namespaceId}/candidates                              ListFactCandidates
    POST /namespaces/{namespaceId}/candidates/{candidateId}/approve      ApproveFactCandidate
    POST /namespaces/{namespaceId}/candidates/{candidateId}/reject       RejectFactCandidate

Approval writes one assertion to two places, in one request and one order:

1. the **platform fact ledger** (``platform.fact_assertion`` + its chained
   ``fact_event``), which is the authoritative record, including provenance
   (candidate, document, reviewer) and the graph the triple lives in;
2. the **A-Box triple** in the namespace graph (the ledger projects it; the
   route re-issues the same ``INSERT DATA`` so a retry heals a projection that
   failed after the ledger commit);
3. the namespace's ``facts`` item (a per-namespace projection keyed by the
   ledger's fact id) and the candidate status.

The ledger is written first: if any later step fails the ledger row is retracted
in the same request, so the assertion is either fully recorded or not recorded
at all -- never "written here, repaired later".  Re-approving is idempotent:
the candidate guard returns 409, and the ledger's active-duplicate check returns
the existing fact instead of inserting a second row.

The ledger writer is injected by the host (the local bridge installs the
in-process platform runtime).  Without it approval fails with 503
``fact_ledger_unavailable`` instead of silently writing only one of the two.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable
from urllib.parse import quote

import httpx
import structlog
from coa_common.constants import validate_id
from coa_common.response import api_response, get_caller_identity

from ..documents import store

logger = structlog.get_logger(__name__)

_STATUSES = {"PENDING", "APPROVED", "REJECTED"}
_MAX_CANDIDATES = 200


_LEDGER_RECORD: Callable[..., dict[str, Any]] | None = None
_LEDGER_RETRACT: Callable[..., dict[str, Any]] | None = None


def install_fact_ledger(
    record: Callable[..., dict[str, Any]],
    retract: Callable[..., dict[str, Any]],
) -> None:
    """Wire approval to the platform fact ledger (host-specific).

    ``record(**fields)`` must write ``platform.fact_assertion`` + ``fact_event``
    and project the triple; ``retract(fact_id, reason, actor)`` must undo both.
    """
    global _LEDGER_RECORD, _LEDGER_RETRACT
    _LEDGER_RECORD = record
    _LEDGER_RETRACT = retract


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

    if _LEDGER_RECORD is None:
        logger.error("fact_ledger_unavailable", candidate_id=candidate_id)
        return api_response(
            503,
            {
                "error": (
                    "fact ledger is not configured: the host did not install "
                    "candidate_routes.install_fact_ledger; refusing to approve "
                    "into one store only"
                ),
                "code": "fact_ledger_unavailable",
            },
        )

    graph_uri = _abox_graph_uri(namespace_id)
    subject_term, subject_kind = _term(subject, "subject")
    predicate_term, predicate_kind = _term(predicate, "predicate")
    object_term, object_kind = _term(obj, "object")
    triple = _triple_from_terms(
        (subject_term, subject_kind),
        (predicate_term, predicate_kind),
        (object_term, object_kind),
    )
    now = _now()
    actor = str(body.get("actor") or get_caller_identity(event) or "local").strip()

    # 1. Authoritative write. A duplicate (same active assertion for the same
    #    document + graph) returns the existing row, so retries never double-write.
    try:
        fact = _LEDGER_RECORD(
            subject=subject_term,
            predicate=predicate_term,
            object_value=object_term,
            object_kind=object_kind,
            graph=graph_uri,
            source_kind="extraction",
            source_document_id=candidate.get("documentId"),
            candidate_id=candidate_id,
            actor=actor,
        )
    except Exception as exc:  # PortError, DB error, graph error: all explicit
        logger.exception("fact_ledger_record_failed", candidate_id=candidate_id)
        return api_response(
            502,
            {"error": f"fact ledger write failed: {exc}", "code": "fact_ledger_write_failed"},
        )
    fact_id = str(fact["factId"])
    created_here = not bool(fact.get("duplicate"))

    # 2. Two projections of that one row: the A-Box triple (idempotent, also
    #    heals a ledger row whose projection failed after the ledger commit) and
    #    the namespace's facts item keyed by the ledger fact id.
    try:
        _project(graph_uri, triple)
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
    except Exception as exc:
        logger.exception(
            "fact_candidate_approve_failed", candidate_id=candidate_id, fact_id=fact_id
        )
        # All-or-nothing: retract the row this request created. A duplicate row
        # belongs to an earlier approval and must not be retracted here.
        compensated = False
        if created_here and _LEDGER_RETRACT is not None:
            try:
                _LEDGER_RETRACT(
                    fact_id,
                    f"approval rollback: projection/persistence failed ({type(exc).__name__})",
                    actor,
                )
                compensated = True
            except Exception:
                logger.exception("fact_ledger_compensation_failed", fact_id=fact_id)
        status = 500 if (compensated or not created_here) else 503
        return api_response(
            status,
            {
                "error": f"approval failed after the ledger write: {exc}",
                "code": "fact_candidate_approve_failed",
                "factId": fact_id,
                "compensated": compensated,
                **(
                    {}
                    if compensated or not created_here
                    else {"warning": "ledger row left active; retract it manually"}
                ),
            },
        )

    logger.info(
        "fact_candidate_approved",
        namespace_id=namespace_id,
        candidate_id=candidate_id,
        fact_id=fact_id,
        duplicate=not created_here,
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


def _term(value: str, kind: str) -> tuple[str, str]:
    """Normalise one candidate position to ``(term, "iri"|"literal")``.

    The same normalisation feeds the ledger (which validates and projects the
    term) and the N-Triples serialisation, so both stores hold the same triple.
    """
    if value in _PREFIXES:
        return _PREFIXES[value], "iri"
    if _is_iri(value):
        return value, "iri"
    if kind == "predicate":
        return f"urn:coa:predicate:{quote(value, safe='')}", "iri"
    if kind == "subject":
        return f"urn:coa:entity:{quote(value, safe='')}", "iri"
    return value, "literal"


def _serialize(term: str, kind: str) -> str:
    return f"<{term}>" if kind == "iri" else json.dumps(term, ensure_ascii=False)


def _triple_from_terms(
    subject: tuple[str, str], predicate: tuple[str, str], obj: tuple[str, str]
) -> str:
    return (
        f"{_serialize(*subject)} {_serialize(*predicate)} {_serialize(*obj)} ."
    )


def _project(graph_uri: str, triple: str) -> None:
    update = f"INSERT DATA {{ GRAPH <{graph_uri}> {{ {triple} }} }}"
    response = httpx.post(
        f"{_oxigraph_url()}/update",
        content=update.encode("utf-8"),
        headers={"Content-Type": "application/sparql-update"},
        timeout=15.0,
    )
    response.raise_for_status()
