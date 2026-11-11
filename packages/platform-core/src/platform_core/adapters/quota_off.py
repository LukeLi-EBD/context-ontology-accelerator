"""``quota.provider=off``: allow everything, never count (design 87 §4.1).

This is the default. It must not change any existing endpoint: there is no
database read/write and ``record`` is a no-op. A status call reports zeros and
``counted=false`` rather than inventing usage.
"""

from __future__ import annotations

from typing import Any

from ..config import QuotaConfig
from ..ports import Manifest, QuotaDecision
from .quota_simple import today_utc


class OffQuota:
    port = "QuotaPort"

    def __init__(self, config: QuotaConfig | None = None) -> None:
        self._config = config

    def manifest(self) -> Manifest:
        return Manifest(
            provider="off",
            port=self.port,
            capabilities=[],
            notes={"status": "disabled", "reason": "quota.provider=off", "counted": False},
        )

    def check(self, scope: str, units: int = 1) -> QuotaDecision:
        return QuotaDecision(
            allowed=True,
            action="allow",
            reason=None,
            provider="off",
            scope=scope,
            units=max(0, int(units)),
            day=today_utc().isoformat(),
        )

    def record(self, scope: str, units: int, cost: float = 0.0) -> None:
        return None

    def status(self, scope: str) -> dict[str, Any]:
        return {
            "provider": "off",
            "scope": scope,
            "counted": False,
            "day": today_utc().isoformat(),
            "window": "UTC day",
            "tokens": {"used": 0, "limit": None, "remaining": None, "exceeded": False},
            "requests": {"used": 0, "limit": None, "remaining": None, "exceeded": False},
            "cost": {"used": 0.0, "unit": "provider_units"},
            "onExceed": self._config.on_exceed if self._config else "degrade",
            "note": "quota.provider=off: no usage is recorded and no limit is enforced",
        }
