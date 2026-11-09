"""Provider selection: one ``COA_PROVIDER_<INTERFACE>`` per COA contract.

Every interface has an explicit default (see ``config/gateway.env.example``).
``none`` means "deliberately not provided": it disables the interface instead of
silently substituting a local implementation. An unknown name is an error, not a
fallback.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

INTERFACES = (
    "graph",
    "vector",
    "embedding",
    "llm",
    "query_executor",
    "source_catalog",
    "conversation",
    "memory",
    "object_store",
)

# Interface defaults. Kept in sync with config/gateway.env.example.
DEFAULTS: dict[str, str] = {
    "graph": "oxigraph",
    "vector": "in-memory",
    "embedding": "none",
    "llm": "none",
    "query_executor": "none",
    "source_catalog": "none",
    "conversation": "none",
    "memory": "none",
    "object_store": "none",
}


class ProviderConfigError(RuntimeError):
    """A provider selection cannot be honoured; callers must not fall back."""


class UnknownProviderError(ProviderConfigError):
    """The value of ``COA_PROVIDER_<INTERFACE>`` names no implementation."""


class ProviderNotConfigured(ProviderConfigError):
    """The provider was selected but its required settings are absent."""


@dataclass(frozen=True)
class ProviderSettings:
    """Resolved provider names plus the raw settings mapping they were read from."""

    providers: dict[str, str]
    values: Mapping[str, str]

    @classmethod
    def from_env(cls) -> ProviderSettings:
        """Read the process environment."""
        return cls.from_mapping(os.environ)

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> ProviderSettings:
        """Read an explicit mapping (tests, config files, switch demos)."""
        providers: dict[str, str] = {}
        for interface in INTERFACES:
            raw = mapping.get(f"COA_PROVIDER_{interface.upper()}") or DEFAULTS[interface]
            providers[interface] = str(raw).strip().lower()
        return cls(providers=providers, values={k: str(v) for k, v in mapping.items()})

    def provider(self, interface: str) -> str:
        """The selected provider name for one interface."""
        if interface not in self.providers:
            raise UnknownProviderError(f"unknown COA interface {interface!r}; known: {', '.join(INTERFACES)}")
        return self.providers[interface]

    def optional(self, key: str, default: str) -> str:
        """A setting with a usable default."""
        value = (self.values.get(key) or "").strip()
        return value or default

    def require(self, key: str, *, interface: str) -> str:
        """A setting the selected provider cannot run without."""
        value = (self.values.get(key) or "").strip()
        if not value:
            raise ProviderNotConfigured(
                f"COA_PROVIDER_{interface.upper()}={self.provider(interface)} requires {key}; "
                "refusing to fall back to another implementation"
            )
        return value
