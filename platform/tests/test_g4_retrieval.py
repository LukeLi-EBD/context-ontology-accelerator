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


def _citation(kind, **extra):
    item = {"kind": kind, "ref": kind + "-ref", "id": "urn:test:" + kind}
    item.update(extra)
    return item


def _fake_answer(_runtime, query, **_kwargs):
    if any(word in query for word in ("量子", "火星", "超导")):
        return {
            "query": query,
            "refused": True,
            "answerType": "refusal",
            "answerMode": "none",
            "reasonCode": "NO_LAYER_COVERAGE",
            "citations": [],
            "missing": [
                {"layer": "ontology", "code": "NO_CLASS_MATCH", "what": "no class"},
                {"layer": "metrics", "code": "NO_METRIC_MATCH", "what": "no metric"},
            ],
            "degraded": False,
        }
    citations = [_citation("ontology-version", id="ont-test")]
    if "13个月继续率" in query:
        citations = [
            _citation("metric-definition", metricId="FIN-INS-001"),
            _citation("formula", metricId="FIN-INS-001"),
        ]
    if "逾期分档" in query:
        citations = [_citation("rule-set", metricId="FIN-BANK-002")]
    return {
        "query": query,
        "refused": False,
        "answerType": "rule_set" if "逾期分档" in query else "definition",
        "answerMode": "definition",
        "reasonCode": "OK",
        "citations": citations,
        "missing": [],
        "degraded": False,
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


class AnswerQualityTests(unittest.TestCase):
    def test_ten_case_golden_set_passes_with_citations_and_refusal_layers(self):
        with patch.object(api_module, "_qa_answer", _fake_answer):
            with _client() as client:
                payload = client.get("/answer/quality").json()
        summary = payload["summary"]
        self.assertEqual(payload["goldenSet"]["count"], 10)
        self.assertEqual(summary["cases"], 10)
        self.assertEqual(summary["passed"], 10, payload["cases"])
        self.assertEqual(summary["failed"], 0)
        self.assertGreater(summary["citations"], 0)
        self.assertEqual(summary["brokenLinkRate"], 0.0)
        self.assertFalse(summary["regression"])
        self.assertEqual(payload["refusalsWithoutLayers"], [])
        self.assertEqual(payload["brokenLinks"], [])
        refused = [item for item in payload["cases"] if item["actual"]["refused"]]
        self.assertEqual(len(refused), 4)
        for item in refused:
            self.assertTrue(item["actual"]["missingLayers"])
        self.assertTrue(payload["refusalsByReason"])

    def test_case_id_drill_down(self):
        with patch.object(api_module, "_qa_answer", _fake_answer):
            with _client() as client:
                one = client.get("/answer/quality", params={"caseId": "G01"}).json()
                missing = client.get("/answer/quality", params={"caseId": "ZZ"}).json()
        self.assertEqual(one["goldenSet"]["evaluated"], 1)
        self.assertEqual(len(one["cases"]), 1)
        self.assertEqual(one["cases"][0]["id"], "G01")
        self.assertIn("caseId=G01", one["cases"][0]["drillDownUrl"])
        self.assertTrue(missing["empty"])
        self.assertEqual(missing["emptyReason"], "case_not_found")

    def test_refusal_without_layers_and_broken_citation_are_flagged(self):
        def bad(_runtime, query, **_kwargs):
            if any(word in query for word in ("量子", "火星", "超导")):
                return {
                    "refused": True,
                    "answerType": "refusal",
                    "answerMode": "none",
                    "reasonCode": "NO_LAYER_COVERAGE",
                    "citations": [],
                    "missing": [],
                    "degraded": False,
                }
            return {
                "refused": False,
                "answerType": "definition",
                "answerMode": "definition",
                "reasonCode": "OK",
                "citations": [{"kind": "mystery-kind", "ref": None, "id": None}],
                "missing": [],
                "degraded": False,
            }

        with patch.object(api_module, "_qa_answer", bad):
            with _client() as client:
                payload = client.get("/answer/quality").json()
        self.assertGreater(payload["summary"]["failed"], 0)
        self.assertTrue(payload["summary"]["regression"])
        self.assertGreater(payload["summary"]["brokenLinkRate"], 0.0)
        self.assertGreaterEqual(len(payload["refusalsWithoutLayers"]), 4)

    def test_invalid_strategy_is_rejected(self):
        with _client() as client:
            response = client.get("/answer/quality", params={"strategy": "magic"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["providerCode"], "E_ANSWER_STRATEGY_INVALID")

    def test_triple_citation_is_resolvable(self):
        def with_triple(_runtime, query, **_kwargs):
            return {
                "refused": False,
                "answerType": "definition",
                "answerMode": "definition",
                "reasonCode": "OK",
                "citations": [
                    {"kind": "triple", "ref": "<urn:s> <urn:p> <urn:o>", "id": None}
                ],
                "missing": [],
                "degraded": False,
            }

        with patch.object(api_module, "_qa_answer", with_triple):
            with _client() as client:
                payload = client.get("/answer/quality").json()
        self.assertGreater(payload["summary"]["citations"], 0)
        self.assertEqual(payload["summary"]["brokenLinkRate"], 0.0)
        self.assertEqual(payload["brokenLinks"], [])

    def test_quality_never_persists_prov(self):
        seen = []

        def capture(_runtime, query, **kwargs):
            seen.append(kwargs)
            return {
                "refused": True,
                "answerType": "refusal",
                "answerMode": "none",
                "reasonCode": "NO_LAYER_COVERAGE",
                "citations": [],
                "missing": [{"layer": "ontology"}],
                "degraded": False,
            }

        with patch.object(api_module, "_qa_answer", capture):
            with _client() as client:
                client.get("/answer/quality").json()
        self.assertTrue(seen)
        self.assertTrue(all(item.get("persist") is False for item in seen))


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


class EntityProvenanceTests(unittest.TestCase):
    def test_every_field_has_badge_and_missing_provenance_says_none(self):
        with patch.object(api_module.entity_view, "entity_detail", return_value=ENTITY_DETAIL):
            with _client() as client:
                payload = client.get(
                    "/entity/provenance", params={"iri": "urn:test:e1"}
                ).json()
        self.assertEqual(payload["summary"]["total"], 5)
        self.assertFalse(payload["empty"])
        fields = {item["label"]: item for item in payload["fields"]}
        self.assertEqual(fields["名称"]["badge"]["label"], "有溯源")
        self.assertIn("/source/resolve", fields["名称"]["links"][0]["url"])
        self.assertEqual(fields["年龄"]["badge"]["label"], "有溯源")
        self.assertIn("/browse/facts", fields["年龄"]["links"][0]["url"])
        self.assertEqual(fields["备注"]["badge"]["state"], "none")
        self.assertEqual(fields["备注"]["badge"]["label"], "无")
        self.assertTrue(fields["备注"]["badge"]["basis"])
        self.assertEqual(fields["seeAlso"]["badge"]["label"], "有溯源")
        self.assertEqual(fields["推理属性"]["badge"]["label"], "仅推理")
        for item in payload["fields"]:
            self.assertIn("badge", item)
            self.assertIn(item["badge"]["state"], ("evidenced", "inferred", "none"))

    def test_missing_entity_iri_is_rejected_by_validation(self):
        with _client() as client:
            response = client.get("/entity/provenance")
        self.assertEqual(response.status_code, 422)


class BrowseLinksTests(unittest.TestCase):
    def test_four_stable_read_only_paths(self):
        with _client() as client:
            payload = client.get("/browse/links").json()
        self.assertEqual(payload["paths"][0]["id"], "triples-to-entity")
        self.assertEqual(payload["paths"][1]["id"], "metrics-to-definition")
        self.assertEqual(payload["paths"][2]["id"], "tree-to-entity")
        self.assertEqual(payload["paths"][3]["id"], "entity-to-tab")
        self.assertEqual(payload["templates"]["triples-to-entity"], "/ui/entity.html?iri={iri}")
        self.assertEqual(
            payload["templates"]["metrics-to-definition"],
            "/ui/browse.html?tab=metrics&metricId={metricId}",
        )
        self.assertEqual(payload["templates"]["entity-to-tab"],
                         "/ui/browse.html?tab={tab}&entity={iri}")
        self.assertTrue(payload["stable"])
        self.assertTrue(payload["readOnly"])
        self.assertEqual(payload["writeOperations"], 0)
        self.assertTrue(all(item["method"] == "GET" for item in payload["paths"]))

    def test_concrete_hrefs_are_url_encoded(self):
        with _client() as client:
            payload = client.get(
                "/browse/links",
                params={
                    "iri": "http://example.org/E 1",
                    "metricId": "FIN BANK 001",
                    "classIri": "http://example.org/C",
                    "entity": "urn:test:e1",
                    "tab": "metrics",
                },
            ).json()
        hrefs = {item["id"]: item["href"] for item in payload["paths"]}
        self.assertEqual(hrefs["triples-to-entity"], "/ui/entity.html?iri=http%3A%2F%2Fexample.org%2FE%201")
        self.assertEqual(
            hrefs["metrics-to-definition"],
            "/ui/browse.html?tab=metrics&metricId=FIN%20BANK%20001",
        )
        self.assertEqual(
            hrefs["entity-to-tab"],
            "/ui/browse.html?tab=metrics&entity=urn%3Atest%3Ae1",
        )


if __name__ == "__main__":
    unittest.main()
