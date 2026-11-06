"""G2 metrics-core: M-01 compute route + M-06 readiness ledger.

Fixtures are written with data_source='fixture' and removed in tearDownClass;
no metric_observation rows are touched. Values below are hand-computed from
the inserted rows, not copied from any prior run.
"""

from __future__ import annotations

import os
import sys
import unittest
from importlib.resources import files

sys.path.insert(0, "/app/src")

from fastapi.testclient import TestClient

import platform_core.api as api_module
from platform_core.assembly import assemble
from platform_core.config import load_config
from platform_core.sqlsplit import split_sql_statements

CONFIG = os.environ.get("PLATFORM_CONFIG", "/data/platform.yaml")
AS_OF = "2025-12-31"
Q4 = {"periodStart": "2025-10-01", "periodEnd": "2025-12-31"}
INST = "M01-INST-A"

# account rows: (id, risk_class, principal_balance, start_class, end_class,
#                balance_start, period_decrease_amount)
ACCOUNTS = (
    ("A1", "special", 80, "normal", "special", 100, 20),
    ("A2", "normal", 200, "normal", "normal", 200, 0),
    ("A3", "substandard", 150, "special", "substandard", 150, 0),
    ("A4", "special", 50, "special", "special", 50, 0),
    ("A5", "doubtful", 120, "substandard", "doubtful", 120, 0),
    ("A6", "substandard", 80, "substandard", "substandard", 80, 0),
    ("A7", "loss", 90, "doubtful", "loss", 90, 0),
    ("A8", "doubtful", 60, "doubtful", "doubtful", 60, 0),
    ("A9", "loss", 40, "loss", "loss", 40, 0),
)


class G2MetricsCoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = assemble(load_config(CONFIG, None))
        cls.runtime.metadata.open(retry_seconds=10.0)
        cls.runtime.metadata.migrate()
        cls.meta = cls.runtime.metadata
        cls.client = TestClient(api_module.create_app(cls.runtime, []))
        cls._load()

    @classmethod
    def tearDownClass(cls) -> None:
        with cls.meta.tx() as tx:
            for table in ("bank_loan_account", "bank_concentration_stat",
                          "ins_policy", "ins_claim_case"):
                tx.execute(f"DELETE FROM platform.{table} WHERE data_source = 'fixture'", None)
        cls.runtime.close()

    # ------------------------------------------------------------- fixtures
    @classmethod
    def _loan(cls, tx, row) -> None:
        tx.execute(
            "INSERT INTO platform.bank_loan_account (account_id, customer_no, product,"
            " risk_class, principal_balance, account_status, as_of, institution,"
            " period_start, risk_class_start, risk_class_end, balance_start,"
            " balance_end, period_decrease_amount, data_source, fixture)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (row[0], "M01-C-" + row[0], "mortgage", row[1], row[2], "active", AS_OF,
             INST, "2025-01-01", row[3], row[4], row[5], row[2], row[6], "fixture", True),
        )

    @classmethod
    def _load(cls) -> None:
        with cls.meta.tx() as tx:
            for row in ACCOUNTS:
                cls._loan(tx, row)
            for inst, tier1, exposure in (
                (INST, 8000, 120), ("M01-INST-B", 5000, 250),
            ):
                tx.execute(
                    "INSERT INTO platform.bank_concentration_stat (institution, as_of,"
                    " tier1_capital_net, max_single_customer_exposure, data_source, fixture)"
                    " VALUES (%s,%s,%s,%s,%s,%s)",
                    (inst, AS_OF, tier1, exposure, "fixture", True),
                )
            for policy in (
                ("M01-P1", "term_life", "2025-11-10", 1000, 0),
                ("M01-P2", "term_life", "2025-12-20", 2000, 100),
                ("M01-P3", "health", "2025-10-15", 500, 0),
                ("M01-P4", "term_life", "2025-09-15", 3000, 0),
            ):
                tx.execute(
                    "INSERT INTO platform.ins_policy (policy_no, product, channel,"
                    " institution, customer_no, issue_date, premium_type, premium_amount,"
                    " reversal_amount, policy_status, status_as_of, data_source, fixture)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (policy[0], policy[1], "personal", INST, "M01-C1", policy[2],
                     "regular", policy[3], policy[4], "in_force", AS_OF, "fixture", True),
                )
            for claim in (
                ("M01-K1", "term_life", "2025-11-05", "2025-11-06", "paid", 500),
                ("M01-K2", "term_life", "2025-11-20", None, "rejected", 0),
                ("M01-K3", "term_life", "2025-12-10", "2025-12-11", "paid", 600),
                ("M01-K4", "term_life", "2025-11-01", "2025-11-02", "withdrawn", 0),
                ("M01-K5", "health", "2025-10-05", "2025-10-06", "paid", 400),
            ):
                tx.execute(
                    "INSERT INTO platform.ins_claim_case (claim_no, policy_no, product,"
                    " institution, report_date, filing_date, claim_amount, paid_amount,"
                    " claim_status, data_source, fixture)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (claim[0], "M01-P1", claim[1], INST, claim[2], claim[3],
                     claim[4] == "paid" and claim[5] or 0, claim[5], claim[4],
                     "fixture", True),
                )

    # ------------------------------------------------------------- helpers
    def _compute(self, metric_id: str, **params):
        response = self.client.get(f"/metrics/{metric_id}/compute",
                                   params={"dataSource": "fixture", **params})
        return response

    def _rows(self, response) -> dict[str, dict]:
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertGreater(body["rowCount"], 0, body)
        return {str(row["entityKey"]): row for row in body["rows"]}

    # ---------------------------------------------------- M-01 8 selected
    def test_01_npl_ratio(self) -> None:
        # NPL 540 / total 870 = 62.0689655%
        rows = self._rows(self._compute("FIN-BANK-008", asOf=AS_OF))
        self.assertAlmostEqual(rows[INST]["numerator"], 540.0, places=6)
        self.assertAlmostEqual(rows[INST]["denominator"], 870.0, places=6)
        self.assertAlmostEqual(rows[INST]["value"], 62.068966, places=5)

    def test_02_normal_migration(self) -> None:
        # numerator 80 (100 start - 20 decrease) / denominator 300 = 26.666667
        rows = self._rows(self._compute("FIN-BANK-013", asOf=AS_OF))
        self.assertAlmostEqual(rows[INST]["numerator"], 80.0, places=6)
        self.assertAlmostEqual(rows[INST]["denominator"], 300.0, places=6)
        self.assertAlmostEqual(rows[INST]["value"], 26.666667, places=5)

    def test_03_special_migration(self) -> None:
        rows = self._rows(self._compute("FIN-BANK-014", asOf=AS_OF))
        self.assertAlmostEqual(rows[INST]["value"], 75.0, places=5)

    def test_04_substandard_migration(self) -> None:
        rows = self._rows(self._compute("FIN-BANK-015", asOf=AS_OF))
        self.assertAlmostEqual(rows[INST]["value"], 60.0, places=5)

    def test_05_doubtful_migration(self) -> None:
        rows = self._rows(self._compute("FIN-BANK-016", asOf=AS_OF))
        self.assertAlmostEqual(rows[INST]["value"], 60.0, places=5)

    def test_06_concentration(self) -> None:
        # 120/8000=1.5%; 250/5000=5.0%
        rows = self._rows(self._compute("FIN-BANK-026", asOf=AS_OF))
        self.assertAlmostEqual(rows[INST]["value"], 1.5, places=6)
        self.assertAlmostEqual(rows["M01-INST-B"]["value"], 5.0, places=6)

    def test_07_signed_premium(self) -> None:
        rows = self._rows(self._compute("FIN-INS-002", **Q4))
        self.assertAlmostEqual(rows["term_life"]["value"], 2900.0, places=6)
        self.assertAlmostEqual(rows["health"]["value"], 500.0, places=6)

    def test_08_claim_filing_rate(self) -> None:
        # term_life: filed 2 / reported 3 (withdrawn excluded) = 66.666667
        rows = self._rows(self._compute("FIN-INS-018", **Q4))
        self.assertAlmostEqual(rows["term_life"]["numerator"], 2.0, places=6)
        self.assertAlmostEqual(rows["term_life"]["denominator"], 3.0, places=6)
        self.assertAlmostEqual(rows["term_life"]["value"], 66.666667, places=5)

    def test_09_recomputable_after_new_fact(self) -> None:
        first = self._rows(self._compute("FIN-BANK-013", asOf=AS_OF))[INST]["value"]
        extra = ("A10", "normal", 100, "normal", "special", 100, 0)
        with self.meta.tx() as tx:
            self._loan(tx, extra)
        try:
            second = self._rows(self._compute("FIN-BANK-013", asOf=AS_OF))[INST]
            # numerator 80+100=180; denominator 300+100=400 -> 45%
            self.assertAlmostEqual(second["numerator"], 180.0, places=6)
            self.assertAlmostEqual(second["value"], 45.0, places=6)
            self.assertNotAlmostEqual(first, second["value"], places=3)
        finally:
            self.meta.execute(
                "DELETE FROM platform.bank_loan_account WHERE data_source = 'fixture'"
                " AND account_id = 'A10'",
                None,
            )
        restored = self._rows(self._compute("FIN-BANK-013", asOf=AS_OF))[INST]["value"]
        self.assertAlmostEqual(restored, first, places=6)

    # -------------------------------------------------------- explicit errors
    def test_10_non_executable_has_code_and_reason(self) -> None:
        response = self._compute("FIN-BANK-019", asOf=AS_OF)
        self.assertEqual(response.status_code, 400, response.text)
        error = response.json()["error"]
        self.assertEqual(error["providerCode"], "E_METRIC_NOT_STRUCTURALLY_COMPUTABLE")
        self.assertIn("quartet incomplete", error["message"])
        self.assertEqual(error["details"]["metricId"], "FIN-BANK-019")

    def test_11_rule_set_routes_to_rules(self) -> None:
        response = self._compute("FIN-BANK-034", asOf=AS_OF)
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(
            response.json()["error"]["providerCode"], "E_METRIC_RULE_SET_ONLY"
        )

    def test_12_missing_binding(self) -> None:
        response = self._compute("FIN-BANK-001", asOf=AS_OF, internal="true")
        self.assertEqual(response.status_code, 400, response.text)
        error = response.json()["error"]
        self.assertEqual(error["providerCode"], "E_METRIC_BINDING_MISSING")
        self.assertIn("numerator", error["message"])

    def test_13_not_publishable_gate(self) -> None:
        response = self._compute("CUST-001", asOf=AS_OF)
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(
            response.json()["error"]["providerCode"], "E_METRIC_NOT_PUBLISHABLE"
        )

    def test_14_unknown_metric(self) -> None:
        response = self._compute("NO-SUCH-METRIC", asOf=AS_OF)
        # MetricCompiler maps every lookup failure to InvalidArgument (400);
        # the stable discriminator is the provider code, not the HTTP status.
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json()["error"]["providerCode"], "E_METRIC_NOT_FOUND")

    def test_15_period_window_insufficient(self) -> None:
        response = self._compute(
            "FIN-INS-013",
            periodStart="2025-12-01",
            periodEnd="2025-12-31",
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(
            response.json()["error"]["providerCode"], "E_METRIC_WINDOW_INSUFFICIENT"
        )

    # ------------------------------------------------------------ M-06 ledger
    def test_16_readiness_ledger(self) -> None:
        response = self.client.get("/metrics-readiness")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["count"], 20)
        self.assertEqual(body["counts"]["executed"], 16)
        self.assertEqual(body["counts"]["registered_only"], 1)
        self.assertEqual(body["counts"]["not_executable"], 3)
        by_id = {(item["itemKind"], item["metricId"]): item for item in body["items"]}
        self.assertEqual(by_id[("partial", "CUST-005")]["status"], "registered_only")
        self.assertEqual(by_id[("partial", "FIN-BANK-019")]["status"], "not_executable")
        self.assertEqual(by_id[("rule", "FIN-BANK-007")]["detail"]["ruleCount"], 4)

    def test_17_registered_only_export(self) -> None:
        response = self.client.get(
            "/metrics-readiness", params={"status": "registered_only", "format": "csv"}
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("text/csv", response.headers["content-type"])
        lines = [line for line in response.text.splitlines() if line]
        self.assertEqual(len(lines), 2)  # header + CUST-005 only
        self.assertTrue(lines[0].startswith("item_kind,metric_id,status"))
        self.assertIn("CUST-005", lines[1])
        self.assertIn("registered_only", lines[1])
        self.assertNotIn("executed", response.text)

    def test_18_readiness_invalid_status(self) -> None:
        response = self.client.get(
            "/metrics-readiness", params={"status": "partial"}
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(
            response.json()["error"]["providerCode"],
            "E_METRIC_READINESS_STATUS_INVALID",
        )

    def test_19_v34_reentrant(self) -> None:
        sql = files("platform_core").joinpath(
            "sql/V34__metrics_core_m01_m06.sql"
        ).read_text(encoding="utf-8")
        statements = split_sql_statements(sql)

        def snapshot() -> tuple:
            rows = self.meta.query(
                "SELECT item_kind, metric_id, status, reason, detail::text AS detail,"
                " evidence_ref, checked_at FROM platform.metric_readiness"
                " ORDER BY item_kind, metric_id"
            )
            bindings = self.meta.query(
                "SELECT metric_id, role, value_expr, filter_sql, window_column"
                " FROM platform.metric_field_binding"
                " WHERE metric_id IN ('FIN-BANK-013','FIN-BANK-014','FIN-BANK-015',"
                "'FIN-BANK-016','FIN-INS-018') ORDER BY metric_id, role"
            )
            return (tuple(tuple(sorted(r.items())) for r in rows),
                    tuple(tuple(sorted(r.items())) for r in bindings))

        before = snapshot()
        for _ in range(2):
            with self.meta.tx() as tx:
                for statement in statements:
                    tx.execute(statement, None)
        self.assertEqual(snapshot(), before)


if __name__ == "__main__":
    unittest.main()
