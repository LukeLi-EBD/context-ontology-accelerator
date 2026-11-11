"""C2-2 quota provider skeleton (recognised but not assembled yet).

``quota.provider=full`` is rejected at config load with
``E_PROVIDER_NOT_IMPLEMENTED``; this class exists so the port signature and
manifest stay defined and both implementations cannot drift (design 87 §4.3).

Every method raises explicitly. It returns no counters, no prices and no
placeholder rows: a skeleton must not look like it supports anything.

What C2-2 will add (not in this slice):

- quotas per user/tenant (``scope`` becomes ``user:<id>`` / ``tenant:<id>``
  with a hierarchy lookup), replacing the single daily counter;
- pricing: convert recorded provider units to money at
  ``quota.unit_price_per_1k_tokens`` (CNY per 1k tokens), per model;
- alerts: threshold events (``quota.alert_threshold_pct``) pushed to a
  webhook/log channel before the hard limit is hit;
- dashboard: aggregate usage per scope/day/model, with remaining budget;
- CSV export: the same aggregates as a downloadable report;
- per-endpoint rate limiting (``/answer``, ``/documents/*/extract``) instead of
  one global bucket. That needs a second dimension in the ledger and a
  request-class column.

Method-face difference vs ``simple``: the port surface (check/record/status)
stays byte-identical. ``full`` only adds fields to ``status`` (price, alert
state, per-endpoint breakdown) and interprets ``cost`` as money-bearing
provider units; no new port method may be added without updating design 59 and
both implementations together.
"""

from __future__ import annotations

from typing import Any

from ..errors import PortError
from ..ports import Manifest, QuotaDecision

NOT_IMPLEMENTED = "E_PROVIDER_NOT_IMPLEMENTED"


class FullQuota:
    """Placeholder: every call fails explicitly, no fake counters."""

    port = "QuotaPort"

    def manifest(self) -> Manifest:
        return Manifest(
            provider="full",
            port=self.port,
            capabilities=["quota.check", "quota.record", "quota.status"],
            notes={
                "status": "not_implemented",
                "slice": "C2-2",
                "pending": [
                    "per-user/tenant quota",
                    "unit price -> money per 1k tokens",
                    "threshold alerts",
                    "usage dashboard",
                    "CSV export",
                    "per-endpoint rate limiting",
                ],
            },
        )

    def _raise(self, method: str) -> Any:
        raise PortError(
            code="Unsupported",
            message=(
                f"quota.provider=full: {method} is a known provider but no adapter "
                "is assembled (C2-2)"
            ),
            provider="full",
            provider_code=NOT_IMPLEMENTED,
            details={"provider": "full", "slice": "C2-2", "method": method},
        )

    def check(self, *_args: Any, **_kwargs: Any) -> QuotaDecision:
        return self._raise("check")

    def record(self, *_args: Any, **_kwargs: Any) -> None:
        return self._raise("record")

    def status(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return self._raise("status")
