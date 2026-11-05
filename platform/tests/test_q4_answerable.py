"""Q4 answerability tests: 2 positives + 1 negative against the live T-Box.

Runs against the already-running postgres/oxigraph (no rebuild):
  docker compose exec -T -e PYTHONPATH=/app/src platform \
    python /app/tests/test_q4_answerable.py

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

DSN = os.environ.get(
    "TEST_PG_DSN",
    os.environ.get(
        "PLATFORM__DATABASE__URL",
        "postgres://platform:platform_dev@host.docker.internal:5432/platform",
    ),
)
OXIGRAPH_URL = os.environ.get("TEST_OXIGRAPH_URL", "http://host.docker.internal:7878")


class AnswerableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = MetadataPg(DSN)
        cls.meta.open(retry_seconds=15)
        cls.graph = OxigraphHttpStore(OXIGRAPH_URL)
        cls.registry = OntologyRegistry(cls.meta, cls.graph, None, OntologyConfig())
        cls.service = AnswerabilityService(ContextConfig(), cls.registry, cls.graph)
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
        result = self.service.check("产品包的产品特性有哪些")
        self.assert_covered(result, ("产品包", "产品特性"))
        self.assertEqual(result["coverage"], 1.0)
        self.assertEqual(result["coverageChars"], {"covered": 7, "total": 7})
        self.assertIsNotNone(result["ontologyVersion"])

    def test_2_answerable_via_http(self):
        response = self.client.get("/answerable", params={"q": "事件金额和事件编号"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assert_covered(response.json(), ("事件金额", "事件编号"))

    # ---- negative --------------------------------------------------------

    def test_3_not_answerable_reports_what_is_missing(self):
        result = self.service.check("量子计算机的制冷功率是多少")
        self.assertFalse(result["answerable"], result)
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
