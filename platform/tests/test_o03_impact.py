"""O-03 T-Box change impact analysis tests.

Pure unit tests with fakes (no postgres/oxigraph). Run with:
  docker run --rm --entrypoint python -e PYTHONPATH=/hostsrc \
    -v <repo>/src:/hostsrc:ro -v <repo>/tests:/hosttests:ro \
    agent-platform:0.1-s5 /hosttests/test_o03_impact.py
"""

from __future__ import annotations

import json
import sys
import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient

sys.path.insert(0, "/hostsrc")
sys.path.insert(0, "../src")

import platform_core.api as api_module
from platform_core import impact
from platform_core.errors import PortError

CLASS_A = "urn:onto#LoanAccount"
CLASS_B = "urn:onto#Collateral"
PROP_1 = "urn:onto#principalAmount"
PROP_2 = "urn:onto#collateralType"
CLASS_DOMAIN_TARGET = "urn:onto#Guarantee"
CLASS_RANGE_ONE = "urn:onto#Valuation"
CLASS_RANGE_TWO = "urn:onto#CollateralValuation"

# ontology_pg.diff_graphs 产出的 domain/range 变更是 IRI 列表（多值）；这里复刻真实形状。
MULTI_VALUE_DIFF = {
    "summary": {
        "addedTriples": 4, "removedTriples": 2,
        "addedClasses": [CLASS_B], "removedClasses": [],
        "addedProperties": [PROP_2], "removedProperties": [],
        "domainChanges": [{"property": PROP_1, "from": [CLASS_A], "to": [CLASS_DOMAIN_TARGET]}],
        "rangeChanges": [{"property": PROP_2, "from": [CLASS_RANGE_ONE, CLASS_RANGE_TWO],
                          "to": []}],
    },
    "breaking": False,
    "breakingItems": [],
}


def _row(**values):
    return {"values": values}


def _iri(value):
    return {"kind": "iri", "iri": value}


def _lit(value):
    return {"kind": "literal", "value": value}


class FakeGraph:
    """Answers only the SPARQL shapes O-03 actually sends."""

    def __init__(self, *, abox=True, empty_changes=False):
        self.abox = abox
        self.empty_changes = empty_changes
        self.queries: list[str] = []

    def query(self, sparql):
        self.queries.append(sparql)
        if self.empty_changes:
            return {"bindings": []}
        if "GROUP BY ?c" in sparql:
            return {"bindings": [
                _row(c=_iri(CLASS_A), n=_lit(10)),
                _row(c=_iri(CLASS_B), n=_lit(4)),
            ]}
        if "GROUP BY ?s ?p" in sparql:
            if "GRAPH <urn:g:new>" in sparql and sparql.index("GRAPH <urn:g:new>") < sparql.index("MINUS"):
                return {"bindings": [
                    _row(s=_iri(CLASS_A), p=_iri(PROP_1), n=_lit(3)),
                    _row(s=_iri(PROP_2), p=_iri("urn:onto#range"), n=_lit(1)),
                ]}
            return {"bindings": [
                _row(s=_iri(CLASS_B), p=_iri(PROP_1), n=_lit(2)),
            ]}
        if "?s a <" in sparql and "COUNT(DISTINCT ?s)" in sparql:
            if CLASS_A in sparql:
                return {"bindings": [_row(n=_lit(10))]}
            return {"bindings": [_row(n=_lit(4))]}
        if "?s a ?t" in sparql:
            return {"bindings": [_row(n=_lit(20 if self.abox else 0))]}
        if "?c ?label ?pref" in sparql:
            return {"bindings": [_row(c=_iri(CLASS_A)), _row(c=_iri(CLASS_B))]}
        if "?p a ?t" in sparql:
            return {"bindings": [_row(p=_iri(PROP_1)), _row(p=_iri(PROP_2))]}
        return {"bindings": []}


class FakeOntology:
    def __init__(self):
        self.versions = [
            {"id": "ont-old", "semver": "1.0.0", "status": "published",
             "contentHash": "hash-old", "tripleCount": 100, "graph": "urn:g:old"},
            {"id": "ont-new", "semver": "2.0.0", "status": "approved",
             "contentHash": "hash-new", "tripleCount": 104, "graph": "urn:g:new"},
        ]
        self.diff_result = {
            "summary": {
                "addedTriples": 4, "removedTriples": 2,
                "addedClasses": [CLASS_B], "removedClasses": [],
                "addedProperties": [PROP_2], "removedProperties": [],
                "domainChanges": [{"property": PROP_1, "from": CLASS_A, "to": CLASS_B}],
                "rangeChanges": [],
            },
            "breaking": False,
            "breakingItems": [],
        }

    def current(self):
        return {"versionId": "ont-new"}

    def list_versions(self):
        return list(self.versions)

    def get(self, version_id):
        for item in self.versions:
            if item["id"] == version_id:
                return item
        raise PortError(code="NotFound", message="missing", provider="postgres",
                        provider_code="E_ONTOLOGY_VERSION_NOT_FOUND")

    def diff(self, from_id, to_id):
        return self.diff_result


class FakeMetadata:
    def query(self, sql, params=()):
        if "metric_definition" in sql:
            return [
                {"metric_id": "FIN-BANK-008", "name_zh": "不良贷款率",
                 "display_name": "NPL ratio", "definition": "loan account 口径",
                 "formula_text": "sum(principalAmount)", "denominator_text": None,
                 "rule_set_json": [{"ruleId": "R-NPL-1", "level": "warn"}]},
                {"metric_id": "FIN-BANK-022", "name_zh": "拨备覆盖率",
                 "display_name": None, "definition": "unrelated",
                 "formula_text": None, "denominator_text": None,
                 "rule_set_json": [{"ruleId": "R-UNRELATED", "level": "info"}]},
            ]
        if "metric_field_binding" in sql:
            return [{"metric_id": "FIN-BANK-008", "role": "numerator",
                     "fact_table": "fact_loan", "entity_column": "loan_id",
                     "value_expr": "principal_amount"}]
        if "data_dictionary" in sql:
            return [{"table_name": "fact_loan", "column_name": "principal_amount",
                     "property_iri": PROP_1}]
        return []


def _runtime(*, abox=True, empty_changes=False):
    graph = FakeGraph(abox=abox, empty_changes=empty_changes)
    ontology = FakeOntology()
    runtime = SimpleNamespace(
        metadata=FakeMetadata(), graph=graph, ontology=ontology,
        reasoning=SimpleNamespace(status=lambda: {"aboxGraphs": ["urn:abox"] if abox else []}),
        config=SimpleNamespace(reasoning=SimpleNamespace(abox_graphs=())),
        bundle=object(),
    )
    return runtime, graph, ontology


def _stable(report):
    """Determinism payload: everything except the wall-clock timestamp."""
    payload = {key: value for key, value in report.items() if key != "computedAt"}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)


class ImpactAnalysisTests(unittest.TestCase):
    def test_affected_classes_properties_instances(self):
        runtime, _, _ = _runtime()
        report = impact.analyze(runtime, "ont-old", "ont-new", sample=2)
        self.assertEqual(report["from"], "ont-old")
        classes = {item["iri"]: item for item in report["affected"]["classes"]}
        self.assertEqual(classes[CLASS_A]["change"], "modified")
        self.assertEqual(classes[CLASS_A]["addedTriples"], 3)
        self.assertEqual(classes[CLASS_B]["change"], "added")
        self.assertEqual(classes[CLASS_B]["removedTriples"], 2)
        props = {item["iri"]: item for item in report["affected"]["properties"]}
        self.assertEqual(props[PROP_1]["change"], "modified")
        self.assertEqual(props[PROP_2]["change"], "added")
        counts = {item["iri"]: item["instances"]
                  for item in report["affected"]["instances"]["byClass"]}
        self.assertEqual(counts[CLASS_A], 10)
        self.assertEqual(counts[CLASS_B], 4)
        self.assertEqual(report["affected"]["instances"]["total"], 20)
        self.assertFalse(report["empty"])

    def test_dependent_metrics_and_rules(self):
        runtime, _, _ = _runtime()
        report = impact.analyze(runtime, "ont-old", "ont-new")
        metric_ids = [item["metricId"] for item in report["dependencies"]["metrics"]]
        self.assertEqual(metric_ids, ["FIN-BANK-008"])
        rules = [item["ruleId"] for item in report["dependencies"]["rules"]]
        self.assertEqual(rules, ["R-NPL-1"])
        matched = report["dependencies"]["metrics"][0]["matchedBy"]
        self.assertTrue(any(item.startswith("text:") for item in matched))
        self.assertTrue(any(item.startswith("binding:") for item in matched))

    def test_sampling_recount_is_consistent_and_deterministic(self):
        runtime, _, _ = _runtime()
        first = impact.analyze(runtime, "ont-old", "ont-new", sample=2)
        second = impact.analyze(runtime, "ont-old", "ont-new", sample=2)
        self.assertTrue(first["verification"]["consistent"])
        self.assertEqual(len(first["verification"]["sampled"]), 2)
        self.assertEqual(_stable(first), _stable(second))
        self.assertEqual(first["inputsFingerprint"], second["inputsFingerprint"])

    def test_missing_abox_reports_null_not_zero(self):
        runtime, _, _ = _runtime(abox=False)
        report = impact.analyze(runtime, "ont-old", "ont-new")
        instances = report["affected"]["instances"]
        self.assertIsNone(instances["total"])
        self.assertIsNone(instances["byClass"][0]["instances"])
        self.assertIn("未以 0 代替", instances["note"])
        self.assertIsNone(report["verification"]["consistent"])
        self.assertIn("不可重算", report["verification"]["reason"])

    def test_empty_change_set_is_explicit(self):
        runtime, _, ontology = _runtime(empty_changes=True)
        ontology.diff_result = {"summary": {}, "breaking": False, "breakingItems": []}
        report = impact.analyze(runtime, "ont-old", "ont-new")
        self.assertTrue(report["empty"])
        self.assertEqual(report["affected"]["classes"], [])
        self.assertEqual(report["dependencies"]["metrics"], [])
        self.assertTrue(report["aggregations"]["empty"])

    def test_no_previous_baseline_returns_empty_report(self):
        runtime, _, _ = _runtime()
        report = impact.analyze(runtime, None, "ont-old")
        self.assertTrue(report["empty"])
        self.assertIn("基线", report["emptyReason"])

    def test_multi_valued_domain_range_changes_are_expanded(self):
        """from/to 为列表时必须展开去重，不能直接进 set()（会 TypeError）。"""
        runtime, _, ontology = _runtime()
        ontology.diff_result = MULTI_VALUE_DIFF
        report = impact.analyze(runtime, "ont-old", "ont-new")
        classes = {item["iri"] for item in report["affected"]["classes"]}
        self.assertIn(CLASS_DOMAIN_TARGET, classes)
        self.assertIn(CLASS_RANGE_ONE, classes)
        self.assertIn(CLASS_RANGE_TWO, classes)
        props = {item["iri"]: item for item in report["affected"]["properties"]}
        self.assertIn(PROP_1, props)
        self.assertEqual(props[PROP_1]["domainChanges"][0]["to"], [CLASS_DOMAIN_TARGET])

    def test_default_baseline_uses_publish_time_not_list_index(self):
        runtime, _, ontology = _runtime()
        ontology.versions = [
            {"id": "ont-new", "semver": "2.0.0", "status": "approved",
             "contentHash": "hash-new", "tripleCount": 104, "graph": "urn:g:new",
             "createdAt": "2026-11-07T07:00:00+08:00",
             "publishedAt": "2026-11-07T10:00:00+08:00"},
            {"id": "ont-mid", "semver": "1.1.0", "status": "superseded",
             "contentHash": "hash-mid", "tripleCount": 102, "graph": "urn:g:mid",
             "createdAt": "2026-11-07T08:00:00+08:00",
             "publishedAt": "2026-11-07T09:00:00+08:00"},
            {"id": "ont-old", "semver": "1.0.0", "status": "superseded",
             "contentHash": "hash-old", "tripleCount": 100, "graph": "urn:g:old",
             "createdAt": "2026-11-07T08:30:00+08:00",
             "publishedAt": "2026-11-07T08:00:00+08:00"},
        ]
        report = impact.analyze(runtime, None, "ont-new")
        self.assertEqual(report["from"], "ont-mid")


class ExportTests(unittest.TestCase):
    def test_markdown_csv_and_json_exports(self):
        runtime, _, _ = _runtime()
        report = impact.analyze(runtime, "ont-old", "ont-new")
        name, media, body = impact.export(report, "markdown")
        self.assertEqual(name, "impact-ont-old-to-ont-new.md")
        self.assertIn("text/markdown", media)
        for heading in ("## 受影响类", "## 受影响属性", "## 依赖指标与规则", "## 抽样重算"):
            self.assertIn(heading, body)
        self.assertIn("FIN-BANK-008", body)

        name, media, body = impact.export(report, "csv")
        self.assertTrue(name.endswith(".csv"))
        self.assertIn("class,urn:onto#LoanAccount", body)

        _, _, body = impact.export(report, "json")
        self.assertEqual(json.loads(body)["to"], "ont-new")

    def test_unsupported_format_is_invalid_argument(self):
        with self.assertRaises(PortError) as ctx:
            impact.export({"from": "a", "to": "b"}, "pdf")
        self.assertEqual(ctx.exception.code, "InvalidArgument")
        self.assertEqual(ctx.exception.provider_code, "E_IMPACT_EXPORT_FORMAT")


class ImpactRouteTests(unittest.TestCase):
    def test_impact_and_export_endpoints(self):
        runtime, _, _ = _runtime()
        client = TestClient(api_module.create_app(runtime, []))
        with client:
            response = client.get("/ontology/impact",
                                  params={"from": "ont-old", "to": "ont-new", "sample": 1})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["to"], "ont-new")

            response = client.get("/ontology/impact/export",
                                  params={"from": "ont-old", "to": "ont-new",
                                          "format": "markdown"})
            self.assertEqual(response.status_code, 200)
            self.assertIn("attachment; filename=", response.headers["content-disposition"])
            self.assertIn("受影响类", response.text)

    def test_multi_valued_change_set_routes_return_200(self):
        runtime, _, ontology = _runtime()
        ontology.diff_result = MULTI_VALUE_DIFF
        client = TestClient(api_module.create_app(runtime, []))
        params = {"from": "ont-old", "to": "ont-new", "sample": 1}
        with client:
            response = client.get("/ontology/impact", params=params)
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["from"], "ont-old")
            self.assertIn(CLASS_DOMAIN_TARGET,
                          {item["iri"] for item in payload["affected"]["classes"]})

            response = client.get("/ontology/impact/export",
                                  params={**params, "format": "markdown"})
            self.assertEqual(response.status_code, 200)
            self.assertIn("受影响类", response.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
