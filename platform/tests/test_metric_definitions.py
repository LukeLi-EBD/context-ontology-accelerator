"""V21 metric-definition v5 verdict: schema, seed, variants, rule set.

The v5 verdict (``_fsldm/10-口径判定-三项open.md``) splits three metric
families into an index row plus executable variants, turns FIN-BANK-034 into
a 10-rule early-warning rule set, and fixes the denominators of four
no-source bank metrics. All of it is seed-level: no fact table and no rule
executor is added, so the number of computable metrics stays unchanged.

Run inside the platform container (same as the other DB-backed suites):
  python -m unittest /hosttests/test_metric_definitions.py
"""

from __future__ import annotations

import os
import sys
import unittest
from importlib.resources import files
from types import SimpleNamespace

sys.path.insert(0, "/app/src")

from fastapi.testclient import TestClient

import platform_core.api as api_module
from platform_core.adapters.metadata_pg import SUPPORTED_SCHEMA_VERSION
from platform_core.assembly import assemble
from platform_core.config import load_config
from platform_core.errors import PortError
from platform_core.sqlsplit import split_sql_statements

CONFIG = os.environ.get("PLATFORM_CONFIG", "/data/platform.yaml")
SQL_NAME = "V21__metric_definition_v5.sql"

FAMILY_IDS = ("FIN-INS-022", "FIN-INS-023", "FIN-BANK-036")
VARIANT_IDS = (
    "FIN-INS-022-v1", "FIN-INS-022-v2",
    "FIN-INS-023-v1", "FIN-INS-023-v2",
    "FIN-BANK-036-v1", "FIN-BANK-036-v2",
)
EXPECTED_VARIANTS = {
    "FIN-INS-022": ["FIN-INS-022-v1", "FIN-INS-022-v2"],
    "FIN-INS-023": ["FIN-INS-023-v1", "FIN-INS-023-v2"],
    "FIN-BANK-036": ["FIN-BANK-036-v1", "FIN-BANK-036-v2"],
}
SEEDED_IDS = FAMILY_IDS + VARIANT_IDS + (
    "FIN-BANK-031", "FIN-BANK-032", "FIN-BANK-034", "FIN-BANK-035",
)

# Every column that existed before V21: re-applying V21 must not drift any of
# them (the 13 seeded rows are deterministic upserts, the other rows untouched).
SNAPSHOT_COLUMNS = (
    "metric_id, name_zh, domain, evidence_basis, publishable, inference, "
    "formula_disabled, missing, evidence_status, note, "
    "definition_version, metric_kind, formula_expr, numerator_agg, "
    "denominator_agg, window_kind, min_window_days, grain, unit, fact_function, "
    "display_name, definition, formula_text, denominator_text, "
    "observation_period, granularity, provenance_label, effective_date, "
    "variant_of, output_mode, rule_set_json"
)


def _normalized(row: dict) -> tuple:
    values = []
    for column in [c.strip() for c in SNAPSHOT_COLUMNS.split(",")]:
        value = row[column]
        if isinstance(value, list):
            value = repr(value)
        values.append(value)
    return tuple(values)


class MetricDefinitionV5Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = assemble(load_config(CONFIG, None))
        cls.runtime.metadata.open(retry_seconds=10.0)
        cls.runtime.metadata.migrate()
        cls.meta = cls.runtime.metadata
        cls.metrics = cls.runtime.metrics
        cls.sql = files("platform_core").joinpath(f"sql/{SQL_NAME}").read_text(
            encoding="utf-8"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.runtime.close()

    # ---- helpers -------------------------------------------------------

    def _apply_v21(self, times: int = 1) -> None:
        statements = split_sql_statements(self.sql)
        for _ in range(times):
            with self.meta.tx() as tx:
                for statement in statements:
                    # params=None: the seed text contains literal '%' units
                    tx.execute(statement, None)

    def _count(self, where: str = "", params: tuple = ()) -> int:
        rows = self.meta.query(
            "SELECT COUNT(*) AS n FROM platform.metric_definition "
            "WHERE metric_id NOT LIKE %s" + where,
            ("TEST-%",) + params,
        )
        return int(rows[0]["n"])

    def _snapshot(self) -> dict[str, tuple]:
        rows = self.meta.query(
            f"SELECT {SNAPSHOT_COLUMNS} FROM platform.metric_definition "
            "WHERE metric_id NOT LIKE %s",
            ("TEST-%",),
        )
        return {row["metric_id"]: _normalized(row) for row in rows}

    def _row(self, metric_id: str) -> dict:
        rows = self.meta.query(
            f"SELECT {SNAPSHOT_COLUMNS} FROM platform.metric_definition "
            "WHERE metric_id = %s",
            (metric_id,),
        )
        self.assertTrue(rows, metric_id)
        return rows[0]

    # ---- 1. schema -----------------------------------------------------

    def test_1_schema_version_and_new_columns(self) -> None:
        self.assertEqual(SUPPORTED_SCHEMA_VERSION, 21)
        rows = self.meta.query(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = 'platform' AND table_name = 'metric_definition'"
        )
        types = {row["column_name"]: row["data_type"] for row in rows}
        self.assertEqual(types["effective_date"], "date")
        self.assertEqual(types["variant_of"], "text")
        self.assertEqual(types["output_mode"], "text")
        self.assertEqual(types["rule_set_json"], "jsonb")
        version = self.meta.query(
            "SELECT MAX(version) AS v FROM platform.schema_version"
        )
        self.assertEqual(int(version[0]["v"]), 21)

    # ---- 2. idempotency -------------------------------------------------

    def test_2_seed_is_idempotent_and_lands_85_rows(self) -> None:
        before = self._count()
        self.assertEqual(before, 85)
        self._apply_v21(times=2)
        self.assertEqual(self._count(), 85)
        self.assertEqual(self._count(" AND variant_of IS NOT NULL"), 6)
        self.assertEqual(self._count(" AND variant_of IS NULL"), 79)
        disabled = self.meta.query(
            "SELECT metric_id FROM platform.metric_definition "
            "WHERE formula_disabled = true AND metric_id NOT LIKE %s "
            "ORDER BY metric_id",
            ("TEST-%",),
        )
        self.assertEqual(
            [row["metric_id"] for row in disabled], sorted(FAMILY_IDS)
        )

    # ---- 3. family index rejection -------------------------------------

    def test_3_family_index_requires_a_variant(self) -> None:
        for metric_id in FAMILY_IDS:
            card = self.metrics.get(metric_id)
            self.assertTrue(card["formulaDisabled"], metric_id)
            self.assertEqual(card["outputMode"], "index", metric_id)
            self.assertIsNone(card["variantOf"], metric_id)

            with self.assertRaises(PortError) as caught:
                self.metrics.output(metric_id, internal=True)
            exc = caught.exception
            self.assertEqual(exc.code, "InvalidArgument", metric_id)
            self.assertEqual(exc.provider_code, "E_METRIC_VARIANT_REQUIRED", metric_id)
            self.assertNotEqual(exc.provider_code, "E_METRIC_FORMULA_DISABLED", metric_id)
            self.assertEqual(exc.details["variants"], EXPECTED_VARIANTS[metric_id], metric_id)
            self.assertIn("specify a variant", exc.message, metric_id)

            with self.assertRaises(PortError) as computed:
                self.metrics.compute(metric_id, internal=True)
            self.assertEqual(
                computed.exception.provider_code,
                "E_METRIC_VARIANT_REQUIRED",
                metric_id,
            )

    # ---- 4. variants are readable --------------------------------------

    def test_4_variants_read_definition_cards(self) -> None:
        for metric_id in VARIANT_IDS:
            family = metric_id.rsplit("-v", 1)[0]
            card = self.metrics.output(metric_id, internal=True)
            self.assertFalse(card["formulaDisabled"], metric_id)
            self.assertEqual(card["variantOf"], family, metric_id)
            self.assertEqual(card["outputMode"], "value", metric_id)
            self.assertEqual(card["effectiveDate"], "2026-11-06", metric_id)
            self.assertFalse(card["publishable"], metric_id)
            self.assertTrue(card["inference"], metric_id)
            self.assertEqual(card["evidenceBasis"], "industry", metric_id)
            self.assertEqual(card["source"], "INDUSTRY", metric_id)
            self.assertEqual(card["outputType"], "definition", metric_id)
            # the stored verdict text is present, not just the legacy card
            self.assertTrue(self._row(metric_id)["definition"], metric_id)
            self.assertTrue(self._row(metric_id)["formula_text"], metric_id)
            self.assertTrue(self._row(metric_id)["denominator_text"], metric_id)

            with self.assertRaises(PortError) as caught:
                self.metrics.output(metric_id)
            self.assertEqual(
                caught.exception.provider_code,
                "E_METRIC_NOT_PUBLISHABLE",
                metric_id,
            )

        for family, expected in EXPECTED_VARIANTS.items():
            self.assertEqual(self.metrics.variants(family), expected, family)

    # ---- 5. FIN-BANK-034 rule set --------------------------------------

    def test_5_bank034_returns_rule_set_not_a_value(self) -> None:
        card = self.metrics.output("FIN-BANK-034", internal=True)
        self.assertEqual(card["outputMode"], "rule_set")
        self.assertEqual(card["outputType"], "rule_set")
        self.assertFalse(card["publishable"])
        self.assertEqual(card["evidenceBasis"], "industry")
        rules = card["ruleSet"]
        self.assertIsInstance(rules, list)
        self.assertEqual(len(rules), 10)
        self.assertEqual([rule["id"] for rule in rules], [f"R{i:02d}" for i in range(1, 11)])
        for rule in rules:
            self.assertIn("threshold", rule)
            self.assertIn("level", rule)
            self.assertIn("trigger_fields", rule)
        self.assertNotIn("value", card)

        with self.assertRaises(PortError) as caught:
            self.metrics.compute("FIN-BANK-034", internal=True)
        self.assertEqual(
            caught.exception.provider_code, "E_METRIC_NOT_DRIVABLE"
        )

    def test_6_no_definition_field_drift_on_reapply(self) -> None:
        before = self._snapshot()
        self.assertEqual(len(before), 85)
        self._apply_v21(times=2)
        after = self._snapshot()
        self.assertEqual(after, before)

        for metric_id in SEEDED_IDS:
            self.assertIn(metric_id, before)
        rows = self.meta.query(
            "SELECT metric_id FROM platform.metric_definition WHERE variant_of IS NOT NULL "
            "AND metric_id NOT LIKE %s ORDER BY metric_id",
            ("TEST-%",),
        )
        self.assertEqual([row["metric_id"] for row in rows], sorted(VARIANT_IDS))

    def test_7_browse_list_distinguishes_variants(self) -> None:
        runtime = SimpleNamespace(
            metadata=self.meta, graph=None, ontology=None, metrics=self.metrics
        )
        with TestClient(api_module.create_app(runtime, [])) as client:
            items = client.get("/browse/metrics").json()["items"]
        by_id = {item["metricId"]: item for item in items}
        self.assertEqual(len([item for item in items if item["variantOf"]]), 6)
        for metric_id in FAMILY_IDS:
            self.assertEqual(by_id[metric_id]["outputMode"], "index", metric_id)
            self.assertIsNone(by_id[metric_id]["variantOf"], metric_id)
        for metric_id in VARIANT_IDS:
            self.assertIsNotNone(by_id[metric_id]["variantOf"], metric_id)
            self.assertEqual(by_id[metric_id]["outputMode"], "value", metric_id)
        detail = client.get("/browse/metrics/FIN-BANK-034").json()["metric"]
        self.assertEqual(detail["outputMode"], "rule_set")
        self.assertEqual(len(detail["ruleSet"]), 10)
        self.assertEqual([rule["id"] for rule in detail["ruleSet"]][0], "R01")


if __name__ == "__main__":
    unittest.main(verbosity=2)
