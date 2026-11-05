"""Metric definition registry (basis v3) with the publishability guard.

The platform has no metric fact store, so "output" here is the governed
definition card: the v3 fields plus the provenance envelope. A metric that
cannot be released never reaches the caller, regardless of whether a value
happens to exist elsewhere.
"""

from __future__ import annotations

from typing import Any

from .adapters.metadata_pg import MetadataPg
from .errors import PortError

PUBLISH_CODE = "E_METRIC_NOT_PUBLISHABLE"
DISABLED_CODE = "E_METRIC_FORMULA_DISABLED"
NOT_FOUND_CODE = "E_METRIC_NOT_FOUND"

_COLUMNS = (
    "metric_id, name_zh, domain, evidence_basis, publishable, inference, "
    "formula_disabled, missing, evidence_status, note"
)


def _card(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "metricId": row["metric_id"],
        "name": row["name_zh"],
        "domain": row["domain"],
        "evidenceBasis": row["evidence_basis"],
        "publishable": row["publishable"],
        "inference": row["inference"],
        "formulaDisabled": row["formula_disabled"],
        "missing": row["missing"],
        "evidenceStatus": row["evidence_status"],
        "note": row["note"],
    }


def _reject(metric_id: str, missing: str | None, message: str) -> PortError:
    return PortError(
        code="PermissionDenied",
        message=message,
        provider="platform",
        provider_code=PUBLISH_CODE,
        details={"metricId": metric_id, "missing": missing or "source"},
    )


class MetricService:
    port = "MetricService"

    def __init__(self, metadata: MetadataPg) -> None:
        self._meta = metadata

    def list(self, domain: str | None = None) -> list[dict[str, Any]]:
        if domain is None:
            rows = self._meta.query(
                f"SELECT {_COLUMNS} FROM platform.metric_definition ORDER BY metric_id"
            )
        else:
            rows = self._meta.query(
                f"SELECT {_COLUMNS} FROM platform.metric_definition "
                "WHERE domain = %s ORDER BY metric_id",
                (domain,),
            )
        return [_card(row) for row in rows]

    def get(self, metric_id: str) -> dict[str, Any]:
        rows = self._meta.query(
            f"SELECT {_COLUMNS} FROM platform.metric_definition WHERE metric_id = %s",
            (metric_id,),
        )
        if not rows:
            raise PortError(
                code="NotFound",
                message=f"unknown metric: {metric_id}",
                provider="platform",
                provider_code=NOT_FOUND_CODE,
                details={"metricId": metric_id},
            )
        return _card(rows[0])

    def output(self, metric_id: str, internal: bool = False) -> dict[str, Any]:
        """Return the governed definition card, or refuse with a typed error."""
        row = self.get(metric_id)
        if row["formulaDisabled"]:
            raise PortError(
                code="PolicyRejected",
                message=f"metric formula is disabled: {metric_id}",
                provider="platform",
                provider_code=DISABLED_CODE,
                details={"metricId": metric_id, "missing": "formula"},
            )
        if row["evidenceBasis"] == "none":
            raise _reject(metric_id, row["missing"], "metric has no evidence basis")
        if not row["publishable"] and not internal:
            raise _reject(
                metric_id,
                row["missing"] or "regulatory_source",
                "metric is not publishable externally",
            )
        payload = dict(row)
        payload["source"] = "INDUSTRY" if row["evidenceBasis"] == "industry" else "REGULATORY"
        payload["outputType"] = "definition"
        return payload
