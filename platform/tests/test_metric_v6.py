"""V22 fact model: fixture -> projection -> calculator, and the rule executor.

Every number below is hand-computed in the docstring of the test that asserts
it. Fixtures use data_source=fixture and are deleted in tearDownClass, so
platform.metric_observation returns to its 0-row baseline.
"""

from __future__ import annotations

import os
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, "/app/src")

from platform_core.assembly import assemble
from platform_core.config import load_config
from platform_core.errors import PortError
from platform_core.metric_facts import FactLoader, MetricProjector

CONFIG = os.environ.get("PLATFORM_CONFIG", "/data/platform.yaml")
HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures" / "metrics" / "v6"

FACT_KINDS = (
    "bank_credit_application", "bank_credit_facility", "bank_collection_case",
    "bank_collection_recovery", "bank_npl_snapshot", "bank_disposal_event",
    "ins_policy", "cust_master", "cust_product_holding",
)
METRICS = (
    "FIN-BANK-031", "FIN-BANK-032", "FIN-BANK-035",
    "FIN-BANK-036-v1", "FIN-BANK-036-v2", "FIN-INS-001", "CUST-010",
)
TABLES = (
    "bank_credit_application", "bank_credit_facility", "bank_collection_case",
    "bank_collection_recovery", "bank_npl_snapshot", "bank_disposal_event",
    "ins_policy", "cust_master", "cust_product_holding",
)


class FactModelV6Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = assemble(load_config(CONFIG, None))
        cls.runtime.metadata.open(retry_seconds=10.0)
        cls.runtime.metadata.migrate()
        cls.meta = cls.runtime.metadata
        cls.loader = FactLoader(cls.meta)
        cls.projector = MetricProjector(cls.meta)
        cls.baseline = cls._observation_count()
        for kind in FACT_KINDS:
            result = cls.loader.load(
                kind=kind,
                file=str(FIXTURES / f"{kind}.csv"),
                apply=True,
                data_source="fixture",
                fixture=True,
            )
            assert result["ok"], result

    @classmethod
    def tearDownClass(cls) -> None:
        with cls.meta.tx() as tx:
            for table in TABLES:
                tx.execute(
                    f"DELETE FROM platform.{table} WHERE data_source = 'fixture'",
                    None,
                )
            tx.execute(
                "DELETE FROM platform.metric_observation WHERE data_source = 'fixture'",
                None,
            )
        cls.runtime.close()

    @classmethod
    def _observation_count(cls) -> int:
        rows = cls.meta.query(
            "SELECT COUNT(*) AS n FROM platform.metric_observation"
        )
        return int(rows[0]["n"])

    def _compute(self, metric_id: str, institution: str | None = None, **window):
        start = window.get("start") or window.get("as_of")
        end = window.get("end") or window.get("as_of")
        projected = self.projector.project(
            metric_id=metric_id,
            window_start=start,
            window_end=end,
            data_source="fixture",
            apply=True,
        )
        self.assertTrue(projected["ok"], projected)
        if "as_of" in window:
            return self.runtime.metrics.compute(
                metric_id, internal=True, as_of=window["as_of"],
                institution=institution,
            )
        return self.runtime.metrics.compute(
            metric_id,
            internal=True,
            period_start=window["start"],
            period_end=window["end"],
            institution=institution,
        )

    # ---- hand-checked computations -------------------------------------

    def test_01_bank_031_approval_rate(self) -> None:
        """First-accepted 2025-01: A1,A2,A3 (A4 duplicate, A5 test, A6 withdrawn).
        Approvals decided by 2025-03-02: A1 only -> 1/3 = 33.3333%."""
        result = self._compute(
            "FIN-BANK-031", start=date(2025, 1, 1), end=date(2025, 1, 31)
        )
        self.assertAlmostEqual(result["value"], 100 / 3, places=6)

    def test_02_bank_032_limit_utilization(self) -> None:
        """Active non-test non-internal: F1 900/1000 + F2 100/500 = 1000/1500
        -> 66.6667%; F3 frozen, F4 test, F5 internal excluded.

        Scoped to this suite's institution: synthetic observations for the
        same metric and as_of are written by the datagen track into the same
        database, and an unscoped sum would include them."""
        result = self._compute(
            "FIN-BANK-032", institution="B1", as_of=date(2025, 12, 31)
        )
        self.assertAlmostEqual(result["value"], 66.666667, places=6)

    def test_03_bank_035_collection_recovery(self) -> None:
        """T0 collecting: C1 1000 + C2 500 = 1500. In-window principal:
        C1 300 + C2 200 = 500 (C1's April 100 out of window, C3 not in cohort)
        -> 33.3333%."""
        result = self._compute(
            "FIN-BANK-035", start=date(2025, 1, 1), end=date(2025, 3, 31)
        )
        self.assertAlmostEqual(result["value"], 100 / 3, places=6)

    def test_04_bank_036_v1_disposal_rate(self) -> None:
        """Opening NPL 1000 + 500 = 1500; disposed gross 400 + 300 + 200
        (write-off counts as completed disposal) = 900 -> 60%."""
        result = self._compute(
            "FIN-BANK-036-v1", start=date(2025, 1, 1), end=date(2025, 3, 31)
        )
        self.assertAlmostEqual(result["value"], 60.0, places=6)

    def test_05_bank_036_v2_recovery_rate(self) -> None:
        """Recovery-method disposals only: D1 (350-10) + D2 (100+180-5)
        = 615; gross 400 + 300 = 700 -> 87.8571%."""
        result = self._compute(
            "FIN-BANK-036-v2", start=date(2025, 1, 1), end=date(2025, 3, 31)
        )
        self.assertAlmostEqual(result["value"], 87.857143, places=6)

    def test_06_insurance_premium_income(self) -> None:
        """January issue dates, non-investment: P1 (1000-50) + P2 2000 = 2950;
        P3 investment-linked and P4 issued in February are excluded."""
        result = self._compute(
            "FIN-INS-001", institution="I1", start=date(2025, 1, 1), end=date(2025, 1, 31)
        )
        self.assertAlmostEqual(result["value"], 2950.0, places=6)
        self.assertEqual(result["unit"], "元")

    def test_07_customer_products_per_customer(self) -> None:
        """Active customers M1,M2 (S1) and M4 (S2) = 3; active holdings
        M1 x2 + M2 x2 + M4 x1 = 5 -> 5/3 = 1.6667 products per customer.

        Scoped to this suite's institution (see test_02)."""
        result = self._compute(
            "CUST-010", institution="B1", as_of=date(2025, 12, 31)
        )
        self.assertAlmostEqual(result["value"], 5 / 3, places=6)

    # ---- rule executor -------------------------------------------------

    HIT = {
        "customerId": "K9", "asOf": "2025-12-31",
        "dpd": 95, "dpd_start": 20, "dpd_end": 95,
        "risk_class_prev": "normal", "risk_class_curr": "substandard",
        "rating_notch_prev": 1, "rating_notch_curr": 2,
        "drawn_principal": 950, "approved_limit": 1000,
        "monthly_inflow": 40, "inflow_12m_avg": 100,
        "consecutive_partial_count": 2, "paid_amount": 80, "due_amount": 100,
        "collateral_ratio_prev": 0.5, "collateral_ratio_curr": 0.3,
        "guarantee_status": "valid",
        "other_facility_dpd_90plus": True, "default_flag": False,
    }
    CLEAN = {
        "customerId": "K8", "asOf": "2025-12-31",
        "dpd": 0, "dpd_start": 0, "dpd_end": 0,
        "risk_class_prev": "normal", "risk_class_curr": "normal",
        "rating_notch_prev": 1, "rating_notch_curr": 1,
        "drawn_principal": 100, "approved_limit": 1000,
        "monthly_inflow": 100, "inflow_12m_avg": 100,
        "consecutive_partial_count": 0, "paid_amount": 100, "due_amount": 100,
        "collateral_ratio_prev": 0.5, "collateral_ratio_curr": 0.5,
        "guarantee_status": "valid",
        "other_facility_dpd_90plus": False, "default_flag": False,
    }

    def test_08_rule_set_hit(self) -> None:
        result = self.runtime.rules.execute("FIN-BANK-034", [self.HIT])
        self.assertEqual(result["outputMode"], "rule_set")
        self.assertEqual(result["ruleCount"], 10)
        self.assertEqual(result["level"], "L3")
        ids = [hit["ruleId"] for hit in result["hits"]]
        self.assertIn("R02", ids)   # dpd 95 >= 90
        self.assertIn("R07", ids)   # other facility 90+
        self.assertIn("R06", ids)   # 950/1000 = 95% >= 90%
        self.assertIn("R08", ids)   # inflow -60% vs 12m average
        self.assertEqual(result["customers"][0]["level"], "L3")

    def test_09_rule_set_no_hit(self) -> None:
        result = self.runtime.rules.execute("FIN-BANK-034", [self.CLEAN])
        self.assertEqual(result["triggeredCount"], 0)
        self.assertIsNone(result["level"])
        self.assertEqual(result["unevaluatedRules"], [])

    def test_10_rule_set_no_data(self) -> None:
        with self.assertRaises(PortError) as caught:
            self.runtime.rules.execute("FIN-BANK-034", [])
        self.assertEqual(caught.exception.provider_code, "E_METRIC_NO_DATA")

    def test_11_rule_executor_rejects_value_metric(self) -> None:
        with self.assertRaises(PortError) as caught:
            self.runtime.rules.execute("FIN-BANK-031", [self.CLEAN])
        self.assertEqual(caught.exception.provider_code, "E_METRIC_NOT_RULE_SET")

    def test_12_projection_keeps_fixture_provenance(self) -> None:
        for table in TABLES:
            rows = self.meta.query(
                f"SELECT COUNT(*) AS n FROM platform.{table} "
                "WHERE data_source = 'fixture'"
            )
            self.assertGreater(int(rows[0]["n"]), 0, table)
        # Scope to the entity keys this suite projected. Other tracks write
        # synthetic/business observations for the same definitions into the
        # same database; asserting "no non-fixture row for this metric at all"
        # would go red as soon as the platform is used normally.
        rows = self.meta.query(
            "SELECT COUNT(*) AS n FROM platform.metric_observation "
            "WHERE metric_id = ANY(%s) AND data_source <> 'fixture' "
            "AND entity_key IN ("
            " SELECT entity_key FROM platform.metric_observation "
            " WHERE metric_id = ANY(%s) AND data_source = 'fixture')",
            (list(METRICS), list(METRICS)),
        )
        self.assertEqual(int(rows[0]["n"]), 0)
        fixture_rows = self.meta.query(
            "SELECT COUNT(*) AS n FROM platform.metric_observation "
            "WHERE metric_id = ANY(%s) AND fixture",
            (list(METRICS),),
        )
        self.assertGreater(int(fixture_rows[0]["n"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
