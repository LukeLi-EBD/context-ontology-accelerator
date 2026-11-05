"""DocumentParser adapter: format routing over pypdfium2 / pdfplumber / MarkItDown.

Boundary (D18): no layout analysis, no OCR, no semantic table understanding.
This module only routes a file to a third-party parser, normalizes the result
and maps failures to PortError. See _design/impl/S2-文档入库-设计.md §3.6.
"""

from __future__ import annotations

import logging
import re
import threading
import uuid
from pathlib import Path
from typing import Any

from .config import DocumentsConfig, OcrConfig
from .errors import PortError
from .ports import Manifest

log = logging.getLogger(__name__)

PARSER_VERSION = "s2.1"
LOCAL_PROVIDER = "local"

EXTENSION_MIME: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".html": "text/html",
    ".htm": "text/html",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".csv": "text/csv",
}

OFFICE_MIME = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/html",
}
TEXT_MIME = {"text/plain", "text/markdown", "text/csv"}


def mime_for_filename(filename: str) -> str | None:
    return EXTENSION_MIME.get(Path(filename).suffix.lower())


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _invalid(code: str, message: str, details: dict[str, Any] | None = None) -> PortError:
    return PortError(
        code="InvalidArgument",
        message=message,
        provider=LOCAL_PROVIDER,
        provider_code=code,
        details=details,
    )


_ENCRYPT_REF = re.compile(rb"/Encrypt\s+\d+\s+\d+\s+R")
# PDFium is not thread-safe. Bulk import may run several parsers concurrently;
# serialise the PDFium critical section instead of allowing a native crash.
_PDFIUM_LOCK = threading.Lock()


def _pdf_is_encrypted(path: Path) -> bool:
    """Detect standard-security PDFs from the trailer without parsing them.

    Encrypted files must fail with a distinct code (S13 acceptance): a generic
    parse exception is not actionable for the operator.
    """
    try:
        size = path.stat().st_size
        with open(path, "rb") as handle:
            handle.seek(max(0, size - 256 * 1024))
            return bool(_ENCRYPT_REF.search(handle.read()))
    except OSError:
        return False


def _pdf_open_error(path: Path, exc: Exception) -> PortError:
    text = str(exc).lower()
    if _pdf_is_encrypted(path) or "password" in text or "encrypt" in text:
        return _invalid(
            "E_DOC_PDF_ENCRYPTED",
            "PDF is encrypted (password required); decrypt it before import",
            {"file": path.name},
        )
    return _invalid("E_DOC_PARSE_FAILED", f"cannot open PDF: {exc}", {"file": path.name})


class LocalDocumentParser:
    port = "DocumentParser"

    def __init__(
        self, documents: DocumentsConfig, ocr: OcrConfig, tmp_dir: str, objects: Any = None
    ) -> None:
        self._config = documents
        self._ocr = ocr
        self._tmp_dir = Path(tmp_dir)
        self._objects = objects

    def manifest(self) -> Manifest:
        return Manifest(
            provider=LOCAL_PROVIDER,
            port=self.port,
            provider_version=PARSER_VERSION,
            capabilities=[
                "parse.pdf",
                "parse.office",
                "parse.text",
                "parse.tables",
                "parse.page_locator",
            ],
            limits={
                "ocr": False,
                "tables": self._config.extract_tables,
                "min_chars_per_page": self._ocr.min_chars_per_page,
            },
            notes={
                "engines": ["pypdfium2==5.14.0", "pdfplumber==0.11.10", "markitdown==0.1.9"],
                "ocr": False,
                "async": False,
            },
        )

    def capabilities(self) -> dict[str, Any]:
        return {
            "pdf": True,
            "office": True,
            "text": True,
            "tables": self._config.extract_tables,
            "ocr": False,
        }

    def parse(self, ref: dict[str, Any], opts: dict[str, Any] | None = None) -> dict[str, Any]:
        """Port-shaped entry: fetch the object and parse it via a temp file."""
        if not isinstance(ref, dict) or "bucket" not in ref or "key" not in ref:
            raise _invalid("E_DOC_REF", "parse() requires an ObjectRef with bucket/key")
        if self._objects is None:
            raise PortError(
                code="Unsupported",
                message="parse(ref) is not wired; use parse_path() during ingest",
                provider=LOCAL_PROVIDER,
                provider_code="E_DOC_PARSE_REF_UNWIRED",
            )
        data, meta = self._objects.get(ref["bucket"], ref["key"])
        suffix = Path(ref.get("filename") or "source").suffix or ".bin"
        tmp = self._tmp_dir / f"parse-{uuid.uuid4().hex}{suffix}"
        try:
            tmp.write_bytes(data)
            return self.parse_path(tmp, meta["contentType"], ref.get("documentId", ""), opts)
        finally:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass

    # ---- engine routing --------------------------------------------------

    def parse_path(
        self,
        path: str | Path,
        mime_type: str,
        document_id: str = "",
        opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        opts = opts or {}
        if opts.get("ocr") is True:
            raise PortError(
                code="Unsupported",
                message="OCR is not available: ocr.enabled=false (D22)",
                provider=LOCAL_PROVIDER,
                provider_code="E_DOC_OCR_UNSUPPORTED",
                details={"hint": "set ocr.enabled=false; scanned PDFs are reported as degraded"},
            )
        if mime_type == "application/pdf":
            return self._parse_pdf(Path(path), document_id, opts)
        if mime_type in OFFICE_MIME:
            return self._parse_office(Path(path), mime_type, document_id)
        if mime_type in TEXT_MIME:
            return self._parse_text(Path(path), mime_type, document_id)
        raise _invalid(
            "E_DOC_FORMAT_UNSUPPORTED",
            f"unsupported mime type: {mime_type}",
            {"mimeType": mime_type},
        )

    # ---- engines ---------------------------------------------------------

    def _parse_pdf(
        self, path: Path, document_id: str, opts: dict[str, Any]
    ) -> dict[str, Any]:
        if _pdf_is_encrypted(path):
            raise _invalid(
                "E_DOC_PDF_ENCRYPTED",
                "PDF is encrypted (password required); decrypt it before import",
                {"file": path.name},
            )
        try:
            with _PDFIUM_LOCK:
                import pypdfium2  # noqa: PLC0415 - lazy so check-config needs no parser libs

                pdf = pypdfium2.PdfDocument(str(path))
        except Exception as exc:  # noqa: BLE001 - third-party parse failure
            raise _pdf_open_error(path, exc) from exc

        pages: list[dict[str, Any]] = []
        try:
            with _PDFIUM_LOCK:
                for index in range(len(pdf)):
                    page = pdf[index]
                    try:
                        textpage = page.get_textpage()
                        try:
                            text = normalize_text(textpage.get_text_range() or "")
                        finally:
                            textpage.close()
                    finally:
                        page.close()
                    pages.append(
                        {"number": index + 1, "text": text, "charCount": len(text)}
                    )
        except Exception as exc:  # noqa: BLE001
            raise _invalid(
                "E_DOC_PARSE_FAILED", f"cannot extract PDF text: {exc}", {"file": path.name}
            ) from exc
        finally:
            with _PDFIUM_LOCK:
                pdf.close()

        warnings: list[dict[str, str]] = []
        degraded = False
        threshold = self._ocr.min_chars_per_page
        empty_pages = [p["number"] for p in pages if p["charCount"] < threshold]
        if not pages:
            warnings.append(
                {
                    "code": "EMPTY_TEXT",
                    "message": "PDF has no pages; nothing to index",
                }
            )
            degraded = True
        elif len(empty_pages) == len(pages):
            warnings.append(
                {
                    "code": "NO_OCR_ENABLED",
                    "message": (
                        "文档疑似扫描件，当前未启用 OCR；如需处理请开启 ocr.enabled=true "
                        "并启用 parse profile"
                    ),
                }
            )
            degraded = True
        elif empty_pages:
            warnings.append(
                {
                    "code": "PARTIAL_NO_TEXT_PAGES",
                    "message": f"pages without a text layer: {empty_pages}",
                }
            )
            degraded = True

        tables: list[dict[str, Any]] = []
        if self._config.extract_tables and bool(opts.get("tables", True)):
            tables, table_warning = self._extract_tables(path)
            if table_warning:
                warnings.append(table_warning)
                degraded = True

        return self._result(
            document_id=document_id,
            pages=pages,
            tables=tables,
            warnings=warnings,
            degraded=degraded,
            extra={"emptyPages": empty_pages, "minCharsPerPage": threshold},
        )

    def _extract_tables(self, path: Path) -> tuple[list[dict[str, Any]], dict[str, str] | None]:
        try:
            import pdfplumber  # noqa: PLC0415

            tables: list[dict[str, Any]] = []
            with pdfplumber.open(str(path)) as pdf:
                for page_index, page in enumerate(pdf.pages, start=1):
                    for table_index, rows in enumerate(page.extract_tables() or []):
                        normalized = [
                            ["" if cell is None else str(cell) for cell in row]
                            for row in rows
                        ]
                        tables.append(
                            {
                                "id": f"t{page_index}-{table_index}",
                                "page": page_index,
                                "rows": normalized,
                            }
                        )
            return tables, None
        except Exception as exc:  # noqa: BLE001 - tables are optional
            log.warning(
                "table extraction failed",
                extra={"event": {"event": "table_extract_failed", "error": str(exc)}},
            )
            return [], {
                "code": "TABLE_EXTRACTION_FAILED",
                "message": f"table extraction failed: {exc}",
            }

    def _parse_office(
        self, path: Path, mime_type: str, document_id: str
    ) -> dict[str, Any]:
        try:
            from markitdown import MarkItDown  # noqa: PLC0415

            converter = MarkItDown(enable_plugins=False)
            result = converter.convert(str(path))
            text = normalize_text(result.text_content or "")
        except Exception as exc:  # noqa: BLE001 - third-party parse failure
            raise _invalid(
                "E_DOC_PARSE_FAILED",
                f"cannot parse Office document: {exc}",
                {"file": path.name, "mimeType": mime_type},
            ) from exc
        return self._single_page_result(text, document_id, mime_type)

    def _parse_text(self, path: Path, mime_type: str, document_id: str) -> dict[str, Any]:
        raw = path.read_bytes()
        if not raw:
            raise _invalid("E_DOC_EMPTY", "document is empty", {"file": path.name})
        text: str | None = None
        for encoding in ("utf-8-sig", "utf-8", "gb18030"):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            raise _invalid(
                "E_DOC_ENCODING",
                "cannot decode text document as utf-8 or gb18030",
                {"file": path.name},
            )
        return self._single_page_result(normalize_text(text), document_id, mime_type)

    # ---- result shaping --------------------------------------------------

    def _single_page_result(self, text: str, document_id: str, mime_type: str) -> dict[str, Any]:
        warnings: list[dict[str, str]] = []
        degraded = False
        if not text.strip():
            warnings.append({"code": "EMPTY_TEXT", "message": "document contains no text"})
            degraded = True
        return self._result(
            document_id=document_id,
            pages=[{"number": 1, "text": text, "charCount": len(text)}],
            tables=[],
            warnings=warnings,
            degraded=degraded,
            extra={"mimeType": mime_type},
        )

    def _result(
        self,
        *,
        document_id: str,
        pages: list[dict[str, Any]],
        tables: list[dict[str, Any]],
        warnings: list[dict[str, str]],
        degraded: bool,
        extra: dict[str, Any],
    ) -> dict[str, Any]:
        blocks = [
            {
                "id": f"b{page['number']}",
                "kind": "text",
                "page": page["number"],
                "text": page["text"],
            }
            for page in pages
            if page["text"].strip()
        ]
        metadata = {
            "pageCount": len(pages),
            "charCount": sum(page["charCount"] for page in pages),
            "tableCount": len(tables),
            **extra,
        }
        return {
            "documentId": document_id,
            "pages": pages,
            "blocks": blocks,
            "tables": tables,
            "metadata": metadata,
            "provider": {"name": LOCAL_PROVIDER, "version": PARSER_VERSION},
            "warnings": warnings,
            "degraded": degraded,
        }
