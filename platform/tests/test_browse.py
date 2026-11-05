"""T6 read-only browse API tests: metrics list/detail, instances, terms, SPARQL.

These are pure API tests: the metadata and graph ports are small fakes, so no
postgres/oxigraph/reasoner is required. Run them with:
  docker run --rm --entrypoint python -e PYTHONPATH=/hostsrc \
    -v <repo>/src:/hostsrc:ro -v <repo>/tests:/hosttests:ro \
    agent-platform:0.1-s6 /hosttests/test_browse.py
"""

from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient

sys.path.insert(0, "/app/src")
sys.path.insert(0, "../src")

import platform_core.api as api_module


def _metric_row(metric_id, domain, basis, publishable, inference=False, disabled=False):
    return {
        "metric_id": metric_id,
        "name_zh": f"{metric_id} 名称",
        "domain": domain,
        "evidence_basis": basis,
        "publishable": publishable,
        "inference": inference,
        "formula_disabled": disabled,
        "missing": None,
        "evidence_status": "defined",
        "note": None,
        "definition_version": "v3",
        "metric_kind": "ratio",
        "formula_expr": "sum(numerator) / sum(denominator)",
        "numerator_agg": "sum",
        "denominator_agg": "sum",
        "window_kind": "month",
        "min_window_days": 28,
        "grain": "institution",
        "unit": "%",
    }


ROWS = [
    _metric_row("FIN-BANK-001", "bank", "regulatory", True, inference=True),
    _metric_row("FIN-BANK-002", "bank", "industry", False),
    _metric_row("FIN-INS-001", "insurance", "regulatory", True, disabled=True),
]


class FakeMetadata:
    """Applies only the browse filters, so a filter test is meaningful."""

    def __init__(self, rows):
        self.rows = list(rows)
        self.calls = []

    def query(self, sql, params=()):
        self.calls.append((sql, params))
        rows = list(self.rows)
        params = list(params)
        index = 0
        for clause, key in (
            ("domain = %s", "domain"),
            ("evidence_basis = %s", "evidence_basis"),
            ("publishable = %s", "publishable"),
        ):
            if clause in sql:
                wanted = params[index]
                index += 1
                rows = [row for row in rows if row[key] == wanted]
        if "WHERE metric_id = %s" in sql:
            wanted = params[0]
            rows = [row for row in rows if row["metric_id"] == wanted]
        return rows


class FakeGraph:
    def __init__(self, items=None, total=0):
        self.items = items or []
        self.total = total
        self.calls = []

    def query(self, sparql):
        self.calls.append(sparql)
        if "COUNT(DISTINCT" in sparql:
            return {
                "kind": "select",
                "variables": ["n"],
                "bindings": [{"values": {"n": {"kind": "literal", "value": str(self.total)}}}],
            }
        bindings = []
        for item in self.items:
            values = {}
            for name, value in item.items():
                values[name] = {"kind": "iri", "iri": value}
            bindings.append({"values": values})
        return {"kind": "select", "variables": list(bindings[0]["values"]) if bindings else [],
                "bindings": bindings}


class FakeOntology:
    def __init__(self, pointer=None):
        self._pointer = pointer

    def current(self):
        return self._pointer


def _client(rows=ROWS, pointer=None, graph=None):
    runtime = SimpleNamespace(
        metadata=FakeMetadata(rows),
        graph=graph or FakeGraph(),
        ontology=FakeOntology(pointer),
    )
    return TestClient(api_module.create_app(runtime, []))


POINTER = {"name": "tbox/current", "versionId": "ont-test", "semver": "1.0.0",
           "contentHash": "hash", "graph": "urn:platform:graph:tbox:ont-test",
           "updatedAt": "2026-01-01T00:00:00Z"}


class MetricsBrowseTests(unittest.TestCase):
    def test_1_list_returns_all_79_style_rows_with_camel_case(self):
        with _client() as client:
            payload = client.get("/browse/metrics").json()
        self.assertEqual(payload["count"], 3)
        self.assertEqual(payload["source"], "metric_definition")
        first = payload["items"][0]
        self.assertEqual(first["metricId"], "FIN-BANK-001")
        self.assertEqual(first["evidenceBasis"], "regulatory")
        self.assertIs(first["publishable"], True)
        self.assertIs(first["inference"], True)
        self.assertEqual(first["definitionVersion"], "v3")

    def test_2_filters_by_domain_evidence_and_publishable(self):
        with _client() as client:
            bank = client.get("/browse/metrics", params={"domain": "bank"}).json()
            strict = client.get(
                "/browse/metrics",
                params={"domain": "bank", "publishable": "true"},
            ).json()
            none = client.get(
                "/browse/metrics", params={"evidenceBasis": "none"}
            ).json()
        self.assertEqual(bank["count"], 2)
        self.assertEqual(strict["count"], 1)
        self.assertEqual(strict["items"][0]["metricId"], "FIN-BANK-001")
        self.assertEqual(none["count"], 0)
        self.assertEqual(none["items"], [])

    def test_3_detail_carries_formula_window_and_flags(self):
        with _client() as client:
            detail = client.get("/browse/metrics/FIN-INS-001").json()["metric"]
        self.assertEqual(detail["formula"], "sum(numerator) / sum(denominator)")
        self.assertEqual(detail["denominator"], "sum")
        self.assertEqual(detail["observationPeriod"], {"kind": "month", "minWindowDays": 28})
        self.assertIs(detail["formulaDisabled"], True)
        self.assertEqual(detail["definitionVersion"], "v3")

        with _client() as client:
            missing = client.get("/browse/metrics/NOPE-404")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json()["error"]["providerCode"], "E_METRIC_NOT_FOUND")


class OntologyBrowseTests(unittest.TestCase):
    def test_4_instances_require_a_safe_class_iri(self):
        with _client() as client:
            no_class = client.get("/browse/ontology/instances")
            bad = client.get("/browse/ontology/instances",
                             params={"class": "urn:evil:<drop>"})
        self.assertEqual(no_class.status_code, 400)
        self.assertEqual(no_class.json()["error"]["providerCode"], "E_BROWSE_IRI_REQUIRED")
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(bad.json()["error"]["providerCode"], "E_BROWSE_BAD_IRI")

    def test_5_instances_empty_state_without_pointer(self):
        graph = FakeGraph()
        with _client(pointer=None, graph=graph) as client:
            payload = client.get(
                "/browse/ontology/instances", params={"class": "urn:test:Thing"}
            ).json()
        self.assertEqual(payload["total"], 0)
        self.assertEqual(payload["items"], [])
        self.assertIsNone(payload["pointer"])
        self.assertEqual(graph.calls, [])

    def test_6_instances_paginate_with_total(self):
        graph = FakeGraph(
            items=[{"s": "urn:test:a", "label": "A", "g": "urn:platform:graph:abox:main"},
                   {"s": "urn:test:b", "label": "B", "g": "urn:platform:graph:abox:main"}],
            total=2,
        )
        with _client(pointer=POINTER, graph=graph) as client:
            payload = client.get(
                "/browse/ontology/instances",
                params={"class": "urn:test:Thing", "limit": 2, "offset": 0},
            ).json()
        self.assertEqual(payload["total"], 2)
        self.assertEqual(len(payload["items"]), 2)
        self.assertEqual(payload["items"][0]["iri"], "urn:test:a")
        self.assertEqual(payload["limit"], 2)


class TermsAndSparqlTests(unittest.TestCase):
    def test_7_terms_empty_state_without_pointer(self):
        with _client(pointer=None) as client:
            payload = client.get("/browse/terms").json()
        self.assertEqual(payload["entries"], [])
        self.assertEqual(payload["classes"], [])
        self.assertEqual(payload["counts"]["anchorClasses"], 0)
        self.assertEqual(payload["counts"]["altLabels"], 0)

    def test_8_sparql_rejects_write_queries_but_allows_select(self):
        graph = FakeGraph()

        def fake_query(sparql):
            graph.calls.append(sparql)
            return {"kind": "select", "variables": [], "bindings": [], "truncated": False}

        graph.query = fake_query
        with _client(pointer=POINTER, graph=graph) as client:
            for query in (
                "DELETE WHERE { ?s ?p ?o }",
                "INSERT DATA { <urn:a> <urn:b> <urn:c> }",
                "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }",
            ):
                response = client.get("/browse/sparql", params={"query": query})
                self.assertEqual(response.status_code, 400, query)
                self.assertEqual(
                    response.json()["error"]["providerCode"], "E_BROWSE_NOT_READ_ONLY"
                )
            ok = client.get(
                "/browse/sparql",
                params={"query": "PREFIX owl: <http://www.w3.org/2002/07/owl#> "
                                  "SELECT ?s WHERE { ?s a owl:Class }"},
            )
        self.assertEqual(ok.status_code, 200)
        self.assertIs(ok.json()["readOnly"], True)
        self.assertEqual(len(graph.calls), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
