"""Synthetic data generator: scale, self-consistency, isolation and reproducibility.

The suite runs inside the platform container (``PYTHONPATH=/app/src``) against
the test database. It writes only fact tables with ``data_source='synthetic'``
and asserts that the metric/T-Box tables never change.

Environment switch: ``datagen.allow_official_schema`` must be true for the
platform target, which is exactly what the CLI passes; here the flag is passed
explicitly so the suite also works when the YAML default is false.
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, "/app/src")

from platform_core.assembly import assemble
from platform_core.config import load_config
from platform_core.datagen import (
    SyntheticFactory,
    _insert_rows,
    clean_only,
    database_digest,
    ensure_target,
    generate,
    introspect,
    run_datagen,
    validate_all,
    verify_metrics,
)
from platform_core.errors import PortError

CONFIG = os.environ.get("PLATFORM_CONFIG", "/data/platform.yaml")
SCHEMA = "platform"
SEED = 42
ROWS = 1000
PROTECTED_SQL = (
    ("metric_observation", "SELECT count(*) AS n FROM platform.metric_observation"),
    (
        "metric_observation_synthetic",
        "SELECT count(*) AS n FROM platform.metric_observation WHERE data_source = 'synthetic'",
    ),
    ("metric_definition", "SELECT count(*) AS n FROM platform.metric_definition"),
    ("metric_field_binding", "SELECT count(*) AS n FROM platform.metric_field_binding"),
    ("ontology_version", "SELECT count(*) AS n FROM platform.ontology_version"),
    ("fact_assertion", "SELECT count(*) AS n FROM platform.fact_assertion"),
)


class DatagenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = assemble(load_config(CONFIG, None))
        cls.runtime.metadata.open(retry_seconds=10.0)
        cls.meta = cls.runtime.metadata
        cls.meta.migrate()
        cls.snapshot = cls._protected_counts()
        cls.info = introspect(cls.meta, SCHEMA)
        run_datagen(
            cls.meta,
            seed=SEED,
            scale=1.0,
            target_schema=SCHEMA,
            allow_official=True,
            rows_per_table=ROWS,
            clean=True,
            check_repro=False,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.runtime.close()

    @classmethod
    def _protected_counts(cls) -> dict[str, int]:
        return {name: int(cls.meta.query(sql)[0]["n"]) for name, sql in PROTECTED_SQL}

    # -- generator -----------------------------------------------------------
    def test_a_generation_scale_and_consistency(self) -> None:
        checks = validate_all(self.meta, SCHEMA, rows_per_table=ROWS)
        self.assertEqual(checks["scope"]["tables"], 28)
        self.assertGreaterEqual(checks["coverage"]["minFactRows"], ROWS)
        self.assertGreaterEqual(checks["coverage"]["tables"]["cust_master"], 5000)
        self.assertGreaterEqual(checks["coverage"]["tables"]["ins_policy"], 5000)
        self.assertGreaterEqual(checks["coverage"]["tables"]["bank_loan_account"], 5000)
        self.assertTrue(checks["fk"]["ok"], checks["fk"])
        self.assertEqual(checks["fk"]["orphans"], 0)
        self.assertTrue(checks["time"]["ok"], checks["time"])
        self.assertEqual(checks["time"]["violations"], 0)
        self.assertTrue(checks["money"]["ok"], checks["money"])
        self.assertEqual(checks["money"]["violations"], 0)
        self.assertTrue(checks["coverageOk"], checks["missingCases"])
        self.assertGreater(len(checks["coverage"]["matrix"]), 40)

    def test_b_schema_drift_is_loud(self) -> None:
        factory_rows = list(SyntheticFactory(SEED)._t_cust_master())
        row = dict(factory_rows[0])
        del row["customer_no"]
        with self.assertRaises(PortError) as ctx:
            _insert_rows(self.meta, self.info["cust_master"], [row])
        self.assertEqual(ctx.exception.provider_code, "E_DATAGEN_SCHEMA_DRIFT")

    def test_c_official_schema_requires_switch(self) -> None:
        with self.assertRaises(PortError) as ctx:
            ensure_target(self.meta, SCHEMA, allow_official=False)
        self.assertEqual(ctx.exception.provider_code, "E_DATAGEN_TARGET_FORBIDDEN")

    # -- validator + 30-metric e2e ------------------------------------------
    def test_d_metrics_three_categories(self) -> None:
        out = verify_metrics(self.meta)
        self.assertEqual(out["total"], 30)
        self.assertGreaterEqual(out["counts"]["success"], 5, out["counts"])
        self.assertGreaterEqual(out["counts"]["refusal"], 5, out["counts"])
        self.assertGreaterEqual(out["counts"]["exception"], 5, out["counts"])
        self.assertTrue(all(h["match"] for h in out["handChecks"]), out["handChecks"])
        self.assertGreaterEqual(len(out["handChecks"]), 10)

    def test_e_isolation_protected_tables_unchanged(self) -> None:
        after = self._protected_counts()
        # T-Box versions are shared with other tracks running tests in the same
        # database, so only metric/evidence tables are asserted as byte-stable;
        # the ontology ledger must never shrink.
        for name in ("metric_observation", "metric_observation_synthetic",
                     "metric_definition", "metric_field_binding", "fact_assertion"):
            self.assertEqual(after[name], self.snapshot[name], name)
        self.assertGreaterEqual(after["ontology_version"], self.snapshot["ontology_version"])

    def test_f_same_seed_is_byte_identical(self) -> None:
        info = introspect(self.meta, SCHEMA)
        first = database_digest(self.meta, SCHEMA, info)
        generate(
            self.meta,
            seed=SEED,
            scale=1.0,
            target_schema=SCHEMA,
            allow_official=True,
            rows_per_table=ROWS,
            clean=True,
        )
        second = database_digest(self.meta, SCHEMA, info)
        self.assertEqual(first, second)

    def test_g_clean_removes_only_synthetic(self) -> None:
        before = {name: int(self.meta.query(f"SELECT count(*) AS n FROM {SCHEMA}.{name}")[0]["n"]) for name in self.info}
        synthetic = {name: int(self.meta.query(f"SELECT count(*) AS n FROM {SCHEMA}.{name} WHERE data_source = 'synthetic'")[0]["n"]) for name in self.info}
        result = clean_only(self.meta, target_schema=SCHEMA, allow_official=True)
        for name in self.info:
            self.assertEqual(result["deleted"][name], synthetic[name])
            self.assertEqual(result["after"][name], before[name] - synthetic[name])
            self.assertEqual(result["syntheticAfter"][name], 0)
        # Leave the test environment populated for the next suites/tracks.
        generate(
            self.meta,
            seed=SEED,
            scale=1.0,
            target_schema=SCHEMA,
            allow_official=True,
            rows_per_table=ROWS,
            clean=False,
        )


if __name__ == "__main__":
    unittest.main()
