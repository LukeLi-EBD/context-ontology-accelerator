"""O-06 health & diff enhancement tests: aggregation, snapshots, empty states."""

from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient

sys.path.insert(0, "/hostsrc")
sys.path.insert(0, "../src")

import platform_core.api as api_module
from platform_core import healthboard

CLASS_A = "urn:onto#LoanAccount"
CLASS_B = "urn:onto#Collateral"
PROP_1 = "urn:onto#principalAmount"
PROP_2 = "urn:onto#collateralType"


def _row(**values):
    return {"values": values}


def _iri(value):
    return {"kind": "iri", "iri": value}


def _lit(value):
    return {"kind": "literal", "value": value}


class FakeGraph:
    def __init__(self, *, changes=True, abox=True):
        self.changes = changes
        self.abox = abox
        self.queries: list[str] = []

    def query(self, sparql):
        self.queries.append(sparql)
        if "GROUP BY ?s ?p" in sparql:
            if not self.changes:
                return {"bindings": []}
            if sparql.index("GRAPH <urn:g:new>") < sparql.index("MINUS"):
                return {"bindings": [
                    _row(s=_iri(CLASS_A), p=_iri(PROP_1), n=_lit(3)),
                    _row(s=_iri(PROP_2), p=_iri("urn:r#range"), n=_lit(1)),
                ]}
            return {"bindings": [
                _row(s=_iri(CLASS_B), p=_iri(PROP_1), n=_lit(2)),
            ]}
        if "?c a <" in sparql:
            return {"bindings": [_row(c=_iri(CLASS_A)), _row(c=_iri(CLASS_B))]}
        if "?p a ?t" in sparql:
            return {"bindings": [_row(p=_iri(PROP_1)), _row(p=_iri(PROP_2))]}
        if "COUNT(DISTINCT ?s)" in sparql and "?s a ?t" in sparql:
            return {"bindings": [_row(n=_lit(20 if self.abox else 0))]}
        return {"bindings": []}


class FakeOntology:
    def __init__(self):
        self.versions = [
            {"id": "ont-old", "versionId": "ont-old", "semver": "1.0.0",
             "status": "published", "contentHash": "h1", "tripleCount": 100,
             "graph": "urn:g:old"},
            {"id": "ont-new", "versionId": "ont-new", "semver": "2.0.0",
             "status": "published", "contentHash": "h2", "tripleCount": 104,
             "graph": "urn:g:new"},
        ]

    def current(self):
        return {"versionId": "ont-new"}

    def list_versions(self):
        return list(self.versions)

    def get(self, version_id):
        for item in self.versions:
            if item["id"] == version_id:
                return item
        raise RuntimeError("missing version")

    def diff(self, from_id, to_id):
        return {
            "summary": {"addedTriples": 3, "removedTriples": 2,
                        "addedClasses": [CLASS_B], "removedClasses": [],
                        "addedProperties": [PROP_2], "removedProperties": [],
                        "domainChanges": [], "rangeChanges": []},
            "breaking": False, "breakingItems": [],
        }


def _version(vid, *, published=None, created=None, status="published", triples=100):
    return {"id": vid, "versionId": vid, "semver": "1.0.0", "status": status,
            "contentHash": f"h-{vid}", "tripleCount": triples,
            "graph": f"urn:g:{vid}", "createdAt": created, "publishedAt": published}


def _runtime(*, changes=True, abox=True):
    graph = FakeGraph(changes=changes, abox=abox)
    runtime = SimpleNamespace(
        metadata=SimpleNamespace(query=lambda sql, params=(): []),
        graph=graph, ontology=FakeOntology(),
        reasoning=SimpleNamespace(status=lambda: {"aboxGraphs": ["urn:abox"] if abox else []}),
        config=SimpleNamespace(reasoning=SimpleNamespace(abox_graphs=())),
        bundle=object(),
    )
    return runtime, graph


class AggregationTests(unittest.TestCase):
    def test_changes_grouped_by_class_and_property(self):
        runtime, _ = _runtime()
        block = healthboard._aggregate_block(runtime, "urn:g:old", "urn:g:new")
        classes = {item["iri"]: item for item in block["byClass"]}
        self.assertEqual(classes[CLASS_A]["addedTriples"], 3)
        self.assertEqual(classes[CLASS_B]["removedTriples"], 2)
        props = {item["iri"]: item for item in block["byProperty"]}
        self.assertEqual(props[PROP_1]["addedTriples"], 3)
        self.assertEqual(props[PROP_1]["removedTriples"], 2)
        self.assertGreater(block["unclassified"]["addedTriples"], 0)
        self.assertFalse(block["empty"])

    def test_no_baseline_is_explicit(self):
        runtime, _ = _runtime()
        block = healthboard._aggregate_block(runtime, None, "urn:g:new")
        self.assertTrue(block["empty"])
        self.assertIn("无基线版本", block["emptyReason"])

    def test_no_changes_is_explicit(self):
        runtime, _ = _runtime(changes=False)
        block = healthboard._aggregate_block(runtime, "urn:g:old", "urn:g:new")
        self.assertTrue(block["empty"])
        self.assertIn("无三元组差异", block["emptyReason"])


class SnapshotTests(unittest.TestCase):
    def test_snapshot_counts(self):
        runtime, _ = _runtime()
        snap = healthboard.snapshot(runtime, "ont-new")
        self.assertEqual(snap["triples"], 104)
        self.assertEqual(snap["classes"], 2)
        self.assertEqual(snap["properties"], 2)
        self.assertEqual(snap["instances"], 20)
        self.assertFalse(snap["empty"])

    def test_missing_abox_is_null_with_reason(self):
        runtime, _ = _runtime(abox=False)
        snap = healthboard.snapshot(runtime, "ont-new")
        self.assertIsNone(snap["instances"])
        self.assertIn("未以 0 代替", snap["instancesNote"])
        self.assertEqual(snap["instancesSource"], "A-Box 未配置")

    def test_compare_delta(self):
        runtime, _ = _runtime()
        block = healthboard.snapshot_compare(runtime, "ont-old", "ont-new")
        self.assertEqual(block["delta"]["triples"], 4)
        self.assertEqual(block["delta"]["classes"], 0)
        self.assertEqual(block["delta"]["instances"], 0)
        self.assertFalse(block["empty"])

    def test_same_version_is_explicit_empty(self):
        runtime, _ = _runtime()
        block = healthboard.snapshot_compare(runtime, "ont-new", "ont-new")
        self.assertTrue(block["empty"])
        self.assertIn("两版本相同", block["emptyReason"])

    def test_no_pointer_empty_state(self):
        runtime, _ = _runtime()
        runtime.ontology = SimpleNamespace(current=lambda: {}, list_versions=lambda: [])
        block = healthboard.snapshot_compare(runtime)
        self.assertTrue(block["empty"])
        self.assertIn("指针不存在", block["emptyReason"])
        self.assertEqual(block["delta"], {})


class DefaultBaselineTests(unittest.TestCase):
    """O-06: 默认基线按发布时间取“严格早于当前指针版本的最新一版”。"""

    def _runtime_with(self, versions, pointer):
        runtime, _ = _runtime()
        runtime.ontology = FakeOntology()
        runtime.ontology.versions = versions
        runtime.ontology.current = lambda: {"versionId": pointer}
        return runtime

    def test_pointer_first_in_list_uses_latest_earlier_published(self):
        versions = [
            _version("ont-new", published="2026-11-07T10:00:00+08:00",
                     created="2026-11-07T07:00:00+08:00", triples=104),
            _version("ont-mid", published="2026-11-07T09:00:00+08:00",
                     created="2026-11-07T08:00:00+08:00"),
            _version("ont-old", published="2026-11-07T08:00:00+08:00",
                     created="2026-11-07T08:30:00+08:00"),
        ]
        runtime = self._runtime_with(versions, "ont-new")
        client = TestClient(api_module.create_app(runtime, []))
        with client:
            response = client.get("/health/ontology-diff")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["from"], "ont-mid")
            self.assertEqual(response.json()["to"], "ont-new")

            snapshot = client.get("/health/ontology-snapshot")
            self.assertEqual(snapshot.status_code, 200)
            self.assertEqual(snapshot.json()["from"]["versionId"], "ont-mid")

    def test_tied_publish_time_breaks_tie_by_sequence(self):
        versions = [
            _version("ont-old", published="2026-11-07T09:00:00+08:00",
                     created="2026-11-07T08:00:00+08:00"),
            _version("ont-tie", published="2026-11-07T10:00:00+08:00",
                     created="2026-11-07T08:10:00+08:00"),
            _version("ont-new", published="2026-11-07T10:00:00+08:00",
                     created="2026-11-07T08:20:00+08:00"),
        ]
        runtime = self._runtime_with(versions, "ont-new")
        client = TestClient(api_module.create_app(runtime, []))
        with client:
            response = client.get("/health/ontology-diff")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["from"], "ont-tie")

    def test_single_version_has_no_baseline(self):
        versions = [_version("ont-new", published="2026-11-07T10:00:00+08:00",
                             created="2026-11-07T07:00:00+08:00")]
        runtime = self._runtime_with(versions, "ont-new")
        client = TestClient(api_module.create_app(runtime, []))
        with client:
            response = client.get("/health/ontology-diff")
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json()["error"]["providerCode"],
                             "E_DIFF_NO_PREVIOUS_BASELINE")

            snapshot = client.get("/health/ontology-snapshot")
            self.assertEqual(snapshot.status_code, 200)
            self.assertTrue(snapshot.json()["empty"])
            self.assertIn("没有基线版本", snapshot.json()["emptyReason"])


class DiffPayloadTests(unittest.TestCase):
    def test_diff_embeds_aggregations_and_snapshots(self):
        runtime, _ = _runtime()
        client = TestClient(api_module.create_app(runtime, []))
        with client:
            response = client.get("/health/ontology-diff",
                                  params={"from": "ont-old", "to": "ont-new"})
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertIn("aggregations", payload)
            self.assertIn("byClass", payload["aggregations"])
            self.assertIn("byProperty", payload["aggregations"])
            self.assertIn("snapshots", payload)
            self.assertEqual(payload["snapshots"]["delta"]["triples"], 4)
            self.assertIn("lifecycle", payload)

    def test_snapshot_route(self):
        runtime, _ = _runtime()
        client = TestClient(api_module.create_app(runtime, []))
        with client:
            response = client.get("/health/ontology-snapshot",
                                  params={"from": "ont-old", "to": "ont-new"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["to"]["versionId"], "ont-new")

            empty = client.get("/health/ontology-snapshot",
                               params={"from": "ont-old", "to": "ont-old"})
            self.assertTrue(empty.json()["empty"])
            self.assertIn("两版本相同", empty.json()["emptyReason"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
