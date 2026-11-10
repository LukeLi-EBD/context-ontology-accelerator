"""C2-1 quota provider: daily token/request counters in PostgreSQL (design 87).

Scope of the lightweight version:

- counters are per ``(UTC day, scope)``; they survive a process restart because
  they live in ``platform.quota_usage`` (migration V50);
- a limit of ``0`` means unlimited; counting still happens;
- ``check`` never writes (it only predicts), ``record`` is the single atomic
  upsert that increments tokens/requests;
- over a limit ``check`` returns ``allowed=false`` with
  ``reason=E_QUOTA_EXCEEDED`` and ``action`` taken from ``quota.on_exceed``
  (``degrade`` by default, ``reject`` opt-in).

Known limitation (documented, not hidden): check-then-record is not a
reservation, so two concurrent calls can both pass the last remaining unit.
The counter itself is atomic and never loses an increment.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Callable

from ..config import QuotaConfig
from ..errors import PortError
from ..ports import Manifest, MetadataStorePort, QuotaDecision

QUOTA_EXCEEDED = "E_QUOTA_EXCEEDED"


def today_utc() -> date:
    return datetime.now(timezone.utc).date()


class SimpleQuota:
    port = "QuotaPort"

    def __init__(
        self,
        config: QuotaConfig,
        metadata: MetadataStorePort,
        clock: Callable[[], date] | None = None,
    ) -> None:
        self._config = config
        self._meta = metadata
        self._clock = clock or today_utc

    def manifest(self) -> Manifest:
        return Manifest(
            provider="simple",
            port=self.port,
            capabilities=["quota.check", "quota.record", "quota.status"],
            limits={
                "daily_token_limit": self._config.daily_token_limit,
                "daily_request_limit": self._config.daily_request_limit,
                "on_exceed": self._config.on_exceed,
            },
            notes={
                "slice": "C2-1",
                "storage": "platform.quota_usage (V50)",
                "window": "UTC day",
                "counted": True,
            },
        )

    # ---- port surface ----------------------------------------------------

    def check(self, scope: str, units: int = 1) -> QuotaDecision:
        scope = self._scope(scope)
        units = max(0, int(units))
        day = self._clock()
        row = self._read(day, scope)
        used_tokens = int(row.get("tokens") or 0)
        used_requests = int(row.get("requests") or 0)
        limit_tokens = self._limit(self._config.daily_token_limit)
        limit_requests = self._limit(self._config.daily_request_limit)
        over_tokens = limit_tokens is not None and used_tokens + units > limit_tokens
        # check() describes one more request (record() increments requests by 1).
        over_requests = limit_requests is not None and used_requests + 1 > limit_requests
        allowed = not (over_tokens or over_requests)
        return QuotaDecision(
            allowed=allowed,
            action="allow" if allowed else self._config.on_exceed,
            reason=None if allowed else QUOTA_EXCEEDED,
            provider="simple",
            scope=scope,
            units=units,
            used_tokens=used_tokens,
            used_requests=used_requests,
            limit_tokens=limit_tokens,
            limit_requests=limit_requests,
            remaining_tokens=(
                None if limit_tokens is None else max(0, limit_tokens - used_tokens)
            ),
            remaining_requests=(
                None if limit_requests is None else max(0, limit_requests - used_requests)
            ),
            day=day.isoformat(),
        )

    def record(self, scope: str, units: int, cost: float = 0.0) -> None:
        scope = self._scope(scope)
        day = self._clock()
        self._meta.execute(
            """
            INSERT INTO platform.quota_usage (quota_day, scope, tokens, requests, cost_units, updated_at)
            VALUES (%s, %s, %s, 1, %s, now())
            ON CONFLICT (quota_day, scope) DO UPDATE
               SET tokens = platform.quota_usage.tokens + EXCLUDED.tokens,
                   requests = platform.quota_usage.requests + EXCLUDED.requests,
                   cost_units = platform.quota_usage.cost_units + EXCLUDED.cost_units,
                   updated_at = now()
            """,
            (day, scope, max(0, int(units)), max(0.0, float(cost))),
        )

    def status(self, scope: str) -> dict[str, Any]:
        scope = self._scope(scope)
        decision = self.check(scope, 0)
        row = self._read(self._clock(), scope)
        cost = float(row.get("cost_units") or 0.0)
        return {
            "provider": "simple",
            "scope": scope,
            "counted": True,
            "day": decision.day,
            "window": "UTC day",
            "tokens": self._block(decision.used_tokens, decision.limit_tokens, decision.remaining_tokens),
            "requests": self._block(
                decision.used_requests, decision.limit_requests, decision.remaining_requests
            ),
            "cost": {"used": cost, "unit": "provider_units"},
            "onExceed": self._config.on_exceed,
        }

    # ---- internals -------------------------------------------------------

    @staticmethod
    def _block(used: int, limit: int | None, remaining: int | None) -> dict[str, Any]:
        return {
            "used": used,
            "limit": limit,
            "remaining": remaining,
            "exceeded": limit is not None and used >= limit,
        }

    @staticmethod
    def _limit(value: int) -> int | None:
        return None if int(value) <= 0 else int(value)

    def _scope(self, scope: str) -> str:
        text = str(scope or "").strip()
        if not text:
            raise PortError(
                code="InvalidArgument",
                message="quota scope must be a non-empty string",
                provider="simple",
                provider_code="E_QUOTA_SCOPE_INVALID",
            )
        return text

    def _read(self, day: date, scope: str) -> dict[str, Any]:
        rows = self._meta.query(
            """
            SELECT tokens, requests, cost_units
              FROM platform.quota_usage
             WHERE quota_day = %s AND scope = %s
            """,
            (day, scope),
        )
        return rows[0] if rows else {}
