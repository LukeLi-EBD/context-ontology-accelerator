"""DataSourceLookup proof: S1's JsonDataSourceLookup, consumed by coa_metrics.validator."""

from __future__ import annotations

import inspect
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from coa_metrics.lookups import ColumnMetadata, DataSourceLookup
from coa_metrics.validator import validate_metric
from coa_local_providers.json_lookup import JsonDataSourceLookup

from coa_gateway import ProviderNotConfigured, ProviderSettings, build_client

SNAPSHOT = {
    "data_sources": {
        "platform": {
            "catalog_available": True,
            "tables": {
                "platform.bank_collection_case": [
                    {"name": "case_id", "data_type": "text"},
                    {"name": "case_status", "data_type": "text"},
                ]
            },
        }
    }
}

BODY = {
    "dataSourceId": "platform",
    "sourceTable": "platform.bank_collection_case",
    "expression": {
        "dialects": [
            {
                "dialect": "TRINO",
                "expression": "SELECT case_id, case_status FROM platform.bank_collection_case",
            }
        ]
    },
}


class CountingLookup(JsonDataSourceLookup):
    """Same S1 class, with call counting so the consumer is observable."""

    def __init__(self, snapshot: dict) -> None:
        super().__init__(snapshot)
        self.calls: Counter[str] = Counter()
        self.validator_frames: set[str] = set()

    def _note(self, method: str) -> None:
        self.calls[method] += 1
        for frame in inspect.stack():
            if "coa_metrics" in frame.filename and "validator.py" in frame.filename:
                self.validator_frames.add(frame.function)

    def data_source_exists(self, data_source_id: str) -> bool:
        self._note("data_source_exists")
        return super().data_source_exists(data_source_id)

    def table_exists(self, data_source_id: str, table_name: str) -> bool:
        self._note("table_exists")
        return super().table_exists(data_source_id, table_name)

    def get_table_columns(self, data_source_id: str, table_name: str) -> list[ColumnMetadata] | None:
        self._note("get_table_columns")
        return super().get_table_columns(data_source_id, table_name)

    def catalog_available(self, data_source_id: str) -> bool:
        self._note("catalog_available")
        return super().catalog_available(data_source_id)

    def known_tables(self, data_source_id: str) -> set[str]:
        self._note("known_tables")
        return super().known_tables(data_source_id)

    def table_rejection_reason(self, data_source_id: str, table_name: str) -> str | None:
        self._note("table_rejection_reason")
        return super().table_rejection_reason(data_source_id, table_name)


class SourceCatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        path = Path(self._tmp.name) / "catalog.json"
        path.write_text(json.dumps(SNAPSHOT), encoding="utf-8")
        self.path = path

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_registry_builds_s1_class_and_it_answers(self) -> None:
        lookup = build_client(
            "source_catalog",
            ProviderSettings.from_mapping(
                {"COA_PROVIDER_SOURCE_CATALOG": "json", "COA_SOURCE_CATALOG_JSON_PATH": str(self.path)}
            ),
        )
        self.assertIsInstance(lookup, JsonDataSourceLookup)
        self.assertIsInstance(lookup, DataSourceLookup)
        self.assertTrue(lookup.data_source_exists("platform"))
        self.assertTrue(lookup.table_exists("platform", "platform.bank_collection_case"))
        self.assertEqual(
            [column.name for column in lookup.get_table_columns("platform", "platform.bank_collection_case")],
            ["case_id", "case_status"],
        )

    def test_validator_consumes_it_and_calls_are_observable(self) -> None:
        lookup = CountingLookup(SNAPSHOT)
        result = validate_metric(BODY, data_sources_lookup=lookup)

        self.assertTrue(result.valid, result.errors)
        self.assertGreater(sum(lookup.calls.values()), 0)
        self.assertGreaterEqual(lookup.calls["table_exists"] + lookup.calls["known_tables"], 1)
        self.assertIn("validate_metric", lookup.validator_frames)

    def test_missing_snapshot_path_is_a_clear_error(self) -> None:
        with self.assertRaises(ProviderNotConfigured) as caught:
            build_client("source_catalog", ProviderSettings.from_mapping({"COA_PROVIDER_SOURCE_CATALOG": "json"}))
        self.assertIn("COA_SOURCE_CATALOG_JSON_PATH", str(caught.exception))

    def test_smus_is_declared_but_unwired(self) -> None:
        with self.assertRaises(ProviderNotConfigured) as caught:
            build_client("source_catalog", ProviderSettings.from_mapping({"COA_PROVIDER_SOURCE_CATALOG": "smus"}))
        self.assertIn("not wired", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
