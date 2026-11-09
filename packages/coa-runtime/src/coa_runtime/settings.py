"""Configuration reading with explicit absence.

``Settings`` never invents a default. ``require`` raises
:class:`MissingConfigurationError` and names the interface, so a missing key
fails at the composition root instead of degrading silently at request time.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

from .errors import MissingConfigurationError


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class Settings:
    """An immutable view over a mapping of configuration keys."""

    def __init__(self, values: Mapping[str, str]) -> None:
        self._values = dict(values)

    @classmethod
    def from_environ(cls, environ: Mapping[str, str] | None = None) -> Settings:
        return cls(dict(os.environ if environ is None else environ))

    def get(self, key: str) -> str | None:
        """Value for ``key``; an empty or whitespace-only value counts as absent."""
        return _clean(self._values.get(key))

    def require(self, key: str, *, interface: str = "") -> str:
        """Value for ``key``; raise ``config_missing`` when absent or empty."""
        value = self.get(key)
        if value is None:
            raise MissingConfigurationError(
                f"{interface or 'configuration'} requires {key}",
                interface=interface,
                key=key,
            )
        return value

    def get_int(self, key: str, *, default: int | None = None, interface: str = "") -> int:
        raw = self.get(key)
        if raw is None:
            if default is None:
                self.require(key, interface=interface)
                raise AssertionError("unreachable")
            return default
        try:
            return int(raw)
        except ValueError as exc:
            raise MissingConfigurationError(
                f"{key} must be an integer",
                interface=interface,
                key=key,
                value=raw,
                reason=str(exc),
            ) from exc

    def get_float(self, key: str, *, default: float | None = None, interface: str = "") -> float:
        raw = self.get(key)
        if raw is None:
            if default is None:
                self.require(key, interface=interface)
                raise AssertionError("unreachable")
            return default
        try:
            return float(raw)
        except ValueError as exc:
            raise MissingConfigurationError(
                f"{key} must be a number",
                interface=interface,
                key=key,
                value=raw,
                reason=str(exc),
            ) from exc

    def snapshot(self) -> Mapping[str, str]:
        """Copy of the raw values, with absent entries removed."""
        return {key: value for key, value in self._values.items() if _clean(value) is not None}
