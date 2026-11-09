"""Startup self-check: the S0 subset of _design/03 section 16.1."""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from .assembly import Runtime
from .errors import (
    EXIT_CONFIG,
    EXIT_IO,
    EXIT_UNAVAILABLE,
    PlatformError,
    PortError,
    port_error_exit_code,
)

log = logging.getLogger(__name__)


@dataclass
class CheckResult:
    stage: str
    status: str
    detail: str
    code: str | None = None

    def to_dict(self) -> dict:
        return {"stage": self.stage, "status": self.status, "detail": self.detail, "code": self.code}


def run_self_check(runtime: Runtime, retry_seconds: float = 60.0) -> list[CheckResult]:
    checks: list[CheckResult] = []
    checks.append(
        CheckResult(
            stage="config",
            status="ok",
            detail=f"config_version={runtime.config.config_version} file={runtime.bundle.path}",
        )
    )

    _check_io(runtime, checks)
    _check_db(runtime, retry_seconds, checks)
    _check_graph(runtime, retry_seconds, checks)
    _check_storage(runtime, checks)
    _check_parser(runtime, checks)
    _check_embedding_identity(runtime, checks)
    _check_capabilities(runtime, checks)

    summary = {
        "event": "self_check",
        "result": "ok",
        "checks": [item.to_dict() for item in checks],
        "degraded": runtime.degraded,
        "runtime_mode": runtime.config.runtime.mode,
    }
    log.info("self-check passed", extra={"event": summary})
    return checks


def _check_io(runtime: Runtime, checks: list[CheckResult]) -> None:
    cfg = runtime.config
    root = Path(cfg.storage.root)
    tmp = Path(cfg.storage.tmp_dir)
    data_dir = Path(cfg.data_dir)
    try:
        for path in (data_dir, root, root / "blobs", tmp):
            path.mkdir(parents=True, exist_ok=True)
        probe = tmp / f".selfcheck-{uuid.uuid4().hex}"
        probe.write_bytes(b"io-probe")
        probe.unlink()
    except OSError as exc:
        raise PlatformError(
            code="E_IO_PERM",
            detail=f"data/tmp directory is not writable: {exc}",
            stage="io",
            key="storage.root",
            hint="check volume permissions and that ./data is mounted",
            exit_code=EXIT_IO,
        ) from exc

    root_dev = os.stat(root).st_dev
    tmp_dev = os.stat(tmp).st_dev
    if root_dev != tmp_dev:
        raise PlatformError(
            code="E_IO_VOLUME",
            detail=f"storage.root (dev={root_dev}) and storage.tmp_dir (dev={tmp_dev}) are on different volumes",
            stage="io",
            key="storage.tmp_dir",
            hint="put tmp_dir under the same filesystem as root so rename is atomic",
            exit_code=EXIT_IO,
        )

    usage = shutil.disk_usage(root)
    free_pct = (usage.free / usage.total) * 100 if usage.total else 0
    if free_pct < cfg.storage.min_free_pct:
        raise PlatformError(
            code="E_DISK_LOW",
            detail=f"disk free {free_pct:.1f}% < storage.min_free_pct={cfg.storage.min_free_pct}%",
            stage="io",
            key="storage.min_free_pct",
            hint="free disk space or lower the threshold",
            exit_code=EXIT_IO,
        )

    checks.append(
        CheckResult(
            stage="io",
            status="ok",
            detail=f"root={root} tmp={tmp} same_volume=true free_pct={free_pct:.1f}",
        )
    )


def _check_db(runtime: Runtime, retry_seconds: float, checks: list[CheckResult]) -> None:
    try:
        runtime.metadata.open(retry_seconds=retry_seconds)
    except PortError as exc:
        raise PlatformError(
            code=exc.provider_code or "E_DB_UNAVAILABLE",
            detail=exc.message,
            stage="db",
            key="database.url",
            provider=exc.provider,
            hint="ensure the postgres container is healthy; check database.url",
            exit_code=port_error_exit_code(exc),
        ) from exc
    try:
        migration = runtime.metadata.migrate()
    except Exception as exc:
        # Q7-a: a failed schema migration is a deployment/config problem (78),
        # never a transient "try again" (69).
        raise PlatformError(
            code="E_DB_MIGRATION_FAILED",
            detail=f"database migration failed: {exc}",
            stage="db",
            key="database.url",
            provider="postgres",
            hint="inspect postgres logs; verify the role can create schema and the migration set is complete",
            exit_code=EXIT_CONFIG,
        ) from exc
    try:
        runtime.metadata.health()
        shapes_loaded = runtime.shapes.load_directory(
            runtime.config.reasoning.shapes_dir
        )
    except PlatformError:
        raise
    except Exception as exc:
        raise PlatformError(
            code="E_DB_UNAVAILABLE",
            detail=f"database health/shapes check failed: {exc}",
            stage="db",
            key="database.url",
            provider="postgres",
            hint="inspect postgres logs; verify the role can create schema",
            exit_code=EXIT_UNAVAILABLE,
        ) from exc

    checks.append(
        CheckResult(
            stage="db",
            status="ok",
            detail=f"postgres ok schema_version={migration['to']}",
        )
    )


def _check_graph(runtime: Runtime, retry_seconds: float, checks: list[CheckResult]) -> None:
    deadline = time.monotonic() + max(retry_seconds, 0)
    last: PortError | None = None
    while True:
        try:
            runtime.graph.probe()
            checks.append(CheckResult(stage="graph", status="ok", detail="sparql ask+write+read+drop ok"))
            return
        except PortError as exc:
            last = exc
            if exc.code not in ("Unavailable", "DeadlineExceeded", "Aborted") or time.monotonic() >= deadline:
                break
            time.sleep(1.0)
    assert last is not None
    raise PlatformError(
        code=last.provider_code or "E_GRAPH_UNAVAILABLE",
        detail=last.message,
        stage="graph",
        key="graph.endpoint",
        provider=last.provider,
        hint="ensure the oxigraph container is running and graph.endpoint is reachable",
        exit_code=port_error_exit_code(last),
    )


def _storage_roundtrip(runtime: Runtime, label: str, data: bytes, expected_tier: str) -> dict:
    objects = runtime.objects
    bucket = "selfcheck"
    key = f"{label}-{uuid.uuid4().hex}"
    ref = objects.put(bucket, key, data, "application/octet-stream", {"probe": "s0"})
    if ref["tier"] != expected_tier:
        raise PortError(
            code="Internal",
            message=f"{label}: expected tier={expected_tier}, got {ref['tier']}",
            provider="layered",
            provider_code="E_STORAGE_TIER",
        )
    meta = objects.head(bucket, key)
    body, meta2 = objects.get(bucket, key)
    digest = hashlib.sha256(body).hexdigest()
    if digest != meta2["ref"]["checksum"]["value"] or len(body) != len(data):
        raise PortError(
            code="DataLoss",
            message=f"{label}: sha256/size mismatch after CAS read",
            provider="layered",
            provider_code="E_STORAGE_HASH_MISMATCH",
        )
    objects.delete(bucket, key)
    try:
        objects.head(bucket, key)
    except PortError as exc:
        if exc.code != "NotFound":
            raise
    else:
        raise PortError(
            code="Internal",
            message=f"{label}: object still visible after delete",
            provider="layered",
            provider_code="E_STORAGE_DELETE",
        )
    return {"key": key, "size": meta["ref"]["size"], "tier": ref["tier"]}


def _check_storage(runtime: Runtime, checks: list[CheckResult]) -> None:
    cfg = runtime.config
    small = b"S" * 4096
    large = b"0123456789abcdef" * (11 * 1024 * 1024 // 16)
    try:
        small_tier = "pg" if cfg.storage.small_object_provider == "pg" else "fs"
        _storage_roundtrip(runtime, "pg-or-small", small, small_tier)
        _storage_roundtrip(runtime, "large", large, "fs")
    except PortError as exc:
        raise PlatformError(
            code=exc.provider_code or "E_STORAGE_UNAVAILABLE",
            detail=exc.message,
            stage="storage",
            key="storage.root",
            provider=exc.provider,
            hint="check ./data mount, disk space and database availability",
            exit_code=port_error_exit_code(exc),
        ) from exc
    checks.append(
        CheckResult(
            stage="storage",
            status="ok",
            detail=(
                f"small_tier={cfg.storage.small_object_provider} "
                f"large_tier={cfg.storage.large_object_provider} sha256=ok"
            ),
        )
    )


def _check_parser(runtime: Runtime, checks: list[CheckResult]) -> None:
    """S2: parser engines must be importable in the runtime image."""
    try:
        from importlib import metadata

        import markitdown  # noqa: F401
        import pdfplumber  # noqa: F401
        import pypdfium2  # noqa: F401

        versions = []
        for package in ("pypdfium2", "pdfplumber", "markitdown"):
            try:
                versions.append(f"{package}={metadata.version(package)}")
            except metadata.PackageNotFoundError:
                versions.append(f"{package}=unknown")
    except ImportError as exc:
        raise PlatformError(
            code="E_PARSER_MISSING",
            detail=f"document parser dependency is missing: {exc}",
            stage="parser",
            key="documents.parser",
            hint="rebuild the image from requirements.txt (pypdfium2/pdfplumber/markitdown)",
            exit_code=EXIT_CONFIG,
        ) from exc
    checks.append(
        CheckResult(
            stage="parser",
            status="ok",
            detail=f"{' '.join(versions)} ocr=false tables={runtime.config.documents.extract_tables}",
        )
    )


def _model_key(value: str) -> str:
    text = (value or "").strip().rstrip("/")
    return text.rsplit("/", 1)[-1].lower() if text else ""


def _check_embedding_identity(runtime: Runtime, checks: list[CheckResult]) -> None:
    """Q7-b: the served model and vector width must match the config.

    A mismatch would silently mix vector spaces, so it blocks startup (78) with
    E_EMBED_MODEL_MISMATCH. An unreachable endpoint stays 'degraded' - that is
    an availability problem, not an identity problem.
    """
    cfg = runtime.config.embedding
    if cfg.provider in ("disabled", "fake"):
        checks.append(
            CheckResult(
                stage="embedding",
                status="skipped",
                detail=f"provider={cfg.provider} (no external model identity)",
            )
        )
        return
    if not runtime.embedding.available():
        checks.append(
            CheckResult(
                stage="embedding",
                status="degraded",
                detail="embedding endpoint unreachable; model/dimension identity not verified",
                code="E_EMBED_UNAVAILABLE",
            )
        )
        return
    try:
        info = runtime.embedding.service_info()
    except PortError as exc:
        checks.append(
            CheckResult(
                stage="embedding",
                status="degraded",
                detail=f"identity probe failed: {exc.message}",
                code=exc.provider_code or "E_EMBED_UNAVAILABLE",
            )
        )
        return

    reported = str(info.get("model") or "")
    expected = runtime.embedding.model_name()
    if reported and _model_key(reported) != _model_key(expected):
        raise PlatformError(
            code="E_EMBED_MODEL_MISMATCH",
            detail=f"embedding model mismatch: config={expected} service={reported}",
            stage="embedding",
            key="embedding.model",
            provider=cfg.provider,
            hint=(
                "align embedding.model/embedding.endpoint with the served model, "
                "or re-embed the corpus; refusing to mix vector spaces"
            ),
            exit_code=EXIT_CONFIG,
        )

    try:
        vectors = runtime.embedding.embed(["platform embedding identity probe"])
    except PortError as exc:
        if exc.provider_code == "E_EMBED_DIM_MISMATCH":
            raise PlatformError(
                code="E_EMBED_MODEL_MISMATCH",
                detail=exc.message,
                stage="embedding",
                key="embedding.dimensions",
                provider=cfg.provider,
                hint="align embedding.dimensions with the served model or re-embed the corpus",
                exit_code=EXIT_CONFIG,
            ) from exc
        checks.append(
            CheckResult(
                stage="embedding",
                status="degraded",
                detail=f"dimension probe failed: {exc.message}",
                code=exc.provider_code or "E_EMBED_UNAVAILABLE",
            )
        )
        return

    got = len(vectors[0]) if vectors else 0
    if got != runtime.embedding.dimensions():
        raise PlatformError(
            code="E_EMBED_MODEL_MISMATCH",
            detail=(
                f"embedding dimension mismatch: service={got} "
                f"config={runtime.embedding.dimensions()}"
            ),
            stage="embedding",
            key="embedding.dimensions",
            provider=cfg.provider,
            hint="align embedding.dimensions with the served model or re-embed the corpus",
            exit_code=EXIT_CONFIG,
        )
    checks.append(
        CheckResult(
            stage="embedding",
            status="ok",
            detail=f"model={reported} dimensions={got}",
        )
    )


def _check_capabilities(runtime: Runtime, checks: list[CheckResult]) -> None:
    available: set[str] = set()
    for adapter in (runtime.metadata, runtime.graph, runtime.objects):
        available.update(adapter.manifest().capabilities)
    available.update(runtime.parser.manifest().capabilities)
    available.update(runtime.documents.manifest().capabilities)
    available.update(runtime.embedding.manifest().capabilities)
    available.update(runtime.vectors.manifest().capabilities)
    available.update(runtime.search_index.manifest().capabilities)
    available.update(runtime.search.manifest().capabilities)
    available.update(runtime.llm.manifest().capabilities)
    available.update(runtime.extraction.manifest().capabilities)
    available.update(runtime.reasoner.manifest().capabilities)
    available.update(runtime.reasoning.manifest().capabilities)
    available.update(runtime.context.manifest().capabilities)
    available.update(runtime.answerable.manifest().capabilities)

    requirements: dict[str, list[str]] = runtime.config.requirements
    deny = set(runtime.config.degradation.get("deny", []))
    missing: list[str] = []
    for task, caps in requirements.items():
        if any(cap in available for cap in caps):
            continue
        if task in deny:
            missing.append(f"{task}<-{caps}")
    if missing:
        raise PlatformError(
            code="E_CAP_MISSING",
            detail="required capabilities are missing: " + "; ".join(missing),
            stage="capability",
            key="requirements",
            hint="enable the provider or move the task to degradation.allow",
            exit_code=EXIT_CONFIG,
        )
    checks.append(
        CheckResult(stage="capability", status="ok", detail=f"{len(requirements)} requirements satisfied")
    )
