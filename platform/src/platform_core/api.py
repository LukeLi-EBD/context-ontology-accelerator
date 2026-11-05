"""HTTP surface: health/readiness/status + S2 document ingest.

No auth, no metrics, no queue. Errors are mapped from PortError to stable HTTP
codes so clients see provider codes instead of stack traces.
"""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, File, Form, Query, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from . import __version__
from .adapters.ontology_pg import (
    build_import_document,
    get_import_record,
    import_format_from_name,
    parse_import_document,
    persist_import,
    publish_import,
)
from .assembly import Runtime
from .bootstrap import CheckResult
from .errors import PortError
from . import webui

WEB_DIR = Path(__file__).resolve().parents[2] / "web"

_HTTP_STATUS = {
    "InvalidArgument": 400,
    "NotFound": 404,
    "Conflict": 409,
    "PreconditionFailed": 412,
    "Unsupported": 400,
    "PermissionDenied": 403,
    "PolicyRejected": 422,
    "ResourceExhausted": 413,
    "DeadlineExceeded": 504,
    "Unavailable": 503,
    "Aborted": 409,
    "Internal": 500,
    "DataLoss": 500,
}


def create_app(runtime: Runtime, checks: list[CheckResult]) -> FastAPI:
    app = FastAPI(
        title="Platform Kernel",
        version=__version__,
        description="S0-S2: health, readiness, status, document ingest.",
    )
    # S7: the static UI also works when opened from disk (Origin: null). There
    # is no auth, so this is not a security boundary -- it only lets the
    # file:// entry point reach 127.0.0.1:8080.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["null", "http://127.0.0.1:8080", "http://localhost:8080"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.exception_handler(PortError)
    def port_error_handler(_request: Request, exc: PortError) -> JSONResponse:
        body = {
            "error": {
                "code": exc.code,
                "provider": exc.provider,
                "providerCode": exc.provider_code,
                "message": exc.message,
                "retryable": exc.retryable,
                "details": exc.details or {},
            }
        }
        return JSONResponse(status_code=_HTTP_STATUS.get(exc.code, 500), content=body)

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        return {"status": "ok", "version": __version__}

    @app.get("/readyz")
    def readyz() -> JSONResponse:
        results: dict[str, Any] = {}

        try:
            runtime.metadata.health()
            results["database"] = {"status": "ok"}
        except Exception as exc:
            results["database"] = {"status": "fail", "detail": str(exc)}

        try:
            runtime.graph.ask("ASK {}")
            results["graph"] = {"status": "ok"}
        except Exception as exc:
            results["graph"] = {"status": "fail", "detail": str(exc)}

        try:
            root = Path(runtime.config.storage.root)
            blobs = root / "blobs"
            if not blobs.is_dir():
                raise RuntimeError(f"blobs directory missing: {blobs}")
            usage = shutil.disk_usage(root)
            free_pct = (usage.free / usage.total) * 100 if usage.total else 0
            if free_pct < runtime.config.storage.min_free_pct:
                raise RuntimeError(
                    f"disk free {free_pct:.1f}% < min_free_pct={runtime.config.storage.min_free_pct}%"
                )
            results["storage"] = {"status": "ok", "disk_free_pct": round(free_pct, 2)}
        except Exception as exc:
            results["storage"] = {"status": "fail", "detail": str(exc)}

        healthy = all(item["status"] == "ok" for item in results.values())
        return JSONResponse(status_code=200 if healthy else 503, content={"status": "ok" if healthy else "degraded", "checks": results})

    # ---- S2 documents ---------------------------------------------------

    @app.post("/documents")
    def upload_document(
        file: UploadFile = File(...),
        filename: str | None = Form(default=None),
        metadata: str | None = Form(default=None),
    ) -> JSONResponse:
        try:
            extra = json.loads(metadata) if metadata else {}
        except json.JSONDecodeError as exc:
            raise PortError(
                code="InvalidArgument",
                message=f"metadata is not valid JSON: {exc}",
                provider="platform",
                provider_code="E_DOC_METADATA",
            ) from exc
        if not isinstance(extra, dict):
            raise PortError(
                code="InvalidArgument",
                message="metadata must be a JSON object",
                provider="platform",
                provider_code="E_DOC_METADATA",
            )
        effective_name = filename or file.filename or "upload.bin"
        result = runtime.documents.ingest_stream(file.file, effective_name, extra)
        status_code = 200 if result.get("deduplicated") else 201
        return JSONResponse(status_code=status_code, content=result)

    @app.get("/documents")
    def list_documents(
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        return runtime.documents.list(limit=limit, offset=offset)

    @app.get("/documents/{document_id}")
    def get_document(
        document_id: str,
        include: str | None = Query(default=None),
    ) -> dict[str, Any]:
        return runtime.documents.get(document_id, include_pages="pages" in (include or ""))

    @app.get("/documents/{document_id}/chunks")
    def document_chunks(
        document_id: str,
        limit: int = Query(default=100, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        return runtime.documents.chunks(document_id, limit=limit, offset=offset)

    @app.get("/documents/{document_id}/source")
    def document_source(document_id: str) -> Response:
        from urllib.parse import quote

        data, meta = runtime.documents.source(document_id)
        content_type = meta.get("contentType", "application/octet-stream")
        headers = {
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(document_id)}",
            "X-Content-Sha256": meta.get("ref", {}).get("checksum", {}).get("value", ""),
            "X-Presign": "false",
        }
        return Response(content=data, media_type=content_type, headers=headers)

    @app.get("/imports/batches")
    def import_batches(limit: int = Query(default=5, ge=1, le=50)) -> dict[str, Any]:
        from .importer import batches_overview

        return batches_overview(runtime, limit)

    @app.get("/imports/items")
    def import_items(
        batch_id: str | None = Query(default=None),
        status: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=500),
    ) -> dict[str, Any]:
        from .importer import list_items

        return {"items": list_items(runtime, batch_id, status, limit)}

    # ---- S3 retrieval ----------------------------------------------------

    @app.post("/documents/{document_id}/index")
    def index_document(
        document_id: str,
        max_batches: int | None = Query(default=None, ge=0, le=100),
    ) -> dict[str, Any]:
        # maxBatches=N pauses between batches; re-POST with the same/None to resume
        # (the checkpoint + chunk_embedding rows make the resume idempotent).
        return runtime.search.index_document(document_id, max_batches=max_batches)

    @app.get("/search")
    def search(
        q: str = Query(min_length=1, max_length=2000),
        limit: int | None = Query(default=None, ge=1, le=100),
        mode: str = Query(default="hybrid"),
    ) -> dict[str, Any]:
        if mode not in ("hybrid", "vector", "lexical"):
            raise PortError(
                code="InvalidArgument",
                message=f"unsupported search mode: {mode}",
                provider="platform",
                provider_code="E_SEARCH_MODE",
                details={"mode": mode, "allowed": ["hybrid", "vector", "lexical"]},
            )
        return runtime.search.hybrid_search(q, limit=limit, mode=mode)  # type: ignore[arg-type]

    # ---- Q4: ontology coverage pre-check ---------------------------------

    @app.get("/answerable")
    def answerable_get(
        q: str = Query(min_length=1, max_length=2000),
        ontologyVersion: str | None = Query(default=None),
        minCoverage: float | None = Query(default=None, ge=0.0, le=1.0),
    ) -> dict[str, Any]:
        return runtime.answerable.check(
            q, ontology_version=ontologyVersion, min_coverage=minCoverage
        )

    @app.post("/answerable")
    def answerable_post(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        return runtime.answerable.check(
            str(body.get("query") or ""),
            ontology_version=body.get("ontologyVersion"),
            min_coverage=body.get("minCoverage"),
        )

    # ---- v3 metric registry / publishability guard -----------------------

    @app.get("/metrics")
    def metrics_list(domain: str | None = None) -> dict[str, Any]:
        return {"metrics": runtime.metrics.list(domain=domain)}

    @app.get("/metrics/{metric_id}")
    def metric_get(metric_id: str) -> dict[str, Any]:
        return runtime.metrics.get(metric_id)

    @app.get("/metrics/{metric_id}/output")
    def metric_output(
        metric_id: str,
        internal: bool = False,
        compute: bool = False,
        as_of: date | None = Query(None, alias="asOf"),
        period_start: date | None = Query(None, alias="periodStart"),
        period_end: date | None = Query(None, alias="periodEnd"),
        entity_key: str | None = Query(None, alias="entityKey"),
        institution: str | None = None,
    ) -> dict[str, Any]:
        if not compute:
            return runtime.metrics.output(metric_id, internal=internal)
        return runtime.metrics.compute(
            metric_id,
            internal=internal,
            as_of=as_of,
            period_start=period_start,
            period_end=period_end,
            entity_key=entity_key,
            institution=institution,
        )

    # ---- S4 extraction ---------------------------------------------------

    @app.post("/documents/{document_id}/extract")
    def extract_document(
        document_id: str,
        body: dict[str, Any] | None = Body(default=None),
    ) -> dict[str, Any]:
        mode = (body or {}).get("mode", "auto")
        if mode not in ("auto", "rules", "llm"):
            raise PortError(
                code="InvalidArgument",
                message=f"unsupported extraction mode: {mode}",
                provider="platform",
                provider_code="E_EXTRACT_MODE",
                details={"mode": mode, "allowed": ["auto", "rules", "llm"]},
            )
        return runtime.extraction.extract_document(document_id, mode=mode)

    @app.get("/candidates")
    def list_candidates(
        state: str | None = Query(default=None),
        documentId: str | None = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
    ) -> dict[str, Any]:
        items = runtime.extraction.list_candidates(
            state=state, document_id=documentId, limit=limit
        )
        return {"candidates": items, "count": len(items)}

    @app.post("/candidates/{candidate_id}/approve")
    def approve_candidate(
        candidate_id: str,
        graph: str | None = Query(default=None),
    ) -> dict[str, Any]:
        return runtime.extraction.approve(candidate_id, graph=graph)

    @app.post("/candidates/{candidate_id}/reject")
    def reject_candidate(
        candidate_id: str,
        body: dict[str, Any] | None = Body(default=None),
    ) -> dict[str, Any]:
        return runtime.extraction.reject(candidate_id, (body or {}).get("reason"))

    # ---- S8 fact governance ---------------------------------------------

    @app.get("/facts")
    def list_facts(
        state: str = Query(default="active"),
        subject: str | None = Query(default=None),
        predicate: str | None = Query(default=None),
        sourceDocumentId: str | None = Query(default=None),
        conflict: bool = Query(default=False),
        limit: int = Query(default=100, ge=1, le=500),
    ) -> dict[str, Any]:
        result = runtime.facts.list(
            state=state,
            subject=subject,
            predicate=predicate,
            source_document_id=sourceDocumentId,
            conflict_only=conflict,
            limit=limit,
        )
        result["conflicts"] = runtime.facts.conflicts()
        return result

    @app.get("/facts/conflicts")
    def fact_conflicts(includeAccepted: bool = Query(default=False)) -> dict[str, Any]:
        items = runtime.facts.conflicts(include_accepted=includeAccepted)
        for entry in items:
            for fact in entry.get("facts", []):
                candidate_id = (fact.get("source") or {}).get("candidateId")
                if not candidate_id:
                    continue
                rows = runtime.metadata.query(
                    """
                    SELECT e.chunk_id, c.text
                      FROM platform.extraction_candidate e
                      JOIN platform.document_chunk c ON c.chunk_id = e.chunk_id
                     WHERE e.candidate_id = %s
                    """,
                    (candidate_id,),
                )
                if rows:
                    fact["evidence"] = {
                        "chunkId": rows[0]["chunk_id"],
                        "text": rows[0]["text"][:240],
                    }
        pending = [item for item in items if item["pending"]]
        return {
            "conflicts": items, "count": len(items),
            "pending": len(pending), "includeAccepted": includeAccepted,
        }

    @app.post("/facts/conflicts/resolve")
    def resolve_conflict(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        missing = [
            key for key in ("subject", "predicate", "action")
            if not isinstance(body.get(key), str) or not body.get(key)
        ]
        if missing:
            raise PortError(
                code="InvalidArgument",
                message=f"missing adjudication fields: {missing}",
                provider="platform",
                provider_code="E_FACT_MISSING_FIELDS",
                details={"missing": missing},
            )
        return runtime.facts.resolve_conflict(
            subject=body["subject"],
            predicate=body["predicate"],
            action=body["action"],
            actor=body.get("actor", "operator"),
            reason=body.get("reason"),
            keep=body.get("keep"),
            merged_object=body.get("mergedObject"),
            merged_object_kind=body.get("mergedObjectKind", "iri"),
            graph=body.get("graph"),
            source_document_id=body.get("sourceDocumentId"),
        )

    @app.post("/facts/conflicts/undo")
    def undo_conflict(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        return runtime.facts.undo_resolution(
            event_id=body.get("eventId"),
            subject=body.get("subject"),
            predicate=body.get("predicate"),
            actor=body.get("actor", "operator"),
            reason=body.get("reason"),
            dry_run=bool(body.get("dryRun", False)),
        )

    @app.post("/facts/conflicts/unmerge")
    def unmerge_conflict(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        merge_event_id = body.get("eventId")
        if not isinstance(merge_event_id, int):
            raise PortError(
                code="InvalidArgument",
                message="unmerge requires an integer eventId",
                provider="platform",
                provider_code="E_FACT_UNDO_TARGET",
                details={"field": "eventId"},
            )
        return runtime.facts.unmerge(
            merge_event_id,
            actor=body.get("actor", "operator"),
            reason=body.get("reason"),
            dry_run=bool(body.get("dryRun", False)),
        )

    @app.post("/facts/conflicts/batch")
    def batch_keep(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        return runtime.facts.batch_keep(
            keep=body.get("keep"),
            predicate=body.get("predicate"),
            subject=body.get("subject"),
            source_document_id=body.get("sourceDocumentId"),
            actor=body.get("actor", "operator"),
            reason=body.get("reason"),
            dry_run=bool(body.get("dryRun", True)),
        )

    @app.post("/facts")
    def assert_fact(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        missing = [
            key for key in ("subject", "predicate", "object")
            if not isinstance(body.get(key), str) or not body.get(key)
        ]
        if missing:
            raise PortError(
                code="InvalidArgument",
                message=f"missing fact fields: {missing}",
                provider="platform",
                provider_code="E_FACT_MISSING_FIELDS",
                details={"missing": missing},
            )
        return runtime.facts.record(
            subject=body["subject"],
            predicate=body["predicate"],
            object_value=body["object"],
            object_kind=body.get("objectKind", "iri"),
            graph=body.get("graph", "urn:platform:graph:abox:main"),
            source_kind=body.get("sourceKind", "manual"),
            source_document_id=body.get("sourceDocumentId"),
            source_run_id=body.get("sourceRunId"),
            actor=body.get("actor", "api"),
        )

    @app.post("/facts/retract")
    def retract_facts(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        return runtime.facts.retract_by_source(
            document_id=body.get("sourceDocumentId"),
            run_id=body.get("sourceRunId"),
            reason=body.get("reason"),
            actor=body.get("actor", "api"),
        )

    @app.get("/facts/{fact_id}")
    def get_fact(fact_id: str) -> dict[str, Any]:
        fact = runtime.facts.get(fact_id)
        fact["events"] = runtime.facts.events(fact_id)
        return fact

    @app.post("/facts/{fact_id}/retract")
    def retract_fact(
        fact_id: str,
        body: dict[str, Any] | None = Body(default=None),
    ) -> dict[str, Any]:
        return runtime.facts.retract(
            fact_id, (body or {}).get("reason"), (body or {}).get("actor", "api")
        )

    @app.post("/facts/{fact_id}/restore")
    def restore_fact(
        fact_id: str,
        body: dict[str, Any] | None = Body(default=None),
    ) -> dict[str, Any]:
        return runtime.facts.restore(fact_id, (body or {}).get("actor", "api"))

    @app.get("/facts/{fact_id}/events")
    def fact_events(fact_id: str) -> dict[str, Any]:
        return {"factId": fact_id, "events": runtime.facts.events(fact_id)}

    @app.get("/facts/events/export")
    def export_fact_events(
        start: str | None = Query(default=None, alias="from"),
        end: str | None = Query(default=None, alias="to"),
        sourceDocumentId: str | None = Query(default=None),
    ) -> dict[str, Any]:
        from .fact_export import build_ndjson, export_meta, summarize

        data = runtime.facts.export_events(start, end, sourceDocumentId)
        conflicts = runtime.facts.conflicts(include_accepted=True)
        fact_ids = [
            item["factId"] for item in data["windowItems"] if item.get("factId")
        ]
        data["snapshot"] = runtime.facts.snapshot(fact_ids=fact_ids)
        meta = export_meta(
            data, data["snapshot"], runtime.facts.assertion_count(),
            {"from": start, "to": end, "sourceDocumentId": sourceDocumentId},
        )
        data["export"] = meta
        data["ndjson"] = build_ndjson(data["items"])
        data["snapshotNdjson"] = build_ndjson(data["snapshot"])
        data["markdown"] = summarize(data["items"], conflicts, meta)
        return data

    # ---- S11 T-Box change governance -------------------------------------

    @app.get("/ontology/versions")
    def ontology_versions() -> dict[str, Any]:
        versions = runtime.ontology.list_versions()
        return {
            "items": versions,
            "count": len(versions),
            "pointer": runtime.ontology.current(),
        }

    @app.get("/ontology/versions/{version_id}")
    def ontology_version(version_id: str) -> dict[str, Any]:
        result = runtime.ontology.get(version_id)
        result["graphTripleCount"] = runtime.ontology.graph_count(version_id)
        result["proposals"] = runtime.ontology.list_proposals(version_id)["items"]
        result["events"] = runtime.ontology.events(version_id)["items"]
        return result

    @app.get("/ontology/versions/{version_id}/diff")
    def ontology_diff(
        version_id: str,
        against: str | None = Query(default=None),
    ) -> dict[str, Any]:
        return runtime.ontology.diff(against, version_id)

    @app.get("/ontology/versions/{version_id}/export")
    def ontology_export(
        version_id: str,
        format: str = Query(default="turtle"),
    ) -> Response:
        exported = runtime.ontology.export_version(version_id, format)
        media = "text/turtle" if format == "turtle" else "application/n-quads"
        filename = f"{version_id}.{'ttl' if format == 'turtle' else 'nq'}"
        return Response(
            content=exported["content"],
            media_type=media,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.post("/ontology/versions/{version_id}/propose")
    def ontology_propose(
        version_id: str,
        body: dict[str, Any] = Body(...),
    ) -> dict[str, Any]:
        return runtime.ontology.propose(
            version_id,
            change_summary=body.get("changeSummary", ""),
            actor=body.get("actor", "operator"),
            against_version=body.get("againstVersion"),
        )

    @app.get("/ontology/proposals")
    def ontology_proposals(versionId: str | None = Query(default=None)) -> dict[str, Any]:
        return runtime.ontology.list_proposals(versionId)

    @app.post("/ontology/proposals/{proposal_id}/approve")
    def ontology_approve(
        proposal_id: str,
        body: dict[str, Any] | None = Body(default=None),
    ) -> dict[str, Any]:
        payload = body or {}
        return runtime.ontology.approve(
            proposal_id, actor=payload.get("actor", "operator"), reason=payload.get("reason")
        )

    @app.post("/ontology/publish")
    def ontology_publish(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        version_id = body.get("versionId")
        if not isinstance(version_id, str) or not version_id:
            raise PortError(
                code="InvalidArgument",
                message="publish requires versionId",
                provider="platform",
                provider_code="E_ONTOLOGY_VERSION_REQUIRED",
            )
        return runtime.ontology.publish(
            version_id,
            proposal_id=body.get("proposalId"),
            acknowledge_breaking=bool(body.get("acknowledgeBreaking", False)),
            actor=body.get("actor", "operator"),
            reason=body.get("reason"),
        )

    @app.post("/ontology/rollback")
    def ontology_rollback(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        version_id = body.get("versionId")
        if not isinstance(version_id, str) or not version_id:
            raise PortError(
                code="InvalidArgument",
                message="rollback requires versionId",
                provider="platform",
                provider_code="E_ONTOLOGY_VERSION_REQUIRED",
            )
        return runtime.ontology.rollback_to(
            version_id, actor=body.get("actor", "operator"), reason=body.get("reason")
        )

    @app.get("/ontology/events")
    def ontology_events(
        versionId: str | None = Query(default=None),
        limit: int = Query(default=200, ge=1, le=1000),
    ) -> dict[str, Any]:
        return runtime.ontology.events(versionId, limit=limit)

    @app.get("/ontology/verify")
    def ontology_verify() -> dict[str, Any]:
        return runtime.ontology.verify_events()

    # ---- G-01: versioned TTL import --------------------------------------

    @app.post("/ontology/import")
    @app.post("/api/ontology/import")
    async def ontology_import(request: Request) -> dict[str, Any]:
        """G-01 first half: parse the uploaded ontology and return real counts.

        Boundary of this slice: no owl:imports closure, no SHACL, no publish.
        Every response therefore carries usable=false plus an explicit reason.
        Input: multipart `file` + `targetNamespace`/`changeSummary`/`author`,
        or JSON `{content|contentBase64, ...}`, or a raw TTL body.
        """
        ctype = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
        payload: dict[str, Any] = {}
        raw: bytes | None = None
        filename = ""
        if ctype == "multipart/form-data":
            form = await request.form()
            upload = form.get("file")
            if upload is None or not hasattr(upload, "read"):
                raise PortError(
                    code="InvalidArgument",
                    message="multipart import requires a `file` part",
                    provider="platform",
                    provider_code="E_ONTOLOGY_IMPORT_SOURCE",
                )
            filename = str(getattr(upload, "filename", "") or "")
            raw = await upload.read()
            payload = {
                key: form.get(key)
                for key in ("targetNamespace", "changeSummary", "author", "format")
                if form.get(key)
            }
        else:
            body = await request.body()
            if ctype == "application/json":
                try:
                    payload = json.loads(body.decode("utf-8") or "{}")
                except ValueError as exc:
                    raise PortError(
                        code="InvalidArgument",
                        message=f"import body is not valid JSON: {exc}",
                        provider="platform",
                        provider_code="E_ONTOLOGY_IMPORT_BODY",
                    ) from exc
            elif body:
                raw = body

        def _option(name: str, default: Any = None) -> Any:
            if name in payload:
                return payload[name]
            value = request.query_params.get(name)
            return default if value is None else value

        if raw is None and isinstance(payload.get("content"), str):
            raw = payload["content"].encode("utf-8")
        if raw is None and payload.get("contentBase64"):
            import base64

            try:
                raw = base64.b64decode(payload["contentBase64"])
            except ValueError as exc:
                raise PortError(
                    code="InvalidArgument",
                    message=f"contentBase64 is not valid base64: {exc}",
                    provider="platform",
                    provider_code="E_ONTOLOGY_IMPORT_BODY",
                ) from exc
        if raw is None:
            raise PortError(
                code="InvalidArgument",
                message="import requires a `file` upload or content in the body",
                provider="platform",
                provider_code="E_ONTOLOGY_IMPORT_SOURCE",
            )

        rdf_format = str(_option("format") or import_format_from_name(filename))
        result, merged = build_import_document(
            raw,
            rdf_format=rdf_format,
            target_namespace=_option("targetNamespace") or _option("namespace"),
            author=_option("author"),
            change_summary=_option("changeSummary"),
            shapes_dir=runtime.config.reasoning.shapes_dir,
            consistency_checker=runtime.reasoning.check_consistency,
            shapes_provider=runtime.shapes.load_deployed,
        )
        return persist_import(result, merged, raw, runtime.metadata, runtime.graph)

    @app.get("/ontology/imports/{import_id}")
    @app.get("/api/ontology/imports/{import_id}")
    def ontology_import_record(import_id: str) -> dict[str, Any]:
        record = get_import_record(runtime.metadata, import_id)
        if record is None:
            raise PortError(
                code="NotFound",
                message=f"import {import_id} not found",
                provider="platform",
                provider_code="E_ONTOLOGY_IMPORT_NOT_FOUND",
            )
        return record

    @app.post("/ontology/imports/{import_id}/publish")
    @app.post("/api/ontology/imports/{import_id}/publish")
    def ontology_import_publish(
        import_id: str, body: dict[str, Any] | None = Body(default=None)
    ) -> dict[str, Any]:
        payload = body or {}
        dry_run = payload.get("dryRun", True)
        if not isinstance(dry_run, bool):
            raise PortError(
                code="InvalidArgument",
                message=f"dryRun must be a boolean, got {type(dry_run).__name__}",
                provider="platform",
                provider_code="E_ONTOLOGY_IMPORT_BODY",
            )
        return publish_import(
            runtime.metadata,
            runtime.graph,
            runtime.objects,
            runtime.ontology,
            import_id,
            dry_run=dry_run,
            actor=str(payload.get("actor") or "operator"),
            change_summary=payload.get("changeSummary"),
            acknowledge_breaking=bool(payload.get("acknowledgeBreaking", False)),
            abox_graphs=runtime.config.reasoning.abox_graphs,
            publish_existing=bool(payload.get("publishExisting", False)),
        )

    @app.put("/ontology/shapes")
    @app.put("/api/ontology/shapes")
    async def ontology_shapes_deploy(
        request: Request,
        namespace: str = Query(...),
        shapesId: str | None = Query(default=None),
    ) -> dict[str, Any]:
        raw = await request.body()
        rdf_format = "turtle"
        actor = "operator"
        body_shapes_id: str | None = None
        if request.headers.get("content-type", "").startswith("application/json"):
            try:
                payload = json.loads(raw or b"{}")
            except ValueError as exc:
                raise PortError(
                    code="InvalidArgument",
                    message=f"shapes body is not valid JSON: {exc}",
                    provider="platform",
                    provider_code="E_SHAPES_PARSE",
                ) from exc
            raw = str(payload.get("content") or "").encode("utf-8")
            rdf_format = str(payload.get("format") or "turtle")
            body_shapes_id = payload.get("shapesId")
            actor = str(payload.get("actor") or "operator")
        if not raw.strip():
            raise PortError(
                code="InvalidArgument",
                message="shapes deployment requires a TTL body",
                provider="platform",
                provider_code="E_SHAPES_SOURCE",
            )
        return runtime.shapes.deploy(
            namespace,
            raw,
            rdf_format=rdf_format,
            shapes_id=shapesId or body_shapes_id,
            actor=actor,
        )

    @app.get("/ontology/shapes")
    @app.get("/api/ontology/shapes")
    def ontology_shapes_list() -> dict[str, Any]:
        return runtime.shapes.list()

    # ---- GSP write guard (G-01: no GSP bypass) ---------------------------

    GSP_PROTECTED = (
        "urn:platform:graph:tbox:",
        "urn:fsldm:",
        "https://w3id.org/fsldm/",
    )

    @app.api_route("/store", methods=["PUT", "POST", "DELETE"])
    @app.api_route("/api/store", methods=["PUT", "POST", "DELETE"])
    def gsp_write(graph: str | None = Query(default=None)) -> JSONResponse:
        """Reject Graph Store Protocol writes.

        T-Box state must move through /ontology/import + publish gates. Allowing
        a write here would be a governance bypass, so every GSP write is refused
        with a stable code instead of being forwarded to Oxigraph.
        """
        target = graph or ""
        protected = any(target.startswith(prefix) for prefix in GSP_PROTECTED)
        raise PortError(
            code="PermissionDenied",
            message=(
                "GSP writes are disabled; ontology state must go through "
                "/ontology/import and the publish gates"
            ),
            provider="platform",
            provider_code="E_GSP_GOVERNANCE_REQUIRED",
            details={"graph": target or None, "protectedGraph": protected},
        )

    # ---- S5 reasoning + SHACL -------------------------------------------

    @app.post("/reasoning/materialize")
    def materialize(body: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
        payload = body or {}
        profile = payload.get("profile")
        if profile is not None and profile not in ("EL", "OWL2EL"):
            raise PortError(
                code="InvalidArgument",
                message=f"unsupported reasoning profile: {profile}",
                provider="platform",
                provider_code="E_REASONING_PROFILE",
                details={"profile": profile, "allowed": ["EL", "OWL2EL"]},
            )
        abox_graphs = payload.get("aboxGraphs")
        if abox_graphs is not None and (
            not isinstance(abox_graphs, list)
            or not abox_graphs
            or not all(isinstance(item, str) and item.startswith("urn:platform:") for item in abox_graphs)
        ):
            raise PortError(
                code="InvalidArgument",
                message="aboxGraphs must be a non-empty list of urn:platform: IRIs",
                provider="platform",
                provider_code="E_REASONING_ABOX_GRAPHS",
            )
        return runtime.reasoning.materialize(
            profile=profile, force=bool(payload.get("force", False)),
            abox_graphs=abox_graphs,
        )

    @app.get("/reasoning/status")
    def reasoning_status() -> dict[str, Any]:
        return runtime.reasoning.status()

    @app.post("/validation/run")
    def run_validation(body: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
        target = (body or {}).get("graph", "abox")
        if not isinstance(target, str):
            raise PortError(
                code="InvalidArgument",
                message="validation graph must be a string",
                provider="platform",
                provider_code="E_VALIDATE_TARGET",
            )
        return runtime.reasoning.validate(target)

    @app.get("/validation/shapes")
    def validation_shapes() -> dict[str, Any]:
        try:
            return {
                "shapesDir": runtime.config.reasoning.shapes_dir,
                "files": [p.name for p in runtime.validator.shapes()],
                "shapesVersion": runtime.validator.shapes_version(),
                # G-03: which namespace, which shape set, which version.
                "namespaces": runtime.validator.registries(),
            }
        except OSError as exc:
            raise PortError(
                code="Unavailable",
                message=f"cannot read shapes directory: {exc}",
                provider="pyshacl",
                provider_code="E_SHACL_SHAPES_MISSING",
            ) from exc

    @app.post("/context/resolve")
    def context_resolve(body: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
        return runtime.context.resolve(body or {})

    # ---- S7 Web UI views (read-only; no framework, no build chain) -------

    @app.get("/ui/api/overview")
    def ui_overview() -> dict[str, Any]:
        return webui.overview(runtime)

    @app.get("/ui/api/ontology")
    def ui_ontology() -> dict[str, Any]:
        return webui.ontology(runtime)

    @app.get("/ui/api/entities")
    def ui_entities(
        q: str = Query(default="", max_length=200),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> dict[str, Any]:
        return webui.entities(runtime, q, limit=limit)

    @app.get("/ui/api/neighbors")
    def ui_neighbors(
        iri: str = Query(min_length=1, max_length=2000),
        limit: int = Query(default=50, ge=1, le=200),
    ) -> dict[str, Any]:
        return webui.neighbors(runtime, iri, limit=limit)

    @app.get("/ui/api/candidates")
    def ui_candidates(
        state: str | None = Query(default="pending"),
        limit: int = Query(default=50, ge=1, le=200),
    ) -> dict[str, Any]:
        return webui.candidates_with_evidence(runtime, state=state, limit=limit)

    @app.get("/ui/api/search")
    def ui_search(
        q: str = Query(min_length=1, max_length=2000),
        topK: int = Query(default=10, ge=1, le=50),
        tokenBudget: int = Query(default=2048, ge=32, le=8192),
        strategy: str = Query(default="hybrid"),
    ) -> dict[str, Any]:
        if strategy not in ("hybrid", "vector", "lexical"):
            raise PortError(
                code="InvalidArgument",
                message=f"unsupported strategy: {strategy}",
                provider="platform",
                provider_code="E_CONTEXT_STRATEGY",
                details={"strategy": strategy},
            )
        return runtime.context.resolve(
            {"query": q, "topK": topK, "tokenBudget": tokenBudget, "strategy": strategy}
        )

    @app.get("/")
    def ui_root() -> Any:
        if (WEB_DIR / "index.html").is_file():
            return RedirectResponse(url="/ui/")
        return {"status": "ok", "ui": "not bundled", "webDir": str(WEB_DIR)}

    if WEB_DIR.is_dir():
        app.mount("/ui", StaticFiles(directory=str(WEB_DIR), html=True), name="ui")

    @app.get("/status")
    def status() -> dict[str, Any]:
        disk: dict[str, Any] = {}
        try:
            usage = shutil.disk_usage(runtime.config.storage.root)
            disk = {
                "free_pct": round((usage.free / usage.total) * 100, 2) if usage.total else 0,
                "free_bytes": usage.free,
                "total_bytes": usage.total,
            }
        except OSError as exc:
            disk = {"error": str(exc)}

        counts: dict[str, Any] = {}
        try:
            counts["blobs"] = runtime.metadata.count_blobs()
            counts["refs"] = runtime.metadata.count_refs()
        except Exception as exc:
            counts["error"] = str(exc)

        ontology: dict[str, Any] = {}
        try:
            pointer = runtime.ontology.current()
            versions = runtime.ontology.list_versions()
            ontology = {
                "pointer": pointer,
                "versions": len(versions),
                "statuses": {v["id"]: v["status"] for v in versions},
            }
        except Exception as exc:
            ontology = {"error": str(exc)}

        triples: int | None = None
        try:
            result = runtime.graph.query(
                "SELECT (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } }"
            )
            if result["bindings"]:
                triples = int(result["bindings"][0]["values"]["n"]["value"])
        except PortError:
            triples = None

        documents_counts: dict[str, Any] = {}
        try:
            documents_counts = runtime.documents.counts()
        except Exception as exc:
            documents_counts = {"error": str(exc)}

        search_counts: dict[str, Any] = {}
        try:
            search_counts = runtime.search.counts()
        except Exception as exc:
            search_counts = {"error": str(exc)}

        extraction_counts: dict[str, Any] = {}
        try:
            extraction_counts = runtime.extraction.counts()
        except Exception as exc:
            extraction_counts = {"error": str(exc)}

        reasoning_status: dict[str, Any] = {}
        try:
            reasoning_status = runtime.reasoning.status()
        except Exception as exc:
            reasoning_status = {"error": str(exc)}

        return {
            "status": "ok",
            "version": __version__,
            "slice": "S13",
            "mode": runtime.config.mode,
            "runtime_mode": runtime.config.runtime.mode,
            "config_version": runtime.config.config_version,
            "config_file": str(runtime.bundle.path),
            "providers": {
                "metadata": runtime.metadata.manifest().__dict__,
                "graph": runtime.graph.manifest().__dict__,
                "object": runtime.objects.manifest().__dict__,
                "ontology": runtime.ontology.manifest().__dict__,
                "parser": runtime.parser.manifest().__dict__,
                "documents": runtime.documents.manifest().__dict__,
                "embedding": runtime.embedding.manifest().__dict__,
                "vectors": runtime.vectors.manifest().__dict__,
                "search_index": runtime.search_index.manifest().__dict__,
                "search": runtime.search.manifest().__dict__,
                "llm": runtime.llm.manifest().__dict__,
                "extraction": runtime.extraction.manifest().__dict__,
                "reasoner": runtime.reasoner.manifest().__dict__,
                "consistency_reasoner": (
                    runtime.consistency_reasoner.manifest().__dict__
                    if runtime.consistency_reasoner is not None
                    else None
                ),
                "validation": runtime.validator.manifest().__dict__ if hasattr(runtime.validator, "manifest") else {},
                "reasoning": runtime.reasoning.manifest().__dict__,
                "context": runtime.context.manifest().__dict__,
                "answerability": runtime.answerable.manifest().__dict__,
                "facts": runtime.facts.manifest().__dict__,
                "secrets": runtime.secrets.manifest().__dict__,
            },
            "not_implemented": {
                name: port.manifest().notes for name, port in runtime.placeholders.items()
            },
            "degraded": runtime.degraded,
            "storage": {"disk": disk, "counts": counts},
            "graph": {"triples": triples},
            "documents": documents_counts,
            "search": search_counts,
            "extraction": extraction_counts,
            "reasoning": reasoning_status,
            "self_check": [item.to_dict() for item in checks],
            "notes": [
                "no auth, no metrics/tracing, no job queue or event bus",
                "OCR is disabled; scanned PDFs are returned as degraded with NO_OCR_ENABLED",
                "embedding unavailable -> hybrid search returns lexical results with degraded=true",
                "extraction candidates are approval-gated: nothing is written to the graph before approval",
                "llm is OpenAI-compatible and optional: auto mode degrades to rules when unconfigured",
                "reasoning materializes into a separate graph; source graphs are never overwritten",
                "SHACL without shapes is an explicit Unsupported error, never a silent pass",
            ],
        }

    return app
