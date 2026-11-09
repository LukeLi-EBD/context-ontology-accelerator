"""B-02 PROV-O judgement provenance: three positive lookups, negatives, mixing.

Runs inside the platform image against the real database/graph:
  * decision      -- FIN-BANK-002 decision_recommendation (band(dpd, 30, 6))
  * rule_trigger  -- FIN-BANK-002 R03 (dpd >= 61) with dpd=75
  * refusal       -- real /answer coverage gate on an uncovered topic

Negatives:
  * unknown metric -> E_PROV_SUBJECT_NOT_FOUND
  * physical delete -> API refusal + DB trigger refusal, row still present
  * graph mixing   -> E_PROV_GRAPH_MIXING

Zero-mixing is asserted in both directions against the current T-Box graph.
The ledger is append-only by design, so this module never cleans up.
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, "/app/src")

from platform_core import prov as prov_module
from platform_core.api import _qa_answer
from platform_core.assembly import assemble
from platform_core.config import load_config
from platform_core.errors import PortError

CONFIG = os.environ.get("PLATFORM_CONFIG", "/data/platform.yaml")
METRIC = "FIN-BANK-002"


class ProvDatabaseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = assemble(load_config(CONFIG, None))
        cls.runtime.metadata.open(retry_seconds=15.0)
        cls.runtime.metadata.migrate()
        cls.meta = cls.runtime.metadata
        cls.prov = cls.runtime.prov

    @classmethod
    def tearDownClass(cls) -> None:
        cls.runtime.close()

    def _code(self, call, *args, **kwargs) -> PortError:
        with self.assertRaises(PortError) as caught:
            call(*args, **kwargs)
        return caught.exception

    # ---- positive: decision ---------------------------------------------

    def test_decision_history_and_rejudgement(self) -> None:
        first = self.prov.record_decision(
            METRIC, actor="operator:test-prov", reason="b02-positive"
        )
        self.assertEqual(first["kind"], "decision")
        self.assertTrue(first["conclusion"]["publishable"])
        self.assertFalse(first["conclusion"]["inference"])
        recommendation = first["conclusion"]["decisionRecommendation"]
        self.assertEqual(recommendation["recommendation"]["formulaExpr"], "band(dpd, 30, 6)")
        self.assertEqual(recommendation["status"], "recommended_pending_business_signoff")
        refs = [entry["ref"] for entry in first["evidence"]]
        self.assertTrue(any("37-指标口径判定书" in ref for ref in refs), refs)
        self.assertTrue(any("platform.metric_definition#" in ref for ref in refs), refs)

        history = self.prov.decision_history(METRIC)
        self.assertGreaterEqual(history["count"], 1)
        latest = history["items"][0]
        self.assertEqual(latest["activityId"], first["activityId"])
        self.assertGreaterEqual(latest["eventId"], 1)
        self.assertTrue(latest["hash"])
        self.assertEqual(latest["actorKind"], "human")

        second = self.prov.record_decision(
            METRIC, actor="operator:test-prov", reason="b02-rejudge"
        )
        self.assertEqual(second["derivedFrom"], first["conclusionIri"])
        self.assertEqual(second["before"]["definitionVersion"], "v3.0")
        history = self.prov.decision_history(METRIC)
        self.assertEqual(history["items"][0]["activityId"], second["activityId"])
        self.assertEqual(history["items"][0]["prevEvent"], first["eventId"])
        self.assertEqual(history["items"][0]["derivedFrom"], first["conclusionIri"])

    # ---- positive: rule trigger -----------------------------------------

    def test_rule_trigger_history(self) -> None:
        executed = self.runtime.rules.execute(
            METRIC,
            [{"customerId": "CUST-PROV-001", "dpd": 75, "asOf": "2026-11-06"}],
            as_of="2026-11-06",
        )
        self.assertGreaterEqual(executed["triggeredCount"], 1)
        recorded = self.prov.record_rule_execution(
            METRIC, executed, request_id="req-test-rule"
        )
        self.assertGreaterEqual(len(recorded), 1)

        triggers = self.prov.rule_triggers("R03")
        self.assertGreaterEqual(triggers["count"], 1)
        item = triggers["items"][0]
        conclusion = item["conclusion"]
        self.assertEqual(conclusion["ruleId"], "R03")
        self.assertEqual(conclusion["threshold"], ">=61 天")
        self.assertEqual(conclusion["level"], "L2")
        self.assertEqual(conclusion["observed"]["dpd"], 75.0)
        self.assertEqual(conclusion["spec"]["field"], "dpd")
        self.assertEqual(conclusion["spec"]["value"], 61)
        self.assertEqual(conclusion["customerId"], "CUST-PROV-001")
        self.assertEqual(item["metricId"], METRIC)
        self.assertIn("activity/", item["activityIri"])
        refs = [entry["ref"] for entry in item["evidence"]]
        self.assertTrue(any("rule_set_json.R03.spec" in ref for ref in refs), refs)
        self.assertTrue(any(ref.startswith("req-test-rule#customer=") for ref in refs), refs)

    # ---- positive: refusal ----------------------------------------------

    REFUSAL_QUERY = "量子纠缠担保品的监管处置口径是什么"

    def test_refusal_lookup_by_request(self) -> None:
        answer = _qa_answer(self.runtime, self.REFUSAL_QUERY, top_k=3)
        self.assertTrue(answer["refused"], answer.get("reasonCode"))
        request_id = answer["requestId"]
        result = self.prov.refusal(request_id=request_id)
        self.assertEqual(result["count"], 1)
        item = result["items"][0]
        self.assertEqual(item["kind"], "refusal")
        self.assertEqual(item["conclusion"]["reasonCode"], answer["reasonCode"])
        self.assertTrue(item["conclusion"]["missing"])
        self.assertEqual(item["conclusion"]["query"], self.REFUSAL_QUERY)
        self.assertEqual(item["conclusion"]["retrieval"]["topK"], 3)
        self.assertEqual(item["conclusion"]["retrieval"]["strategy"], "lexical")
        layers = [gap.get("layer") for gap in item["conclusion"]["missing"]]
        self.assertTrue(layers)
        self.assertTrue(any(entry["ref"].startswith("answerable.missing#") for entry in item["evidence"]))

    def test_refusal_lookup_by_query(self) -> None:
        query = self.REFUSAL_QUERY + "（按查询反查）"
        answer = _qa_answer(self.runtime, query, top_k=2)
        self.assertTrue(answer["refused"], answer.get("reasonCode"))
        result = self.prov.refusal(query=query)
        self.assertGreaterEqual(result["count"], 1)
        self.assertEqual(result["items"][0]["conclusion"]["query"], query)

    # ---- negatives -------------------------------------------------------

    def test_unknown_metric_is_not_found(self) -> None:
        exc = self._code(self.prov.decision_history, "PROV-NOT-A-METRIC")
        self.assertEqual(exc.provider_code, prov_module.SUBJECT_NOT_FOUND)
        exc = self._code(self.prov.record_decision, "PROV-NOT-A-METRIC")
        self.assertEqual(exc.provider_code, prov_module.SUBJECT_NOT_FOUND)

    def test_unknown_request_is_not_found(self) -> None:
        exc = self._code(self.prov.refusal, request_id="req-does-not-exist")
        self.assertEqual(exc.provider_code, prov_module.NOT_FOUND)

    def test_physical_delete_refused(self) -> None:
        rows = self.meta.query(
            "SELECT event_id FROM platform.prov_event ORDER BY event_id DESC LIMIT 1"
        )
        self.assertTrue(rows)
        event_id = int(rows[0]["event_id"])
        exc = self._code(self.prov.refuse_delete, "act-any")
        self.assertEqual(exc.provider_code, prov_module.APPEND_ONLY)
        with self.assertRaises(Exception) as caught:
            with self.meta.tx() as tx:
                tx.execute(
                    "DELETE FROM platform.prov_event WHERE event_id = %s", (event_id,)
                )
        self.assertIn("append-only", str(caught.exception))
        still = self.meta.query(
            "SELECT event_id FROM platform.prov_event WHERE event_id = %s", (event_id,)
        )
        self.assertEqual(len(still), 1)

    def test_graph_mixing_refused(self) -> None:
        exc = self._code(self.prov.guard, "urn:platform:graph:tbox:ont-3f57d8ce6636")
        self.assertEqual(exc.provider_code, prov_module.GRAPH_MIXING)
        exc = self._code(
            self.prov.write_triples,
            "urn:platform:graph:fact:override",
            [],
        )
        self.assertEqual(exc.provider_code, prov_module.GRAPH_MIXING)
        ok = self.prov.guard(prov_module.PROV_GRAPH)
        self.assertTrue(ok["allowed"])

    # ---- audit + zero mixing ---------------------------------------------

    def test_chain_verifies_and_graphs_do_not_mix(self) -> None:
        # Seed two activities so a fresh database proves continuity, not just one row.
        self.prov.record_decision(METRIC, actor="operator:test-prov", reason="b02-chain")
        self.prov.record_decision(METRIC, actor="operator:test-prov", reason="b02-chain-2")
        verification = self.prov.verify()
        self.assertTrue(verification["ok"], verification)
        self.assertGreaterEqual(verification["checked"], 2)
        self.assertTrue(verification["lastHash"])

        separation = self.prov.separation()
        self.assertTrue(separation["ok"], separation)
        self.assertEqual(separation["tboxProvTriples"], 0)
        self.assertEqual(separation["provTboxTriples"], 0)
        self.assertEqual(separation["provGraph"], prov_module.PROV_GRAPH)
        self.assertGreater(separation["provTriples"], 0)

        # direct both-direction check, independent of ontology.verify
        tbox = separation["tboxGraph"]
        if tbox:
            prov_in_tbox = self.prov._count(
                f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{tbox}> {{ ?s ?p ?o . "
                f'FILTER(STRSTARTS(STR(?s), "{prov_module.NS}")) }} }}'
            )
            self.assertEqual(prov_in_tbox, 0)
        foreign_in_prov = self.prov._count(
            f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{prov_module.PROV_GRAPH}> {{ ?s ?p ?o . "
            f'FILTER(STRSTARTS(STR(?s), "{prov_module.FSLDM}") || '
            f'STRSTARTS(STR(?p), "{prov_module.FSLDM}")) }} }}'
        )
        self.assertEqual(foreign_in_prov, 0)


if __name__ == "__main__":
    unittest.main()
