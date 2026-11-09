"""v3 metric guard: real registry queries for five representative metrics.

Run inside the platform container (after the API has migrated V18):
  python -m unittest /tmp/hosttests/test_metric_guard.py
or from the host with PYTHONPATH=<repo>/src and PLATFORM_CONFIG pointing at
the same platform.yaml.
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, "/app/src")

from platform_core.assembly import assemble
from platform_core.config import load_config
from platform_core.errors import PortError

CONFIG = os.environ.get("PLATFORM_CONFIG", "/data/platform.yaml")


class MetricGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = assemble(load_config(CONFIG, None))
        cls.runtime.metadata.open(retry_seconds=10.0)
        cls.runtime.metadata.migrate()
        cls.metrics = cls.runtime.metrics

    @classmethod
    def tearDownClass(cls) -> None:
        cls.runtime.close()

    def _rejected(self, metric_id: str, internal: bool = False) -> PortError:
        with self.assertRaises(PortError) as caught:
            self.metrics.output(metric_id, internal=internal)
        return caught.exception

    def test_bank020_is_released_without_regulatory_source(self) -> None:
        # v9 releases the v8 "no source" rows as internal industry baselines.
        card = self.metrics.output("FIN-BANK-020")
        self.assertEqual(card["source"], "INDUSTRY")
        self.assertTrue(card["inference"])
        self.assertEqual(card["evidenceBasis"], "industry")
        self.assertTrue(card["publishable"])

    def test_bank031_v5_industry_denominator_is_internal_only(self) -> None:
        # v9 moved the denominator to industry and released the metric as an
        # industry baseline; it is still marked inference and never regulatory.
        card = self.metrics.output("FIN-BANK-031")
        self.assertEqual(card["source"], "INDUSTRY")
        self.assertTrue(card["inference"])
        self.assertEqual(card["evidenceBasis"], "industry")
        self.assertTrue(card["publishable"])
        self.assertEqual(card["effectiveDate"], "2026-11-06")
        self.assertIsNone(card["variantOf"])
        self.assertIsNone(card["ruleSet"])

    def test_ins003_industry_output_is_marked(self) -> None:
        card = self.metrics.output("FIN-INS-003", internal=True)
        self.assertEqual(card["source"], "INDUSTRY")
        self.assertFalse(card["inference"])
        self.assertEqual(card["evidenceBasis"], "industry")
        self.assertEqual(card["evidenceStatus"], "EVIDENCE_MISSING")
        self.assertTrue(card["publishable"])

    def test_cust009_industry_output_is_marked(self) -> None:
        card = self.metrics.output("CUST-009", internal=True)
        self.assertEqual(card["source"], "INDUSTRY")
        self.assertFalse(card["inference"])
        self.assertEqual(card["evidenceBasis"], "industry")
        self.assertEqual(card["evidenceStatus"], "EVIDENCE_MISSING")
        self.assertTrue(card["publishable"])

    def test_bank001_regulatory_output_is_unchanged(self) -> None:
        card = self.metrics.output("FIN-BANK-001")
        self.assertEqual(card["source"], "REGULATORY")
        self.assertFalse(card["inference"])
        self.assertEqual(card["evidenceBasis"], "regulatory")
        self.assertTrue(card["publishable"])
        self.assertEqual(card["evidenceStatus"], "EVIDENCED")


if __name__ == "__main__":
    unittest.main()
