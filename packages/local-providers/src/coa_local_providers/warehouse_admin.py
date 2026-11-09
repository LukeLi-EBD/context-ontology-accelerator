"""Local ``WarehouseAdminPort``: PostgreSQL as the only warehouse.

There are no Athena workgroups and no Glue catalogues locally, so those methods
are documented no-ops rather than fake AWS objects: the local catalogue *is* the
PostgreSQL schema, and nothing needs creating. ``run_query`` is the part that
really runs — it serves metadata sampling and catalogue discovery — and it
accepts read-only statements only.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from coa_ports import PortError, PortErrorCode
from platform_core.adapters.metadata_pg import MetadataPg

_READ_ONLY_PREFIXES = ("select", "with")


class PgWarehouseAdmin:
    """``WarehouseAdminPort`` over the platform PostgreSQL database."""

    backend = "postgres"

    def __init__(
        self,
        dsn: str,
        *,
        pool_max: int = 4,
        open_timeout_seconds: float = 10.0,
    ) -> None:
        self._meta = MetadataPg(dsn, pool_max=pool_max)
        self._meta.open(retry_seconds=open_timeout_seconds)

    def create_workgroup(
        self,
        name: str,
        *,
        output_location: str = "",
        encryption: str = "",
        engine_version: str = "",
        enforce_configuration: bool = False,
        publish_metrics: bool = False,
        tags: Mapping[str, str] | None = None,
    ) -> str:
        """No-op: PostgreSQL needs no workgroup; returns ``name`` for bookkeeping.

        The policy fields (location, encryption, engine version, enforcement,
        metrics, tags) are accepted so callers pass the same arguments as on
        Athena; locally there is nothing to configure.
        """
        if not name:
            raise PortError(
                PortErrorCode.INVALID_ARGUMENT,
                "workgroup name must not be empty",
                provider=self.backend,
                provider_code="E_WAREHOUSE_NAME_EMPTY",
            )
        return name

    def delete_workgroup(self, name: str) -> None:
        """No-op: nothing was created."""
        return None

    def register_catalog(self, name: str, *, parameters: Mapping[str, str] | None = None) -> None:
        """No-op: the local catalogue is the PostgreSQL schema."""
        if not name:
            raise PortError(
                PortErrorCode.INVALID_ARGUMENT,
                "catalog name must not be empty",
                provider=self.backend,
                provider_code="E_WAREHOUSE_NAME_EMPTY",
            )

    def delete_catalog(self, name: str) -> None:
        """No-op: nothing was registered."""
        return None

    def run_query(
        self,
        sql: str,
        *,
        database: str = "",
        max_rows: int = 200,
    ) -> tuple[tuple[str, ...], ...]:
        """Run a read-only query, capped at ``max_rows``; ``database`` is ignored."""
        statement = sql.strip().rstrip(";").strip()
        if not statement:
            raise PortError(
                PortErrorCode.INVALID_ARGUMENT,
                "SQL must not be empty",
                provider=self.backend,
                provider_code="E_WAREHOUSE_SQL_EMPTY",
            )
        if statement.split(None, 1)[0].lower() not in _READ_ONLY_PREFIXES:
            raise PortError(
                PortErrorCode.INVALID_ARGUMENT,
                "the local warehouse admin runs read-only SQL only",
                provider=self.backend,
                provider_code="E_WAREHOUSE_READ_ONLY",
                details={"prefix": statement.split(None, 1)[0][:20]},
            )
        rows = self._meta.query(
            f"SELECT * FROM ({statement}) AS coa_admin_query LIMIT %s",
            (max_rows,),
        )
        return tuple(tuple("" if value is None else str(value) for value in row.values()) for row in rows)

    def probe(self) -> Mapping[str, Any]:
        """Reachability snapshot; never raises."""
        try:
            self._meta.query("SELECT 1 AS ok")
            return {"ok": True, "backend": self.backend}
        except Exception as exc:  # noqa: BLE001 - probe must not raise
            return {"ok": False, "backend": self.backend, "error": f"{type(exc).__name__}: {exc}"}

    def close(self) -> None:
        self._meta.close()


__all__ = ["PgWarehouseAdmin"]
