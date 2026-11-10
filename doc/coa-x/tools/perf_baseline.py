#!/usr/bin/env python3
"""Read-only performance baseline for the COA local stack.

Two subcommands:

  load     – append synthetic ontology triples to the namespace graph until it
             holds exactly --target quads (for the data-amplification runs).
  measure  – hit every read-only route and write p50/p95/max/count as JSON.

Run against the isolated stack from perf-baseline-stack.ps1 (PG 6144,
Oxigraph 8088, engine 8812, context-manager 8898, bridge 8899).

Only GET plus the read-only POST /sparql are issued. No write route is called.

Examples:
  python perf_baseline.py load --target 100000
  python perf_baseline.py measure --label 100k --quads 100000 --iterations 6 --out 100k.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import quote

import httpx

OXIGRAPH = "http://127.0.0.1:8088"
BRIDGE = "http://127.0.0.1:8899"
ONTOLOGY_ID = "https://w3id.org/fsldm/codes"
GRAPH_BASE = "https://coa.local/graph"
DEFAULT_NS = "3f2a9c1e-7b4d-4e2a-9c6f-1a2b3c4d5e6f"

NAMED_GRAPH = f"{GRAPH_BASE}/{DEFAULT_NS}/{quote(ONTOLOGY_ID, safe='')}"
METRIC_GRAPH = f"{GRAPH_BASE}/{DEFAULT_NS}/{quote('urn:coa:vocab#GovernedMetrics', safe='')}"

RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
COA_VOCAB = "urn:coa:vocab#"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"

# Fixed, pre-existing IRIs used by /graph/path and /entities/{id}. They come
# from the bundled FS-LDM folios, so they exist before any synthetic load.
PATH_START = "https://w3id.org/fsldm/investment#InvestmentObjective"
PATH_END = "https://w3id.org/fsldm/core#Classification"
ENTITY_IRI = "https://w3id.org/fsldm/party#PartyRelationship"


# ── Oxigraph helpers ────────────────────────────────────────────────────────


def sparql_select(query: str) -> list[dict[str, str]]:
    r = httpx.post(
        f"{OXIGRAPH}/query",
        content=query.encode(),
        headers={"Content-Type": "application/sparql-query", "Accept": "application/sparql-results+json"},
        timeout=120.0,
    )
    r.raise_for_status()
    return r.json()["results"]["bindings"]


def graph_quad_count(graph: str) -> int:
    rows = sparql_select(f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{graph}> {{ ?s ?p ?o }} }}")
    return int(rows[0]["n"]["value"])


def gsp_post(graph: str, body: bytes, content_type: str = "application/n-triples") -> None:
    r = httpx.post(
        f"{OXIGRAPH}/store",
        params={"graph": graph},
        content=body,
        headers={"Content-Type": content_type},
        timeout=300.0,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"GSP POST failed {r.status_code}: {r.text[:500]}")


def seed_metrics(count: int = 100) -> None:
    """Materialise `count` synthetic GovernedMetric rows in the metric graph.

    Metrics are a fixed-size dimension; they do not scale with the quad
    amplification, so this is done once per fresh Oxigraph.
    """
    lines: list[str] = []
    for i in range(count):
        uri = f"<urn:coa:{DEFAULT_NS}:metric:perf_metric_{i:04d}>"
        label = f"Perf Metric {i:04d}"
        lines += [
            f"{uri} <{RDF_TYPE}> <http://www.w3.org/2002/07/owl#Class> .",
            f"{uri} <{RDFS}subClassOf> <{COA_VOCAB}GovernedMetric> .",
            f'{uri} <{RDFS}label> "{label}" .',
            f'{uri} <{COA_VOCAB}displayLabel> "{label}" .',
            f'{uri} <{COA_VOCAB}dataSourceId> "ds-perf" .',
            f'{uri} <{COA_VOCAB}sourceTable> "perf_table_{i:04d}" .',
            f'{uri} <{COA_VOCAB}bindingStatus> "bound" .',
            f'{uri} <{COA_VOCAB}expressionDialects> "[{{\\"dialect\\":\\"ansiSql\\",\\"expression\\":\\"SUM(x)\\"}}]" .',
            f"{uri} <{COA_VOCAB}publishable> \"true\"^^<http://www.w3.org/2001/XMLSchema#boolean> .",
        ]
    gsp_post(METRIC_GRAPH, "\n".join(lines).encode())


def load_until(target: int, batch_quads: int = 25_000, start_index: int = 0) -> None:
    current = graph_quad_count(NAMED_GRAPH)
    print(f"current quads: {current}, target: {target}")
    if current > target:
        raise SystemExit(f"graph already holds {current} quads, above target {target}; drop and reseed instead")
    if current == target:
        print("already at target")
        return

    added = 0
    i = start_index
    t0 = time.perf_counter()
    while current + added < target:
        remaining = target - current - added
        lines: list[str] = []
        # 4 triples per synthetic class: type, label, comment, subClassOf.
        per_entity = 4
        n_entities = min(batch_quads // per_entity, (remaining + per_entity - 1) // per_entity)
        for _ in range(n_entities):
            iri = f"<https://w3id.org/fsldm/perf#C{i}>"
            nxt = f"<https://w3id.org/fsldm/perf#C{i + 1}>"
            lines += [
                f"{iri} <{RDF_TYPE}> <{OWL}Class> .",
                f'{iri} <{RDFS}label> "Perf Class {i}"@en .',
                f'{iri} <{RDFS}comment> "synthetic perf class {i}" .',
                f"{iri} <{RDFS}subClassOf> {nxt} .",
            ]
            i += 1
        # Pad the final batch with filler statements so the total is exact.
        deficit = remaining - len(lines)
        if deficit > 0 and n_entities < batch_quads // per_entity:
            for k in range(deficit):
                lines.append(f'<https://w3id.org/fsldm/perf#Filler> <{RDFS}comment> "filler {k}" .')
        gsp_post(NAMED_GRAPH, "\n".join(lines).encode())
        added += len(lines)
        print(f"  +{len(lines):>7} quads  total={current + added}  ({time.perf_counter() - t0:.1f}s)")

    final = graph_quad_count(NAMED_GRAPH)
    print(f"final quads: {final}")
    if final != target:
        raise SystemExit(f"quad count mismatch: {final} != {target}")


# ── Route probing ───────────────────────────────────────────────────────────


@dataclass
class Route:
    name: str
    method: str
    path: str
    params: dict[str, str] | None = None
    body: dict[str, Any] | None = None
    timeout_s: float = 90.0
    rows: Callable[[Any], int | None] = lambda _j: None
    note: str = ""
    is_error_expected: bool = False
    attempts: int | None = None  # overrides iterations+1 (e.g. a runaway probe)


def _rows(obj: Any, *keys: str) -> int | None:
    if not isinstance(obj, dict):
        return None
    for k in keys:
        v = obj.get(k)
        if isinstance(v, list):
            return len(v)
        if isinstance(v, int):
            return v
    return None


def routes(ns: str) -> list[Route]:
    b = f"/namespaces/{ns}"
    q = quote
    return [
        Route(
            "system-health", "GET", "/system-health",
            rows=lambda j: len(j.get("components", {})) if isinstance(j, dict) else None,
        ),
        Route(
            "metrics", "GET", f"{b}/metrics",
            rows=lambda j: _rows(j, "metrics"),
            note="list is capped at 51 by the service",
        ),
        Route(
            "dictionaries", "GET", f"{b}/dictionaries",
            rows=lambda j: _rows(j, "items"),
        ),
        Route(
            "answer-quality", "GET", "/answer/quality",
            rows=lambda j: _rows(j, "cases"),
        ),
        Route(
            f"entities/{{id}}", "GET", f"/entities/{q(ENTITY_IRI, safe='')}",
            rows=lambda j: _rows(j, "properties"),
        ),
        Route(
            "graph-statements", "GET", f"{b}/graph/statements",
            params={"limit": "50"},
            timeout_s=180.0,
            rows=lambda j: _rows(j, "statements"),
        ),
        Route(
            "graph-canvas", "GET", f"{b}/graph/canvas",
            params={"limit": "50"},
            timeout_s=180.0,
            rows=lambda j: (_rows(j, "nodes") or 0) + (_rows(j, "edges") or 0) if isinstance(j, dict) else None,
        ),
        Route(
            "graph-path", "GET", f"{b}/graph/path",
            params={"start": PATH_START, "end": PATH_END, "max_hops": "3"},
            timeout_s=180.0,
            rows=lambda j: _rows(j, "paths"),
        ),
        Route(
            "sparql-simple", "POST", f"{b}/sparql",
            body={"sparql": "SELECT ?s ?label WHERE { ?s <http://www.w3.org/2000/01/rdf-schema#label> ?label } LIMIT 10"},
            timeout_s=60.0,
            rows=lambda j: _rows(j, "rows"),
        ),
        Route(
            "graph-search-kind", "GET", f"{b}/graph/search",
            params={"q": "Class", "kind": "class", "limit": "50"},
            timeout_s=180.0,
            rows=lambda j: _rows(j, "hits"),
            note="kind=class avoids the 50k-quad unfiltered budget",
        ),
        Route(
            "graph-search-nokind", "GET", f"{b}/graph/search",
            params={"q": "Class", "limit": "50"},
            timeout_s=180.0,
            rows=lambda j: _rows(j, "hits"),
            note="subject to the 50,000-quad hard cap (422 above it)",
        ),
        Route(
            "sparql-timeout", "POST", f"{b}/sparql",
            body={
                "sparql": (
                    "SELECT (COUNT(*) AS ?n) WHERE { "
                    "?a ?b ?c . ?d ?e ?f . ?g ?h ?i }"
                )
            },
            timeout_s=40.0,
            rows=lambda j: _rows(j, "rows"),
            note=(
                "cross-product COUNT; trips the 10 s console deadline. Probed once: "
                "Oxigraph does not cancel the query, so repeats stack runaway work"
            ),
            attempts=1,
        ),
    ]


def percentile(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def measure(base: str, ns: str, iterations: int, quads: int, label: str, out: str, only: set[str] | None = None) -> None:
    client = httpx.Client(timeout=None)
    results: list[dict[str, Any]] = []

    for route in routes(ns):
        if only and route.name not in only:
            continue
        times: list[float] = []
        statuses: list[int] = []
        last_json: Any = None
        error: str | None = None
        errors: list[str] = []
        total_attempts = route.attempts if route.attempts else iterations + 1
        warmup = 0 if route.attempts else 1
        for n in range(total_attempts):
            t0 = time.perf_counter()
            try:
                r = client.request(
                    route.method,
                    base + route.path,
                    params=route.params,
                    json=route.body,
                    timeout=route.timeout_s,
                )
                dt = (time.perf_counter() - t0) * 1000
                statuses.append(r.status_code)
                try:
                    last_json = r.json()
                except ValueError:
                    last_json = None
                if n >= warmup:
                    times.append(dt)
                if r.status_code >= 400:
                    detail = ""
                    if isinstance(last_json, dict):
                        detail = str(last_json.get("detail") or last_json.get("error") or last_json)[:300]
                    errors.append(f"{r.status_code} {detail}")
            except Exception as exc:  # timeout / connect / protocol
                dt = (time.perf_counter() - t0) * 1000
                if n >= warmup:
                    times.append(dt)
                statuses.append(-1)
                error = f"{type(exc).__name__}: {exc}"[:300]
                errors.append(error)
            # Let an exploded backend settle; the Oxigraph query is not
            # cancelled when the 10 s console deadline fires.
            if route.name == "sparql-timeout":
                time.sleep(10)

        entry = {
            "route": route.name,
            "method": route.method,
            "path": route.path,
            "params": route.params,
            "note": route.note,
            "attempts": total_attempts,
            "p50_ms": round(percentile(times, 0.50), 1),
            "p95_ms": round(percentile(times, 0.95), 1),
            "max_ms": round(max(times), 1) if times else None,
            "status": sorted(set(statuses)),
            "returned_rows": route.rows(last_json) if last_json is not None else None,
            "samples_ms": [round(x, 1) for x in times],
            "error": error or (errors[-1] if errors else None),
        }
        results.append(entry)
        # Persist after every route so a wedged backend cannot lose earlier numbers.
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(
                {"label": label, "quads": quads, "iterations": iterations, "namespace": ns, "results": results},
                fh,
                ensure_ascii=False,
                indent=2,
            )
        print(
            f"{route.name:<20} p50={entry['p50_ms']:>8} p95={entry['p95_ms']:>8} "
            f"max={str(entry['max_ms']):>8} status={entry['status']} rows={entry['returned_rows']}"
        )

    doc = {"label": label, "quads": quads, "iterations": iterations, "namespace": ns, "results": results}
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
    print(f"wrote {out}")


def seed_dictionaries(rows: int, ns: str, source: str = "ds-perf", dsn: str = "postgresql://platform:platform_dev@127.0.0.1:6144/serve_local") -> None:
    """Seed a single source with `rows` dictionary columns.

    The platform-core app inside the bridge reads PLATFORM__DATABASE__URL,
    which is serve_local (not the control-plane `platform` DB).
    """
    import psycopg

    run_id = f"perf-seed-{rows}"
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM platform.dictionary_column WHERE namespace_id=%s AND source_id=%s",
                (ns, source),
            )
            cur.execute(
                "DELETE FROM platform.dictionary_refresh_run WHERE namespace_id=%s AND source_id=%s",
                (ns, source),
            )
            cur.execute(
                """
                INSERT INTO platform.dictionary_refresh_run
                  (run_id, namespace_id, source_id, idempotency_key, requested_by,
                   status, started_at, finished_at, processed, inserted)
                VALUES (%s,%s,%s,%s,%s,'succeeded', now(), now(), %s, %s)
                """,
                (run_id, ns, source, f"perf-{rows}", "perf-baseline", rows, rows),
            )
            with cur.copy(
                "COPY platform.dictionary_column "
                "(namespace_id, source_id, catalog_name, schema_name, table_name, column_name, "
                " data_type, is_nullable, comment, source_kind, binding_method, last_refresh_run_id) "
                "FROM STDIN"
            ) as copy:
                for i in range(rows):
                    copy.write_row(
                        (
                            ns, source, "perf_catalog", "perf_schema",
                            f"perf_table_{i // 100:05d}", f"col_{i:07d}",
                            "text", True, None, "postgresql", "none", run_id,
                        )
                    )
        conn.commit()
    print(f"seeded {rows} dictionary columns for source {source}")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_load = sub.add_parser("load")
    p_load.add_argument("--target", type=int, required=True)
    p_load.add_argument("--start-index", type=int, default=0)
    p_load.add_argument("--seed-metrics", type=int, default=100)

    p_measure = sub.add_parser("measure")
    p_measure.add_argument("--label", required=True)
    p_measure.add_argument("--quads", type=int, required=True)
    p_measure.add_argument("--iterations", type=int, default=6)
    p_measure.add_argument("--namespace", default=DEFAULT_NS)
    p_measure.add_argument("--base-url", default=BRIDGE)
    p_measure.add_argument("--out", required=True)
    p_measure.add_argument("--only", default="", help="comma-separated route names")

    p_dict = sub.add_parser("seed-dict")
    p_dict.add_argument("--rows", type=int, required=True)
    p_dict.add_argument("--namespace", default=DEFAULT_NS)

    args = ap.parse_args()
    if args.cmd == "load":
        if graph_quad_count(METRIC_GRAPH) == 0:
            seed_metrics(args.seed_metrics)
        load_until(args.target, start_index=args.start_index)
    elif args.cmd == "seed-dict":
        seed_dictionaries(args.rows, args.namespace)
    else:
        only = {x.strip() for x in args.only.split(",") if x.strip()}
        measure(args.base_url, args.namespace, args.iterations, args.quads, args.label, args.out, only)
    return 0


if __name__ == "__main__":
    sys.exit(main())
