"""Unit tests for migration bundle verification (no DB / no graph writes)."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np

from platform_core import bundle
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
        "schemaVersion": 17,
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


if __name__ == "__main__":
    unittest.main()
