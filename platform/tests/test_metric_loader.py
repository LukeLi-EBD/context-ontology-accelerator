"""Metric fact loader contract: fixture-only files, no business data.

Six cases: whole-batch rollback on a bad row, idempotent re-import, window
contract rejection, unpublishable rejection, non-numeric rejection, and the
happy path with the dry-run default.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, "/app/src")

from platform_core.assembly import assemble
from platform_core.config import load_config
from platform_core.metric_loader import MetricLoader

CONFIG = os.environ.get("PLATFORM_CONFIG", "/data/platform.yaml")
FIX = Path(__file__).resolve().parent / "fixtures" / "metrics"

DPD = "FIN-BANK-001"
CONCENTRATION = "FIN-BANK-025"
CONTINUATION = "FIN-INS-021"
UNPUBLISHABLE = "FIN-INS-003"


class MetricLoaderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = assemble(load_config(CONFIG, None))
        cls.runtime.metadata.open(retry_seconds=10.0)
        cls.runtime.metadata.migrate()
        cls.meta = cls.runtime.metadata
        cls.loader = MetricLoader(cls.meta)
        cls._clean()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._clean()
        cls.runtime.close()

    @classmethod
    def _clean(cls) -> None:
        cls.meta.execute(
            "DELETE FROM platform.metric_observation WHERE entity_key LIKE %s",
            ("LOADER-TEST-%",),
        )

    def _load(self, file: str, mapping: str, metric: str, apply: bool = True,
              data_source: str = "fixture", fixture: bool = True):
        return self.loader.load(
            file=str(FIX / file),
            metric_id=metric,
            mapping_path=str(FIX / mapping),
            apply=apply,
            data_source=data_source,
            fixture=fixture,
        )

    def _count(self, metric: str) -> int:
        rows = self.meta.query(
            "SELECT COUNT(*) AS n FROM platform.metric_observation "
            "WHERE metric_id = %s AND definition_version = 'v3.0'",
            (metric,),
        )
        return int(rows[0]["n"])

    def _count_prefix(self, prefix: str) -> int:
        rows = self.meta.query(
            "SELECT COUNT(*) AS n FROM platform.metric_observation "
            "WHERE entity_key LIKE %s",
            (prefix + "%",),
        )
        return int(rows[0]["n"])

    def test_bad_row_rolls_back_entire_batch(self) -> None:
        before = self._count(DPD)
        result = self._load("load_dpd_bad_entity.csv", "load_dpd.yaml", DPD)
        self.assertFalse(result["ok"])
        self.assertEqual(result["errorCode"], "E_LOADER_BAD_ROWS")
        self.assertEqual(result["errorCount"], 1)
        self.assertEqual(result["errors"][0]["row"], 3)
        self.assertEqual(result["rowsAfter"], before)
        self.assertEqual(self._count(DPD), before)
        self.assertEqual(self._count_prefix("LOADER-TEST-B"), 0)

    def test_reimport_is_idempotent(self) -> None:
        before = self._count(DPD)
        first = self._load("load_dpd_ok.csv", "load_dpd.yaml", DPD)
        self.assertTrue(first["ok"], first)
        self.assertEqual(first["rowsBefore"], before)
        self.assertEqual(first["rowsAfter"], before + 3)
        second = self._load("load_dpd_ok.csv", "load_dpd.yaml", DPD)
        self.assertTrue(second["ok"], second)
        self.assertEqual(second["rowsBefore"], second["rowsAfter"])
        self.assertEqual(second["rowsUpserted"], 3)
        self.assertEqual(self._count(DPD), before + 3)
        self.assertEqual(self._count_prefix("LOADER-TEST-A"), 3)

    def test_window_out_of_contract_rejected(self) -> None:
        dpd_before = self._count(DPD)
        instant = self._load("load_dpd_bad_window.csv", "load_dpd_window.yaml", DPD)
        self.assertFalse(instant["ok"])
        self.assertEqual(instant["errorCode"], "E_LOADER_WINDOW_INVALID")
        self.assertTrue(all(item["code"] == "E_LOADER_WINDOW_INVALID"
                            for item in instant["errors"]))
        self.assertEqual(self._count(DPD), dpd_before)

        continuation_before = self._count(CONTINUATION)
        period = self._load(
            "load_insurance_period_short.csv", "load_insurance_period.yaml", CONTINUATION
        )
        self.assertFalse(period["ok"])
        self.assertEqual(period["errorCode"], "E_LOADER_WINDOW_INVALID")
        self.assertEqual(self._count(CONTINUATION), continuation_before)
        self.assertEqual(self._count_prefix("LOADER-TEST-Q"), 0)

    def test_unpublishable_metric_rejected(self) -> None:
        result = self._load(
            "load_insurance_unpublishable.csv", "load_insurance_unpublishable.yaml",
            UNPUBLISHABLE,
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["errorCode"], "E_METRIC_NOT_PUBLISHABLE")
        self.assertEqual(self._count_prefix("LOADER-TEST-U"), 0)

    def test_invalid_numeric_type_rejected(self) -> None:
        before = self._count(DPD)
        result = self._load("load_dpd_bad_numeric.csv", "load_dpd.yaml", DPD)
        self.assertFalse(result["ok"])
        self.assertEqual(result["errorCode"], "E_LOADER_BAD_ROWS")
        self.assertEqual(result["errors"][0]["row"], 4)
        self.assertEqual(result["errors"][0]["column"], "dpd_days")
        self.assertEqual(self._count(DPD), before)
        self.assertEqual(self._count_prefix("LOADER-TEST-E"), 0)

    def test_apply_success_with_dry_run_default(self) -> None:
        before = self._count(CONCENTRATION)
        dry = self._load("load_concentration_ok.csv", "load_concentration.yaml",
                         CONCENTRATION, apply=False)
        self.assertTrue(dry["ok"], dry)
        self.assertTrue(dry["dryRun"])
        self.assertEqual(dry["rowsValid"], 2)
        self.assertEqual(dry["rowsAfter"], before)
        self.assertEqual(self._count(CONCENTRATION), before)

        applied = self._load("load_concentration_ok.csv", "load_concentration.yaml",
                             CONCENTRATION, apply=True)
        self.assertTrue(applied["ok"], applied)
        self.assertFalse(applied["dryRun"])
        self.assertEqual(applied["rowsBefore"], before)
        self.assertEqual(applied["rowsAfter"], before + 2)
        self.assertEqual(applied["dataSource"], "fixture")
        self.assertTrue(applied["fixture"])

        rows = self.meta.query(
            "SELECT numerator, denominator, institution, data_source, fixture "
            "FROM platform.metric_observation WHERE entity_key = 'LOADER-TEST-C1'"
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["institution"], "示例银行")
        self.assertEqual(rows[0]["data_source"], "fixture")
        self.assertTrue(rows[0]["fixture"])


if __name__ == "__main__":
    unittest.main()
