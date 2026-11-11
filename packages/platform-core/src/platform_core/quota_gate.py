"""Quota assembly seam and the LLM gate used by C2-1 (design 87 §5).

Scope in this build: the only LLM call site is ``ExtractionService``. The gate
wraps the LLM client, so an over-limit call is skipped and extraction keeps its
rules path (``degraded=true, reasons=["E_QUOTA_EXCEEDED"]``). Retrieval
endpoints do not call the LLM and therefore stay fully readable under quota.

``assembly.build_*`` uses :func:`build_quota`; unit tests use it directly to
check all three provider values without opening PostgreSQL.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from .adapters.quota_full import FullQuota
from .adapters.quota_off import OffQuota
from .adapters.quota_simple import SimpleQuota
from .config import QuotaConfig
from .errors import PortError
from .ports import Manifest, MetadataStorePort, QuotaDecision, QuotaPort

log = logging.getLogger(__name__)

QUOTA_EXCEEDED = "E_QUOTA_EXCEEDED"


def build_quota(config: QuotaConfig, metadata: MetadataStorePort) -> QuotaPort:
    """Assemble the configured quota provider (config already split the codes)."""
    if config.provider == "simple":
        return SimpleQuota(config, metadata)
    if config.provider == "full":
        # Unreachable through load_config (E_PROVIDER_NOT_IMPLEMENTED), kept so
        # the three-way switch has one assembly point like canvas.
        return FullQuota()
    return OffQuota(config)


class QuotaAwareLlm:
    """LLM adapter wrapper: check before the call, record the real usage after.

    ``complete_json`` keeps the inner adapter's error contract. On an exceeded
    budget it raises ``PortError`` with ``provider_code=E_QUOTA_EXCEEDED`` and
    never calls the inner client; ``action=degrade`` maps to
    ``ResourceExhausted`` (callers fall back), ``action=reject`` maps to
    ``PolicyRejected`` (the request fails).
    """

    port = "LLMClient"

    def __init__(
        self,
        inner: Any,
        quota: QuotaPort,
        scope: str = "global",
        chars_per_token: int = 4,
    ) -> None:
        self._inner = inner
        self._quota = quota
        self._scope = scope
        self._chars_per_token = max(1, int(chars_per_token))
        self.last_usage: dict[str, Any] | None = None

    def manifest(self) -> Manifest:
        base = self._inner.manifest()
        notes = dict(base.notes or {})
        notes.update({"quota_scope": self._scope, "quota_provider": self._quota.manifest().provider})
        base.notes = notes
        return base

    def configured(self) -> bool:
        return bool(self._inner.configured())

    def close(self) -> None:
        self._inner.close()

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        # An unconfigured LLM must keep failing exactly as before; quota does
        # not turn "no provider" into a different error.
        if not self.configured():
            return self._inner.complete_json(system, user)

        estimate = max(1, math.ceil((len(system) + len(user)) / self._chars_per_token))
        decision = self._quota.check(self._scope, estimate)
        if not decision.allowed:
            code = "PolicyRejected" if decision.action == "reject" else "ResourceExhausted"
            log.warning(
                "llm call skipped: quota exceeded",
                extra={"event": {"event": "quota_exceeded", "scope": self._scope, "action": decision.action}},
            )
            raise PortError(
                code=code,
                message=(
                    f"daily quota exceeded for scope={self._scope}: "
                    f"tokens {decision.used_tokens}/{decision.limit_tokens}, "
                    f"requests {decision.used_requests}/{decision.limit_requests}"
                ),
                provider=decision.provider,
                provider_code=QUOTA_EXCEEDED,
                retryable=False,
                details=decision.to_dict(),
            )

        result = self._inner.complete_json(system, user)
        usage = getattr(self._inner, "last_usage", None) or {}
        tokens = int(usage.get("prompt_tokens") or 0) + int(usage.get("completion_tokens") or 0)
        self.last_usage = usage or None
        # Counting is a guardrail, not a best-effort log: a database failure
        # propagates instead of silently losing the increment.
        self._quota.record(self._scope, tokens or estimate, cost=0.0)
        return result

    def usage_decision(self, units: int = 1) -> QuotaDecision:
        """Read-only probe kept for callers/tests; never writes."""
        return self._quota.check(self._scope, units)
