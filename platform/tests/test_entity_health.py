"""B-03/B-04 read-only tests: entity detail, health dashboard, ontology diff.

Pure API tests with small metadata/graph/ontology fakes; no postgres/oxigraph.
Run with:
  docker run --rm --entrypoint python -e PYTHONPATH=/hostsrc \
    -v <repo>/src:/hostsrc:ro -v <repo>/tests:/hosttests:ro \
    agent-platform:0.1-s5 /hosttests/test_entity_health.py
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

sys.path.insert(0, os.environ.get("PLATFORM_SRC", "/app/src"))
sys.path.insert(0, "../src")

import platform_core.api as api_module
from platform_core.errors import PortError

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
ENTITY = "urn:platform:synthetic/account#Account-00001"
CLASS_ACCOUNT = "urn:onto#Account"
CLASS_PARTY = "urn:onto#Party"
CLASS_THING = "urn:onto#Thing"
PROP_ACCOUNT_ID = "urn:onto#accountId"
PROP_MEMBER_OF = "urn:onto#memberOf"

TB = "urn:platform:graph:tbox:ont-test"
ABOX = "urn:platform:graph:abox:main"
INFERRED = "urn:platform:graph:inferred:ont-test"

POINTER = {
    "name": "tbox/current",
    "versionId": "ont-test",
    "semver": "1.0.0",
    "graph": TB,
    "updatedAt": "2026-01-01T00:00:00Z",
}


def _iri(value):
    return {"kind": "iri", "iri": value}


def _lit(value):
    return {"kind": "literal", "value": str(value)}


def _row(**terms):
    return {"values": {name: value for name, value in terms.items()}}


def _rows(items):
    return {"kind": "select", "variables": [], "bindings": list(items)}


class FakeGraph:
    def __init__(
        self,
        *,
        edges_by_graph=None,
        class_rows=None,
        restriction_rows=None,
        property_label_rows=None,
        class_coverage_rows=None,
        property_rows=None,
        used_predicate_rows=None,
        instance_count_rows=None,
        instance_total=0,
        orphans=0,
        prov_rows=None,
        diff_rows=None,
    ):
        self.edges_by_graph = edges_by_graph or {}
        self.class_rows = class_rows or []
        self.restriction_rows = restriction_rows or []
        self.property_label_rows = property_label_rows or []
        self.class_coverage_rows = class_coverage_rows or []
        self.property_rows = property_rows or []
        self.used_predicate_rows = used_predicate_rows or []
        self.instance_count_rows = instance_count_rows or []
        self.instance_total = instance_total
        self.orphans = orphans
        self.prov_rows = prov_rows or []
        self.diff_rows = diff_rows or {"added": [], "removed": []}
        self.calls = []

    def ask(self, sparql):
        return True

    def query(self, sparql):
        self.calls.append(sparql)
        if "?activity" in sparql and "prov:used" in sparql.replace("#", "%23"):
            return _rows(self.prov_rows)
        if "?activity <" in sparql:
            return _rows(self.prov_rows)
        if "#onProperty" in sparql:
            return _rows(self.restriction_rows)
        if "FILTER NOT EXISTS" in sparql:
            return _rows([_row(n=_lit(self.orphans))])
        if "?c (COUNT(DISTINCT ?s)" in sparql:
            return _rows(self.instance_count_rows)
        if "COUNT(DISTINCT ?s) AS ?n" in sparql:
            return _rows([_row(n=_lit(self.instance_total))])
        if "?parent" in sparql:
            return _rows(self.class_rows)
        if "?c ?label ?pref" in sparql:
            return _rows(self.class_coverage_rows)
        if "rdf-schema#label" in sparql and "?p" in sparql:
            return _rows(self.property_label_rows)
        if "?p a ?t" in sparql:
            return _rows(self.property_rows)
        if "DISTINCT ?p" in sparql:
            return _rows(self.used_predicate_rows)
        if "MINUS" in sparql:
            if "GRAPH <" in sparql:
                position = sparql.find("MINUS")
                from_graph = getattr(self, "from_graph", None)
                to_graph = getattr(self, "to_graph", None)
                removed = (
                    from_graph is not None
                    and sparql.find(f"<{from_graph}>") > -1
                    and sparql.find(f"<{from_graph}>") < position
                )
                if to_graph is not None and to_graph in sparql:
                    removed = (
                        from_graph is not None
                        and sparql.find(f"<{from_graph}>") < sparql.find(f"<{to_graph}>")
                    )
                key = "removed" if removed else "added"
                return _rows(self.diff_rows.get(key, []))
            return _rows([])
        if "BIND(<" in sparql:
            bindings = []
            for graph, items in self.edges_by_graph.items():
                if f"<{graph}>" not in sparql:
                    continue
                for subject, predicate, obj in items:
                    bindings.append(
                        _row(
                            g=_iri(graph),
                            s=_iri(subject),
                            p=_iri(predicate),
                            o=obj,
                        )
                    )
            return _rows(bindings)
        return _rows([])


class FakeMetadata:
    def __init__(self, *, bindings=None, import_row=None, jobs=0, schema_version=30):
        self.bindings = bindings or []
        self.import_row = import_row
        self.jobs = jobs
        self.schema_version = schema_version
        self.calls = []

    def health(self):
        return None

    def query(self, sql, params=()):
        self.calls.append((sql, params))
        if "metric_field_binding" in sql:
            return list(self.bindings)
        if "ontology_import" in sql:
            return [self.import_row] if self.import_row else []
        if "reasoning_job" in sql:
            return [{"n": self.jobs}]
        if "schema_version" in sql:
            return [{"v": self.schema_version}]
        return []


class FakeOntology:
    def __init__(self, *, pointer=POINTER, versions=None, rows=None, diff=None):
        self.pointer = pointer
        self.versions = versions or []
        self.rows = rows or {}
        self.diff_result = diff or {}

    def current(self):
        return self.pointer

    def list_versions(self):
        return self.versions

    def get(self, version_id):
        if version_id not in self.rows:
            raise PortError(
                code="NotFound",
                message="missing",
                provider="postgres",
                provider_code="E_ONTOLOGY_VERSION_NOT_FOUND",
            )
        return self.rows[version_id]

    def diff(self, from_version, to_version):
        return self.diff_result


def _runtime(*, metadata, graph, ontology, reasoning=None, root=None):
    root = root or tempfile.mkdtemp()
    blobs = Path(root) / "blobs"
    blobs.mkdir(exist_ok=True)
    reasoning = reasoning or SimpleNamespace(
        status=lambda: {"aboxGraphs": [ABOX], "profile": "owl-rl", "pointer": None},
        last_job=lambda: None,
    )
    return SimpleNamespace(
        metadata=metadata,
        graph=graph,
        ontology=ontology,
        reasoning=reasoning,
        config=SimpleNamespace(storage=SimpleNamespace(root=root, min_free_pct=1)),
    )


def _client(runtime):
    return TestClient(api_module.create_app(runtime, []))


class HealthDashboardTests(unittest.TestCase):
    def test_1_dashboard_aggregates_with_explicit_sources(self):
        graph = FakeGraph(
            class_coverage_rows=[
                _row(c=_iri(CLASS_ACCOUNT), label=_lit("账户")),
                _row(c=_iri(CLASS_PARTY), label=_lit("参与方")),
                _row(c=_iri(CLASS_THING)),
                _row(c=_iri("urn:onto#Product"), pref=_lit("产品")),
            ],
            property_rows=[
                _row(p=_iri(PROP_ACCOUNT_ID)),
                _row(p=_iri(PROP_MEMBER_OF)),
                _row(p=_iri("urn:onto#p3")),
                _row(p=_iri("urn:onto#p4")),
                _row(p=_iri("urn:onto#p5")),
            ],
            used_predicate_rows=[
                _row(p=_iri(RDF + "type")),
                _row(p=_iri(PROP_ACCOUNT_ID)),
                _row(p=_iri(PROP_MEMBER_OF)),
            ],
            instance_count_rows=[
                _row(c=_iri(CLASS_ACCOUNT), n=_lit(10)),
                _row(c=_iri(CLASS_PARTY), n=_lit(2)),
            ],
            instance_total=12,
            orphans=1,
        )
        metadata = FakeMetadata(
            import_row={
                "import_id": "imp-1",
                "version_id": "ont-test",
                "conforms": False,
                "violation_count": 12,
                "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
            },
            jobs=3,
            schema_version=30,
        )
        runtime = _runtime(metadata=metadata, graph=graph, ontology=FakeOntology())
        with _client(runtime) as client:
            response = client.get("/health/dashboard")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIs(payload["readOnly"], True)
        self.assertEqual(payload["coverage"]["classes"]["total"], 4)
        self.assertEqual(payload["coverage"]["classes"]["withInstances"], 2)
        self.assertEqual(payload["coverage"]["classes"]["unlabeled"], 1)
        self.assertEqual(payload["coverage"]["classes"]["ratio"], 0.5)
        self.assertEqual(payload["coverage"]["properties"]["withValues"], 2)
        self.assertEqual(payload["coverage"]["instances"]["total"], 12)
        self.assertEqual(payload["orphanInstances"]["count"], 1)
        self.assertEqual(payload["shaclViolations"]["count"], 12)
        self.assertEqual(payload["inferenceFailures"]["count"], 3)
        self.assertIs(payload["migration"]["consistent"], True)
        self.assertEqual(payload["readyz"]["status"], "ok")
        self.assertEqual(payload["tbox"]["versionId"], "ont-test")
        self.assertTrue(payload["dataSource"]["sampledAt"])
        self.assertIn("GET /health/dashboard", payload["dataSource"]["endpoints"])

    def test_2_missing_tbox_pointer_returns_null_not_zero(self):
        graph = FakeGraph(instance_total=5)
        runtime = _runtime(
            metadata=FakeMetadata(),
            graph=graph,
            ontology=FakeOntology(pointer=None),
        )
        with _client(runtime) as client:
            payload = client.get("/health/dashboard").json()
        self.assertIsNone(payload["coverage"]["classes"]["total"])
        self.assertIn("tbox/current", payload["coverage"]["classes"]["error"])
        self.assertEqual(payload["coverage"]["instances"]["total"], 5)


class OntologyDiffTests(unittest.TestCase):
    def _diff_runtime(self, *, pointer=POINTER, versions=None):
        versions = versions or [
            {"id": "v1", "semver": "1.0.0", "status": "superseded"},
            {"id": "ont-test", "semver": "1.1.0", "status": "published"},
        ]
        summary = {
            "summary": {
                "addedTriples": 40,
                "removedTriples": 7,
                "addedClasses": [f"urn:new#C{i}" for i in range(6)],
                "removedClasses": [f"urn:old#C{i}" for i in range(6)],
                "addedProperties": [f"urn:new#P{i}" for i in range(6)],
                "removedProperties": [f"urn:old#P{i}" for i in range(6)],
            }
        }
        graph = FakeGraph(
            diff_rows={
                "added": [
                    _row(
                        s=_iri(f"urn:new#s{i}"),
                        p=_iri(f"urn:new#p{i}"),
                        o=_lit(f"o{i}"),
                    )
                    for i in range(6)
                ],
                "removed": [
                    _row(
                        s=_iri(f"urn:old#s{i}"),
                        p=_iri(f"urn:old#p{i}"),
                        o=_lit(f"o{i}"),
                    )
                    for i in range(6)
                ],
            }
        )
        graph.from_graph = "urn:platform:graph:tbox:v1"
        graph.to_graph = TB
        ontology = FakeOntology(
            pointer=pointer,
            versions=versions,
            rows={
                "v1": {"id": "v1", "semver": "1.0.0", "graph": graph.from_graph},
                "ont-test": {"id": "ont-test", "semver": "1.1.0", "graph": TB},
            },
            diff=summary,
        )
        return _runtime(metadata=FakeMetadata(), graph=graph, ontology=ontology)

    def test_3_diff_explicit_versions_returns_counts_and_5_examples(self):
        runtime = self._diff_runtime()
        with _client(runtime) as client:
            response = client.get(
                "/health/ontology-diff", params={"from": "v1", "to": "ont-test"}
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIs(payload["readOnly"], True)
        self.assertEqual(payload["counts"]["addedTriples"], 40)
        self.assertEqual(payload["counts"]["addedClasses"], 6)
        self.assertEqual(len(payload["examples"]["addedClasses"]), 5)
        self.assertEqual(len(payload["examples"]["removedProperties"]), 5)
        self.assertEqual(len(payload["examples"]["addedTriples"]), 5)
        self.assertEqual(len(payload["examples"]["removedTriples"]), 5)
        self.assertTrue(payload["sampledAt"])

    def test_4_default_diff_uses_current_and_previous(self):
        runtime = self._diff_runtime()
        with _client(runtime) as client:
            payload = client.get("/health/ontology-diff").json()
        self.assertEqual(payload["from"], "v1")
        self.assertEqual(payload["to"], "ont-test")

    def test_5_unknown_version_returns_stable_error_code(self):
        runtime = self._diff_runtime()
        with _client(runtime) as client:
            response = client.get(
                "/health/ontology-diff", params={"from": "no-such", "to": "ont-test"}
            )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["providerCode"], "E_DIFF_VERSION_NOT_FOUND"
        )

    def test_6_post_is_rejected(self):
        runtime = self._diff_runtime()
        with _client(runtime) as client:
            response = client.post("/health/ontology-diff")
        self.assertEqual(response.status_code, 405)


class EntityViewTests(unittest.TestCase):
    def _runtime_for(self, *, asserted, inferred=None, binding_rows=None):
        edges = {ABOX: asserted}
        if inferred:
            edges[INFERRED] = inferred
        graph = FakeGraph(
            edges_by_graph=edges,
            class_rows=[
                _row(c=_iri(CLASS_ACCOUNT), label=_lit("账户"), parent=_iri(CLASS_PARTY)),
                _row(c=_iri(CLASS_PARTY), label=_lit("参与方"), parent=_iri(CLASS_THING)),
                _row(c=_iri(CLASS_THING), label=_lit("事物")),
            ],
            restriction_rows=[
                _row(c=_iri(CLASS_ACCOUNT), p=_iri(PROP_ACCOUNT_ID), n=_lit(1)),
            ],
            property_label_rows=[
                _row(p=_iri(PROP_ACCOUNT_ID), label=_lit("账户号")),
            ],
            instance_count_rows=[_row(c=_iri(CLASS_ACCOUNT), n=_lit(12))],
            prov_rows=[],
        )
        metadata = FakeMetadata(
            bindings=binding_rows
            or [
                {
                    "metric_id": "FIN-BANK-001",
                    "role": "entity",
                    "fact_table": "platform.bank_loan_account",
                    "entity_column": "account_id",
                    "name_zh": "贷款余额",
                    "domain": "bank",
                    "grain": "account",
                    "publishable": True,
                }
            ]
        )
        reasoning = SimpleNamespace(
            status=lambda: {
                "aboxGraphs": [ABOX, INFERRED],
                "profile": "owl-rl",
                "pointer": {"targetGraph": INFERRED, "profile": "owl-rl", "jobId": "job-1"},
            },
            last_job=lambda: None,
        )
        return _runtime(
            metadata=metadata, graph=graph, ontology=FakeOntology(), reasoning=reasoning
        )

    def test_7_entity_evidenced_with_source_ref_and_metrics(self):
        source = "src://fact/platform.bank_loan_account?account_id=A1"
        asserted = [
            (ENTITY, RDF + "type", _iri(CLASS_ACCOUNT)),
            (ENTITY, RDFS + "label", _lit("张三账户")),
            (ENTITY, PROP_ACCOUNT_ID, _lit("A1")),
            (ENTITY, RDFS + "seeAlso", _lit(source)),
            (ENTITY, PROP_MEMBER_OF, _iri("urn:platform:synthetic/party#Party-1")),
        ]
        runtime = self._runtime_for(asserted=asserted)
        with _client(runtime) as client:
            payload = client.get("/ui/api/entity", params={"iri": ENTITY}).json()
        self.assertIs(payload["readOnly"], True)
        self.assertEqual(payload["evidenceBadge"]["state"], "evidenced")
        self.assertEqual(len(payload["sources"]), 1)
        self.assertEqual(
            payload["sources"][0]["href"],
            "/browse/facts?table=platform.bank_loan_account&limit=5",
        )
        self.assertEqual(payload["classes"][0]["iri"], CLASS_ACCOUNT)
        self.assertEqual(
            [item["iri"] for item in payload["classes"][0]["chain"]],
            [CLASS_ACCOUNT, CLASS_PARTY, CLASS_THING],
        )
        self.assertEqual(payload["instanceCount"], 12)
        self.assertEqual(payload["requiredProperties"][0]["label"], "账户号")
        self.assertIs(payload["requiredProperties"][0]["satisfied"], True)
        self.assertEqual(payload["relatedMetrics"]["status"], "bound")
        self.assertEqual(payload["relatedMetrics"]["items"][0]["metricId"], "FIN-BANK-001")
        self.assertIn(
            "entity_column=account_id",
            payload["relatedMetrics"]["items"][0]["matchBasis"],
        )

    def test_8_entity_inferred_badge_exposes_basis_and_judge(self):
        inferred = [
            (ENTITY, RDF + "type", _iri(CLASS_ACCOUNT)),
            (ENTITY, RDFS + "label", _lit("推理账户")),
        ]
        runtime = self._runtime_for(asserted=[], inferred=inferred)
        with _client(runtime) as client:
            payload = client.get("/ui/api/entity", params={"iri": ENTITY}).json()
        badge = payload["evidenceBadge"]
        self.assertEqual(badge["state"], "inferred")
        self.assertIn("owl-rl", badge["basis"])
        self.assertIn("job-1", badge["basis"])
        self.assertEqual(badge["judge"], "system:reasoning/owl-rl")
        self.assertEqual(payload["sources"], [])

    def test_9_entity_without_provenance_is_no_source(self):
        asserted = [
            (ENTITY, RDF + "type", _iri(CLASS_ACCOUNT)),
            (ENTITY, RDFS + "label", _lit("张三账户")),
        ]
        runtime = self._runtime_for(asserted=asserted)
        with _client(runtime) as client:
            payload = client.get("/ui/api/entity", params={"iri": ENTITY}).json()
        self.assertEqual(payload["evidenceBadge"]["state"], "no-source")
        self.assertEqual(payload["sources"], [])
        self.assertIn("未找到 sourceRef", payload["evidenceBadge"]["basis"])

    def test_10_bad_iri_is_rejected(self):
        runtime = self._runtime_for(asserted=[])
        with _client(runtime) as client:
            response = client.get("/ui/api/entity", params={"iri": "<bad iri>"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["providerCode"], "E_ENTITY_BAD_IRI")

    def test_11_unknown_entity_returns_not_found(self):
        runtime = self._runtime_for(asserted=[])
        with _client(runtime) as client:
            response = client.get("/ui/api/entity", params={"iri": ENTITY})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["providerCode"], "E_ENTITY_NOT_FOUND"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
