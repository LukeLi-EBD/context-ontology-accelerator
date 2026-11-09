"""B-01 value-level provenance: ref format, live resolution, stability, negatives.

Covers the three source kinds and the two failure modes that matter:
a ref to a row that never existed -> E_SOURCE_REF_NOT_FOUND, and a ref that was
issued but whose row was later removed -> E_SOURCE_REF_STALE. Fixture rows are
created under TEST-SRC-001 and removed in tearDown.
"""

from __future__ import annotations

import os
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, "/app/src")

from platform_core import source_ref
from platform_core.assembly import assemble
from platform_core.config import load_config
from platform_core.errors import PortError

CONFIG = os.environ.get("PLATFORM_CONFIG", "/data/platform.yaml")
METRIC = "TEST-SRC-001"


class SourceRefUnitTest(unittest.TestCase):
    def _code(self, call, *args, **kwargs) -> PortError:
        with self.assertRaises(PortError) as caught:
            call(*args, **kwargs)
        return caught.exception

    def test_ref_shapes(self) -> None:
        obs = source_ref.observation_ref(METRIC, "v1", "E 1", "2025-01-01", "2025-12-31")
        parsed = source_ref.parse_ref(obs)
        self.assertEqual(parsed["kind"], "obs")
        self.assertEqual(parsed["metricId"], METRIC)
        self.assertEqual(parsed["locator"]["entityKey"], "E 1")
        fact = source_ref.fact_row_ref(
            "platform.bank_loan_account",
            {"account_id": "LN-1", "as_of": "2025-12-31", "data_source": "synthetic"},
        )
        self.assertEqual(source_ref.parse_ref(fact)["table"], "platform.bank_loan_account")
        chunk = source_ref.chunk_ref("0123456789abcdef", 7)
        self.assertEqual(source_ref.parse_ref(chunk)["chunkNo"], 7)
        self.assertEqual(source_ref.chunk_no_from_id("0123:0007"), 7)
        obs_set = source_ref.observation_set_ref(
            METRIC, "v1", as_of="2025-12-31", fixture=True,
        )
        self.assertIn("fixture=true", obs_set)
        self.assertTrue(source_ref.parse_ref(obs_set)["locator"]["fixture"])

    def test_malformed_and_unsupported(self) -> None:
        exc = self._code(source_ref.parse_ref, "http://example.com/x")
        self.assertEqual(exc.provider_code, source_ref.MALFORMED)
        exc = self._code(source_ref.parse_ref, "src://unknown/x")
        self.assertEqual(exc.provider_code, source_ref.TYPE_UNSUPPORTED)


class SourceRefDatabaseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = assemble(load_config(CONFIG, None))
        cls.runtime.metadata.open(retry_seconds=15.0)
        cls.runtime.metadata.migrate()
        cls.meta = cls.runtime.metadata
        cls._seed()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.meta.execute(
            "DELETE FROM platform.metric_observation WHERE metric_id = %s", (METRIC,)
        )
        cls.meta.execute(
            "DELETE FROM platform.metric_definition WHERE metric_id = %s", (METRIC,)
        )
        cls.meta.execute(
            "DELETE FROM platform.source_ref_registry WHERE source_ref LIKE %s",
            (f"%{METRIC}%",),
        )
        cls.runtime.close()

    @classmethod
    def _seed(cls) -> None:
        # metric_definition has PK(metric_id) in this schema, so a metric has one
        # live definition version at a time. The version dimension is still part
        # of the observation natural key and of every observation ref.
        cls.meta.execute(
            "DELETE FROM platform.metric_observation WHERE metric_id = %s", (METRIC,)
        )
        cls.meta.execute(
            """
            INSERT INTO platform.metric_definition
              (metric_id, name_zh, domain, evidence_basis, publishable, inference,
               formula_disabled, missing, evidence_status, note, definition_version,
               metric_kind, formula_expr, numerator_agg, denominator_agg, window_kind,
               min_window_days, grain, unit)
            VALUES (%s, '溯源测试指标', 'bank', 'regulatory', true, false, false, NULL,
                    'EVIDENCED', 'test-only', 'v1', 'sum', 'numerator', 'max', NULL,
                    'instant', 0, 'customer', '个')
            ON CONFLICT (metric_id) DO UPDATE SET
              definition_version = EXCLUDED.definition_version,
              formula_expr = EXCLUDED.formula_expr,
              publishable = EXCLUDED.publishable,
              formula_disabled = false
            """,
            (METRIC,),
        )
        cls._obs("v1", "E1", 10)

    @classmethod
    def _obs(cls, version: str, entity: str, numerator: int) -> None:
        cls.meta.execute(
            """
            INSERT INTO platform.metric_observation
              (metric_id, definition_version, entity_key, as_of, numerator,
               window_start, window_end, data_source, fixture)
            VALUES (%s, %s, %s, '2025-12-31', %s, '2025-12-31', '2025-12-31', 'fixture', true)
            ON CONFLICT ON CONSTRAINT metric_observation_window_key DO UPDATE SET
              numerator = EXCLUDED.numerator, computed_at = now()
            """,
            (METRIC, version, entity, numerator),
        )

    def _code(self, call, *args, **kwargs) -> PortError:
        with self.assertRaises(PortError) as caught:
            call(*args, **kwargs)
        return caught.exception

    # ---- one positive example per source kind ---------------------------

    def test_observation_row(self) -> None:
        ref = source_ref.observation_ref(METRIC, "v1", "E1", "2025-12-31", "2025-12-31")
        result = source_ref.resolve(self.meta, ref)
        self.assertEqual(result["type"], source_ref.OBSERVATION_ROW)
        self.assertEqual(result["rowCount"], 1)
        self.assertGreater(float(result["rows"][0]["numerator"]), 0)

    def test_fact_row(self) -> None:
        key = self.meta.query(
            "SELECT agreement_id, installment_no, status_as_of, data_source "
            "FROM platform.loan_installment_plan LIMIT 1"
        )
        if not key:
            self.skipTest("no installment plan rows")
        ref = source_ref.fact_row_ref("platform.loan_installment_plan", key[0])
        result = source_ref.resolve(self.meta, ref)
        self.assertEqual(result["type"], source_ref.FACT_ROW)
        self.assertEqual(result["rowCount"], 1)
        for column, value in key[0].items():
            self.assertEqual(result["rows"][0][column], source_ref.jsonable(key[0])[column])

    def test_document_chunk(self) -> None:
        chunk = self.meta.query(
            "SELECT document_id, seq, chunk_id FROM platform.document_chunk "
            "ORDER BY document_id, seq LIMIT 1"
        )
        if not chunk:
            self.skipTest("no document chunks")
        ref = source_ref.chunk_ref(chunk[0]["document_id"], chunk[0]["seq"])
        result = source_ref.resolve(self.meta, ref)
        self.assertEqual(result["type"], source_ref.DOCUMENT_CHUNK)
        self.assertEqual(result["locator"]["documentId"], chunk[0]["document_id"])
        self.assertEqual(result["locator"]["chunkNo"], chunk[0]["seq"])

    # ---- stability ------------------------------------------------------

    def test_recompute_keeps_same_row(self) -> None:
        ref = source_ref.observation_ref(METRIC, "v1", "E1", "2025-12-31", "2025-12-31")
        before = source_ref.resolve(self.meta, ref)
        observation_id = before["rows"][0]["observation_id"]
        self._obs("v1", "E1", 33)
        after = source_ref.resolve(self.meta, ref)
        self.assertEqual(after["rows"][0]["observation_id"], observation_id)
        self.assertEqual(float(after["rows"][0]["numerator"]), 33.0)

    def test_version_switch_does_not_misresolve(self) -> None:
        # The version is inside the ref, so a ref that names a version with no
        # row can never silently resolve to another version's row.
        v1 = source_ref.observation_ref(METRIC, "v1", "E1", "2025-12-31", "2025-12-31")
        v2 = source_ref.observation_ref(METRIC, "v2", "E1", "2025-12-31", "2025-12-31")
        one = source_ref.resolve(self.meta, v1)
        self.assertEqual(one["rows"][0]["definition_version"], "v1")
        exc = self._code(source_ref.resolve, self.meta, v2)
        self.assertEqual(exc.provider_code, source_ref.NOT_FOUND)

    def test_compute_carries_resolvable_set_ref(self) -> None:
        computed = self.runtime.metrics.compute(
            METRIC, internal=True, as_of=date(2025, 12, 31),
        )
        descriptor = computed["sourceRef"]
        self.assertEqual(descriptor["type"], source_ref.OBSERVATION_SET)
        self.assertEqual(descriptor["rowCount"], 1)
        resolved = source_ref.resolve(self.meta, descriptor["ref"])
        self.assertEqual(resolved["rowCount"], 1)

    # ---- negatives ------------------------------------------------------

    def test_not_found(self) -> None:
        ref = source_ref.observation_ref(METRIC, "v1", "NOPE", "2025-12-31", "2025-12-31")
        exc = self._code(source_ref.resolve, self.meta, ref)
        self.assertEqual(exc.provider_code, source_ref.NOT_FOUND)

    def test_stale_after_row_removed(self) -> None:
        self._obs("v1", "E9", 7)
        ref = source_ref.observation_ref(METRIC, "v1", "E9", "2025-12-31", "2025-12-31")
        descriptor = source_ref.observation_row_descriptor(
            {"metric_id": METRIC, "definition_version": "v1", "entity_key": "E9",
             "window_start": "2025-12-31", "window_end": "2025-12-31"}
        )
        self.meta.execute(
            "DELETE FROM platform.metric_observation WHERE metric_id = %s "
            "AND definition_version = 'v1' AND entity_key = 'E9'", (METRIC,)
        )
        source_ref.register_ref(self.meta, descriptor)
        exc = self._code(source_ref.resolve, self.meta, ref)
        self.assertEqual(exc.provider_code, source_ref.STALE)

    def test_forbidden_table(self) -> None:
        ref = "src://fact/platform.metric_definition?metric_id=FIN-BANK-001"
        exc = self._code(source_ref.resolve, self.meta, ref)
        self.assertEqual(exc.provider_code, source_ref.FORBIDDEN)


if __name__ == "__main__":
    unittest.main()
