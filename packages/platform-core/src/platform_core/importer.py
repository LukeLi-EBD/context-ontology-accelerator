"""S13 bulk import: scan a directory, ingest/chunk/embed each file, resume safely.

Boundary (D18): orchestration only. Hashing lives here only to dedupe scan
entries; parsing/chunking stays in DocumentService, embedding stays in
SearchService. Nothing about parse or retrieval semantics changes.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import logging
import os
import threading
import time
import uuid
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .assembly import Runtime
from .errors import PortError

log = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = (".pdf", ".docx", ".txt", ".md")
# Platform-owned subdirectories under storage.root: never import the platform's
# own blobs/tmp/model files by accident.
MANAGED_SUBDIRS = {
    "blobs", "tmp", "backups", "exports", "ontology", "owl", "shapes", "jobs", "models",
}
HASH_BLOCK = 1024 * 1024


@dataclass
class ScanEntry:
    rel_path: str
    path: Path
    size_bytes: int
    mtime_ns: int
    sha256: str | None = None


@dataclass
class ScanProblem:
    rel_path: str
    size_bytes: int
    mtime_ns: int
    sha256: str | None
    code: str
    message: str


@dataclass
class ScanResult:
    entries: list[ScanEntry] = field(default_factory=list)
    problems: list[ScanProblem] = field(default_factory=list)
    hidden: int = 0
    unsupported: int = 0
    total_seen: int = 0


def _ensure_storage_dirs(runtime: Runtime) -> None:
    """Create the storage dirs `serve` makes in its IO self-check.

    The import CLI deliberately skips the self-check (it only needs PG + CAS),
    so on a fresh host every file used to fail with E_IMPORT_UNEXPECTED: the
    staging write ``tmp_dir/ingest-*.part`` raised FileNotFoundError. Creating
    the same four dirs here keeps the CLI usable before the first `serve` and
    turns a permission problem into one clear error instead of N item failures.
    """
    cfg = runtime.config
    for path in (
        Path(cfg.data_dir),
        Path(cfg.storage.root),
        Path(cfg.storage.root) / "blobs",
        Path(cfg.storage.tmp_dir),
    ):
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise PortError(
                code="Internal",
                message=f"import storage directory is not writable: {path}: {exc}",
                provider="platform",
                provider_code="E_IO_PERM",
                details={"path": str(path)},
            ) from exc


def _resolve_root(directory: str) -> Path:
    root = Path(directory).expanduser()
    if not root.is_dir():
        raise PortError(
            code="InvalidArgument",
            message=f"import directory not found: {directory}",
            provider="platform",
            provider_code="E_IMPORT_NOT_DIR",
            details={"directory": str(directory)},
        )
    return root.resolve()


def _is_hidden(name: str) -> bool:
    return name.startswith(".")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(HASH_BLOCK)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _prune_dirs(directory: str, names: list[str], data_root: Path, root: Path) -> list[str]:
    keep: list[str] = []
    here = Path(directory).resolve()
    for name in names:
        child = here / name
        if _is_hidden(name) or child.is_symlink():
            continue
        if child.resolve() == data_root and child.resolve() != root:
            continue
        if here == data_root and name in MANAGED_SUBDIRS:
            continue
        keep.append(name)
    return keep


def scan_directory(
    runtime: Runtime, root: Path, cache: dict[str, dict[str, Any]] | None = None
) -> ScanResult:
    """Walk `root` with the S13 rules and hash each eligible file.

    `cache` maps rel_path -> prior import_item row; a matching size+mtime reuses
    the stored sha256 so re-scans do not re-read unchanged data.
    """
    data_root = Path(runtime.config.storage.root).resolve()
    max_bytes = runtime.config.documents.max_upload_bytes
    result = ScanResult()
    cache = cache or {}
    for directory, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = _prune_dirs(directory, dirnames, data_root, root)
        for name in filenames:
            path = Path(directory) / name
            rel = str(path.relative_to(root)).replace("\\", "/")
            result.total_seen += 1
            if _is_hidden(name) or path.is_symlink():
                result.hidden += 1
                continue
            if path.suffix.lower() not in ALLOWED_EXTENSIONS:
                result.unsupported += 1
                continue
            try:
                stat = path.stat()
            except OSError as exc:
                result.problems.append(
                    ScanProblem(rel, 0, 0, None, "E_IMPORT_UNREADABLE", str(exc))
                )
                continue
            size = int(stat.st_size)
            mtime_ns = int(stat.st_mtime_ns)
            if size == 0:
                result.problems.append(
                    ScanProblem(rel, 0, mtime_ns, None, "E_DOC_EMPTY", "document is empty (0 bytes)")
                )
                continue
            if size > max_bytes:
                result.problems.append(
                    ScanProblem(
                        rel, size, mtime_ns, None, "E_DOC_TOO_LARGE",
                        f"document size {size} exceeds documents.max_upload_bytes={max_bytes}",
                    )
                )
                continue
            cached = cache.get(rel)
            sha = None
            if cached and cached.get("sha256") and int(cached["size_bytes"]) == size:
                if cached.get("mtime_ns") is not None and int(cached["mtime_ns"]) == mtime_ns:
                    sha = str(cached["sha256"])
            if sha is None:
                try:
                    sha = _sha256(path)
                except OSError as exc:
                    result.problems.append(
                        ScanProblem(rel, size, mtime_ns, None, "E_IMPORT_UNREADABLE", str(exc))
                    )
                    continue
            result.entries.append(ScanEntry(rel, path, size, mtime_ns, sha))
    return result


def _group_entries(entries: Iterable[ScanEntry]) -> dict[str, list[ScanEntry]]:
    groups: dict[str, list[ScanEntry]] = {}
    for entry in entries:
        if entry.sha256:
            groups.setdefault(entry.sha256, []).append(entry)
    for rows in groups.values():
        rows.sort(key=lambda item: item.rel_path)
    return groups


def _embedded_documents(runtime: Runtime, shas: Iterable[str]) -> set[str]:
    """Documents whose every chunk has a vector in the active model partition.

    A row in `platform.document` only proves the file was parsed. Uploads can
    stop before embedding, and an embed failure leaves the document row behind,
    so treating "document exists" as "indexed" would report success without
    searchable vectors. Require at least one chunk and no un-embedded chunk.
    """
    unique = [sha for sha in dict.fromkeys(shas) if sha]
    if not unique:
        return set()
    model = str(runtime.vectors.pointer()["model"])
    rows = runtime.metadata.query(
        """
        SELECT d.document_id
          FROM platform.document d
         WHERE d.document_id = ANY(%s)
           AND EXISTS (
                 SELECT 1 FROM platform.document_chunk c
                  WHERE c.document_id = d.document_id)
           AND NOT EXISTS (
                 SELECT 1 FROM platform.document_chunk c
                  WHERE c.document_id = d.document_id
                    AND NOT EXISTS (
                          SELECT 1 FROM platform.chunk_embedding e
                           WHERE e.chunk_id = c.chunk_id AND e.model = %s))
        """,
        (unique, model),
    )
    return {str(row["document_id"]) for row in rows}


def _coerce_namespace_id(value: str | uuid.UUID) -> uuid.UUID:
    """Parse the caller-supplied namespace; never invent a default."""
    try:
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise PortError(
            code="InvalidArgument",
            message=f"namespace id is not a UUID: {value}",
            provider="platform",
            provider_code="E_NAMESPACE_ID_INVALID",
            details={"namespaceId": str(value)},
        ) from exc


def _batch_items(runtime: Runtime, batch_id: uuid.UUID) -> dict[str, dict[str, Any]]:
    rows = runtime.metadata.query(
        "SELECT rel_path, size_bytes, mtime_ns, sha256, status FROM platform.import_item "
        "WHERE batch_id = %s",
        (batch_id,),
    )
    return {str(row["rel_path"]): row for row in rows}


def _get_or_create_batch(
    runtime: Runtime, root: Path, options: dict[str, Any], namespace_id: uuid.UUID
) -> uuid.UUID:
    from psycopg.types.json import Jsonb

    previous = runtime.metadata.query(
        "SELECT batch_id, namespace_id FROM platform.import_batch WHERE root_path = %s",
        (str(root),),
    )
    if previous and previous[0]["namespace_id"] is not None:
        current = str(previous[0]["namespace_id"])
        # A directory belongs to the namespace that claimed it. Re-pointing an
        # existing batch would silently move already-imported rows across a
        # namespace boundary, so refuse instead of guessing.
        if current != str(namespace_id):
            raise PortError(
                code="Conflict",
                message=(
                    f"import batch for {root} belongs to namespace {current}, "
                    f"not {namespace_id}"
                ),
                provider="platform",
                provider_code="E_IMPORT_NAMESPACE_MISMATCH",
                details={
                    "root": str(root),
                    "batchId": str(previous[0]["batch_id"]),
                    "namespaceId": current,
                    "requestedNamespaceId": str(namespace_id),
                },
            )
    rows = runtime.metadata.query(
        """
        INSERT INTO platform.import_batch (batch_id, root_path, namespace_id, status, options)
        VALUES (gen_random_uuid(), %s, %s, 'running', %s)
        ON CONFLICT (root_path) DO UPDATE
           SET status = 'running',
               namespace_id = COALESCE(platform.import_batch.namespace_id,
                                       EXCLUDED.namespace_id),
               options = EXCLUDED.options,
               updated_at = now()
        RETURNING batch_id
        """,
        (str(root), namespace_id, Jsonb(options)),
    )
    return rows[0]["batch_id"]


def _find_batch(runtime: Runtime, root: Path) -> uuid.UUID | None:
    rows = runtime.metadata.query(
        "SELECT batch_id FROM platform.import_batch WHERE root_path = %s", (str(root),)
    )
    return rows[0]["batch_id"] if rows else None


def _start_run(
    runtime: Runtime,
    batch_id: uuid.UUID,
    namespace_id: uuid.UUID,
    options: dict[str, Any],
) -> uuid.UUID:
    """Open one ledger row for this invocation.

    The batch advisory lock is already held, so any `running` row for the same
    batch belongs to a process that died without finishing: close it as
    interrupted instead of leaving a phantom run forever.
    """
    from psycopg.types.json import Jsonb

    runtime.metadata.execute(
        """
        UPDATE platform.import_run
           SET status = 'interrupted',
               finished_at = now(),
               error_code = COALESCE(error_code, 'E_RUN_ABANDONED'),
               error_message = COALESCE(error_message, 'process exited without finishing')
         WHERE batch_id = %s AND status = 'running'
        """,
        (batch_id,),
    )
    rows = runtime.metadata.query(
        """
        INSERT INTO platform.import_run (batch_id, namespace_id, status, options)
        VALUES (%s, %s, 'running', %s)
        RETURNING run_id
        """,
        (batch_id, namespace_id, Jsonb(options)),
    )
    return rows[0]["run_id"]


def _finish_run(
    runtime: Runtime,
    run_id: uuid.UUID,
    batch_id: uuid.UUID,
    *,
    status: str,
    counters: dict[str, Any],
    exit_code: int | None,
    error: BaseException | None = None,
) -> None:
    from psycopg.types.json import Jsonb

    code = message = None
    if error is not None:
        code = (
            getattr(error, "provider_code", None)
            or getattr(error, "code", None)
            or type(error).__name__
        )
        message = getattr(error, "message", None) or str(error)
    # The ledger row and the batch state close together: a failed run must not
    # leave the batch showing "running", or the page keeps reporting a live
    # import that no longer exists and no stale pass can ever fire on it.
    # `lastError` is written into options so the batch carries the reason; the
    # next invocation rewrites options from scratch and clears it.
    with runtime.metadata.tx() as tx:
        tx.execute(
            """
            UPDATE platform.import_run
               SET status = %s,
                   finished_at = now(),
                   exit_code = %s,
                   counters = %s,
                   error_code = %s,
                   error_message = %s
             WHERE run_id = %s
            """,
            (status, exit_code, Jsonb(counters), code, message, run_id),
        )
        if status == "failed":
            tx.execute(
                """
                UPDATE platform.import_batch
                   SET status = 'interrupted',
                       finished_at = now(),
                       updated_at = now(),
                       options = options || jsonb_build_object(
                           'lastError', jsonb_build_object(
                               'code', %s::text,
                               'message', %s::text,
                               'at', now()))
                 WHERE batch_id = %s AND status = 'running'
                """,
                (code, (message or "")[:2000], batch_id),
            )


def _upsert_items(
    runtime: Runtime, batch_id: uuid.UUID, scan: ScanResult, indexed_shas: set[str]
) -> None:
    """Persist scan results without clobbering unchanged terminal rows."""
    with runtime.metadata.tx() as tx:
        for entry in scan.entries:
            done = entry.sha256 in indexed_shas
            tx.execute(
                """
                INSERT INTO platform.import_item
                    (batch_id, rel_path, size_bytes, mtime_ns, sha256, status,
                     document_id, deduplicated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (batch_id, rel_path) DO UPDATE
                   SET size_bytes = EXCLUDED.size_bytes,
                       mtime_ns = EXCLUDED.mtime_ns,
                       sha256 = EXCLUDED.sha256,
                       status = EXCLUDED.status,
                       document_id = EXCLUDED.document_id,
                       deduplicated = EXCLUDED.deduplicated,
                       degraded = false,
                       failure_code = NULL,
                       failure_message = NULL,
                       updated_at = now()
                 WHERE platform.import_item.size_bytes <> EXCLUDED.size_bytes
                    OR platform.import_item.mtime_ns IS DISTINCT FROM EXCLUDED.mtime_ns
                """,
                (
                    batch_id, entry.rel_path, entry.size_bytes, entry.mtime_ns,
                    entry.sha256, "indexed" if done else "pending",
                    entry.sha256 if done else None, done,
                ),
            )
        for problem in scan.problems:
            # Scan problems are authoritative: they always end as failed, even
            # when --retry-failed reset the row to pending beforehand.
            tx.execute(
                """
                INSERT INTO platform.import_item
                    (batch_id, rel_path, size_bytes, mtime_ns, sha256, status,
                     failure_code, failure_message)
                VALUES (%s, %s, %s, %s, %s, 'failed', %s, %s)
                ON CONFLICT (batch_id, rel_path) DO UPDATE
                   SET size_bytes = EXCLUDED.size_bytes,
                       mtime_ns = EXCLUDED.mtime_ns,
                       status = 'failed',
                       document_id = NULL,
                       deduplicated = false,
                       degraded = false,
                       failure_code = EXCLUDED.failure_code,
                       failure_message = EXCLUDED.failure_message,
                       updated_at = now()
                """,
                (
                    batch_id, problem.rel_path, problem.size_bytes, problem.mtime_ns,
                    problem.sha256, problem.code, problem.message,
                ),
            )


def dry_run(runtime: Runtime, directory: str) -> dict[str, Any]:
    root = _resolve_root(directory)
    batch_id = _find_batch(runtime, root)
    cache = _batch_items(runtime, batch_id) if batch_id else {}
    scan = scan_directory(runtime, root, cache)
    groups = _group_entries(scan.entries)
    existing = _embedded_documents(runtime, groups.keys())
    to_import = {sha: rows for sha, rows in groups.items() if sha not in existing}
    duplicate_within = sum(len(rows) - 1 for rows in groups.values())
    duplicate_existing = sum(len(rows) for sha, rows in groups.items() if sha in existing)
    breakdown = {
        "duplicate": duplicate_within + duplicate_existing,
        "unsupported": scan.unsupported,
        "empty": sum(1 for item in scan.problems if item.code == "E_DOC_EMPTY"),
        "tooLarge": sum(1 for item in scan.problems if item.code == "E_DOC_TOO_LARGE"),
        "unreadable": sum(1 for item in scan.problems if item.code == "E_IMPORT_UNREADABLE"),
        "hidden": scan.hidden,
    }
    return {
        "dryRun": True,
        "batchId": str(batch_id) if batch_id else None,
        "root": str(root),
        "totalFiles": scan.total_seen,
        "toImport": len(to_import),
        "toImportFiles": sum(len(rows) for rows in to_import.values()),
        "bytesToImport": sum(entry.size_bytes for rows in to_import.values() for entry in rows),
        "skipped": sum(breakdown.values()),
        "skipBreakdown": breakdown,
        "alreadyIndexed": len(existing),
        "willFail": len(scan.problems),
        "maxUploadBytes": runtime.config.documents.max_upload_bytes,
    }


def _failure(exc: BaseException) -> tuple[str, str]:
    if isinstance(exc, PortError):
        return str(exc.provider_code or exc.code), str(exc.message)[:2000]
    return "E_IMPORT_UNEXPECTED", f"{type(exc).__name__}: {exc}"[:2000]


def _peak_rss_mb() -> float:
    try:
        for line in Path("/proc/self/status").read_text(encoding="ascii").splitlines():
            if line.startswith("VmHWM:"):
                return round(int(line.split()[1]) / 1024.0, 1)
    except (OSError, ValueError, IndexError):
        pass
    return 0.0


class _Group:
    __slots__ = ("sha", "rows", "path", "size_bytes", "degraded")

    def __init__(self, sha: str, rows: list[dict[str, Any]], path: Path, size: int) -> None:
        self.sha = sha
        self.rows = rows
        self.path = path
        self.size_bytes = size
        self.degraded = False

    @property
    def rel_paths(self) -> list[str]:
        return [str(row["rel_path"]) for row in self.rows]

    @property
    def primary(self) -> dict[str, Any]:
        return self.rows[0]

    @property
    def all_chunked(self) -> bool:
        return all(str(row["status"]) == "chunked" for row in self.rows)


class Importer:
    def __init__(
        self,
        runtime: Runtime,
        parse_concurrency: int = 2,
        embed_concurrency: int = 1,
        progress_seconds: float = 30.0,
        max_files: int = 30,
        max_seconds: float = 180.0,
        queue_max_chunks: int = 512,
    ) -> None:
        self._runtime = runtime
        self._parse_concurrency = max(1, parse_concurrency)
        self._embed_concurrency = max(1, embed_concurrency)
        self._progress_seconds = max(0.0, progress_seconds)
        # Bounded parse->embed queue: parsing stops once this many chunks are
        # waiting for embedding. Prevents unbounded memory/workpile growth when
        # parsing is much faster than the local CPU model (R3/R4, S13H-12).
        # S13H-13: 环境变量仅用于临时压测，未设置时维持默认 512。
        self._queue_max_chunks = max(
            1, int(os.environ.get("PLATFORM_IMPORT_QUEUE_MAX_CHUNKS", queue_max_chunks))
        )
        # Segment size: stop after N files so one invocation stays short and
        # the operator gets progress between segments. 0 = unlimited.
        self._max_files = max(0, max_files)
        # Wall-clock guard: stop submitting new files once the segment has run
        # this long, so one invocation never blocks the operator for long even
        # when file sizes are wildly uneven. In-flight files always finish.
        self._max_seconds = max(0.0, max_seconds)
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._counters: dict[str, int] = {
            "processed": 0, "indexed": 0, "failed": 0, "parsed": 0,
            "resumed": 0, "added": 0, "embedded": 0,
        }
        self._queue_depth = 0
        self._bytes = 0
        self._total = 0
        self._baseline = 0
        self._failed_baseline = 0
        self._started = 0.0

    # ---- helpers ---------------------------------------------------------

    def _mark(self, batch_id: uuid.UUID, group: _Group, status: str, **fields: Any) -> None:
        allowed = {"document_id", "deduplicated", "degraded", "failure_code", "failure_message"}
        updates = {key: value for key, value in fields.items() if key in allowed}
        assignments = ["status = %s", "updated_at = now()"]
        params: list[Any] = [status]
        for key, value in updates.items():
            assignments.append(f"{key} = %s")
            params.append(value)
        sql = (
            "UPDATE platform.import_item SET " + ", ".join(assignments) +
            " WHERE batch_id = %s AND rel_path = ANY(%s)"
        )
        params.extend([batch_id, group.rel_paths])
        self._runtime.metadata.execute(sql, params)

    def _bump(self, key: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[key] += amount

    def _print_progress(self) -> None:
        elapsed = max(0.001, time.monotonic() - self._started)
        with self._lock:
            processed = self._baseline + self._counters["processed"]
            indexed = self._counters["indexed"]
            failed = self._failed_baseline + self._counters["failed"]
            done_this_run = self._counters["processed"]
        rate = done_this_run / elapsed
        with self._lock:
            embedded = self._counters["embedded"]
            queue_depth = self._queue_depth
        mb = self._bytes / (1024.0 * 1024.0)
        print(
            f"[import] {processed}/{self._total} done"
            f" processed={done_this_run} indexed={indexed} failed={failed}"
            f" embedded={embedded} chunk_s={embedded / elapsed:.2f}"
            f" queue={queue_depth}/{self._queue_max_chunks}"
            f" rate={rate:.2f} files/s {mb / elapsed:.2f} MB/s elapsed={elapsed:.0f}s",
            flush=True,
        )

    def _progress_loop(self) -> None:
        while not self._stop.wait(self._progress_seconds):
            self._print_progress()

    # ---- processing ------------------------------------------------------

    def _parse_group(self, batch_id: uuid.UUID, group: _Group) -> dict[str, Any]:
        self._runtime.metadata.execute(
            "UPDATE platform.import_item SET status = 'parsing', attempts = attempts + 1, "
            "updated_at = now() WHERE batch_id = %s AND rel_path = ANY(%s)",
            (batch_id, group.rel_paths),
        )
        self._bump("parsed")
        primary = Path(str(group.primary["rel_path"]))
        return self._runtime.documents.ingest_path(
            group.path,
            primary.name,
            {"import": {"batchId": str(batch_id), "relPath": str(group.primary["rel_path"])}},
        )

    def _apply_ingest(self, batch_id: uuid.UUID, group: _Group, ingested: dict[str, Any]) -> None:
        group.degraded = bool(ingested.get("degraded"))
        if ingested.get("ingested"):
            self._bump("added")
        self._mark(
            batch_id, group, "chunked",
            document_id=str(ingested["documentId"]),
            deduplicated=bool(ingested.get("deduplicated")) or len(group.rows) > 1,
            degraded=group.degraded,
        )

    def _index_group(self, batch_id: uuid.UUID, group: _Group, document_id: str) -> dict[str, Any]:
        return self._runtime.search.index_document(document_id)

    def _record_failure(self, batch_id: uuid.UUID, group: _Group, exc: BaseException) -> None:
        code, message = _failure(exc)
        self._mark(
            batch_id, group, "failed",
            failure_code=code, failure_message=message,
            deduplicated=False, degraded=False,
        )
        self._bump("failed", len(group.rows))
        self._bump("processed", len(group.rows))
        log.warning(
            "import item failed",
            extra={
                "event": {
                    "event": "import_item_failed",
                    "batchId": str(batch_id),
                    "relPaths": list(group.rel_paths),
                    "sha256": group.sha,
                    "code": code,
                }
            },
        )

    def _pending_groups(self, batch_id: uuid.UUID) -> list[_Group]:
        rows = self._runtime.metadata.query(
            """
            SELECT rel_path, sha256, status, size_bytes, document_id, degraded
              FROM platform.import_item
             WHERE batch_id = %s AND status IN ('pending', 'parsing', 'chunked')
             ORDER BY rel_path
            """,
            (batch_id,),
        )
        batch_root = Path(
            self._runtime.metadata.query(
                "SELECT root_path FROM platform.import_batch WHERE batch_id = %s", (batch_id,)
            )[0]["root_path"]
        )
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            if row["sha256"]:
                grouped.setdefault(str(row["sha256"]), []).append(row)
        groups: list[_Group] = []
        for sha, items in grouped.items():
            items.sort(key=lambda item: str(item["rel_path"]))
            primary = items[0]
            group = _Group(
                sha, items, batch_root / str(primary["rel_path"]), int(primary["size_bytes"])
            )
            group.degraded = bool(primary.get("degraded"))
            groups.append(group)
        groups.sort(key=lambda item: item.rel_paths[0])
        return groups

    def run(
        self,
        directory: str,
        *,
        namespace_id: str | uuid.UUID,
        retry_failed: bool = False,
    ) -> dict[str, Any]:
        root = _resolve_root(directory)
        namespace = _coerce_namespace_id(namespace_id)
        _ensure_storage_dirs(self._runtime)
        started = time.monotonic()
        self._started = started
        options = {
            "parseConcurrency": self._parse_concurrency,
            "embedConcurrency": self._embed_concurrency,
            "retryFailed": retry_failed,
            "namespaceId": str(namespace),
        }
        # Simple mutual exclusion convention (no scheduler): any CPU-heavy job
        # (import / reindex / benchmark) takes `platform:heavy` first, so two
        # heavy jobs never compete for the host or the local embedding service.
        # `docker builder prune` and full-disk scans must wait for this lock too.
        #
        # The batch row is written only after the heavy lock is held. Creating it
        # first left a `running` batch behind every time a call was rejected with
        # E_HEAVY_BUSY: no process was running, and each retry bumped updated_at,
        # so a stale detector would never fire. Rejected calls now write nothing.
        with self._runtime.metadata.advisory_lock("platform:heavy", blocking=False) as heavy:
            if not heavy:
                raise PortError(
                    code="Aborted",
                    message="another heavy platform job is already running",
                    provider="platform",
                    provider_code="E_HEAVY_BUSY",
                )
            # The context manager releases the lock in `finally`, so a failure
            # while creating the batch cannot strand it either.
            batch_id = _get_or_create_batch(self._runtime, root, options, namespace)
            with self._runtime.metadata.advisory_lock(
                f"platform:import:{batch_id}", blocking=False
            ) as acquired:
                if not acquired:
                    raise PortError(
                        code="Aborted",
                        message=f"another importer is already running for {root}",
                        provider="platform",
                        provider_code="E_IMPORT_BUSY",
                    )
                run_id = _start_run(self._runtime, batch_id, namespace, options)
                try:
                    result = self._run_locked(root, batch_id, retry_failed, started)
                except Exception as exc:  # noqa: BLE001 - ledger must not hide the failure
                    _finish_run(
                        self._runtime, run_id, batch_id, status="failed",
                        counters={}, exit_code=None, error=exc,
                    )
                    raise
                result["runId"] = str(run_id)
                run_status = "interrupted" if result["interrupted"] else "completed"
                _finish_run(
                    self._runtime,
                    run_id,
                    batch_id,
                    status=run_status,
                    counters={
                        "total": result["total"],
                        "alreadyDone": result["alreadyDone"],
                        "processed": result["processed"],
                        "parsed": result["parsed"],
                        "resumedChunked": result["resumedChunked"],
                        "indexed": result["indexed"],
                        "failedThisRun": result["failedThisRun"],
                        "failedTotal": result["failed"],
                        "documentsAdded": result["documentsAdded"],
                        "remainingFiles": result["remainingFiles"],
                        "interrupted": result["interrupted"],
                        "skipped": result["skipped"],
                        "elapsedSeconds": result["elapsedSeconds"],
                    },
                    exit_code=result["exitCode"],
                )
                # One structured line per invocation: the JSON goes to stdout,
                # this is what survives in the log pipeline.
                log.info(
                    "import run finished",
                    extra={
                        "event": {
                            "event": "import_run_finished",
                            "runId": result["runId"],
                            "batchId": result["batchId"],
                            "namespaceId": str(namespace),
                            "status": run_status,
                            **{
                                key: result[key]
                                for key in (
                                    "total", "alreadyDone", "processed", "indexed",
                                    "failedThisRun", "failed", "remainingFiles",
                                    "interrupted", "skipped", "elapsedSeconds", "exitCode",
                                )
                            },
                        }
                    },
                )
                return result

    def _run_locked(
        self,
        root: Path,
        batch_id: uuid.UUID,
        retry_failed: bool,
        started: float,
    ) -> dict[str, Any]:
        cache = _batch_items(self._runtime, batch_id)
        scan = scan_directory(self._runtime, root, cache)
        indexed_shas = {
            str(row["sha256"])
            for row in self._runtime.metadata.query(
                "SELECT sha256 FROM platform.import_item WHERE batch_id = %s "
                "AND status = 'indexed' AND sha256 IS NOT NULL",
                (batch_id,),
            )
        }
        existing = _embedded_documents(self._runtime, _group_entries(scan.entries).keys())
        _upsert_items(self._runtime, batch_id, scan, indexed_shas | existing)

        # Crash residue: a killed process leaves rows in `parsing`; they are
        # incomplete and must be retried from the start of that file.
        self._runtime.metadata.execute(
            "UPDATE platform.import_item SET status = 'pending', updated_at = now() "
            "WHERE batch_id = %s AND status = 'parsing'",
            (batch_id,),
        )
        if retry_failed:
            self._runtime.metadata.execute(
                "UPDATE platform.import_item SET status = 'pending', updated_at = now() "
                "WHERE batch_id = %s AND status = 'failed' AND sha256 IS NOT NULL",
                (batch_id,),
            )

        totals = self._runtime.metadata.query(
            """
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE status IN ('indexed', 'failed')) AS done,
                   COUNT(*) FILTER (WHERE status = 'failed') AS failed
              FROM platform.import_item WHERE batch_id = %s
            """,
            (batch_id,),
        )
        self._total = int(totals[0]["total"]) if totals else 0
        self._baseline = int(totals[0]["done"]) if totals else 0
        self._failed_baseline = int(totals[0]["failed"]) if totals else 0
        groups = self._pending_groups(batch_id)
        segment_limit = self._max_files
        if segment_limit:
            selected: list[_Group] = []
            count = 0
            for group in groups:
                selected.append(group)
                count += len(group.rows)
                if count >= segment_limit:
                    break
            groups = selected

        interrupted = False
        progress_thread = None
        if self._progress_seconds and groups:
            progress_thread = threading.Thread(target=self._progress_loop, daemon=True)
            progress_thread.start()

        parse_pool = ThreadPoolExecutor(max_workers=self._parse_concurrency)
        embed_pool = ThreadPoolExecutor(max_workers=self._embed_concurrency)
        inflight_parse: dict[Any, _Group] = {}
        inflight_embed: dict[Any, _Group] = {}
        future_chunks: dict[Any, int] = {}
        queued_chunks = 0
        self._queue_depth = 0
        group_iter = iter(groups)
        exhausted = False
        exit_code = 0

        def finish_embed(future: Any) -> None:
            """Book-keep one finished embed future (also called while queue is full)."""
            nonlocal queued_chunks
            group = inflight_embed.pop(future)
            queued_chunks = max(0, queued_chunks - future_chunks.pop(future, 0))
            with self._lock:
                self._queue_depth = queued_chunks
            try:
                indexed = future.result()
            except Exception as exc:  # noqa: BLE001 - isolated per file
                self._record_failure(batch_id, group, exc)
                return
            if indexed.get("degraded"):
                # S14H-17: no silent downgrade - a document with missing vectors is
                # not "indexed". Keep it failed so the batch counts stay honest.
                code = str(indexed.get("failureCode") or "E_EMBED_DEGRADED")
                self._mark(
                    batch_id, group, "failed",
                    degraded=True, failure_code=code,
                    failure_message=(
                        "embedding degraded: "
                        + ",".join(str(item) for item in (indexed.get("reasons") or []))
                    ),
                )
                self._bump("failed", len(group.rows))
                self._bump("processed", len(group.rows))
                return
            self._mark(
                batch_id, group, "indexed",
                degraded=group.degraded or bool(indexed.get("degraded")),
                # A retried file that now succeeds must not keep the old
                # failure reason: readers filter/export on failure_code and
                # would report a healthy document as failed.
                failure_code=None,
                failure_message=None,
            )
            self._bump("embedded", int(indexed.get("embedded") or 0))
            self._bump("indexed", len(group.rows))
            self._bump("processed", len(group.rows))

        def submit_embed(group: _Group, document_id: str) -> None:
            nonlocal queued_chunks
            rows = self._runtime.metadata.query(
                "SELECT COUNT(*) AS n FROM platform.document_chunk WHERE document_id = %s",
                (document_id,),
            )
            chunks = int(rows[0]["n"]) if rows else 0
            # Bounded queue: block parsing when 512 chunks are already waiting.
            if inflight_embed and queued_chunks + chunks > self._queue_max_chunks:
                print(
                    f"[import] queue full queue={queued_chunks}/{self._queue_max_chunks}"
                    f" waiting={chunks} -> parse blocked",
                    flush=True,
                )
            while inflight_embed and queued_chunks + chunks > self._queue_max_chunks:
                done, _ = wait(set(inflight_embed), timeout=5.0, return_when=FIRST_COMPLETED)
                for finished in done:
                    finish_embed(finished)
            queued_chunks += chunks
            with self._lock:
                self._queue_depth = queued_chunks
            future = embed_pool.submit(self._index_group, batch_id, group, document_id)
            inflight_embed[future] = group
            future_chunks[future] = chunks

        try:
            while True:
                while len(inflight_parse) < self._parse_concurrency and not exhausted:
                    if self._max_seconds and (time.monotonic() - started) >= self._max_seconds:
                        # Segment budget exhausted: drain in-flight work and exit.
                        exhausted = True
                        break
                    try:
                        group = next(group_iter)
                    except StopIteration:
                        exhausted = True
                        break
                    if group.all_chunked and group.primary.get("document_id"):
                        # Resume point after parse+chunk committed: index only, no re-parse.
                        self._bump("resumed", len(group.rows))
                        self._bytes += group.size_bytes
                        submit_embed(group, str(group.primary["document_id"]))
                        continue
                    future = parse_pool.submit(self._parse_group, batch_id, group)
                    inflight_parse[future] = group

                pending = set(inflight_parse) | set(inflight_embed)
                if not pending:
                    break
                done, _ = wait(pending, timeout=5.0, return_when=FIRST_COMPLETED)
                for future in done:
                    group = inflight_parse.pop(future, None)
                    if group is not None:
                        try:
                            ingested = future.result()
                        except Exception as exc:  # noqa: BLE001 - isolated per file
                            self._record_failure(batch_id, group, exc)
                            continue
                        self._bytes += group.size_bytes
                        self._apply_ingest(batch_id, group, ingested)
                        submit_embed(group, str(ingested["documentId"]))
                        continue

                    group = inflight_embed.pop(future, None)
                    if group is not None:
                        # Put it back so finish_embed owns the whole completion path.
                        inflight_embed[future] = group
                        finish_embed(future)
        except KeyboardInterrupt:
            interrupted = True
            exit_code = 130
            for future in list(inflight_parse) + list(inflight_embed):
                future.cancel()
            self._runtime.metadata.execute(
                "UPDATE platform.import_batch SET status = 'interrupted', updated_at = now() "
                "WHERE batch_id = %s",
                (batch_id,),
            )
        finally:
            self._stop.set()
            if progress_thread is not None:
                progress_thread.join(timeout=2.0)
            parse_pool.shutdown(wait=False, cancel_futures=True)
            embed_pool.shutdown(wait=False, cancel_futures=True)

        elapsed = max(0.001, time.monotonic() - started)
        remaining_rows = self._runtime.metadata.query(
            """
            SELECT COUNT(*) AS n FROM platform.import_item
             WHERE batch_id = %s AND status IN ('pending', 'parsing', 'chunked')
            """,
            (batch_id,),
        )
        remaining = int(remaining_rows[0]["n"]) if remaining_rows else 0
        if not interrupted:
            if remaining:
                # Segment finished, batch still has work: keep it running so the
                # next invocation resumes instead of reporting completion.
                self._runtime.metadata.execute(
                    "UPDATE platform.import_batch SET status = 'running', updated_at = now() "
                    "WHERE batch_id = %s",
                    (batch_id,),
                )
            else:
                self._runtime.metadata.execute(
                    "UPDATE platform.import_batch SET status = 'completed', updated_at = now(), "
                    "finished_at = now() WHERE batch_id = %s",
                    (batch_id,),
                )
            self._print_progress()

        failures = failure_items(self._runtime, batch_id)
        failed_total = int(
            self._runtime.metadata.query(
                "SELECT COUNT(*) AS n FROM platform.import_item "
                "WHERE batch_id = %s AND status = 'failed'",
                (batch_id,),
            )[0]["n"]
        )
        with self._lock:
            counters = dict(self._counters)
        result = {
            "batchId": str(batch_id),
            "root": str(root),
            "dryRun": False,
            "retryFailed": retry_failed,
            "interrupted": interrupted,
            "total": self._total,
            "segmentLimit": segment_limit,
            "segmentSecondsLimit": self._max_seconds,
            "segmentSeconds": round(elapsed, 2),
            "remainingFiles": remaining,
            "continued": remaining > 0,
            "alreadyDone": self._baseline,
            "processed": counters["processed"],
            "parsed": counters["parsed"],
            "resumedChunked": counters["resumed"],
            "indexed": counters["indexed"],
            "failed": failed_total,
            "failedThisRun": counters["failed"],
            "documentsAdded": counters["added"],
            "skipped": {
                "unsupported": scan.unsupported,
                "hidden": scan.hidden,
                "empty": sum(1 for item in scan.problems if item.code == "E_DOC_EMPTY"),
                "tooLarge": sum(1 for item in scan.problems if item.code == "E_DOC_TOO_LARGE"),
                "unreadable": sum(1 for item in scan.problems if item.code == "E_IMPORT_UNREADABLE"),
            },
            "elapsedSeconds": round(elapsed, 2),
            "bytesProcessed": self._bytes,
            "throughputMbPerSec": round(self._bytes / (1024.0 * 1024.0) / elapsed, 2),
            "peakRssMb": _peak_rss_mb(),
            "failures": failures,
            "exitCode": exit_code,
        }
        return result


def failure_items(
    runtime: Runtime, batch_id: uuid.UUID | None = None, limit: int = 200
) -> list[dict[str, Any]]:
    if batch_id is None:
        rows = runtime.metadata.query(
            "SELECT batch_id, rel_path, attempts, failure_code, failure_message, updated_at "
            "FROM platform.import_item WHERE status = 'failed' "
            "ORDER BY updated_at DESC LIMIT %s",
            (limit,),
        )
    else:
        rows = runtime.metadata.query(
            "SELECT batch_id, rel_path, attempts, failure_code, failure_message, updated_at "
            "FROM platform.import_item WHERE batch_id = %s AND status = 'failed' "
            "ORDER BY rel_path LIMIT %s",
            (batch_id, limit),
        )
    return [
        {
            "batchId": str(row["batch_id"]),
            "relPath": row["rel_path"],
            "attempts": int(row["attempts"]),
            "code": row["failure_code"],
            "message": row["failure_message"],
            "updatedAt": row["updated_at"].isoformat() if row["updated_at"] else None,
        }
        for row in rows
    ]


def list_items(
    runtime: Runtime,
    batch_id: uuid.UUID | str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if batch_id:
        clauses.append("batch_id = %s")
        params.append(uuid.UUID(str(batch_id)))
    if status:
        clauses.append("status = %s")
        params.append(status)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(max(1, min(1000, limit)))
    rows = runtime.metadata.query(
        "SELECT batch_id, rel_path, size_bytes, sha256, document_id, status, "
        "deduplicated, degraded, attempts, failure_code, failure_message, updated_at "
        f"FROM platform.import_item{where} ORDER BY rel_path LIMIT %s",
        tuple(params),
    )
    return [
        {
            "batchId": str(row["batch_id"]),
            "relPath": row["rel_path"],
            "sizeBytes": int(row["size_bytes"]),
            "sha256": row["sha256"],
            "documentId": row["document_id"],
            "status": row["status"],
            "deduplicated": bool(row["deduplicated"]),
            "degraded": bool(row["degraded"]),
            "attempts": int(row["attempts"]),
            "failureCode": row["failure_code"],
            "failureMessage": row["failure_message"],
            "updatedAt": row["updated_at"].isoformat() if row["updated_at"] else None,
        }
        for row in rows
    ]


# S14H-16 lease/timeout convergence: a batch whose process died stays 'running'
# forever (sample: 4a1812cb, 13/20, updated_at frozen at 11:39). After this many
# minutes without any update it becomes 'stale'. Completed/indexed items and the
# resume breakpoint are preserved; only orphaned 'parsing' rows return to
# 'pending' so the next run on the same root continues instead of restarting.
STALE_AFTER_MINUTES = 30


def converge_stale_batches(runtime: Runtime, threshold_minutes: int = STALE_AFTER_MINUTES) -> int:
    """Mark dead 'running' batches stale; returns how many were converged."""
    stale = runtime.metadata.query(
        """
        SELECT batch_id FROM platform.import_batch
         WHERE status = 'running'
           AND updated_at < now() - make_interval(mins => %s)
        """,
        (threshold_minutes,),
    )
    if not stale:
        return 0
    runtime.metadata.execute(
        """
        UPDATE platform.import_batch
           SET status = 'stale', updated_at = now(),
               finished_at = COALESCE(finished_at, now()),
               options = COALESCE(options, '{}'::jsonb)
                         || jsonb_build_object('staleReason', 'E_BATCH_TIMEOUT',
                                               'staleAfterMinutes', %s)
         WHERE status = 'running'
           AND updated_at < now() - make_interval(mins => %s)
        """,
        (threshold_minutes, threshold_minutes),
    )
    runtime.metadata.execute(
        """
        UPDATE platform.import_item i
           SET status = 'pending', updated_at = now()
          FROM platform.import_batch b
         WHERE i.batch_id = b.batch_id
           AND i.status = 'parsing'
           AND b.status = 'stale'
           AND b.options->>'staleReason' = 'E_BATCH_TIMEOUT'
        """
    )
    return len(stale)


def batches_overview(runtime: Runtime, limit: int = 5) -> dict[str, Any]:
    converged = converge_stale_batches(runtime)
    if converged:
        log.warning("import batches converged to stale: %s", converged)
    rows = runtime.metadata.query(
        """
        SELECT b.batch_id, b.root_path, b.status, b.created_at, b.updated_at,
               b.finished_at,
               COUNT(i.rel_path) AS total,
               COUNT(i.rel_path) FILTER (
                   WHERE i.status IN ('indexed', 'failed')) AS completed,
               COUNT(i.rel_path) FILTER (WHERE i.status = 'indexed') AS indexed,
               COUNT(i.rel_path) FILTER (WHERE i.status = 'failed') AS failed,
               COUNT(i.rel_path) FILTER (WHERE i.degraded) AS degraded
          FROM platform.import_batch b
          LEFT JOIN platform.import_item i ON i.batch_id = b.batch_id
         GROUP BY b.batch_id, b.root_path, b.status, b.created_at, b.updated_at, b.finished_at
         ORDER BY b.updated_at DESC
         LIMIT %s
        """,
        (limit,),
    )
    batches = [
        {
            "batchId": str(row["batch_id"]),
            "root": row["root_path"],
            "status": row["status"],
            "stale": row["status"] == "stale",
            "staleReason": "E_BATCH_TIMEOUT" if row["status"] == "stale" else None,
            "total": int(row["total"]),
            "completed": int(row["completed"]),
            "indexed": int(row["indexed"]),
            "failed": int(row["failed"]),
            "degraded": int(row["degraded"]),
            "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
            "updatedAt": row["updated_at"].isoformat() if row["updated_at"] else None,
            "finishedAt": row["finished_at"].isoformat() if row["finished_at"] else None,
        }
        for row in rows
    ]
    failures = failure_items(runtime, limit=20)
    return {"batches": batches, "failures": failures}


_INGESTION_RUN_STATUSES = {"RUNNING", "COMPLETED", "INTERRUPTED", "STALE"}


def _decode_offset(next_token: str | None) -> int:
    if not next_token:
        return 0
    try:
        raw = base64.urlsafe_b64decode(next_token.encode("ascii")).decode("ascii")
        offset = int(raw)
    except (ValueError, UnicodeError, binascii.Error) as exc:
        raise PortError(
            code="InvalidArgument",
            message=f"nextToken is not a token issued by ListIngestionRuns: {next_token!r}",
            provider="platform",
            provider_code="E_INGESTION_TOKEN_INVALID",
        ) from exc
    if offset < 0:
        raise PortError(
            code="InvalidArgument",
            message="nextToken points before the first page",
            provider="platform",
            provider_code="E_INGESTION_TOKEN_INVALID",
        )
    return offset


def _encode_offset(offset: int) -> str:
    return base64.urlsafe_b64encode(str(offset).encode("ascii")).decode("ascii")


def _last_runs(runtime: Runtime, batch_ids: list[Any]) -> dict[Any, dict[str, Any]]:
    """Latest ledger row per batch (one query, no N+1)."""
    if not batch_ids:
        return {}
    rows = runtime.metadata.query(
        """
        SELECT DISTINCT ON (batch_id)
               batch_id, run_id, status, started_at, finished_at, exit_code,
               counters, error_code, error_message
          FROM platform.import_run
         WHERE batch_id = ANY(%s)
         ORDER BY batch_id, started_at DESC
        """,
        (list(batch_ids),),
    )
    return {row["batch_id"]: row for row in rows}


def _run_view(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "runId": str(row["run_id"]),
        "status": row["status"].upper(),
        "startedAt": row["started_at"].isoformat() if row["started_at"] else None,
        "finishedAt": row["finished_at"].isoformat() if row["finished_at"] else None,
        "exitCode": row["exit_code"],
        "counters": row["counters"] or None,
        "errorCode": row["error_code"],
        "errorMessage": row["error_message"],
    }


def ingestion_runs(
    runtime: Runtime,
    namespace_id: str,
    *,
    kind: str | None = None,
    status: str | None = None,
    max_results: int = 20,
    next_token: str | None = None,
) -> dict[str, Any]:
    """F17/F18: namespace-scoped import batches with live per-item counters.

    Reads only. Stale convergence stays with the import worker: a @readonly
    operation must not write, so a dead `running` batch keeps reporting
    `running` until the worker's recovery pass marks it stale.
    """
    try:
        ns = uuid.UUID(namespace_id)
    except ValueError as exc:
        raise PortError(
            code="InvalidArgument",
            message=f"namespaceId is not a UUID: {namespace_id!r}",
            provider="platform",
            provider_code="E_NAMESPACE_ID_INVALID",
        ) from exc

    run_kind = (kind or "BATCH").upper()
    if run_kind != "BATCH":
        raise PortError(
            code="InvalidArgument",
            message=(
                f"kind={run_kind} is not implemented; ListIngestionRuns only "
                "serves kind=BATCH in this batch"
            ),
            provider="platform",
            provider_code="E_INGESTION_KIND_UNSUPPORTED",
        )

    run_status = status.upper() if status else None
    if run_status is not None and run_status not in _INGESTION_RUN_STATUSES:
        raise PortError(
            code="InvalidArgument",
            message=(
                f"status={status!r} is not one of "
                f"{sorted(_INGESTION_RUN_STATUSES)}"
            ),
            provider="platform",
            provider_code="E_INGESTION_STATUS_INVALID",
        )
    db_status = run_status.lower() if run_status else None

    if max_results < 1 or max_results > 50:
        raise PortError(
            code="InvalidArgument",
            message="maxResults must be between 1 and 50",
            provider="platform",
            provider_code="E_INGESTION_LIMIT_INVALID",
        )
    offset = _decode_offset(next_token)

    where = "b.namespace_id = %s"
    params: list[Any] = [ns]
    if db_status is not None:
        where += " AND b.status = %s"
        params.append(db_status)

    total_row = runtime.metadata.query(
        f"SELECT count(*) AS n FROM platform.import_batch b WHERE {where}",
        tuple(params),
    )
    total_count = int(total_row[0]["n"])

    rows = runtime.metadata.query(
        f"""
        SELECT b.batch_id, b.root_path, b.status, b.created_at, b.updated_at,
               b.finished_at,
               COUNT(i.rel_path) AS total,
               COUNT(i.rel_path) FILTER (
                   WHERE i.status IN ('indexed', 'failed')) AS completed,
               COUNT(i.rel_path) FILTER (WHERE i.status = 'indexed') AS indexed,
               COUNT(i.rel_path) FILTER (WHERE i.status = 'failed') AS failed,
               COUNT(i.rel_path) FILTER (WHERE i.degraded) AS degraded
          FROM platform.import_batch b
          LEFT JOIN platform.import_item i ON i.batch_id = b.batch_id
         WHERE {where}
         GROUP BY b.batch_id, b.root_path, b.status, b.created_at, b.updated_at,
                  b.finished_at
         ORDER BY b.updated_at DESC, b.batch_id
         LIMIT %s OFFSET %s
        """,
        tuple(params) + (max_results + 1, offset),
    )
    has_more = len(rows) > max_results
    rows = rows[:max_results]
    last_runs = _last_runs(runtime, [row["batch_id"] for row in rows])

    items = [
        {
            "runId": str(row["batch_id"]),
            "root": row["root_path"],
            "status": row["status"].upper(),
            "stale": row["status"] == "stale",
            "staleReason": "E_BATCH_TIMEOUT" if row["status"] == "stale" else None,
            "total": int(row["total"]),
            "completed": int(row["completed"]),
            "indexed": int(row["indexed"]),
            "failed": int(row["failed"]),
            "degraded": int(row["degraded"]),
            "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
            "updatedAt": row["updated_at"].isoformat() if row["updated_at"] else None,
            "finishedAt": row["finished_at"].isoformat() if row["finished_at"] else None,
            "lastRun": _run_view(last_runs.get(row["batch_id"])),
        }
        for row in rows
    ]

    failures = runtime.metadata.query(
        """
        SELECT i.batch_id, i.rel_path, i.attempts, i.failure_code,
               i.failure_message, i.updated_at
          FROM platform.import_item i
          JOIN platform.import_batch b ON b.batch_id = i.batch_id
         WHERE i.status = 'failed' AND b.namespace_id = %s
         ORDER BY i.updated_at DESC
         LIMIT 20
        """,
        (ns,),
    )
    failure_feed = [
        {
            "runId": str(row["batch_id"]),
            "relPath": row["rel_path"],
            "attempts": int(row["attempts"]),
            "code": row["failure_code"],
            "message": row["failure_message"],
            "updatedAt": row["updated_at"].isoformat() if row["updated_at"] else None,
        }
        for row in failures
    ]

    return {
        "items": items,
        "totalCount": total_count,
        "failures": failure_feed,
        "nextToken": _encode_offset(offset + max_results) if has_more else None,
    }
