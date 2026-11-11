"""Contract-shaped routes for P8 ingestion runs (F17/F18).

Lives outside ``api.py`` so the P8 branch adds one registration line and one
router module, mirroring how P4 mounted ``term_api`` / ``dictionary_api``.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Query

from .importer import get_ingestion_run, ingestion_runs


def register_ingestion_routes(app: FastAPI, runtime: Any) -> None:
    """Mount the readonly ingestion-run routes on the app."""

    @app.get("/namespaces/{namespace_id}/ingestion-runs")
    def list_ingestion_runs(
        namespace_id: str,
        kind: str | None = Query(default=None),
        status: str | None = Query(default=None),
        max_results: int = Query(default=20, alias="maxResults", ge=1, le=50),
        next_token: str | None = Query(default=None, alias="nextToken"),
    ) -> dict[str, Any]:
        return ingestion_runs(
            runtime,
            namespace_id,
            kind=kind,
            status=status,
            max_results=max_results,
            next_token=next_token,
        )

    @app.get("/namespaces/{namespace_id}/ingestion-runs/{run_id}")
    def read_ingestion_run(namespace_id: str, run_id: str) -> dict[str, Any]:
        return {"run": get_ingestion_run(runtime, namespace_id, run_id)}
