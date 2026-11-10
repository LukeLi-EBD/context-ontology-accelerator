"""Materialize ``platform.metric_definition`` rows into the COA metric graph.

Source of truth is the **old platform's PostgreSQL registry** (read only). Each
row becomes one governed-metric entity under the demo namespace:

- 54 rows have a ``platform.metric_field_binding`` → ``sourceTable`` is written
  from its ``fact_table`` and ``coa:bindingStatus "bound"``.
- 31 rows have no binding → the entity is still created, but **no**
  ``sourceTable`` is written (never ``""``); ``coa:bindingStatus "unbound"``
  marks it so the gap is visible instead of hidden.

The tool is idempotent: an existing metric is left untouched and counted as
``exists``. Nothing is written to the source database.

Usage (from the repository root):

    python doc/coa-x/tools/coa_metrics_local.py --dry-run
    python doc/coa-x/tools/coa_metrics_local.py --namespace ed70a15c-2d42-4dc9-8c61-33b2584f05fd
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
# The worktree has no installed environment of its own; put every workspace
# source root first so this script always exercises the checked-out code.
for _root in (REPO / "packages", REPO / "libs"):
    if not _root.is_dir():
        continue
    for _child in sorted(_root.iterdir()):
        _src = _child / "src"
        if _src.is_dir() and str(_src) not in sys.path:
            sys.path.insert(0, str(_src))

DEFAULT_NAMESPACE = "ed70a15c-2d42-4dc9-8c61-33b2584f05fd"
GRAPH_BASE = "https://coa.local/graph"
OXIGRAPH_URL = "http://127.0.0.1:7878"
PG_CONTAINER = "coa-local-pg"
PG_DB = "serve_local"
PG_USER = "platform"

# P10/P11 test row: not part of the 85 registry entries, never materialized here.
SYNTHETIC_METRIC_IDS = {"synthetic_agreement_exposure"}

EXPECTED_REAL_ROWS = 85
# 53 registry rows have a ``metric_field_binding``. The 54th metric id in that
# table is the P10/P11 synthetic row, which is excluded here.
EXPECTED_BOUND = 53
EXPECTED_UNBOUND = 32


def _psql_csv(sql: str) -> list[dict[str, str]]:
    completed = subprocess.run(
        [
            "docker",
            "exec",
            "-e",
            "PGCLIENTENCODING=UTF8",
            PG_CONTAINER,
            "psql",
            "-U",
            PG_USER,
            "-d",
            PG_DB,
            "--csv",
            "-c",
            sql,
        ],
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(f"FATAL: psql failed: {completed.stderr.decode('utf-8', 'replace')}")
    text = completed.stdout.decode("utf-8")
    return list(csv.DictReader(io.StringIO(text)))


def load_registry() -> list[dict[str, str]]:
    rows = _psql_csv(
        """
        SELECT metric_id,
               coalesce(name_zh, '') AS name_zh,
               coalesce(display_name, '') AS display_name,
               coalesce(definition, '') AS definition,
               coalesce(unit, '') AS unit,
               coalesce(domain, '') AS domain,
               coalesce(evidence_basis, '') AS evidence_basis,
               coalesce(publishable::text, '') AS publishable,
               coalesce(effective_date::text, '') AS effective_date,
               coalesce(decision_owner, '') AS decision_owner
          FROM platform.metric_definition
         ORDER BY metric_id
        """
    )
    real = [r for r in rows if r["metric_id"] not in SYNTHETIC_METRIC_IDS]
    if len(real) != EXPECTED_REAL_ROWS:
        raise SystemExit(
            f"FATAL: expected {EXPECTED_REAL_ROWS} registry rows, got {len(real)} "
            f"({len(rows)} including synthetic)"
        )
    return real


def load_bindings() -> dict[str, list[str]]:
    rows = _psql_csv(
        """
        SELECT metric_id, fact_table
          FROM platform.metric_field_binding
         ORDER BY metric_id, fact_table
        """
    )
    tables: dict[str, list[str]] = {}
    for row in rows:
        if not row["fact_table"]:
            continue
        tables.setdefault(row["metric_id"], [])
        if row["fact_table"] not in tables[row["metric_id"]]:
            tables[row["metric_id"]].append(row["fact_table"])
    return tables


def build_metric(row: dict[str, str], tables: list[str]):
    from coa_metrics.neptune_client import MetricDefinition

    metric_id = row["metric_id"]
    description = row["definition"] or row["display_name"] or row["name_zh"] or metric_id
    label = row["display_name"] or row["name_zh"] or None
    publishable_text = row["publishable"].strip().lower()
    publishable = None if publishable_text == "" else publishable_text in {"t", "true", "1"}
    return MetricDefinition(
        name=metric_id,
        description=description,
        expression_dialects=[],
        # There is no data-source registry in either database; inventing an id
        # would be worse than leaving it out.
        data_source_id="",
        source_table=tables[0] if tables else "",
        label=label,
        unit=row["unit"] or None,
        defined_by=row["decision_owner"] or None,
        effective_from=row["effective_date"] or None,
        domain=row["domain"] or None,
        evidence_basis=row["evidence_basis"] or None,
        publishable=publishable,
        binding_status="bound" if tables else "unbound",
    )


def make_client():
    os.environ.setdefault("NDB_GRAPH_URI_BASE", GRAPH_BASE)
    from coa_local_providers.metric_graph import oxigraph_transport
    from coa_metrics.neptune_client import MetricNeptuneClient

    transport = oxigraph_transport(
        os.getenv("COA_GRAPH_OXIGRAPH_URL", OXIGRAPH_URL),
        graph_base=GRAPH_BASE,
    )
    return MetricNeptuneClient(transport=transport)


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill COA governed metrics from platform.metric_definition")
    parser.add_argument("--namespace", default=DEFAULT_NAMESPACE)
    parser.add_argument("--dry-run", action="store_true", help="read and report, write nothing")
    parser.add_argument("--verify-only", action="store_true", help="skip writes, only re-read and check")
    args = parser.parse_args()

    rows = load_registry()
    bindings = load_bindings()
    multi = {m: t for m, t in bindings.items() if len(t) > 1}
    planned_bound = sum(1 for r in rows if bindings.get(r["metric_id"]))
    planned_unbound = len(rows) - planned_bound
    print(
        f"registry rows: {len(rows)}  bound: {planned_bound}  unbound: {planned_unbound}",
        flush=True,
    )
    if (planned_bound, planned_unbound) != (EXPECTED_BOUND, EXPECTED_UNBOUND):
        print(
            f"[warn] binding split {(planned_bound, planned_unbound)} != pinned "
            f"{(EXPECTED_BOUND, EXPECTED_UNBOUND)}",
            flush=True,
        )
    if multi:
        print(f"[note] {len(multi)} metrics bind to more than one table; using the first: {sorted(multi)[:5]}", flush=True)

    client = make_client()
    ns = args.namespace

    created = existed = failed = 0
    failures: list[tuple[str, str]] = []
    for row in rows:
        metric_id = row["metric_id"]
        metric = build_metric(row, bindings.get(metric_id, []))
        if args.dry_run or args.verify_only:
            exists = client.get_metric(ns, metric_id) is not None
            created += 0 if exists else 1
            existed += 1 if exists else 0
            continue
        try:
            if client.get_metric(ns, metric_id) is not None:
                existed += 1
                continue
            client.create_metric(ns, metric)
            created += 1
        except Exception as exc:  # noqa: BLE001 — report and keep going
            failed += 1
            failures.append((metric_id, f"{type(exc).__name__}: {exc}"))

    print(f"新增 {created} / 已存在 {existed} / 失败 {failed}", flush=True)
    for metric_id, why in failures:
        print(f"  FAIL {metric_id}: {why}", flush=True)
    if args.dry_run:
        print("dry-run: nothing written", flush=True)
        return 0 if failed == 0 else 1

    # ── read back through the same code path the API uses ──────────────────
    listed = {m.name: m for m in client.list_metrics(ns, limit=200)}
    missing = [r["metric_id"] for r in rows if r["metric_id"] not in listed]
    bound_ok = unbound_ok = 0
    bad_binding: list[str] = []
    bad_provenance: list[str] = []
    for row in rows:
        metric = listed.get(row["metric_id"])
        if metric is None:
            continue
        expected_table = (bindings.get(row["metric_id"]) or [""])[0]
        if expected_table:
            if metric.source_table == expected_table and metric.binding_status == "bound":
                bound_ok += 1
            else:
                bad_binding.append(row["metric_id"])
        else:
            if not metric.source_table and metric.binding_status == "unbound":
                unbound_ok += 1
            else:
                bad_binding.append(row["metric_id"])
        want_domain = row["domain"] or None
        want_evidence = row["evidence_basis"] or None
        want_publishable = None if not row["publishable"].strip() else row["publishable"].strip().lower() in {"t", "true", "1"}
        if (metric.domain, metric.evidence_basis, metric.publishable) != (want_domain, want_evidence, want_publishable):
            bad_provenance.append(row["metric_id"])

    print(
        f"read-back: listed {len(listed)}  missing {len(missing)}  "
        f"bound ok {bound_ok}/{EXPECTED_BOUND}  unbound ok {unbound_ok}/{EXPECTED_UNBOUND}",
        flush=True,
    )
    if missing:
        print(f"  MISSING {missing[:10]}", flush=True)
    if bad_binding:
        print(f"  BAD BINDING {bad_binding[:10]}", flush=True)
    if bad_provenance:
        print(f"  BAD PROVENANCE {bad_provenance[:10]}", flush=True)

    ok = (
        not missing
        and not bad_binding
        and not bad_provenance
        and bound_ok == EXPECTED_BOUND
        and unbound_ok == EXPECTED_UNBOUND
        and failed == 0
    )
    print("OK" if ok else "FAILED", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
