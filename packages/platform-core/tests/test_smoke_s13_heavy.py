"""S13H-13: smoke-s13 waits for the existing `platform:heavy` advisory lock.

Needs a live platform DB, so it runs inside the API container:

    docker compose exec -T platform python /app/tests/test_smoke_s13_heavy.py

Scenario: a second connection holds `platform:heavy`. Import must wait and
succeed within budget; when the budget is exhausted smoke-s13 must exit 75
(SKIP blocked_by_heavy), never a FAIL.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import threading
import time
import uuid
from pathlib import Path

import psycopg

from platform_core.assembly import assemble
from platform_core.config import load_config
from platform_core import smoke_s13

CONFIG_PATH = "/data/platform.yaml"


def _hold_heavy(dsn: str, seconds: float, ready: threading.Event) -> None:
    conn = psycopg.connect(dsn)
    try:
        conn.execute("SELECT pg_advisory_lock(hashtext('platform:heavy'))")
        conn.commit()
        ready.set()
        time.sleep(seconds)
    finally:
        conn.execute("SELECT pg_advisory_unlock(hashtext('platform:heavy'))")
        conn.commit()
        conn.close()


def main() -> int:
    bundle = load_config(CONFIG_PATH)
    runtime = assemble(bundle)
    runtime.metadata.open(retry_seconds=10.0)
    runtime.metadata.migrate()
    dsn = bundle.config.database.url
    tmp = Path(bundle.config.storage.tmp_dir) / f"s13heavy-{uuid.uuid4().hex[:8]}"
    tmp.mkdir(parents=True, exist_ok=True)
    nonce = uuid.uuid4().hex[:8]
    for i in range(2):
        (tmp / f"doc-{i}.txt").write_text(
            f"heavy wait probe {nonce} line\n" * 20, encoding="utf-8"
        )

    batches: list[str] = []
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))
        print(f"{'PASS' if ok else 'FAIL'} {name} {detail}")

    # ---- 1) waits for the lock holder, then succeeds within budget ------
    ready = threading.Event()
    holder = threading.Thread(
        target=_hold_heavy, args=(dsn, 4.0, ready), daemon=True
    )
    holder.start()
    ready.wait(10)
    started = time.monotonic()
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            result = smoke_s13._run_importer(runtime, str(tmp))
        batches.append(result["batchId"])
        waited = time.monotonic() - started
        output = buf.getvalue()
        check(
            "wait.within_budget_succeeds",
            result["processed"] == 2 and waited >= 2.0 and "SKIP" not in output,
            f"processed={result['processed']} waited={waited:.1f}s",
        )
    except Exception as exc:  # noqa: BLE001
        check("wait.within_budget_succeeds", False, f"{type(exc).__name__}: {exc}")
    holder.join(10)

    # ---- 2) budget exhausted -> exit 75 + SKIP blocked_by_heavy ---------
    ready = threading.Event()
    holder = threading.Thread(
        target=_hold_heavy, args=(dsn, 6.0, ready), daemon=True
    )
    holder.start()
    ready.wait(10)
    original = smoke_s13.HEAVY_WAIT_SECONDS
    smoke_s13.HEAVY_WAIT_SECONDS = 0.5
    started = time.monotonic()
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = smoke_s13.run_smoke_s13(runtime, "http://127.0.0.1:8080")
        output = buf.getvalue()
        elapsed = time.monotonic() - started
        check(
            "timeout.exit_75_skip",
            code == 75 and "SKIP blocked_by_heavy" in output and elapsed < 6.0,
            f"code={code} elapsed={elapsed:.1f}s output={output.strip().splitlines()[-1] if output.strip() else ''}",
        )
    finally:
        smoke_s13.HEAVY_WAIT_SECONDS = original
        holder.join(10)

    digests = [hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp.glob("*")]
    for digest in digests:
        runtime.metadata.execute(
            "DELETE FROM platform.document WHERE document_id = %s", (digest,)
        )
    for batch_id in batches:
        runtime.metadata.execute(
            "DELETE FROM platform.import_batch WHERE batch_id = %s",
            (uuid.UUID(batch_id),),
        )
    for path in tmp.glob("*"):
        path.unlink(missing_ok=True)
    tmp.rmdir()
    runtime.close()

    print(f"SMOKE-S13-HEAVY {sum(1 for _, ok, _ in checks if ok)}/{len(checks)}")
    return 0 if all(ok for _, ok, _ in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
