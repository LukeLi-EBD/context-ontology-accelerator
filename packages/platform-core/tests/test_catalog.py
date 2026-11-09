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
        if filters.get("missingComment"):
            rows = [row for row in rows if not row.get("comment")]
        if filters.get("unbound"):
            rows = [row for row in rows if row.get("binding_method") == "none"]
        if filters.get("mappable"):
            rows = [
                row
                for row in rows
                if row.get("binding_method") != "none"
                or catalog.is_mappable(row["table_name"], row["column_name"])
            ]
        if filters.get("mappableUnbound"):
            rows = [
                row
                for row in rows
                if row.get("binding_method") == "none"
                and catalog.is_mappable(row["table_name"], row["column_name"])
            ]
        return rows[offset: offset + limit], len(rows)

    def table_row(self, catalog_name, schema_name, table, column):
        row = self.rows.get((catalog_name, schema_name, table, column))
        return dict(row) if row else None

    def set_manual_binding(
        self, catalog_name, schema_name, table, column, property_iri, confidence, note
    ):
        row = self.rows[(catalog_name, schema_name, table, column)]
        row["property_iri"] = property_iri
        row["binding_method"] = "manual"
        row["confidence"] = confidence
        row["binding_note"] = note
        row["observed_at"] = "2026-11-06T01:00:00+00:00"

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

    def test_as_of_binds_to_observation_date(self) -> None:
        binding = catalog.resolve_binding("bank_loan_account", "as_of")
        self.assertEqual(binding["bindingMethod"], "explicit")
        self.assertEqual(
            binding["propertyIri"], "https://w3id.org/fsldm/core#observationDate"
        )

    def test_mappable_candidate_stays_unbound(self) -> None:
        binding = catalog.resolve_binding("bank_loan_account", "period_start")
        self.assertEqual(binding["bindingMethod"], "none")
        self.assertIsNone(binding["propertyIri"])
        self.assertIn("可映射候选", binding["bindingNote"])
        self.assertTrue(catalog.is_mappable("bank_loan_account", "period_start"))


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


MIXED_COLUMNS = [
    {
        "table": "bank_loan_account",
        "column": "customer_no",
        "dataType": "character varying",
        "isNullable": False,
        "comment": "客户号",
        "ordinal": 1,
    },
    {
        "table": "bank_loan_account",
        "column": "as_of",
        "dataType": "date",
        "isNullable": False,
        "comment": "观察时点",
        "ordinal": 2,
    },
    {
        "table": "bank_loan_account",
        "column": "product",
        "dataType": "character varying",
        "isNullable": True,
        "comment": "产品代码",
        "ordinal": 3,
    },
    {
        "table": "bank_loan_account",
        "column": "period_start",
        "dataType": "date",
        "isNullable": True,
        "comment": None,
        "ordinal": 4,
    },
    {
        "table": "bank_loan_account",
        "column": "dpd_start",
        "dataType": "integer",
        "isNullable": True,
        "comment": None,
        "ordinal": 5,
    },
    {
        "table": "bank_loan_account",
        "column": "created_at",
        "dataType": "timestamp with time zone",
        "isNullable": False,
        "comment": None,
        "ordinal": 6,
    },
]


class DictHarness(unittest.TestCase):
    columns = MIXED_COLUMNS

    def make_service(self):
        repo = FakeRepo()
        service = catalog.CatalogService(
            FakeRuntime(),
            repository=repo,
            mysql_dsn="",
            pg_introspector=lambda schema, tables: list(self.columns),
        )
        service.refresh(sources=["pg"])
        return service, repo


class CoverageTests(DictHarness):
    def test_column_coverage_is_zero_gap(self) -> None:
        service, repo = self.make_service()
        report = service.coverage()
        self.assertTrue(report["complete"])
        self.assertEqual(report["totals"]["tables"], 1)
        self.assertEqual(report["totals"]["expectedColumns"], 6)
        self.assertEqual(report["totals"]["dictionaryRows"], 6)
        self.assertEqual(report["totals"]["missingColumns"], 0)
        self.assertEqual(report["totals"]["extraColumns"], 0)
        item = report["items"][0]
        self.assertEqual(item["missingColumns"], [])
        self.assertEqual(item["extraColumns"], [])
        # Uncommented columns must still be present.
        self.assertIn(
            ("platform", "platform", "bank_loan_account", "created_at"), repo.rows
        )

    def test_binding_rate_uses_mappable_denominator(self) -> None:
        service, _repo = self.make_service()
        report = service.coverage()
        binding = report["binding"]
        self.assertEqual(binding["total"], 6)
        self.assertEqual(binding["mappable"], 4)  # 3 bound + period_start candidate
        self.assertEqual(binding["bound"], 3)
        self.assertEqual(binding["unbound"], 1)
        self.assertEqual(binding["rate"], 0.75)
        self.assertEqual(binding["ratePercent"], 75.0)
        self.assertEqual(
            binding["unboundColumns"],
            [{"table": "bank_loan_account", "column": "period_start"}],
        )


class ManualBindingTests(DictHarness):
    def test_manual_binding_records_operator_basis_and_time(self) -> None:
        service, repo = self.make_service()
        result = service.record_manual_binding(
            table="bank_loan_account",
            column="period_start",
            property_iri="https://w3id.org/fsldm/core#validFrom",
            operator="data-ops",
            basis="期初观察日按 validFrom 登记",
            note="O-01 人工确认",
        )
        self.assertEqual(result["bindingMethod"], "manual")
        self.assertEqual(result["propertyIri"], "https://w3id.org/fsldm/core#validFrom")
        self.assertEqual(result["confidence"], 1.0)
        self.assertEqual(result["manualOperator"], "data-ops")
        self.assertEqual(result["manualBasis"], "期初观察日按 validFrom 登记")
        self.assertTrue(result["manualAt"])
        self.assertIn("人工绑定", result["bindingNote"])
        stored = repo.rows[("platform", "platform", "bank_loan_account", "period_start")]
        audit = catalog.parse_manual_note(stored["binding_note"])
        self.assertEqual(audit["operator"], "data-ops")
        self.assertEqual(audit["basis"], "期初观察日按 validFrom 登记")
        self.assertTrue(audit["at"])

    def test_manual_binding_requires_operator_basis_and_known_property(self) -> None:
        service, _repo = self.make_service()
        cases = [
            ({"operator": "", "basis": "x"}, "operator"),
            ({"operator": "ops", "basis": ""}, "basis"),
            ({"operator": "ops", "basis": "x", "property_iri": "example"}, "propertyIri"),
            (
                {
                    "operator": "ops",
                    "basis": "x",
                    "property_iri": "https://example.com/nope",
                },
                "propertyIri",
            ),
        ]
        for overrides, field in cases:
            payload = {
                "table": "bank_loan_account",
                "column": "period_start",
                "property_iri": "https://w3id.org/fsldm/core#validFrom",
                "operator": "ops",
                "basis": "依据",
            }
            payload.update(overrides)
            with self.assertRaises(PortError) as caught:
                service.record_manual_binding(**payload)
            self.assertEqual(caught.exception.provider_code, "E_DICT_BINDING_INVALID")
            self.assertEqual(
                (caught.exception.details or {}).get("field"), field
            )

    def test_manual_binding_rejects_unknown_column(self) -> None:
        service, _repo = self.make_service()
        with self.assertRaises(PortError) as caught:
            service.record_manual_binding(
                table="bank_loan_account",
                column="no_such_column",
                property_iri="https://w3id.org/fsldm/core#validFrom",
                operator="ops",
                basis="依据",
            )
        self.assertEqual(caught.exception.provider_code, "E_DICT_COLUMN_NOT_FOUND")

    def test_refresh_preserves_manual_binding(self) -> None:
        service, repo = self.make_service()
        service.record_manual_binding(
            table="bank_loan_account",
            column="period_start",
            property_iri="https://w3id.org/fsldm/core#validFrom",
            operator="data-ops",
            basis="期初观察日按 validFrom 登记",
        )
        service.refresh(sources=["pg"])
        stored = repo.rows[("platform", "platform", "bank_loan_account", "period_start")]
        self.assertEqual(stored["binding_method"], "manual")
        self.assertEqual(
            stored["property_iri"], "https://w3id.org/fsldm/core#validFrom"
        )
        audit = catalog.parse_manual_note(stored["binding_note"])
        self.assertEqual(audit["operator"], "data-ops")


class FilterViewTests(DictHarness):
    def test_missing_comment_view(self) -> None:
        service, _repo = self.make_service()
        page = service.list({"missingComment": True}, limit=50)
        self.assertEqual(page["total"], 3)
        self.assertEqual(
            {item["column"] for item in page["items"]},
            {"period_start", "dpd_start", "created_at"},
        )

    def test_unbound_view(self) -> None:
        service, _repo = self.make_service()
        page = service.list({"unbound": True}, limit=50)
        self.assertEqual(page["total"], 3)

    def test_mappable_view(self) -> None:
        service, _repo = self.make_service()
        page = service.list({"mappable": True}, limit=50)
        self.assertEqual(page["total"], 4)
        self.assertEqual(
            {item["column"] for item in page["items"]},
            {"customer_no", "as_of", "product", "period_start"},
        )

    def test_mappable_unbound_view_keeps_denominator_honest(self) -> None:
        service, _repo = self.make_service()
        page = service.list({"mappableUnbound": True}, limit=50)
        self.assertEqual(page["total"], 1)
        self.assertEqual(page["items"][0]["column"], "period_start")


if __name__ == "__main__":
    unittest.main()
