"""P1 regressions: import batch creation order and the per-run ledger.

Needs a disposable PostgreSQL with the platform schema; point ``TEST_PG_DSN``
at it (same convention as the other DB-backed platform-core tests). Every row
the tests create is removed in ``tearDown``.

Covered behaviour:
  * a call rejected by the `platform:heavy` lock writes no `import_batch` or
    `import_run` row (the ghost-batch regression);
  * once the lock is free, a normal call creates the batch and closes both the
    batch and its `import_run` row as completed;
  * the ledger records completed counters, failed runs with their error code,
    and closes a run abandoned by a dead process as interrupted;
  * a run that lands `failed` closes its batch in the same transaction, so the
    batch never keeps showing "running" after the run is dead.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace

import psycopg

from platform_core.adapters.metadata_pg import MetadataPg
from platform_core.errors import PortError
from platform_core.importer import Importer

DSN = os.environ.get("TEST_PG_DSN")
NAMESPACE = uuid.UUID("00000000-0000-0000-0000-0000000000a1")
MODEL = "p1-ledger-test"
_VECTOR = "[" + ",".join(["0.0"] * 1024) + "]"


class _Documents:
    """Minimal stand-in for DocumentService: one chunk, one embedding.

    `_embedded_documents` counts a document as indexed only when it has a chunk
    and that chunk has a vector, so the stub writes exactly those rows.
    """

    def __init__(self, meta: MetadataPg, shas: set[str]) -> None:
        self._meta = meta
        self._shas = shas

    def ingest_path(self, path, name, meta):  # noqa: ANN001, ARG002
        data = Path(path).read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        text = data.decode("utf-8")
        self._shas.add(sha)
        self._meta.execute(
            "INSERT INTO platform.document (document_id, sha256, bucket, object_key, "
            "filename, mime_type, size_bytes, status, parser, parser_version) "
            "VALUES (%s, %s, 'test', %s, %s, 'text/plain', %s, 'parsed', 'stub', '0') "
            "ON CONFLICT (document_id) DO NOTHING",
            (sha, sha, str(path), name, len(data)),
        )
        chunk_id = f"{sha}:0"
        self._meta.execute(
            "INSERT INTO platform.document_chunk (chunk_id, document_id, seq, page_from, "
            "page_to, char_start, char_end, text, token_estimate) "
            "VALUES (%s, %s, 0, 1, 1, 0, %s, %s, 4) ON CONFLICT (chunk_id) DO NOTHING",
            (chunk_id, sha, len(text), text),
        )
        self._meta.execute(
            "INSERT INTO platform.chunk_embedding (chunk_id, model, dimensions, embedding) "
            "VALUES (%s, %s, 1024, %s::vector) ON CONFLICT (chunk_id, model) DO NOTHING",
            (chunk_id, MODEL, _VECTOR),
        )
        return {"documentId": sha, "ingested": True, "deduplicated": False, "degraded": False}


class _BoomOnItems:
    """Metadata proxy that fails the first import_item read.

    Per-file parse/embed errors are isolated and recorded as item failures, so
    they never fail the run. An infrastructure error during the run is what the
    `failed` ledger status covers; this proxy simulates one after the run row
    and the batch row already exist.
    """

    def __init__(self, meta: MetadataPg) -> None:
        self._meta = meta

    def __getattr__(self, name):
        return getattr(self._meta, name)

    def query(self, sql, params=()):
        if "FROM platform.import_item" in sql:
            raise PortError(
                code="Internal",
                message="forced infrastructure failure",
                provider="test",
                provider_code="E_TEST_BOOM",
            )
        return self._meta.query(sql, params)

    def execute(self, sql, params=()):
        return self._meta.execute(sql, params)


@unittest.skipUnless(DSN, "TEST_PG_DSN not set; refusing to fall back to PLATFORM__DATABASE__URL")
class ImportRunLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = MetadataPg(DSN)
        cls.meta.open(retry_seconds=15)
        cls.meta.migrate()

    @classmethod
    def tearDownClass(cls):
        cls.meta.close()

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="p1-import-test-"))
        self._batch_ids: set[str] = set()
        self._shas: set[str] = set()

    def tearDown(self):
        for batch_id in self._batch_ids:
            self.meta.execute(
                "DELETE FROM platform.import_batch WHERE batch_id = %s", (batch_id,)
            )
        for sha in self._shas:
            self.meta.execute(
                "DELETE FROM platform.chunk_embedding WHERE chunk_id LIKE %s", (sha + "%",)
            )
            self.meta.execute(
                "DELETE FROM platform.document_chunk WHERE document_id = %s", (sha,)
            )
            self.meta.execute(
                "DELETE FROM platform.document WHERE document_id = %s", (sha,)
            )
        shutil.rmtree(self._tmp, ignore_errors=True)

    # ---- helpers -------------------------------------------------------

    def _importer(self, documents=None, metadata=None, search=None):
        runtime = SimpleNamespace(
            metadata=metadata or self.meta,
            documents=documents or _Documents(self.meta, self._shas),
            search=search
            or SimpleNamespace(
                index_document=lambda document_id: {"embedded": 1, "degraded": False}
            ),
            vectors=SimpleNamespace(pointer=lambda: {"model": MODEL}),
            config=SimpleNamespace(
                data_dir=str(self._tmp / "_data"),
                storage=SimpleNamespace(
                    root=str(self._tmp / "_data"),
                    tmp_dir=str(self._tmp / "_data" / "tmp"),
                ),
                documents=SimpleNamespace(max_upload_bytes=10 * 1024 * 1024),
            ),
        )
        return Importer(
            runtime,
            parse_concurrency=1,
            embed_concurrency=1,
            progress_seconds=0,
            max_files=0,
            max_seconds=0,
        )

    def _write_doc(self, name: str = "a.txt") -> str:
        text = f"p1 ledger regression {uuid.uuid4().hex}\n"
        (self._tmp / name).write_text(text, encoding="utf-8")
        sha = hashlib.sha256(text.encode()).hexdigest()
        self._shas.add(sha)
        return sha

    def _root(self) -> str:
        return str(self._tmp.resolve())

    def _batch_count(self) -> int:
        return int(
            self.meta.query(
                "SELECT count(*) AS n FROM platform.import_batch WHERE root_path = %s",
                (self._root(),),
            )[0]["n"]
        )

    def _run_count(self) -> int:
        return int(
            self.meta.query(
                "SELECT count(*) AS n FROM platform.import_run r "
                "JOIN platform.import_batch b USING (batch_id) WHERE b.root_path = %s",
                (self._root(),),
            )[0]["n"]
        )

    # ---- 0) fresh host --------------------------------------------------

    def test_import_creates_missing_storage_dirs(self):
        """The import CLI skips the serve-time IO self-check.

        Without creating these dirs first, the staging write
        (tmp_dir/ingest-*.part) raises FileNotFoundError and every item lands
        as E_IMPORT_UNEXPECTED, so a first import on a fresh host cannot run.
        """
        self._write_doc()
        data_root = self._tmp / "_data"
        self.assertFalse(data_root.exists())
        result = self._importer().run(str(self._tmp), namespace_id=NAMESPACE)
        self._batch_ids.add(result["batchId"])
        self.assertEqual(result["indexed"], 1)
        self.assertEqual(result["failed"], 0)
        for path in (data_root, data_root / "blobs", data_root / "tmp"):
            self.assertTrue(path.is_dir(), f"{path} not created")

    # ---- 2) recovery ----------------------------------------------------

    def test_retried_file_drops_stale_failure_code(self):
        """A recovered file must not keep reporting its old failure reason.

        Readers filter and export `import_item.failure_code`; leaving it set
        after a successful retry reports a healthy document as failed.
        """
        sha = self._write_doc()
        degraded = SimpleNamespace(
            index_document=lambda document_id: {
                "embedded": 0,
                "degraded": True,
                "failureCode": "E_EMBED_UNAVAILABLE",
                "reasons": ["E_EMBED_UNAVAILABLE"],
            }
        )
        first = self._importer(search=degraded).run(
            str(self._tmp), namespace_id=NAMESPACE
        )
        self._batch_ids.add(first["batchId"])
        self.assertEqual(first["failedThisRun"], 1)
        batch_id = uuid.UUID(first["batchId"])
        before = self.meta.query(
            "SELECT status, attempts, failure_code FROM platform.import_item "
            "WHERE batch_id = %s",
            (batch_id,),
        )[0]
        self.assertEqual(before["status"], "failed")
        self.assertEqual(before["attempts"], 1)
        self.assertEqual(before["failure_code"], "E_EMBED_UNAVAILABLE")

        # The failed embed left no vector behind; drop the stub's placeholder so
        # the retry must index for real instead of passing the done-check.
        self.meta.execute(
            "DELETE FROM platform.chunk_embedding WHERE chunk_id IN "
            "(SELECT chunk_id FROM platform.document_chunk WHERE document_id = %s)",
            (sha,),
        )

        second = self._importer().run(
            str(self._tmp), namespace_id=NAMESPACE, retry_failed=True
        )
        self.assertEqual(second["batchId"], first["batchId"])
        self.assertEqual(second["indexed"], 1)
        after = self.meta.query(
            "SELECT status, attempts, failure_code, failure_message "
            "FROM platform.import_item WHERE batch_id = %s",
            (batch_id,),
        )[0]
        self.assertEqual(after["status"], "indexed")
        self.assertEqual(after["attempts"], 2)
        self.assertIsNone(after["failure_code"])
        self.assertIsNone(after["failure_message"])

    def test_partial_failure_exits_non_zero(self):
        """Automation needs a hard signal; parsing stdout is not one."""
        self._write_doc()
        degraded = SimpleNamespace(
            index_document=lambda document_id: {
                "embedded": 0,
                "degraded": True,
                "failureCode": "E_EMBED_UNAVAILABLE",
                "reasons": ["E_EMBED_UNAVAILABLE"],
            }
        )
        result = self._importer(search=degraded).run(
            str(self._tmp), namespace_id=NAMESPACE
        )
        self._batch_ids.add(result["batchId"])
        self.assertEqual(result["failedThisRun"], 1)
        self.assertEqual(result["exitCode"], 1)
        run = self.meta.query(
            "SELECT exit_code FROM platform.import_run WHERE batch_id = %s",
            (uuid.UUID(result["batchId"]),),
        )[0]
        self.assertEqual(run["exit_code"], 1)
        from platform_core.importer import failure_code_counts

        self.assertEqual(
            failure_code_counts(
                SimpleNamespace(metadata=self.meta), uuid.UUID(result["batchId"])
            ),
            {"E_EMBED_UNAVAILABLE": 1},
        )

    # ---- 1) ghost batch ------------------------------------------------

    def test_rejected_when_heavy_lock_held_writes_no_rows(self):
        self._write_doc()
        importer = self._importer()
        holder = psycopg.connect(DSN, autocommit=True)
        try:
            holder.execute("SELECT pg_advisory_lock(hashtext('platform:heavy'))")
            for _ in range(10):
                with self.assertRaises(PortError) as ctx:
                    importer.run(str(self._tmp), namespace_id=NAMESPACE)
                self.assertEqual(ctx.exception.provider_code, "E_HEAVY_BUSY")
            self.assertEqual(self._batch_count(), 0)
            self.assertEqual(self._run_count(), 0)
        finally:
            holder.execute("SELECT pg_advisory_unlock(hashtext('platform:heavy'))")
            holder.close()

    def test_run_after_lock_release_creates_completed_batch(self):
        self._write_doc()
        importer = self._importer()
        result = importer.run(str(self._tmp), namespace_id=NAMESPACE)
        self._batch_ids.add(result["batchId"])

        batch = self.meta.query(
            "SELECT status, namespace_id, finished_at FROM platform.import_batch "
            "WHERE batch_id = %s",
            (result["batchId"],),
        )[0]
        self.assertEqual(batch["status"], "completed")
        self.assertEqual(str(batch["namespace_id"]), str(NAMESPACE))
        self.assertIsNotNone(batch["finished_at"])
        self.assertEqual(self._batch_count(), 1)
        self.assertEqual(self._run_count(), 1)

    # ---- 2) run ledger -------------------------------------------------

    def test_completed_run_records_counters(self):
        self._write_doc()
        result = self._importer().run(str(self._tmp), namespace_id=NAMESPACE)
        self._batch_ids.add(result["batchId"])

        run = self.meta.query(
            "SELECT status, exit_code, error_code, counters FROM platform.import_run "
            "WHERE run_id = %s",
            (result["runId"],),
        )[0]
        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["exit_code"], 0)
        self.assertIsNone(run["error_code"])
        self.assertEqual(int(run["counters"]["total"]), 1)
        self.assertEqual(int(run["counters"]["indexed"]), 1)
        self.assertEqual(int(run["counters"]["failedThisRun"]), 0)

    def test_failed_run_records_status_and_error_code(self):
        self._write_doc()
        importer = self._importer(metadata=_BoomOnItems(self.meta))
        with self.assertRaises(PortError):
            importer.run(str(self._tmp), namespace_id=NAMESPACE)

        runs = self.meta.query(
            "SELECT r.run_id, r.status, r.exit_code, r.error_code, r.error_message, "
            "r.counters, r.batch_id FROM platform.import_run r "
            "JOIN platform.import_batch b USING (batch_id) WHERE b.root_path = %s",
            (self._root(),),
        )
        self.assertEqual(len(runs), 1)
        self._batch_ids.add(str(runs[0]["batch_id"]))
        self.assertEqual(runs[0]["status"], "failed")
        self.assertEqual(runs[0]["error_code"], "E_TEST_BOOM")
        self.assertIn("forced infrastructure failure", runs[0]["error_message"])
        self.assertIsNone(runs[0]["exit_code"])
        self.assertEqual(runs[0]["counters"], {})

    def test_failed_run_closes_batch_as_interrupted(self):
        """A dead run must not leave the batch showing "running".

        The batch row has no error column, so the reason travels in
        `options.lastError`; assert it is present, not blank.
        """
        self._write_doc()
        importer = self._importer(metadata=_BoomOnItems(self.meta))
        with self.assertRaises(PortError):
            importer.run(str(self._tmp), namespace_id=NAMESPACE)

        row = self.meta.query(
            "SELECT b.batch_id, b.status, b.finished_at, b.options "
            "FROM platform.import_batch b "
            "JOIN platform.import_run r USING (batch_id) "
            "WHERE b.root_path = %s",
            (self._root(),),
        )[0]
        self._batch_ids.add(str(row["batch_id"]))
        self.assertEqual(row["status"], "interrupted")
        self.assertIsNotNone(row["finished_at"])
        last_error = row["options"].get("lastError") or {}
        self.assertEqual(last_error.get("code"), "E_TEST_BOOM")
        self.assertTrue(str(last_error.get("message") or "").strip())

    def test_next_run_closes_abandoned_running_row_as_interrupted(self):
        self._write_doc()
        importer = self._importer()
        first = importer.run(str(self._tmp), namespace_id=NAMESPACE)
        self._batch_ids.add(first["batchId"])

        stale_id = uuid.uuid4()
        self.meta.execute(
            "INSERT INTO platform.import_run "
            "(run_id, batch_id, namespace_id, status, started_at, options, counters) "
            "VALUES (%s, %s, %s, 'running', now() - interval '1 hour', '{}'::jsonb, "
            "'{}'::jsonb)",
            (stale_id, first["batchId"], NAMESPACE),
        )

        second = importer.run(str(self._tmp), namespace_id=NAMESPACE)
        self.assertEqual(second["batchId"], first["batchId"])

        stale = self.meta.query(
            "SELECT status, error_code, finished_at FROM platform.import_run "
            "WHERE run_id = %s",
            (stale_id,),
        )[0]
        self.assertEqual(stale["status"], "interrupted")
        self.assertEqual(stale["error_code"], "E_RUN_ABANDONED")
        self.assertIsNotNone(stale["finished_at"])


if __name__ == "__main__":
    unittest.main()
