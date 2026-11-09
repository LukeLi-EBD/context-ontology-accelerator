"""Unit tests for migration bundle verification (no DB / no graph writes)."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np

from platform_core import bundle
from platform_core.adapters.metadata_pg import SUPPORTED_SCHEMA_VERSION
from platform_core.errors import PortError


def _entry(root: Path, rel: str, kind: str, records: int | None = None) -> dict:
    return bundle._file_entry(root, rel, kind, records)


def _write_bundle(root: Path, *, dim: int = 1024, rows: int = 1) -> dict:
    (root / "graph").mkdir(parents=True)
    (root / "meta").mkdir()
    (root / "vectors").mkdir()
    (root / "ledger").mkdir()

    (root / "graph/tbox.ttl").write_text("<urn:s> <urn:p> <urn:o> .\n", encoding="utf-8")
    (root / "graph/abox.ttl").write_text("<urn:a> <urn:p> <urn:b> .\n", encoding="utf-8")
    (root / "graph/shapes.ttl").write_text("# shapesId=core\n<urn:s> <urn:p> <urn:o> .\n", encoding="utf-8")
    (root / "meta/ontology_import.jsonl").write_text("", encoding="utf-8")
    (root / "meta/documents.jsonl").write_text("", encoding="utf-8")
    chunks = [json.dumps({"chunk_id": f"c{index}", "document_id": "d1", "text": "hello"}) for index in range(rows)]
    (root / "meta/chunks.jsonl").write_text("\n".join(chunks) + "\n", encoding="utf-8")
    ids = np.array([f"c{index}" for index in range(rows)], dtype="<U8")
    np.savez(root / "vectors/embeddings.npz", chunk_ids=ids, embeddings=np.ones((rows, dim), dtype=np.float32))
    (root / "vectors/README").write_text("model=BAAI/bge-m3\ndimensions=1024\n", encoding="utf-8")
    (root / "ledger/fact_events.jsonl").write_text("", encoding="utf-8")
    (root / "ledger/verify.json").write_text('{"ok": true}', encoding="utf-8")

    files = [
        _entry(root, "graph/tbox.ttl", "ttl"),
        _entry(root, "graph/abox.ttl", "ttl"),
        _entry(root, "graph/shapes.ttl", "ttl"),
        _entry(root, "meta/ontology_import.jsonl", "jsonl", 0),
        _entry(root, "meta/documents.jsonl", "jsonl", 0),
        _entry(root, "meta/chunks.jsonl", "jsonl", rows),
        _entry(root, "vectors/embeddings.npz", "npz", rows),
        _entry(root, "vectors/README", "text"),
        _entry(root, "ledger/fact_events.jsonl", "jsonl", 0),
        _entry(root, "ledger/verify.json", "json"),
    ]
    manifest = {
        "bundleVersion": 1,
        "schemaVersion": SUPPORTED_SCHEMA_VERSION,
        "tag": "v1-test",
        "generatedAt": "2026-11-05T00:00:00+08:00",
        "source": {
            "tbox": {"versionId": "ont-x", "semver": "1.0.0", "contentHash": "0" * 64, "graph": "urn:g"},
            "embedding": {"provider": "local-bge", "model": "BAAI/bge-m3", "dimensions": 1024},
            "shapes": [],
        },
        "totals": {
            "documents": 0, "chunks": rows, "embeddings": rows,
            "triples": 2, "factEvents": 0, "factAssertions": 0,
        },
        "files": files,
    }
    (root / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


class BundleVerifyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="bundle-test-"))
        self.root = self.tmp / "v1-test"
        self.manifest = _write_bundle(self.root)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_ok(self) -> None:
        manifest = bundle.verify_bundle(self.root)
        self.assertEqual(manifest["tag"], "v1-test")

    def test_sha_mismatch(self) -> None:
        (self.root / "graph/tbox.ttl").write_text("<urn:s> <urn:p> <urn:x> .\n", encoding="utf-8")
        with self.assertRaises(PortError) as ctx:
            bundle.verify_bundle(self.root)
        self.assertEqual(ctx.exception.provider_code, "E_BUNDLE_SHA")

    def test_schema_version_mismatch(self) -> None:
        self.manifest["schemaVersion"] = 99
        (self.root / "MANIFEST.json").write_text(json.dumps(self.manifest), encoding="utf-8")
        with self.assertRaises(PortError) as ctx:
            bundle.verify_bundle(self.root)
        self.assertEqual(ctx.exception.provider_code, "E_BUNDLE_SCHEMA_MISMATCH")

    def test_missing_file(self) -> None:
        (self.root / "graph/tbox.ttl").unlink()
        with self.assertRaises(PortError) as ctx:
            bundle.verify_bundle(self.root)
        self.assertEqual(ctx.exception.provider_code, "E_BUNDLE_MISSING")

    def test_vector_dimension_mismatch(self) -> None:
        np.savez(
            self.root / "vectors/embeddings.npz",
            chunk_ids=np.array(["c0"], dtype="<U8"),
            embeddings=np.ones((1, 8), dtype=np.float32),
        )
        self.manifest = _write_manifest(self.root, self.manifest)
        with self.assertRaises(PortError) as ctx:
            bundle.verify_bundle(self.root)
        self.assertEqual(ctx.exception.provider_code, "E_BUNDLE_VECTOR_DIM")


def _write_manifest(root: Path, manifest: dict) -> dict:
    manifest["files"] = [
        _entry(root, "graph/tbox.ttl", "ttl"),
        _entry(root, "graph/abox.ttl", "ttl"),
        _entry(root, "graph/shapes.ttl", "ttl"),
        _entry(root, "meta/ontology_import.jsonl", "jsonl", 0),
        _entry(root, "meta/documents.jsonl", "jsonl", 0),
        _entry(root, "meta/chunks.jsonl", "jsonl", 1),
        _entry(root, "vectors/embeddings.npz", "npz", 1),
        _entry(root, "vectors/README", "text"),
        _entry(root, "ledger/fact_events.jsonl", "jsonl", 0),
        _entry(root, "ledger/verify.json", "json"),
    ]
    (root / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


class _FakeGraph:
    def __init__(self) -> None:
        self.cleared: list[str] = []

    def clear_graph(self, graph_iri: str) -> None:
        self.cleared.append(graph_iri)


class RestoreCleanupTests(unittest.TestCase):
    """OQ-69 regression: cleanup must only delete urn:platform:graph:restore:*."""

    def test_only_restore_graphs_deleted(self) -> None:
        restore = [
            "urn:platform:graph:restore:v1:abox",
            "urn:platform:graph:restore:v2:abox",
            "urn:platform:graph:restore:v1:tbox",
        ]
        history = [
            "urn:platform:graph:tbox:ont-f413054a0c72",
            "urn:platform:inferred:ont-f413054a0c72",
        ]
        graph = _FakeGraph()
        result = bundle.cleanup_restore_graphs(graph, restore + history)
        self.assertEqual(result["count"], 3)
        self.assertEqual(sorted(result["deleted"]), sorted(restore))
        self.assertEqual(sorted(graph.cleared), sorted(restore))
        self.assertFalse(set(graph.cleared) & set(history))

    def test_keep_list_is_honoured(self) -> None:
        iris = [
            "urn:platform:graph:restore:v1:abox",
            "urn:platform:graph:restore:v2:abox",
        ]
        graph = _FakeGraph()
        result = bundle.cleanup_restore_graphs(graph, iris, keep=iris[:1])
        self.assertEqual(result["deleted"], iris[1:])


class MetricDefinitionRegistryTest(unittest.TestCase):
    """指标注册表随 bundle 迁移：hash 覆盖的字段必须被导出携带，且不许静默补默认值。"""

    def _row(self, **overrides: object) -> dict:
        row = {name: None for name in bundle._METRIC_DEF_COLUMNS}
        row.update(
            {
                "metric_id": "CUST-001",
                "name_zh": "RFM-R",
                "domain": "customer",
                "evidence_basis": "industry",
                "publishable": False,
                "inference": True,
                "formula_disabled": False,
                "evidence_status": "INDUSTRY_ONLY",
                "definition_version": "v3.0",
                "metric_kind": "duration",
                "formula_expr": "numerator",
                "numerator_agg": "max",
                "window_kind": "instant",
                "min_window_days": 0,
                "grain": "customer",
                "unit": "天",
                "aggregation_semantics": "sum",
                "updated_at": "2026-11-09T17:10:47.742102+00:00",
            }
        )
        row.update(overrides)
        return row

    def test_hash_ignores_updated_at(self) -> None:
        base = self._row()
        moved = self._row(updated_at="2026-11-10T00:00:00+00:00")
        self.assertEqual(
            bundle._metric_def_hash([base]), bundle._metric_def_hash([moved])
        )

    def test_hash_covers_aggregation_semantics(self) -> None:
        # 回归：导出曾漏掉这一列，85/85 条全对但 hash 判不等。
        self.assertNotEqual(
            bundle._metric_def_hash([self._row()]),
            bundle._metric_def_hash([self._row(aggregation_semantics="distinct_count")]),
        )

    def test_hash_is_order_independent(self) -> None:
        first, second = self._row(), self._row(metric_id="CUST-002")
        self.assertEqual(
            bundle._metric_def_hash([first, second]),
            bundle._metric_def_hash([second, first]),
        )

    def test_params_reject_row_without_aggregation_semantics(self) -> None:
        row = self._row()
        row.pop("aggregation_semantics")
        with self.assertRaises(PortError) as ctx:
            bundle._metric_def_params(row)
        self.assertEqual(ctx.exception.provider_code, "E_BUNDLE_METRIC_DEF_INCOMPLETE")

    def test_params_carry_aggregation_semantics(self) -> None:
        params = bundle._metric_def_params(
            self._row(aggregation_semantics="distinct_count")
        )
        index = bundle._METRIC_DEF_COLUMNS.index("aggregation_semantics")
        self.assertEqual(params[index], "distinct_count")


if __name__ == "__main__":
    unittest.main()
