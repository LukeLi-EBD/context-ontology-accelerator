"""Definition-driven calculator: fixture-only computability checks.

No business value is asserted; every observation is marked fixture=true.
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, "/app/src")

from platform_core.assembly import assemble
from platform_core.config import load_config
from platform_core.errors import PortError

CONFIG = os.environ.get("PLATFORM_CONFIG", "/data/platform.yaml")
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "metrics" / "observations.json"

FIXTURE_IDS = ("FIN-BANK-001", "FIN-BANK-025", "FIN-BANK-030", "FIN-INS-021")
TEST_IDS = ("TEST-METRIC-MISSING", "TEST-METRIC-ND")


class MetricComputeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = assemble(load_config(CONFIG, None))
        cls.runtime.metadata.open(retry_seconds=10.0)
        cls.runtime.metadata.migrate()
        cls.meta = cls.runtime.metadata
        cls.metrics = cls.runtime.metrics
        cls._seed()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.meta.execute(
            "DELETE FROM platform.metric_observation WHERE fixture = true AND metric_id = ANY(%s)",
            (list(FIXTURE_IDS),),
        )
        cls.meta.execute(
            "DELETE FROM platform.metric_definition WHERE metric_id = ANY(%s)",
            (list(TEST_IDS),),
        )
        cls.runtime.close()

    @classmethod
    def _seed(cls) -> None:
        rows = json.loads(FIXTURES.read_text(encoding="utf-8"))
        for row in rows:
            cls.meta.execute(
                """
                INSERT INTO platform.metric_observation
                  (metric_id, definition_version, institution, product, entity_key,
                   as_of, period_start, period_end, numerator, denominator,
                   window_start, window_end, data_source, fixture)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT ON CONSTRAINT metric_observation_window_key DO NOTHING
                """,
                (
                    row["metricId"], row["definitionVersion"], row.get("institution"),
                    row.get("product"), row["entityKey"], row.get("asOf"),
                    row.get("periodStart"), row.get("periodEnd"), row["numerator"],
                    row.get("denominator"), row["windowStart"], row["windowEnd"],
                    row["dataSource"], row["fixture"],
                ),
            )
        cls.meta.execute(
            """
            INSERT INTO platform.metric_definition
              (metric_id, name_zh, domain, evidence_basis, publishable, inference,
               formula_disabled, missing, evidence_status, note, metric_kind,
               formula_expr, numerator_agg, denominator_agg, window_kind,
               min_window_days, grain, unit)
            VALUES ('TEST-METRIC-MISSING', '测试缺分母', 'bank', 'regulatory', true,
                    false, false, NULL, 'EVIDENCED', 'test-only', 'ratio',
                    'numerator / denominator', 'sum', NULL, 'instant', 0, 'customer', '%%')
            ON CONFLICT (metric_id) DO UPDATE SET
              metric_kind = EXCLUDED.metric_kind, formula_expr = EXCLUDED.formula_expr,
              numerator_agg = EXCLUDED.numerator_agg, denominator_agg = EXCLUDED.denominator_agg,
              window_kind = EXCLUDED.window_kind, min_window_days = EXCLUDED.min_window_days,
              grain = EXCLUDED.grain, unit = EXCLUDED.unit
            """
        )
        cls.meta.execute(
            """
            INSERT INTO platform.metric_definition
              (metric_id, name_zh, domain, evidence_basis, publishable, inference,
               formula_disabled, missing, evidence_status, note, metric_kind,
               formula_expr, numerator_agg, denominator_agg, window_kind,
               min_window_days, grain, unit)
            VALUES ('TEST-METRIC-ND', '测试不可驱动', 'bank', 'regulatory', true,
                    false, false, NULL, 'EVIDENCED', 'test-only', 'ratio',
                    'sqrt(numerator)', 'sum', 'sum', 'instant', 0, 'customer', '%%')
            ON CONFLICT (metric_id) DO UPDATE SET
              metric_kind = EXCLUDED.metric_kind, formula_expr = EXCLUDED.formula_expr,
              numerator_agg = EXCLUDED.numerator_agg, denominator_agg = EXCLUDED.denominator_agg,
              window_kind = EXCLUDED.window_kind, min_window_days = EXCLUDED.min_window_days,
              grain = EXCLUDED.grain, unit = EXCLUDED.unit
            """
        )

    def _code(self, call, **kwargs) -> PortError:
        with self.assertRaises(PortError) as caught:
            call(**kwargs)
        return caught.exception

    def test_denominator_zero(self) -> None:
        exc = self._code(
            self.metrics.compute, metric_id="FIN-BANK-025",
            as_of=date(2025, 12, 31), entity_key="ZERO",
        )
        self.assertEqual(exc.provider_code, "E_METRIC_DENOM_ZERO")

    def test_window_insufficient(self) -> None:
        exc = self._code(
            self.metrics.compute, metric_id="FIN-INS-021",
            period_start=date(2025, 12, 1), period_end=date(2025, 12, 31),
        )
        self.assertEqual(exc.provider_code, "E_METRIC_WINDOW_INSUFFICIENT")

    def test_not_publishable(self) -> None:
        exc = self._code(
            self.metrics.compute, metric_id="FIN-INS-003", as_of=date(2025, 12, 31),
        )
        self.assertEqual(exc.provider_code, "E_METRIC_NOT_PUBLISHABLE")

    def test_evidence_missing(self) -> None:
        exc = self._code(
            self.metrics.compute, metric_id="TEST-METRIC-MISSING", as_of=date(2025, 12, 31),
        )
        self.assertEqual(exc.provider_code, "E_METRIC_EVIDENCE_MISSING")

    def test_not_drivable(self) -> None:
        exc = self._code(
            self.metrics.compute, metric_id="TEST-METRIC-ND", as_of=date(2025, 12, 31),
        )
        self.assertEqual(exc.provider_code, "E_METRIC_NOT_DRIVABLE")

    def test_four_drivable_metrics_return_fixture_values(self) -> None:
        cases = {
            "FIN-BANK-001": dict(as_of=date(2025, 12, 31)),
            "FIN-BANK-025": dict(as_of=date(2025, 12, 31)),
            "FIN-BANK-030": dict(as_of=date(2025, 12, 31)),
            "FIN-INS-021": dict(period_start=date(2025, 1, 1), period_end=date(2025, 12, 31)),
        }
        for metric_id, kwargs in cases.items():
            card = self.metrics.compute(metric_id, **kwargs)
            self.assertIsNotNone(card["value"], metric_id)
            self.assertEqual(card["dataSource"], "fixture", metric_id)
            self.assertTrue(card["fixture"], metric_id)
            self.assertEqual(card["definitionVersion"], "v3.0", metric_id)
            self.assertTrue(card["formula"], metric_id)
            self.assertIn(card["window"]["kind"], ("instant", "period"), metric_id)
            self.assertEqual(card["evidenceBasis"], "regulatory", metric_id)


if __name__ == "__main__":
    unittest.main()
