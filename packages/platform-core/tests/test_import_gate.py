"""P1-02: the repeatable-import gate.

Runs the real ``platform_core.cli import`` command against a throwaway
PostgreSQL and a fixed three-file corpus, three times, then a fail/retry
scenario. It asserts the contract a re-run must keep:

  * every invocation opens its own ``import_run`` row (three distinct run ids);
  * a second and third run add no ``import_batch`` / ``import_item`` /
    ``document`` / ``document_chunk`` / ``chunk_embedding`` rows and report
    ``indexed=0`` with ``alreadyDone=3``;
  * an embedding outage fails loudly (exit 1, every item
    ``E_EMBED_UNAVAILABLE``) and ``--retry-failed`` recovers it (exit 0,
    ``attempts`` goes 1 -> 2, the document leaves the degraded state).

Point ``IMPORT_GATE_PG_DSN`` at a disposable database (the CI script starts one
and deletes it); without it the module skips, like the other DB-backed tests.
``scripts/ci/import-idempotency.sh`` is the only intended entry point.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

import psycopg

GATE_DSN = os.environ.get("IMPORT_GATE_PG_DSN")
NAMESPACE = uuid.UUID("00000000-0000-0000-0000-0000000000b2")
FAKE_MODEL = "fake-hash-1024"
DIMENSIONS = 1024
# A port that is closed on purpose: the embedding client maps the refused
# connection to E_EMBED_UNAVAILABLE, which is the outage this gate simulates.
DEAD_ENDPOINT = "http://127.0.0.1:1/v1"

REPO_ROOT = Path(__file__).resolve().parents[3]

# Fixed corpus: the bytes (and therefore the document ids) never change, so a
# failing assertion points at the importer, not at test data drift.
REPEAT_CORPUS = {
    "01-handbook.txt": "Alpha handbook.\nRe-importing this directory must not add rows.\n",
    "02-policy.md": "# Policy\n\nA retried import reads the same three files.\n",
    "03-notes.txt": "Notes\nthird file\nfixed corpus\n",
}
RETRY_CORPUS = {
    "01-outage.txt": "Outage corpus one.\nEmbedding is down on the first pass.\n",
    "02-outage.md": "# Outage two\n\nThe retry uses a healthy provider.\n",
    "03-outage.txt": "Outage corpus three.\nattempts must reach two.\n",
}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _pythonpath() -> str:
    """Same import path the local venv needs; harmless where packages are installed."""
    parts = [str(p) for p in sorted(REPO_ROOT.glob("packages/*/src"))]
    parts += [str(p) for p in sorted(REPO_ROOT.glob("libs/*/src"))]
    server = REPO_ROOT / "smithy-generated" / "control-plane-python-server"
    if server.is_dir():
        parts.append(str(server))
    inherited = os.environ.get("PYTHONPATH")
    if inherited:
        parts.append(inherited)
    return os.pathsep.join(parts)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _json_tail(stdout: str) -> dict:
    """The command may print a progress line before the JSON document."""
    lines = stdout.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "{":
            return json.loads("\n".join(lines[index:]))
    raise json.JSONDecodeError("no JSON object in stdout", stdout, 0)


@unittest.skipUnless(
    GATE_DSN,
    "IMPORT_GATE_PG_DSN not set; run scripts/ci/import-idempotency.sh",
)
class ImportGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = Path(tempfile.mkdtemp(prefix="p1-02-import-gate-"))
        cls.addClassCleanup(shutil.rmtree, cls.tmp, True)
        cls.conn = psycopg.connect(GATE_DSN, autocommit=True)
        cls.addClassCleanup(cls.conn.close)
        # The first CLI invocation would migrate too, but the fixtures below
        # read and write the pointer table before that call.
        from platform_core.adapters.metadata_pg import MetadataPg

        meta = MetadataPg(GATE_DSN)
        meta.open(retry_seconds=15)
        try:
            meta.migrate()
        finally:
            meta.close()
        cls._previous_pointer = cls._read_pointer()
        cls.addClassCleanup(cls._restore_pointer)

        cls.repeat_root = cls._make_corpus("repeat", REPEAT_CORPUS)
        cls.retry_root = cls._make_corpus("retry", RETRY_CORPUS)
        cls.repeat_shas = [_sha(text) for text in REPEAT_CORPUS.values()]
        cls.retry_shas = [_sha(text) for text in RETRY_CORPUS.values()]

        # --- scenario 1: the same command three times ---------------------
        cls._set_pointer("fake", FAKE_MODEL, DIMENSIONS)
        repeat_cfg = cls._write_config("repeat.yaml")
        cls.repeat_runs = []
        cls.repeat_counts = []
        cls.repeat_batch = ""
        for _ in range(3):
            run = cls._run_import(cls.repeat_root, repeat_cfg)
            batch = str(run["result"]["batchId"])
            if cls.repeat_batch:
                if batch != cls.repeat_batch:
                    raise AssertionError(f"batch moved: {batch} != {cls.repeat_batch}")
            else:
                cls.repeat_batch = batch
            cls.repeat_runs.append(run)
            cls.repeat_counts.append(cls._counts(batch, cls.repeat_shas))
        cls.repeat_run_rows = cls._run_rows(cls.repeat_batch)

        # --- scenario 2: embedding outage, then --retry-failed ------------
        cls._set_pointer("local-bge", "BAAI/bge-m3", DIMENSIONS)
        outage_cfg = cls._write_config("outage.yaml")
        cls.outage = cls._run_import(cls.retry_root, outage_cfg)
        cls.outage_batch = str(cls.outage["result"]["batchId"])
        # Snapshot now: --retry-failed below rewrites these rows.
        cls.outage_items = cls._items(cls.outage_batch)
        cls.outage_histogram = cls._failure_histogram(cls.outage_batch)
        cls.outage_documents = cls._documents(cls.retry_shas)
        cls.outage_runs = cls._run_rows(cls.outage_batch)

        cls._set_pointer("fake", FAKE_MODEL, DIMENSIONS)
        healthy_cfg = cls._write_config("healthy.yaml")
        cls.retry = cls._run_import(cls.retry_root, healthy_cfg, "--retry-failed")
        cls.retry_items = cls._items(cls.outage_batch)
        cls.retry_documents = cls._documents(cls.retry_shas)
        cls.addClassCleanup(
            cls._delete_rows,
            [cls.repeat_batch, cls.outage_batch],
            cls.repeat_shas + cls.retry_shas,
        )

    # ---- fixtures ---------------------------------------------------------

    @classmethod
    def _make_corpus(cls, name: str, corpus: dict[str, str]) -> Path:
        root = cls.tmp / name
        root.mkdir(parents=True)
        for filename, text in corpus.items():
            with open(root / filename, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
        return root

    @classmethod
    def _write_config(cls, name: str) -> Path:
        data = cls.tmp / "data"
        storage = data / "storage"
        tmp_dir = data / "tmp"
        for directory in (data, storage, tmp_dir):
            directory.mkdir(parents=True, exist_ok=True)
        config = cls.tmp / name
        config.write_text(
            "\n".join(
                [
                    "mode: single",
                    "config_version: 1",
                    f"data_dir: {data.as_posix()}",
                    "database:",
                    f"  url: {GATE_DSN}",
                    "graph:",
                    "  provider: oxigraph-http",
                    f"  endpoint: http://127.0.0.1:{_free_port()}",
                    "canvas:",
                    '  provider: "off"',
                    "storage:",
                    f"  root: {storage.as_posix()}",
                    f"  tmp_dir: {tmp_dir.as_posix()}",
                    "  min_free_pct: 0",
                    "embedding:",
                    "  provider: fake",
                    f"  dimensions: {DIMENSIONS}",
                    # Only consulted when the pointer says local-bge (the
                    # outage scenario); the fake partition never opens a socket.
                    f"  endpoint: {DEAD_ENDPOINT}",
                    "  max_chunks_per_sec: 0",
                    "  retry_max: 0",
                    "  request_timeout_s: 2",
                    "log:",
                    "  level: warning",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return config

    @classmethod
    def _run_import(
        cls, directory: Path, config: Path, *extra: str
    ) -> dict[str, object]:
        env = {k: v for k, v in os.environ.items() if not k.startswith("PLATFORM__")}
        env["PYTHONPATH"] = _pythonpath()
        env["PYTHONUNBUFFERED"] = "1"
        command = [
            sys.executable,
            "-m",
            "platform_core.cli",
            "import",
            str(directory),
            "--namespace-id",
            str(NAMESPACE),
            "--config",
            str(config),
            "--progress-seconds",
            "0",
            "--batch-size",
            "0",
            "--max-seconds",
            "0",
            *extra,
        ]
        completed = subprocess.run(
            command, capture_output=True, text=True, env=env, timeout=300
        )
        try:
            payload = _json_tail(completed.stdout)
        except json.JSONDecodeError as exc:  # pragma: no cover - diagnostic path
            raise AssertionError(
                "import command did not print JSON\n"
                f"exit={completed.returncode}\nstdout:\n{completed.stdout}\n"
                f"stderr:\n{completed.stderr}"
            ) from exc
        return {
            "exit": completed.returncode,
            "result": payload,
            "stderr": completed.stderr,
        }

    # ---- database helpers -------------------------------------------------

    @classmethod
    def _scalar(cls, sql: str, params: tuple = ()) -> int:
        with cls.conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
        return int(row[0])

    @classmethod
    def _read_pointer(cls) -> dict[str, object] | None:
        with cls.conn.cursor() as cur:
            cur.execute(
                "SELECT provider, model, dimensions FROM platform.embedding_pointer WHERE id"
            )
            row = cur.fetchone()
        if not row:
            return None
        return {"provider": row[0], "model": row[1], "dimensions": int(row[2])}

    @classmethod
    def _set_pointer(cls, provider: str, model: str, dimensions: int) -> None:
        with cls.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO platform.embedding_pointer (id, provider, model, dimensions)
                VALUES (true, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                   SET provider = EXCLUDED.provider,
                       model = EXCLUDED.model,
                       dimensions = EXCLUDED.dimensions,
                       updated_at = now()
                """,
                (provider, model, dimensions),
            )

    @classmethod
    def _restore_pointer(cls) -> None:
        if cls._previous_pointer is None:
            with cls.conn.cursor() as cur:
                cur.execute("DELETE FROM platform.embedding_pointer WHERE id")
            return
        cls._set_pointer(
            str(cls._previous_pointer["provider"]),
            str(cls._previous_pointer["model"]),
            int(cls._previous_pointer["dimensions"]),
        )

    @classmethod
    def _run_rows(cls, batch: str) -> list[dict[str, object]]:
        with cls.conn.cursor() as cur:
            cur.execute(
                """
                SELECT run_id, status, exit_code, counters
                  FROM platform.import_run
                 WHERE batch_id = %s
                 ORDER BY started_at, run_id
                """,
                (batch,),
            )
            rows = cur.fetchall()
        return [
            {"runId": str(row[0]), "status": row[1], "exitCode": row[2], "counters": row[3]}
            for row in rows
        ]

    @classmethod
    def _items(cls, batch: str) -> list[dict[str, object]]:
        with cls.conn.cursor() as cur:
            cur.execute(
                """
                SELECT rel_path, status, attempts, degraded, failure_code
                  FROM platform.import_item
                 WHERE batch_id = %s
                 ORDER BY rel_path
                """,
                (batch,),
            )
            rows = cur.fetchall()
        return [
            {
                "relPath": row[0],
                "status": row[1],
                "attempts": int(row[2]),
                "degraded": bool(row[3]),
                "failureCode": row[4],
            }
            for row in rows
        ]

    @classmethod
    def _failure_histogram(cls, batch: str) -> dict[str, int]:
        with cls.conn.cursor() as cur:
            cur.execute(
                "SELECT failure_code, COUNT(*) FROM platform.import_item "
                "WHERE batch_id = %s AND status = 'failed' GROUP BY 1",
                (batch,),
            )
            return {str(code): int(count) for code, count in cur.fetchall()}

    @classmethod
    def _documents(cls, shas: list[str]) -> list[dict[str, object]]:
        with cls.conn.cursor() as cur:
            cur.execute(
                "SELECT document_id, status FROM platform.document "
                "WHERE document_id = ANY(%s) ORDER BY document_id",
                (shas,),
            )
            rows = cur.fetchall()
        return [{"documentId": row[0], "status": row[1]} for row in rows]

    @classmethod
    def _counts(cls, batch: str, shas: list[str]) -> dict[str, int]:
        chunk = (
            "SELECT COUNT(*) FROM platform.document_chunk "
            "WHERE document_id = ANY(%s)"
        )
        return {
            "import_batch": cls._scalar(
                "SELECT COUNT(*) FROM platform.import_batch WHERE batch_id = %s",
                (batch,),
            ),
            "import_item": cls._scalar(
                "SELECT COUNT(*) FROM platform.import_item WHERE batch_id = %s",
                (batch,),
            ),
            "document": cls._scalar(
                "SELECT COUNT(*) FROM platform.document WHERE document_id = ANY(%s)",
                (shas,),
            ),
            "document_chunk": cls._scalar(chunk, (shas,)),
            "chunk_embedding": cls._scalar(
                "SELECT COUNT(*) FROM platform.chunk_embedding "
                "WHERE chunk_id IN (SELECT chunk_id FROM platform.document_chunk "
                "                   WHERE document_id = ANY(%s))",
                (shas,),
            ),
        }

    @classmethod
    def _delete_rows(cls, batches: list[str], shas: list[str]) -> None:
        """Leave the database as found; the CI database is disposable, a local
        one is not, and a leftover document would make the next first run look
        like a re-run."""
        with cls.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM platform.import_batch WHERE batch_id = ANY(%s)",
                (batches,),
            )
            cur.execute(
                "DELETE FROM platform.chunk_embedding WHERE chunk_id IN "
                "(SELECT chunk_id FROM platform.document_chunk "
                " WHERE document_id = ANY(%s))",
                (shas,),
            )
            cur.execute(
                "DELETE FROM platform.document_chunk WHERE document_id = ANY(%s)",
                (shas,),
            )
            cur.execute(
                "DELETE FROM platform.document WHERE document_id = ANY(%s)",
                (shas,),
            )

    # ---- scenario 1: three identical runs --------------------------------

    def test_reruns_open_their_own_run_row(self) -> None:
        self.assertEqual(len(self.repeat_run_rows), 3)
        run_ids = [str(row["runId"]) for row in self.repeat_run_rows]
        self.assertEqual(len(set(run_ids)), 3, f"run ids repeat: {run_ids}")
        for row in self.repeat_run_rows:
            self.assertEqual(row["status"], "completed")
        self.assertEqual(int(self.repeat_run_rows[0]["exitCode"]), 0)
        self.assertEqual(int(self.repeat_run_rows[1]["exitCode"]), 0)
        self.assertEqual(int(self.repeat_run_rows[2]["exitCode"]), 0)

    def test_first_run_indexes_the_whole_corpus(self) -> None:
        first = self.repeat_runs[0]["result"]
        self.assertEqual(self.repeat_runs[0]["exit"], 0)
        self.assertEqual(int(first["indexed"]), 3)
        self.assertEqual(int(first["failed"]), 0)
        self.assertEqual(int(first["alreadyDone"]), 0)
        self.assertEqual(self.repeat_counts[0]["import_batch"], 1)
        self.assertEqual(self.repeat_counts[0]["import_item"], 3)
        self.assertEqual(self.repeat_counts[0]["document"], 3)
        self.assertEqual(self.repeat_counts[0]["document_chunk"], 3)
        self.assertEqual(self.repeat_counts[0]["chunk_embedding"], 3)

    def test_reruns_add_no_rows_and_report_everything_done(self) -> None:
        for index in (1, 2):
            run = self.repeat_runs[index]
            self.assertEqual(run["exit"], 0)
            result = run["result"]
            self.assertEqual(int(result["indexed"]), 0, f"run {index + 1} reindexed")
            self.assertEqual(
                int(result["alreadyDone"]), 3, f"run {index + 1} alreadyDone"
            )
            self.assertEqual(int(result["failed"]), 0)
            self.assertEqual(int(result["failedThisRun"]), 0)
            self.assertEqual(int(result["documentsAdded"]), 0)
            # The ledger must tell the same story as the stdout JSON.
            ledger = self.repeat_run_rows[index]["counters"]
            self.assertEqual(int(ledger["total"]), 3)
            self.assertEqual(int(ledger["indexed"]), 0)
            self.assertEqual(int(ledger["alreadyDone"]), 3)

    def test_reruns_do_not_touch_the_five_tables(self) -> None:
        self.assertEqual(
            self.repeat_counts[1],
            self.repeat_counts[0],
            "the second run inserted rows",
        )
        self.assertEqual(
            self.repeat_counts[2],
            self.repeat_counts[0],
            "the third run inserted rows",
        )
        self.assertEqual(self.repeat_counts[2]["import_batch"], 1)

    def test_batch_is_completed_once_the_corpus_is_done(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT status FROM platform.import_batch WHERE batch_id = %s",
                (self.repeat_batch,),
            )
            row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "completed")
        repeat_items = self._items(self.repeat_batch)
        self.assertEqual([item["status"] for item in repeat_items], ["indexed"] * 3)

    # ---- scenario 2: outage, then retry ----------------------------------

    def test_embedding_outage_exits_non_zero_and_names_the_code(self) -> None:
        self.assertEqual(self.outage["exit"], 1)
        result = self.outage["result"]
        self.assertEqual(int(result["failed"]), 3)
        self.assertEqual(int(result["failedThisRun"]), 3)
        self.assertEqual(int(result["indexed"]), 0)
        self.assertEqual(int(result["documentsAdded"]), 3)
        self.assertIn("E_EMBED_UNAVAILABLE=3", self.outage["stderr"])
        self.assertEqual(self.outage_histogram, {"E_EMBED_UNAVAILABLE": 3})
        self.assertEqual([item["attempts"] for item in self.outage_items], [1, 1, 1])
        self.assertEqual([item["status"] for item in self.outage_items], ["failed"] * 3)
        self.assertEqual(
            [doc["status"] for doc in self.outage_documents], ["degraded"] * 3
        )
        run_rows = self.outage_runs
        self.assertEqual(len(run_rows), 1)
        self.assertEqual(run_rows[0]["status"], "completed")
        self.assertEqual(int(run_rows[0]["exitCode"]), 1)

    def test_retry_failed_recovers_the_batch(self) -> None:
        self.assertEqual(self.retry["exit"], 0)
        result = self.retry["result"]
        self.assertEqual(int(result["failed"]), 0)
        self.assertEqual(int(result["indexed"]), 3)
        self.assertEqual(result["failures"], [])
        self.assertEqual([item["status"] for item in self.retry_items], ["indexed"] * 3)
        self.assertEqual([item["attempts"] for item in self.retry_items], [2, 2, 2])
        self.assertEqual(
            [item["failureCode"] for item in self.retry_items], [None, None, None]
        )
        # The retry really embedded: every chunk has a vector in the active
        # partition, so the document is parsed, not degraded.
        self.assertEqual(
            [doc["status"] for doc in self.retry_documents], ["parsed"] * 3
        )
        self.assertEqual(
            self._counts(
                self.outage_batch,
                self.retry_shas,
            )["chunk_embedding"],
            3,
        )
        run_rows = self._run_rows(self.outage_batch)
        self.assertEqual(len(run_rows), 2, "the retry must open its own run row")
        self.assertEqual(run_rows[1]["status"], "completed")
        self.assertEqual(int(run_rows[1]["exitCode"]), 0)

    def test_retry_clears_the_item_degraded_flag(self) -> None:
        self.assertEqual(
            [item["degraded"] for item in self.retry_items], [False, False, False]
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
