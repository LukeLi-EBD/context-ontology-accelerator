"""Explicit configuration failures. No silent fallback by design (plan §3).

Every error names the interface and config key so an operator can fix it
without reading source. None of these inherit from ``PortError``: they are
composition-root failures and must surface at startup, not be translated into
a client-facing contract error.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


class ConfigurationError(Exception):
    """Base for every composition-root failure."""

    code = "config_error"

    def __init__(
        self,
        message: str,
        *,
        interface: str = "",
        key: str = "",
        value: str = "",
        allowed: Sequence[str] = (),
        reason: str = "",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.interface = interface
        self.key = key
        self.value = value
        self.allowed = tuple(allowed)
        self.reason = reason

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "interface": self.interface,
            "key": self.key,
            "value": self.value,
            "allowed": list(self.allowed),
            "reason": self.reason,
        }

    def __str__(self) -> str:
        parts = [self.message]
        if self.key:
            parts.append(f"key={self.key}")
        if self.value:
            parts.append(f"value={self.value!r}")
        if self.allowed:
            parts.append(f"allowed={list(self.allowed)}")
        if self.reason:
            parts.append(f"reason={self.reason}")
        return " | ".join(parts)


class MissingConfigurationError(ConfigurationError):
    """The interface's config key is absent or empty."""

    code = "config_missing"


class UnknownProviderError(ConfigurationError):
    """The configured value is not one of the interface's registered providers."""

    code = "provider_unknown"


class ProviderNotAvailableError(ConfigurationError):
    """The provider name is valid but its implementation is not wired yet."""

    code = "provider_not_available"


class ProviderMismatchError(ConfigurationError):
    """The built object does not satisfy the interface it was registered for."""

    code = "provider_mismatch"


class UnknownInterfaceError(ConfigurationError):
    """The requested interface has no spec in the catalog."""

    code = "interface_unknown"


class ResolutionErrors(ConfigurationError):
    """Several interfaces failed to resolve; all failures are reported at once."""

    code = "resolution_failed"

    def __init__(self, errors: Sequence[ConfigurationError]) -> None:
        self.errors = tuple(errors)
        message = "; ".join(f"[{err.interface or '-'}] {err}" for err in self.errors)
        super().__init__(message or "no errors")
