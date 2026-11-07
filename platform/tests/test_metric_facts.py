"""Entity facts -> observation projection -> calculator, fixture-only.

FIN-INS-021 is computed from policy snapshots (V41: issue_date + 13 months)
and FIN-BANK-001 from installment-level rows, never from pre-aggregated
numbers. All values are synthetic and must not be read as business
conclusions.
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
        cls._apply_v41()
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
            "WHERE metric_id = ANY(%s) AND data_source = 'fixture' AND fixture = true",
            (list(IDS),),
        )
        cls.meta.execute(
            "DELETE FROM platform.ins_payment_record WHERE policy_no LIKE %s",
            (PREFIX + "%",),
        )
        cls.meta.execute(
            "DELETE FROM platform.loan_installment_plan WHERE agreement_id LIKE %s",
            (PREFIX + "%",),
        )
        cls.meta.execute(
            "DELETE FROM platform.ins_policy WHERE policy_no LIKE %s",
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

    @classmethod
    def _apply_v41(cls) -> None:
        """Re-apply V41 (idempotent) so this suite never depends on whether
        the shared database migrated before the file last changed."""
        sql = files("platform_core").joinpath("sql/V41__metric_semantics.sql").read_text(
            encoding="utf-8"
        )
        for statement in split_sql_statements(sql):
            with cls.meta.tx() as tx:
                tx.execute(statement)

    def test_v20_migration_is_reentrant(self) -> None:
        # V25 added the v7 fact model; later migrations may raise the ceiling.
        self.assertGreaterEqual(SUPPORTED_SCHEMA_VERSION, 25)
        sql = files("platform_core").joinpath("sql/V20__metric_entities.sql").read_text(
            encoding="utf-8"
        )
        statements = split_sql_statements(sql)
        for _ in range(2):
            with self.meta.tx() as tx:
                for statement in statements:
                    tx.execute(statement)
        # V20 defines the pre-V41 body of FIN-INS-021; restore the current one.
        for _ in range(2):
            self._apply_v41()
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

    def _insert_policies(self) -> None:
        """One policy snapshot per policy at 2024-12-31.

        V41 anchors the 13-month cohort on issue_date + 13 months, so no
        ins_payment_record row is needed. All rows are single-pay on purpose:
        single premium must not be excluded from the persistency cohort.
        """
        rows = [
            ("H04-P1", "LIFE-A", "2022-12-01", "in_force"),
            ("H04-P2", "LIFE-A", "2022-12-01", "in_force"),
            ("H04-P3", "LIFE-A", "2022-12-01", "lapsed"),
            ("H04-P4", "LIFE-A", "2022-12-01", "surrendered"),
            ("H04-P5", "LIFE-A", "2022-12-01", "cancelled"),
            ("H04-Q1", "LIFE-B", "2022-12-01", "in_force"),
            ("H04-Q2", "LIFE-B", "2022-12-01", "in_force"),
            # X1: 2023-12-15 + 13 months = 2025-01-15, outside the window.
            ("H04-X1", "LIFE-A", "2023-12-15", "in_force"),
        ]
        with self.meta.tx() as tx:
            tx.executemany(
                "INSERT INTO platform.ins_policy (policy_no, product, channel, "
                "institution, issue_date, policy_year, premium_type, premium_amount, "
                "first_year_premium, policy_status, status_as_of, data_source, fixture) "
                "VALUES (%s, %s, 'agent', 'H04-INS', %s::date, 2, 'single', 1000, 1000, "
                "%s, '2024-12-31'::date, 'fixture', true)",
                rows,
            )

    def test_ins_021_is_entity_driven(self) -> None:
        self._insert_policies()
        projected = self._project(INS, date(2024, 1, 1), date(2024, 12, 31))
        self.assertTrue(projected["ok"], projected)
        self.assertEqual(projected["rowsProjected"], 2)

        card = self.metrics.compute(
            INS, period_start=date(2024, 1, 1), period_end=date(2024, 12, 31)
        )
        # LIFE-A: 5 in cohort (X1 anchored outside), 2 kept (P1,P2)
        # LIFE-B: 2 in cohort, 2 kept (Q1,Q2)
        # (2 + 2) / (5 + 2) * 100 = 57.142857...
        self.assertAlmostEqual(card["value"], 400.0 / 7.0, places=9)
        self.assertEqual(card["window"]["kind"], "period")
        self.assertEqual(card["sampleCount"], 2)
        self.assertEqual(card["dataSource"], "fixture")
        self.assertTrue(card["fixture"])
        self.assertEqual(card["definitionVersion"], "v3.0")
        rows = self.meta.query(
            "SELECT entity_key, numerator, denominator "
            "FROM platform.metric_observation WHERE metric_id = %s "
            "AND data_source = 'fixture' AND entity_key = ANY(%s) ORDER BY entity_key",
            (INS, ["LIFE-A", "LIFE-B"]),
        )
        self.assertEqual(
            [(row["entity_key"], row["numerator"], row["denominator"]) for row in rows],
            [("LIFE-A", 2.0, 5.0), ("LIFE-B", 2.0, 2.0)],
        )

    def test_period_window_short_is_rejected_before_write(self) -> None:
        before = self._obs_count(INS)
        rejected = self._project(INS, date(2024, 12, 1), date(2024, 12, 31))
        self.assertFalse(rejected["ok"])
        self.assertEqual(rejected["errorCode"], "E_METRIC_WINDOW_INSUFFICIENT")
        self.assertEqual(self._obs_count(INS), before)

    def test_distinct_count_semantics_are_declared(self) -> None:
        rows = self.meta.query(
            "SELECT metric_id, aggregation_semantics, denominator_agg, fact_function "
            "FROM platform.metric_definition "
            "WHERE metric_id IN ('FIN-INS-015','FIN-INS-016','FIN-INS-018',"
            "'FIN-INS-021','FIN-INS-025') "
            "ORDER BY metric_id"
        )
        for row in rows:
            self.assertEqual(row["aggregation_semantics"], "distinct_count")
            self.assertEqual(row["denominator_agg"], "sum")
        self.assertEqual(
            {row["metric_id"] for row in rows},
            {"FIN-INS-015", "FIN-INS-016", "FIN-INS-018", "FIN-INS-021", "FIN-INS-025"},
        )

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
