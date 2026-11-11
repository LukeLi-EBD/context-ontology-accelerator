# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Ontology job / proposal storage on PostgreSQL (local) instead of DynamoDB.

``coa_ontology.dynamo_store`` keeps every non-graph record — induction jobs,
async ingest jobs, validation jobs, proposals — in one DynamoDB table. All of
those call sites go through exactly two seams:

    _get_table()   boto3 ``Table``   (put_item / get_item / update_item /
                                      delete_item / scan / query / batch_writer)
    _get_dao()     ``DynamoDBDAO``   (ingest-job helpers)

This module swaps both seams for a PostgreSQL-backed item table
(``public.coa_local_items``, the same table ``control_plane_pg`` uses) at
process start, so the call sites stay untouched. It is the write-path sibling
of ``ontology_registry_pg``: that one replaced the *catalog* functions, this one
replaces the *item table* itself, which is why jobs and proposals come along
for free. The boto3-compatible table object itself is shared with the metric
import-job provider and lives in ``pg_table``.

Configuration (no default provider — startup fails closed):

    COA_PROVIDER_ONTOLOGY_JOBS   postgres | dynamodb   (required)
    COA_CONTROL_PLANE_PG_DSN     PostgreSQL DSN        (required for postgres)
    COA_ONTOLOGY_PROPOSALS_PG_DSN
                                 platform-database DSN for the read-only
                                 proposal view (falls back to
                                 PLATFORM__DATABASE__URL); a different database
                                 from COA_CONTROL_PLANE_PG_DSN
    DYNAMODB_TABLE               logical table name    (default ``ontology-engine``)

``dynamodb`` leaves the upstream AWS implementation untouched.
"""

from __future__ import annotations

import os

from coa_local_providers.control_plane_pg import PgDatastoreDAO
from coa_local_providers.pg_table import PgTable

_PROVIDERS = ("postgres", "dynamodb")


def _provider() -> str:
    raw = os.environ.get("COA_PROVIDER_ONTOLOGY_JOBS", "").strip().lower()
    if not raw:
        raise RuntimeError(
            "COA_PROVIDER_ONTOLOGY_JOBS is required (postgres|dynamodb); refusing to start "
            "without an explicitly selected ontology job store"
        )
    if raw not in _PROVIDERS:
        raise RuntimeError(f"Unknown COA_PROVIDER_ONTOLOGY_JOBS={raw!r}; expected one of {_PROVIDERS}")
    return raw


def _table_name() -> str:
    return os.environ.get("DYNAMODB_TABLE", "").strip() or "ontology-engine"


def install_ontology_jobs() -> str:
    """Patch the ontology engine's item-table seams; returns the provider."""
    provider = _provider()
    if provider == "dynamodb":
        return provider
    if not os.environ.get("COA_CONTROL_PLANE_PG_DSN", "").strip():
        raise RuntimeError("COA_CONTROL_PLANE_PG_DSN is required when COA_PROVIDER_ONTOLOGY_JOBS=postgres")

    from coa_ontology import dynamo_store

    dao = PgDatastoreDAO(_table_name(), region=os.environ.get("AWS_REGION"))
    table = PgTable(dao)
    dynamo_store._get_table = lambda: table  # type: ignore[assignment]
    dynamo_store._get_dao = lambda: dao  # type: ignore[assignment]

    # Proposals are NOT stored in the item table: the platform database is the
    # single source of truth. Replace the two read seams with a read-only view
    # over platform.ontology_proposal instead of copying those rows in.
    from coa_local_providers.ontology_proposals_pg import install_ontology_proposals_readonly

    install_ontology_proposals_readonly()
    return provider
