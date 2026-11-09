# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Document ingestion routes.

    POST /namespaces/{namespaceId}/documents                          UploadDocument
    GET  /namespaces/{namespaceId}/documents                          ListDocuments
    GET  /namespaces/{namespaceId}/documents/{documentId}/chunks      ListDocumentChunks

The paths and payloads mirror ``models/src/main/smithy/documents.smithy``; the
local bridge maps them to this module exactly as ``infra/bin/app.ts`` maps them
to the sources Lambda.
"""

from __future__ import annotations

import base64
import binascii
import hmac
import json
import os
import uuid
from typing import Any

import structlog
from botocore.exceptions import ClientError
from coa_common.constants import SUPPORTED_UPLOAD_CONTENT_TYPES, validate_id
from coa_common.response import api_response, get_caller_identity

from ..documents import store

logger = structlog.get_logger(__name__)

_STATUSES = {"UPLOADED", "PROCESSING", "INDEXED", "FAILED"}
_MAX_DOCUMENTS = 100
_MAX_CHUNKS = 200


def _now() -> str:
    from . import sources_handler

    return sources_handler._now_iso()


def _body(event: dict[str, Any]) -> dict[str, Any] | None:
    try:
        body = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return None
    return body if isinstance(body, dict) else None


def _document_response(item: dict[str, Any]) -> dict[str, Any]:
    response = {
        "documentId": item.get("documentId"),
        "title": item.get("title"),
        "status": item.get("status"),
        "chunkCount": int(item.get("chunkCount") or 0),
        "updatedAt": item.get("updatedAt"),
    }
    # Only FAILED rows carry a reason; a stale error on a recovered document is
    # not surfaced, so the UI never shows an error next to a healthy status.
    if response["status"] == "FAILED" and item.get("errorMessage"):
        response["errorMessage"] = item["errorMessage"]
    return response


def _chunk_response(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "chunkId": item.get("chunkId"),
        "page": int(item.get("page") or 1),
        "text": item.get("text") or "",
        "charStart": int(item.get("charStart") or 0),
        "charEnd": int(item.get("charEnd") or 0),
    }


def _safe_filename(filename: str) -> str:
    cleaned = filename.replace("\\", "/").split("/")[-1].strip()
    if not cleaned or cleaned.startswith("."):
        raise ValueError("filename contains invalid characters")
    return cleaned


def _encode_key(namespace_id: str, document_id: str, filename: str) -> str:
    return f"{namespace_id}/documents/{document_id}/raw/{filename}"


def handle_upload_document(event: dict[str, Any], namespace_id: str) -> dict[str, Any]:
    """POST …/documents — store bytes, write the document row, start ingestion."""
    from . import sources_handler

    body = _body(event)
    if body is None:
        return api_response(400, {"error": "Invalid JSON in request body"})

    filename = str(body.get("filename") or "").strip()
    content_type = str(body.get("contentType") or "").strip()
    content_b64 = body.get("contentBase64")
    if not filename or not content_type:
        return api_response(400, {"error": "filename and contentType are required"})
    if not isinstance(content_b64, str) or not content_b64:
        return api_response(400, {"error": "contentBase64 is required"})
    if content_type not in SUPPORTED_UPLOAD_CONTENT_TYPES:
        return api_response(
            400,
            {
                "error": (
                    "contentType is not supported; supported types: "
                    f"{', '.join(sorted(SUPPORTED_UPLOAD_CONTENT_TYPES))}"
                )
            },
        )
    try:
        filename = _safe_filename(filename)
    except ValueError as exc:
        return api_response(400, {"error": str(exc)})

    try:
        raw = base64.b64decode(content_b64, validate=True)
    except (binascii.Error, ValueError):
        return api_response(400, {"error": "contentBase64 is not valid base64"})
    if not raw:
        return api_response(400, {"error": "contentBase64 decodes to an empty document"})

    content_hash = __import__("hashlib").sha256(raw).hexdigest()
    supplied_hash = body.get("contentSha256")
    if supplied_hash and not hmac.compare_digest(str(supplied_hash).lower(), content_hash):
        return api_response(400, {"error": "contentSha256 does not match the decoded content"})

    existing = store.find_document_by_hash(namespace_id, content_hash)
    if existing:
        return api_response(
            409,
            {
                "error": "A document with identical content already exists in this namespace.",
                "documentId": existing.get("documentId"),
                "status": existing.get("status"),
            },
        )

    bucket = sources_handler._BUCKET_NAME
    if not bucket:
        return api_response(500, {"error": "Internal server error"})

    document_id = str(uuid.uuid4())
    key = _encode_key(namespace_id, document_id, filename)
    try:
        sources_handler._get_s3().put_object(
            Bucket=bucket,
            Key=key,
            Body=raw,
            ContentType=content_type,
        )
    except ClientError:
        logger.exception("document_object_put_failed", namespace_id=namespace_id)
        return api_response(500, {"error": "Internal server error"})

    now = _now()
    item: dict[str, Any] = {
        "PK": store.pk(namespace_id),
        "SK": f"DOC#{document_id}",
        "documentId": document_id,
        "namespaceId": namespace_id,
        "title": str(body.get("title") or filename).strip() or filename,
        "filename": filename,
        "contentType": content_type,
        "contentHash": content_hash,
        "version": 1,
        "sizeBytes": len(raw),
        "s3Bucket": bucket,
        "s3Key": key,
        "status": "PROCESSING",
        "chunkCount": 0,
        "createdBy": get_caller_identity(event),
        "createdAt": now,
        "updatedAt": now,
    }
    metadata = body.get("metadata")
    if isinstance(metadata, dict):
        item["metadata"] = {str(k): str(v) for k, v in metadata.items()}
    store.put_document(item)

    queue_url = sources_handler._INGESTION_QUEUE_URL
    if queue_url:
        message = {
            "operation": "UploadDocument",
            "namespace_id": namespace_id,
            "document_id": document_id,
            "bucket": bucket,
            "key": key,
            "filename": filename,
            "content_type": content_type,
        }
        try:
            sources_handler._get_sqs().send_message(
                QueueUrl=queue_url, MessageBody=json.dumps(message, default=str)
            )
        except ClientError:
            logger.exception("document_ingestion_enqueue_failed", document_id=document_id)
            store.documents_dao().update(
                {"PK": store.pk(namespace_id), "SK": f"DOC#{document_id}"},
                {"status": "FAILED", "errorMessage": "Failed to enqueue ingestion job"},
            )
            return api_response(500, {"error": "Internal server error"})
    else:
        # Local stack: no S3 event / SQS, so the worker runs in-process.
        from ..documents.local_worker import schedule

        schedule(
            namespace_id=namespace_id,
            document_id=document_id,
            bucket=bucket,
            key=key,
            filename=filename,
            content_type=content_type,
        )

    logger.info("document_uploaded", namespace_id=namespace_id, document_id=document_id, bytes=len(raw))
    return api_response(
        201,
        {
            "documentId": document_id,
            "version": 1,
            "contentHash": content_hash,
            "status": "PROCESSING",
        },
    )


def handle_list_documents(event: dict[str, Any], namespace_id: str) -> dict[str, Any]:
    """GET …/documents — newest first, optional status filter."""
    query = event.get("queryStringParameters") or {}
    status = query.get("status")
    if status and status not in _STATUSES:
        return api_response(400, {"error": f"status must be one of {', '.join(sorted(_STATUSES))}"})
    try:
        max_results = int(query.get("maxResults") or 100)
    except (TypeError, ValueError):
        return api_response(400, {"error": "maxResults must be an integer"})
    if max_results < 1 or max_results > _MAX_DOCUMENTS:
        return api_response(400, {"error": f"maxResults must be between 1 and {_MAX_DOCUMENTS}"})

    items = store.list_document_items(namespace_id)
    if status:
        items = [item for item in items if item.get("status") == status]
    try:
        page, next_token = store.paginate(items, namespace_id, max_results, query.get("nextToken"))
    except ValueError as exc:
        return api_response(400, {"error": str(exc)})

    body: dict[str, Any] = {"items": [_document_response(item) for item in page]}
    if next_token:
        body["nextToken"] = next_token
    return api_response(200, body)


def handle_list_document_chunks(event: dict[str, Any], namespace_id: str, document_id: str) -> dict[str, Any]:
    """GET …/documents/{documentId}/chunks — document order."""
    try:
        validate_id(document_id, "documentId")
    except ValueError as exc:
        return api_response(400, {"error": str(exc)})
    if store.get_document(namespace_id, document_id) is None:
        return api_response(404, {"error": f"Document {document_id} not found"})

    query = event.get("queryStringParameters") or {}
    try:
        max_results = int(query.get("maxResults") or 100)
    except (TypeError, ValueError):
        return api_response(400, {"error": "maxResults must be an integer"})
    if max_results < 1 or max_results > _MAX_CHUNKS:
        return api_response(400, {"error": f"maxResults must be between 1 and {_MAX_CHUNKS}"})

    items = sorted(store.list_chunk_items(namespace_id, document_id), key=lambda i: int(i.get("seq") or 0))
    try:
        page, next_token = store.paginate(items, namespace_id, max_results, query.get("nextToken"))
    except ValueError as exc:
        return api_response(400, {"error": str(exc)})

    body: dict[str, Any] = {"items": [_chunk_response(item) for item in page]}
    if next_token:
        body["nextToken"] = next_token
    return api_response(200, body)


# Referenced by the ingestion worker for its own uploads; kept here so the
# content-hash definition lives next to the upload path that validates it.
def content_hash(raw: bytes) -> str:
    import hashlib

    return hashlib.sha256(raw).hexdigest()


_ = os  # keep the module import surface stable for the local bridge loader
