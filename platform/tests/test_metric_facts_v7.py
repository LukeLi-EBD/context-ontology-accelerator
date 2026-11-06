"""V25 fact model: 8 new tables + 2 extensions, 44 metrics compile and execute.

Fixtures are written with data_source='fixture' and removed in tearDownClass.
No metric_observation row is produced; the compiler only reads fact tables.
"""

from __future__ import annotations

import os
import sys
import unittest
from datetime import date

sys.path.insert(0, "/app/src")

from platform_core.assembly import assemble
from platform_core.config import load_config
from platform_core.metric_compiler import MetricCompiler

CONFIG = os.environ.get("PLATFORM_CONFIG", "/data/platform.yaml")
YEAR = {"start": "2025-01-01", "end": "2025-12-31"}
TWO_YEARS = {"start": "2024-01-01", "end": "2025-12-31"}
JAN = {"start": "2025-01-01", "end": "2025-01-30"}
# compile() resolves an instant window from start (falling back to end), so callers
# pass the as-of date as both bounds.
AS_OF = {"start": "2025-12-31", "end": "2025-12-31"}

FACT_TABLES = (
    "bank_loan_account", "bank_provision_snapshot", "bank_concentration_stat",
    "ins_underwriting_stat", "ins_claim_reserve_snapshot", "ins_persistence_stat",
    "ins_claim_case", "ins_policy",
    "cust_behavior_snapshot", "cust_cohort_stat", "cust_aum_snapshot",
)


class MetricFactsV7Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = assemble(load_config(CONFIG, None))
        cls.runtime.metadata.open(retry_seconds=10.0)
        cls.runtime.metadata.migrate()
        cls.meta = cls.runtime.metadata
        cls.compiler = MetricCompiler(cls.meta)
        cls._cleanup()
        cls._load()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._cleanup()
        cls.runtime.close()

    @classmethod
    def _cleanup(cls) -> None:
        with cls.meta.tx() as tx:
            for table in FACT_TABLES:
                tx.execute(
                    f"DELETE FROM platform.{table} WHERE data_source = 'fixture'", None
                )

    @classmethod
    def _load(cls) -> None:
        with cls.meta.tx() as tx:
            for row in (
                ("A", "CU1", "normal", "special", 100, 90, 10, 45, 70,
                 "2025-03-01", True),
                ("B", "CU2", "normal", "normal", 200, 180, 20, 0, 0,
                 "2025-03-01", False),
                ("C", "CU3", "special", "special", 50, 50, 0, 45, 50, None, False),
            ):
                tx.execute(
                    "INSERT INTO platform.bank_loan_account (account_id, customer_no,"
                    " product, risk_class, account_status, as_of, institution,"
                    " period_start, risk_class_start, risk_class_end, balance_start,"
                    " balance_end, period_decrease_amount, dpd_start, dpd_end,"
                    " first_payment_due_date, first_payment_default_flag,"
                    " data_source, fixture) VALUES"
                    " (%s,%s,'loan',%s,'active','2025-12-31','TEST-BANK','2025-01-01',"
                    " %s,%s,%s,%s,%s,%s,%s,%s,%s,'fixture',true)",
                    (row[0], row[1], row[3], row[2], row[3], row[4], row[5],
                     row[6], row[7], row[8], row[9], row[10]),
                )
            tx.execute(
                "INSERT INTO platform.bank_provision_snapshot (institution, as_of,"
                " provision_balance, npl_balance, loan_balance, data_source, fixture)"
                " VALUES ('TEST-BANK','2025-12-31',30,10,100,'fixture',true)", None,
            )
            tx.execute(
                "INSERT INTO platform.bank_concentration_stat (institution, as_of,"
                " capital_balance, capital_net, tier1_capital_net,"
                " max_single_customer_loan, max_single_customer_exposure,"
                " max_group_exposure, max_group_credit, total_related_exposure,"
                " data_source, fixture) VALUES"
                " ('TEST-BANK','2025-12-31',1000,800,600,150,120,140,200,250,"
                " 'fixture',true)", None,
            )
            # P1 property, P2 other (channel agent), L1 life, H1 health
            for row in (
                ("prop", "-", "property", 100, 120, 90, 20, 80, 10, 70,
                 40, 10, 5, 2, 15, 8, 0, 0, 0, 0, 50),
                ("prop2", "agent", "other", 50, 0, 0, 0, 50, 0, 50,
                 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0),
                ("life1", "-", "life", 100, 0, 0, 10, 90, 0, 90,
                 0, 0, 0, 0, 0, 0, 20, 100, 10, 5, 50),
                ("health1", "-", "health", 70, 0, 0, 10, 60, 0, 60,
                 20, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            ):
                tx.execute(
                    "INSERT INTO platform.ins_underwriting_stat"
                    " (institution, product, channel, business_line, period_start,"
                    " period_end, signed_premium, plan_premium, collected_premium,"
                    " ceded_premium, retained_premium, unearned_reserve_change,"
                    " earned_premium, paid_claims, claim_reserve_change,"
                    " reinsurance_recoverable, long_term_reserve_change,"
                    " expense_total, commission_expense, surrender_amount,"
                    " beginning_reserve_total, policyholder_deposit_beginning,"
                    " separate_account_beginning, current_term_premium,"
                    " data_source, fixture) VALUES"
                    " ('TEST-INS',%s,%s,%s,'2025-01-01','2025-12-31',"
                    " %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"
                    " 'fixture',true)",
                    (row[0], row[1], row[2], row[3], row[4], row[5], row[6],
                     row[7], row[8], row[9], row[10], row[11], row[12], row[13],
                     row[14], row[15], row[16], row[17], row[18], row[19],
                     row[20]),
                )
            for row in (
                ("CL1", "prop", 10, 5, 1, "open"),
                ("CL2", "prop", 4, 2, 0, "open"),
                ("CL3", "other", 20, 0, 0, "open"),
                ("CL4", "prop", 99, 99, 99, "closed"),
            ):
                tx.execute(
                    "INSERT INTO platform.ins_claim_reserve_snapshot (claim_no,"
                    " institution, product, as_of, reported_reserve, ibnr_reserve,"
                    " expense_reserve, case_status, data_source, fixture) VALUES"
                    " (%s,'TEST-INS',%s,'2025-12-31',%s,%s,%s,%s,'fixture',true)",
                    row,
                )
            for row in (
                ("C1", "P1", "prop", "2025-02-01", "2025-02-01", "reported"),
                ("C2", "P2", "prop", "2025-02-05", "2025-02-05", "reported"),
                ("C3", "P3", "prop", "2025-02-06", "2025-02-06", "withdrawn"),
                ("C4", "P4", "other", "2025-03-01", "2025-03-01", "reported"),
            ):
                tx.execute(
                    "INSERT INTO platform.ins_claim_case (claim_no, policy_no,"
                    " product, institution, report_date, filing_date, claim_status,"
                    " data_source, fixture) VALUES"
                    " (%s,%s,%s,'TEST-INS',%s,%s,%s,'fixture',true)",
                    row,
                )
            for row in (
                ("P1", "prop", "individual_agent", "regular", 1000, 100),
                ("P2", "prop", "individual_agent", "regular", 1000, 100),
                ("P3", "prop", "individual_agent", "regular", 1000, 100),
                ("P4", "other", "agency", "regular", 1000, 100),
                ("P5", "prop", "individual_agent", "single", 200, None),
                ("P6", "prop", "unknown", "regular", 1000, 100),
            ):
                tx.execute(
                    "INSERT INTO platform.ins_policy (policy_no, product, channel,"
                    " institution, issue_date, premium_type, premium_amount,"
                    " first_year_premium, policy_status, status_as_of,"
                    " data_source, fixture) VALUES"
                    " (%s,%s,%s,'TEST-INS','2025-01-01',%s,%s,%s,'in_force',"
                    " '2025-12-31','fixture',true)",
                    row,
                )
            for row in (
                ("prop", "grace", 2, 100, 70, 0, 0),
                ("prop", "natural", 2, 100, 80, 0, 0),
                ("prop", "grace", 3, 100, 60, 0, 0),
                ("prop", "vehicle_renewal", 1, 0, 0, 20, 15),
            ):
                tx.execute(
                    "INSERT INTO platform.ins_persistence_stat (institution, product,"
                    " channel, cohort_period, valuation_basis, renewal_year,"
                    " first_year_premium, renewed_premium, due_vehicle_count,"
                    " renewed_vehicle_count, data_source, fixture) VALUES"
                    " ('TEST-INS',%s,'-','2025-01-01',%s,%s,%s,%s,%s,%s,"
                    " 'fixture',true)",
                    row,
                )
            for row in (
                ("CU1", "2025-12-26", 5, "2025-12-20", 30),
                ("CU2", "2025-12-21", 10, "2025-12-01", 5),
                ("CU3", None, None, None, 30),
            ):
                tx.execute(
                    "INSERT INTO platform.cust_behavior_snapshot (customer_no,"
                    " institution, as_of, last_behavior_date,"
                    " days_since_last_behavior, last_txn_date,"
                    " days_since_proxy_event, data_source, fixture) VALUES"
                    " (%s,'TEST-CUST','2025-12-31',%s,%s,%s,%s,'fixture',true)",
                    row,
                )
            for row in (
                ("K1", "2024-01-01", 100, 60, 40, 50, 30),
                ("K2", "2024-02-01", 50, 25, 20, 50, 10),
            ):
                tx.execute(
                    "INSERT INTO platform.cust_cohort_stat (cohort_key, institution,"
                    " cohort_month, as_of, cohort_customers, retained_customers,"
                    " active_customers, prior_month_active, active_and_prior_month,"
                    " data_source, fixture) VALUES"
                    " (%s,'TEST-CUST',%s,'2025-12-31',%s,%s,%s,%s,%s,"
                    " 'fixture',true)",
                    row,
                )
            for row in (
                ("CU1", "deposit", "2025-01-01", 100),
                ("CU1", "deposit", "2025-01-02", 200),
                ("CU1", "deposit", "2025-01-03", 300),
                ("CU1", "deposit", "2025-12-31", 100),
                ("CU1", "wealth", "2025-12-31", 50),
                ("CU2", "deposit", "2025-12-31", 40),
            ):
                tx.execute(
                    "INSERT INTO platform.cust_aum_snapshot (customer_no,"
                    " institution, product_type, as_of, aum, data_source, fixture)"
                    " VALUES (%s,'TEST-CUST',%s,%s,%s,'fixture',true)",
                    row,
                )

    def _run(self, metric_id: str, window: dict) -> dict:
        result = self.compiler.execute(
            metric_id, start=window["start"], end=window["end"], internal=True
        )
        return {r["entityKey"]: r["value"] for r in result["rows"]}

    def _value(self, metric_id: str, window: dict, key: str) -> float:
        return self._run(metric_id, window)[key]

    # ---------------------------------------------------------------- schema
    def test_01_new_tables_are_documented(self) -> None:
        rows = self.meta.query(
            "SELECT c.relname AS table_name, d.description AS comment"
            " FROM pg_class c"
            " JOIN pg_namespace n ON n.oid = c.relnamespace"
            " LEFT JOIN pg_description d ON d.objoid = c.oid AND d.objsubid = 0"
            " WHERE n.nspname = 'platform' AND c.relkind = 'r'"
            " AND c.relname IN ('bank_provision_snapshot','bank_concentration_stat',"
            "'ins_underwriting_stat','ins_claim_reserve_snapshot',"
            "'ins_persistence_stat','cust_behavior_snapshot','cust_cohort_stat',"
            "'cust_aum_snapshot')"
        )
        self.assertEqual(len(rows), 8)
        for row in rows:
            self.assertIn("business_meaning", row["comment"])
            self.assertIn("why_this_way", row["comment"])
            self.assertRegex(row["comment"], r"basis: (regulatory|industry|inferred)")
        columns = self.meta.query(
            "SELECT c.relname AS table_name, a.attname AS column_name,"
            " d.description AS comment"
            " FROM pg_class c"
            " JOIN pg_namespace n ON n.oid = c.relnamespace"
            " JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0"
            " LEFT JOIN pg_description d ON d.objoid = c.oid AND d.objsubid = a.attnum"
            " WHERE n.nspname = 'platform' AND c.relkind = 'r'"
            " AND c.relname IN ('bank_provision_snapshot','bank_concentration_stat',"
            "'ins_underwriting_stat','ins_claim_reserve_snapshot',"
            "'ins_persistence_stat','cust_behavior_snapshot','cust_cohort_stat',"
            "'cust_aum_snapshot')"
        )
        undocumented = [
            (r["table_name"], r["column_name"]) for r in columns
            if r["column_name"] not in ("created_at", "fixture", "data_source")
            and (not r["comment"] or "business_meaning" not in r["comment"])
        ]
        self.assertEqual(undocumented, [])
        extended = self.meta.query(
            "SELECT c.relname AS table_name, a.attname AS column_name,"
            " d.description AS comment"
            " FROM pg_class c"
            " JOIN pg_namespace n ON n.oid = c.relnamespace"
            " JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0"
            " LEFT JOIN pg_description d ON d.objoid = c.oid AND d.objsubid = a.attnum"
            " WHERE n.nspname = 'platform' AND c.relkind = 'r'"
            " AND ((c.relname = 'bank_loan_account' AND a.attname IN"
            " ('period_start','risk_class_start','risk_class_end','balance_start',"
            "'balance_end','period_decrease_amount','dpd_start','dpd_end',"
            "'first_payment_due_date','first_payment_default_flag'))"
            " OR (c.relname = 'ins_claim_case' AND a.attname = 'filing_date'))"
        )
        self.assertEqual(len(extended), 11)
        for row in extended:
            self.assertIn("business_meaning", row["comment"])
            self.assertIn("why_this_way", row["comment"])
            self.assertRegex(row["comment"], r"basis: (regulatory|industry|inferred)")

    # ----------------------------------------------------------------- bank
    def test_02_bank_migration_dpd_fpd(self) -> None:
        # 期初正常类向下迁徙 90（A：100-10）／（期初正常类余额 300 − 期间减少 30）
        self.assertAlmostEqual(self._value("FIN-BANK-013", AS_OF, "TEST-BANK"),
                               90 / 270 * 100, places=6)
        self.assertAlmostEqual(self._value("FIN-BANK-017", AS_OF, "TEST-BANK"),
                               1 / 2 * 100, places=6)
        self.assertAlmostEqual(self._value("FIN-BANK-033", YEAR, "TEST-BANK"),
                               1 / 2 * 100, places=6)

    def test_03_bank_provision_and_concentration(self) -> None:
        expected = {
            "FIN-BANK-022": 30 / 10 * 100,
            "FIN-BANK-023": 30 / 100 * 100,
            "FIN-BANK-025": 150 / 1000 * 100,
            "FIN-BANK-026": 120 / 600 * 100,
            "FIN-BANK-027": 140 / 600 * 100,
            "FIN-BANK-028": 200 / 800 * 100,
            "FIN-BANK-029": 250 / 800 * 100,
            "FIN-BANK-030": 140 / 600 * 100,
        }
        for metric_id, value in expected.items():
            self.assertAlmostEqual(self._value(metric_id, AS_OF, "TEST-BANK"),
                                   value, places=6, msg=metric_id)

    # ------------------------------------------------------------ insurance
    def test_04_underwriting_ratios(self) -> None:
        expected = {
            "FIN-INS-003": 90,
            "FIN-INS-006": 90 / 120 * 100,
            "FIN-INS-008": 45 / 70 * 100,
            "FIN-INS-009": 25 / 50 * 100,
            "FIN-INS-011": 60 / 70 * 100,
            "FIN-INS-027": 15 / 70 * 100,
        }
        for metric_id, value in expected.items():
            self.assertAlmostEqual(self._value(metric_id, YEAR, "TEST-INS"),
                                   value, places=6, msg=metric_id)
        self.assertAlmostEqual(self._value("FIN-INS-013", TWO_YEARS, "TEST-INS"),
                               47 / 68 * 100, places=6)

    def test_05_claim_reserves_and_report_rates(self) -> None:
        reserves = self._run("FIN-INS-014", AS_OF)
        self.assertAlmostEqual(reserves["prop"], 22, places=6)
        self.assertAlmostEqual(reserves["other"], 20, places=6)
        per_claim = self._run("FIN-INS-016", AS_OF)
        self.assertAlmostEqual(per_claim["prop"], 22 / 2, places=6)
        self.assertAlmostEqual(per_claim["other"], 20 / 1, places=6)
        reports = self._run("FIN-INS-017", YEAR)
        self.assertAlmostEqual(reports["prop"], 2 / 5 * 100, places=6)
        self.assertAlmostEqual(reports["other"], 1 / 1 * 100, places=6)
        filings = self._run("FIN-INS-018", YEAR)
        self.assertAlmostEqual(filings["prop"], 2 / 2 * 100, places=6)
        self.assertAlmostEqual(filings["other"], 1 / 1 * 100, places=6)

    def test_06_surrender_persistence_channel(self) -> None:
        self.assertAlmostEqual(self._value("FIN-INS-019", YEAR, "TEST-INS"),
                               20 / 165 * 100, places=6)
        self.assertAlmostEqual(self._value("FIN-INS-020", YEAR, "TEST-INS"),
                               20 / 150 * 100, places=6)
        self.assertAlmostEqual(self._value("FIN-INS-022-v1", YEAR, "prop"), 70, places=6)
        self.assertAlmostEqual(self._value("FIN-INS-022-v2", YEAR, "prop"), 80, places=6)
        self.assertAlmostEqual(self._value("FIN-INS-024", YEAR, "prop"), 75, places=6)
        self.assertAlmostEqual(self._value("FIN-INS-023-v1", TWO_YEARS, "prop"), 60, places=6)
        self.assertAlmostEqual(self._value("FIN-INS-025", YEAR, "individual_agent"), 125, places=6)
        self.assertAlmostEqual(self._value("FIN-INS-026", YEAR, "agent"), 20, places=6)
        self.assertAlmostEqual(self._value("FIN-INS-028", YEAR, "agent"), 0, places=6)

    # ------------------------------------------------------------- customer
    def test_07_customer_recency_and_retention(self) -> None:
        recency = self._run("CUST-001", AS_OF)
        self.assertAlmostEqual(recency["CU1"], 5, places=6)
        self.assertAlmostEqual(recency["CU2"], 10, places=6)
        proxy = self._run("CUST-005", AS_OF)
        self.assertEqual(set(proxy), {"CU3"})
        self.assertAlmostEqual(proxy["CU3"], 30, places=6)
        retention = self._run("CUST-006", AS_OF)
        self.assertAlmostEqual(retention["K1"], 60, places=6)
        self.assertAlmostEqual(retention["K2"], 50, places=6)
        churn = self._run("CUST-007", AS_OF)
        self.assertAlmostEqual(churn["K1"], 60, places=6)
        self.assertAlmostEqual(churn["K2"], 60, places=6)
        self.assertAlmostEqual(self._value("CUST-008", AS_OF, "TEST-CUST"), 40, places=6)

    def test_08_customer_aum_point_and_daily_average(self) -> None:
        aum = self._run("CUST-012", AS_OF)
        self.assertAlmostEqual(aum["CU1"], 150, places=6)
        self.assertAlmostEqual(aum["CU2"], 40, places=6)
        daily = self._run("CUST-013", JAN)
        self.assertAlmostEqual(daily["CU1"], 200, places=6)

    def test_09_no_metric_observation_written(self) -> None:
        rows = self.meta.query("SELECT COUNT(*) AS n FROM platform.metric_observation")
        self.assertEqual(rows[0]["n"], 0)


if __name__ == "__main__":
    unittest.main()
