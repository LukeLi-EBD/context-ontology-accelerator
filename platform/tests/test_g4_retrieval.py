"""G4 retrieval QA unit tests (R-01..R-04).

Pure API tests: the answer/answerable helpers are patched locally and the
metadata/graph ports are small fakes, so no postgres/oxigraph/reasoner is
required. Run only this file:
  .venv/Scripts/python.exe -m pytest platform/tests/test_g4_retrieval.py -q
"""

from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, "../src")
sys.path.insert(0, "platform/src")

import platform_core.api as api_module


class FakeMetadata:
    def __init__(self):
        self.calls = []

    def query(self, sql, params=()):
        self.calls.append((sql, params))
        return []


class FakeGraph:
    def __init__(self):
        self.calls = []

    def query(self, sparql):
        self.calls.append(sparql)
        return {"kind": "select", "variables": [], "bindings": []}


class FakeOntology:
    def __init__(self, pointer=None):
        self._pointer = pointer

    def current(self):
        return self._pointer


def _client():
    runtime = SimpleNamespace(
        metadata=FakeMetadata(),
        graph=FakeGraph(),
        ontology=FakeOntology(None),
    )
    return TestClient(api_module.create_app(runtime, []))


def _layer(name, status):
    return {"layer": name, "status": status, "coverage": 1.0 if status == "covered" else 0.0}


def _fake_answerable(_runtime, query, **_kwargs):
    """Deterministic 24-query fixture: value queries with an unknown concept fail."""
    if any(word in query for word in ("量子", "火星", "超导", "不良率")):
        return {
            "query": query,
            "answerable": False,
            "intent": "value",
            "reasonCode": "NO_LAYER_COVERAGE",
            "layers": [
                _layer("ontology", "missing"),
                _layer("terms", "missing"),
                _layer("metrics", "missing"),
                _layer("facts", "not_applicable"),
            ],
            "missing": [
                {"layer": "ontology", "code": "NO_CLASS_MATCH", "what": "no class matched"},
                {"layer": "metrics", "code": "NO_METRIC_MATCH", "what": "no metric matched"},
            ],
            "candidates": [
                {"layer": "ontology", "id": "https://w3id.org/fsldm/core#Metric",
                 "label": "Metric", "reason": "label", "score": 1.0}
            ],
            "selectedMetrics": [],
        }
    definition = any(word in query for word in ("口径", "是什么", "保留多久", "如何处理", "哪些字段"))
    return {
        "query": query,
        "answerable": True,
        "intent": "definition" if definition else "value",
        "reasonCode": "OK",
        "layers": [
            _layer("ontology", "covered"),
            _layer("terms", "partial" if definition else "covered"),
            _layer("metrics", "not_applicable" if definition else "covered"),
            _layer("facts", "not_applicable" if definition else "partial"),
        ],
        "missing": [] if definition else [
            {"layer": "facts", "code": "FACT_COVERAGE_LOW", "what": "facts partially covered"}
        ],
        "candidates": [
            {"layer": "ontology", "id": "https://w3id.org/fsldm/core#Party",
             "label": "Party", "reason": "label", "score": 1.0},
            {"layer": "terms", "id": "https://w3id.org/fsldm/core#Party",
             "label": "当事人", "reason": "alias", "score": 0.9},
        ],
        "selectedMetrics": [] if definition else ["FIN-BANK-001"],
    }


class AnswerablePanelTests(unittest.TestCase):
    def test_panel_aggregates_four_layers_missing_candidates_and_trend(self):
        with patch.object(api_module, "_qa_answerable", _fake_answerable):
            with _client() as client:
                payload = client.get("/answerable/panel").json()
        self.assertEqual(payload["querySet"]["evaluated"], 24)
        self.assertEqual([row["layer"] for row in payload["layers"]],
                         ["ontology", "terms", "metrics", "facts"])
        self.assertGreater(payload["missing"]["total"], 0)
        self.assertEqual(payload["candidates"]["total"], 3)
        self.assertEqual(len(payload["trend"]["byGroup"]), 3)
        self.assertEqual(payload["trend"]["byGroup"][0]["bucket"], "A")
        self.assertIs(payload["readOnly"], True)
        self.assertFalse(payload["empty"])
        self.assertGreater(payload["misjudgments"]["count"], 0)
        first = payload["misjudgments"]["items"][0]
        self.assertIn(first["verdict"], ("overclaim", "underclaim"))
        self.assertIn("layerStatuses", first)
        self.assertTrue(first["drillDownUrl"].startswith("/answerable/panel?queryId="))
        self.assertEqual(payload["termExpansion"]["status"], "unavailable")

    def test_panel_filters_intent_group_and_layer(self):
        with patch.object(api_module, "_qa_answerable", _fake_answerable):
            with _client() as client:
                definition = client.get("/answerable/panel", params={"intent": "definition"}).json()
                group_a = client.get("/answerable/panel", params={"group": "A"}).json()
                facts = client.get("/answerable/panel", params={"layer": "facts"}).json()
        self.assertTrue(all(row["evaluated"] > 0 for row in definition["layers"]))
        self.assertEqual(group_a["querySet"]["evaluated"], 12)
        self.assertTrue(
            all(item["layer"] == "facts" for item in facts["missing"]["items"])
        )

    def test_panel_query_id_drill_down_and_unknown_id(self):
        with patch.object(api_module, "_qa_answerable", _fake_answerable):
            with _client() as client:
                one = client.get("/answerable/panel", params={"queryId": "A8"}).json()
                missing = client.get("/answerable/panel", params={"queryId": "ZZ"}).json()
        self.assertEqual(one["querySet"]["evaluated"], 1)
        self.assertEqual(one["layers"][0]["evaluated"], 1)
        self.assertFalse(one["empty"])
        self.assertTrue(missing["empty"])
        self.assertEqual(missing["emptyReason"], "query_not_found")

    def test_panel_empty_state_is_explicit_when_runtime_is_unavailable(self):
        def broken(_runtime, _query, **_kwargs):
            raise api_module.PortError(
                code="NotFound",
                message="no published ontology version",
                provider="platform",
                provider_code="E_ONTO_NOT_PUBLISHED",
            )

        with patch.object(api_module, "_qa_answerable", broken):
            with _client() as client:
                payload = client.get("/answerable/panel").json()
        self.assertTrue(payload["empty"])
        self.assertEqual(payload["emptyReason"], "runtime_unavailable")
        self.assertTrue(payload["degraded"])
        self.assertEqual(len(payload["errors"]), 24)


ENTITY_DETAIL = {
    "label": "测试实体",
    "properties": [
        {"property": "http://example.org/name", "label": "名称",
         "values": [{"kind": "literal", "value": "张三"}]},
        {"property": "http://example.org/age", "label": "年龄",
         "values": [{"kind": "literal", "value": "99"}]},
        {"property": "http://example.org/note", "label": "备注",
         "values": [{"kind": "literal", "value": "无来源备注"}]},
        {"property": "http://www.w3.org/2000/01/rdf-schema#seeAlso", "label": "seeAlso",
         "values": [{"kind": "literal", "value": "src://doc/1"}]},
        {"property": "http://example.org/inferredOnly", "label": "推理属性",
         "values": [{"kind": "literal", "value": "推理值"}]},
    ],
    "sources": [
        {"kind": "doc", "ref": "src://doc/1", "text": "张三 42 岁",
         "resolveUrl": "/source/resolve?ref=src%3A%2F%2Fdoc%2F1"}
    ],
    "neighbors": {
        "edges": [
            {"s": "urn:test:e1", "p": "http://example.org/name", "inferred": False},
            {"s": "urn:test:e1", "p": "http://example.org/age", "inferred": False},
            {"s": "urn:test:e1", "p": "http://example.org/note", "inferred": False},
            {"s": "urn:test:e1", "p": "http://www.w3.org/2000/01/rdf-schema#seeAlso", "inferred": False},
            {"s": "urn:test:e1", "p": "http://example.org/inferredOnly", "inferred": True},
        ]
    },
    "relatedMetrics": {
        "items": [
            {"metricId": "FIN-BANK-001",
             "bindings": [{"entityColumn": "age", "factTable": "t_age", "role": "key"}]}
        ]
    },
    "evidenceBadge": {"state": "evidenced", "label": "有溯源"},
}


if __name__ == "__main__":
    unittest.main()
