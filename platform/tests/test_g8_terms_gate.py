"""O-05 G8: terminology gate on the T-Box publish path.

Unit part runs anywhere:
  python test_g8_terms_gate.py

Live part needs the already-running postgres/oxigraph/reasoner (no rebuild):
  docker run --rm --entrypoint python -e PYTHONPATH=/hostsrc \
    -v <repo>/src:/hostsrc:ro -v <repo>/tests:/hosttests:ro \
    agent-platform:0.1-s5 /hosttests/test_g8_terms_gate.py

The live tests use urn:s14term: and restore the pointer and delete their
version/graph/evidence rows in tearDown.
"""

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import yaml
from fastapi.testclient import TestClient

import platform_core.api as api_module
import platform_core.config as config_module
from platform_core import termgate, termgov
from platform_core.adapters.graph_oxigraph import OxigraphHttpStore
from platform_core.adapters.metadata_pg import MetadataPg
from platform_core.adapters.ontology_pg import (
    OntologyRegistry,
    _import_version_id,
    build_import_document,
    persist_import,
)
from platform_core.adapters.reasoner_robot import ReasonerClient
from platform_core.config import (
    DEFAULT_TERMS_BLOCKING_CODES,
    OntologyConfig,
    ReasoningConfig,
    TermsConfig,
    load_config,
)
from platform_core.errors import EXIT_CONFIG, PlatformError
from platform_core.validation import ShaclValidator

BASE = {"database": {"url": "postgresql://platform:platform_dev@postgres:5432/platform"}}

SKOS_PREFIX = """\
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix term: <https://w3id.org/fsldm/terms#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
"""

DUPLICATE_TTL = SKOS_PREFIX + """
<urn:s14term:MetricScheme> a skos:ConceptScheme .
<urn:s14term:A> a skos:Concept ;
    skos:inScheme <urn:s14term:MetricScheme> ;
    skos:prefLabel "共享名"@zh ; skos:definition "A 概念" ; skos:notation "A" .
<urn:s14term:B> a skos:Concept ;
    skos:inScheme <urn:s14term:MetricScheme> ;
    skos:prefLabel "共享名"@zh ; skos:definition "B 概念" ; skos:notation "B" .
<urn:s14term:Widget> a owl:Class ; rdfs:label "Widget"@en .
"""

ALIAS_MISSING_TARGET_TTL = SKOS_PREFIX + """
<urn:s14term:Entry> a term:TermEntry ;
    term:label "孤立别名" ;
    term:forClass <urn:s14term:NotImported> .
"""

DEFINITION_GAP_TTL = SKOS_PREFIX + """
<urn:s14term:C> a skos:Concept ; skos:prefLabel "C"@zh .
"""

ROOT_SHAPES_TTL = """\
@prefix sh: <http://www.w3.org/ns/shacl#> .

<urn:test:shape:Noop> a sh:NodeShape .
"""

SHAPES_TTL = """\
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<urn:s14term:shape:ClassLabel> a sh:NodeShape ;
    sh:targetClass owl:Class ;
    sh:property [ sh:path rdfs:label ; sh:minCount 1 ] .
"""


def load(overrides: dict, environ: dict | None = None):
    doc = dict(BASE)
    for key, value in overrides.items():
        if isinstance(value, dict):
            doc.setdefault(key, {}).update(value)
        else:
            doc[key] = value
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as handle:
        yaml.safe_dump(doc, handle)
        path = handle.name
    try:
        return load_config(path, environ=environ or {})
    finally:
        Path(path).unlink(missing_ok=True)


class TermsConfigTests(unittest.TestCase):
    def _assert_error(self, overrides: dict, code: str) -> None:
        with self.assertRaises(PlatformError) as ctx:
            load(overrides)
        self.assertEqual(ctx.exception.code, code, ctx.exception.detail)
        self.assertEqual(ctx.exception.key, "terms.gate")
        self.assertEqual(ctx.exception.exit_code, EXIT_CONFIG)

    def test_1_default_is_warn(self):
        bundle = load({})
        self.assertEqual(bundle.config.terms.gate, "warn")
        self.assertEqual(
            bundle.config.terms.blocking_codes, list(DEFAULT_TERMS_BLOCKING_CODES)
        )
        self.assertEqual(bundle.config.terms.coverage_decrease_tolerance, 0.0)

    def test_2_unknown_gate_is_provider_invalid(self):
        self._assert_error({"terms": {"gate": "strict"}}, "E_PROVIDER_INVALID")

    def test_3_known_but_unimplemented_uses_its_own_code(self):
        # No shipped value is known-but-unimplemented today. Patching the
        # implemented tuple proves the Q8 split without inventing a config value.
        with mock.patch.object(config_module, "TERMS_GATE_IMPLEMENTED", ("off", "warn")):
            self._assert_error({"terms": {"gate": "block"}}, "E_PROVIDER_NOT_IMPLEMENTED")

    def test_4_env_override_sets_block(self):
        bundle = load({}, environ={"PLATFORM__TERMS__GATE": "block"})
        self.assertEqual(bundle.config.terms.gate, "block")

    def test_5_blocking_codes_are_configurable(self):
        bundle = load({"terms": {"blocking_codes": ["CONCEPT_MISSING_DEFINITION"]}})
        self.assertEqual(bundle.config.terms.blocking_codes, ["CONCEPT_MISSING_DEFINITION"])

    def test_6_off_is_accepted_and_announced(self):
        bundle = load({"terms": {"gate": "off"}})
        self.assertEqual(bundle.config.terms.gate, "off")
        self.assertTrue(any("terms.gate=off" in item for item in bundle.warnings))


class GateSemanticsTests(unittest.TestCase):
    def _snapshot(self, ttl: str):
        return termgov.parse_skos(ttl, "turtle")

    def test_1_off_returns_none(self):
        snapshot = self._snapshot(DUPLICATE_TTL)
        self.assertIsNone(termgate.evaluate_snapshot(snapshot, TermsConfig(gate="off")))

    def test_2_warn_never_blocks_and_records_counts(self):
        result = termgate.evaluate_snapshot(
            self._snapshot(DUPLICATE_TTL), TermsConfig(gate="warn")
        )
        self.assertEqual(result["gate"], "warn")
        self.assertEqual(result["verdict"], "warned")
        self.assertFalse(result["blocked"])
        self.assertFalse(result["enforced"])
        self.assertEqual(result["blocking"], 1)
        self.assertEqual(result["total"], 1)
        codes = [item["code"] for item in result["findings"]]
        self.assertIn("SURFACE_SHARED_BY_MULTIPLE_CONCEPTS", codes)

    def test_3_block_blocks_only_on_blocking_codes(self):
        result = termgate.evaluate_snapshot(
            self._snapshot(DUPLICATE_TTL), TermsConfig(gate="block")
        )
        self.assertTrue(result["blocked"])
        self.assertEqual(result["verdict"], "blocked")
        self.assertTrue(result["enforced"])

        clean = termgate.evaluate_snapshot(
            self._snapshot(DEFINITION_GAP_TTL), TermsConfig(gate="block")
        )
        self.assertFalse(clean["blocked"])
        self.assertEqual(clean["verdict"], "warned")

    def test_4_alias_missing_target_is_blocking_by_default(self):
        result = termgate.evaluate_snapshot(
            self._snapshot(ALIAS_MISSING_TARGET_TTL), TermsConfig(gate="block")
        )
        alias = [
            item for item in result["findings"]
            if item["code"] == "ALIAS_TARGET_MISSING"
        ]
        self.assertEqual(len(alias), 1)
        self.assertTrue(alias[0]["blocking"])
        self.assertEqual(alias[0]["severity"], "blocking")
        self.assertFalse(alias[0]["defaultBlocking"])
        self.assertTrue(result["blocked"])

    def test_5_severity_threshold_is_reconfigurable(self):
        result = termgate.evaluate_snapshot(
            self._snapshot(DEFINITION_GAP_TTL),
            TermsConfig(gate="block", blocking_codes=["CONCEPT_MISSING_DEFINITION"]),
        )
        self.assertTrue(result["blocked"])
        self.assertEqual(result["blocking"], 1)

    def test_6_coverage_decline_is_warning_and_tolerance_is_honoured(self):
        snapshot = self._snapshot(DEFINITION_GAP_TTL)
        baseline = {
            "actual": {
                "conceptPrefCoverage": 1.0,
                "conceptDefinitionCoverage": 1.0,
                "conceptNotationCoverage": 1.0,
                "aliasTargetCoverage": None,
            }
        }
        result = termgate.evaluate_snapshot(
            snapshot, TermsConfig(gate="warn"), baseline=baseline
        )
        declines = [
            item for item in result["findings"]
            if item["code"] == termgate.COVERAGE_DECREASE_CODE
        ]
        self.assertTrue(declines)
        self.assertTrue(all(not item["blocking"] for item in declines))

        tolerant = termgate.evaluate_snapshot(
            snapshot,
            TermsConfig(gate="warn", coverage_decrease_tolerance=1.0),
            baseline=baseline,
        )
        self.assertFalse(
            [
                item for item in tolerant["findings"]
                if item["code"] == termgate.COVERAGE_DECREASE_CODE
            ]
        )


DSN = os.environ.get(
    "TEST_PG_DSN",
    os.environ.get(
        "PLATFORM__DATABASE__URL",
        "postgres://platform:***MASKED***@host.docker.internal:5432/platform",
    ),
)
OXIGRAPH_URL = os.environ.get("TEST_OXIGRAPH_URL", "http://host.docker.internal:7878")
REASONER_URL = os.environ.get("TEST_REASONER_URL", "http://host.docker.internal:7879")
POINTER_NAME = "tbox/current"
NAMESPACE = "urn:s14term:"


class _FakeObjects:
    def __init__(self):
        self.store: dict[tuple[str, str], bytes] = {}

    def put(self, bucket, key, body, content_type="application/octet-stream", metadata=None):
        self.store[(bucket, key)] = bytes(body)
        return {"bucket": bucket, "key": key, "size": len(self.store[(bucket, key)])}

    def get(self, bucket, key):
        return self.store[(bucket, key)], {}


class PublishGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = MetadataPg(DSN)
        cls.meta.open(retry_seconds=15)
        cls.graph = OxigraphHttpStore(OXIGRAPH_URL)
        cls.objects = _FakeObjects()
        cls.registry = OntologyRegistry(cls.meta, cls.graph, cls.objects, OntologyConfig())
        cls.reasoner = ReasonerClient(
            ReasoningConfig(endpoint=REASONER_URL, timeout_ms=120000, profile="EL")
        )
        cls.registry.set_governance(
            validator=ShaclValidator(ReasoningConfig(shapes_dir=cls._root_shapes_dir())),
            reasoner=cls.reasoner,
            materializer=lambda: {"jobId": "job-stub", "inferred": 0, "skipped": True},
            abox_graphs=[],
            reason_profile="EL",
        )
        cls.terms = TermsConfig(gate="warn")
        cls.registry.set_terms_gate(cls.terms)
        runtime = SimpleNamespace(
            metadata=cls.meta,
            graph=cls.graph,
            objects=cls.objects,
            ontology=cls.registry,
            config=SimpleNamespace(
                mode="test",
                config_version=1,
                runtime=SimpleNamespace(mode="test"),
                reasoning=ReasoningConfig(endpoint=REASONER_URL, profile="EL"),
                terms=cls.terms,
            ),
        )
        cls.client = TestClient(api_module.create_app(runtime, []))
        cls.client.__enter__()

    @classmethod
    def _root_shapes_dir(cls) -> str:
        directory = Path(tempfile.mkdtemp())
        (directory / "core.ttl").write_text(ROOT_SHAPES_TTL, encoding="utf-8")
        return str(directory)

    @classmethod
    def _namespace_shapes_dir(cls) -> str:
        directory = Path(tempfile.mkdtemp())
        segment = directory / "s14term"
        segment.mkdir()
        (segment / "shapes.ttl").write_text(SHAPES_TTL, encoding="utf-8")
        (segment / "manifest.json").write_text(
            '{"id": "s14term-shapes", "version": "0.2.0"}', encoding="utf-8"
        )
        return str(directory)

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        cls.reasoner.close()
        cls.graph.close()
        cls.meta.close()

    def setUp(self):
        self.created: list[dict] = []
        rows = self.meta.query(
            "SELECT version_id, updated_by FROM platform.graph_pointer WHERE name = %s",
            (POINTER_NAME,),
        )
        self.original_pointer = rows[0]["version_id"] if rows else None
        status = self.meta.query(
            "SELECT status FROM platform.ontology_version WHERE version_id = %s",
            (self.original_pointer,) if self.original_pointer else (None,),
        )
        self.original_status = status[0]["status"] if status else "published"

    def tearDown(self):
        self.registry.set_terms_gate(None)
        if self.original_pointer:
            with self.meta.tx() as tx:
                tx.execute(
                    """
                    INSERT INTO platform.graph_pointer (name, version_id, updated_at, updated_by)
                    VALUES (%s, %s, now(), 'test-cleanup')
                    ON CONFLICT (name) DO UPDATE
                      SET version_id = EXCLUDED.version_id, updated_at = now()
                    """,
                    (POINTER_NAME, self.original_pointer),
                )
                tx.execute(
                    "UPDATE platform.ontology_version SET status = %s WHERE version_id = %s",
                    (self.original_status, self.original_pointer),
                )
        for record in self.created:
            version_id = _import_version_id(record["importId"])
            with self.meta.tx() as tx:
                tx.execute(
                    "DELETE FROM platform.ontology_evidence WHERE version_id = %s", (version_id,)
                )
                tx.execute(
                    "DELETE FROM platform.ontology_proposal WHERE version_id = %s", (version_id,)
                )
                tx.execute(
                    "DELETE FROM platform.ontology_event WHERE version_id = %s", (version_id,)
                )
                tx.execute(
                    "DELETE FROM platform.ontology_event WHERE action = 'superseded' "
                    "AND payload->>'replacedBy' = %s",
                    (version_id,),
                )
                tx.execute(
                    "DELETE FROM platform.ontology_version WHERE version_id = %s", (version_id,)
                )
                tx.execute(
                    "DELETE FROM platform.ontology_import WHERE import_id = %s",
                    (record["importId"],),
                )
            for graph_iri in (record["stagingGraph"], f"urn:platform:graph:tbox:{version_id}"):
                try:
                    self.graph.update(f"DROP SILENT GRAPH <{graph_iri}>")
                except Exception:
                    pass
        self.created = []

    def _consistency(self, tbox_nt: bytes):
        return self.reasoner.reason(tbox_nt, b"", profile="EL", consistency_first=True)

    def _import(self, ttl: str, author: str):
        result, merged = build_import_document(
            ttl.encode("utf-8"),
            target_namespace=NAMESPACE,
            author=author,
            change_summary="G8 gate test",
            shapes_dir=self._namespace_shapes_dir(),
            consistency_checker=self._consistency,
        )
        record = persist_import(result, merged, ttl.encode("utf-8"), self.meta, self.graph)
        self.created.append(record)
        return record

    def _publish(self, import_id: str, dry_run: bool):
        response = self.client.post(
            f"/ontology/imports/{import_id}/publish",
            json={"dryRun": dry_run, "acknowledgeBreaking": not dry_run},
        )
        return response

    def _version_rows(self, version_id: str) -> list[dict]:
        return self.meta.query(
            "SELECT version_id FROM platform.ontology_version WHERE version_id = %s",
            (version_id,),
        )

    def _evidence(self, version_id: str) -> list[dict]:
        return self.meta.query(
            "SELECT payload FROM platform.ontology_evidence WHERE version_id = %s "
            "ORDER BY created_at DESC",
            (version_id,),
        )

    def test_7_off_is_byte_identical_to_the_legacy_dry_run_payload(self):
        record = self._import(DUPLICATE_TTL, "g8off")
        self.registry.set_terms_gate(TermsConfig(gate="off"))
        baseline_keys = {
            "importId", "versionId", "previousVersionId", "pointer", "dryRun",
            "diff", "impact", "usable", "reason", "canonicalEqualTo",
            "published", "publishedAt", "publishExisting",
        }
        with mock.patch.object(
            termgate, "evaluate_content", side_effect=AssertionError("off must not evaluate")
        ):
            response = self._publish(record["importId"], dry_run=True)
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(set(payload), baseline_keys)
        self.assertNotIn("termsGate", payload)
        self.assertNotIn("terms", (payload.get("gates") or {}))

    def test_8_warn_publishes_and_records_the_gate_in_evidence(self):
        record = self._import(DUPLICATE_TTL, "g8warn")
        self.registry.set_terms_gate(TermsConfig(gate="warn"))
        response = self._publish(record["importId"], dry_run=False)
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertTrue(payload["published"])
        gate = payload["termsGate"]
        self.assertEqual(gate["gate"], "warn")
        self.assertEqual(gate["verdict"], "warned")
        self.assertEqual(gate["blocking"], 1)
        self.assertFalse(gate["blocked"])
        self.assertIn("terms", payload["gates"])
        self.assertEqual(payload["gates"]["terms"]["blocking"], 1)
        packs = self._evidence(payload["versionId"])
        self.assertEqual(len(packs), 1)
        stored = packs[0]["payload"]
        self.assertIn("terms", stored["gates"])
        self.assertEqual(stored["gates"]["terms"]["blocking"], 1)

        dashboard = self.client.get("/health/dashboard")
        self.assertEqual(dashboard.status_code, 200, dashboard.text)
        terms_block = dashboard.json()["termsGate"]
        self.assertEqual(terms_block["configuredGate"], "warn")
        self.assertEqual(terms_block["last"]["blocking"], 1)
        self.assertFalse(terms_block["empty"])

    def test_9_block_refuses_before_any_write(self):
        record = self._import(DUPLICATE_TTL, "g8block")
        self.registry.set_terms_gate(TermsConfig(gate="block"))
        version_id = _import_version_id(record["importId"])
        tbox_graph = f"urn:platform:graph:tbox:{version_id}"
        before_pointer = self.registry.current()
        before_versions = self._version_rows(version_id)
        before_proposals = self.meta.query(
            "SELECT proposal_id FROM platform.ontology_proposal WHERE version_id = %s",
            (version_id,),
        )
        before_events = self.meta.query(
            "SELECT event_id FROM platform.ontology_event WHERE version_id = %s",
            (version_id,),
        )
        before_evidence = self._evidence(version_id)
        before_tbox = self.graph.count_graph(tbox_graph)

        response = self._publish(record["importId"], dry_run=False)
        self.assertEqual(response.status_code, 409, response.text)
        error = response.json()["error"]
        self.assertEqual(error["providerCode"], "E_TERM_GATE_BLOCKED")
        self.assertEqual(error["details"]["blocking"], 1)
        self.assertTrue(error["details"]["allowed"])
        self.assertTrue(error["details"]["problems"])

        pointer = self.registry.current()
        self.assertEqual((pointer or {}).get("versionId"), (before_pointer or {}).get("versionId"))
        self.assertEqual(self._version_rows(version_id), before_versions)
        self.assertEqual(
            self.meta.query(
                "SELECT proposal_id FROM platform.ontology_proposal WHERE version_id = %s",
                (version_id,),
            ),
            before_proposals,
        )
        self.assertEqual(
            self.meta.query(
                "SELECT event_id FROM platform.ontology_event WHERE version_id = %s",
                (version_id,),
            ),
            before_events,
        )
        self.assertEqual(self._evidence(version_id), before_evidence)
        self.assertEqual(self.graph.count_graph(tbox_graph), before_tbox)

    def test_10_block_passes_when_no_blocking_finding_exists(self):
        record = self._import(DEFINITION_GAP_TTL, "g8blockpass")
        self.registry.set_terms_gate(TermsConfig(gate="block"))
        response = self._publish(record["importId"], dry_run=False)
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertTrue(payload["published"])
        self.assertEqual(payload["termsGate"]["verdict"], "warned")
        self.assertFalse(payload["termsGate"]["blocked"])

    def test_11_gate_status_endpoint_is_null_with_reason_before_publish(self):
        self.registry._last_terms_gate = None
        self.registry.set_terms_gate(TermsConfig(gate="warn"))
        response = self.client.get("/ontology/terms/gate")
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["configuredGate"], "warn")
        self.assertIsNone(payload["last"])
        self.assertTrue(payload["empty"])
        self.assertTrue(payload["emptyReason"])

        dashboard = self.client.get("/health/dashboard")
        self.assertEqual(dashboard.status_code, 200, dashboard.text)
        terms_block = dashboard.json()["termsGate"]
        self.assertIsNone(terms_block["last"])
        self.assertTrue(terms_block["empty"])
        self.assertTrue(terms_block["emptyReason"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
