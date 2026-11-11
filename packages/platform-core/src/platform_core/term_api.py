# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Terms surface for the P4 ops (F58/F59).

Reads ``term:TermEntry`` rows from the named graph that actually carries the
lexicon folio for the namespace (the published T-Box pointer is preferred when
it does). The same loader backs the legacy ``/browse/terms`` panel and the
contract-shaped ``GET /namespaces/{namespaceId}/terms`` route, so the two cannot
drift.

The seven F59 columns are: classLabel, label, status, confidence, guardRegex,
canonicalFor, suppressedSurface. `anchorClasses` counts distinct forClass
targets (F58).
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

_SKOS = "http://www.w3.org/2004/02/skos/core#"
_TERM = "https://w3id.org/fsldm/terms#"

PAGE_DEFAULT = 100
PAGE_MAX = 500
STATUS_VALUES = ("evidenced", "inferred")


def _binding(binding: dict[str, Any], name: str) -> str | None:
    term = (binding.get("values") or {}).get(name)
    if not isinstance(term, dict):
        return None
    kind = term.get("kind")
    if kind == "iri":
        return term.get("iri")
    if kind == "bnode":
        return term.get("label")
    return term.get("value")


def _local_name(iri: str | None) -> str | None:
    if not iri:
        return None
    for sep in ("#", "/"):
        if sep in iri:
            return iri.rsplit(sep, 1)[-1]
    return iri


def _current_graph(runtime: Any) -> str | None:
    pointer = runtime.ontology.current()
    return pointer.get("graph") if pointer else None


def _term_graphs(runtime: Any) -> list[str]:
    """Named graphs that actually carry ``term:TermEntry`` rows.

    The lexicon folio is written to its own graph by the ontology seeder, so a
    published T-Box pointer does not imply the terms live in that graph. Asking
    the store which graph holds the entries keeps the listing honest instead of
    reporting a zero count for a graph that never carried them.
    """
    rows = runtime.graph.query(
        f"""
        SELECT DISTINCT ?g WHERE {{
          GRAPH ?g {{ ?s a <{_TERM}TermEntry> }}
        }}
        """
    ).get("bindings", [])
    graphs: list[str] = []
    for row in rows:
        graph = _binding(row, "g")
        if graph and graph not in graphs:
            graphs.append(graph)
    return sorted(graphs)


def _resolve_graph(runtime: Any, namespace_id: str | None) -> str | None:
    pointer_graph = _current_graph(runtime)
    graphs = _term_graphs(runtime)
    if namespace_id:
        graphs = [graph for graph in graphs if namespace_id in graph]
    if not graphs:
        return None
    if pointer_graph in graphs:
        return pointer_graph
    return graphs[0]


def _as_float(value: str | None) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def load_terms(
    runtime: Any,
    *,
    namespace_id: str | None = None,
    query: str | None = None,
    status: str | None = None,
    limit: int = PAGE_DEFAULT,
    offset: int = 0,
) -> dict[str, Any]:
    """Return the alias entries plus F58 counts, filtered and paged."""
    graph_iri = _resolve_graph(runtime, namespace_id)
    empty = {
        "pointer": runtime.ontology.current(),
        "graph": None,
        "entries": [],
        "classes": [],
        "counts": {"anchorClasses": 0, "altLabels": 0, "evidenced": 0, "inferred": 0},
        "total": 0,
        "offset": offset,
        "limit": limit,
    }
    if not graph_iri:
        return empty

    rows = runtime.graph.query(
        f"""
        SELECT ?e ?c ?classLabel ?label ?status ?confidence ?guard ?canonical ?suppressed
          FROM <{graph_iri}> WHERE {{
          ?e a <{_TERM}TermEntry> ;
             <{_TERM}forClass> ?c ;
             <{_TERM}label> ?label .
          OPTIONAL {{ ?c <{_SKOS}prefLabel> ?classLabel }}
          OPTIONAL {{ ?e <{_TERM}status> ?status }}
          OPTIONAL {{ ?e <{_TERM}confidence> ?confidence }}
          OPTIONAL {{ ?e <{_TERM}guardRegex> ?guard }}
          OPTIONAL {{ ?c <{_TERM}canonicalFor> ?canonical }}
          OPTIONAL {{ ?c <{_TERM}suppressedSurface> ?suppressed }}
        }}
        """
    ).get("bindings", [])

    entries: dict[str, dict[str, Any]] = {}
    for row in rows:
        entry_iri = _binding(row, "e")
        if not entry_iri:
            continue
        entry = entries.setdefault(
            entry_iri,
            {
                "entry": entry_iri,
                "classIri": _binding(row, "c"),
                "classLabel": _binding(row, "classLabel") or _local_name(_binding(row, "c")),
                "label": _binding(row, "label"),
                "status": _local_name(_binding(row, "status")),
                "confidence": _as_float(_binding(row, "confidence")),
                "guardRegex": _binding(row, "guard"),
                "canonicalFor": [],
                "suppressedSurface": [],
            },
        )
        for field, key in (("canonical", "canonicalFor"), ("suppressed", "suppressedSurface")):
            value = _binding(row, field)
            if value and value not in entry[key]:
                entry[key].append(value)

    items = sorted(entries.values(), key=lambda item: (item["classIri"] or "", item["label"] or ""))
    classes: dict[str, dict[str, Any]] = {}
    for entry in items:
        class_iri = entry["classIri"]
        if not class_iri:
            continue
        group = classes.setdefault(
            class_iri,
            {"iri": class_iri, "label": entry["classLabel"], "aliases": []},
        )
        group["aliases"].append(entry["label"])

    filtered = items
    if query:
        needle = query.strip().lower()
        if needle:
            filtered = [
                item
                for item in filtered
                if needle in (item["label"] or "").lower()
                or needle in (item["classLabel"] or "").lower()
                or needle in (item["classIri"] or "").lower()
            ]
    if status:
        filtered = [item for item in filtered if item["status"] == status]

    return {
        "pointer": runtime.ontology.current(),
        "graph": graph_iri,
        "entries": filtered[offset : offset + limit],
        "classes": sorted(classes.values(), key=lambda item: item["label"] or ""),
        "counts": {
            "anchorClasses": len(classes),
            "altLabels": len(items),
            "evidenced": sum(1 for item in items if item["status"] == "evidenced"),
            "inferred": sum(1 for item in items if item["status"] == "inferred"),
        },
        "total": len(filtered),
        "offset": offset,
        "limit": limit,
    }


def register_term_routes(app: FastAPI, runtime: Any) -> None:
    """Mount the contract-shaped terms route on the platform-core app."""

    @app.get("/namespaces/{namespace_id}/terms")
    def list_terms(
        namespace_id: str,
        q: str | None = None,
        status: str | None = None,
        limit: int = PAGE_DEFAULT,
        offset: int = 0,
    ) -> Any:
        if status is not None and status not in STATUS_VALUES:
            return JSONResponse(
                status_code=400,
                content={
                    "code": "ValidationError",
                    "message": f"status must be one of {list(STATUS_VALUES)}",
                },
            )
        if limit < 1 or limit > PAGE_MAX:
            return JSONResponse(
                status_code=400,
                content={
                    "code": "ValidationError",
                    "message": f"limit must be between 1 and {PAGE_MAX}",
                },
            )
        if offset < 0:
            return JSONResponse(
                status_code=400,
                content={
                    "code": "ValidationError",
                    "message": "offset must be >= 0",
                },
            )
        result = load_terms(
            runtime,
            namespace_id=namespace_id,
            query=q,
            status=status,
            limit=limit,
            offset=offset,
        )
        counts = result["counts"]
        return {
            "namespaceId": namespace_id,
            "graph": result["graph"],
            "counts": {
                "anchorClasses": counts["anchorClasses"],
                "termEntries": counts["altLabels"],
                "evidenced": counts["evidenced"],
                "inferred": counts["inferred"],
            },
            "entries": result["entries"],
            "total": result["total"],
            "offset": result["offset"],
            "limit": result["limit"],
        }
