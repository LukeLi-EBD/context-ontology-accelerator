"""Runtime configuration port (replaces SSM parameter reads)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable


@runtime_checkable
class ConfigProvider(Protocol):
    """Read-only configuration lookup shared by every context.

    ``get`` returns ``None`` for an absent key. ``require`` raises
    :class:`coa_ports.errors.PortError` with ``not_found`` and never falls
    back to a default; the composition root decides defaults, not the port.
    """

    def get(self, key: str) -> str | None:
        """Value for ``key``, or ``None`` when absent."""
        ...

    def require(self, key: str) -> str:
        """Value for ``key``; raise ``not_found`` when absent."""
        ...

    def as_mapping(self) -> Mapping[str, str]:
        """Diagnostic snapshot of the currently visible keys."""
        ...
