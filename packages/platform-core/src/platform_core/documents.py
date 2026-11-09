"""Document ingest service (S2): CAS + parse + fixed-window chunking + PG rows.

Boundary (D18): orchestration only. Parsing is delegated to LocalDocumentParser,
chunking is a fixed character window (no semantic splitting), storage is the S0
ObjectStore, metadata is PostgreSQL. See _design/impl/S2-文档入库-设计.md §3.
"""

from __future__ import annotations

import hashlib
import logging
import math
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO

from psycopg.types.json import Jsonb

from .config import DocumentsConfig
from .errors import PortError
from .parsers import PARSER_VERSION, LocalDocumentParser, mime_for_filename
from .ports import Manifest
from .adapters.metadata_pg import MetadataPg
from .adapters.object_layered import LayeredObjectStore

log = logging.getLogger(__name__)

OWNER_BUCKET = "documents"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: Any) -> str | None:
    return value.isoformat() if value else None


class DocumentService:
    port = "DocumentService"

    def __init__(
        self,
        config: DocumentsConfig,
        metadata: MetadataPg,
        objects: LayeredObjectStore,
        parser: LocalDocumentParser,
        tmp_dir: str,
    ) -> None:
        self._config = config
        self._meta = metadata
        self._objects = objects
        self._parser = parser
        self._tmp_dir = Path(tmp_dir)

    def manifest(self) -> Manifest:
        return Manifest(
            provider="pg+layered",
            port=self.port,
            provider_version=PARSER_VERSION,
            capabilities=[
                "document.ingest",
                "document.get",
                "document.list",
                "document.chunks",
                "document.source",
            ],
            notes={
                "slice": "S2",
                "idempotency": "document_id = sha256(content)",
                "pages": "PDF pages; office/text/HTML recorded as page 1",
                "ocr": False,
                "not_implemented": [
                    "delete",
                    "reparse",
                    "async",
                    "ocr",
                    "table_semantics",
                ],
            },
        )

    # ---- ingest ----------------------------------------------------------

    def ingest_stream(
        self,
        fileobj: BinaryIO,
        filename: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Stream an upload to tmp, hashing while writing, then ingest it."""
        safe_name = Path(filename or "").name or "upload.bin"
        tmp = self._tmp_dir / f"upload-{uuid.uuid4().hex}.part"
        digest = hashlib.sha256()
        size = 0
        try:
            with open(tmp, "wb") as handle:
                while True:
                    block = fileobj.read(1024 * 1024)
                    if not block:
                        break
                    size += len(block)
                    if size > self._config.max_upload_bytes:
                        raise PortError(
                            code="ResourceExhausted",
                            message=(
                                f"upload exceeds documents.max_upload_bytes="
                                f"{self._config.max_upload_bytes}"
                            ),
                            provider="platform",
                            provider_code="E_DOC_TOO_LARGE",
                            details={"maxBytes": self._config.max_upload_bytes},
                        )
                    digest.update(block)
                    handle.write(block)
                handle.flush()
                os.fsync(handle.fileno())
            return self._ingest(tmp, safe_name, digest.hexdigest(), size, metadata)
        except Exception:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            raise

    def ingest_path(
        self,
        path: str | Path,
        filename: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        source = Path(path)
        if not source.is_file():
            raise PortError(
                code="InvalidArgument",
                message=f"document path not found: {source}",
                provider="platform",
                provider_code="E_DOC_PATH",
            )
        tmp = self._tmp_dir / f"ingest-{uuid.uuid4().hex}.part"
        digest = hashlib.sha256()
        size = 0
        try:
            with open(source, "rb") as src, open(tmp, "wb") as handle:
                while True:
                    block = src.read(1024 * 1024)
                    if not block:
                        break
                    digest.update(block)
                    size += len(block)
                    handle.write(block)
                handle.flush()
                os.fsync(handle.fileno())
            return self._ingest(tmp, filename or source.name, digest.hexdigest(), size, metadata)
        except Exception:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            raise

    def _ingest(
        self,
        path: Path,
        filename: str,
        sha256: str,
        size: int,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if size == 0:
            raise PortError(
                code="InvalidArgument",
                message="document is empty",
                provider="platform",
                provider_code="E_DOC_EMPTY",
                details={"filename": filename},
            )
        if size > self._config.max_upload_bytes:
            raise PortError(
                code="ResourceExhausted",
                message=(
                    f"document size {size} exceeds documents.max_upload_bytes="
                    f"{self._config.max_upload_bytes}"
                ),
                provider="platform",
                provider_code="E_DOC_TOO_LARGE",
            )
        mime_type = mime_for_filename(filename)
        if mime_type is None:
            raise PortError(
                code="InvalidArgument",
                message=f"unsupported document extension: {Path(filename).suffix or '(none)'}",
                provider="platform",
                provider_code="E_DOC_FORMAT_UNSUPPORTED",
                details={"filename": filename},
            )

        existing = self._row(sha256)
        if existing is not None:
            self._discard(path)
            view = self._to_view(existing)
            view.update({"deduplicated": True, "ingested": False})
            return view

        try:
            parsed = self._parser.parse_path(path, mime_type, sha256, {})
        except PortError:
            self._discard(path)
            raise

        self._objects.put_from_path(
            OWNER_BUCKET,
            sha256,
            path,
            mime_type,
            {"filename": filename},
            sha256,
            size,
        )

        pages = parsed["pages"]
        chunks = self._build_chunks(sha256, pages)
        status = "degraded" if parsed["degraded"] else "parsed"
        char_count = sum(page["charCount"] for page in pages)
        manifest = {
            "provider": parsed["provider"],
            "pages": [
                {"number": page["number"], "charCount": page["charCount"]}
                for page in pages
            ],
            "tables": parsed["tables"],
            "metadata": parsed["metadata"],
            "options": {"tables": bool(self._config.extract_tables)},
        }

        inserted = False
        try:
            with self._meta.tx() as tx:
                inserted_rows = tx.execute_returning(
                    """
                    INSERT INTO platform.document (
                        document_id, sha256, bucket, object_key, filename, mime_type,
                        size_bytes, status, page_count, char_count, chunk_count,
                        parser, parser_version, warnings, manifest, metadata, parsed_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (document_id) DO NOTHING
                    RETURNING document_id
                    """,
                    (
                        sha256,
                        sha256,
                        OWNER_BUCKET,
                        sha256,
                        filename,
                        mime_type,
                        size,
                        status,
                        len(pages),
                        char_count,
                        len(chunks),
                        "local",
                        PARSER_VERSION,
                        Jsonb(parsed["warnings"]),
                        Jsonb(manifest),
                        Jsonb(metadata or {}),
                        _now(),
                    ),
                )
                inserted = bool(inserted_rows)
                if inserted:
                    for page in pages:
                        tx.execute(
                            """
                            INSERT INTO platform.document_page
                                (document_id, page_number, text, char_count)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                            """,
                            (sha256, page["number"], page["text"], page["charCount"]),
                        )
                    for chunk in chunks:
                        tx.execute(
                            """
                            INSERT INTO platform.document_chunk (
                                chunk_id, document_id, seq, page_from, page_to,
                                char_start, char_end, text, token_estimate
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                            """,
                            (
                                chunk["chunkId"],
                                sha256,
                                chunk["seq"],
                                chunk["pageFrom"],
                                chunk["pageTo"],
                                chunk["charStart"],
                                chunk["charEnd"],
                                chunk["text"],
                                chunk["tokenEstimate"],
                            ),
                        )
        except Exception:
            if not self._row_exists(sha256):
                try:
                    self._objects.delete(OWNER_BUCKET, sha256)
                except PortError:
                    log.warning(
                        "cleanup after failed ingest did not remove the source object",
                        extra={"event": {"event": "document_cleanup_failed", "sha256": sha256}},
                    )
            raise

        result = {
            "documentId": sha256,
            "sha256": sha256,
            "status": status,
            "deduplicated": not inserted,
            "ingested": inserted,
            "filename": filename,
            "mimeType": mime_type,
            "sizeBytes": size,
            "pageCount": len(pages),
            "charCount": char_count,
            "chunkCount": len(chunks),
            "degraded": bool(parsed["degraded"]),
            "warnings": parsed["warnings"],
        }
        log.info(
            "document ingested",
            extra={
                "event": {
                    "event": "document_ingest",
                    "documentId": sha256,
                    "mimeType": mime_type,
                    "sizeBytes": size,
                    "pages": len(pages),
                    "chunks": len(chunks),
                    "degraded": bool(parsed["degraded"]),
                    "deduplicated": not inserted,
                }
            },
        )
        return result

    # ---- chunking --------------------------------------------------------

    def _build_chunks(
        self, document_id: str, pages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        limit = self._config.chunk_max_chars
        overlap = self._config.chunk_overlap_chars
        minimum = self._config.min_chunk_chars
        chunks: list[dict[str, Any]] = []
        sequence = 0
        for page in pages:
            text = page["text"]
            length = len(text)
            position = 0
            while position < length:
                end = min(position + limit, length)
                window = text[position:end]
                left = len(window) - len(window.lstrip())
                right = len(window.rstrip())
                trimmed = window.strip()
                if len(trimmed) >= minimum:
                    chunks.append(
                        {
                            "chunkId": f"{document_id}:{sequence:04d}",
                            "seq": sequence,
                            "pageFrom": page["number"],
                            "pageTo": page["number"],
                            "charStart": position + left,
                            "charEnd": position + right,
                            "text": trimmed,
                            "tokenEstimate": max(1, math.ceil(len(trimmed) / 2)),
                        }
                    )
                    sequence += 1
                if end >= length:
                    break
                position = end - overlap
        return chunks

    # ---- read paths ------------------------------------------------------

    def get(self, document_id: str, include_pages: bool = False) -> dict[str, Any]:
        row = self._row(document_id)
        if row is None:
            raise PortError(
                code="NotFound",
                message=f"document not found: {document_id}",
                provider="postgres",
                provider_code="E_DOC_NOT_FOUND",
            )
        view = self._to_view(row)
        if include_pages:
            pages = self._meta.query(
                """
                SELECT page_number, text, char_count
                  FROM platform.document_page
                 WHERE document_id = %s
                 ORDER BY page_number
                """,
                (document_id,),
            )
            view["pages"] = [
                {
                    "number": page["page_number"],
                    "text": page["text"],
                    "charCount": page["char_count"],
                }
                for page in pages
            ]
        return view

    def list(self, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        rows = self._meta.query(
            """
            SELECT * FROM platform.document
             ORDER BY created_at DESC, document_id
             LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        total = self._meta.query("SELECT COUNT(*) AS n FROM platform.document")
        return {
            "items": [self._to_view(row) for row in rows],
            "total": int(total[0]["n"]) if total else 0,
        }

    def chunks(self, document_id: str, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        if self._row(document_id) is None:
            raise PortError(
                code="NotFound",
                message=f"document not found: {document_id}",
                provider="postgres",
                provider_code="E_DOC_NOT_FOUND",
            )
        rows = self._meta.query(
            """
            SELECT chunk_id, seq, page_from, page_to, char_start, char_end,
                   text, token_estimate
              FROM platform.document_chunk
             WHERE document_id = %s
             ORDER BY seq
             LIMIT %s OFFSET %s
            """,
            (document_id, limit, offset),
        )
        total = self._meta.query(
            "SELECT COUNT(*) AS n FROM platform.document_chunk WHERE document_id = %s",
            (document_id,),
        )
        return {
            "items": [
                {
                    "chunkId": row["chunk_id"],
                    "seq": row["seq"],
                    "pageFrom": row["page_from"],
                    "pageTo": row["page_to"],
                    "charStart": row["char_start"],
                    "charEnd": row["char_end"],
                    "text": row["text"],
                    "tokenEstimate": row["token_estimate"],
                }
                for row in rows
            ],
            "total": int(total[0]["n"]) if total else 0,
        }

    def counts(self) -> dict[str, int]:
        rows = self._meta.query(
            """
            SELECT COUNT(*) AS documents,
                   COUNT(*) FILTER (WHERE status = 'degraded') AS degraded,
                   COALESCE(SUM(chunk_count), 0) AS chunks
              FROM platform.document
            """
        )
        if not rows:
            return {"documents": 0, "degraded": 0, "chunks": 0}
        return {
            "documents": int(rows[0]["documents"]),
            "degraded": int(rows[0]["degraded"]),
            "chunks": int(rows[0]["chunks"]),
        }

    def source(self, document_id: str) -> tuple[bytes, dict[str, Any]]:
        row = self._row(document_id)
        if row is None:
            raise PortError(
                code="NotFound",
                message=f"document not found: {document_id}",
                provider="postgres",
                provider_code="E_DOC_NOT_FOUND",
            )
        return self._objects.get(row["bucket"], row["object_key"])

    # ---- helpers ---------------------------------------------------------

    def _row(self, document_id: str) -> dict[str, Any] | None:
        rows = self._meta.query(
            "SELECT * FROM platform.document WHERE document_id = %s", (document_id,)
        )
        return rows[0] if rows else None

    def _row_exists(self, document_id: str) -> bool:
        rows = self._meta.query(
            "SELECT 1 AS one FROM platform.document WHERE document_id = %s",
            (document_id,),
        )
        return bool(rows)

    @staticmethod
    def _to_view(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "documentId": row["document_id"],
            "sha256": row["sha256"],
            "bucket": row["bucket"],
            "objectKey": row["object_key"],
            "filename": row["filename"],
            "mimeType": row["mime_type"],
            "sizeBytes": row["size_bytes"],
            "status": row["status"],
            "pageCount": row["page_count"],
            "charCount": row["char_count"],
            "chunkCount": row["chunk_count"],
            "parser": row["parser"],
            "parserVersion": row["parser_version"],
            "warnings": row["warnings"] or [],
            "manifest": row["manifest"] or {},
            "metadata": row["metadata"] or {},
            "createdAt": _iso(row["created_at"]),
            "parsedAt": _iso(row["parsed_at"]),
            "degraded": row["status"] == "degraded",
        }

    def _discard(self, path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            log.warning(
                "could not remove ingest temp file",
                extra={"event": {"event": "document_temp_unlink_failed", "path": str(path)}},
            )
