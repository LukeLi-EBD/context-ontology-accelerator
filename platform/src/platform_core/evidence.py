"""O-04: publish gate evidence pack.

Every publish attempt (successful or refused by a gate) writes one immutable
pack containing the SHACL report, consistency verdict, breaking-change
acknowledgement, materialization verdict and the fingerprints of the input
versions. Packs are stored in ``platform.ontology_evidence`` and materialized as
JSON files under ``storage.root/evidence/<version>/`` when downloaded.

This module never decides whether a publish is allowed: it only observes the
gate results computed by the existing publish path. A failure to write evidence
is logged and ignored so that the gate verdict cannot be changed by bookkeeping.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb

from .errors import PortError

SCHEMA_VERSION = 32
E_EVIDENCE_NOT_FOUND = "E_ONTOLOGY_EVIDENCE_NOT_FOUND"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _version_fingerprint(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "versionId": row.get("id") or row.get("versionId") or row.get("version_id"),
        "semver": row.get("semver"),
        "contentHash": row.get("contentHash") or row.get("content_hash"),
        "tripleCount": row.get("tripleCount") if row.get("tripleCount") is not None
        else row.get("triple_count"),
    }


def build_pack(
    *,
    version: dict[str, Any],
    against: dict[str, Any] | None,
    proposal: dict[str, Any] | None,
    mode: str,
    gates: dict[str, Any],
    verdict: str,
    actor: str,
    reason: str | None,
    diff: dict[str, Any] | None = None,
    error: PortError | None = None,
    shapes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if verdict not in ("pass", "fail"):
        raise ValueError(f"verdict must be pass/fail, got {verdict!r}")
    fingerprint = {
        "version": _version_fingerprint(version),
        "against": _version_fingerprint(against),
        "diff": {
            "from": (diff or {}).get("from"),
            "to": (diff or {}).get("to"),
            "sha256": _sha256(diff) if diff else None,
        },
        "shapes": shapes,
        "algorithms": "sha256; canonical JSON (sort_keys=True)",
    }
    pack: dict[str, Any] = {
        "evidenceId": f"ev-{uuid.uuid4().hex[:12]}",
        "versionId": fingerprint["version"]["versionId"] if fingerprint["version"] else None,
        "semver": fingerprint["version"]["semver"] if fingerprint["version"] else None,
        "proposalId": (proposal or {}).get("proposal_id") or (proposal or {}).get("proposalId"),
        "mode": mode,
        "verdict": verdict,
        "gates": gates or {},
        "inputFingerprint": fingerprint,
        "error": (
            {
                "code": error.code,
                "providerCode": error.provider_code,
                "message": error.message,
                "details": error.details,
            }
            if error is not None
            else None
        ),
        "actor": actor,
        "reason": reason,
        "createdAt": _now(),
        "schemaVersion": SCHEMA_VERSION,
        "source": "publish 门禁（SHACL + 一致性 + breaking ack + 物化）+ 输入版本指纹",
        "readOnly": True,
    }
    pack["sha256"] = _sha256({key: value for key, value in pack.items() if key != "sha256"})
    return pack


def record(metadata: Any, pack: dict[str, Any]) -> dict[str, Any]:
    """Persist one pack. The caller decides whether an exception is fatal."""
    metadata.query(
        """
        INSERT INTO platform.ontology_evidence
          (evidence_id, version_id, proposal_id, verdict, path, sha256, payload, created_by)
        VALUES (%s, %s, %s, %s, NULL, %s, %s, %s)
        ON CONFLICT (evidence_id) DO NOTHING
        RETURNING evidence_id
        """,
        (
            pack["evidenceId"], pack.get("versionId"), pack.get("proposalId"),
            pack["verdict"], pack["sha256"], Jsonb(pack), pack.get("actor") or "operator",
        ),
    )
    return pack


def _payload(row: dict[str, Any]) -> dict[str, Any]:
    payload = row.get("payload") or {}
    return json.loads(payload) if isinstance(payload, str) else payload


def list_packs(
    metadata: Any, version_id: str | None = None, verdict: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    rows = metadata.query(
        """
        SELECT evidence_id, version_id, proposal_id, verdict, path, sha256, created_at
          FROM platform.ontology_evidence
         WHERE (%s::text IS NULL OR version_id = %s)
           AND (%s::text IS NULL OR verdict = %s)
         ORDER BY created_at DESC, evidence_id
         LIMIT %s
        """,
        (version_id, version_id, verdict, verdict, limit),
    )
    items = [
        {
            "evidenceId": row["evidence_id"],
            "versionId": row["version_id"],
            "proposalId": row.get("proposal_id"),
            "verdict": row["verdict"],
            "sha256": row["sha256"],
            "path": row.get("path"),
            "downloadUrl": f"/ontology/evidence/{row['evidence_id']}/download",
            "createdAt": (
                row["created_at"].isoformat()
                if hasattr(row["created_at"], "isoformat") else row["created_at"]
            ),
        }
        for row in rows
    ]
    return {
        "items": items,
        "count": len(items),
        "empty": not items,
        "emptyReason": None if items else "尚无发布证据包（版本未发布或迁移前的发布）",
        "filter": {"versionId": version_id, "verdict": verdict},
        "readOnly": True,
    }


def fetch(metadata: Any, evidence_id: str) -> dict[str, Any]:
    rows = metadata.query(
        "SELECT evidence_id, path, sha256, payload FROM platform.ontology_evidence "
        "WHERE evidence_id = %s",
        (evidence_id,),
    )
    if not rows:
        raise PortError(
            code="NotFound", message=f"evidence pack not found: {evidence_id}",
            provider="platform", provider_code=E_EVIDENCE_NOT_FOUND,
        )
    pack = _payload(rows[0])
    pack["path"] = rows[0].get("path")
    pack["sha256"] = rows[0].get("sha256")
    return pack


def materialize(root: str | Path, pack: dict[str, Any]) -> Path:
    """Write the pack under storage.root/evidence/<version>/ atomically."""
    version = str(pack.get("versionId") or "unknown")
    target = Path(root) / "evidence" / version
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{pack['evidenceId']}.json"
    body = json.dumps(pack, ensure_ascii=False, indent=2, sort_keys=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(body, encoding="utf-8")
    os.replace(tmp, path)
    return path


def check_download(pack: dict[str, Any]) -> None:
    """Guard the download route: the stored sha256 must match the payload."""
    recomputed = _sha256({
        key: value for key, value in pack.items() if key not in ("sha256", "path")
    })
    if pack.get("sha256") and recomputed != pack["sha256"]:
        raise PortError(
            code="Conflict", message="evidence pack sha256 mismatch; refusing download",
            provider="platform", provider_code="E_ONTOLOGY_EVIDENCE_CORRUPT",
        )
