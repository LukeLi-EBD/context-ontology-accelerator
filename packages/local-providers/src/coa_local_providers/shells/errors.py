"""Translate a ``platform_core`` failure into the closed COA port error.

Every storage shell faces the same platform exception class, whose ``code`` is
a PascalCase string (``"NotFound"``). COA callers must not import the platform
package just to catch it (plan §11.3), so the mapping lives here once.

An unrecognised code is deliberately mapped to ``internal`` instead of being
matched by name: an unknown failure must not masquerade as ``not_found``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from coa_ports import PortError, PortErrorCode

PLATFORM_TO_PORT_CODE: Mapping[str, PortErrorCode] = {
    "NotFound": PortErrorCode.NOT_FOUND,
    "InvalidArgument": PortErrorCode.INVALID_ARGUMENT,
    "Unavailable": PortErrorCode.UNAVAILABLE,
    "Timeout": PortErrorCode.TIMEOUT,
    "Conflict": PortErrorCode.CONFLICT,
    "Unsupported": PortErrorCode.UNSUPPORTED,
    "Internal": PortErrorCode.INTERNAL,
}


def to_port_error(
    exc: Exception,
    *,
    provider: str,
    message: str,
    details: Mapping[str, Any] | None = None,
    drop: tuple[str, ...] = ("value",),
) -> PortError:
    """Return the COA error for ``exc``.

    Args:
        exc: A platform exception, or any unexpected exception.
        provider: Provider name used when the exception carries none.
        message: Fallback message when the exception has no ``message``.
        details: Context the caller already knows (ids); merged with the
            exception's own details.
        drop: Detail keys removed before publishing (secrets must never leak).

    Returns:
        A ``coa_ports.PortError`` whose ``code`` is one of the seven closed
        codes. ``provider_code`` is kept for diagnostics only.
    """
    merged: dict[str, Any] = dict(details or {})
    platform_details = getattr(exc, "details", None)
    if isinstance(platform_details, Mapping):
        for key, value in platform_details.items():
            if key not in drop:
                merged[key] = value

    code = getattr(exc, "code", "")
    if not isinstance(code, str) or code not in PLATFORM_TO_PORT_CODE:
        return PortError(
            PortErrorCode.INTERNAL,
            message or "provider failed",
            provider=provider,
            provider_code=str(code or type(exc).__name__),
            details=merged,
        )
    return PortError(
        PLATFORM_TO_PORT_CODE[code],
        str(getattr(exc, "message", "") or message),
        provider=str(getattr(exc, "provider", "") or provider),
        provider_code=str(getattr(exc, "provider_code", "") or ""),
        details=merged,
    )


__all__ = ["PLATFORM_TO_PORT_CODE", "to_port_error"]
