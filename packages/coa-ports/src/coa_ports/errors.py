"""Port error contract shared by every outbound port.

Ruling (plan §11.3): callers translate a ``PortError`` into their own
context's error. ``provider_code`` is diagnostic only and must never reach a
customer-facing contract. ``code`` is restricted to the seven values below;
providers that need finer distinctions put them in ``provider_code``.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any


class PortErrorCode(StrEnum):
    """The only error classes a port may expose to its caller."""

    NOT_FOUND = "not_found"
    UNAVAILABLE = "unavailable"
    TIMEOUT = "timeout"
    INVALID_ARGUMENT = "invalid_argument"
    CONFLICT = "conflict"
    UNSUPPORTED = "unsupported"
    INTERNAL = "internal"


class PortError(Exception):
    """A port failure with a stable, context-neutral code.

    Attributes:
        code: One of :class:`PortErrorCode`. This is what callers switch on.
        message: Human-readable, safe to log. Not necessarily client-safe.
        provider: Provider name selected by the composition root, e.g. ``pgvector``.
        provider_code: The provider's own code (``E_EMBED_DIM_MISMATCH``). Diagnostics only.
        details: Structured context (ids, limits). Must not carry secrets.
    """

    def __init__(
        self,
        code: PortErrorCode,
        message: str,
        *,
        provider: str = "",
        provider_code: str = "",
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.provider = provider
        self.provider_code = provider_code
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        """Diagnostic projection for logs and trace steps (never for a customer body)."""
        return {
            "code": str(self.code),
            "message": self.message,
            "provider": self.provider,
            "provider_code": self.provider_code,
            "details": dict(self.details),
        }


__all__ = ["PortError", "PortErrorCode"]
