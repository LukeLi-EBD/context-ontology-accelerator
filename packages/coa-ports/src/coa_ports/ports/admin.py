"""Administrative (control-plane) ports that are not query paths.

``GraphClient`` answers graph questions and ``QueryExecutor`` answers warehouse
questions; neither may construct an AWS control-plane client. The calls that
list clusters, probe an engine, create workgroups or register a data catalogue
live here instead, so a local deployment can serve them without any AWS SDK.

Both protocols are synchronous on purpose: every current caller is synchronous
(Lambda handlers, connector code), and an async-only admin port would force
``asyncio.run`` into those paths.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from ..dto import GraphCluster

__all__ = ["GraphAdminPort", "WarehouseAdminPort"]


@runtime_checkable
class GraphAdminPort(Protocol):
    """Graph control plane: engine reachability, cluster inventory, tags."""

    def probe_engine(self, endpoint: str, *, region: str = "") -> None:
        """Prove ``endpoint`` answers and this identity may call it.

        Returns normally on success and raises ``PortError`` on refusal; it is a
        control-plane check, not a SPARQL query.
        """
        ...

    def list_clusters(
        self,
        *,
        region: str = "",
        cluster_id: str = "",
    ) -> tuple[GraphCluster, ...]:
        """Every known graph cluster, or the one ``cluster_id`` names."""
        ...

    def list_tags(self, resource_arn: str) -> Mapping[str, str]:
        """Tags of one cluster resource; empty when the provider has no tags."""
        ...

    def probe(self) -> Mapping[str, Any]:
        """Reachability snapshot; never raises."""
        ...


@runtime_checkable
class WarehouseAdminPort(Protocol):
    """Warehouse control plane: workgroups, catalogues, read-only ad-hoc SQL."""

    def create_workgroup(self, name: str, *, output_location: str = "") -> str:
        """Create (or acknowledge) a workgroup and return its name."""
        ...

    def delete_workgroup(self, name: str) -> None:
        """Delete a workgroup; deleting an absent one is a no-op."""
        ...

    def register_catalog(self, name: str, *, parameters: Mapping[str, str] | None = None) -> None:
        """Register an external data catalogue under ``name``."""
        ...

    def delete_catalog(self, name: str) -> None:
        """Remove a data catalogue; removing an absent one is a no-op."""
        ...

    def run_query(
        self,
        sql: str,
        *,
        database: str = "",
        max_rows: int = 200,
    ) -> tuple[tuple[str, ...], ...]:
        """Run read-only SQL and return rows of string values, capped at ``max_rows``.

        This exists for metadata sampling and catalogue discovery, never for
        mutation: an implementation must reject non-read statements.
        """
        ...

    def probe(self) -> Mapping[str, Any]:
        """Reachability snapshot; never raises."""
        ...
