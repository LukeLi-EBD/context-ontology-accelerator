# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Read-only proposal view over the platform database (P1-06).

The platform database is the single source of truth for proposals
(``platform.ontology_proposal``). The local engine used to answer
``ListProposals`` / ``GetProposal`` from its own DynamoDB-compatible item table
(``public.coa_local_items``), which holds no proposal rows in the local stack —
so the engine listed 0 proposals while the platform held 15.

This module does **not** copy or dual-write those rows. It replaces the two
read seams of :mod:`coa_ontology.dynamo_store` with a query against the platform
table and maps each row into the item shape the engine's routes already expect:

    dynamo_store.list_proposals             <- list_proposals()
    dynamo_store.get_proposal_by_id         <- get_proposal_by_id()

Missing is missing. A platform row is a governance record, not an induction
artifact: it has no namespace, no proposal type, no source type and no Turtle
body. Those fields are left absent (``namespace`` is present but ``null``)
and named in ``missing_fields`` on every mapped item, rather than filled with
invented values. ``ontology_id`` is read from
``platform.ontology_version.graph_iri`` (the same derivation V52 uses), and is
listed as missing when that join finds no version.

Configuration:

    COA_ONTOLOGY_PROPOSALS_PG_DSN   platform database DSN (required)
                                    falls back to PLATFORM__DATABASE__URL

The DSN must point at the database that holds ``platform.ontology_proposal``
(``serve_local`` in the local stack), which is a different database from
``COA_CONTROL_PLANE_PG_DSN`` (the control-plane ``platform`` database that holds
``public.coa_local_items``). Pointing it at the latter would silently list 0
proposals, so resolution fails closed when neither variable is set.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

_log = logging.getLogger(__name__)

# Platform lifecycle -> engine ProposalStatus. ``review`` is platform's
# pre-approval governance state; the engine has no equivalent, and the proposal
# is still awaiting a decision, so it maps to ``pending``.
_STATUS_MAP = {
    "proposed": "pending",
    "review": "pending",
    "approved": "accepted",
    "published": "accepted",
    "rejected": "rejected",
}

# Fields the engine proposal view expects but a platform governance row does not
# carry. They are reported per item instead of being fabricated.
_ABSENT_FIELDS = (
    "namespace",
    "proposal_type",
    "source_type",
    "ontology_turtle",
    "r2rml_turtle",
    "matches",
)

_SELECT = """
SELECT p.proposal_id, p.version_id, p.against_version, p.change_summary,
       p.status, p.breaking, p.acknowledged_breaking, p.diff, p.impact,
       p.created_by, p.created_at, p.approved_by, p.approved_at, p.published_at,
       regexp_replace(v.graph_iri, '^.*:', '') AS ontology_id
  FROM platform.ontology_proposal p
  LEFT JOIN platform.ontology_version v ON v.version_id = p.version_id
"""


def proposals_dsn() -> str:
    """Resolve the platform-database DSN, failing closed when unset."""
    for key in ("COA_ONTOLOGY_PROPOSALS_PG_DSN", "PLATFORM__DATABASE__URL"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    raise RuntimeError(
        "COA_ONTOLOGY_PROPOSALS_PG_DSN is required to read platform proposals "
        "(set it to the database that holds platform.ontology_proposal, e.g. serve_local; "
        "COA_CONTROL_PLANE_PG_DSN points at the control-plane database and would list 0)"
    )


def _as_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _as_json(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def map_row(row: dict[str, Any], namespace: str) -> dict[str, Any]:
    """Map one ``platform.ontology_proposal`` row to the engine item shape.

    ``namespace`` is only used to build the engine's ``PK``. A platform row has
    no recorded namespace, so the item's ``namespace`` field is ``None`` and the
    field is named in ``missing_fields``: the PK prefix is an internal key, not
    source data.
    """
    proposal_id = str(row["proposal_id"])
    created_at = _as_iso(row.get("created_at"))
    approved_at = _as_iso(row.get("approved_at"))
    published_at = _as_iso(row.get("published_at"))
    updated_at = published_at or approved_at or created_at
    ontology_id = row.get("ontology_id")

    missing = list(_ABSENT_FIELDS)
    if not ontology_id:
        missing.append("ontology_id")

    return {
        "PK": f"{namespace}#PROPOSAL#{proposal_id}",
        "SK": "META",
        "proposal_id": proposal_id,
        "namespace": None,
        "version_id": row.get("version_id"),
        "against_version": row.get("against_version"),
        "ontology_id": ontology_id,
        "status": _STATUS_MAP.get(str(row.get("status")), row.get("status")),
        "change_summary": row.get("change_summary"),
        "breaking": bool(row.get("breaking")),
        "acknowledged_breaking": bool(row.get("acknowledged_breaking")),
        "diff": _as_json(row.get("diff")),
        "impact": _as_json(row.get("impact")),
        "created_by": row.get("created_by"),
        "created_at": created_at,
        "updated_at": updated_at,
        "approved_by": row.get("approved_by"),
        "approved_at": approved_at,
        "published_at": published_at,
        "metadata": {"authority": "platform.ontology_proposal"},
        "missing_fields": missing,
    }


def _rows(dsn: str, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with psycopg.connect(dsn, connect_timeout=5, row_factory=dict_row) as conn:
        return list(conn.execute(sql, params).fetchall())


def _newest_first(item: dict[str, Any]) -> tuple[str, str]:
    return (str(item.get("created_at") or "-"), str(item.get("PK") or ""))


def list_proposals(
    namespace: str | None = None,
    ontology_id: str | None = None,
    status: str | None = None,
    proposal_type: str | None = None,
    source_type: str | None = None,
    limit: int | None = 50,
) -> list[dict]:
    """Drop-in for ``dynamo_store.list_proposals`` backed by the platform table.

    The platform table records no namespace, so ``namespace`` does not narrow the
    result — the platform API itself lists governance proposals without a
    namespace. ``ontology_id`` / ``status`` filter on the mapped values.
    ``proposal_type`` and ``source_type`` are not recorded: a ``proposal_type``
    filter matches nothing, ``UNSTRUCTURED`` matches nothing, and ``STRUCTURED``
    matches everything (platform proposals are structured governance records).
    """
    if limit is not None and limit <= 0:
        return []
    if proposal_type:
        return []
    if source_type == "UNSTRUCTURED":
        return []

    rows = _rows(proposals_dsn(), _SELECT + " ORDER BY p.created_at DESC")
    items = [map_row(row, namespace or os.environ.get("DYNAMODB_DEFAULT_NAMESPACE", "default")) for row in rows]
    if ontology_id:
        items = [item for item in items if item.get("ontology_id") == ontology_id]
    if status:
        items = [item for item in items if item.get("status") == status]
    items.sort(key=_newest_first, reverse=True)
    return items if limit is None else items[:limit]


def get_proposal_by_id(
    proposal_id: str,
    namespace: str | None = None,
    *,
    hydrate_turtle: bool = True,
    hydrate_matches: bool = True,
    hydrate_constraints: bool = True,
) -> dict | None:
    """Drop-in for ``dynamo_store.get_proposal_by_id``; ``None`` means 404.

    Hydration flags are accepted for signature compatibility. The platform table
    stores no Turtle, matches or constraint artifacts, so there is nothing to
    hydrate; ``missing_fields`` names what is absent.
    """
    rows = _rows(proposals_dsn(), _SELECT + " WHERE p.proposal_id = %s", (proposal_id,))
    if not rows:
        return None
    return map_row(rows[0], namespace or os.environ.get("DYNAMODB_DEFAULT_NAMESPACE", "default"))


def install_ontology_proposals_readonly() -> str:
    """Patch the engine's two proposal read seams; returns the resolved DSN."""
    dsn = proposals_dsn()
    from coa_ontology import dynamo_store

    dynamo_store.list_proposals = list_proposals  # type: ignore[assignment]
    dynamo_store.get_proposal_by_id = get_proposal_by_id  # type: ignore[assignment]
    _log.info("ontology proposals: read-only view over platform.ontology_proposal")
    return dsn
