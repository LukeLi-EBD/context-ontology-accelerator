"""Local import-job store: provider selection and PG table wiring."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest
from coa_local_providers import metric_jobs_pg
from coa_local_providers.metric_jobs_pg import install_metric_import_jobs


class _FakePool:
    @contextmanager
    def connection(self) -> Iterator[None]:
        yield None


class _FakeDao:
    """In-memory stand-in exercising the PgTable surface the store needs."""

    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], dict[str, Any]] = {}
        self._pool = _FakePool()

    def _keys(self, item: dict[str, Any]) -> tuple[str, str]:
        return str(item["PK"]), str(item["SK"])

    def _fetch(self, pk: str, sk: str) -> dict[str, Any] | None:
        return self.rows.get((pk, sk))

    def _write(self, item: dict[str, Any], conn: Any) -> None:
        self.rows[(item["PK"], item["SK"])] = dict(item)

    def _delete(self, pk: str, sk: str, conn: Any) -> None:
        self.rows.pop((pk, sk), None)


def test_provider_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COA_PROVIDER_METRIC_IMPORT_JOBS", raising=False)
    with pytest.raises(RuntimeError, match="COA_PROVIDER_METRIC_IMPORT_JOBS is required"):
        install_metric_import_jobs()


def test_unknown_provider_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COA_PROVIDER_METRIC_IMPORT_JOBS", "sqlite")
    with pytest.raises(RuntimeError, match="Unknown COA_PROVIDER_METRIC_IMPORT_JOBS"):
        install_metric_import_jobs()


def test_postgres_requires_a_dsn(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COA_PROVIDER_METRIC_IMPORT_JOBS", "postgres")
    monkeypatch.delenv("COA_CONTROL_PLANE_PG_DSN", raising=False)
    with pytest.raises(RuntimeError, match="COA_CONTROL_PLANE_PG_DSN is required"):
        install_metric_import_jobs()


def test_dynamodb_leaves_the_upstream_table_untouched(monkeypatch: pytest.MonkeyPatch) -> None:
    from coa_metrics.api import import_job_store

    monkeypatch.setenv("COA_PROVIDER_METRIC_IMPORT_JOBS", "dynamodb")
    original = import_job_store._get_table
    monkeypatch.setattr(import_job_store, "_get_table", original)

    assert install_metric_import_jobs() == "dynamodb"
    assert import_job_store._get_table is original


def test_postgres_routes_import_jobs_through_the_pg_table(monkeypatch: pytest.MonkeyPatch) -> None:
    from coa_metrics.api import import_job_store

    dao = _FakeDao()
    monkeypatch.setenv("COA_PROVIDER_METRIC_IMPORT_JOBS", "postgres")
    monkeypatch.setenv("COA_CONTROL_PLANE_PG_DSN", "postgresql://local/test")
    monkeypatch.setenv("IMPORT_JOBS_TABLE", "coa-local-metric-import-jobs")
    monkeypatch.setattr(metric_jobs_pg, "PgDatastoreDAO", lambda name, region=None: dao)
    original = import_job_store._get_table
    monkeypatch.setattr(import_job_store, "_get_table", original)

    assert install_metric_import_jobs() == "postgres"

    job = import_job_store.create_job("ns-1", "osi/ns-1/a.yaml", 2, chunk_size=1)
    stored = import_job_store.get_job("ns-1", job["jobId"])

    assert stored is not None
    assert stored["status"] == "IN_PROGRESS"
    assert stored["metricsTotal"] == 2
    assert import_job_store.get_job("ns-1", "missing") is None
