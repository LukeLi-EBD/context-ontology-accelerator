"""``platform_core.ports.EnvSecretProvider`` -> ``coa_ports.SecretProvider``.

Signature difference: none. Both expose ``get(name: str) -> str``.

The real difference is the exception class. The platform provider raises
``platform_core.ports.PortError`` whose ``code`` is a PascalCase string
(``"NotFound"``) and which COA code cannot catch without importing the
platform package — exactly the leak plan §11.3 forbids. This shell maps the
platform error onto :class:`coa_ports.errors.PortError` with a closed
lowercase code and keeps ``provider_code`` for diagnostics only.

That is the whole adapter: ~60 lines, no business rules, no fallback.
"""

from __future__ import annotations

from .errors import to_port_error


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
            raise to_port_error(
                exc,
                provider=self._provider,
                message=f"secret {name} lookup failed",
                details={"name": name},
            ) from exc


__all__ = ["EnvSecretShell"]
