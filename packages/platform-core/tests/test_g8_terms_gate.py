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

import hashlib
import inspect
import os
import tempfile
import unittest
import uuid
from importlib.resources import files
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
    publish_import,
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
from platform_core.sqlsplit import split_sql_statements
from platform_core.validation import ShaclValidator

DSN = os.environ.get("TEST_PG_DSN")
BASE = {"database": {"url": DSN or "postgresql://test@127.0.0.1:1/test_offline"}}

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

# No MetricScheme concept at all: the effective term set is zero. Used by the
# vocab-zero guard tests (the old ratio checks produce no finding for it).
NO_TERMS_TTL = SKOS_PREFIX + """
<urn:s14term:NoTermsWidget> a owl:Class ; rdfs:label "NoTermsWidget"@en .
"""

NO_TERMS_NT = b"""\
<urn:s14term:NoTermsNT> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> \
<http://www.w3.org/2002/07/owl#Class> .
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

    # --- vocab-zero guard: effective term set vs high-water mark -----------

    def test_7_zero_drop_blocks_at_every_tier(self):
        snapshot = self._snapshot(NO_TERMS_TTL)
        for gate in ("off", "warn", "block"):
            with self.subTest(gate=gate):
                result = termgate.evaluate_snapshot(
                    snapshot,
                    TermsConfig(gate=gate),
                    high_water={"conceptsInScheme": 85, "aliases": 18,
                                "versionId": "ont-hw", "graph": "urn:platform:graph:tbox:ont-hw"},
                )
                self.assertIsNotNone(result)
                self.assertTrue(result["blocked"])
                self.assertEqual(result["verdict"], "blocked")
                self.assertTrue(result["enforced"])
                self.assertEqual(result["gate"], gate)
                codes = [item["code"] for item in result["findings"]]
                self.assertEqual(codes, [termgate.VOCAB_ZERO_CODE])
                self.assertTrue(result["vocabGuard"]["zeroDrop"])
                self.assertTrue(result["vocabGuard"]["forcedBlocking"])
                self.assertIsNone(result["vocabGuard"]["exemption"])

    def test_8_first_import_without_a_mark_is_not_blocked(self):
        result = termgate.evaluate_snapshot(
            self._snapshot(NO_TERMS_TTL), TermsConfig(gate="warn")
        )
        self.assertFalse(result["blocked"])
        self.assertEqual(result["verdict"], "pass")
        self.assertFalse(result["vocabGuard"]["zeroDrop"])

    def test_9_smoke_exemption_records_actor_path_and_baseline(self):
        result = termgate.evaluate_snapshot(
            self._snapshot(NO_TERMS_TTL),
            TermsConfig(gate="block"),
            high_water={"conceptsInScheme": 85, "aliases": 18, "versionId": "ont-published"},
            context={
                "purpose": "smoke",
                "purposeVerified": True,
                "purposeStatus": "verified",
                "actor": "smoke-selftest",
                "path": "POST /ontology/publish",
                "versionId": "ont-probe",
            },
        )
        self.assertFalse(result["blocked"])
        exemption = result["vocabGuard"]["exemption"]
        self.assertEqual(exemption["purpose"], "smoke")
        self.assertEqual(exemption["actor"], "smoke-selftest")
        self.assertEqual(exemption["path"], "POST /ontology/publish")
        self.assertEqual(exemption["versionId"], "ont-probe")
        self.assertEqual(exemption["baseline"]["conceptsInScheme"], 85)
        self.assertEqual(exemption["baseline"]["versionId"], "ont-published")
        self.assertEqual(exemption["current"]["conceptsInScheme"], 0)
        self.assertEqual(exemption["tokenStatus"], "verified")
        self.assertTrue(exemption["purposeVerified"])
        self.assertTrue(exemption["exemptedAt"])
        stored = [
            item for item in result["findings"]
            if item["code"] == termgate.VOCAB_ZERO_EXEMPT_CODE
        ]
        self.assertEqual(len(stored), 1)
        self.assertFalse(stored[0]["blocking"])
        self.assertEqual(stored[0]["exemption"]["actor"], "smoke-selftest")

    def test_10_other_purposes_are_not_exemptions(self):
        result = termgate.evaluate_snapshot(
            self._snapshot(NO_TERMS_TTL),
            TermsConfig(gate="warn"),
            high_water={"conceptsInScheme": 85},
            context={"purpose": "audit", "actor": "ci-bot", "path": "POST /ontology/publish"},
        )
        self.assertTrue(result["blocked"])
        self.assertIsNone(result["vocabGuard"]["exemption"])

    def test_11_consecutive_collapse_uses_the_mark_not_the_pointer(self):
        # The pointer is already at zero, so every ratio in the live baseline is
        # None/0 and the old checks stay silent. The mark is what catches the
        # second (third, ...) collapse.
        result = termgate.evaluate_snapshot(
            self._snapshot(NO_TERMS_TTL),
            TermsConfig(gate="off"),
            baseline={"actual": {"conceptsInMetricScheme": 0, "aliases": 0}},
            high_water={"conceptsInScheme": 85, "versionId": "ont-hw"},
        )
        self.assertIsNotNone(result)
        self.assertTrue(result["blocked"])
        self.assertEqual(result["coverage"]["actual"]["conceptsInMetricScheme"], 0)

    def test_19_smoke_context_keys_match_publish_signatures(self):
        """键名漂移守卫：这条路径没人调用时 421 个单测可以全绿，但 smoke 会 70。

        上一轮就是 `smoke_env_context` 返回驼峰键、直接 `**` 传给下划线形参，
        所有 smoke 探针 TypeError。这里同时钉住进程内与 HTTP 两套字典：
        键集合必须与 `publish` / `publish_import` 的形参对得上，改名即红。
        """
        in_process = set(termgate.smoke_env_context("smoke"))
        self.assertEqual(
            in_process, {"purpose_verified", "purpose_status", "remote_addr"}
        )
        publish_params = set(
            inspect.signature(OntologyRegistry.publish).parameters
        )
        import_params = set(inspect.signature(publish_import).parameters)
        snake = {"purpose_verified", "purpose_status", "remote_addr"}
        self.assertTrue(snake <= publish_params, publish_params)
        self.assertTrue(snake <= import_params, import_params)

        # HTTP 入口侧：`**smoke` 直接展开，键必须就是形参名。
        request = SimpleNamespace(
            headers={}, client=SimpleNamespace(host="127.0.0.1")
        )
        http_keys = set(api_module._smoke_guard(request, None, None))
        self.assertEqual(http_keys, snake)
        self.assertTrue(http_keys <= publish_params)
        self.assertTrue(http_keys <= import_params)
        # 驼峰键若再次出现，`**` 展开会 TypeError —— 这里提前拦住。
        self.assertTrue(all("_" in key and key.islower() for key in http_keys), http_keys)

        # smoke 分支同样只能返回 snake_case 键（这是真正 `**` 展开的那条路径）。
        previous = os.environ.get("PLATFORM_SMOKE_TOKEN")
        os.environ["PLATFORM_SMOKE_TOKEN"] = "guard-token"
        try:
            smoke_request = SimpleNamespace(
                headers={termgate.SMOKE_TOKEN_HEADER: "guard-token"},
                client=SimpleNamespace(host="127.0.0.1"),
            )
            smoke_keys = set(
                api_module._smoke_guard(smoke_request, "smoke", None)
            )
            self.assertEqual(smoke_keys, snake)
            self.assertTrue(smoke_keys <= publish_params)
            self.assertTrue(smoke_keys <= import_params)
        finally:
            if previous is None:
                os.environ.pop("PLATFORM_SMOKE_TOKEN", None)
            else:
                os.environ["PLATFORM_SMOKE_TOKEN"] = previous


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


@unittest.skipUnless(DSN, "TEST_PG_DSN not set; refusing to fall back to PLATFORM__DATABASE__URL")
class PublishGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = MetadataPg(DSN)
        cls.meta.open(retry_seconds=15)
        # The live stack may still run an image whose schema stops at V34. Apply
        # the V40 DDL directly (idempotent) instead of bumping schema_version
        # under that older image; the next migrate() will pick V40 up normally.
        ddl = (
            files("platform_core").joinpath("sql/V40__term_high_water.sql")
            .read_text(encoding="utf-8")
        )
        for statement in split_sql_statements(ddl):
            cls.meta.execute(statement)
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
        # 方案 A：purpose=smoke 必须携带内部 token（header）。测试用随机值，
        # 只存进程环境，不写进任何断言以外的落盘位置。
        cls.smoke_token = "smoke-" + uuid.uuid4().hex
        cls._previous_token = os.environ.get("PLATFORM_SMOKE_TOKEN")
        os.environ["PLATFORM_SMOKE_TOKEN"] = cls.smoke_token

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
        if cls._previous_token is None:
            os.environ.pop("PLATFORM_SMOKE_TOKEN", None)
        else:
            os.environ["PLATFORM_SMOKE_TOKEN"] = cls._previous_token
        cls.client.__exit__(None, None, None)
        cls.reasoner.close()
        cls.graph.close()
        cls.meta.close()

    def setUp(self):
        self.created: list[dict] = []
        self.manual_versions: list[str] = []
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
        self.original_mark = self.meta.query(
            "SELECT scope, concepts_in_scheme, aliases, version_id, graph_iri "
            "FROM platform.term_high_water"
        )
        # These fixtures use urn:s14term:, not the fsldm MetricScheme, so their
        # effective term set is zero. Pin the mark to zero (first-import
        # semantics) so the vocab-zero guard stays out of the ratio tests;
        # tests 12-14 install their own non-zero mark explicitly.
        self._set_mark(concepts=0, aliases=0)

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
        else:
            with self.meta.tx() as tx:
                tx.execute("DELETE FROM platform.graph_pointer WHERE name = %s", (POINTER_NAME,))
        with self.meta.tx() as tx:
            tx.execute("DELETE FROM platform.term_high_water")
            for row in self.original_mark:
                tx.execute(
                    "INSERT INTO platform.term_high_water "
                    "(scope, concepts_in_scheme, aliases, version_id, graph_iri) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (
                        row["scope"], row["concepts_in_scheme"], row["aliases"],
                        row["version_id"], row["graph_iri"],
                    ),
                )
        for version_id in self.manual_versions:
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
                    "DELETE FROM platform.ontology_version WHERE version_id = %s", (version_id,)
                )
            try:
                self.graph.update(f"DROP SILENT GRAPH <urn:platform:graph:tbox:{version_id}>")
            except Exception:
                pass
        self.manual_versions = []
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

    def _smoke_headers(self, token: str | None = None):
        return {termgate.SMOKE_TOKEN_HEADER: token or self.smoke_token}

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

    def _blocked_events(self, version_id: str, path: str) -> list[dict]:
        """被拒的 publish 必须落进哈希链，即使没有版本行。"""
        rows = self.meta.query(
            "SELECT action, actor, payload FROM platform.ontology_event "
            "WHERE version_id = %s AND action = 'publish_blocked' "
            "ORDER BY event_id",
            (version_id,),
        )
        return [row for row in rows if (row["payload"] or {}).get("path") == path]

    def _set_mark(self, concepts: int = 85, aliases: int = 18) -> None:
        """Install a non-zero high-water mark without publishing a real version."""
        with self.meta.tx() as tx:
            tx.execute("DELETE FROM platform.term_high_water")
            tx.execute(
                "INSERT INTO platform.term_high_water "
                "(scope, concepts_in_scheme, aliases, version_id, graph_iri) "
                "VALUES ('metric', %s, %s, 'ont-mark-baseline', "
                "'urn:platform:graph:tbox:ont-mark-baseline')",
                (concepts, aliases),
            )

    def _insert_draft_version(self, nt: bytes) -> str:
        """Create a draft version row + graph, so POST /ontology/publish is implicit."""
        version_id = "ont-" + uuid.uuid4().hex[:12]
        graph_iri = f"urn:platform:graph:tbox:{version_id}"
        self.graph.replace_graph(graph_iri, nt, "nt")
        count = self.graph.count_graph(graph_iri)
        with self.meta.tx() as tx:
            tx.execute(
                "INSERT INTO platform.ontology_version "
                "(version_id, semver, status, content_hash, triple_count, "
                " source_format, source_key, graph_iri, label) "
                "VALUES (%s, '0.0.0', 'draft', %s, %s, 'turtle', %s, %s, %s)",
                (
                    version_id, hashlib.sha256(nt).hexdigest(), count,
                    f"sources/{version_id}.nt", graph_iri, "g8 vocab guard test",
                ),
            )
        self.manual_versions.append(version_id)
        return version_id

    def test_7_off_attaches_no_gate_when_the_effective_term_set_is_nonzero(self):
        record = self._import(DUPLICATE_TTL, "g8off")
        self.registry.set_terms_gate(TermsConfig(gate="off"))
        baseline_keys = {
            "importId", "versionId", "previousVersionId", "pointer", "dryRun",
            "diff", "impact", "usable", "reason", "canonicalEqualTo",
            "published", "publishedAt", "publishExisting",
        }
        response = self._publish(record["importId"], dry_run=True)
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(set(payload), baseline_keys)
        self.assertNotIn("termsGate", payload)
        self.assertNotIn("terms", (payload.get("gates") or {}))

    def test_12_implicit_publish_zeroing_terms_is_blocked_without_a_request(self):
        self.registry.set_terms_gate(TermsConfig(gate="warn"))
        self._set_mark()
        version_id = self._insert_draft_version(NO_TERMS_NT)
        before = self.registry.current()
        response = self.client.post(
            "/ontology/publish",
            json={"versionId": version_id, "actor": "ci-bot", "acknowledgeBreaking": True},
        )
        self.assertEqual(response.status_code, 409, response.text)
        error = response.json()["error"]
        self.assertEqual(error["providerCode"], "E_TERM_GATE_BLOCKED")
        guard = error["details"]["vocabGuard"]
        self.assertTrue(guard["zeroDrop"])
        self.assertTrue(guard["forcedBlocking"])
        self.assertIsNone(guard["exemption"])
        self.assertEqual(guard["highWater"]["conceptsInScheme"], 85)
        self.assertEqual(guard["effective"]["conceptsInScheme"], 0)
        self.assertEqual(error["details"]["gate"], "warn")
        self.assertTrue(error["details"]["allowed"])

        self.assertEqual((self.registry.current() or {}).get("versionId"),
                         (before or {}).get("versionId"))
        rows = self.meta.query(
            "SELECT status FROM platform.ontology_version WHERE version_id = %s",
            (version_id,),
        )
        self.assertEqual(rows[0]["status"], "draft")
        packs = self._evidence(version_id)
        self.assertEqual(len(packs), 1)
        stored = packs[0]["payload"]
        self.assertEqual(stored["verdict"], "fail")
        self.assertTrue(stored["gates"]["terms"]["vocabGuard"]["zeroDrop"])

    def test_13_implicit_publish_purpose_smoke_with_token_is_exempted_and_leaves_a_trace(self):
        self.registry.set_terms_gate(TermsConfig(gate="warn"))
        self._set_mark()
        version_id = self._insert_draft_version(NO_TERMS_NT)
        response = self.client.post(
            "/ontology/publish",
            json={
                "versionId": version_id, "actor": "smoke-selftest",
                "purpose": "smoke", "acknowledgeBreaking": True,
            },
            headers=self._smoke_headers(),
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        terms = payload["gates"]["terms"]
        self.assertFalse(terms["blocked"])
        exemption = terms["vocabGuard"]["exemption"]
        self.assertEqual(exemption["purpose"], "smoke")
        self.assertEqual(exemption["actor"], "smoke-selftest")
        self.assertEqual(exemption["path"], "POST /ontology/publish")
        self.assertEqual(exemption["versionId"], version_id)
        self.assertEqual(exemption["baseline"]["conceptsInScheme"], 85)
        self.assertEqual(exemption["baseline"]["versionId"], "ont-mark-baseline")
        self.assertEqual(exemption["current"]["conceptsInScheme"], 0)
        self.assertEqual(exemption["tokenStatus"], "verified")
        self.assertEqual(payload["previousVersionId"], self.original_pointer)

        stored = self._evidence(version_id)[0]["payload"]
        self.assertEqual(stored["verdict"], "pass")
        self.assertEqual(
            stored["gates"]["terms"]["vocabGuard"]["exemption"]["actor"], "smoke-selftest"
        )
        self.assertEqual(
            stored["gates"]["terms"]["vocabGuard"]["exemption"]["baseline"]["conceptsInScheme"],
            85,
        )
        # 证据包补的两个字段，且 token 明文不落证据包。
        self.assertEqual(stored["purposeVerified"], True)
        self.assertIsNotNone(stored["remoteAddr"])
        self.assertNotIn(self.smoke_token, str(stored))

        # 豁免关键字段进哈希链：published 事件 payload 的 terms 摘要。
        events = self.meta.query(
            "SELECT payload FROM platform.ontology_event "
            "WHERE version_id = %s AND action = 'published'",
            (version_id,),
        )
        self.assertEqual(len(events), 1)
        audit = events[0]["payload"]["terms"]
        self.assertEqual(audit["purpose"], "smoke")
        self.assertTrue(audit["exempted"])
        self.assertEqual(audit["verdict"], "warned")
        self.assertEqual(audit["baseline"]["conceptsInScheme"], 85)
        self.assertEqual(audit["baseline"]["aliases"], 18)
        self.assertEqual(audit["baseline"]["versionId"], "ont-mark-baseline")
        self.assertEqual(audit["current"]["conceptsInScheme"], 0)
        self.assertEqual(audit["tokenStatus"], "verified")
        self.assertTrue(audit["purposeVerified"])
        self.assertNotIn(self.smoke_token, str(audit))
        self.assertTrue(self.registry.verify_events()["ok"])

    def test_14_import_publish_zero_terms_is_blocked_then_exempted_by_smoke(self):
        self.registry.set_terms_gate(TermsConfig(gate="warn"))
        self._set_mark()
        record = self._import(NO_TERMS_TTL, "g8zero")
        version_id = _import_version_id(record["importId"])

        denied = self._publish(record["importId"], dry_run=False)
        self.assertEqual(denied.status_code, 409, denied.text)
        error = denied.json()["error"]
        self.assertEqual(error["providerCode"], "E_TERM_GATE_BLOCKED")
        self.assertTrue(error["details"]["vocabGuard"]["zeroDrop"])
        self.assertEqual(error["details"]["vocabGuard"]["highWater"]["conceptsInScheme"], 85)
        self.assertEqual(
            self.meta.query(
                "SELECT version_id FROM platform.ontology_version WHERE version_id = %s",
                (version_id,),
            ),
            [],
        )

        allowed = self.client.post(
            f"/ontology/imports/{record['importId']}/publish",
            json={
                "dryRun": False, "acknowledgeBreaking": True,
                "actor": "smoke-selftest", "purpose": "smoke",
            },
            headers=self._smoke_headers(),
        )
        self.assertEqual(allowed.status_code, 200, allowed.text)
        payload = allowed.json()
        exemption = payload["termsGate"]["vocabGuard"]["exemption"]
        self.assertEqual(exemption["purpose"], "smoke")
        self.assertEqual(exemption["actor"], "smoke-selftest")
        self.assertEqual(exemption["path"], "POST /ontology/import")
        self.assertEqual(exemption["baseline"]["conceptsInScheme"], 85)
        self.assertEqual(exemption["current"]["conceptsInScheme"], 0)
        self.assertEqual(exemption["tokenStatus"], "verified")
        stored = self._evidence(payload["versionId"])[0]["payload"]
        self.assertTrue(stored["gates"]["terms"]["vocabGuard"]["exemption"])
        self.assertEqual(stored["purposeVerified"], True)
        self.assertIsNotNone(stored["remoteAddr"])
        self.assertNotIn(self.smoke_token, str(stored))

    def test_15_off_cannot_switch_off_the_vocab_guard(self):
        self.registry.set_terms_gate(TermsConfig(gate="off"))
        self._set_mark()
        record = self._import(NO_TERMS_TTL, "g8offzero")
        preview = self._publish(record["importId"], dry_run=True)
        self.assertEqual(preview.status_code, 200, preview.text)
        self.assertTrue(preview.json()["termsGate"]["blocked"])
        self.assertEqual(preview.json()["termsGate"]["gate"], "off")
        response = self._publish(record["importId"], dry_run=False)
        self.assertEqual(response.status_code, 409, response.text)
        error = response.json()["error"]
        self.assertEqual(error["providerCode"], "E_TERM_GATE_BLOCKED")
        self.assertEqual(error["details"]["gate"], "off")
        self.assertTrue(error["details"]["vocabGuard"]["forcedBlocking"])
        self.assertEqual(error["details"]["vocabGuard"]["highWater"]["conceptsInScheme"], 85)

    def test_16_smoke_without_token_is_blocked_and_recorded_as_forged(self):
        self.registry.set_terms_gate(TermsConfig(gate="warn"))
        self._set_mark()
        version_id = self._insert_draft_version(NO_TERMS_NT)
        response = self.client.post(
            "/ontology/publish",
            json={
                "versionId": version_id, "actor": "smoke-selftest",
                "purpose": "smoke", "acknowledgeBreaking": True,
            },
        )
        self.assertEqual(response.status_code, 409, response.text)
        error = response.json()["error"]
        self.assertEqual(error["providerCode"], "E_TERM_GATE_BLOCKED")
        guard = error["details"]["vocabGuard"]
        self.assertTrue(guard["zeroDrop"])
        self.assertIsNone(guard["exemption"])
        self.assertEqual(guard["tokenStatus"], "missing")
        self.assertFalse(guard["purposeVerified"])
        codes = [item["code"] for item in error["details"]["findings"]]
        self.assertIn(termgate.VOCAB_ZERO_CODE, codes)
        self.assertIn(termgate.VOCAB_ZERO_FORGED_CODE, codes)
        self.assertIn("未携带", error["details"]["exemptionRejected"])
        rows = self.meta.query(
            "SELECT status FROM platform.ontology_version WHERE version_id = %s",
            (version_id,),
        )
        self.assertEqual(rows[0]["status"], "draft")
        blocked = self._blocked_events(version_id, "POST /ontology/publish")
        self.assertEqual(len(blocked), 1)
        audit = blocked[0]["payload"]
        self.assertTrue(audit["rejected"])
        self.assertEqual(audit["verdict"], "blocked")
        self.assertEqual(audit["tokenStatus"], "missing")
        self.assertFalse(audit["purposeVerified"])
        self.assertEqual(audit["purpose"], "smoke")
        self.assertIsNotNone(audit["remoteAddr"])
        self.assertEqual(audit["baseline"]["conceptsInScheme"], 85)
        self.assertEqual(audit["baseline"]["aliases"], 18)
        self.assertEqual(audit["current"]["conceptsInScheme"], 0)
        self.assertIn("未携带", audit["exemptionRejected"])
        self.assertNotIn(self.smoke_token, str(blocked))
        self.assertTrue(self.registry.verify_events()["ok"])
        stored = self._evidence(version_id)[0]["payload"]
        self.assertEqual(stored["verdict"], "fail")
        self.assertEqual(stored["purposeVerified"], False)
        self.assertNotIn(self.smoke_token, response.text)

    def test_17_wrong_token_on_publish_is_blocked_and_recorded_as_forged(self):
        self.registry.set_terms_gate(TermsConfig(gate="warn"))
        self._set_mark()
        record = self._import(NO_TERMS_TTL, "g8wrongtoken")
        version_id = _import_version_id(record["importId"])
        wrong = "wrong-" + uuid.uuid4().hex
        response = self.client.post(
            f"/ontology/imports/{record['importId']}/publish",
            json={
                "dryRun": False, "acknowledgeBreaking": True,
                "actor": "smoke-selftest", "purpose": "smoke",
            },
            headers={termgate.SMOKE_TOKEN_HEADER: wrong},
        )
        self.assertEqual(response.status_code, 409, response.text)
        error = response.json()["error"]
        self.assertEqual(error["providerCode"], "E_TERM_GATE_BLOCKED")
        guard = error["details"]["vocabGuard"]
        self.assertEqual(guard["tokenStatus"], "invalid")
        self.assertIsNone(guard["exemption"])
        codes = [item["code"] for item in error["details"]["problems"]]
        self.assertIn(termgate.VOCAB_ZERO_FORGED_CODE, codes)
        self.assertIn("校验失败", error["details"]["exemptionRejected"])
        self.assertNotIn(wrong, response.text)
        self.assertNotIn(self.smoke_token, response.text)
        self.assertEqual(
            self.meta.query(
                "SELECT version_id FROM platform.ontology_version WHERE version_id = %s",
                (version_id,),
            ),
            [],
        )
        # 被拒本身进哈希链：没有版本行也要能回答"谁试过绕过、从哪来"。
        blocked = self._blocked_events(version_id, "POST /ontology/import")
        self.assertEqual(len(blocked), 1)
        audit = blocked[0]["payload"]
        self.assertTrue(audit["rejected"])
        self.assertEqual(audit["tokenStatus"], "invalid")
        self.assertFalse(audit["purposeVerified"])
        self.assertIsNotNone(audit["remoteAddr"])
        self.assertEqual(audit["baseline"]["conceptsInScheme"], 85)
        self.assertEqual(audit["current"]["conceptsInScheme"], 0)
        self.assertIn("校验失败", audit["exemptionRejected"])
        self.assertNotIn(wrong, str(blocked))
        self.assertTrue(self.registry.verify_events()["ok"])

    def test_18_unconfigured_token_env_fails_closed(self):
        self.registry.set_terms_gate(TermsConfig(gate="warn"))
        self._set_mark()
        record = self._import(NO_TERMS_TTL, "g8unconfigured")
        version_id = _import_version_id(record["importId"])
        os.environ.pop("PLATFORM_SMOKE_TOKEN", None)
        try:
            response = self.client.post(
                f"/ontology/imports/{record['importId']}/publish",
                json={
                    "dryRun": False, "acknowledgeBreaking": True,
                    "actor": "smoke-selftest", "purpose": "smoke",
                },
                headers={termgate.SMOKE_TOKEN_HEADER: "any-" + uuid.uuid4().hex},
            )
        finally:
            os.environ["PLATFORM_SMOKE_TOKEN"] = self.smoke_token
        self.assertEqual(response.status_code, 409, response.text)
        error = response.json()["error"]
        self.assertEqual(error["providerCode"], "E_TERM_GATE_BLOCKED")
        self.assertIn("fail-closed", error["message"])
        guard = error["details"]["vocabGuard"]
        self.assertEqual(guard["tokenStatus"], "unconfigured")
        self.assertIsNone(guard["exemption"])
        codes = [item["code"] for item in error["details"]["problems"]]
        self.assertIn(termgate.VOCAB_ZERO_FORGED_CODE, codes)
        self.assertIn("未配置", error["details"]["exemptionRejected"])
        self.assertEqual(
            self.meta.query(
                "SELECT version_id FROM platform.ontology_version WHERE version_id = %s",
                (version_id,),
            ),
            [],
        )
        blocked = self._blocked_events(version_id, "POST /ontology/import")
        self.assertEqual(len(blocked), 1)
        audit = blocked[0]["payload"]
        self.assertEqual(audit["tokenStatus"], "unconfigured")
        self.assertFalse(audit["purposeVerified"])
        self.assertIn("fail-closed", audit["exemptionRejected"])
        self.assertTrue(self.registry.verify_events()["ok"])

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
        # 被拒也要留痕：只新增一条 publish_blocked 审计事件，其余写入不变。
        events = self.meta.query(
            "SELECT event_id, action FROM platform.ontology_event "
            "WHERE version_id = %s ORDER BY event_id",
            (version_id,),
        )
        self.assertEqual(len(events), len(before_events) + 1)
        self.assertEqual(events[-1]["action"], "publish_blocked")
        self.assertEqual(
            {row["event_id"] for row in events[:-1]},
            {row["event_id"] for row in before_events},
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
