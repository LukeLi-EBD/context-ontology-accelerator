"""Local ``GraphAdminPort``: one Oxigraph endpoint, no AWS control plane.

The local deployment has exactly one graph cluster and no tag service, so the
port's minimal runnable subset is:

* ``probe_engine`` — a real ``ASK {}`` against the configured endpoint;
* ``list_clusters`` — that one endpoint, named by its URL;
* ``list_tags`` — empty, because there is no tag store to read;
* ``probe`` — the same reachability check, never raising.

Probing an endpoint other than the configured one is refused rather than
answered from the wrong cluster.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from coa_ports import GraphCluster, PortError, PortErrorCode


class OxigraphGraphAdmin:
    """``GraphAdminPort`` over a single Oxigraph endpoint."""

    backend = "oxigraph"

    def __init__(self, endpoint: str, *, timeout_ms: int = 30000, store: Any | None = None) -> None:
        self._endpoint = endpoint.rstrip("/")
        if store is None:
            # Imported here so the module stays importable where rdflib is absent
            # (unit tests inject a store; production always constructs the real one).
            from platform_core.adapters.graph_oxigraph import OxigraphHttpStore

            store = OxigraphHttpStore(self._endpoint, timeout_ms=timeout_ms, max_rows=1)
        self._store = store

    def probe_engine(self, endpoint: str, *, region: str = "") -> None:
        """Raise ``PortError(unavailable)`` unless the endpoint answers ``ASK {}``."""
        target = endpoint.rstrip("/")
        if target != self._endpoint:
            raise PortError(
                PortErrorCode.INVALID_ARGUMENT,
                "the local graph admin serves only its configured endpoint",
                provider=self.backend,
                provider_code="E_GRAPH_ADMIN_ENDPOINT_MISMATCH",
                details={"configured": self._endpoint, "requested": target},
            )
        try:
            self._store.ask("ASK {}")
        except Exception as exc:  # noqa: BLE001 - every failure means "not reachable"
            raise PortError(
                PortErrorCode.UNAVAILABLE,
                f"graph engine at {endpoint} did not answer",
                provider=self.backend,
                provider_code="E_GRAPH_ADMIN_PROBE",
                details={"error": type(exc).__name__},
            ) from exc

    def list_clusters(self, *, region: str = "", cluster_id: str = "") -> tuple[GraphCluster, ...]:
        """The single local cluster; empty when ``cluster_id`` names another."""
        if cluster_id and cluster_id != self._endpoint:
            return ()
        return (
            GraphCluster(
                identifier=self._endpoint,
                engine="oxigraph",
                endpoints=(self._endpoint,),
                iam_auth_enabled=False,
            ),
        )

    def list_tags(self, resource_arn: str) -> Mapping[str, str]:
        """No tag store exists locally; callers get an empty mapping."""
        return {}

    def probe(self) -> Mapping[str, Any]:
        """Reachability snapshot; never raises."""
        try:
            self._store.ask("ASK {}")
            return {"ok": True, "backend": self.backend, "endpoint": self._endpoint}
        except Exception as exc:  # noqa: BLE001 - probe must not raise
            return {
                "ok": False,
                "backend": self.backend,
                "endpoint": self._endpoint,
                "error": f"{type(exc).__name__}: {exc}",
            }

    def close(self) -> None:
        self._store.close()


__all__ = ["OxigraphGraphAdmin"]
