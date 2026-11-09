"""O-05 term-layer governance tests (rdflib parsing + fakes, no postgres)."""

from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient

sys.path.insert(0, "/hostsrc")
sys.path.insert(0, "../src")

import platform_core.api as api_module
from platform_core import termgov
from platform_core.errors import PortError

PREFIX = """@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix term: <https://w.wid.org/fsldm/terms#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
""".replace("https://w.wid.org", "https://w3id.org")

BASE = PREFIX + """
<urn:m#M1> a skos:Concept ; skos:inScheme term:MetricScheme ;
  skos:notation "M1" ; skos:prefLabel "指标一"@zh ; skos:definition "定义一"@zh .
<urn:m#M2> a skos:Concept ; skos:inScheme term:MetricScheme ;
  skos:notation "M2" ; skos:prefLabel "指标二"@zh ; skos:definition "定义二"@zh ;
  skos:altLabel "别名二"@zh .
"""

INCOMING = PREFIX + """
<urn:m#M1> a skos:Concept ; skos:inScheme term:MetricScheme ;
  skos:notation "M1" ; skos:prefLabel "指标一（新）"@zh ; skos:definition "定义一改"@zh .
<urn:m#M3> a skos:Concept ; skos:inScheme term:MetricScheme ;
  skos:notation "M3" ; skos:prefLabel "指标三"@zh ; skos:definition "定义三"@zh .
"""

CONFLICT = PREFIX + """
<urn:m#X> a skos:Concept ; skos:inScheme term:MetricScheme ;
  skos:prefLabel "同名"@zh ; skos:definition "a" .
<urn:m#Y> a skos:Concept ; skos:inScheme term:MetricScheme ;
  skos:prefLabel "同名"@zh ; skos:definition "b" .
"""

BAD_GUARD = PREFIX + """
<urn:m#A> a skos:Concept ; skos:inScheme term:MetricScheme ;
  skos:prefLabel "甲"@zh ; skos:definition "a" .
<urn:t#E1> a term:TermEntry ; term:forClass <urn:c#C> ; term:label "甲" ;
  term:guardRegex "[" .
"""


def _row(**values):
    return {"values": values}


def _iri(value):
    return {"kind": "iri", "iri": value}


def _lit(value, lang=""):
    return {"kind": "literal", "value": value, "lang": lang}


class FakeGraph:
    def query(self, sql):
        if "core#Concept" in sql and "inScheme" in sql:
            return {"bindings": [
                _row(s=_iri("urn:m#M1"), p=_iri("http://www.w3.org/2004/02/skos/core#prefLabel"),
                     o=_lit("指标一", "zh")),
                _row(s=_iri("urn:m#M1"), p=_iri("http://www.w3.org/2004/02/skos/core#definition"),
                     o=_lit("定义一", "zh")),
                _row(s=_iri("urn:m#M2"), p=_iri("http://www.w3.org/2004/02/skos/core#prefLabel"),
                     o=_lit("指标二", "zh")),
                _row(s=_iri("urn:m#M2"), p=_iri("http://www.w3.org/2004/02/skos/core#altLabel"),
                     o=_lit("别名二", "zh")),
            ]}
        if "TermEntry" in sql:
            return {"bindings": [
                _row(e=_iri("urn:t#E1"), c=_iri("urn:c#C"), l=_lit("别名一")),
            ]}
        if "termBatch" in sql:
            return {"bindings": [
                _row(s=_iri("urn:c#C"),
                     p=_iri("http://www.w3.org/2004/02/skos/core#prefLabel"),
                     o=_lit("客户", "zh")),
            ]}
        return {"bindings": []}


class FakeOntology:
    def current(self):
        return {"versionId": "ont-1"}

    def get(self, version_id):
        return {"id": version_id, "graph": "urn:g:1"}


class FakeMetadata:
    def __init__(self, *, fail_checks=False):
        self.statements: list[tuple[str, tuple]] = []
        self.fail_checks = fail_checks

    def query(self, sql, params=()):
        self.statements.append((sql, params))
        if "INSERT INTO platform.term_check" in sql:
            return [{"check_id": params[0]}]
        if "INSERT INTO platform.term_import" in sql:
            return [{"import_id": params[0]}]
        if "FROM platform.term_check" in sql:
            return [{"check_id": "tc-1", "source_kind": "import", "version_id": None,
                     "status": "pass", "diff_hash": "a" * 64,
                     "created_at": "2026-01-01T00:00:00+00:00"}]
        return []


def _runtime(metadata=None):
    return SimpleNamespace(
        metadata=metadata or FakeMetadata(), graph=FakeGraph(),
        ontology=FakeOntology(), bundle=object(),
        config=SimpleNamespace(storage=SimpleNamespace(root="/tmp")),
    )


class DiffTests(unittest.TestCase):
    def test_diff_shows_add_remove_and_redefinition(self):
        current = termgov.parse_skos(BASE)
        incoming = termgov.parse_skos(INCOMING)
        report = termgov.diff_snapshots(current, incoming)
        self.assertEqual(report["added"]["concepts"], ["urn:m#M3"])
        self.assertEqual(report["removed"]["concepts"], ["urn:m#M2"])
        self.assertEqual(len(report["changed"]), 1)
        self.assertEqual(report["changed"][0]["iri"], "urn:m#M1")
        self.assertIn("definition", report["changed"][0]["fields"])
        self.assertTrue(report["changed"][0]["semanticChange"])
        self.assertEqual(report["redefined"][0]["iri"], "urn:m#M1")
        self.assertTrue(report["verdict"]["mayPublish"])
        self.assertEqual(report["verdict"]["status"], "pass")

    def test_shared_surface_is_blocking(self):
        report = termgov.diff_snapshots({}, termgov.parse_skos(CONFLICT))
        codes = [item["code"] for item in report["conflicts"]]
        self.assertIn("SURFACE_SHARED_BY_MULTIPLE_CONCEPTS", codes)
        self.assertFalse(report["verdict"]["mayPublish"])
        self.assertEqual(report["verdict"]["status"], "fail")

    def test_bad_guard_regex_is_blocking(self):
        report = termgov.diff_snapshots({}, termgov.parse_skos(BAD_GUARD))
        codes = [item["code"] for item in report["conflicts"]]
        self.assertIn("GUARD_REGEX_INVALID", codes)
        self.assertFalse(report["verdict"]["mayPublish"])

    def test_missing_pref_blocks_publish(self):
        snapshot = {"concepts": {"urn:x": {"pref": {}, "alt": [], "definition": "d",
                                          "notation": "n", "broader": [],
                                          "inScheme": termgov.METRIC_SCHEME}},
                    "aliases": {}, "classes": {}}
        report = termgov.diff_snapshots({}, snapshot)
        self.assertFalse(report["verdict"]["mayPublish"])

    def test_diff_hash_is_stable_for_same_input(self):
        first = termgov.diff_snapshots(termgov.parse_skos(BASE), termgov.parse_skos(INCOMING))
        second = termgov.diff_snapshots(termgov.parse_skos(BASE), termgov.parse_skos(INCOMING))
        self.assertEqual(first["diffHash"], second["diffHash"])

    def test_unparsable_content_is_invalid_argument(self):
        with self.assertRaises(PortError) as ctx:
            termgov.parse_skos("not turtle {", "turtle")
        self.assertEqual(ctx.exception.provider_code, "E_TERM_PARSE_FAILED")


class CoverageTests(unittest.TestCase):
    def test_coverage_against_documented_baseline(self):
        report = termgov.coverage(termgov.parse_skos(BASE))
        self.assertEqual(report["expected"]["concepts"], 85)
        self.assertEqual(report["expected"]["aliases"], 18)
        self.assertEqual(report["actual"]["concepts"], 2)
        self.assertEqual(report["coverage"]["missingConcepts"], 83)
        self.assertFalse(report["complete"])
        self.assertEqual(report["actual"]["conceptPrefCoverage"], 1.0)
        self.assertIn("设计文档", report["expected"]["note"])

    def test_baseline_can_be_overridden(self):
        report = termgov.coverage(termgov.parse_skos(BASE), expect_concepts=2,
                                  expect_aliases=0)
        self.assertTrue(report["complete"])

    def test_graph_coverage_empty_state(self):
        runtime = _runtime()
        runtime.ontology = SimpleNamespace(current=lambda: {})
        report = termgov.graph_coverage(runtime)
        self.assertTrue(report["empty"])
        self.assertIn("指针不存在", report["emptyReason"])
        self.assertIsNone(report["actual"])

    def test_graph_coverage_reads_published_terms(self):
        report = termgov.graph_coverage(_runtime(), expect_concepts=2, expect_aliases=1)
        self.assertFalse(report["empty"])
        self.assertEqual(report["actual"]["concepts"], 2)
        self.assertEqual(report["actual"]["aliases"], 1)
        self.assertEqual(report["actual"]["aliasesWithTarget"], 1)


class RouteTests(unittest.TestCase):
    def test_coverage_route(self):
        client = TestClient(api_module.create_app(_runtime(), []))
        with client:
            response = client.get("/ontology/terms/coverage",
                                  params={"expectConcepts": 2, "expectAliases": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["actual"]["concepts"], 2)

    def test_diff_route_records_check_and_requires_content(self):
        runtime = _runtime()
        client = TestClient(api_module.create_app(runtime, []))
        with client:
            response = client.post("/ontology/terms/diff", json={"content": BASE})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["verdict"]["mayPublish"])
            self.assertTrue(any("INSERT INTO platform.term_check" in sql
                                for sql, _ in runtime.metadata.statements))
            response = client.post("/ontology/terms/diff", json={"content": " "})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["error"]["providerCode"],
                             "E_TERM_CONTENT_REQUIRED")

    def test_import_refuses_blocking_diff_and_accepts_clean_one(self):
        runtime = _runtime()
        client = TestClient(api_module.create_app(runtime, []))
        with client:
            blocked = client.post("/ontology/terms/import",
                                  json={"content": CONFLICT, "dryRun": False})
            self.assertEqual(blocked.status_code, 409)
            self.assertEqual(blocked.json()["error"]["providerCode"],
                             termgov.E_TERM_CHECK_FAILED)
            ok = client.post("/ontology/terms/import",
                             json={"content": BASE, "dryRun": False, "sourceName": "m.ttl"})
            self.assertEqual(ok.status_code, 200)
            self.assertEqual(ok.json()["status"], "checked")
            self.assertIn("next", ok.json())
            dry = client.post("/ontology/terms/import", json={"content": BASE})
            self.assertTrue(dry.json()["dryRun"])

    def test_checks_route(self):
        client = TestClient(api_module.create_app(_runtime(), []))
        with client:
            response = client.get("/ontology/terms/checks")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
