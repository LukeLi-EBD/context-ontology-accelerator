"""V23 scheme-A compiler: compile -> execute on fixtures -> hand-checked values.

Every asserted number is hand-computed below. Rows are written with
data_source=fixture and deleted in tearDownClass; the compiler never writes
metric_observation, so the baseline stays at 0 rows.
"""

from __future__ import annotations

import os
import sys
import unittest
from importlib.resources import files

sys.path.insert(0, "/app/src")

from platform_core.assembly import assemble
from platform_core.config import load_config
from platform_core.errors import PortError
from platform_core.metric_compiler import (
    BINDING_MISSING, EXPR_UNSUPPORTED, PUBLISH, RULE_SET_ONLY, MetricCompiler,
    formula_to_sql,
)
from platform_core.sqlsplit import split_sql_statements

CONFIG = os.environ.get("PLATFORM_CONFIG", "/data/platform.yaml")
TABLES = (
    "bank_loan_account", "ins_policy", "ins_claim_case", "ins_payment_record",
    "cust_transaction", "cust_product_holding",
)

AS_OF = "2025-12-31"
JAN = {"start": "2025-01-01", "end": "2025-01-31"}


class MetricCompilerV7Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = assemble(load_config(CONFIG, None))
        cls.runtime.metadata.open(retry_seconds=10.0)
        cls.runtime.metadata.migrate()
        cls.meta = cls.runtime.metadata
        cls.compiler = MetricCompiler(cls.meta)
        cls._load()

    @classmethod
    def tearDownClass(cls) -> None:
        with cls.meta.tx() as tx:
            for table in TABLES:
                tx.execute(f"DELETE FROM platform.{table} WHERE data_source = 'fixture'", None)
        cls.runtime.close()

    @classmethod
    def _load(cls) -> None:
        with cls.meta.tx() as tx:
            # bank loan accounts (FIN-BANK-008: NPL balance / total balance)
            for row in (
                ("A1", "C1", "I1", "normal", 1000),
                ("A2", "C2", "I1", "substandard", 200),
                ("A3", "C3", "I1", "doubtful", 100),
                ("A4", "C4", "I1", "loss", 50),
                ("A5", "C5", "I2", "normal", 500),
            ):
                tx.execute(
                    "INSERT INTO platform.bank_loan_account (account_id, customer_no, product,"
                    " risk_class, principal_balance, account_status, as_of, institution,"
                    " data_source, fixture) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (row[0], row[1], "mortgage", row[3], row[4], "active", AS_OF, row[2],
                     "fixture", True),
                )
            # insurance policies (FIN-INS-002/005/007 denominator)
            policies = (
                ("P1", "term_life", "regular", 1000, 1000, False, 0, "2025-01-10", "2025-01-31"),
                ("P2", "term_life", "regular", 2000, 2000, False, 100, "2025-01-20", "2025-01-31"),
                ("P3", "whole_life", "single", 5000, None, False, 0, "2025-01-15", "2025-01-31"),
                ("P4", "term_life", "regular", 3000, 3000, False, 0, "2025-02-05", "2025-01-31"),
                ("P5", "term_life", "regular", 1000, 1000, False, 0, "2025-01-10", "2025-02-28"),
            )
            for p in policies:
                tx.execute(
                    "INSERT INTO platform.ins_policy (policy_no, product, channel, institution,"
                    " customer_no, issue_date, policy_year, premium_type, premium_amount,"
                    " first_year_premium, is_investment_linked, reversal_amount, policy_status,"
                    " status_as_of, data_source, fixture)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (p[0], p[1], "personal", "I1", "C1", p[7], 1, p[2], p[3], p[4],
                     p[5], p[6], "in_force", p[8], "fixture", True),
                )
            # claims (FIN-INS-007 numerator, FIN-INS-015)
            claims = (
                ("C1", "P1", "term_life", "2025-01-05", "2025-01-15", 300, "paid"),
                ("C2", "P1", "term_life", "2025-01-10", "2025-01-25", 500, "paid"),
                ("C3", "P2", "term_life", "2025-01-12", "2025-01-20", 0, "rejected"),
                ("C4", "P3", "whole_life", "2025-01-20", "2025-01-30", 400, "paid"),
                ("C5", "P2", "term_life", "2024-12-10", "2024-12-30", 700, "paid"),
            )
            for c in claims:
                tx.execute(
                    "INSERT INTO platform.ins_claim_case (claim_no, policy_no, product,"
                    " institution, report_date, decision_date, claim_amount, paid_amount,"
                    " claim_status, data_source, fixture)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (c[0], c[1], c[2], "I1", c[3], c[4], c[5], c[5], c[6], "fixture", True),
                )
            # payment records (FIN-INS-004 renewal premium: current, policy_year>=2)
            pays = (
                ("P1", 1, "2025-01-05", 1000, "current", 1),
                ("P1", 2, "2025-01-05", 800, "current", 2),
                ("P2", 2, "2025-01-20", 900, "current", 2),
                ("P3", 1, "2025-01-10", 500, "single", 1),
                ("P2", 3, "2025-01-25", 400, "arrears", 3),
            )
            for p in pays:
                tx.execute(
                    "INSERT INTO platform.ins_payment_record (policy_no, product,"
                    " installment_no, due_date, due_amount, paid_amount, payment_status,"
                    " policy_status, status_as_of, institution, payment_type, policy_year,"
                    " data_source, fixture)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (p[0], "term_life" if p[0] != "P3" else "whole_life", p[1], p[2], p[3],
                     p[3], "paid", "in_force", "2025-01-31", "I1", p[4], p[5],
                     "fixture", True),
                )
            # customer transactions (CUST-003 RFM-M, refund excluded)
            txns = (
                ("T1", "M1", "2025-03-01", "purchase", 100),
                ("T2", "M1", "2025-06-01", "purchase", 200),
                ("T3", "M1", "2025-07-01", "refund", 50),
                ("T4", "M2", "2024-12-20", "purchase", 50),
                ("T5", "M2", "2025-02-01", "purchase", 60),
            )
            for t in txns:
                tx.execute(
                    "INSERT INTO platform.cust_transaction (txn_id, customer_no, txn_date,"
                    " txn_type, amount, product_category, channel, data_source, fixture)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (t[0], t[1], t[2], t[3], t[4], "retail", "app", "fixture", True),
                )
            # product holdings (CUST-009 active distinct categories)
            holds = (
                ("H1", "M1", "deposit", "active"),
                ("H2", "M1", "loan", "active"),
                ("H3", "M1", "wealth", "closed"),
                ("H4", "M1", "card", "active"),
                ("H5", "M2", "deposit", "active"),
            )
            for h in holds:
                tx.execute(
                    "INSERT INTO platform.cust_product_holding (holding_id, customer_no,"
                    " product_category, holding_status, as_of, institution, data_source, fixture)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (h[0], h[1], h[2], h[3], AS_OF, "I1", "fixture", True),
                )

    def _rows(self, metric_id: str, internal: bool = False, **window) -> dict[str, dict]:
        result = self.compiler.execute(metric_id, internal=internal, **window)
        return {str(r["entityKey"]): r for r in result["rows"]}

    # ---------------------------------------------------------------- values
    def test_01_npl_ratio(self) -> None:
        # I1: (200+100+50)/1350*100 = 25.9259259; I2: 0/500 = 0
        rows = self._rows("FIN-BANK-008", start=AS_OF, end=AS_OF)
        self.assertAlmostEqual(rows["I1"]["value"], 25.925926, places=5)
        self.assertEqual(rows["I2"]["numerator"], 0.0)

    def test_02_rfm_m(self) -> None:
        # M1: 100+200 (refund excluded) = 300; M2: only 2025-02-01 = 60
        rows = self._rows("CUST-003", internal=True, **YEAR_2025())
        self.assertEqual(rows["M1"]["value"], 300.0)
        self.assertEqual(rows["M2"]["value"], 60.0)

    def test_03_signed_premium(self) -> None:
        # Jan 31: term_life 1000 + (2000-100) = 2900; whole_life 5000
        rows = self._rows("FIN-INS-002", **JAN)
        self.assertEqual(rows["term_life"]["value"], 2900.0)
        self.assertEqual(rows["whole_life"]["value"], 5000.0)

    def test_04_first_year_premium(self) -> None:
        # term_life 1000 + 2000 = 3000; whole_life single = 5000
        rows = self._rows("FIN-INS-005", internal=True, **JAN)
        self.assertEqual(rows["term_life"]["value"], 3000.0)
        self.assertEqual(rows["whole_life"]["value"], 5000.0)

    def test_05_renewal_premium(self) -> None:
        # current & policy_year>=2: 800 + 900 = 1700 (inst1/1y, single and arrears excluded)
        rows = self._rows("FIN-INS-004", internal=True, **JAN)
        self.assertEqual(rows["term_life"]["value"], 1700.0)

    def test_06_simple_loss_ratio(self) -> None:
        # term_life 800/2900*100 = 27.586207; whole_life 400/5000*100 = 8.0
        rows = self._rows("FIN-INS-007", internal=True, **JAN)
        self.assertAlmostEqual(rows["term_life"]["value"], 27.586207, places=5)
        self.assertAlmostEqual(rows["whole_life"]["value"], 8.0, places=5)

    def test_07_average_settled_claim(self) -> None:
        # term_life (300+500)/2 = 400; whole_life 400/1 = 400
        rows = self._rows("FIN-INS-015", **JAN)
        self.assertEqual(rows["term_life"]["value"], 400.0)
        self.assertEqual(rows["whole_life"]["value"], 400.0)

    def test_08_product_holdings(self) -> None:
        # M1 active distinct {deposit,loan,card} = 3; M2 = 1
        rows = self._rows("CUST-009", internal=True, start=AS_OF, end=AS_OF)
        self.assertEqual(rows["M1"]["value"], 3.0)
        self.assertEqual(rows["M2"]["value"], 1.0)

    # ------------------------------------------------------------ gate/errors
    def test_09_external_gate(self) -> None:
        with self.assertRaises(PortError) as ctx:
            self.compiler.execute("CUST-001", start=AS_OF, end=AS_OF)
        self.assertEqual(ctx.exception.provider_code, PUBLISH)

    def test_10_rule_metric_routes_to_rules(self) -> None:
        with self.assertRaises(PortError) as ctx:
            self.compiler.execute("FIN-BANK-034", internal=True, start=AS_OF, end=AS_OF)
        self.assertEqual(ctx.exception.provider_code, RULE_SET_ONLY)

    def test_11_unsupported_expression(self) -> None:
        with self.assertRaises(PortError) as ctx:
            formula_to_sql("numerator ** denominator")
        self.assertEqual(ctx.exception.provider_code, EXPR_UNSUPPORTED)

    def test_12_missing_binding(self) -> None:
        with self.assertRaises(PortError) as ctx:
            self.compiler.compile("FIN-BANK-001", internal=True, start=AS_OF, end=AS_OF)
        self.assertEqual(ctx.exception.provider_code, BINDING_MISSING)

    def test_13_migrations_reentrant(self) -> None:
        # replay V23+V24+V25+V30+V41 twice: row count, definitions and binding
        # count must be identical. V30 closes the v9 chain; V41 re-applies the
        # post-v9 observation semantics so the snapshot stays at current state.
        def snapshot() -> tuple:
            rows = self.meta.query(
                "SELECT metric_id, metric_kind, formula_expr, window_kind, numerator_agg,"
                " denominator_agg, computability_tier, output_mode, decision_owner,"
                " quartet_derivation::text AS qd, decision_recommendation::text AS dr,"
                " rule_set_json::text AS rs"
                " FROM platform.metric_definition ORDER BY metric_id"
            )
            bindings = self.meta.query(
                "SELECT COUNT(*) AS n FROM platform.metric_field_binding"
            )
            return tuple(tuple(sorted(r.items())) for r in rows), bindings[0]["n"]

        sql = "".join(
            files("platform_core").joinpath(f"sql/{name}").read_text(encoding="utf-8")
            for name in ("V23__metric_quartet_v7.sql", "V24__metric_decisions_v8.sql",
                         "V25__fact_model_v7.sql", "V30__metric_decisions_v9.sql",
                         "V41__metric_semantics.sql")
        )
        statements = split_sql_statements(sql)
        before = snapshot()
        for _ in range(2):
            with self.meta.tx() as tx:
                for statement in statements:
                    tx.execute(statement, None)
        self.assertEqual(snapshot(), before)


def YEAR_2025() -> dict:
    return {"start": "2025-01-01", "end": "2025-12-31"}


if __name__ == "__main__":
    unittest.main()
