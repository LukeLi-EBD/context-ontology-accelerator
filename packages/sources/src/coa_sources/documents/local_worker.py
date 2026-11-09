# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Local document ingestion worker.

In AWS an S3 ``ObjectCreated`` event feeds an SQS queue and the ingestion
Trigger Lambda starts the chunk/embed/extract pipeline. The local stack has
neither S3 events nor SQS, so ``UploadDocument`` calls :func:`schedule`
instead: the same pipeline runs in a background thread inside the API process.

The pipeline is deliberately small but real — every row it writes is derived
from the uploaded bytes:

1. read the object back through the same object-store seam that stored it;
2. split the extracted text into overlapping chunks and write chunk rows;
3. embed each chunk with the configured embedding provider and write the
   vectors to the namespace's vector store (``entity_type=chunk``);
4. extract subject/predicate/object candidates from the chunk text and write
   candidate rows.

Extraction quality is not the goal here; traceability is. Nothing is
hard-coded: an upload with no recognisable sentence produces zero candidates.
"""

from __future__ import annotations

import hashlib
import os
import re
import threading
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from . import store

logger = structlog.get_logger(__name__)

CHUNK_SIZE = int(os.environ.get("COA_LOCAL_CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.environ.get("COA_LOCAL_CHUNK_OVERLAP", "120"))

_TEXT_TYPES = {"text/plain", "text/markdown", "application/json"}
_DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def schedule(
    *,
    namespace_id: str,
    document_id: str,
    bucket: str,
    key: str,
    filename: str,
    content_type: str,
) -> None:
    """Kick off ingestion without blocking the upload response."""
    thread = threading.Thread(
        target=_run_safely,
        kwargs={
            "namespace_id": namespace_id,
            "document_id": document_id,
            "bucket": bucket,
            "key": key,
            "filename": filename,
            "content_type": content_type,
        },
        name=f"ingest-{document_id[:8]}",
        daemon=True,
    )
    thread.start()


def _run_safely(**kwargs: Any) -> None:
    namespace_id = kwargs["namespace_id"]
    document_id = kwargs["document_id"]
    try:
        ingest(**kwargs)
    except Exception as exc:  # noqa: BLE001 - the document row must record the failure
        logger.exception("document_ingestion_failed", document_id=document_id)
        documents_dao = store.documents_dao()
        documents_dao.update(
            {"PK": store.pk(namespace_id), "SK": f"DOC#{document_id}"},
            {"status": "FAILED", "errorMessage": str(exc)[:1024]},
        )


def ingest(
    *,
    namespace_id: str,
    document_id: str,
    bucket: str,
    key: str,
    filename: str,
    content_type: str,
) -> None:
    documents = store.documents_dao()
    doc_key = {"PK": store.pk(namespace_id), "SK": f"DOC#{document_id}"}
    documents.update(doc_key, {"status": "PROCESSING"})

    raw = _read_object(bucket, key)
    text = _extract_text(raw, filename, content_type)
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        raise RuntimeError("no text could be extracted from the uploaded document")

    chunks = _chunk(text)
    if not chunks:
        raise RuntimeError("document produced no chunks")

    now = _now()
    chunk_items = [
        {
            "PK": store.pk(namespace_id),
            "SK": f"CHUNK#{document_id}#{seq:06d}",
            "chunkId": chunk_id,
            "documentId": document_id,
            "namespaceId": namespace_id,
            "seq": seq,
            "page": 1,
            "text": chunk_text,
            "charStart": start,
            "charEnd": end,
            "createdAt": now,
        }
        for seq, (chunk_id, chunk_text, start, end) in enumerate(chunks)
    ]
    store.put_chunks(chunk_items)
    documents.update(doc_key, {"chunkCount": len(chunk_items), "updatedAt": now})

    _write_chunk_vectors(namespace_id, document_id, chunk_items)

    candidates = []
    for item in chunk_items:
        for candidate in _extract_candidates(item["text"]):
            candidates.append(
                {
                    "PK": store.pk(namespace_id),
                    "SK": f"CAND#{candidate['candidateId']}",
                    "candidateId": candidate["candidateId"],
                    "namespaceId": namespace_id,
                    "documentId": document_id,
                    "chunkId": item["chunkId"],
                    "subject": candidate["subject"],
                    "predicate": candidate["predicate"],
                    "object": candidate["object"],
                    "confidence": candidate["confidence"],
                    "evidence": candidate["evidence"],
                    "status": "PENDING",
                    "createdAt": _now(),
                }
            )
    for item in candidates:
        store.put_candidate(item)

    documents.update(
        doc_key,
        {
            "status": "INDEXED",
            "chunkCount": len(chunk_items),
            "candidateCount": len(candidates),
            "indexedAt": _now(),
        },
    )
    logger.info(
        "document_ingested",
        namespace_id=namespace_id,
        document_id=document_id,
        chunks=len(chunk_items),
        candidates=len(candidates),
    )


# ── reading + text extraction ──────────────────────────────────────────────


def _read_object(bucket: str, key: str) -> bytes:
    from coa_sources.api import sources_handler

    s3 = sources_handler._get_s3()
    response = s3.get_object(Bucket=bucket, Key=key)
    body = response["Body"]
    return body.read() if hasattr(body, "read") else bytes(body)


def _extract_text(raw: bytes, filename: str, content_type: str) -> str:
    suffix = os.path.splitext(filename)[1].lower()
    if content_type in _TEXT_TYPES or suffix in {".txt", ".md", ".markdown", ".json", ".csv"}:
        for encoding in ("utf-8", "utf-8-sig", "gb18030"):
            try:
                return raw.decode(encoding)
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="replace")
    if content_type == _DOCX_TYPE or suffix == ".docx":
        from docx import Document  # type: ignore[import-not-found]
        import io

        document = Document(io.BytesIO(raw))
        return "\n".join(p.text for p in document.paragraphs if p.text.strip())
    raise RuntimeError(f"unsupported content type for local ingestion: {content_type}")


# ── chunking ───────────────────────────────────────────────────────────────


def _chunk(text: str) -> list[tuple[str, str, int, int]]:
    """Split ``text`` into overlapping windows, preferring paragraph boundaries."""
    if len(text) <= CHUNK_SIZE:
        return [(str(uuid.uuid4()), text, 0, len(text))]

    chunks: list[tuple[str, str, int, int]] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        if end < len(text):
            # Prefer the last paragraph/sentence break in the trailing window so
            # chunks do not end mid-sentence when a boundary is available.
            window = text[start:end]
            for boundary in ("\n\n", "\n", "。", ".", "！", "？", ";", "；"):
                index = window.rfind(boundary)
                if index >= CHUNK_SIZE // 2:
                    end = start + index + len(boundary)
                    break
        piece = text[start:end].strip()
        if piece:
            chunks.append((str(uuid.uuid4()), piece, start, end))
        if end >= len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


# ── embeddings ─────────────────────────────────────────────────────────────


def _write_chunk_vectors(namespace_id: str, document_id: str, chunk_items: list[dict[str, Any]]) -> None:
    from coa_local_providers.ontology_embedding_http import HttpEmbedder
    from coa_local_providers.ontology_vectors_pg import PgVectorStore

    url = os.environ.get("COA_EMBEDDING_URL", "").strip()
    if not url:
        raise RuntimeError("COA_EMBEDDING_URL is required for local document ingestion")
    model = os.environ.get("COA_EMBEDDING_MODEL", "BAAI/bge-m3")
    dimensions = int(os.environ.get("COA_EMBEDDING_DIMENSIONS", "1024"))

    embedder = HttpEmbedder(url=url, model=model, dimensions=dimensions)
    store_vectors = PgVectorStore(namespace_id, dimensions)
    ontology_id = f"urn:coa:document:{document_id}"

    batch = 8
    for index in range(0, len(chunk_items), batch):
        window = chunk_items[index : index + batch]
        vectors = embedder.embed_documents([item["text"] for item in window])
        if len(vectors) != len(window):
            raise RuntimeError(f"embedding returned {len(vectors)} vectors for {len(window)} chunks")
        store_vectors.store_embeddings_batch(
            [
                {
                    "entity_uri": f"urn:coa:chunk:{item['chunkId']}",
                    "entity_type": "chunk",
                    "embedding_type": "chunk",
                    "model_id": model,
                    "ontology_id": ontology_id,
                    "text": item["text"],
                    "vector": vector,
                    "dimensions": dimensions,
                    "metadata": {
                        "document_id": document_id,
                        "chunk_id": item["chunkId"],
                        "namespace_id": namespace_id,
                        "page": item["page"],
                        "char_start": item["charStart"],
                        "char_end": item["charEnd"],
                    },
                }
                for item, vector in zip(window, vectors, strict=True)
            ]
        )


# ── candidate extraction ───────────────────────────────────────────────────

_SENTENCE_SPLIT = re.compile(r"(?<=[。！？!?；;\n])")
_NOISE = re.compile(r"^[\s#>*\-\d.、)（(]+")
_ARTICLE = re.compile(r"^第[一二三四五六七八九十百千零〇0-9]+[条章节款项]\s*")
_TRAILING = "。；;，,！？!?：: \t"

# Ordered by confidence. These are surface patterns, not a model: the point is
# that every candidate is traceable to the sentence it came from.
_PATTERNS: list[tuple[re.Pattern[str], str, float]] = [
    (
        re.compile(r"^(?P<s>[^，,。；;：:]{2,40})的(?P<p>[^，,。；;：:]{1,20})是(?P<o>[^，,。；;：:]{1,80})$"),
        "possessive",
        0.62,
    ),
    (
        re.compile(r"^(?P<s>[^，,。；;：:]{2,40})(?:属于|隶属于|归属于)(?P<o>[^，,。；;：:]{1,80})$"),
        "membership",
        0.60,
    ),
    (
        re.compile(r"^(?P<s>[^，,。；;：:]{2,40})是(?:一个|一种|一份|一家|一项)?(?P<o>[^，,。；;：:]{1,80})$"),
        "type",
        0.55,
    ),
]


def _extract_candidates(text: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for raw in _SENTENCE_SPLIT.split(text):
        sentence = _NOISE.sub("", raw.strip())
        sentence = _ARTICLE.sub("", sentence).strip().rstrip(_TRAILING)
        if not sentence:
            continue
        for pattern, predicate, confidence in _PATTERNS:
            match = pattern.match(sentence)
            if not match:
                continue
            subject = match.group("s").strip()
            obj = match.group("o").strip()
            pred = match.groupdict().get("p") or (
                "rdf:type" if predicate == "type" else ("属于" if predicate == "membership" else "")
            )
            if not pred:
                continue
            key = (subject, pred, obj)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                {
                    "candidateId": str(uuid.uuid4()),
                    "subject": subject,
                    "predicate": pred,
                    "object": obj,
                    "confidence": confidence,
                    "evidence": sentence[:500],
                }
            )
    return candidates


def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
