"""The ``config=env`` provider.

Lives in the composition root because reading configuration *is* the
composition root's job; exporting it from a service package would invert the
dependency direction.
"""

from __future__ import annotations

from collections.abc import Mapping

from coa_ports import PortError, PortErrorCode


class EnvironmentConfigProvider:
    """``ConfigProvider`` over an immutable snapshot of configuration values."""

    def __init__(self, values: Mapping[str, str]) -> None:
        self._values = {key: value for key, value in values.items() if value is not None}

    def get(self, key: str) -> str | None:
        value = self._values.get(key)
        return value if value else None

    def require(self, key: str) -> str:
        value = self.get(key)
        if value is None:
            raise PortError(
                PortErrorCode.NOT_FOUND,
                f"required configuration key is absent: {key}",
                provider="env",
                details={"key": key},
            )
        return value

    def as_mapping(self) -> Mapping[str, str]:
        return dict(self._values)


__all__ = ["EnvironmentConfigProvider"]
