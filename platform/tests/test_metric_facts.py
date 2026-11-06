"""Entity facts -> observation projection -> calculator, fixture-only.

The two v3 metrics that had no fact table are computed here from
installment-level rows, never from pre-aggregated numbers. All values are
synthetic and must not be read as business conclusions.
"""

from __future__ import annotations

import os
import sys
import unittest
from datetime import date
from importlib.resources import files
from pathlib import Path

sys.path.insert(0, "/app/src")

from platform_core.adapters.metadata_pg import SUPPORTED_SCHEMA_VERSION
from platform_core.assembly import assemble
from platform_core.config import load_config
from platform_core.metric_facts import FactLoader, MetricProjector
from platform_core.sqlsplit import split_sql_statements

CONFIG = os.environ.get("PLATFORM_CONFIG", "/data/platform.yaml")
FIX = Path(__file__).resolve().parent / "fixtures" / "metrics" / "s14h04"

INS = "FIN-INS-021"
BANK = "FIN-BANK-001"
IDS = (INS, BANK)
PREFIX = "H04-"


class MetricFactsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = assemble(load_config(CONFIG, None))
        cls.runtime.metadata.open(retry_seconds=10.0)
        cls.runtime.metadata.migrate()
        cls.meta = cls.runtime.metadata
        cls.loader = FactLoader(cls.meta)
        cls.projector = MetricProjector(cls.meta)
        cls.metrics = cls.runtime.metrics
        cls._clean()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._clean()
        cls.runtime.close()

    def setUp(self) -> None:
        self._clean()

    @classmethod
    def _clean(cls) -> None:
        cls.meta.execute(
            "DELETE FROM platform.metric_observation "
            "WHERE metric_id = ANY(%s) AND entity_key LIKE %s",
            (list(IDS), PREFIX + "%"),
        )
        cls.meta.execute(
            "DELETE FROM platform.ins_payment_record WHERE policy_no LIKE %s",
            (PREFIX + "%",),
        )
        cls.meta.execute(
            "DELETE FROM platform.loan_installment_plan WHERE agreement_id LIKE %s",
            (PREFIX + "%",),
        )

    def _obs_count(self, metric_id: str) -> int:
        rows = self.meta.query(
            "SELECT COUNT(*) AS n FROM platform.metric_observation "
            "WHERE metric_id = %s AND definition_version = 'v3.0'",
            (metric_id,),
        )
        return int(rows[0]["n"])

    def _load(self, kind: str, name: str, apply: bool = True):
        return self.loader.load(
            kind=kind,
            file=str(FIX / name),
            apply=apply,
            data_source="fixture",
            fixture=True,
        )

    def _project(self, metric_id: str, start: date, end: date, apply: bool = True):
        return self.projector.project(
            metric_id=metric_id,
            window_start=start,
            window_end=end,
            data_source="fixture",
            apply=apply,
        )

    # ---- migration -----------------------------------------------------

    def test_v20_migration_is_reentrant(self) -> None:
        self.assertEqual(SUPPORTED_SCHEMA_VERSION, 23)
        sql = files("platform_core").joinpath("sql/V20__metric_entities.sql").read_text(
            encoding="utf-8"
        )
        statements = split_sql_statements(sql)
        for _ in range(2):
            with self.meta.tx() as tx:
                for statement in statements:
                    tx.execute(statement)
        rows = self.meta.query(
            "SELECT to_regclass('platform.ins_payment_record') AS ins, "
            "to_regclass('platform.loan_installment_plan') AS loan, "
            "to_regprocedure('platform.metric_fact_fin_ins_021(date,date,text)') AS f1, "
            "to_regprocedure('platform.metric_fact_fin_bank_001(date,date,text)') AS f2"
        )
        self.assertIsNotNone(rows[0]["ins"])
        self.assertIsNotNone(rows[0]["loan"])
        self.assertIsNotNone(rows[0]["f1"])
        self.assertIsNotNone(rows[0]["f2"])
        bound = self.meta.query(
            "SELECT metric_id, fact_function FROM platform.metric_definition "
            "WHERE metric_id = ANY(%s) ORDER BY metric_id",
            (list(IDS),),
        )
        self.assertEqual(
            {row["metric_id"]: row["fact_function"] for row in bound},
            {
                BANK: "platform.metric_fact_fin_bank_001",
                INS: "platform.metric_fact_fin_ins_021",
            },
        )

    # ---- loader contract ----------------------------------------------

    def test_fact_loader_dry_run_then_idempotent(self) -> None:
        dry = self._load("insurance_payment", "insurance_payment_records.csv", apply=False)
        self.assertTrue(dry["ok"], dry)
        self.assertEqual(dry["rowsValid"], 11)
        self.assertEqual(dry["rowsAfter"], 0)

        first = self._load("insurance_payment", "insurance_payment_records.csv")
        self.assertTrue(first["ok"], first)
        self.assertEqual(first["rowsAfter"], 11)
        second = self._load("insurance_payment", "insurance_payment_records.csv")
        self.assertTrue(second["ok"], second)
        self.assertEqual(second["rowsBefore"], 11)
        self.assertEqual(second["rowsAfter"], 11)

    def test_bad_row_rolls_back_whole_batch(self) -> None:
        before = self._load(
            "insurance_payment", "insurance_payment_records.csv", apply=False
        )["rowsBefore"]
        result = self._load("insurance_payment", "insurance_payment_bad.csv")
        self.assertFalse(result["ok"])
        self.assertEqual(result["errorCode"], "E_FACT_BAD_ROWS")
        self.assertEqual(result["errorCount"], 1)
        self.assertEqual(result["rowsAfter"], before)
        rows = self.meta.query(
            "SELECT COUNT(*) AS n FROM platform.ins_payment_record WHERE policy_no = 'H04-B1'"
        )
        self.assertEqual(int(rows[0]["n"]), 0)

    # ---- FIN-INS-021: period aggregation -------------------------------

    def test_ins_021_is_entity_driven(self) -> None:
        loaded = self._load("insurance_payment", "insurance_payment_records.csv")
        self.assertTrue(loaded["ok"], loaded)
        projected = self._project(INS, date(2024, 1, 1), date(2024, 12, 31))
        self.assertTrue(projected["ok"], projected)
        self.assertEqual(projected["rowsProjected"], 2)

        card = self.metrics.compute(
            INS, period_start=date(2024, 1, 1), period_end=date(2024, 12, 31)
        )
        # LIFE-A: 5 due, 2 kept (P1,P2; P3 unpaid, P4 lapsed, P5 latest=surrendered)
        # LIFE-B: 3 due, 2 kept (Q1,Q3; Q2 unpaid)
        # (2 + 2) / (5 + 3) * 100 = 50.0
        self.assertAlmostEqual(card["value"], 50.0, places=9)
        self.assertEqual(card["window"]["kind"], "period")
        self.assertEqual(card["sampleCount"], 2)
        self.assertEqual(card["dataSource"], "fixture")
        self.assertTrue(card["fixture"])
        self.assertEqual(card["definitionVersion"], "v3.0")

    def test_period_window_short_is_rejected_before_write(self) -> None:
        self.assertTrue(self._load("insurance_payment", "insurance_payment_records.csv")["ok"])
        before = self._obs_count(INS)
        rejected = self._project(INS, date(2024, 12, 1), date(2024, 12, 31))
        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["errorCode"], "E_METRIC_WINDOW_INSUFFICIENT")
        self.assertEqual(self._obs_count(INS), before)

    # ---- FIN-BANK-001: instant aggregation -----------------------------

    def test_bank_001_is_entity_driven(self) -> None:
        loaded = self._load("loan_installment", "loan_installment_plans.csv")
        self.assertTrue(loaded["ok"], loaded)
        projected = self._project(BANK, date(2024, 12, 31), date(2024, 12, 31))
        self.assertTrue(projected["ok"], projected)
        self.assertEqual(projected["rowsProjected"], 4)

        card = self.metrics.compute(BANK, as_of=date(2024, 12, 31))
        # A=0, B=45, C=90, D=0 at 2024-12-31; E only has 2024-09-30 (excluded)
        # max(0, 45, 90, 0) = 90
        self.assertAlmostEqual(card["value"], 90.0, places=9)
        self.assertEqual(card["window"]["kind"], "instant")
        self.assertEqual(card["sampleCount"], 4)
        self.assertEqual(card["dataSource"], "fixture")
        self.assertEqual(card["unit"], "天")

    def test_instant_metric_rejects_a_period_window(self) -> None:
        self.assertTrue(self._load("loan_installment", "loan_installment_plans.csv")["ok"])
        rejected = self._project(BANK, date(2024, 12, 30), date(2024, 12, 31))
        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["errorCode"], "E_METRIC_WINDOW_INSUFFICIENT")

    def test_metric_without_fact_source_is_rejected(self) -> None:
        rejected = self._project("FIN-BANK-025", date(2024, 12, 31), date(2024, 12, 31))
        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["errorCode"], "E_METRIC_FACT_SOURCE_MISSING")


if __name__ == "__main__":
    unittest.main()
