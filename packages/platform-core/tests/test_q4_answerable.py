"""Q4 answerability tests: 2 positives + 1 negative against a pinned T-Box.

Runs against the already-running postgres/oxigraph (no rebuild):
  docker compose exec -T -e PYTHONPATH=/app/src platform \
    python /app/tests/test_q4_answerable.py

The cases bind an explicit ontology version. By default they resolve the live
``tbox/current`` pointer, so a fresh stack (random version id per import) works
without any historical snapshot; set ``Q4_ONTOLOGY_VERSION`` to pin a specific
version explicitly. They never depend on a version id baked into this file.

The positive queries use real FS-LDM labels (产品包/产品特性/事件金额/事件编号);
the negative query uses concepts absent from the T-Box and must come back
"not answerable" with the uncovered fragments listed.
"""

import os
import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient

import platform_core.api as api_module
from platform_core.adapters.graph_oxigraph import OxigraphHttpStore
from platform_core.adapters.metadata_pg import MetadataPg
from platform_core.adapters.ontology_pg import OntologyRegistry
from platform_core.answerable import AnswerabilityService
from platform_core.config import ContextConfig, OntologyConfig
from platform_core.errors import PortError

DSN = os.environ.get("TEST_PG_DSN")
OXIGRAPH_URL = os.environ.get("TEST_OXIGRAPH_URL", "http://oxigraph:7878")


def _resolve_pinned_version(registry) -> str:
    """Q4_ONTOLOGY_VERSION wins; otherwise follow the live tbox/current pointer."""
    override = os.environ.get("Q4_ONTOLOGY_VERSION")
    if override:
        return override
    pointer = registry.current()
    if not pointer:
        raise AssertionError("no tbox/current pointer; ontology init has not published a T-Box")
    return pointer["versionId"]


@unittest.skipUnless(DSN, "TEST_PG_DSN not set; refusing to fall back to PLATFORM__DATABASE__URL")
class AnswerableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = MetadataPg(DSN)
        cls.meta.open(retry_seconds=15)
        cls.graph = OxigraphHttpStore(OXIGRAPH_URL)
        cls.registry = OntologyRegistry(cls.meta, cls.graph, None, OntologyConfig())
        cls.service = AnswerabilityService(ContextConfig(), cls.registry, cls.graph)
        cls.pinned_version = _resolve_pinned_version(cls.registry)
        try:
            cls.registry.get(cls.pinned_version)
        except PortError as exc:
            raise AssertionError(
                f"pinned ontology version is missing: {cls.pinned_version} ({exc.message})"
            ) from exc
        runtime = SimpleNamespace(
            answerable=cls.service,
            metadata=cls.meta,
            graph=cls.graph,
            config=SimpleNamespace(storage=SimpleNamespace(root="/data")),
        )
        cls.client = TestClient(api_module.create_app(runtime, []))

    @classmethod
    def tearDownClass(cls):
        cls.graph.close()
        cls.meta.close()

    def assert_covered(self, result, labels):
        self.assertTrue(result["answerable"], result)
        self.assertIsNone(result["reasonCode"])
        self.assertGreaterEqual(result["coverage"], result["threshold"])
        matched = {item["label"] for item in result["matchedTerms"]}
        for label in labels:
            self.assertIn(label, matched)
        self.assertEqual(result["missing"], [])
        self.assertIn(result["termSource"], ("skos+rdfs:label", "rdfs:label"))

    # ---- positives -------------------------------------------------------

    def test_1_answerable_when_labels_cover_the_question(self):
        result = self.service.check(
            "产品包的产品特性有哪些", ontology_version=self.pinned_version
        )
        self.assert_covered(result, ("产品包", "产品特性"))
        self.assertEqual(result["coverage"], 1.0)
        self.assertEqual(result["coverageChars"], {"covered": 7, "total": 7})
        self.assertEqual(result["ontologyVersion"], self.pinned_version)

    def test_2_answerable_via_http(self):
        response = self.client.get(
            "/answerable",
            params={"q": "事件金额和事件编号", "ontologyVersion": self.pinned_version},
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assert_covered(payload, ("事件金额", "事件编号"))
        self.assertEqual(payload["ontologyVersion"], self.pinned_version)

    # ---- negative --------------------------------------------------------

    def test_3_not_answerable_reports_what_is_missing(self):
        result = self.service.check(
            "量子计算机的制冷功率是多少", ontology_version=self.pinned_version
        )
        self.assertFalse(result["answerable"], result)
        self.assertEqual(result["ontologyVersion"], self.pinned_version)
        self.assertEqual(result["reasonCode"], "E_ANSWER_NOT_COVERED")
        self.assertLess(result["coverage"], result["threshold"])
        self.assertEqual(result["matchedTerms"], [])
        self.assertEqual(result["coverageChars"]["covered"], 0)
        # Missing fragments are exactly the content words; the stopwords
        # (的/是/多少) are excluded from both the score and the report.
        fragments = [item["text"] for item in result["missing"]]
        self.assertGreater(len(fragments), 0, result)
        self.assertEqual("".join(fragments), "量子计算机制冷功率")
        for item in result["missing"]:
            self.assertEqual(item["reason"], "no_ontology_term")
        self.assertIn("本体未覆盖", result["hint"])


SKOS_PREF = "http://www.w3.org/2004/02/skos/core#prefLabel"
SKOS_ALT = "http://www.w3.org/2004/02/skos/core#altLabel"


def _binding(iri, predicate, label):
    return {
        "values": {
            "s": {"kind": "iri", "iri": iri},
            "p": {"kind": "iri", "iri": predicate},
            "l": {"kind": "literal", "value": label},
        }
    }


class _StubRegistry:
    """Pinned version, no database."""

    def current(self):
        return {"versionId": "v-test", "graph": "urn:graph:test"}

    def get(self, version_id):
        return {"id": version_id, "graph": "urn:graph:test"}


class _StubGraph:
    def __init__(self, bindings):
        self._bindings = bindings

    def query(self, sparql, params=None):
        return {"bindings": list(self._bindings)}


class EntityCoverageTests(unittest.TestCase):
    """Entity-level (1/n) coverage; runs offline against a stub T-Box."""

    def setUp(self):
        self.bindings = [
            _binding("urn:term:package", SKOS_PREF, "产品包"),
            _binding("urn:term:package", SKOS_ALT, "产品套餐"),
            _binding("urn:term:feature", SKOS_PREF, "产品特性"),
            _binding("urn:term:amount", SKOS_PREF, "事件金额"),
            _binding("urn:term:number", SKOS_PREF, "事件编号"),
            _binding("urn:term:collateral", SKOS_PREF, "抵押物"),
        ]
        self.service = AnswerabilityService(
            ContextConfig(), _StubRegistry(), _StubGraph(self.bindings)
        )

    def test_synonym_surface_matches_same_entity(self):
        result = self.service.check("产品套餐的产品特性是什么")
        self.assertTrue(result["answerable"], result)
        self.assertEqual(result["entityCoverage"], 1.0)
        self.assertEqual(result["entityCount"], 2)
        self.assertEqual(result["matchedEntityCount"], 2)
        self.assertFalse(result["entityDegraded"])
        surfaces = {item["text"] for item in result["entityMentions"]}
        self.assertEqual(surfaces, {"产品套餐", "产品特性"})

    def test_no_entity_degrades_to_zero_not_full(self):
        result = self.service.check("量子计算机的制冷功率是多少")
        self.assertFalse(result["answerable"], result)
        self.assertEqual(result["entityCoverage"], 0.0)
        self.assertNotEqual(result["entityCoverage"], 1.0)
        self.assertEqual(result["matchedEntityCount"], 0)
        self.assertEqual(result["entityCount"], 2)
        self.assertTrue(result["entityDegraded"])
        self.assertEqual(result["entityDegradeReason"], "no_ontology_entity")

    def test_multi_entity_partial_is_one_over_n(self):
        # 3 mentioned entities, 2 matched -> 2/3 >= 0.6
        result = self.service.check("事件金额和事件编号的量子属性")
        self.assertEqual(result["entityCount"], 3)
        self.assertEqual(result["matchedEntityCount"], 2)
        self.assertAlmostEqual(result["entityCoverage"], 0.6667, places=4)
        self.assertTrue(result["answerable"], result)
        # same ratio family, 1/3 -> below the 0.6 default
        result = self.service.check("事件金额的量子属性与虫洞效应")
        self.assertEqual(result["entityCount"], 3)
        self.assertEqual(result["matchedEntityCount"], 1)
        self.assertAlmostEqual(result["entityCoverage"], 0.3333, places=4)
        self.assertFalse(result["answerable"], result)

    def test_negative_known_plus_unknown_is_not_answerable(self):
        # Character coverage would be 3/5 = 0.6 and slip through; entity
        # coverage is 1/2 = 0.5 and must refuse.
        result = self.service.check("产品包的价格")
        self.assertEqual(result["coverage"], 0.6)
        self.assertEqual(result["entityCoverage"], 0.5)
        self.assertFalse(result["answerable"], result)
        self.assertFalse(result["entityDegraded"])
        self.assertEqual(result["reasonCode"], "E_ANSWER_NOT_COVERED")
        self.assertEqual(
            [item["text"] for item in result["entityMentions"]],
            ["产品包", "价格"],
        )

    def test_repeated_entity_counts_once_and_meta_words_excluded(self):
        result = self.service.check("产品包和产品包的口径是什么")
        self.assertEqual(result["entityCount"], 1)
        self.assertEqual(result["matchedEntityCount"], 1)
        self.assertEqual(result["entityCoverage"], 1.0)
        self.assertTrue(result["answerable"], result)

    def test_unresolved_fragments_split_on_connector(self):
        # Without the split rule this was one glued 10-char fragment: 1/2.
        # "时" is a connector and "处理" is a meta word, so the denominator
        # must become 抵押物 + {价值发生巨大变化, 银行} = 3.
        result = self.service.check("抵押物价值发生巨大变化时银行如何处理")
        self.assertEqual(result["entityCount"], 3)
        self.assertEqual(result["matchedEntityCount"], 1)
        self.assertAlmostEqual(result["entityCoverage"], 0.3333, places=4)
        self.assertFalse(result["answerable"], result)
        unknown = [
            item["text"]
            for item in result["entityMentions"]
            if item["kind"] == "unknown"
        ]
        self.assertEqual(unknown, ["价值发生巨大变化", "银行"])

    def test_mandated_query_counts_split_fragments(self):
        # 事件金额 matched; 税务处理 and 合规口径 are two missing concepts,
        # so coverage is 1/3, not 1/2.
        result = self.service.check("事件金额的税务处理与合规口径")
        self.assertEqual(result["entityCount"], 3)
        self.assertEqual(result["matchedEntityCount"], 1)
        self.assertAlmostEqual(result["entityCoverage"], 0.3333, places=4)
        self.assertFalse(result["answerable"], result)
        unknown = [
            item["text"]
            for item in result["entityMentions"]
            if item["kind"] == "unknown"
        ]
        self.assertEqual(unknown, ["税务处理", "合规口径"])

    def test_meta_word_entity_match_is_not_swallowed(self):
        # The meta filter only runs on unmatched fragments, so an ontology
        # entity literally named 口径 is matched and counted normally.
        bindings = self.bindings + [_binding("urn:term:caliber", SKOS_PREF, "口径")]
        service = AnswerabilityService(
            ContextConfig(), _StubRegistry(), _StubGraph(bindings)
        )
        result = service.check("口径")
        self.assertEqual(result["entityCount"], 1)
        self.assertEqual(result["matchedEntityCount"], 1)
        self.assertEqual(result["entityCoverage"], 1.0)
        self.assertFalse(result["entityDegraded"])
        self.assertTrue(result["answerable"], result)

    def test_character_diagnostics_are_unchanged(self):
        result = self.service.check("产品包的价格")
        self.assertEqual(result["coverageChars"], {"covered": 3, "total": 5})
        self.assertEqual(result["coverage"], 0.6)


if __name__ == "__main__":
    unittest.main(verbosity=2)