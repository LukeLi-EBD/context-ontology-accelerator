"""``platform_core.ports.EnvSecretProvider`` -> ``coa_ports.SecretProvider``.

Signature difference: none. Both expose ``get(name: str) -> str``.

The real difference is the exception class. The platform provider raises
``platform_core.ports.PortError`` whose ``code`` is a PascalCase string
(``"NotFound"``) and which COA code cannot catch without importing the
platform package — exactly the leak plan §11.3 forbids. This shell maps the
platform error onto :class:`coa_ports.errors.PortError` with a closed
lowercase code and keeps ``provider_code`` for diagnostics only.

That is the whole adapter: ~50 lines, no business rules, no fallback.
"""

from __future__ import annotations

from coa_ports import PortError, PortErrorCode

_PLATFORM_TO_PORT_CODE = {
    "NotFound": PortErrorCode.NOT_FOUND,
    "InvalidArgument": PortErrorCode.INVALID_ARGUMENT,
    "Unavailable": PortErrorCode.UNAVAILABLE,
    "Timeout": PortErrorCode.TIMEOUT,
    "Conflict": PortErrorCode.CONFLICT,
    "Unsupported": PortErrorCode.UNSUPPORTED,
    "Internal": PortErrorCode.INTERNAL,
}


class EnvSecretShell:
    """Adapt a platform secret provider to the COA ``SecretProvider`` port.

    Args:
        inner: A platform provider exposing ``get(name) -> str``. Type is
            ``object`` on purpose: importing the platform class here would
            pull the whole adapter stack into every importer of this module.
        provider: Provider name recorded on translated errors.
    """

    def __init__(self, inner: object, *, provider: str = "env") -> None:
        getter = getattr(inner, "get", None)
        if not callable(getter):
            raise TypeError("inner must expose a callable get(name)")
        self._inner = inner
        self._provider = provider

    def get(self, name: str) -> str:
        """Return the secret value; never log or echo it in an error."""
        try:
            return self._inner.get(name)  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001 - the platform error class is not importable here
            raise self._translate(name, exc) from exc

    # ── internals ───────────────────────────────────────────────────────────

    def _translate(self, name: str, exc: Exception) -> PortError:
        # The platform ``PortError`` exposes ``code`` / ``provider`` /
        # ``provider_code`` / ``details``. Anything else is an unexpected
        # failure and must not masquerade as "secret not found".
        platform_code = getattr(exc, "code", "")
        if not isinstance(platform_code, str) or platform_code not in _PLATFORM_TO_PORT_CODE:
            return PortError(
                PortErrorCode.INTERNAL,
                "secret provider failed",
                provider=self._provider,
                provider_code=type(exc).__name__,
                details={"name": name},
            )
        publishable_details = {"name": name}
        details = getattr(exc, "details", None)
        if isinstance(details, dict):
            for key, value in details.items():
                if key != "value":
                    publishable_details[key] = value
        return PortError(
            _PLATFORM_TO_PORT_CODE[platform_code],
            str(getattr(exc, "message", "") or f"secret {name} lookup failed"),
            provider=str(getattr(exc, "provider", "") or self._provider),
            provider_code=str(getattr(exc, "provider_code", "") or ""),
            details=publishable_details,
        )


__all__ = ["EnvSecretShell"]
