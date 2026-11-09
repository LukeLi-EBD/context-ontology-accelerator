"""NDJSON audit export + Markdown summary + offline chain verification.

No template engine: both formats are assembled with plain string building.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .facts import verify_records


def build_ndjson(records: list[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for record in records
    )


def export_meta(exported: dict[str, Any], snapshot: list[dict[str, Any]],
                total_assertions: int,
                filters: dict[str, Any] | None = None) -> dict[str, Any]:
    """Required self-description for a windowed export (S12/OQ-46)."""
    cutoff = exported.get("cutoff") or {}
    return {
        "cutoff_seq": int(cutoff.get("seq") or 0),
        "cutoff_hash": cutoff.get("hash"),
        "cutoff_at": cutoff.get("at"),
        "verified_prefix": bool((exported.get("chain") or {}).get("ok")),
        "events_total": int(exported.get("count") or 0),
        "events_window": int(exported.get("windowCount", exported.get("count") or 0)),
        "assertions_count": len(snapshot),
        "excluded_count": max(0, int(total_assertions) - len(snapshot)),
        "filter": filters or {},
    }


def summarize(records: list[dict[str, Any]],
              conflicts: list[dict[str, Any]] | None = None,
              meta: dict[str, Any] | None = None) -> str:
    actions = Counter(record["action"] for record in records)
    sources = Counter(
        (record.get("source") or {}).get("documentId") or "unknown"
        for record in records
    )
    conflicts = conflicts or []
    pending = [entry for entry in conflicts if entry.get("pending")]
    lines = [
        "# Fact audit export",
        "",
        f"- events: {len(records)}",
    ]
    if meta is not None:
        lines.extend([
            f"- cutoff_seq: {meta.get('cutoff_seq')}",
            f"- cutoff_hash: {meta.get('cutoff_hash')}",
            f"- verified_prefix: {str(bool(meta.get('verified_prefix'))).lower()}",
            f"- excluded_count: {meta.get('excluded_count')}",
            f"- assertions: {meta.get('assertions_count')}",
        ])
    lines.extend([
        f"- asserted: {actions.get('asserted', 0)}",
        f"- retracted: {actions.get('retracted', 0) + actions.get('batch_retracted', 0) + actions.get('conflict_kept', 0) + actions.get('merge_superseded', 0)}",
        f"- restored: {actions.get('restored', 0)}",
        f"- adjudicated: {actions.get('conflict_accepted', 0)}",
        f"- merged: {actions.get('merged', 0)}",
        f"- unmerged: {actions.get('unmerged', 0)}",
        f"- adjudication undone: {actions.get('resolution_undo', 0)}",
        f"- conflicts total: {len(conflicts)} (pending {len(pending)})",
        "",
        "## Events by source",
        "",
    ])
    for source, count in sorted(sources.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {source}: {count}")
    lines.extend(["", "## Action breakdown", ""])
    for action, count in sorted(actions.items()):
        lines.append(f"- {action}: {count}")
    if pending:
        lines.extend(["", "## Pending conflicts", ""])
        for entry in pending:
            values = ", ".join(str(value) for value in entry.get("values", []))
            lines.append(f"- {entry['subject']} {entry['predicate']}: {values}")
    return "\n".join(lines) + "\n"


def write_export(records: list[dict[str, Any]], out_dir: str | Path,
                 conflicts: list[dict[str, Any]] | None = None,
                 snapshot: list[dict[str, Any]] | None = None,
                 meta: dict[str, Any] | None = None) -> dict[str, Any]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    ndjson_path = target / "events.ndjson"
    summary_path = target / "summary.md"
    ndjson_path.write_text(build_ndjson(records), encoding="utf-8")
    summary_path.write_text(summarize(records, conflicts, meta), encoding="utf-8")
    written: dict[str, Any] = {
        "outDir": str(target),
        "ndjson": str(ndjson_path),
        "markdown": str(summary_path),
        "count": len(records),
    }
    if snapshot is not None:
        snapshot_path = target / "assertions.ndjson"
        snapshot_path.write_text(build_ndjson(snapshot), encoding="utf-8")
        written["snapshot"] = str(snapshot_path)
        written["snapshotCount"] = len(snapshot)
    if meta is not None:
        meta_path = target / "export.json"
        meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written["meta"] = str(meta_path)
        written["export"] = meta
    return written


def read_ndjson(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    return [
        json.loads(line)
        for line in source.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def verify_file(path: str | Path) -> dict[str, Any]:
    try:
        records = read_ndjson(path)
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "checked": 0, "error": f"cannot read NDJSON: {exc}"}
    result = verify_records(records)
    result["cutoff_seq"] = int(records[-1]["eventId"]) if records else 0
    result["cutoff_hash"] = records[-1].get("hash") if records else None
    # A prefix is only self-proving when it starts at the chain origin. A
    # filtered chain that starts mid-way must never be reported as complete.
    result["verified_prefix"] = bool(records) and records[0].get("prevEvent") in (None, 0)
    if result.get("ok") and not result["verified_prefix"]:
        first = records[0]
        result["ok"] = False
        result["error"] = (
            f"event {first.get('eventId')} has prevEvent={first.get('prevEvent')}; "
            "the file is a chain fragment, not a prefix"
        )
    # When the export sidecar is next to the NDJSON, enforce its cutoff too: a
    # truncated file would otherwise still look like a valid (shorter) prefix.
    meta_path = Path(path).with_name("export.json")
    if meta_path.is_file():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            meta = None
        if isinstance(meta, dict):
            expected_seq = meta.get("cutoff_seq")
            expected_hash = meta.get("cutoff_hash")
            result["expected_cutoff_seq"] = expected_seq
            if expected_seq is not None and int(expected_seq) != result["cutoff_seq"]:
                result["ok"] = False
                result["error"] = (
                    f"cutoff_seq mismatch: file={result['cutoff_seq']} "
                    f"export.json={expected_seq} (truncated chain?)"
                )
            elif expected_hash and expected_hash != result["cutoff_hash"]:
                result["ok"] = False
                result["error"] = (
                    f"cutoff_hash mismatch at event {result['cutoff_seq']} "
                    "(truncated or replaced chain?)"
                )
    return result
