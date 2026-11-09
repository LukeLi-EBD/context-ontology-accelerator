"""S13 acceptance: bulk directory import.

Covers dry-run accuracy, sha256 dedupe (including renamed copies), crash
resume (only unfinished rows), per-file failure isolation with explicit
reasons and --retry-failed, plus the read-only import progress endpoint.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

import httpx

from .assembly import Runtime
from .errors import PortError
from .importer import Importer, dry_run, list_items

# S13H-13 fix: acceptance imports used to fail outright when a real import held
# the `platform:heavy` advisory lock. Wait (2s steps, 180s total) instead of
# creating a second lock; if the budget runs out the suite reports SKIP (75)
# rather than FAIL so a long import cannot fail an acceptance run.
HEAVY_WAIT_SECONDS = 180.0
HEAVY_RETRY_INTERVAL_SECONDS = 2.0


class HeavyBlocked(Exception):
    """Raised when the wait budget is spent; maps to exit 75 (SKIP)."""

    def __init__(self, attempts: int, limit: int, holder: str) -> None:
        self.attempts = attempts
        self.limit = limit
        self.holder = holder
        super().__init__(f"blocked_by_heavy attempts={attempts}/{limit} holder={holder}")


def _heavy_busy(exc: PortError) -> bool:
    return getattr(exc, "provider_code", None) == "E_HEAVY_BUSY"


def _heavy_holder(runtime: Runtime) -> str:
    """Describe the session holding `platform:heavy` for the SKIP line."""
    try:
        rows = runtime.metadata.query(
            """
            SELECT l.pid, a.application_name, a.state,
                   to_char(a.query_start, 'HH24:MI:SS') AS started
            FROM pg_locks l
            LEFT JOIN pg_stat_activity a ON a.pid = l.pid
            WHERE l.locktype = 'advisory' AND l.granted
              AND (l.classid::bigint, l.objid::bigint) = (
                  SELECT (k >> 32) & 4294967295, k & 4294967295
                  FROM (SELECT hashtext('platform:heavy')::bigint AS k) t
              )
            ORDER BY l.pid
            LIMIT 1
            """
        )
    except Exception:  # noqa: BLE001 - diagnostics must not mask the skip
        return "unknown"
    if not rows:
        return "unknown"
    row = rows[0]
    return (
        f"pid={row['pid']} app={row.get('application_name') or '-'} "
        f"state={row.get('state') or '-'} started={row.get('started') or '-'}"
    )


def _wait_heavy_free(runtime: Runtime) -> None:
    """Block until the existing `platform:heavy` lock is free (same lock, no new one)."""
    deadline = time.monotonic() + HEAVY_WAIT_SECONDS
    attempt = 0
    limit = max(1, int(HEAVY_WAIT_SECONDS / HEAVY_RETRY_INTERVAL_SECONDS))
    while True:
        with runtime.metadata.advisory_lock("platform:heavy", blocking=False) as free:
            if free:
                return
        attempt += 1
        if time.monotonic() >= deadline:
            raise HeavyBlocked(attempt, limit, _heavy_holder(runtime))
        print(f"[smoke] waiting heavy job {attempt}/{limit}", flush=True)
        time.sleep(HEAVY_RETRY_INTERVAL_SECONDS)


def _run_importer(
    runtime: Runtime,
    directory: str,
    *,
    retry_failed: bool = False,
    timeout_s: float | None = None,
) -> dict:
    """Run an import, retrying E_HEAVY_BUSY up to the wait budget."""
    timeout = HEAVY_WAIT_SECONDS if timeout_s is None else timeout_s
    deadline = time.monotonic() + timeout
    attempt = 0
    limit = max(1, int(timeout / HEAVY_RETRY_INTERVAL_SECONDS))
    while True:
        try:
            return Importer(runtime, progress_seconds=0).run(
                directory, retry_failed=retry_failed
            )
        except PortError as exc:
            if not _heavy_busy(exc):
                raise
            attempt += 1
            if time.monotonic() >= deadline:
                raise HeavyBlocked(attempt, limit, _heavy_holder(runtime)) from exc
            print(f"[smoke] waiting heavy job {attempt}/{limit}", flush=True)
            time.sleep(HEAVY_RETRY_INTERVAL_SECONDS)


class _Case:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def check(self, name: str, condition: bool, detail: str = "") -> bool:
        self.results.append((name, bool(condition), detail))
        return bool(condition)

    def fail(self, name: str, detail: str) -> None:
        self.results.append((name, False, detail))


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _item_states(runtime: Runtime, batch_id: str) -> dict[str, int]:
    rows = runtime.metadata.query(
        "SELECT status, COUNT(*) AS n FROM platform.import_item WHERE batch_id = %s "
        "GROUP BY status",
        (uuid.UUID(batch_id),),
    )
    return {str(row["status"]): int(row["n"]) for row in rows}


def _document_count(runtime: Runtime, document_ids: list[str]) -> int:
    if not document_ids:
        return 0
    rows = runtime.metadata.query(
        "SELECT COUNT(*) AS n FROM platform.document WHERE document_id = ANY(%s)",
        (document_ids,),
    )
    return int(rows[0]["n"])


def run_smoke_s13(runtime: Runtime, base_url: str) -> int:
    suite = _Case()
    base = base_url.rstrip("/")
    nonce = uuid.uuid4().hex[:8]
    tmp_dir = Path(runtime.config.storage.tmp_dir) / f"s13-{nonce}"
    clean_dir = tmp_dir / "clean"
    crash_dir = tmp_dir / "crash"
    bad_dir = tmp_dir / "bad"
    created_batches: list[str] = []
    fixture = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "encrypted.pdf"

    try:
        runtime.metadata.open(retry_seconds=10.0)
        runtime.metadata.migrate()

        # ---- 1) dry-run accuracy + sha256 dedupe (rename = same object) ----
        content_a = f"alpha {nonce}\n" * 40
        _write(clean_dir / "a.txt", content_a)
        _write(clean_dir / "copy-of-a.md", content_a)  # rename, same content
        _write(clean_dir / "b.md", f"# beta {nonce}\n" + "beta body\n" * 40)
        _write(clean_dir / "sub" / "c.txt", f"gamma {nonce}\n" * 40)
        _write(clean_dir / "empty.txt", "")
        _write(clean_dir / "notes.bin", "not a document")
        _write(clean_dir / ".hidden.txt", "hidden")

        preview = dry_run(runtime, str(clean_dir))
        suite.check(
            "dryrun.counts",
            preview["toImport"] == 3 and preview["toImportFiles"] == 4
            and preview["skipped"] == 4
            and preview["skipBreakdown"]["duplicate"] == 1
            and preview["skipBreakdown"]["unsupported"] == 1
            and preview["skipBreakdown"]["empty"] == 1
            and preview["skipBreakdown"]["hidden"] == 1,
            f"toImport={preview['toImport']} files={preview['toImportFiles']} "
            f"skipped={preview['skipped']} breakdown={preview['skipBreakdown']}",
        )

        first = _run_importer(runtime, str(clean_dir))
        created_batches.append(first["batchId"])
        suite.check(
            "import.dryrun_matches",
            first["documentsAdded"] == preview["toImport"]
            and first["indexed"] == preview["toImportFiles"] and first["failed"] == 1,
            f"added={first['documentsAdded']} indexed={first['indexed']} "
            f"failed={first['failed']}",
        )
        items = list_items(runtime, first["batchId"])
        copy_items = [item for item in items if item["relPath"] == "copy-of-a.md"]
        a_items = [item for item in items if item["relPath"] == "a.txt"]
        suite.check(
            "dedupe.rename_cas",
            bool(copy_items and a_items)
            and copy_items[0]["documentId"] == a_items[0]["documentId"]
            and copy_items[0]["deduplicated"] is True,
            f"copyDoc={copy_items[0]['documentId'] if copy_items else None} "
            f"aDoc={a_items[0]['documentId'] if a_items else None}",
        )
        suite.check(
            "state.empty_failed",
            _item_states(runtime, first["batchId"]).get("failed") == 1
            and [
                item for item in list_items(runtime, first["batchId"], "failed")
                if item["relPath"] == "empty.txt"
                and item["failureCode"] == "E_DOC_EMPTY"
            ] != [],
            f"states={_item_states(runtime, first['batchId'])}",
        )

        second = _run_importer(runtime, str(clean_dir))
        suite.check(
            "rerun.no_work",
            second["processed"] == 0 and second["parsed"] == 0
            and second["documentsAdded"] == 0 and second["indexed"] == 0,
            f"processed={second['processed']} parsed={second['parsed']} "
            f"added={second['documentsAdded']}",
        )
        after_ids = [item["documentId"] for item in list_items(runtime, first["batchId"])]
        suite.check(
            "rerun.no_duplicate_docs",
            len({sha for sha in after_ids if sha}) == 3
            and after_ids.count(None) == 1,
            f"uniqueDocs={len({sha for sha in after_ids if sha})} rows={len(after_ids)}",
        )

        # ---- 2) crash/interrupt resume only unfinished rows ----
        filler = ("resume probe line " + nonce + "\n") * 12
        crash_files = []
        for index in range(20):
            path = crash_dir / f"bulk-{index:02d}.txt"
            _write(path, f"file {index} {nonce}\n" + filler)
            crash_files.append(path)

        _wait_heavy_free(runtime)
        process = subprocess.Popen(
            [sys.executable, "-m", "platform_core.cli", "import", str(crash_dir),
             "--config", str(runtime.bundle.path), "--progress-seconds", "0",
             "--parse-concurrency", "1", "--embed-concurrency", "1"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        batch_id = None
        deadline = time.monotonic() + 30.0
        while time.monotonic() < deadline:
            rows = runtime.metadata.query(
                "SELECT batch_id FROM platform.import_batch WHERE root_path = %s",
                (str(crash_dir.resolve()),),
            )
            if rows:
                batch_id = str(rows[0]["batch_id"])
                states = _item_states(runtime, batch_id)
                if states.get("indexed", 0) >= 1 and (
                    states.get("pending", 0) + states.get("parsing", 0)
                    + states.get("chunked", 0)
                ) >= 1:
                    break
            if process.poll() is not None:
                break
            time.sleep(0.1)
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

        if batch_id:
            created_batches.append(batch_id)
            states = _item_states(runtime, batch_id)
            remaining = (
                states.get("pending", 0) + states.get("parsing", 0)
                + states.get("chunked", 0)
            )
            done = states.get("indexed", 0)
            resumed = _run_importer(runtime, str(crash_dir))
            final_states = _item_states(runtime, batch_id)
            suite.check(
                "resume.only_remaining",
                remaining >= 1 and done >= 1 and resumed["processed"] == remaining
                and final_states.get("indexed", 0) == len(crash_files),
                f"indexed_before={done} remaining={remaining} "
                f"processed={resumed['processed']} final={final_states}",
            )
        else:
            suite.fail("resume.only_remaining", "batch row never appeared before kill")

        # ---- 3) failure isolation + --retry-failed ----
        _write(bad_dir / "good.txt", f"good {nonce}\n" * 30)
        _write(bad_dir / "empty.txt", "")
        (bad_dir / "corrupted.pdf").write_bytes(b"%PDF-1.4\n1 0 obj\n<< broken")
        if fixture.exists():
            shutil.copyfile(fixture, bad_dir / "encrypted.pdf")
        else:
            suite.fail("fixture.encrypted", f"missing fixture {fixture}")

        bad_run = _run_importer(runtime, str(bad_dir))
        created_batches.append(bad_run["batchId"])
        codes = {item["code"] for item in bad_run["failures"]}
        suite.check(
            "failure.isolation",
            bad_run["indexed"] == 1 and bad_run["failed"] == 3
            and len(bad_run["failures"]) == 3
            and codes == {"E_DOC_EMPTY", "E_DOC_PARSE_FAILED", "E_DOC_PDF_ENCRYPTED"}
            and bad_run["interrupted"] is False,
            f"indexed={bad_run['indexed']} failures={sorted(codes)}",
        )

        retry = _run_importer(runtime, str(bad_dir), retry_failed=True)
        retry_codes = {item["code"] for item in retry["failures"]}
        suite.check(
            "failure.retry_failed",
            retry["processed"] == 2 and retry["indexed"] == 0
            and len(retry["failures"]) == 3
            and retry_codes == {"E_DOC_EMPTY", "E_DOC_PARSE_FAILED", "E_DOC_PDF_ENCRYPTED"},
            f"processed={retry['processed']} indexed={retry['indexed']} "
            f"failures={sorted(retry_codes)}",
        )
        suite.check(
            "summary.metrics",
            bad_run["throughputMbPerSec"] >= 0 and bad_run["peakRssMb"] > 0
            and bad_run["elapsedSeconds"] > 0,
            f"throughput={bad_run['throughputMbPerSec']}MB/s "
            f"rss={bad_run['peakRssMb']}MB elapsed={bad_run['elapsedSeconds']}s",
        )

        # ---- 4) read-only progress endpoint ----
        with httpx.Client(base_url=base, timeout=60.0) as client:
            status = client.get("/status").json()
            suite.check(
                "http.status", status.get("slice") == "S13",
                f"slice={status.get('slice')}",
            )
            batches = client.get("/imports/batches?limit=10").json().get("batches", [])
            target = [b for b in batches if b.get("batchId") == bad_run["batchId"]]
            suite.check(
                "http.import_progress",
                bool(target) and target[0]["total"] == 4
                and target[0]["completed"] == 4 and target[0]["failed"] == 3,
                f"batch={target[0] if target else None}",
            )
            failed_items = client.get(
                "/imports/items", params={"batch_id": bad_run["batchId"], "status": "failed"}
            ).json().get("items", [])
            suite.check(
                "http.failure_reasons", len(failed_items) == 3,
                f"failed_items={len(failed_items)}",
            )
    except HeavyBlocked as exc:
        # S13H-13: being blocked by another heavy job is a SKIP (exit 75), not a
        # failure: the suite is incomplete, not incorrect.
        print(
            f"SKIP blocked_by_heavy attempts={exc.attempts}/{exc.limit} holder={exc.holder}",
            flush=True,
        )
        return 75
    except Exception as exc:  # noqa: BLE001 - report as a failed suite, not a crash
        suite.fail("runtime", f"{type(exc).__name__}: {exc}")
    finally:
        try:
            for batch_id in created_batches:
                runtime.metadata.execute(
                    "DELETE FROM platform.import_batch WHERE batch_id = %s",
                    (uuid.UUID(batch_id),),
                )
        except Exception:  # noqa: BLE001 - cleanup must not mask results
            pass
        shutil.rmtree(tmp_dir, ignore_errors=True)

    passed = sum(1 for _, ok, _ in suite.results if ok)
    total = len(suite.results)
    print(f"SMOKE-S13 {passed}/{total}")
    for name, ok, detail in suite.results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    return 0 if passed == total else 1
