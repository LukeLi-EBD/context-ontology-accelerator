"""V24 decisions: 9 partial quartets resolved, 11 rule specs executable.

Rule executions use caller-supplied fact dicts only; no fact rows are written.
CUST-002 uses fixture transactions and is removed in tearDownClass, so
platform.metric_observation stays at its 0-row baseline.
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, "/app/src")

from platform_core.assembly import assemble
from platform_core.config import load_config
from platform_core.errors import PortError
from platform_core.metric_compiler import (
    EXPR_UNSUPPORTED, NOT_COMPUTABLE, RULE_SET_ONLY, MetricCompiler,
    formula_to_sql,
)
from platform_core.rules import NO_DATA, RuleExecutor

CONFIG = os.environ.get("PLATFORM_CONFIG", "/data/platform.yaml")

PARTIALS = (
    "FIN-BANK-002", "FIN-BANK-017", "FIN-BANK-018", "FIN-BANK-019",
    "FIN-INS-009", "FIN-INS-012", "CUST-002", "CUST-004", "CUST-005",
)
RULE_METRICS = (
    "FIN-BANK-002", "FIN-BANK-003", "FIN-BANK-004", "FIN-BANK-005",
    "FIN-BANK-006", "FIN-BANK-007", "FIN-BANK-009", "FIN-BANK-010",
    "FIN-BANK-011", "FIN-BANK-012", "FIN-BANK-024",
)

HIT_FACTS = {
    "FIN-BANK-002": {"dpd": 31},
    "FIN-BANK-003": {"dpd": 91},
    "FIN-BANK-004": {"dpd": 91},
    "FIN-BANK-005": {"dpd": 31, "credit_impaired": False},
    "FIN-BANK-006": {"paid_amount": 100, "due_amount": 200},
    "FIN-BANK-007": {"risk_class": "substandard"},
    "FIN-BANK-009": {"npl_balance": 12, "total_balance": 100},
    "FIN-BANK-010": {"financial_difficulty": True, "contract_modified": True},
    "FIN-BANK-011": {"restructuring_flag": True, "days_since_restructure": 180},
    "FIN-BANK-012": {"extension_approved": True},
    "FIN-BANK-024": {"credit_impaired": True},
}
MISS_FACTS = {
    "FIN-BANK-002": {"dpd": 0},
    "FIN-BANK-003": {"dpd": 30},
    "FIN-BANK-004": {"dpd": 30},
    "FIN-BANK-005": {"dpd": 31, "credit_impaired": True},
    "FIN-BANK-006": {"paid_amount": 200, "due_amount": 200},
    "FIN-BANK-007": {"risk_class": "normal"},
    "FIN-BANK-009": {"npl_balance": 5, "total_balance": 100},
    "FIN-BANK-010": {"financial_difficulty": False, "contract_modified": True},
    "FIN-BANK-011": {"restructuring_flag": True, "days_since_restructure": 100},
    "FIN-BANK-012": {"extension_approved": False, "refinanced": False},
    "FIN-BANK-024": {"significant_increase": False, "credit_impaired": False},
}

YEAR = {"start": "2025-01-01", "end": "2025-12-31"}


class MetricDecisionsV8Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = assemble(load_config(CONFIG, None))
        cls.runtime.metadata.open(retry_seconds=10.0)
        cls.runtime.metadata.migrate()
        cls.meta = cls.runtime.metadata
        cls.compiler = MetricCompiler(cls.meta)
        cls.rules = RuleExecutor(cls.meta)
        cls._load_cust002()

    @classmethod
    def tearDownClass(cls) -> None:
        with cls.meta.tx() as tx:
            tx.execute(
                "DELETE FROM platform.cust_transaction WHERE data_source = 'fixture'",
                None,
            )
        cls.runtime.close()

    @classmethod
    def _load_cust002(cls) -> None:
        rows = (
            ("T1", "C1", "2025-01-05", "purchase", 100),
            ("T2", "C1", "2025-01-05", "purchase", 50),
            ("T3", "C1", "2025-01-10", "purchase", 20),
            ("T4", "C1", "2025-01-10", "refund", 30),
            ("T5", "C2", "2025-01-20", "purchase", 10),
        )
        with cls.meta.tx() as tx:
            for row in rows:
                tx.execute(
                    "INSERT INTO platform.cust_transaction (txn_id, customer_no,"
                    " txn_date, txn_type, amount, product_category, channel,"
                    " data_source, fixture) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (row[0], row[1], row[2], row[3], row[4], "card", "app",
                     "fixture", True),
                )

    def _row(self, metric_id: str) -> dict:
        rows = self.meta.query(
            "SELECT metric_kind, formula_expr, window_kind, numerator_agg,"
            " denominator_agg, missing, inference, publishable, decision_owner,"
            " decision_recommendation, computability_tier, output_mode, rule_set_json"
            " FROM platform.metric_definition WHERE metric_id = %s",
            (metric_id,),
        )
        self.assertTrue(rows, metric_id)
        return rows[0]

    # ------------------------------------------------------ partial quartets
    def test_01_partials_have_auditable_decisions(self) -> None:
        for metric_id in PARTIALS:
            row = self._row(metric_id)
            self.assertIsNotNone(row["metric_kind"], metric_id)
            self.assertIsNotNone(row["formula_expr"], metric_id)
            self.assertIsNotNone(row["window_kind"], metric_id)
            if row["computability_tier"] == "blocked_semantics":
                # V25 kept a few partials blocked and recorded the exact gap/owner.
                self.assertIsNotNone(row["missing"], metric_id)
            else:
                self.assertIsNone(row["missing"], metric_id)
            # v9 supersedes the v8 sign-off owner for the seeded rows; the
            # release flags themselves are asserted in test_metric_v9_seed.
            self.assertTrue(row["decision_owner"], metric_id)
            self.assertIsInstance(row["decision_recommendation"], dict, metric_id)
            rec = row["decision_recommendation"]
            for key in ("decisionId", "status", "reason", "impact", "changePoint"):
                self.assertIn(key, rec, metric_id)

    def test_02_scalar_partials_have_numerator_agg(self) -> None:
        # Non-scalar/derived metrics have no meaningful numerator aggregate.
        for metric_id in ("FIN-BANK-002", "FIN-BANK-017", "FIN-BANK-018",
                          "FIN-INS-009", "CUST-002", "CUST-005"):
            self.assertIsNotNone(self._row(metric_id)["numerator_agg"], metric_id)
        for metric_id in ("FIN-BANK-019", "FIN-INS-012", "CUST-004"):
            self.assertIsNone(self._row(metric_id)["numerator_agg"], metric_id)

    def test_03_partial_fields_by_family(self) -> None:
        self.assertEqual(self._row("FIN-BANK-017")["numerator_agg"], "count_distinct")
        self.assertEqual(self._row("FIN-BANK-017")["denominator_agg"], "count_distinct")
        self.assertEqual(self._row("FIN-INS-009")["numerator_agg"], "sum")
        self.assertEqual(self._row("CUST-002")["numerator_agg"], "count_distinct")
        self.assertEqual(self._row("FIN-BANK-019")["metric_kind"], "derived_rate")
        self.assertEqual(self._row("FIN-INS-012")["metric_kind"], "derived_rate")

    # ----------------------------------------------------------- rule specs
    def test_04_rule_specs_are_machine_readable(self) -> None:
        for metric_id in RULE_METRICS:
            row = self._row(metric_id)
            self.assertEqual(row["output_mode"], "rule_set", metric_id)
            self.assertIsInstance(row["rule_set_json"], list, metric_id)
            self.assertGreater(len(row["rule_set_json"]), 0, metric_id)
            for rule in row["rule_set_json"]:
                for key in ("id", "signal", "level", "window", "threshold",
                            "debounce", "suppression", "trigger_fields",
                            "configurable", "evidence_basis", "spec"):
                    self.assertIn(key, rule, f"{metric_id}/{rule.get('id')}")
                self.assertTrue(rule["trigger_fields"], metric_id)
                self.assertIsInstance(rule["spec"], dict, metric_id)
                self.assertIn(rule["level"], ("L1", "L2", "L3"), metric_id)

    def test_05_rule_executor_hit_miss_unevaluated(self) -> None:
        for metric_id in RULE_METRICS:
            hit = self.rules.execute(metric_id, [HIT_FACTS[metric_id]])
            self.assertGreater(hit["triggeredCount"], 0, metric_id)

            miss = self.rules.execute(metric_id, [MISS_FACTS[metric_id]])
            self.assertEqual(miss["triggeredCount"], 0, metric_id)
            self.assertEqual(miss["factsEvaluated"], 1, metric_id)

            missing = self.rules.execute(metric_id, [{}])
            self.assertTrue(missing["unevaluatedRules"], metric_id)
            self.assertEqual(missing["triggeredCount"], 0, metric_id)

    def test_06_rule_executor_no_data_is_typed(self) -> None:
        for metric_id in RULE_METRICS:
            with self.assertRaises(PortError) as ctx:
                self.rules.execute(metric_id, [])
            self.assertEqual(ctx.exception.provider_code, NO_DATA, metric_id)

    # ------------------------------------------------- CUST-002 binding
    def test_07_cust002_counts_distinct_days(self) -> None:
        result = self.compiler.execute(
            "CUST-002", internal=True, start=YEAR["start"], end=YEAR["end"],
            data_source="fixture",
        )
        rows = {r["entityKey"]: r for r in result["rows"]}
        # C1: {2025-01-05, 2025-01-10} = 2; refund on 01-10 excluded.
        self.assertEqual(rows["C1"]["value"], 2.0)
        # C2: {2025-01-20} = 1
        self.assertEqual(rows["C2"]["value"], 1.0)

    # ----------------------------------------------------------- boundaries
    def test_08_non_scalar_and_derived_are_explicit(self) -> None:
        with self.assertRaises(PortError) as ctx:
            self.compiler.compile("FIN-BANK-002", internal=True, start="2025-12-31",
                                  end="2025-12-31", data_source="fixture")
        self.assertEqual(ctx.exception.provider_code, RULE_SET_ONLY)

        # Derived metrics have no independent numerator aggregate -> quartet gate.
        with self.assertRaises(PortError) as ctx:
            self.compiler.compile("FIN-BANK-019", internal=True,
                                  start=YEAR["start"], end=YEAR["end"],
                                  data_source="fixture")
        self.assertEqual(ctx.exception.provider_code, NOT_COMPUTABLE)

        # The metric-reference syntax itself is rejected, never silently degraded.
        with self.assertRaises(PortError) as ctx:
            formula_to_sql("metric_fin_bank_017 * metric_fin_bank_018")
        self.assertEqual(ctx.exception.provider_code, EXPR_UNSUPPORTED)

        with self.assertRaises(PortError) as ctx:
            self.compiler.compile("CUST-004", internal=True, start="2025-12-31",
                                  end="2025-12-31", data_source="fixture")
        self.assertEqual(ctx.exception.provider_code, NOT_COMPUTABLE)

    def test_09_four_tier_distribution(self) -> None:
        rows = self.meta.query(
            "SELECT computability_tier, COUNT(*) AS n"
            " FROM platform.metric_definition GROUP BY 1"
        )
        counts = {r["computability_tier"]: r["n"] for r in rows}
        self.assertEqual(counts.get("structurally_computable"), 74)
        self.assertEqual(counts.get("blocked_rule"), None)
        self.assertEqual(counts.get("blocked_external"), 3)
        self.assertEqual(counts.get("blocked_semantics"), 8)
        self.assertEqual(sum(counts.values()), 85)

    def test_10_cust002_binding_registered(self) -> None:
        rows = self.meta.query(
            "SELECT fact_table, value_expr, agg, filter_sql, window_column, window_mode"
            " FROM platform.metric_field_binding WHERE metric_id = 'CUST-002'"
        )
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["fact_table"], "platform.cust_transaction")
        self.assertEqual(row["value_expr"], "txn_date")
        self.assertEqual(row["agg"], "count_distinct")
        self.assertEqual(row["window_mode"], "period")


if __name__ == "__main__":
    unittest.main()
