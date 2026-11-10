"""Export the read-only S1 snapshot from the running platform.

Run with the slice's own venv (see ``README.md``)::

    python packages/local-providers/scripts/export_snapshot.py

The script performs HTTP GETs only, reads committed SQL/Python files for the
metric binding definitions, and writes the snapshot under
``doc/_evidence-coa-integration/s1-2026-11-08/``. It does not start any service,
does not connect to PostgreSQL, and does not write to the platform API.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from coa_local_providers.snapshot import (
    apply_overrides,
    build_catalog_snapshot,
    compile_metric_sql,
    fetch_catalog_rows,
    fetch_manifest,
    fetch_metric,
    load_binding_overrides,
    metric_description,
    parse_bindings,
    parse_fact_functions,
    resolve_binding,
)
from coa_local_providers.win_compat import ensure_resource_module

ensure_resource_module()

from coa_metrics.osi_parser import (  # noqa: E402
    OsiCustomExtension,
    OsiDataset,
    OsiDialectExpression,
    OsiDocument,
    OsiMetric,
    serialize_osi_yaml,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:8080")
    parser.add_argument("--repo", default=str(REPO_ROOT))
    parser.add_argument(
        "--out",
        default=str(REPO_ROOT / "doc" / "_evidence-coa-integration" / "s1-2026-11-08"),
    )
    args = parser.parse_args()

    out = Path(args.out)
    repo = Path(args.repo)
    sql_dir = (
        repo / "packages" / "control-plane" / "src"
        / "coa_control_plane" / "platform_db" / "migrations"
    )
    overrides_path = (
        repo / "packages" / "platform-core" / "src" / "platform_core" / "metric_binding_overrides.py"
    )

    manifest = fetch_manifest(args.api)
    write_json(out / "raw" / "manifest.json", {"items": manifest})

    metrics: dict[str, dict] = {}
    for entry in manifest:
        metric_id = entry["metricId"]
        metrics[metric_id] = fetch_metric(args.api, metric_id)
        write_json(out / "raw" / "metrics" / f"{metric_id}.json", metrics[metric_id])

    catalog_rows = fetch_catalog_rows(args.api)
    write_json(out / "raw" / "catalog_dictionaries.json", {"items": catalog_rows})
    catalog = build_catalog_snapshot(catalog_rows)
    write_json(out / "snapshot" / "catalog.json", catalog)

    bindings = parse_bindings(sql_dir)
    apply_overrides(bindings, load_binding_overrides(overrides_path))
    write_json(
        out / "snapshot" / "bindings.json",
        {
            "rows": [
                row
                for (_metric, _version, _role), row in sorted(bindings.items())
            ],
            "fact_functions": parse_fact_functions(sql_dir),
        },
    )

    columns: dict[str, set[str]] = {}
    for source in catalog["data_sources"].values():
        for table, table_columns in source["tables"].items():
            columns[table.lower()] = {column["name"].lower() for column in table_columns}

    fact_functions = parse_fact_functions(sql_dir)
    datasets = [
        OsiDataset(name=table, source="postgres", data_source_id=data_source_id)
        for data_source_id, source in catalog["data_sources"].items()
        for table in sorted(source["tables"])
    ]

    osi_metrics: list[OsiMetric] = []
    reconcile_inputs: dict[str, dict] = {}
    for entry in manifest:
        metric_id = entry["metricId"]
        metric = metrics[metric_id]
        version = str(metric["browse"].get("definitionVersion") or "")
        binding_by_role = resolve_binding(bindings, metric_id, version)
        expression, sql_source = compile_metric_sql(
            metric, binding_by_role, fact_functions.get(metric_id), columns
        )
        expression = expression or str(metric["browse"].get("formula") or metric.get("formulaText") or "")
        if not expression:
            expression = f"metric:{metric_id}"

        fact_table = ""
        time_dimension = ""
        if binding_by_role:
            numerator = binding_by_role.get("numerator")
            if numerator:
                fact_table = numerator["fact_table"]
                time_dimension = numerator["window_column"]

        osi_metrics.append(
            OsiMetric(
                name=metric_id,
                description=metric_description(metric),
                expression=[OsiDialectExpression(dialect="ANSI_SQL", expression=expression)],
                custom_extensions=OsiCustomExtension(
                    data_source_id="platform",
                    source_table=fact_table,
                    unit=str(metric.get("unit") or ""),
                    return_type=str(metric["browse"].get("metricKind") or ""),
                    time_dimension=time_dimension,
                    ontology_concepts=[],
                    defined_by="platform",
                    effective_from=str(metric.get("effectiveDate") or ""),
                    label=str(metric.get("name") or ""),
                ),
            )
        )
        reconcile_inputs[metric_id] = {
            "publishable": bool(entry["publishable"]),
            "executable": bool(entry["executable"]),
            "executionReasonCode": entry.get("executionReasonCode"),
            "executionReason": entry.get("executionReason"),
            "definitionVersion": version,
            "sqlSource": sql_source,
            "sourceTable": fact_table,
        }

    document = OsiDocument(datasets=datasets, metrics=osi_metrics)
    write_json(out / "snapshot" / "reconcile_inputs.json", reconcile_inputs)
    (out / "snapshot").mkdir(parents=True, exist_ok=True)
    (out / "snapshot" / "metrics.osi.yaml").write_text(
        serialize_osi_yaml(document), encoding="utf-8"
    )

    sources = {}
    for payload in reconcile_inputs.values():
        sources[payload["sqlSource"]] = sources.get(payload["sqlSource"], 0) + 1
    print(f"metrics={len(osi_metrics)} datasets={len(datasets)} sources={sources}")
    print(f"out={out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
