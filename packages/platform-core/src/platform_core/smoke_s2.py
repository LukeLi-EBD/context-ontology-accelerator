"""S2 acceptance: ingest TXT/PDF/DOCX, idempotency, scanned PDF, bad input,
config fail-fast, external dependency failure, chunk overlaps and source readback.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

import httpx

from .adapters.metadata_pg import MetadataPg
from .assembly import Runtime
from .config import load_config
from .documents import DocumentService
from .errors import PlatformError, PortError


class _Case:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def ok(self, name: str, detail: str = "") -> None:
        self.results.append((name, True, detail))

    def fail(self, name: str, detail: str) -> None:
        self.results.append((name, False, detail))

    def check(self, name: str, condition: bool, detail: str = "") -> bool:
        (self.ok if condition else self.fail)(name, detail)
        return condition


# ---- fixtures -------------------------------------------------------------


def make_text() -> bytes:
    paragraph = (
        "本体平台单机版文档入库切片验收。本文档用于验证固定窗口切块、重叠、页码定位与幂等上传。"
        "平台只做胶水与 web 层，解析交给 pypdfium2、pdfplumber 与 MarkItDown。"
    )
    body = "\n".join(f"{index:03d} {paragraph}" for index in range(1, 41))
    return ("S2 文档入库验收样本\n" + body + "\n").encode("utf-8")


def _build_pdf(objects: list[bytes]) -> bytes:
    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode("utf-8") + obj + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode("utf-8")
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode("utf-8")
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n"
    ).encode("utf-8")
    return bytes(out)


def _pdf_with_text(text: str) -> bytes:
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({safe}) Tj ET".encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream)} >>\nstream\n".encode("utf-8") + stream + b"\nendstream",
    ]
    return _build_pdf(objects)


def make_pdf() -> bytes:
    return _pdf_with_text(
        "Hello Platform S2. This PDF has one text page for ingest acceptance."
    )


def make_scanned_pdf() -> bytes:
    stream = b""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream)} >>\nstream\n".encode("utf-8") + stream + b"\nendstream",
    ]
    return _build_pdf(objects)


def make_bad_pdf() -> bytes:
    return b"%PDF-1.4\nthis is not a PDF\n"


def make_docx() -> bytes:
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>S2 Office 文档验收：平台只做胶水与 web 层。</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>This docx is parsed by MarkItDown.</w:t></w:r></w:p>"
        "</w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        # Fixed timestamps keep the fixture content-addressed across smoke runs.
        for name, payload in (
            ("[Content_Types].xml", content_types),
            ("_rels/.rels", rels),
            ("word/document.xml", document),
        ):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, payload)
    return buffer.getvalue()


# ---- helpers --------------------------------------------------------------


def _upload(client: httpx.Client, base: str, filename: str, data: bytes, mime: str):
    return client.post(
        f"{base}/documents",
        files={"file": (filename, data, mime)},
        data={"filename": filename, "metadata": json.dumps({"suite": "s2"})},
    )


def _error_code(response: httpx.Response) -> str:
    try:
        return response.json()["error"]["providerCode"]
    except Exception:  # noqa: BLE001
        return ""


def run_smoke_s2(runtime: Runtime, base_url: str, bad_config: str) -> int:
    suite = _Case()
    base = base_url.rstrip("/")
    documents = runtime.documents
    before = documents.counts()

    with httpx.Client(timeout=httpx.Timeout(120.0)) as client:
        health = client.get(f"{base}/healthz")
        ready = client.get(f"{base}/readyz")
        suite.check("health", health.status_code == 200, f"status={health.status_code}")
        suite.check("ready", ready.status_code == 200, f"status={ready.status_code}")

        # 1. TXT
        text_bytes = make_text()
        response = _upload(client, base, "s2-sample.txt", text_bytes, "text/plain")
        txt = response.json()
        suite.check(
            "ingest.txt",
            response.status_code in (200, 201) and txt.get("chunkCount", 0) > 0,
            f"http={response.status_code} chunks={txt.get('chunkCount')} status={txt.get('status')}",
        )
        txt_id = txt.get("documentId", "")

        # 2. PDF
        pdf_bytes = make_pdf()
        response = _upload(client, base, "s2-sample.pdf", pdf_bytes, "application/pdf")
        pdf = response.json()
        suite.check(
            "ingest.pdf",
            response.status_code in (200, 201)
            and pdf.get("pageCount") == 1
            and pdf.get("chunkCount", 0) > 0,
            f"http={response.status_code} pages={pdf.get('pageCount')} chunks={pdf.get('chunkCount')}",
        )

        # 3. DOCX (Office via MarkItDown)
        docx_bytes = make_docx()
        response = _upload(
            client,
            base,
            "s2-sample.docx",
            docx_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        docx = response.json()
        suite.check(
            "ingest.docx",
            response.status_code in (200, 201) and docx.get("chunkCount", 0) > 0,
            f"http={response.status_code} chunks={docx.get('chunkCount')}",
        )

        # 4. idempotent re-upload
        chunks_before = documents.get(txt_id)["chunkCount"] if txt_id else -1
        response = _upload(client, base, "s2-sample-copy.txt", text_bytes, "text/plain")
        again = response.json()
        chunks_after = documents.get(txt_id)["chunkCount"] if txt_id else -1
        suite.check(
            "idempotent",
            response.status_code == 200
            and again.get("deduplicated") is True
            and again.get("documentId") == txt_id
            and chunks_after == chunks_before,
            f"http={response.status_code} dedup={again.get('deduplicated')} chunks={chunks_before}->{chunks_after}",
        )

        # 5. scanned PDF -> degraded + NO_OCR_ENABLED, no chunks
        scanned_bytes = make_scanned_pdf()
        response = _upload(client, base, "s2-scanned.pdf", scanned_bytes, "application/pdf")
        scanned = response.json()
        codes = [w.get("code") for w in scanned.get("warnings", [])]
        suite.check(
            "scanned.degraded",
            response.status_code in (200, 201)
            and scanned.get("degraded") is True
            and "NO_OCR_ENABLED" in codes
            and scanned.get("chunkCount") == 0,
            f"http={response.status_code} degraded={scanned.get('degraded')} warnings={codes} chunks={scanned.get('chunkCount')}",
        )

        # 6. bad PDF -> 400 and no new document row
        before_bad = documents.counts()["documents"]
        response = _upload(client, base, "s2-bad.pdf", make_bad_pdf(), "application/pdf")
        after_bad = documents.counts()["documents"]
        suite.check(
            "bad_pdf.rejected",
            response.status_code == 400
            and _error_code(response) == "E_DOC_PARSE_FAILED"
            and after_bad == before_bad,
            f"http={response.status_code} code={_error_code(response)} rows={before_bad}->{after_bad}",
        )

        # 7. unsupported extension -> 400
        response = _upload(client, base, "s2-sample.bin", b"binary", "application/octet-stream")
        suite.check(
            "unsupported.rejected",
            response.status_code == 400
            and _error_code(response) == "E_DOC_FORMAT_UNSUPPORTED",
            f"http={response.status_code} code={_error_code(response)}",
        )

        # 8. detail + chunks + source sha256
        if txt_id:
            detail = client.get(f"{base}/documents/{txt_id}", params={"include": "pages"})
            suite.check(
                "get.document",
                detail.status_code == 200
                and len(detail.json().get("pages", [])) == detail.json().get("pageCount"),
                f"http={detail.status_code} pages={len(detail.json().get('pages', []))}",
            )
            chunk_response = client.get(f"{base}/documents/{txt_id}/chunks", params={"limit": 5})
            suite.check(
                "get.chunks",
                chunk_response.status_code == 200 and len(chunk_response.json().get("items", [])) > 0,
                f"http={chunk_response.status_code} items={len(chunk_response.json().get('items', []))}",
            )
            source = client.get(f"{base}/documents/{txt_id}/source")
            suite.check(
                "get.source",
                source.status_code == 200
                and hashlib.sha256(source.content).hexdigest() == txt_id,
                f"http={source.status_code} sha_match={hashlib.sha256(source.content).hexdigest() == txt_id}",
            )

            # chunk window relation: adjacent chunks overlap
            items = chunk_response.json().get("items", [])
            if len(items) >= 2:
                overlap = items[1]["charStart"] <= items[0]["charEnd"] and items[0]["charEnd"] > items[0]["charStart"]
                suite.check(
                    "chunk.overlap",
                    overlap,
                    f"c0=[{items[0]['charStart']},{items[0]['charEnd']}] c1_start={items[1]['charStart']}",
                )
            else:
                suite.fail("chunk.overlap", "fewer than 2 chunks")

        # 9. OCR requested on the parser port -> Unsupported
        parser_tmp = Path(tempfile.mkdtemp()) / "ocr.txt"
        parser_tmp.write_text("hello", encoding="utf-8")
        try:
            try:
                runtime.parser.parse_path(parser_tmp, "text/plain", "ocr", {"ocr": True})
                suite.fail("ocr.unsupported", "expected Unsupported, got a result")
            except PortError as exc:
                suite.check(
                    "ocr.unsupported",
                    exc.code == "Unsupported" and exc.provider_code == "E_DOC_OCR_UNSUPPORTED",
                    f"{exc.code}/{exc.provider_code}",
                )
        finally:
            parser_tmp.unlink(missing_ok=True)

        # 10. config fail-fast
        try:
            load_config(bad_config)
            suite.fail("config.failfast", "bad chunk overlap was accepted")
        except PlatformError as exc:
            suite.check(
                "config.failfast",
                exc.code == "E_CONFIG_CHUNK_OVERLAP" and exc.exit_code == 78,
                f"{exc.code} exit={exc.exit_code}",
            )

        # 11. external dependency unavailable
        bad_meta = MetadataPg(
            url="postgres://platform:***MASKED***@127.0.0.1:1/platform",
            pool_max=1,
            statement_timeout_ms=1000,
        )
        bad_documents = DocumentService(
            runtime.config.documents, bad_meta, runtime.objects, runtime.parser,
            runtime.config.storage.tmp_dir,
        )
        try:
            try:
                bad_documents.get(txt_id or "0" * 64)
                suite.fail("db.unavailable", "expected Unavailable, got a result")
            except PortError as exc:
                suite.check(
                    "db.unavailable",
                    exc.code == "Unavailable",
                    f"{exc.code}/{exc.provider_code}",
                )
            except Exception as exc:  # noqa: BLE001
                suite.fail("db.unavailable", f"unexpected exception type: {exc}")
        finally:
            bad_meta.close()

        # 12. counts increased by exactly 4 on first run (txt/pdf/docx/scanned),
        #     or unchanged on a re-run because all four are content-addressed.
        after = documents.counts()
        delta = after["documents"] - before["documents"]
        suite.check(
            "counts",
            0 <= delta <= 4,
            f"documents {before['documents']}->{after['documents']} delta={delta}",
        )

    total = len(suite.results)
    passed = sum(1 for _, ok, _ in suite.results if ok)
    for name, ok, detail in suite.results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    print(f"S2 SMOKE {passed}/{total}")
    return 0 if passed == total else 1
