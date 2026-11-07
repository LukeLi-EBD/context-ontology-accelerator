"""Layered coverage + citation answer regression tests.

Run inside the platform container (same as the other integration tests):

  docker compose exec platform python -m unittest tests.test_answer_layers -v

The T-Box pointer and metric registry are read live. Facts-layer assertions run
against a test-only metric definition (QA_FIXTURE_METRIC) that has no
observations, so "degraded" does not depend on whether some other dataset has
observed a real metric such as FIN-INS-021. The fixture row is inserted in
setUpClass and removed in tearDownClass.
"""

import os
import unittest

from platform_core.api import _qa_answer, _qa_answerable
from platform_core.assembly import assemble
from platform_core.config import load_config

# Test-only definition: unique id, no observations. fact_function is set and no
# metric_field_binding rows exist, so the facts layer always degrades with
# E_FACTS_NO_OBSERVATION instead of depending on fact-table contents.
QA_FIXTURE_METRIC = "TEST-METRIC-NO-OBS"
QA_FIXTURE_VERSION = "v1"


def _current_tbox_version(runtime) -> str:
    """Resolve the published T-Box from the live pointer.

    Version ids are random per import, so a hard-coded id only exists on a
    machine that once imported that exact snapshot. Set ANSWER_ONTOLOGY_VERSION
    (or Q4_ONTOLOGY_VERSION) to pin a specific version explicitly.
    """
    override = os.environ.get("ANSWER_ONTOLOGY_VERSION") or os.environ.get("Q4_ONTOLOGY_VERSION")
    if override:
        return override
    pointer = runtime.ontology.current()
    if not pointer:
        raise AssertionError("no tbox/current pointer; ontology init has not published a T-Box")
    return pointer["versionId"]


def _layer(payload, name):
    for item in payload.get("layers") or []:
        if item.get("layer") == name:
            return item
    raise AssertionError("layer not found: " + name)


class AnswerLayerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = assemble(load_config("/data/platform.yaml", None))
        cls.runtime.metadata.open(retry_seconds=15)
        cls.tbox_version = _current_tbox_version(cls.runtime)
        cls._seed_fixture()

    @classmethod
    def _seed_fixture(cls):
        """Insert the no-observation definition these assertions run against."""
        meta = cls.runtime.metadata
        meta.execute(
            "DELETE FROM platform.metric_observation WHERE metric_id = %s",
            (QA_FIXTURE_METRIC,),
        )
        meta.execute(
            """
            INSERT INTO platform.metric_definition
              (metric_id, name_zh, domain, evidence_basis, publishable, inference,
               formula_disabled, missing, evidence_status, note, definition_version,
               metric_kind, formula_expr, numerator_agg, denominator_agg, window_kind,
               min_window_days, grain, unit, fact_function)
            VALUES (%s, '答案分层测试指标（无观测）', 'insurance', 'regulatory', true,
                    false, false, NULL, 'EVIDENCED', 'test-only', %s,
                    'sum', 'numerator', 'max', NULL, 'instant', 0, 'customer', '个',
                    'platform.qa_fixture_no_observation')
            ON CONFLICT (metric_id) DO UPDATE SET
              name_zh = EXCLUDED.name_zh,
              definition_version = EXCLUDED.definition_version,
              metric_kind = EXCLUDED.metric_kind,
              formula_expr = EXCLUDED.formula_expr,
              numerator_agg = EXCLUDED.numerator_agg,
              denominator_agg = EXCLUDED.denominator_agg,
              window_kind = EXCLUDED.window_kind,
              min_window_days = EXCLUDED.min_window_days,
              grain = EXCLUDED.grain,
              unit = EXCLUDED.unit,
              fact_function = EXCLUDED.fact_function,
              publishable = EXCLUDED.publishable,
              formula_disabled = false
            """,
            (QA_FIXTURE_METRIC, QA_FIXTURE_VERSION),
        )

    @classmethod
    def tearDownClass(cls):
        try:
            meta = cls.runtime.metadata
            meta.execute(
                "DELETE FROM platform.metric_observation WHERE metric_id = %s",
                (QA_FIXTURE_METRIC,),
            )
            meta.execute(
                "DELETE FROM platform.metric_definition WHERE metric_id = %s",
                (QA_FIXTURE_METRIC,),
            )
        finally:
            try:
                cls.runtime.metadata.close()
            except Exception:
                pass

    # ---- /answerable: 3 cases ---------------------------------------------

    def test_answerable_full_ontology_question(self):
        result = _qa_answerable(self.runtime, "产品包的产品特性有哪些")
        self.assertTrue(result["answerable"])
        self.assertFalse(result["valueAnswerable"])
        self.assertEqual(result["answerMode"], "definition")
        self.assertEqual(result["ontologyVersion"], self.tbox_version)
        self.assertEqual(result["missing"], [])
        self.assertEqual(_layer(result, "ontology")["status"], "covered")
        self.assertEqual(_layer(result, "terms")["status"], "not_applicable")
        self.assertEqual(_layer(result, "metrics")["status"], "not_applicable")
        self.assertEqual(_layer(result, "facts")["status"], "not_applicable")

    def test_answerable_partial_layers_missing(self):
        result = _qa_answerable(self.runtime, "产品包的量子制冷功率是多少")
        self.assertFalse(result["answerable"])
        self.assertEqual(result["intent"], "value")
        self.assertEqual(result["answerMode"], "none")
        self.assertEqual(_layer(result, "ontology")["status"], "partial")
        self.assertEqual(_layer(result, "terms")["status"], "missing")
        self.assertEqual(_layer(result, "metrics")["status"], "missing")
        missing_layers = {item["layer"] for item in result["missing"]}
        self.assertIn("ontology", missing_layers)
        self.assertIn("terms", missing_layers)
        self.assertIn("metrics", missing_layers)

    def test_answerable_facts_degraded(self):
        result = _qa_answerable(
            self.runtime, "13个月继续率是多少", metric_id=QA_FIXTURE_METRIC
        )
        self.assertTrue(result["answerable"])
        self.assertFalse(result["valueAnswerable"])
        self.assertTrue(result["degraded"])
        self.assertEqual(result["answerMode"], "definition")
        self.assertEqual(_layer(result, "metrics")["status"], "covered")
        facts = _layer(result, "facts")
        self.assertEqual(facts["status"], "degraded")
        self.assertTrue(
            any(item["metricId"] == QA_FIXTURE_METRIC for item in facts["matched"])
        )
        facts_missing = [item for item in result["missing"] if item["layer"] == "facts"]
        self.assertTrue(facts_missing)
        self.assertEqual(facts_missing[0]["code"], "E_FACTS_NO_OBSERVATION")
        self.assertIsNone(result["selectedMetrics"][0]["dataSource"])

    # ---- /answer: 3 cases ------------------------------------------------

    def test_answer_definition_with_citations(self):
        result = _qa_answer(
            self.runtime,
            "13个月继续率（有效保单件数）的口径是什么",
            metric_id=QA_FIXTURE_METRIC,
        )
        self.assertFalse(result["refused"])
        self.assertEqual(result["answerType"], "definition")
        self.assertFalse(result["degraded"])
        self.assertIsNone(result["value"])
        self.assertIsNone(result["dataSource"])
        self.assertEqual(result["ontologyVersion"], self.tbox_version)
        steps = {item["step"]: item for item in result["steps"]}
        self.assertEqual(
            [name for name in ("retrieve", "terms", "metric", "facts", "compute")],
            [item["step"] for item in result["steps"]],
        )
        self.assertEqual(steps["metric"]["status"], "covered")
        self.assertEqual(steps["facts"]["status"], "degraded")
        kinds = {item["kind"] for item in result["citations"]}
        self.assertIn("ontology-version", kinds)
        self.assertIn("metric-definition", kinds)
        self.assertIn("formula", kinds)
        self.assertIn("fact-projection", kinds)
        metric_citations = [
            item for item in result["citations"] if item["kind"] == "metric-definition"
        ]
        self.assertEqual(metric_citations[0]["metricId"], QA_FIXTURE_METRIC)
        self.assertEqual(
            metric_citations[0]["definitionVersion"], QA_FIXTURE_VERSION
        )
        self.assertEqual(
            metric_citations[0]["id"],
            f"metric:{QA_FIXTURE_METRIC}@{QA_FIXTURE_VERSION}",
        )

    def test_answer_refused_with_gaps(self):
        result = _qa_answer(self.runtime, "量子计算机的制冷功率是多少")
        self.assertTrue(result["refused"])
        self.assertTrue(result["valueRefused"])
        self.assertEqual(result["answerType"], "none")
        self.assertIn(result["reasonCode"], ("E_ANSWER_METRIC_NOT_FOUND", "E_ANSWER_NOT_COVERED"))
        self.assertTrue(result["missing"])
        missing_layers = {item["layer"] for item in result["missing"]}
        self.assertIn("ontology", missing_layers)
        self.assertIn("metrics", missing_layers)
        self.assertFalse(
            any(item["kind"] == "metric-definition" for item in result["citations"])
        )

    def test_answer_rule_metric_routes_to_rules(self):
        result = _qa_answer(self.runtime, "逾期分档（M0–M6）是什么")
        self.assertFalse(result["refused"])
        self.assertEqual(result["answerType"], "rule_set")
        self.assertFalse(result["degraded"])
        self.assertIsNone(result["value"])
        steps = {item["step"]: item for item in result["steps"]}
        self.assertEqual(steps["metric"]["status"], "covered")
        self.assertEqual(steps["facts"]["status"], "degraded")
        self.assertEqual(steps["compute"]["status"], "routed")
        self.assertEqual(steps["compute"]["output"]["mode"], "rule_set")
        self.assertIsNone(steps["compute"]["output"]["value"])
        self.assertIn("rule-set", {item["kind"] for item in result["citations"]})
        self.assertEqual(steps["compute"]["input"]["metricId"], "FIN-BANK-002")


if __name__ == "__main__":
    unittest.main()
