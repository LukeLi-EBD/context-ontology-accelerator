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


class CanvasPort(Protocol):
    """D1 read-only canvas port (design 53/55): same signature for simple/full.

    Implementations must not write to the graph and must return the same key
    set; values may differ (simple returns fewer nodes/paths and layout=none).
    """

    def manifest(self) -> Manifest: ...

    def subgraph(
        self,
        start: str,
        *,
        hops: int = 1,
        max_nodes: int = 200,
        max_edges: int = 400,
        include_types: bool = True,
        include_source: bool = True,
        graphs: list[str] | None = None,
    ) -> dict[str, Any]: ...

    def path(
        self,
        source: str,
        target: str,
        *,
        max_hops: int = 3,
        max_paths: int = 20,
        max_nodes: int = 200,
        include_types: bool = True,
        include_source: bool = True,
        graphs: list[str] | None = None,
    ) -> dict[str, Any]: ...

    def expand(
        self,
        node: str,
        *,
        hops: int = 1,
        max_nodes: int = 100,
        max_edges: int = 200,
        include_types: bool = True,
        include_source: bool = True,
        graphs: list[str] | None = None,
    ) -> dict[str, Any]: ...


@dataclass
class QuotaDecision:
    """Result of ``QuotaPort.check`` (design 87 §3).

    ``allowed=False`` always carries a ``reason`` code; ``action`` tells the
    caller what it may do instead: ``degrade`` keeps the non-LLM path
    (retrieval/rules), ``reject`` fails the request.
    """

    allowed: bool
    action: str
    reason: str | None
    provider: str
    scope: str
    units: int = 0
    used_tokens: int = 0
    used_requests: int = 0
    limit_tokens: int | None = None
    limit_requests: int | None = None
    remaining_tokens: int | None = None
    remaining_requests: int | None = None
    day: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "action": self.action,
            "reason": self.reason,
            "provider": self.provider,
            "scope": self.scope,
            "units": self.units,
            "usedTokens": self.used_tokens,
            "usedRequests": self.used_requests,
            "limitTokens": self.limit_tokens,
            "limitRequests": self.limit_requests,
            "remainingTokens": self.remaining_tokens,
            "remainingRequests": self.remaining_requests,
            "day": self.day,
        }


class QuotaPort(Protocol):
    """C2 budget guardrail (design 87): one surface for off/simple/full.

    ``off`` allows everything and never counts; ``simple`` counts per day/scope
    in PostgreSQL and enforces optional daily token/request limits; ``full`` is
    a skeleton whose methods raise ``E_PROVIDER_NOT_IMPLEMENTED``.
    """

    def manifest(self) -> Manifest: ...

    def check(self, scope: str, units: int = 1) -> QuotaDecision: ...

    def record(self, scope: str, units: int, cost: float = 0.0) -> None: ...

    def status(self, scope: str) -> dict[str, Any]: ...


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
