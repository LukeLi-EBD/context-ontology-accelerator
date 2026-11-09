"""v9 final-ruling seed (V30): row counts, release flags, and replay idempotency.

Runs inside the platform image against the real database:
  * 27 seeded rows carry decision_owner / decision_date / ruling
  * publishable rises to 60 and formula_disabled stays 3
  * FIN-BANK-034 stays refused, FIN-BANK-036 stays a disabled family index
  * replaying V30 twice leaves a byte-identical full-row snapshot
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
from platform_core.sqlsplit import split_sql_statements

CONFIG = os.environ.get("PLATFORM_CONFIG", "/data/platform.yaml")
SEED_IDS = (
    "FIN-BANK-002", "FIN-BANK-005", "FIN-BANK-017", "FIN-BANK-018", "FIN-BANK-019",
    "FIN-BANK-033", "FIN-BANK-034", "FIN-BANK-006", "FIN-BANK-020", "FIN-BANK-021",
    "FIN-BANK-031", "FIN-BANK-032", "FIN-BANK-035", "FIN-BANK-036-v1",
    "FIN-INS-003", "FIN-INS-006", "FIN-INS-007", "FIN-INS-017", "FIN-INS-022-v1",
    "FIN-INS-023-v1", "FIN-INS-024", "FIN-INS-026", "CUST-005", "CUST-009",
    "CUST-010", "FIN-INS-012", "FIN-BANK-036",
)


class MetricV9SeedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = assemble(load_config(CONFIG, None))
        cls.runtime.metadata.open(retry_seconds=15.0)
        cls.runtime.metadata.migrate()
        cls.meta = cls.runtime.metadata
        cls.sql = files("platform_core").joinpath("sql/V30__metric_decisions_v9.sql").read_text(
            encoding="utf-8"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.runtime.close()

    def _row(self, metric_id: str) -> dict:
        rows = self.meta.query(
            "SELECT * FROM platform.metric_definition WHERE metric_id = %s", (metric_id,)
        )
        self.assertTrue(rows, metric_id)
        return rows[0]

    def _snapshot(self) -> dict:
        rows = self.meta.query("SELECT * FROM platform.metric_definition ORDER BY metric_id")
        return {
            r["metric_id"]: {
                k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in r.items()
            }
            for r in rows
        }

    def test_seed_rows_are_finalized(self) -> None:
        for metric_id in SEED_IDS:
            row = self._row(metric_id)
            self.assertEqual(row["decision_owner"], "平台专家组", metric_id)
            self.assertIsNotNone(row["decision_date"], metric_id)
            self.assertTrue(row["ruling"], metric_id)

    def test_publishable_and_disabled_counts(self) -> None:
        row = self.meta.query(
            "SELECT count(*) AS total, count(*) FILTER (WHERE publishable) AS pub, "
            "count(*) FILTER (WHERE formula_disabled) AS fd, "
            "count(*) FILTER (WHERE variant_of IS NOT NULL) AS var "
            "FROM platform.metric_definition"
        )[0]
        self.assertEqual(int(row["total"]), 85)
        self.assertEqual(int(row["pub"]), 60)
        self.assertEqual(int(row["fd"]), 3)
        self.assertEqual(int(row["var"]), 6)

    def test_release_guards_still_hold(self) -> None:
        self.assertFalse(self._row("FIN-BANK-034")["publishable"])
        family = self._row("FIN-BANK-036")
        self.assertFalse(family["publishable"])
        self.assertTrue(family["formula_disabled"])
        variant = self._row("FIN-BANK-036-v1")
        self.assertTrue(variant["publishable"])
        self.assertEqual(variant["variant_of"], "FIN-BANK-036")

        with self.assertRaises(PortError) as refused:
            self.runtime.metrics.output("FIN-BANK-034")
        self.assertEqual(refused.exception.provider_code, "E_METRIC_NOT_PUBLISHABLE")
        with self.assertRaises(PortError) as family_call:
            self.runtime.metrics.output("FIN-BANK-036")
        self.assertEqual(family_call.exception.provider_code, "E_METRIC_VARIANT_REQUIRED")
        released = self.runtime.metrics.output("FIN-BANK-002")
        self.assertTrue(released["publishable"])

    def test_replay_is_idempotent(self) -> None:
        before = self._snapshot()
        for _ in range(2):
            with self.meta.tx() as tx:
                for statement in split_sql_statements(self.sql):
                    tx._conn.execute(statement)
        after = self._snapshot()
        self.assertEqual(len(before), 85)
        self.assertEqual(len(after), 85)
        drift = [mid for mid in before if before[mid] != after.get(mid)]
        self.assertEqual(drift, [])


if __name__ == "__main__":
    unittest.main()
