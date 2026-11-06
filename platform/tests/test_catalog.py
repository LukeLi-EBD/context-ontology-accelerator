"""B-06 data dictionary tests (offline; no live PostgreSQL required)."""

from __future__ import annotations

import unittest

from platform_core import catalog
from platform_core.errors import PortError


COLUMNS = [
    {
        "table": "bank_loan_account",
        "column": "account_id",
        "dataType": "character varying",
        "isNullable": False,
        "comment": "贷款账号",
        "ordinal": 1,
    },
    {
        "table": "bank_loan_account",
        "column": "maturity_date",
        "dataType": "date",
        "isNullable": True,
        "comment": None,
        "ordinal": 2,
    },
    {
        "table": "bank_loan_account",
        "column": "industry",
        "dataType": "character varying",
        "isNullable": True,
        "comment": None,
        "ordinal": 3,
    },
    {
        "table": "bank_ews_signal",
        "column": "dpd",
        "dataType": "integer",
        "isNullable": True,
        "comment": None,
        "ordinal": 1,
    },
]


class FakeGraph:
    def query(self, _statement: str) -> dict:
        return {"bindings": []}


class FakeOntology:
    def current(self) -> None:
        return None


class FakeRuntime:
    def __init__(self) -> None:
        self.metadata = None
        self.ontology = FakeOntology()
        self.graph = FakeGraph()


class FakeRepo:
    def __init__(self) -> None:
        self.rows: dict[tuple, dict] = {}
        self.upserts: list[dict] = []
        self.last_filters: dict | None = None

    def list(self, filters, limit=20, offset=0):
        self.last_filters = filters
        mapping = {
            "catalog": "catalog_name",
            "schema": "schema_name",
            "table": "table_name",
            "column": "column_name",
            "sourceKind": "source_kind",
            "bindingMethod": "binding_method",
        }
        rows = list(self.rows.values())
        for field, column in mapping.items():
            value = filters.get(field)
            if value:
                rows = [row for row in rows if row.get(column) == value]
        return rows[offset: offset + limit], len(rows)

    def table_rows(self, catalog_name, schema_name, table):
        return [row for key, row in self.rows.items() if key[2] == table]

    def distinct_tables(self, catalog_name, schema_name):
        return sorted({key[2] for key in self.rows})

    def existing(self, catalog_name, schema_name, tables):
        return {
            key: row
            for key, row in self.rows.items()
            if key[2] in set(tables)
        }

    def upsert(self, entry, mark_observed=True):
        self.upserts.append(entry)
        self.rows[(entry["catalog"], entry["schema"], entry["table"], entry["column"])] = {
            "catalog_name": entry["catalog"],
            "schema_name": entry["schema"],
            "table_name": entry["table"],
            "column_name": entry["column"],
            "data_type": entry["dataType"],
            "is_nullable": entry["isNullable"],
            "comment": entry.get("comment"),
            "source_kind": entry["sourceKind"],
            "property_iri": entry.get("propertyIri"),
            "binding_method": entry["bindingMethod"],
            "confidence": entry.get("confidence"),
            "binding_note": entry.get("bindingNote"),
            "observed_at": "2026-11-06T00:00:00+00:00",
        }

    def max_observed(self, catalog_name, schema_name):
        return "2026-11-06T00:00:00+00:00"


class BindingTests(unittest.TestCase):
    def test_name_match_confidence_is_080(self) -> None:
        binding = catalog.resolve_binding("bank_loan_account", "maturity_date")
        self.assertEqual(binding["bindingMethod"], "name_match")
        self.assertEqual(binding["confidence"], 0.8)
        self.assertEqual(
            binding["propertyIri"], "https://w3id.org/fsldm/core#maturityDate"
        )

    def test_explicit_binding_beats_name_match(self) -> None:
        explicit = catalog.resolve_binding("bank_disposal_event", "asset_id")
        self.assertEqual(explicit["bindingMethod"], "explicit")
        self.assertEqual(explicit["confidence"], 1.0)
        self.assertIn("处置事件", explicit["bindingNote"])
        name_only = catalog.resolve_binding("bank_npl_snapshot", "asset_id")
        self.assertEqual(name_only["bindingMethod"], "name_match")

    def test_unbound_column_keeps_reason(self) -> None:
        binding = catalog.resolve_binding("bank_loan_account", "industry")
        self.assertEqual(binding["bindingMethod"], "none")
        self.assertIsNone(binding["propertyIri"])
        self.assertIsNone(binding["confidence"])
        self.assertTrue(binding["bindingNote"])

    def test_dpd_is_unbound_without_inventing_property(self) -> None:
        binding = catalog.resolve_binding("bank_ews_signal", "dpd")
        self.assertEqual(binding["bindingMethod"], "none")
        self.assertIsNone(binding["propertyIri"])
        self.assertIn("逾期天数", binding["bindingNote"])

    def test_audit_and_key_columns_are_unbound(self) -> None:
        self.assertIn(
            "系统/审计",
            catalog.resolve_binding("bank_loan_account", "created_at")["bindingNote"],
        )
        self.assertIn(
            "本地编号",
            catalog.resolve_binding("bank_loan_account", "deposit_id")["bindingNote"],
        )


class RefreshTests(unittest.TestCase):
    def _service(self, repo=None):
        runtime = FakeRuntime()
        repo = repo or FakeRepo()
        service = catalog.CatalogService(
            runtime,
            repository=repo,
            mysql_dsn="",
            pg_introspector=lambda schema, tables: list(COLUMNS),
        )
        return service, repo

    def test_refresh_is_idempotent(self) -> None:
        service, repo = self._service()
        first = service.refresh(sources=["pg"])
        self.assertEqual(first["processed"], 4)
        self.assertEqual(first["inserted"], 4)
        self.assertEqual(first["updated"], 0)
        self.assertEqual(first["unchanged"], 0)
        second = service.refresh(sources=["pg"])
        self.assertEqual(second["inserted"], 0)
        self.assertEqual(second["updated"], 0)
        self.assertEqual(second["unchanged"], 4)
        self.assertEqual(len(repo.rows), 4)

    def test_refresh_reports_three_tiers(self) -> None:
        service, _repo = self._service()
        result = service.refresh(sources=["pg"])
        self.assertEqual(result["bySourceKind"], {"pg": 4})
        self.assertEqual(result["binding"]["explicit"], 0)
        self.assertEqual(result["binding"]["name_match"], 1)  # maturity_date
        self.assertEqual(result["binding"]["none"], 3)  # account_id, industry, dpd
        self.assertEqual(result["binding"]["manual"], 0)

    def test_mysql_source_unreachable(self) -> None:
        service, _repo = self._service()
        with self.assertRaises(PortError) as caught:
            service.refresh(sources=["mysql"])
        err = caught.exception
        self.assertEqual(err.provider_code, "E_DICT_SOURCE_UNREACHABLE")
        self.assertEqual(err.code, "Unavailable")
        self.assertEqual((err.details or {}).get("sourceKind"), "mysql")

    def test_glue_source_unreachable(self) -> None:
        service, _repo = self._service()
        with self.assertRaises(PortError) as caught:
            service.refresh(sources=["glue"])
        err = caught.exception
        self.assertEqual(err.provider_code, "E_DICT_SOURCE_UNREACHABLE")
        self.assertEqual((err.details or {}).get("sourceKind"), "glue")

    def test_unknown_source_is_rejected(self) -> None:
        service, _repo = self._service()
        with self.assertRaises(PortError) as caught:
            service.refresh(sources=["snowflake"])
        self.assertEqual(caught.exception.provider_code, "E_DICT_SOURCE_UNKNOWN")
        self.assertEqual(caught.exception.code, "InvalidArgument")


class QueryTests(unittest.TestCase):
    def _loaded_service(self):
        repo = FakeRepo()
        service = catalog.CatalogService(
            FakeRuntime(),
            repository=repo,
            mysql_dsn="",
            pg_introspector=lambda schema, tables: list(COLUMNS),
        )
        service.refresh(sources=["pg"])
        return service, repo

    def test_filter_and_pagination(self) -> None:
        service, repo = self._loaded_service()
        page = service.list({"table": "bank_loan_account"}, limit=2, offset=1)
        self.assertEqual(repo.last_filters["table"], "bank_loan_account")
        self.assertEqual(page["total"], 3)
        self.assertEqual(page["count"], 2)
        self.assertEqual(page["limit"], 2)
        self.assertEqual(page["offset"], 1)
        self.assertEqual(page["items"][0]["column"], "maturity_date")

    def test_table_detail_counts_binding_tiers(self) -> None:
        service, _repo = self._loaded_service()
        detail = service.table("bank_loan_account")
        self.assertEqual(detail["count"], 3)
        self.assertEqual(detail["binding"]["explicit"], 0)
        self.assertEqual(detail["binding"]["name_match"], 1)
        self.assertEqual(detail["binding"]["none"], 2)
        self.assertEqual(detail["sourceKinds"], ["pg"])

    def test_missing_table_detail_is_not_found(self) -> None:
        service, _repo = self._loaded_service()
        with self.assertRaises(PortError) as caught:
            service.table("no_such_table")
        self.assertEqual(caught.exception.provider_code, "E_DICT_TABLE_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
