"""O-02: T-Box proposal/version lifecycle state machine.

The audit chain in ``platform.ontology_event`` records *what* happened; this
module records the *state transition* itself: from/to status, actor, reason and
time. It is append-only and rejects transitions outside the declared graph.

Lifecycle (proposal and version share the same vocabulary):

    proposed -> review -> approved -> published -> superseded

``draft -> proposed`` is the import step; ``rejected``/``deprecated`` are
terminal side states kept from S11. ``proposed -> approved`` stays available
as a compatibility edge used by the governance console and the G-01 import
publish path; it is recorded as two transitions (proposed -> review ->
approved) so the chain is never incomplete.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .errors import PortError

PROPOSAL_STATES = ("proposed", "review", "approved", "published", "superseded", "rejected")
VERSION_STATES = (
    "draft", "proposed", "review", "approved", "published", "superseded",
    "deprecated", "rejected",
)

# Deliberate edges only. Anything not listed is illegal and is refused with
# E_ONTOLOGY_LIFECYCLE_INVALID instead of being written with a bad status.
ALLOWED_TRANSITIONS: dict[str, dict[str, tuple[str, ...]]] = {
    "proposal": {
        "proposed": ("review", "approved", "rejected"),
        "review": ("approved", "rejected"),
        "approved": ("published",),
        "published": ("superseded",),
        "superseded": (),
        "rejected": (),
    },
    "version": {
        "draft": ("proposed", "published", "rejected", "deprecated"),
        "proposed": ("review", "approved", "rejected", "deprecated"),
        "review": ("approved", "rejected", "deprecated"),
        "approved": ("published", "deprecated", "rejected"),
        "published": ("superseded", "deprecated"),
        "superseded": ("published", "deprecated"),
        "deprecated": ("published",),
        "rejected": (),
    },
}

E_LIFECYCLE_INVALID = "E_ONTOLOGY_LIFECYCLE_INVALID"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def allowed_targets(entity_kind: str, from_status: str | None) -> tuple[str, ...]:
    table = ALLOWED_TRANSITIONS.get(entity_kind) or {}
    return tuple(table.get(from_status or "", ()))


def validate_transition(entity_kind: str, from_status: str | None, to_status: str) -> None:
    """Raise Conflict when the edge is not in the state machine."""
    if entity_kind not in ALLOWED_TRANSITIONS:
        raise PortError(
            code="InvalidArgument",
            message=f"unknown lifecycle entity kind: {entity_kind}",
            provider="platform",
            provider_code=E_LIFECYCLE_INVALID,
            details={"entityKind": entity_kind, "allowed": sorted(ALLOWED_TRANSITIONS)},
        )
    targets = allowed_targets(entity_kind, from_status)
    if to_status not in targets:
        raise PortError(
            code="Conflict",
            message=(
                f"illegal {entity_kind} transition: {from_status or '(none)'} -> {to_status}"
            ),
            provider="platform",
            provider_code=E_LIFECYCLE_INVALID,
            details={
                "entityKind": entity_kind,
                "from": from_status,
                "to": to_status,
                "allowed": list(targets),
            },
        )


def record_transition(
    tx: Any,
    *,
    entity_kind: str,
    entity_id: str,
    version_id: str,
    proposal_id: str | None,
    from_status: str | None,
    to_status: str,
    actor: str,
    reason: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    """Append one transition row inside the caller's transaction.

    No validation here: callers validate before mutating state so a refused
    edge never leaves a half-written chain.
    """
    tx.execute(
        """
        INSERT INTO platform.ontology_lifecycle_transition
          (entity_kind, entity_id, version_id, proposal_id, from_status, to_status,
           actor, reason, payload)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
        """,
        (
            entity_kind, entity_id, version_id, proposal_id, from_status, to_status,
            actor, reason, json.dumps(payload or {}, ensure_ascii=False, sort_keys=True),
        ),
    )


def _row_to_transition(row: dict[str, Any]) -> dict[str, Any]:
    created = row.get("created_at")
    payload = row.get("payload") or {}
    if isinstance(payload, str):
        payload = json.loads(payload)
    return {
        "seq": int(row["seq"]),
        "entityKind": row["entity_kind"],
        "entityId": row["entity_id"],
        "versionId": row["version_id"],
        "proposalId": row.get("proposal_id"),
        "from": row.get("from_status"),
        "to": row["to_status"],
        "actor": row.get("actor"),
        "reason": row.get("reason"),
        "at": created.isoformat() if hasattr(created, "isoformat") else created,
        "payload": payload,
    }


def list_transitions(
    metadata: Any,
    *,
    version_id: str | None = None,
    proposal_id: str | None = None,
    entity_id: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    rows = metadata.query(
        """
        SELECT seq, entity_kind, entity_id, version_id, proposal_id, from_status,
               to_status, actor, reason, payload, created_at
          FROM platform.ontology_lifecycle_transition
         WHERE (%s::text IS NULL OR version_id = %s)
           AND (%s::text IS NULL OR proposal_id = %s)
           AND (%s::text IS NULL OR entity_id = %s)
         ORDER BY seq ASC
         LIMIT %s
        """,
        (version_id, version_id, proposal_id, proposal_id, entity_id, entity_id, limit),
    )
    return [_row_to_transition(row) for row in rows]


def flow(metadata: Any, version_id: str) -> dict[str, Any]:
    """Read-only flow for one version plus the states actually reached."""
    items = list_transitions(metadata, version_id=version_id)
    reached: list[str] = []
    for item in items:
        for state in (item.get("from"), item.get("to")):
            if state and state not in reached:
                reached.append(state)
    return {
        "versionId": version_id,
        "items": items,
        "count": len(items),
        "states": reached,
        "empty": not items,
        "emptyReason": None if items else "该版本尚无流转记录（未提案或迁移前的历史版本）",
        "source": "platform.ontology_lifecycle_transition（append-only）",
        "sampledAt": _now(),
        "readOnly": True,
    }


def summarize(metadata: Any, version_ids: list[str]) -> dict[str, Any]:
    """Lifecycle block embedded in /health/ontology-diff."""
    flows: dict[str, Any] = {}
    all_items: list[dict[str, Any]] = []
    for version_id in version_ids:
        if not version_id:
            continue
        data = flow(metadata, version_id)
        flows[version_id] = {
            "count": data["count"],
            "states": data["states"],
            "last": data["items"][-1] if data["items"] else None,
            "empty": data["empty"],
        }
        all_items.extend(data["items"])
    return {
        "versions": flows,
        "items": all_items,
        "empty": not all_items,
        "emptyReason": None if all_items else "涉及版本均无流转记录",
        "source": "platform.ontology_lifecycle_transition",
        "readOnly": True,
    }
