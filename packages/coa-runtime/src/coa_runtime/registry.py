"""Resolution: config key -> provider -> validated instance.

Three refusals, all explicit (plan §3, §11.3):

1. key absent  -> :class:`MissingConfigurationError`
2. value unknown -> :class:`UnknownProviderError`
3. provider known but not wired -> :class:`ProviderNotAvailableError`
4. built object does not satisfy the interface -> :class:`ProviderMismatchError`

There is no default provider and no fallback chain. A caller that does not
need an interface must say so by not resolving it.
"""

from __future__ import annotations

import inspect
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from .catalog import InterfaceSpec, catalog
from .errors import (
    ConfigurationError,
    MissingConfigurationError,
    ProviderMismatchError,
    ProviderNotAvailableError,
    ResolutionErrors,
    UnknownInterfaceError,
    UnknownProviderError,
)
from .settings import Settings

OK = "ok"
MISSING = "missing"
UNKNOWN = "unknown"
NOT_AVAILABLE = "not_available"


@dataclass(frozen=True)
class Status:
    """Config-level status of one interface. No provider is constructed."""

    interface: str
    key: str
    context: str
    status: str
    provider: str = ""
    detail: str = ""


@dataclass(frozen=True)
class Resolution:
    """A resolved, structurally validated provider instance."""

    interface: str
    key: str
    context: str
    provider: str
    instance: Any


class ProviderRegistry:
    """Registry of interface specs. Construct with :func:`default_registry`."""

    def __init__(self, specs: Mapping[str, InterfaceSpec]) -> None:
        self._specs = dict(specs)

    @property
    def interfaces(self) -> tuple[str, ...]:
        return tuple(self._specs)

    def spec(self, interface: str) -> InterfaceSpec:
        try:
            return self._specs[interface]
        except KeyError as exc:
            raise UnknownInterfaceError(
                f"unknown interface {interface!r}",
                interface=interface,
                allowed=self.interfaces,
            ) from exc

    # ── validation without construction ─────────────────────────────────────

    def status(self, interface: str, settings: Settings) -> Status:
        spec = self.spec(interface)
        raw = settings.get(spec.key)
        if raw is None:
            return Status(
                interface=spec.name,
                key=spec.key,
                context=spec.context,
                status=MISSING,
                detail="key is absent or empty",
            )
        name = raw.strip().lower()
        provider = spec.providers.get(name)
        if provider is None:
            return Status(
                interface=spec.name,
                key=spec.key,
                context=spec.context,
                status=UNKNOWN,
                provider=name,
                detail=f"allowed={list(spec.allowed)}",
            )
        if not provider.implemented:
            return Status(
                interface=spec.name,
                key=spec.key,
                context=spec.context,
                status=NOT_AVAILABLE,
                provider=name,
                detail=provider.notes,
            )
        return Status(
            interface=spec.name,
            key=spec.key,
            context=spec.context,
            status=OK,
            provider=name,
            detail=provider.notes,
        )

    def matrix(self, settings: Settings) -> tuple[Status, ...]:
        """One row per interface, in catalog order. Never constructs a provider."""
        return tuple(self.status(name, settings) for name in self.interfaces)

    # ── resolution ──────────────────────────────────────────────────────────

    def resolve(self, interface: str, settings: Settings) -> Resolution:
        """Return the configured provider instance, or raise a specific error."""
        spec = self.spec(interface)
        raw = settings.get(spec.key)
        if raw is None:
            raise MissingConfigurationError(
                f"{interface} has no provider configured",
                interface=interface,
                key=spec.key,
                allowed=spec.allowed,
            )
        name = raw.strip().lower()
        provider = spec.providers.get(name)
        if provider is None:
            raise UnknownProviderError(
                f"{interface} has no provider named {name!r}",
                interface=interface,
                key=spec.key,
                value=name,
                allowed=spec.allowed,
            )
        if not provider.implemented:
            raise ProviderNotAvailableError(
                f"{interface} provider {name!r} is registered but not implemented",
                interface=interface,
                key=spec.key,
                value=name,
                allowed=spec.allowed,
                reason=provider.notes,
            )

        try:
            instance = provider.factory(settings)
        except ConfigurationError:
            raise
        except Exception as exc:  # noqa: BLE001 - any factory failure is a config failure
            raise ProviderMismatchError(
                f"{interface} provider {name!r} failed to construct",
                interface=interface,
                key=spec.key,
                value=name,
                reason=f"{type(exc).__name__}: {exc}",
            ) from exc

        self._check(interface, spec, name, instance, settings)
        return Resolution(
            interface=spec.name,
            key=spec.key,
            context=spec.context,
            provider=name,
            instance=instance,
        )

    def resolve_many(self, settings: Settings, interfaces: Iterable[str]) -> dict[str, Resolution]:
        """Resolve several interfaces; every failure is reported together."""
        resolved: dict[str, Resolution] = {}
        errors: list[ConfigurationError] = []
        for interface in interfaces:
            try:
                resolved[interface] = self.resolve(interface, settings)
            except ConfigurationError as exc:
                errors.append(exc)
        if errors:
            raise ResolutionErrors(errors)
        return resolved

    def resolve_all(self, settings: Settings) -> dict[str, Resolution]:
        return self.resolve_many(settings, self.interfaces)

    # ── structural validation ───────────────────────────────────────────────

    def _check(
        self,
        interface: str,
        spec: InterfaceSpec,
        provider: str,
        instance: Any,
        settings: Settings,
    ) -> None:
        def fail(reason: str) -> None:
            raise ProviderMismatchError(
                f"{interface} provider {provider!r} does not satisfy the interface",
                interface=interface,
                key=spec.key,
                value=provider,
                reason=reason,
            )

        if spec.protocol is not None:
            try:
                matches = isinstance(instance, spec.protocol)
            except TypeError as exc:  # pragma: no cover - defensive
                fail(f"protocol {spec.protocol!r} is not runtime-checkable: {exc}")
                return
            if not matches:
                fail(f"not an instance of {spec.protocol.__name__}")

        for method in spec.required_methods:
            attribute = getattr(instance, method, None)
            if attribute is None or not callable(attribute):
                fail(f"missing callable method {method!r}")
                return
            if spec.expects_async is True and not inspect.iscoroutinefunction(attribute):
                fail(f"method {method!r} must be async")
                return
            if spec.expects_async is False and inspect.iscoroutinefunction(attribute):
                fail(f"method {method!r} must be sync")
                return

        # Lazy providers read their settings inside the factory; re-read once
        # here so a key that disappeared mid-construction is still caught.
        if spec.key not in settings.snapshot():  # pragma: no cover - defensive
            fail(f"config key {spec.key} vanished during construction")


def default_registry() -> ProviderRegistry:
    """The catalog as a registry."""
    return ProviderRegistry(catalog())


__all__ = [
    "MISSING",
    "NOT_AVAILABLE",
    "OK",
    "UNKNOWN",
    "ProviderRegistry",
    "Resolution",
    "Status",
    "default_registry",
]
