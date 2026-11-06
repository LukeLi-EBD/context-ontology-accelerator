"""B-06 data dictionary: read-only introspection of fact tables + property hints.

Scope and boundaries:
* The dictionary is descriptive only. ``property_iri`` is a binding hint for
  browsing; it never participates in publish gates and is never an ontology
  authority.
* Introspection is read-only: PostgreSQL ``information_schema.columns`` plus
  ``pg_description`` for comments. MySQL uses ``information_schema.columns``;
  when no MySQL endpoint/driver is available the call fails loudly with
  ``E_DICT_SOURCE_UNREACHABLE`` instead of inventing rows. Glue goes through a
  configured catalog adapter and fails the same way when none is configured.
* Refresh is idempotent: rows are keyed by (catalog, schema, table, column) and
  unchanged columns keep their previous ``observed_at``.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Sequence
from urllib.parse import unquote, urlparse

from .errors import PortError

FACT_TABLES: tuple[str, ...] = (
    "bank_collection_case",
    "bank_collection_recovery",
    "bank_concentration_stat",
    "bank_credit_application",
    "bank_credit_facility",
    "bank_deposit_account",
    "bank_disposal_event",
    "bank_ews_signal",
    "bank_loan_account",
    "bank_loan_repayment",
    "bank_npl_snapshot",
    "bank_provision_snapshot",
    "cust_aum_snapshot",
    "cust_behavior_snapshot",
    "cust_campaign_touch",
    "cust_cohort_stat",
    "cust_complaint",
    "cust_master",
    "cust_product_holding",
    "cust_transaction",
    "ins_claim_case",
    "ins_claim_reserve_snapshot",
    "ins_payment_record",
    "ins_persistence_stat",
    "ins_policy",
    "ins_policy_event",
    "ins_underwriting_stat",
    "loan_installment_plan",
)

SOURCE_KINDS: tuple[str, ...] = ("pg", "mysql", "glue")
BINDING_METHODS: tuple[str, ...] = ("explicit", "name_match", "manual", "none")

NAME_MATCH_CONFIDENCE = 0.800

# Explicit bindings win over name normalisation. ``("*", column)`` applies to
# every fact table; a table-specific entry overrides the wildcard.
# confidence 1.0 = same meaning, <1.0 = documented semantic approximation.
EXPLICIT_BINDINGS: dict[tuple[str, str], dict[str, Any]] = {
    ("*", "customer_no"): {
        "iri": "https://w3id.org/fsldm/core#partyId",
        "confidence": 1.0,
        "note": "显式绑定：客户号即当事人编号 partyId",
    },
    ("*", "policy_no"): {
        "iri": "https://w3id.org/fsldm/core#agreementId",
        "confidence": 0.9,
        "note": "显式绑定：保单号按协议编号 agreementId 登记（语义近似）",
    },
    ("bank_disposal_event", "asset_id"): {
        "iri": "https://w3id.org/fsldm/core#assetId",
        "confidence": 1.0,
        "note": "显式绑定：处置事件指向的资产 assetId",
    },
    ("bank_loan_account", "disbursed_date"): {
        "iri": "https://w3id.org/fsldm/core#originationDate",
        "confidence": 1.0,
        "note": "显式绑定：放款日即起息日 originationDate",
    },
    ("bank_loan_account", "first_payment_due_date"): {
        "iri": "https://w3id.org/fsldm/core#firstPaymentDate",
        "confidence": 1.0,
        "note": "显式绑定：首期应还款日 firstPaymentDate",
    },
    ("bank_credit_facility", "effective_from"): {
        "iri": "https://w3id.org/fsldm/core#validFrom",
        "confidence": 0.9,
        "note": "显式绑定：额度生效起始时间 validFrom（语义近似）",
    },
    ("bank_credit_facility", "effective_to"): {
        "iri": "https://w3id.org/fsldm/core#validUntil",
        "confidence": 0.9,
        "note": "显式绑定：额度生效结束时间 validUntil（语义近似）",
    },
    ("ins_policy", "issue_date"): {
        "iri": "https://w3id.org/fsldm/core#originationDate",
        "confidence": 0.9,
        "note": "显式绑定：保单签发日按起息日 originationDate 登记（语义近似）",
    },
    ("ins_underwriting_stat", "period_start"): {
        "iri": "https://w3id.org/fsldm/core#validFrom",
        "confidence": 0.9,
        "note": "显式绑定：统计期间起点 validFrom（语义近似）",
    },
    ("ins_underwriting_stat", "period_end"): {
        "iri": "https://w3id.org/fsldm/core#validUntil",
        "confidence": 0.9,
        "note": "显式绑定：统计期间终点 validUntil（语义近似）",
    },
}

# Static mirror of the published T-Box (ont-11f92ebb3326). Refresh prefers the
# live T-Box property index; this copy keeps binding deterministic offline and
# is never used to publish ontology changes.
STATIC_PROPERTIES: tuple[tuple[str, str], ...] = (
    ("accountModifierNumber", "https://w3id.org/fsldm/agreement#accountModifierNumber"),
    ("accountNumber", "https://w3id.org/fsldm/agreement#accountNumber"),
    ("applicationProducedAgreement", "https://w3id.org/fsldm/agreement#applicationProducedAgreement"),
    ("appliedProduct", "https://w3id.org/fsldm/agreement#appliedProduct"),
    ("classifiedAgreement", "https://w3id.org/fsldm/agreement#classifiedAgreement"),
    ("hasPartyRole", "https://w3id.org/fsldm/agreement#hasPartyRole"),
    ("hasProductAssignment", "https://w3id.org/fsldm/agreement#hasProductAssignment"),
    ("ofAgreement", "https://w3id.org/fsldm/agreement#ofAgreement"),
    ("ofClaim", "https://w3id.org/fsldm/agreement#ofClaim"),
    ("parentAgreement", "https://w3id.org/fsldm/agreement#parentAgreement"),
    ("quotationAcceptedBy", "https://w3id.org/fsldm/agreement#quotationAcceptedBy"),
    ("roleParty", "https://w3id.org/fsldm/agreement#roleParty"),
    ("collateralizes", "https://w3id.org/fsldm/asset#collateralizes"),
    ("ownershipShare", "https://w3id.org/fsldm/asset#ownershipShare"),
    ("valuationMethod", "https://w3id.org/fsldm/asset#valuationMethod"),
    ("collateralAsset", "https://w3id.org/fsldm/banking#collateralAsset"),
    ("collateralForAgreement", "https://w3id.org/fsldm/banking#collateralForAgreement"),
    ("haircutOfCollateral", "https://w3id.org/fsldm/banking#haircutOfCollateral"),
    ("mitigatesAgreement", "https://w3id.org/fsldm/banking#mitigatesAgreement"),
    ("conditionExpression", "https://w3id.org/fsldm/campaign#conditionExpression"),
    ("hasCell", "https://w3id.org/fsldm/campaign#hasCell"),
    ("hasPromotion", "https://w3id.org/fsldm/campaign#hasPromotion"),
    ("offeredIncentive", "https://w3id.org/fsldm/campaign#offeredIncentive"),
    ("deviceNumber", "https://w3id.org/fsldm/channel#deviceNumber"),
    ("deviceStatus", "https://w3id.org/fsldm/channel#deviceStatus"),
    ("parentPage", "https://w3id.org/fsldm/channel#parentPage"),
    ("sessionDuration", "https://w3id.org/fsldm/channel#sessionDuration"),
    ("usesChannel", "https://w3id.org/fsldm/channel#usesChannel"),
    ("agreementId", "https://w3id.org/fsldm/core#agreementId"),
    ("agreementOf", "https://w3id.org/fsldm/core#agreementOf"),
    ("assetId", "https://w3id.org/fsldm/core#assetId"),
    ("assetOf", "https://w3id.org/fsldm/core#assetOf"),
    ("campaignOf", "https://w3id.org/fsldm/core#campaignOf"),
    ("channelOf", "https://w3id.org/fsldm/core#channelOf"),
    ("classifies", "https://w3id.org/fsldm/core#classifies"),
    ("dueDate", "https://w3id.org/fsldm/core#dueDate"),
    ("eventId", "https://w3id.org/fsldm/core#eventId"),
    ("eventOf", "https://w3id.org/fsldm/core#eventOf"),
    ("featureOf", "https://w3id.org/fsldm/core#featureOf"),
    ("firstPaymentDate", "https://w3id.org/fsldm/core#firstPaymentDate"),
    ("hasAgreement", "https://w3id.org/fsldm/core#hasAgreement"),
    ("hasAsset", "https://w3id.org/fsldm/core#hasAsset"),
    ("hasCampaign", "https://w3id.org/fsldm/core#hasCampaign"),
    ("hasChannel", "https://w3id.org/fsldm/core#hasChannel"),
    ("hasClassValue", "https://w3id.org/fsldm/core#hasClassValue"),
    ("hasCode", "https://w3id.org/fsldm/core#hasCode"),
    ("hasCurrency", "https://w3id.org/fsldm/core#hasCurrency"),
    ("hasEvent", "https://w3id.org/fsldm/core#hasEvent"),
    ("hasFeature", "https://w3id.org/fsldm/core#hasFeature"),
    ("hasLocator", "https://w3id.org/fsldm/core#hasLocator"),
    ("hasMetric", "https://w3id.org/fsldm/core#hasMetric"),
    ("hasParty", "https://w3id.org/fsldm/core#hasParty"),
    ("hasProduct", "https://w3id.org/fsldm/core#hasProduct"),
    ("hasRole", "https://w3id.org/fsldm/core#hasRole"),
    ("hasStatus", "https://w3id.org/fsldm/core#hasStatus"),
    ("identificationType", "https://w3id.org/fsldm/core#identificationType"),
    ("identificationValue", "https://w3id.org/fsldm/core#identificationValue"),
    ("inScheme", "https://w3id.org/fsldm/core#inScheme"),
    ("isPrimaryRole", "https://w3id.org/fsldm/core#isPrimaryRole"),
    ("lastPaymentDate", "https://w3id.org/fsldm/core#lastPaymentDate"),
    ("locatorOf", "https://w3id.org/fsldm/core#locatorOf"),
    ("maturityDate", "https://w3id.org/fsldm/core#maturityDate"),
    ("metricOf", "https://w3id.org/fsldm/core#metricOf"),
    ("metricType", "https://w3id.org/fsldm/core#metricType"),
    ("metricValue", "https://w3id.org/fsldm/core#metricValue"),
    ("observationDate", "https://w3id.org/fsldm/core#observationDate"),
    ("ofObject", "https://w3id.org/fsldm/core#ofObject"),
    ("ofSubject", "https://w3id.org/fsldm/core#ofSubject"),
    ("originationDate", "https://w3id.org/fsldm/core#originationDate"),
    ("partyId", "https://w3id.org/fsldm/core#partyId"),
    ("partyOf", "https://w3id.org/fsldm/core#partyOf"),
    ("productId", "https://w3id.org/fsldm/core#productId"),
    ("productOf", "https://w3id.org/fsldm/core#productOf"),
    ("recordedAt", "https://w3id.org/fsldm/core#recordedAt"),
    ("sourceRecordId", "https://w3id.org/fsldm/core#sourceRecordId"),
    ("sourceSystem", "https://w3id.org/fsldm/core#sourceSystem"),
    ("unitOfMeasure", "https://w3id.org/fsldm/core#unitOfMeasure"),
    ("validFrom", "https://w3id.org/fsldm/core#validFrom"),
    ("validUntil", "https://w3id.org/fsldm/core#validUntil"),
    ("containsEvent", "https://w3id.org/fsldm/event#containsEvent"),
    ("eventAmount", "https://w3id.org/fsldm/event#eventAmount"),
    ("eventPostedTimestamp", "https://w3id.org/fsldm/event#eventPostedTimestamp"),
    ("eventSubtype", "https://w3id.org/fsldm/event#eventSubtype"),
    ("eventTimestamp", "https://w3id.org/fsldm/event#eventTimestamp"),
    ("eventType", "https://w3id.org/fsldm/event#eventType"),
    ("ofEvent", "https://w3id.org/fsldm/event#ofEvent"),
    ("creditAmount", "https://w3id.org/fsldm/finance#creditAmount"),
    ("debitAmount", "https://w3id.org/fsldm/finance#debitAmount"),
    ("glAccountNumber", "https://w3id.org/fsldm/finance#glAccountNumber"),
    ("lineNumber", "https://w3id.org/fsldm/finance#lineNumber"),
    ("ofExposureAgreement", "https://w3id.org/fsldm/finance#ofExposureAgreement"),
    ("ofJournalEntry", "https://w3id.org/fsldm/finance#ofJournalEntry"),
    ("parentGLAccount", "https://w3id.org/fsldm/finance#parentGLAccount"),
    ("postedAccount", "https://w3id.org/fsldm/finance#postedAccount"),
    ("coverageOfAgreement", "https://w3id.org/fsldm/insurance#coverageOfAgreement"),
    ("insuresAsset", "https://w3id.org/fsldm/insurance#insuresAsset"),
    ("underwritingClassOf", "https://w3id.org/fsldm/insurance#underwritingClassOf"),
    ("portfolioOfParty", "https://w3id.org/fsldm/investment#portfolioOfParty"),
    ("positionInPortfolio", "https://w3id.org/fsldm/investment#positionInPortfolio"),
    ("quotedProduct", "https://w3id.org/fsldm/investment#quotedProduct"),
    ("administrativeCode", "https://w3id.org/fsldm/location#administrativeCode"),
    ("hasLocator", "https://w3id.org/fsldm/location#hasLocator"),
    ("latitude", "https://w3id.org/fsldm/location#latitude"),
    ("locatorUsage", "https://w3id.org/fsldm/location#locatorUsage"),
    ("longitude", "https://w3id.org/fsldm/location#longitude"),
    ("employedAssociate", "https://w3id.org/fsldm/org#employedAssociate"),
    ("employingOrganization", "https://w3id.org/fsldm/org#employingOrganization"),
    ("occupiesPosition", "https://w3id.org/fsldm/org#occupiesPosition"),
    ("partOfOrganization", "https://w3id.org/fsldm/org#partOfOrganization"),
    ("attritionDate", "https://w3id.org/fsldm/party#attritionDate"),
    ("classifiedParty", "https://w3id.org/fsldm/party#classifiedParty"),
    ("financialDocumentOfParty", "https://w3id.org/fsldm/party#financialDocumentOfParty"),
    ("hasGroupMember", "https://w3id.org/fsldm/party#hasGroupMember"),
    ("ofParty", "https://w3id.org/fsldm/party#ofParty"),
    ("partySince", "https://w3id.org/fsldm/party#partySince"),
    ("ratingLowerBound", "https://w3id.org/fsldm/party#ratingLowerBound"),
    ("ratingUpperBound", "https://w3id.org/fsldm/party#ratingUpperBound"),
    ("relatedFrom", "https://w3id.org/fsldm/party#relatedFrom"),
    ("relatedTo", "https://w3id.org/fsldm/party#relatedTo"),
    ("riskGradePrecedes", "https://w3id.org/fsldm/party#riskGradePrecedes"),
    ("riskGradeReviewDate", "https://w3id.org/fsldm/party#riskGradeReviewDate"),
    ("eligibilityCondition", "https://w3id.org/fsldm/product#eligibilityCondition"),
    ("featureCode", "https://w3id.org/fsldm/product#featureCode"),
    ("featureValue", "https://w3id.org/fsldm/product#featureValue"),
    ("hasPackageComponent", "https://w3id.org/fsldm/product#hasPackageComponent"),
    ("leewayLowerBound", "https://w3id.org/fsldm/product#leewayLowerBound"),
    ("leewayUpperBound", "https://w3id.org/fsldm/product#leewayUpperBound"),
    ("memberProduct", "https://w3id.org/fsldm/product#memberProduct"),
    ("parentProductGroup", "https://w3id.org/fsldm/product#parentProductGroup"),
)

AUDIT_COLUMNS = frozenset({"data_source", "fixture", "created_at"})
DPD_COLUMNS = frozenset(
    {"dpd", "dpd_start", "dpd_end", "overdue_days", "other_facility_dpd_90plus"}
)
LOCAL_KEY_SUFFIXES = ("_id", "_no", "_key")

SOURCE_UNAVAILABLE = "E_DICT_SOURCE_UNREACHABLE"
SOURCE_UNKNOWN = "E_DICT_SOURCE_UNKNOWN"
TABLE_NOT_FOUND = "E_DICT_TABLE_NOT_FOUND"


def normalize_name(value: str) -> str:
    """Lowercase + strip non-alphanumerics: account_id and accountId collide."""
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def local_name(iri: str) -> str:
    return re.split(r"[#/]", iri or "")[-1] or ""


def build_property_index(
    properties: Iterable[tuple[str, str]] | None = None,
) -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for name, iri in sorted(properties or STATIC_PROPERTIES, key=lambda item: item[1]):
        local = name or local_name(iri)
        index.setdefault(normalize_name(local), {"iri": iri, "local": local})
    return index


def unbound_reason(table: str, column: str, key: str) -> str:
    if column in AUDIT_COLUMNS:
        return "系统/审计列（data_source/fixture/created_at），本体无对应属性"
    if column in DPD_COLUMNS:
        return (
            "本体 T-Box 无逾期天数属性（无 daysPastDue/overdueDays），"
            "不臆造绑定，按未绑定保留"
        )
    if column == "as_of":
        return "观察时点列；本体仅有 observationDate，名称不相等，未自动绑定"
    if column == "account_id":
        return "本体 T-Box 无 accountId 属性，账号按本地业务编号保留未绑定"
    if column.endswith(LOCAL_KEY_SUFFIXES):
        return "事实表本地编号列，本体无同名属性"
    return f"名称未命中本体属性（归一化 '{key}'）"


def resolve_binding(
    table: str,
    column: str,
    property_index: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    index = property_index if property_index is not None else build_property_index()
    explicit = EXPLICIT_BINDINGS.get((table, column)) or EXPLICIT_BINDINGS.get(("*", column))
    if explicit:
        return {
            "propertyIri": explicit["iri"],
            "bindingMethod": "explicit",
            "confidence": float(explicit["confidence"]),
            "bindingNote": explicit["note"],
        }
    key = normalize_name(column)
    match = index.get(key)
    if match:
        return {
            "propertyIri": match["iri"],
            "bindingMethod": "name_match",
            "confidence": NAME_MATCH_CONFIDENCE,
            "bindingNote": f"名称归一化匹配：{column} ≈ {match['local']}",
        }
    return {
        "propertyIri": None,
        "bindingMethod": "none",
        "confidence": None,
        "bindingNote": unbound_reason(table, column, key),
    }


def _source_error(kind: str, reason: str, details: dict[str, Any] | None = None) -> PortError:
    payload = {"sourceKind": kind, "reason": reason}
    payload.update(details or {})
    return PortError(
        code="Unavailable",
        message=f"dictionary source '{kind}' is unreachable: {reason}",
        provider=kind,
        provider_code=SOURCE_UNAVAILABLE,
        retryable=True,
        details=payload,
    )


def introspect_pg(metadata: Any, schema: str, tables: Sequence[str]) -> list[dict[str, Any]]:
    rows = metadata.query(
        """
        SELECT c.table_name,
               c.column_name,
               c.data_type,
               c.is_nullable,
               c.ordinal_position,
               d.description AS comment
          FROM information_schema.columns c
          LEFT JOIN pg_catalog.pg_namespace n
                 ON n.nspname = c.table_schema
          LEFT JOIN pg_catalog.pg_class t
                 ON t.relname = c.table_name AND t.relnamespace = n.oid
          LEFT JOIN pg_catalog.pg_attribute a
                 ON a.attrelid = t.oid AND a.attname = c.column_name AND a.attnum > 0
          LEFT JOIN pg_catalog.pg_description d
                 ON d.objoid = a.attrelid
                AND d.classoid = 'pg_class'::regclass
                AND d.objsubid = a.attnum
         WHERE c.table_schema = %s AND c.table_name = ANY(%s)
         ORDER BY c.table_name, c.ordinal_position
        """,
        (schema, list(tables)),
    )
    return [
        {
            "table": row["table_name"],
            "column": row["column_name"],
            "dataType": row.get("data_type") or "",
            "isNullable": str(row.get("is_nullable", "YES")).upper() == "YES",
            "comment": row.get("comment"),
            "ordinal": row.get("ordinal_position"),
        }
        for row in rows
    ]


def introspect_mysql(
    dsn: str | None,
    schema: str,
    tables: Sequence[str],
) -> list[dict[str, Any]]:
    """MySQL pathway. No local MySQL: fail with E_DICT_SOURCE_UNREACHABLE."""
    if not dsn:
        raise _source_error("mysql", "no MySQL DSN configured (PLATFORM_CATALOG_MYSQL_DSN)")
    try:
        import pymysql  # type: ignore
    except Exception as exc:  # noqa: BLE001 - driver absence is a source failure
        raise _source_error("mysql", f"pymysql driver unavailable: {exc}") from exc
    parsed = urlparse(dsn)
    try:  # pragma: no cover - needs live MySQL
        connection = pymysql.connect(
            host=parsed.hostname or "127.0.0.1",
            port=parsed.port or 3306,
            user=unquote(parsed.username or ""),
            password=unquote(parsed.password or ""),
            database=parsed.path.lstrip("/") or schema,
            autocommit=True,
        )
    except Exception as exc:  # pragma: no cover - needs live MySQL
        raise _source_error("mysql", f"connect failed: {exc}") from exc
    try:
        with connection.cursor() as cursor:  # pragma: no cover - needs live MySQL
            placeholders = ", ".join(["%s"] * len(tables))
            cursor.execute(
                "SELECT table_name, column_name, column_type, is_nullable, "
                "ordinal_position, column_comment "
                "FROM information_schema.columns "
                f"WHERE table_schema = %s AND table_name IN ({placeholders}) "
                "ORDER BY table_name, ordinal_position",
                (schema, *tables),
            )
            rows = cursor.fetchall()
    finally:
        connection.close()
    return [
        {
            "table": row[0],
            "column": row[1],
            "dataType": row[2],
            "isNullable": str(row[3]).upper() == "YES",
            "comment": row[5] or None,
            "ordinal": row[4],
        }
        for row in rows
    ]  # pragma: no cover - needs live MySQL


def introspect_glue(
    adapter: Callable[[str, Sequence[str]], list[dict[str, Any]]] | None,
    schema: str,
    tables: Sequence[str],
) -> list[dict[str, Any]]:
    """Glue pathway: only a configured catalog adapter can answer."""
    if adapter is None:
        raise _source_error("glue", "catalog.glue adapter is not configured")
    return list(adapter(schema, list(tables)))


def live_property_index(runtime: Any) -> tuple[dict[str, dict[str, str]] | None, str | None]:
    """Read property IRIs from the published T-Box; None means use static."""
    try:
        pointer = runtime.ontology.current()
        if not pointer:
            return None, None
        graph = str(pointer["graph"])
        rows = runtime.graph.query(
            f"""
            SELECT ?p FROM <{graph}> WHERE {{
              VALUES ?kind {{
                <http://www.w3.org/2002/07/owl#ObjectProperty>
                <http://www.w3.org/2002/07/owl#DatatypeProperty>
                <http://www.w3.org/2002/07/owl#AnnotationProperty>
              }}
              ?p a ?kind .
            }}
            LIMIT 5000
            """
        ).get("bindings", [])
        properties = []
        for row in rows:
            value = row.get("p")
            if isinstance(value, dict):
                iri = str(value.get("value") or value.get("iri") or "")
            else:
                iri = str(value or "")
            if iri:
                properties.append((local_name(iri), iri))
        if not properties:
            return None, pointer.get("versionId")
        return build_property_index(properties), pointer.get("versionId")
    except Exception:  # noqa: BLE001 - dictionary still works offline from static list
        return None, None


class CatalogRepository:
    """Thin PostgreSQL layer for ``platform.data_dictionary``."""

    COLUMNS = (
        "catalog_name, schema_name, table_name, column_name, data_type, "
        "is_nullable, comment, source_kind, property_iri, binding_method, "
        "confidence, binding_note, observed_at"
    )

    def __init__(self, metadata: Any) -> None:
        self._metadata = metadata

    def list(
        self,
        filters: dict[str, Any],
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        where, params = self._where(filters)
        total = self._metadata.query(
            "SELECT COUNT(*) AS n FROM platform.data_dictionary" + where, params
        )
        rows = self._metadata.query(
            f"SELECT {self.COLUMNS} FROM platform.data_dictionary{where} "
            "ORDER BY table_name, column_name LIMIT %s OFFSET %s",
            (*params, limit, offset),
        )
        return rows, int(total[0]["n"]) if total else 0

    def table_rows(self, catalog: str, schema: str, table: str) -> list[dict[str, Any]]:
        return self._metadata.query(
            f"SELECT {self.COLUMNS} FROM platform.data_dictionary "
            "WHERE catalog_name = %s AND schema_name = %s AND table_name = %s "
            "ORDER BY column_name",
            (catalog, schema, table),
        )

    def distinct_tables(self, catalog: str, schema: str) -> list[str]:
        rows = self._metadata.query(
            "SELECT DISTINCT table_name FROM platform.data_dictionary "
            "WHERE catalog_name = %s AND schema_name = %s ORDER BY table_name",
            (catalog, schema),
        )
        return [row["table_name"] for row in rows]

    def existing(self, catalog: str, schema: str, tables: Sequence[str]) -> dict[tuple, dict]:
        rows = self._metadata.query(
            f"SELECT {self.COLUMNS} FROM platform.data_dictionary "
            "WHERE catalog_name = %s AND schema_name = %s AND table_name = ANY(%s)",
            (catalog, schema, list(tables)),
        )
        return {
            (row["catalog_name"], row["schema_name"], row["table_name"], row["column_name"]): row
            for row in rows
        }

    def upsert(self, entry: dict[str, Any], mark_observed: bool = True) -> None:
        self._metadata.execute(
            """
            INSERT INTO platform.data_dictionary
              (catalog_name, schema_name, table_name, column_name, data_type,
               is_nullable, comment, source_kind, property_iri, binding_method,
               confidence, binding_note, observed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (catalog_name, schema_name, table_name, column_name)
            DO UPDATE SET
              data_type = EXCLUDED.data_type,
              is_nullable = EXCLUDED.is_nullable,
              comment = EXCLUDED.comment,
              source_kind = EXCLUDED.source_kind,
              property_iri = EXCLUDED.property_iri,
              binding_method = EXCLUDED.binding_method,
              confidence = EXCLUDED.confidence,
              binding_note = EXCLUDED.binding_note,
              observed_at = CASE WHEN %s THEN now()
                                 ELSE platform.data_dictionary.observed_at END
            """,
            (
                entry["catalog"], entry["schema"], entry["table"], entry["column"],
                entry["dataType"], entry["isNullable"], entry.get("comment"),
                entry["sourceKind"], entry.get("propertyIri"), entry["bindingMethod"],
                entry.get("confidence"), entry.get("bindingNote"), mark_observed,
            ),
        )

    def max_observed(self, catalog: str, schema: str) -> str | None:
        rows = self._metadata.query(
            "SELECT MAX(observed_at) AS ts FROM platform.data_dictionary "
            "WHERE catalog_name = %s AND schema_name = %s",
            (catalog, schema),
        )
        value = rows[0]["ts"] if rows else None
        return value.isoformat() if value is not None else None

    def _where(self, filters: dict[str, Any]) -> tuple[str, tuple]:
        clauses: list[str] = []
        params: list[Any] = []
        for field, column in (
            ("catalog", "catalog_name"),
            ("schema", "schema_name"),
            ("table", "table_name"),
            ("column", "column_name"),
            ("sourceKind", "source_kind"),
            ("bindingMethod", "binding_method"),
        ):
            value = filters.get(field)
            if value:
                clauses.append(f"{column} = %s")
                params.append(value)
        query = (filters.get("q") or "").strip()
        if query:
            clauses.append(
                "(table_name ILIKE %s OR column_name ILIKE %s "
                "OR COALESCE(comment, '') ILIKE %s)"
            )
            params.extend([f"%{query}%"] * 3)
        return (" WHERE " + " AND ".join(clauses)) if clauses else "", tuple(params)


class CatalogService:
    def __init__(
        self,
        runtime: Any,
        *,
        repository: CatalogRepository | None = None,
        mysql_dsn: str | None = None,
        glue_adapter: Callable[[str, Sequence[str]], list[dict[str, Any]]] | None = None,
        pg_introspector: Callable[[str, Sequence[str]], list[dict[str, Any]]] | None = None,
    ) -> None:
        self._runtime = runtime
        self._metadata = runtime.metadata
        self._repo = repository or CatalogRepository(runtime.metadata)
        self._mysql_dsn = mysql_dsn if mysql_dsn is not None else os.environ.get(
            "PLATFORM_CATALOG_MYSQL_DSN"
        )
        self._glue_adapter = glue_adapter
        self._pg_introspector = pg_introspector

    def list(self, filters: dict[str, Any], limit: int = 20, offset: int = 0) -> dict[str, Any]:
        limit = max(1, min(int(limit), 200))
        offset = max(0, int(offset))
        rows, total = self._repo.list(filters, limit, offset)
        return {
            "items": [self._row_json(row) for row in rows],
            "count": len(rows),
            "total": total,
            "limit": limit,
            "offset": offset,
            "filters": filters,
            "source": "data_dictionary",
        }

    def table(self, table: str, catalog: str = "platform", schema: str = "platform") -> dict[str, Any]:
        rows = self._repo.table_rows(catalog, schema, table)
        if not rows:
            raise PortError(
                code="NotFound",
                message=f"dictionary table not found: {table}",
                provider="platform",
                provider_code=TABLE_NOT_FOUND,
                details={"table": table, "catalog": catalog, "schema": schema},
            )
        items = [self._row_json(row) for row in rows]
        binding = {method: 0 for method in BINDING_METHODS}
        for item in items:
            binding[item["bindingMethod"]] = binding.get(item["bindingMethod"], 0) + 1
        return {
            "catalog": catalog,
            "schema": schema,
            "table": table,
            "columns": items,
            "count": len(items),
            "binding": binding,
            "sourceKinds": sorted({item["sourceKind"] for item in items}),
            "observedAt": max(item["observedAt"] for item in items),
            "source": "data_dictionary",
        }

    def refresh(
        self,
        sources: Sequence[str] | None = None,
        catalog: str = "platform",
        schema: str = "platform",
        tables: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        kinds = list(sources or ("pg",))
        unknown = [kind for kind in kinds if kind not in SOURCE_KINDS]
        if unknown:
            raise PortError(
                code="InvalidArgument",
                message=f"unsupported dictionary source: {unknown}",
                provider="platform",
                provider_code=SOURCE_UNKNOWN,
                details={"unknown": unknown, "allowed": list(SOURCE_KINDS)},
            )
        table_list = list(tables or FACT_TABLES)
        columns: list[dict[str, Any]] = []
        for kind in kinds:
            columns.extend(self._introspect_source(kind, schema, table_list))

        property_index, ontology_version = live_property_index(self._runtime)
        if property_index is None:
            property_index = build_property_index()

        entries = []
        for item in columns:
            binding = resolve_binding(item["table"], item["column"], property_index)
            entries.append(
                {
                    "catalog": catalog,
                    "schema": schema,
                    "table": item["table"],
                    "column": item["column"],
                    "dataType": item["dataType"],
                    "isNullable": bool(item["isNullable"]),
                    "comment": item.get("comment") or None,
                    "sourceKind": item["sourceKind"],
                    **binding,
                }
            )

        existing = self._repo.existing(catalog, schema, table_list)
        inserted = updated = unchanged = 0
        for entry in entries:
            key = (catalog, schema, entry["table"], entry["column"])
            previous = existing.get(key)
            if previous is None:
                inserted += 1
                mark = True
            else:
                changed = any(
                    self._differs(previous, field, entry[field])
                    for field in (
                        "dataType", "isNullable", "comment", "sourceKind",
                        "propertyIri", "bindingMethod", "confidence", "bindingNote",
                    )
                )
                if changed:
                    updated += 1
                    mark = True
                else:
                    unchanged += 1
                    mark = False
            self._repo.upsert(entry, mark_observed=mark)

        by_source = {kind: 0 for kind in kinds}
        binding_counts = {method: 0 for method in BINDING_METHODS}
        for entry in entries:
            by_source[entry["sourceKind"]] = by_source.get(entry["sourceKind"], 0) + 1
            binding_counts[entry["bindingMethod"]] = (
                binding_counts.get(entry["bindingMethod"], 0) + 1
            )
        return {
            "catalog": catalog,
            "schema": schema,
            "sources": kinds,
            "ontologyVersion": ontology_version,
            "processed": len(entries),
            "inserted": inserted,
            "updated": updated,
            "unchanged": unchanged,
            "bySourceKind": by_source,
            "binding": binding_counts,
            "observedAt": self._repo.max_observed(catalog, schema)
            or datetime.now(timezone.utc).isoformat(),
            "source": "data_dictionary",
        }

    def _introspect_source(
        self, kind: str, schema: str, tables: Sequence[str]
    ) -> list[dict[str, Any]]:
        if kind == "pg":
            raw = (
                self._pg_introspector(schema, tables)
                if self._pg_introspector
                else introspect_pg(self._metadata, schema, tables)
            )
            return [{**item, "sourceKind": "pg"} for item in raw]
        if kind == "mysql":
            raw = introspect_mysql(self._mysql_dsn, schema, tables)
            return [{**item, "sourceKind": "mysql"} for item in raw]
        raw = introspect_glue(self._glue_adapter, schema, tables)
        return [{**item, "sourceKind": "glue"} for item in raw]

    @staticmethod
    def _differs(previous: dict[str, Any], field: str, value: Any) -> bool:
        column = {
            "dataType": "data_type",
            "isNullable": "is_nullable",
            "comment": "comment",
            "sourceKind": "source_kind",
            "propertyIri": "property_iri",
            "bindingMethod": "binding_method",
            "confidence": "confidence",
            "bindingNote": "binding_note",
        }[field]
        old = previous.get(column)
        if field == "confidence":
            if old is None or value is None:
                return old != value
            return float(old) != float(value)
        if field == "isNullable":
            return bool(old) != bool(value)
        return old != value

    @staticmethod
    def _row_json(row: dict[str, Any]) -> dict[str, Any]:
        confidence = row.get("confidence")
        observed = row.get("observed_at")
        return {
            "catalog": row.get("catalog_name"),
            "schema": row.get("schema_name"),
            "table": row.get("table_name"),
            "column": row.get("column_name"),
            "dataType": row.get("data_type"),
            "isNullable": bool(row.get("is_nullable")),
            "comment": row.get("comment"),
            "sourceKind": row.get("source_kind"),
            "propertyIri": row.get("property_iri"),
            "bindingMethod": row.get("binding_method"),
            "confidence": None if confidence is None else round(float(confidence), 3),
            "bindingNote": row.get("binding_note"),
            "observedAt": observed.isoformat() if hasattr(observed, "isoformat") else observed,
        }
