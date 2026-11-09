"""COA-facing operations: shapes that exist in the Smithy contract.

Only operations with a real COA counterpart live here. The primitive gateway
routes (``/graph/query``, ``/vector/search``, ``/query/execute``) remain
internal; this module implements the higher-level operation the COA data layer
actually exposes.

First (and only, for now) mapped operation:

- ``DataLayerService.GraphTraverse`` — ``POST
  /namespaces/{namespaceId}/graph/traverse``. Input ``startUri``,
  ``maxDepth``, ``relationshipFilter``, ``direction``, ``maxResults``; output
  ``entities`` / ``relationships`` / ``trace``. The local executor is
  ``GraphClient.query`` reading SPARQL, not a new graph port.
- ``PlatformKnowledgeService.GetEntity`` — ``GET
  /namespaces/{namespaceId}/graph/entity?uri=``. Input ``uri``; output
  ``entity`` / ``statements``. Also ``GraphClient.query``; no new graph port.

Known local limits, stated rather than hidden:

- namespace: the local graph is single-namespace, so ``namespaceId`` is
  validated as a UUID but does not partition data.
- depth: COA accepts 1–5 and currently traverses 2 hops; this does the same.
- ``relationshipFilter``: accepted and validated, not applied — same as COA's
  current behaviour.
- ``direction``: implemented here (COA accepts and validates it but currently
  follows both directions).
"""

from __future__ import annotations

import time
from typing import Any

RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
_DIRECTIONS = {"outgoing", "incoming", "both"}
_MAX_HOPS = 2


class CoaValidationError(ValueError):
    """A request that the COA contract would reject with 400."""


class CoaEntityNotFound(LookupError):
    """``GetEntity`` found no statement for the IRI (COA ``NotFoundError``)."""


def _local_name(uri: str) -> str:
    for separator in ("#", "/"):
        if separator in uri:
            tail = uri.rsplit(separator, 1)[1]
            if tail:
                return tail
    return uri


def _check_iri(value: str, field: str) -> str:
    if not value or any(ch in value for ch in ' <>"'):
        raise CoaValidationError(f"{field} must be a non-empty IRI without whitespace or angle brackets")
    return value


def _values(uris: list[str]) -> str:
    return " ".join(f"<{uri}>" for uri in uris)


def _hop_query(frontier: list[str], direction: str) -> str:
    """One-hop SELECT from a set of frontier IRIs; literals never become entities."""
    seeds = _values(frontier)

    def patterns(seed: str) -> list[str]:
        # Default graph and named graphs both count; Oxigraph puts published
        # T-Box triples in a named graph, while simple stores use the default.
        return [
            f"{{ VALUES ?{seed} {{ {seeds} }} ?s ?p ?o . }}",
            f"{{ VALUES ?{seed} {{ {seeds} }} GRAPH ?g {{ ?s ?p ?o }} }}",
        ]

    branches = []
    if direction in ("outgoing", "both"):
        branches.extend(patterns("s"))
    if direction in ("incoming", "both"):
        branches.extend(patterns("o"))
    body = " UNION\n  ".join(branches)
    return (
        f"PREFIX rdfs: <{RDFS_LABEL}>\n"
        "SELECT ?s ?p ?o ?sl ?ol WHERE {\n"
        f"  {body}\n"
        "  FILTER(isIRI(?o))\n"
        "  OPTIONAL { ?s rdfs:label ?sl }\n"
        "  OPTIONAL { GRAPH ?lg1 { ?s rdfs:label ?sl } }\n"
        "  OPTIONAL { ?o rdfs:label ?ol }\n"
        "  OPTIONAL { GRAPH ?lg2 { ?o rdfs:label ?ol } }\n"
        "}"
    )


async def graph_traverse(
    graph_client: Any,
    namespace: str,
    *,
    start_uri: str,
    max_depth: int = 2,
    direction: str = "both",
    relationship_filter: list[str] | None = None,
    max_results: int = 100,
) -> dict[str, Any]:
    """``DataLayerService.GraphTraverse`` over a ``GraphClient``."""
    start_uri = _check_iri(start_uri, "startUri")
    if direction not in _DIRECTIONS:
        raise CoaValidationError(
            f"direction must be one of {', '.join(sorted(_DIRECTIONS))}, got {direction!r}"
        )
    if not 1 <= max_depth <= 5:
        raise CoaValidationError(f"maxDepth must be in [1, 5], got {max_depth}")
    if not 1 <= max_results <= 1000:
        raise CoaValidationError(f"maxResults must be in [1, 1000], got {max_results}")
    for value in relationship_filter or []:
        _check_iri(value, "relationshipFilter member")

    hops = min(max_depth, _MAX_HOPS)
    entities: dict[str, dict[str, Any]] = {start_uri: {"uri": start_uri, "label": _local_name(start_uri)}}
    relationships: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str, str]] = set()
    frontier = [start_uri]
    visited = {start_uri}
    trace: list[dict[str, Any]] = []

    def admit(uri: str, label: str | None) -> bool:
        record = entities.get(uri)
        if record is None:
            if len(entities) >= max_results:
                return False
            entities[uri] = {"uri": uri, "label": label or _local_name(uri)}
        elif label and record["label"] == _local_name(uri):
            record["label"] = label
        return True

    for hop in range(1, hops + 1):
        started = time.perf_counter()
        rows = await graph_client.query(_hop_query(frontier, direction))
        discovered: set[str] = set()
        for row in rows:
            source, predicate, target = row.get("s"), row.get("p"), row.get("o")
            if not (source and predicate and target):
                continue
            if not (admit(source, row.get("sl")) and admit(target, row.get("ol"))):
                continue
            edge = (source, predicate, target)
            if edge not in seen_edges:
                seen_edges.add(edge)
                relationships.append({"sourceUri": source, "predicateUri": predicate, "targetUri": target})
            for uri in (source, target):
                if uri not in visited:
                    discovered.add(uri)
        trace.append(
            {
                "step": f"graphTraverse.hop{hop}",
                "status": "success",
                "durationMs": int((time.perf_counter() - started) * 1000),
                "detail": (
                    f"namespace={namespace}, direction={direction}, "
                    f"newEntities={len(discovered)}, relationships={len(seen_edges)}"
                ),
            }
        )
        if not discovered:
            break
        frontier = sorted(discovered)[: max_results - len(visited) if len(visited) < max_results else 0]
        if not frontier:
            break
        visited |= discovered

    return {"entities": list(entities.values()), "relationships": relationships, "trace": trace}


def _entity_query(uri: str, *, literal: bool) -> str:
    """Statements whose subject is exactly ``uri``, split by object kind."""
    condition = "FILTER(!isIRI(?o))" if literal else "FILTER(isIRI(?o))"
    return (
        "SELECT ?p ?o WHERE {\n"
        f"  VALUES ?s {{ <{uri}> }}\n"
        "  { ?s ?p ?o . } UNION { GRAPH ?g { ?s ?p ?o } }\n"
        f"  {condition}\n"
        "}"
    )


async def get_entity(graph_client: Any, *, uri: str) -> dict[str, Any]:
    """``PlatformKnowledgeService.GetEntity`` over a ``GraphClient``.

    Returns the entity's own statements (not its neighbours); ``label`` and
    ``type`` are read from those statements, then fall back to the IRI's local
    name. No statement means the IRI is absent, reported as ``NotFoundError``.
    """
    uri = _check_iri(uri, "uri")
    iri_rows = await graph_client.query(_entity_query(uri, literal=False))
    literal_rows = await graph_client.query(_entity_query(uri, literal=True))

    statements: list[dict[str, Any]] = []
    seen: set[tuple[str, str, bool]] = set()

    def add(predicate: str, obj: str, object_is_literal: bool) -> None:
        key = (predicate, obj, object_is_literal)
        if key in seen:
            return
        seen.add(key)
        statements.append(
            {"subject": uri, "predicate": predicate, "object": obj, "objectIsLiteral": object_is_literal}
        )

    for row in iri_rows:
        if row.get("p") and row.get("o"):
            add(row["p"], row["o"], False)
    for row in literal_rows:
        if row.get("p") and row.get("o"):
            add(row["p"], row["o"], True)

    if not statements:
        raise CoaEntityNotFound(uri)

    labels = [item["object"] for item in statements if item["predicate"] == RDFS_LABEL]
    types = [item["object"] for item in statements if item["predicate"] == RDF_TYPE]
    entity: dict[str, Any] = {"uri": uri, "label": labels[0] if labels else _local_name(uri)}
    if types:
        entity["type"] = types[0]
    entity["properties"] = [
        {"predicate": item["predicate"], "value": item["object"]}
        for item in statements
        if item["objectIsLiteral"]
    ]
    return {"entity": entity, "statements": statements}


__all__ = ["CoaEntityNotFound", "CoaValidationError", "get_entity", "graph_traverse"]
