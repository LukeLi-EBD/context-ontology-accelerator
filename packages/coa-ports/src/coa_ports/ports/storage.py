"""Reused infrastructure ports (confirmed ownership: ``coa-ports``).

These four already existed as platform_core / COA shapes. They live here so
implementations can depend on one neutral protocol instead of importing a
service package. They are synchronous because the platform adapters they
wrap are synchronous; an async caller wraps the call in
``asyncio.to_thread`` inside its thin shell.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from ..dto import GraphQueryResult, ObjectInfo
from ..language import GraphUri


@runtime_checkable
class GraphStorePort(Protocol):
    """Write-capable graph store (replaces Neptune SPARQL update)."""

    def query(self, sparql: str) -> GraphQueryResult:
        """Run a SELECT query and return flat bindings."""
        ...

    def ask(self, sparql: str) -> bool:
        """Run an ASK query."""
        ...

    def update(self, sparql: str) -> None:
        """Apply one SPARQL Update statement."""
        ...

    def clear_graph(self, graph_uri: GraphUri) -> None:
        """Remove one named graph."""
        ...

    def probe(self) -> Mapping[str, Any]:
        """Reachability snapshot; never raises."""
        ...


@runtime_checkable
class ObjectStorePort(Protocol):
    """Binary object store (replaces S3)."""

    def put(
        self,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str = "application/octet-stream",
        metadata: Mapping[str, str] | None = None,
    ) -> ObjectInfo:
        """Store ``body`` and return its metadata."""
        ...

    def get(self, bucket: str, key: str) -> tuple[bytes, ObjectInfo]:
        """Return ``(body, metadata)``; a missing key raises ``not_found``."""
        ...

    def head(self, bucket: str, key: str) -> ObjectInfo:
        """Return metadata only; a missing key raises ``not_found``."""
        ...

    def delete(self, bucket: str, key: str) -> None:
        """Delete one object; deleting an absent key is a no-op."""
        ...

    def list(self, bucket: str, prefix: str = "", limit: int = 100) -> tuple[ObjectInfo, ...]:
        """List objects under ``prefix``."""
        ...

    def probe(self) -> Mapping[str, Any]:
        """Reachability snapshot; never raises."""
        ...


@runtime_checkable
class MetadataStorePort(Protocol):
    """Relational metadata store (replaces DynamoDB item access where relational fits)."""

    def query(self, sql: str, params: tuple[Any, ...] | list[Any] = ()) -> tuple[Mapping[str, Any], ...]:
        """Run a read statement."""
        ...

    def execute(self, sql: str, params: tuple[Any, ...] | list[Any] = ()) -> int:
        """Run a write statement and return the affected row count."""
        ...

    def probe(self) -> Mapping[str, Any]:
        """Reachability snapshot; never raises."""
        ...


@runtime_checkable
class SecretProvider(Protocol):
    """Secret lookup (replaces Secrets Manager). Never logs values."""

    def get(self, name: str) -> str:
        """Return the secret value; a missing secret raises ``not_found``."""
        ...
