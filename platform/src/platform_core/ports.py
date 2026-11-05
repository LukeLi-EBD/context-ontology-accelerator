"""Port boundaries and provider manifests (glue only, no algorithms).

Source of truth: _design/04 sections 1, 2.3 and 4.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Protocol

from .errors import PortError, UNSUPPORTED_PORT


@dataclass
class Manifest:
    provider: str
    port: str
    capabilities: list[str]
    port_version: str = "v1"
    provider_version: str = "0.1.0"
    limits: dict[str, Any] = field(default_factory=dict)
    notes: dict[str, Any] = field(default_factory=dict)


class GraphStorePort(Protocol):
    def manifest(self) -> Manifest: ...
    def ask(self, sparql: str) -> bool: ...
    def query(self, sparql: str) -> dict[str, Any]: ...
    def update(self, sparql: str) -> None: ...
    def clear_graph(self, graph_iri: str) -> None: ...
    def probe(self) -> dict[str, Any]: ...


class ObjectStorePort(Protocol):
    def manifest(self) -> Manifest: ...
    def put(
        self,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]: ...
    def get(self, bucket: str, key: str) -> tuple[bytes, dict[str, Any]]: ...
    def head(self, bucket: str, key: str) -> dict[str, Any]: ...
    def delete(self, bucket: str, key: str) -> None: ...
    def list(self, bucket: str, prefix: str = "", limit: int = 100) -> list[dict[str, Any]]: ...


class MetadataStorePort(Protocol):
    def migrate(self) -> dict[str, Any]: ...
    def query(self, sql: str, params: tuple | list = ()) -> list[dict[str, Any]]: ...
    def execute(self, sql: str, params: tuple | list = ()) -> int: ...


class UnsupportedPort:
    """Explicit placeholder: every call fails with Unsupported (no fake data)."""

    def __init__(self, port: str, slice_name: str) -> None:
        self._port = port
        self._slice = slice_name

    def manifest(self) -> Manifest:
        return Manifest(
            provider="absent",
            port=self._port,
            capabilities=[],
            notes={"status": "not_implemented", "slice": self._slice},
        )

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)

        def _raise(*_args: Any, **_kwargs: Any) -> Any:
            raise PortError(
                code="Unsupported",
                message=f"{self._port}.{name} is not implemented in {self._slice}",
                provider="absent",
                provider_code=UNSUPPORTED_PORT,
                details={"port": self._port, "slice": self._slice},
            )

        return _raise


class EnvSecretProvider:
    """Minimal SecretProvider: environment only, never logs values."""

    def __init__(self, environ: dict[str, str] | None = None) -> None:
        self._environ = environ if environ is not None else dict(os.environ)

    def get(self, name: str) -> str:
        value = self._environ.get(name)
        if value is None:
            raise PortError(
                code="NotFound",
                message=f"secret {name} is not set",
                provider="env",
                provider_code="E_SECRET_NOT_FOUND",
                details={"name": name},
            )
        return value

    def manifest(self) -> Manifest:
        return Manifest(
            provider="env",
            port="SecretProvider",
            capabilities=["secret.get"],
            notes={"source": "environment"},
        )
