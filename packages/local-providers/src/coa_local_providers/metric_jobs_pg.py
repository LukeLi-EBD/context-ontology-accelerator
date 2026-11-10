# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Metric import-job storage on PostgreSQL (local) instead of DynamoDB.

``coa_metrics.api.import_job_store`` builds its own boto3 DynamoDB table in
``_get_table()``; it never goes through ``DynamoDBDAO``, so the local bridge's
global DAO substitution does not reach it. Without a local table object the
first ``GetImportJob`` read tries to sign a real AWS request and answers
500 ``Unable to locate credentials``.

This module patches that single seam onto the PostgreSQL item table
(``public.coa_local_items``), using the same logical table name the upstream
code reads from ``IMPORT_JOBS_TABLE``.

Configuration (no default provider — startup fails closed):

    COA_PROVIDER_METRIC_IMPORT_JOBS  postgres | dynamodb  (required)
    COA_CONTROL_PLANE_PG_DSN         PostgreSQL DSN       (required for postgres)
    IMPORT_JOBS_TABLE                logical table name   (default ``coa-dev-metric-import-jobs``)

``dynamodb`` leaves the upstream AWS implementation untouched.
"""

from __future__ import annotations

import os

from coa_local_providers.control_plane_pg import PgDatastoreDAO
from coa_local_providers.pg_table import PgTable

_PROVIDERS = ("postgres", "dynamodb")


def _provider() -> str:
    raw = os.environ.get("COA_PROVIDER_METRIC_IMPORT_JOBS", "").strip().lower()
    if not raw:
        raise RuntimeError(
            "COA_PROVIDER_METRIC_IMPORT_JOBS is required (postgres|dynamodb); refusing to start "
            "without an explicitly selected import-job store"
        )
    if raw not in _PROVIDERS:
        raise RuntimeError(f"Unknown COA_PROVIDER_METRIC_IMPORT_JOBS={raw!r}; expected one of {_PROVIDERS}")
    return raw


def _table_name() -> str:
    return os.environ.get("IMPORT_JOBS_TABLE", "").strip() or "coa-dev-metric-import-jobs"


def install_metric_import_jobs() -> str:
    """Patch the metric service's import-job table seam; returns the provider."""
    provider = _provider()
    if provider == "dynamodb":
        return provider
    if not os.environ.get("COA_CONTROL_PLANE_PG_DSN", "").strip():
        raise RuntimeError("COA_CONTROL_PLANE_PG_DSN is required when COA_PROVIDER_METRIC_IMPORT_JOBS=postgres")

    from coa_metrics.api import import_job_store

    table = PgTable(PgDatastoreDAO(_table_name(), region=os.environ.get("AWS_REGION")))
    import_job_store._get_table = lambda: table  # type: ignore[assignment]
    return provider
