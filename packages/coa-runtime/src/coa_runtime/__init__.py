"""COA composition root: configuration parsing, provider registry, assembly.

Nothing here is a service. It builds objects; it never serves traffic.
"""

from __future__ import annotations

from .catalog import SPECS, InterfaceSpec, ProviderSpec, catalog
from .contexts import CONTEXT_INTERFACES, assemble, interfaces_for
from .env_config import EnvironmentConfigProvider
from .errors import (
    ConfigurationError,
    MissingConfigurationError,
    ProviderMismatchError,
    ProviderNotAvailableError,
    ResolutionErrors,
    UnknownInterfaceError,
    UnknownProviderError,
)
from .registry import ProviderRegistry, Resolution, Status, default_registry
from .settings import Settings

__all__ = [
    "CONTEXT_INTERFACES",
    "SPECS",
    "ConfigurationError",
    "EnvironmentConfigProvider",
    "InterfaceSpec",
    "MissingConfigurationError",
    "ProviderMismatchError",
    "ProviderNotAvailableError",
    "ProviderRegistry",
    "ProviderSpec",
    "Resolution",
    "ResolutionErrors",
    "Settings",
    "Status",
    "UnknownInterfaceError",
    "UnknownProviderError",
    "assemble",
    "catalog",
    "default_registry",
    "interfaces_for",
]
