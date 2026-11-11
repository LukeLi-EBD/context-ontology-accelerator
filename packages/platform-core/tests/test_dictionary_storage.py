"""P4 字典存储（V48）集成测试。

需要 TEST_PG_DSN 指向一个可迁移的 PostgreSQL 库；未设置时整类跳过。
每个用例使用独立 namespace_id，结束时按外键顺序清理自建数据。
"""

from __future__ import annotations

import os
import sys
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, "/app/src")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_core.adapters.dictionary_pg import (
    DictionaryColumnInput,
    DictionaryError,
    DictionaryPg,
)
from platform_core.adapters.metadata_pg import MetadataPg

DSN = os.environ.get("TEST_PG_DSN")


def _column(
    table: str = "orders",
    column: str = "amount",
    *,
    data_type: str = "numeric(18,2)",
    is_nullable: bool = True,
    comment: str | None = "订单金额",
    source_kind: str = "postgresql",
    property_iri: str | None = None,
    binding_method: str = "none",
    confidence: float | None = None,
    binding_note: str | None = None,
) -> DictionaryColumnInput:
    return DictionaryColumnInput(
        catalog="analytics",
        schema="public",
        table=table,
        column=column,
        data_type=data_type,
        is_nullable=is_nullable,
        source_kind=source_kind,
        comment=comment,
        property_iri=property_iri,
        binding_method=binding_method,
        confidence=confidence,
        binding_note=binding_note,
    )


@unittest.skipUnless(DSN, "TEST_PG_DSN not set")
class DictionaryStorageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.meta = MetadataPg(DSN)
        cls.meta.open()
        cls.meta.migrate()
        cls.store = DictionaryPg(cls.meta)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.meta.close()

    def setUp(self) -> None:
        self.namespace = f"test-{uuid.uuid4().hex}"
        self.source = "source-1"

    def tearDown(self) -> None:
        self.meta.execute(
            "DELETE FROM platform.dictionary_column WHERE namespace_id = %s",
            (self.namespace,),
        )
        self.meta.execute(
            "DELETE FROM platform.dictionary_refresh_run WHERE namespace_id = %s",
            (self.namespace,),
        )

    def _run(self, key: str, columns: list[DictionaryColumnInput]) -> tuple[dict, dict]:
        run = self.store.begin_refresh(self.namespace, self.source, key, requested_by="test")
        counts = self.store.upsert_snapshot(self.namespace, self.source, run["runId"], columns)
        finished = self.store.finish_refresh(run["runId"], status="succeeded", **counts)
        return finished, counts

    def test_refresh_key_is_idempotent(self) -> None:
        first, counts = self._run("k1", [_column(), _column(column="paid_at", data_type="timestamptz")])
        self.assertEqual(counts["inserted"], 2)
        self.assertEqual(counts["unchanged"], 0)

        replay = self.store.begin_refresh(self.namespace, self.source, "k1")
        self.assertFalse(replay["created"])
        self.assertEqual(replay["runId"], first["runId"])
        self.assertEqual(replay["status"], "succeeded")

        second, counts2 = self._run("k2", [_column(), _column(column="paid_at", data_type="timestamptz")])
        self.assertNotEqual(second["runId"], first["runId"])
        self.assertEqual(counts2["inserted"], 0)
        self.assertEqual(counts2["updated"], 0)
        self.assertEqual(counts2["unchanged"], 2)
        self.assertEqual(self.store.list_columns(self.namespace)["total"], 2)

    def test_manual_binding_survives_refresh(self) -> None:
        self._run("k1", [_column(binding_method="explicit", property_iri="p:auto", confidence=0.9)])
        self.meta.execute(
            "UPDATE platform.dictionary_column SET binding_method = 'manual', "
            "property_iri = 'p:manual', binding_note = 'operator' "
            "WHERE namespace_id = %s",
            (self.namespace,),
        )
        _, counts = self._run(
            "k2",
            [_column(comment="新注释", binding_method="name_match", property_iri="p:auto2", confidence=0.5)],
        )
        self.assertEqual(counts["updated"], 1)
        item = self.store.table_columns(self.namespace, table="orders")[0]
        self.assertEqual(item["bindingMethod"], "manual")
        self.assertEqual(item["propertyIri"], "p:manual")
        self.assertEqual(item["bindingNote"], "operator")
        self.assertEqual(item["comment"], "新注释")

    def test_namespace_isolation_and_scope_mismatch(self) -> None:
        other = f"test-{uuid.uuid4().hex}"
        try:
            self._run("k1", [_column()])
            self.store.begin_refresh(other, self.source, "k-other")
            self.store.upsert_snapshot(other, self.source, self.store.begin_refresh(other, self.source, "k-other2")["runId"], [_column(column="other_col")])
            self.assertEqual(self.store.list_columns(self.namespace)["total"], 1)
            self.assertEqual(self.store.list_columns(other)["total"], 1)
            self.assertEqual(self.store.list_columns(self.namespace)["items"][0]["column"], "amount")

            run = self.store.begin_refresh(self.namespace, self.source, "k-scope")
            with self.assertRaises(DictionaryError) as ctx:
                self.store.upsert_snapshot(other, self.source, run["runId"], [_column()])
            self.assertEqual(ctx.exception.provider_code, "E_REFRESH_SCOPE_MISMATCH")
        finally:
            self.meta.execute(
                "DELETE FROM platform.dictionary_column WHERE namespace_id = %s", (other,)
            )
            self.meta.execute(
                "DELETE FROM platform.dictionary_refresh_run WHERE namespace_id = %s", (other,)
            )

    def test_filters_and_pagination(self) -> None:
        columns = [
            _column(comment=None),
            _column(column="paid_at", data_type="timestamptz", comment="支付时间"),
            _column(table="customers", column="name", data_type="text", comment="客户名",
                    binding_method="explicit", property_iri="c:name", confidence=1.0),
        ]
        self._run("k1", columns)

        self.assertEqual(self.store.list_columns(self.namespace)["total"], 3)
        self.assertEqual(
            self.store.list_columns(self.namespace, table="orders")["total"], 2
        )
        self.assertEqual(
            self.store.list_columns(self.namespace, binding_method="explicit")["total"], 1
        )
        self.assertEqual(
            self.store.list_columns(self.namespace, view="missing_comment")["total"], 1
        )
        self.assertEqual(
            self.store.list_columns(self.namespace, view="unbound")["total"], 2
        )
        self.assertEqual(
            self.store.list_columns(self.namespace, q="支付")["total"], 1
        )

        page = self.store.list_columns(self.namespace, limit=1, offset=1)
        self.assertEqual(page["total"], 3)
        self.assertEqual(len(page["items"]), 1)
        self.assertEqual(page["limit"], 1)
        self.assertEqual(page["offset"], 1)

        mappable = self.store.list_columns(
            self.namespace,
            view="mappable_unbound",
            mappable_pairs=[("orders", "amount")],
        )
        self.assertEqual(mappable["total"], 1)
        self.assertEqual(mappable["items"][0]["column"], "amount")

        with self.assertRaises(DictionaryError) as ctx:
            self.store.list_columns(self.namespace, view="mappable_unbound")
        self.assertEqual(ctx.exception.provider_code, "E_MAPPABLE_PAIRS_REQUIRED")

    def test_comment_coverage(self) -> None:
        self._run(
            "k1",
            [
                _column(comment="有注释"),
                _column(column="paid_at", data_type="timestamptz", comment=None),
                _column(column="memo", data_type="text", comment="   "),
            ],
        )
        coverage = self.store.comment_coverage(self.namespace)
        self.assertEqual(coverage["total"], 3)
        self.assertEqual(coverage["commented"], 1)
        self.assertEqual(coverage["missing"], 2)
        self.assertAlmostEqual(coverage["ratio"], 1 / 3)
        self.assertEqual(coverage["tables"][0]["table"], "orders")

        empty = self.store.comment_coverage(f"test-{uuid.uuid4().hex}")
        self.assertEqual(empty["total"], 0)
        self.assertIsNone(empty["ratio"])

    def test_explicit_failures(self) -> None:
        with self.assertRaises(DictionaryError):
            self.store.begin_refresh("  ", self.source, "k")
        with self.assertRaises(DictionaryError):
            self.store.begin_refresh(self.namespace, self.source, "")
        with self.assertRaises(DictionaryError):
            self.store.list_columns(self.namespace, limit=0)
        with self.assertRaises(DictionaryError):
            self.store.list_columns(self.namespace, view="nope")

        run = self.store.begin_refresh(self.namespace, self.source, "k1")
        with self.assertRaises(DictionaryError) as ctx:
            self.store.finish_refresh(run["runId"], status="failed")
        self.assertEqual(ctx.exception.provider_code, "E_DICTIONARY_INVALID")

        with self.assertRaises(DictionaryError) as ctx:
            self.store.upsert_snapshot(
                self.namespace, self.source, run["runId"], [_column(), _column()]
            )
        self.assertEqual(ctx.exception.provider_code, "E_DUPLICATE_COLUMN")

        with self.assertRaises(DictionaryError):
            self.store.upsert_snapshot(
                self.namespace, self.source, run["runId"], [_column(data_type="")]
            )

        self.store.finish_refresh(run["runId"], status="failed", error="introspection failed")
        failed = self.store.begin_refresh(self.namespace, self.source, "k1")
        self.assertFalse(failed["created"])
        self.assertEqual(failed["status"], "failed")
        with self.assertRaises(DictionaryError) as ctx:
            self.store.upsert_snapshot(self.namespace, self.source, run["runId"], [_column()])
        self.assertEqual(ctx.exception.provider_code, "E_REFRESH_NOT_RUNNING")

    def test_unknown_run_is_explicit(self) -> None:
        with self.assertRaises(DictionaryError) as ctx:
            self.store.upsert_snapshot(self.namespace, self.source, "missing", [_column()])
        self.assertEqual(ctx.exception.provider_code, "E_REFRESH_RUN_MISSING")


if __name__ == "__main__":
    unittest.main()
