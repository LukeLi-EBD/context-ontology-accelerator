"""D1-2 canvas provider: full bounded multi-hop canvas (read-only).

Contract: doc/_design/53 (port), 55 (simple landing), 62 (this slice).

Differences from ``simple`` (same public signatures):

- hops up to 6, nodes up to 1000, edges up to 1500, paths up to 50;
- ``path()`` uses a bidirectional BFS (both sides expand ``ceil(hops/2)``
  layers, which provably covers every simple path of length <= hops) and then
  enumerates *all* simple paths in the merged region, not just the shortest
  predecessor DAG;
- predicate-kind filtering (object/datatype/annotation/rdf) via T-Box kinds;
- server-side aggregation (degree, edge weight, class/predicate buckets);
- cursor pagination and explicit truncation reasons (``stats.truncation``);
- ``hasRef`` is filled from real evidence: approved extraction candidates
  (document chunks, via ``source_ref``) and PROV ``src://`` refs. No ref means
  ``false``; nothing is synthesised.

Hard query rules are inherited from simple and are asserted by unit tests:
two plain queries per layer (out/in), ``VALUES ?g {..} GRAPH ?g {...}``, never
``GRAPH ?g { ... UNION ... }``, a ``LIMIT`` on every SPARQL query, and all caps
applied before the query is built.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import math
import time
from typing import Any

from .. import source_ref
from ..errors import PortError
from ..ports import Manifest
from .canvas_simple import (
    OWL,
    PLATFORM_GRAPH_PREFIX,
    PROPERTY_KINDS,
    RDF,
    RDFS,
    RDF_TYPE,
    RDFS_LABEL,
    _batches,
    _binding,
    _iri,
    _literal,
    _local_name,
)

log = logging.getLogger(__name__)

PROV_GRAPH = "urn:platform:prov"
PROV_USED = "http://www.w3.org/ns/prov#used"
RDFS_SEE_ALSO = RDFS + "seeAlso"

HARD_HOPS = 6
HARD_NODES = 1000
HARD_EDGES = 1500
HARD_PATHS = 50
HARD_TIMEOUT_MS = 5000
HARD_PAGE_SIZE = 200
FRONTIER_BATCH = 50
ENRICH_BATCH = 200
REF_BATCH = 100
PATH_VISIT_CAP = 12000
BUCKET_LIMIT = 50
PAGE_CACHE_TTL_S = 60

_KIND_ALIASES = {
    "object": OWL + "ObjectProperty",
    "objectproperty": OWL + "ObjectProperty",
    "datatype": OWL + "DatatypeProperty",
    "datatypeproperty": OWL + "DatatypeProperty",
    "annotation": OWL + "AnnotationProperty",
    "annotationproperty": OWL + "AnnotationProperty",
    "rdf": RDF + "Property",
    "rdfproperty": RDF + "Property",
    "property": RDF + "Property",
}


def _empty_walk(start: str, reason: str | None = None) -> dict[str, Any]:
    return {
        "nodes": {start: {"iri": start, "label": _local_name(start), "types": [],
                          "source": {"graph": None, "hasRef": False}}},
        "edges": [],
        "adj": {},
        "depth": {start: 0},
        "truncated": False,
        "reasons": [],
        "reason": reason,
    }


def _cursor_encode(offset: int, fingerprint: str) -> str:
    raw = json.dumps({"v": 1, "o": offset, "f": fingerprint},
                     separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _cursor_decode(cursor: str, fingerprint: str) -> int:
    bad = PortError(
        code="InvalidArgument",
        message="cursor does not match this canvas query (stale or malformed)",
        provider="full",
        provider_code="E_CANVAS_BAD_CURSOR",
        details={"cursor": cursor},
    )
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded))
    except Exception as exc:  # noqa: BLE001 - any decode failure is a bad cursor
        raise bad from exc
    if (
        not isinstance(data, dict)
        or data.get("v") != 1
        or data.get("f") != fingerprint
        or not isinstance(data.get("o"), int)
        or data["o"] < 0
    ):
        raise bad
    return int(data["o"])


class FullCanvas:
    """D1-2 full implementation. Same public signatures as ``SimpleCanvas``."""

    port = "CanvasPort"

    def __init__(
        self,
        config: Any,
        graph: Any,
        ontology: Any,
        reasoning: Any,
        metadata: Any = None,
    ) -> None:
        # ``config`` is the whole PlatformConfig so readable graphs match
        # webui._graphs (config.reasoning.abox_graphs lives outside .canvas).
        self._config = config.canvas
        self._abox_graphs = list(config.reasoning.abox_graphs)
        self._graph = graph
        self._ontology = ontology
        self._reasoning = reasoning
        self._metadata = metadata
        self._predicate_cache: tuple[str, dict[str, frozenset[str]]] | None = None
        self._page_cache: dict[str, tuple[float, dict[str, Any]]] = {}

    # ---- manifest -----------------------------------------------------

    def manifest(self) -> Manifest:
        return Manifest(
            provider="full",
            port=self.port,
            capabilities=[
                "canvas.subgraph",
                "canvas.path",
                "canvas.expand",
                "canvas.multipath",
                "canvas.bidirectional",
                "canvas.predicate-filter",
                "canvas.aggregate",
                "canvas.pagination",
                "canvas.hasRef",
            ],
            limits={
                "hops": self.max_hops,
                "nodes": self.max_nodes,
                "edges": self.max_edges,
                "paths": self.max_paths,
                "timeout_ms": self.timeout_ms,
                "page_size": HARD_PAGE_SIZE,
            },
            notes={
                "slice": "D1-2",
                "query_shape": "values-graph, two plain queries per layer, no union, LIMIT on every query",
                "layout": "force (structure only, degrees/clusters, no x/y)",
                "read_only": True,
                "ref_sources": ["extraction_candidate", "urn:platform:prov"],
            },
        )

    # ---- effective limits (config clamped to full hard caps) ----------

    @property
    def max_hops(self) -> int:
        return max(1, min(int(self._config.full_max_hops), HARD_HOPS))

    @property
    def max_nodes(self) -> int:
        return max(1, min(int(self._config.max_nodes), HARD_NODES))

    @property
    def max_edges(self) -> int:
        return max(1, min(int(self._config.max_edges), HARD_EDGES))

    @property
    def max_paths(self) -> int:
        return max(1, min(int(self._config.max_paths), HARD_PATHS))

    @property
    def timeout_ms(self) -> int:
        return max(100, min(int(self._config.timeout_ms), HARD_TIMEOUT_MS))

    # ---- public contract (identical signatures to SimpleCanvas) -------

    def subgraph(
        self,
        start: str,
        *,
        hops: int = 1,
        max_nodes: int = 200,
        max_edges: int = 400,
        include_types: bool = True,
        include_source: bool = True,
        graphs: list[str] | None = None,
    ) -> dict[str, Any]:
        return self._subgraph_impl(
            start,
            hops=hops,
            max_nodes=max_nodes,
            max_edges=max_edges,
            include_types=include_types,
            include_source=include_source,
            graphs=graphs,
            predicate_types=None,
        )

    def path(
        self,
        source: str,
        target: str,
        *,
        max_hops: int = 3,
        max_paths: int = 20,
        max_nodes: int = 200,
        include_types: bool = True,
        include_source: bool = True,
        graphs: list[str] | None = None,
    ) -> dict[str, Any]:
        return self._path_impl(
            source,
            target,
            max_hops=max_hops,
            max_paths=max_paths,
            max_nodes=max_nodes,
            include_types=include_types,
            include_source=include_source,
            graphs=graphs,
            predicate_types=None,
        )

    def expand(
        self,
        node: str,
        *,
        hops: int = 1,
        max_nodes: int = 100,
        max_edges: int = 200,
        include_types: bool = True,
        include_source: bool = True,
        graphs: list[str] | None = None,
    ) -> dict[str, Any]:
        result = self._subgraph_impl(
            node,
            hops=hops,
            max_nodes=max_nodes,
            max_edges=max_edges,
            include_types=include_types,
            include_source=include_source,
            graphs=graphs,
            predicate_types=None,
        )
        # The CanvasPort signature has no base-subgraph parameter, so the delta
        # is relative to an empty canvas: the whole expansion is the addition.
        result["merged"] = True
        result["addedNodes"] = [item["iri"] for item in result["nodes"]]
        result["addedEdges"] = list(result["edges"])
        return result

    # ---- full-only extension used by the G10 route --------------------

    def query(
        self,
        start: str,
        *,
        target: str | None = None,
        hops: int = 1,
        max_nodes: int | None = None,
        max_edges: int | None = None,
        max_paths: int | None = None,
        include_types: bool = True,
        include_source: bool = True,
        graphs: list[str] | None = None,
        predicate_types: list[str] | None = None,
        page_size: int = 100,
        cursor: str | None = None,
        aggregate: bool = True,
    ) -> dict[str, Any]:
        """Filtered, paginated, aggregated canvas for ``/browse/canvas/full``.

        The port methods stay untouched; this extension is only reachable when
        ``canvas.provider=full`` (the route checks the manifest provider).
        """
        if page_size < 1 or page_size > HARD_PAGE_SIZE:
            raise PortError(
                code="InvalidArgument",
                message=f"pageSize={page_size} is outside 1..{HARD_PAGE_SIZE}",
                provider="full",
                provider_code="E_CANVAS_PAGE_EXCEEDED",
                details={"pageSize": page_size, "limit": HARD_PAGE_SIZE},
            )
        kinds = _normalize_predicate_types(predicate_types)
        nodes_cap = max(1, min(int(max_nodes or self.max_nodes), self.max_nodes))
        edges_cap = max(1, min(int(max_edges or self.max_edges), self.max_edges))
        paths_cap = max(1, min(int(max_paths or self.max_paths), self.max_paths))
        hop_limit = self.max_hops
        if hops < 1 or hops > hop_limit:
            raise PortError(
                code="InvalidArgument",
                message=f"maxHops={hops} is outside the full provider range 1..{hop_limit}",
                provider="full",
                provider_code="E_CANVAS_HOPS_EXCEEDED",
                details={"maxHops": hops, "limit": hop_limit},
            )
        fingerprint = _fingerprint(
            start, target, hops, nodes_cap, edges_cap, paths_cap,
            include_types, include_source, graphs, kinds,
        )
        offset = _cursor_decode(cursor, fingerprint) if cursor else 0
        full = self._cached_full(
            fingerprint,
            start,
            target,
            hops,
            nodes_cap,
            edges_cap,
            paths_cap,
            include_types,
            include_source,
            graphs,
            kinds,
        )
        nodes_all = full["nodes"]
        edges_all = full["edges"]
        if offset > max(len(nodes_all), len(edges_all)):
            raise PortError(
                code="InvalidArgument",
                message="cursor offset is beyond the current result",
                provider="full",
                provider_code="E_CANVAS_BAD_CURSOR",
                details={"offset": offset, "nodes": len(nodes_all), "edges": len(edges_all)},
            )
        page_nodes = nodes_all[offset : offset + page_size]
        page_edges = edges_all[offset : offset + page_size]
        has_more = offset + page_size < max(len(nodes_all), len(edges_all))
        full["nodes"] = page_nodes
        full["edges"] = page_edges
        full["page"] = {
            "size": page_size,
            "offset": offset,
            "cursor": cursor,
            "nextCursor": _cursor_encode(offset + page_size, fingerprint) if has_more else None,
            "totalNodes": len(nodes_all),
            "totalEdges": len(edges_all),
        }
        full["aggregates"] = (
            self._aggregate(page_nodes, nodes_all, edges_all, page_edges)
            if aggregate
            else None
        )
        full["truncation"] = dict(full["stats"]["truncation"])
        stats = full["stats"]
        stats["nodes"] = len(page_nodes)
        stats["edges"] = len(page_edges)
        stats["totalNodes"] = len(nodes_all)
        stats["totalEdges"] = len(edges_all)
        # Layout is page-scoped too: the browser never receives 1000 layout
        # entries per page; degree comes from the server aggregate above.
        layout = full.get("layout") or {}
        page_iris = {node["iri"] for node in page_nodes}
        full["layout"] = {
            "mode": layout.get("mode", "force"),
            "nodes": [
                item for item in layout.get("nodes", []) if item["iri"] in page_iris
            ],
            "seed": layout.get("seed", 0),
        }
        return full

    # ---- subgraph / path implementations ------------------------------

    def _subgraph_impl(
        self,
        start: str,
        *,
        hops: int,
        max_nodes: int,
        max_edges: int,
        include_types: bool,
        include_source: bool,
        graphs: list[str] | None,
        predicate_types: frozenset[str] | None,
    ) -> dict[str, Any]:
        started = time.monotonic()
        trace: dict[str, float] = {}
        self._require_iri(start, "start")
        hops = self._clamp_hops(hops)
        allowed = self._allowed_graphs(graphs)
        nodes_cap = max(1, min(int(max_nodes), self.max_nodes))
        edges_cap = max(1, min(int(max_edges), self.max_edges))
        walk = self._walk(
            start,
            hops=hops,
            graphs=allowed,
            max_nodes=nodes_cap,
            max_edges=edges_cap,
            started=started,
            trace=trace,
            predicate_kinds=predicate_types,
        )
        nodes = dict(walk["nodes"])
        edges = list(walk["edges"])
        self._enrich(nodes, allowed, include_types, started, trace)
        coverage = self._attach_refs(
            nodes, edges, allowed, include_source, started, trace
        )
        return self._result(
            mode="subgraph",
            start=start,
            target=None,
            graphs=allowed,
            walk=walk,
            nodes=nodes,
            edges=edges,
            paths=[],
            include_source=include_source,
            hops=hops,
            started=started,
            trace=trace,
            coverage=coverage,
            paths_cap=self.max_paths,
            nodes_cap=nodes_cap,
            edges_cap=edges_cap,
        )

    def _path_impl(
        self,
        source: str,
        target: str,
        *,
        max_hops: int,
        max_paths: int,
        max_nodes: int,
        include_types: bool,
        include_source: bool,
        graphs: list[str] | None,
        predicate_types: frozenset[str] | None,
    ) -> dict[str, Any]:
        started = time.monotonic()
        trace: dict[str, float] = {}
        self._require_iri(source, "source")
        self._require_iri(target, "target")
        hops = self._clamp_hops(max_hops)
        paths_cap = max(1, min(int(max_paths), self.max_paths))
        allowed = self._allowed_graphs(graphs)
        nodes_cap = max(1, min(int(max_nodes), self.max_nodes))
        walk = self._walk_bidirectional(
            source,
            target,
            hops=hops,
            graphs=allowed,
            max_nodes=nodes_cap,
            max_edges=self.max_edges,
            started=started,
            trace=trace,
            predicate_kinds=predicate_types,
        )
        paths, paths_truncated = self._enumerate_paths(
            source, target, walk["adj"], paths_cap, hops, started, trace
        )
        nodes: dict[str, dict[str, Any]] = {}
        edges: list[dict[str, Any]] = []
        for item in paths:
            for iri in item["nodes"]:
                if iri not in nodes:
                    nodes[iri] = dict(
                        walk["nodes"].get(iri) or self._node(iri, None)
                    )
            for edge in item["edges"]:
                if edge not in edges:
                    edges.append(edge)
        if not paths and source in walk["nodes"]:
            # Same shape as simple: an empty path result still names the start.
            nodes[source] = dict(walk["nodes"][source])
        if nodes:
            self._enrich(nodes, allowed, include_types, started, trace)
        coverage = self._attach_refs(
            nodes, edges, allowed, include_source, started, trace
        )
        empty_reason: str | None = None
        if not paths:
            empty_reason = walk["reason"] or (
                "E_CANVAS_TRUNCATED" if walk["truncated"] else "E_PATH_NOT_FOUND"
            )
        reasons = list(walk["reasons"])
        if paths_truncated and "E_CANVAS_PATHS_TRUNCATED" not in reasons:
            reasons.append("E_CANVAS_PATHS_TRUNCATED")
        return self._result(
            mode="path",
            start=source,
            target=target,
            graphs=allowed,
            walk=walk,
            nodes=nodes,
            edges=edges,
            paths=paths,
            include_source=include_source,
            hops=hops,
            started=started,
            trace=trace,
            coverage=coverage,
            paths_cap=paths_cap,
            empty_reason=empty_reason,
            extra_truncated=paths_truncated,
            extra_reasons=reasons,
            nodes_cap=nodes_cap,
            edges_cap=self.max_edges,
        )

    # ---- validation and graph selection -------------------------------

    def _require_iri(self, value: str, field: str) -> None:
        if not _iri(value):
            raise PortError(
                code="InvalidArgument",
                message=f"{field} is not a safe absolute IRI",
                provider="full",
                provider_code="E_CANVAS_BAD_IRI",
                details={"field": field, "value": value},
            )

    def _clamp_hops(self, hops: int) -> int:
        if hops < 1 or hops > self.max_hops:
            raise PortError(
                code="InvalidArgument",
                message=(
                    f"maxHops={hops} is outside the full provider range "
                    f"1..{self.max_hops}"
                ),
                provider="full",
                provider_code="E_CANVAS_HOPS_EXCEEDED",
                details={"maxHops": hops, "limit": self.max_hops},
            )
        return hops

    def _allowed_graphs(self, requested: list[str] | None) -> list[str]:
        allowed = self._graphs()
        if requested:
            bad = [graph for graph in requested if graph not in allowed]
            if bad:
                raise PortError(
                    code="PermissionDenied",
                    message="requested graph is outside the current readable set",
                    provider="full",
                    provider_code="E_CANVAS_GRAPH_FORBIDDEN",
                    details={"graphs": bad, "allowed": allowed},
                )
            return list(dict.fromkeys(requested))
        return allowed

    def _graphs(self) -> list[str]:
        """Same graph set as ``webui._graphs`` and SimpleCanvas."""
        graphs: list[str] = []
        pointer = self._ontology.current()
        if pointer and pointer.get("graph"):
            graphs.append(str(pointer["graph"]))
        try:
            status = self._reasoning.status()
            target = (status.get("pointer") or {}).get("targetGraph")
            if target:
                graphs.append(str(target))
        except PortError:
            pass
        graphs.extend(str(iri) for iri in self._abox_graphs)
        return [
            graph
            for graph in dict.fromkeys(graphs)
            if graph.startswith(PLATFORM_GRAPH_PREFIX)
        ]

    def _predicates(
        self, started: float, trace: dict[str, float]
    ) -> dict[str, frozenset[str]]:
        pointer = self._ontology.current()
        tbox = str((pointer or {}).get("graph") or "")
        if not tbox.startswith(PLATFORM_GRAPH_PREFIX):
            return {}
        if self._predicate_cache and self._predicate_cache[0] == tbox:
            return self._predicate_cache[1]
        # Oxigraph requires commas in IN(...) lists; space-separated entries
        # raise "expected ENCODE_FOR_URI" (same bug existed in simple).
        kinds = ", ".join(f"<{kind}>" for kind in PROPERTY_KINDS)
        result = self._query(
            f"""
            SELECT ?p ?k WHERE {{
              VALUES ?g {{ <{tbox}> }}
              GRAPH ?g {{ ?p a ?k }}
              FILTER(?k IN ({kinds}))
            }}
            LIMIT 20000
            """,
            started,
            "whitelist",
            trace,
        )
        predicates: dict[str, set[str]] = {}
        for row in result.get("bindings", []):
            p = _binding(row, "p")
            k = _binding(row, "k")
            if p and k:
                predicates.setdefault(p, set()).add(k)
        mapping = {p: frozenset(values) for p, values in predicates.items()}
        self._predicate_cache = (tbox, mapping)
        return mapping

    # ---- BFS ----------------------------------------------------------

    def _walk(
        self,
        start: str,
        *,
        hops: int,
        graphs: list[str],
        max_nodes: int,
        max_edges: int,
        started: float,
        trace: dict[str, float],
        predicate_kinds: frozenset[str] | None,
    ) -> dict[str, Any]:
        if not graphs:
            return _empty_walk(start, "E_CANVAS_NO_GRAPH")
        predicates = self._filtered_predicates(started, trace, predicate_kinds)
        if not predicates:
            reason = (
                "E_CANVAS_PREDICATE_EMPTY"
                if predicate_kinds
                else "E_CANVAS_TBOX_EMPTY"
            )
            return _empty_walk(start, reason)
        nodes: dict[str, dict[str, Any]] = {start: self._node(start, None)}
        edges: list[dict[str, Any]] = []
        adj: dict[str, list[dict[str, Any]]] = {}
        depth: dict[str, int] = {start: 0}
        seen: set[tuple[str, str, str]] = set()
        reasons: list[str] = []
        truncated = False
        frontier = [start]
        for layer in range(1, hops + 1):
            if not frontier:
                break
            if len(nodes) >= max_nodes:
                truncated = True
                _reason(reasons, "E_CANVAS_NODES_TRUNCATED")
                break
            if len(edges) >= max_edges:
                truncated = True
                _reason(reasons, "E_CANVAS_EDGES_TRUNCATED")
                break
            next_frontier: list[str] = []
            for batch in _batches(frontier):
                rows, directions = self._fetch_layer(
                    batch,
                    graphs,
                    predicates,
                    remaining=max(1, max_edges - len(edges) + 1),
                    started=started,
                    trace=trace,
                )
                for s, p, o, graph in rows:
                    direction = directions[(s, p, o)]
                    if len(edges) >= max_edges:
                        truncated = True
                        _reason(reasons, "E_CANVAS_EDGES_TRUNCATED")
                        break
                    entry = {"s": s, "p": p, "o": o, "g": graph}
                    if (s, p, o) not in seen:
                        seen.add((s, p, o))
                        edges.append(
                            {
                                "s": s,
                                "p": p,
                                "o": o,
                                "dir": direction,
                                "source": {"graph": graph, "hasRef": False},
                            }
                        )
                        adj.setdefault(s, []).append(entry)
                        adj.setdefault(o, []).append(entry)
                    other = o if direction == "out" else s
                    parent = s if direction == "out" else o
                    touched = nodes.get(parent)
                    if touched is not None and touched["source"]["graph"] is None:
                        touched["source"]["graph"] = graph
                    if other not in depth:
                        if len(nodes) >= max_nodes:
                            truncated = True
                            _reason(reasons, "E_CANVAS_NODES_TRUNCATED")
                            continue
                        depth[other] = layer
                        nodes[other] = self._node(other, graph)
                        next_frontier.append(other)
                if len(edges) >= max_edges or len(nodes) >= max_nodes:
                    break
            frontier = next_frontier
        walk = {
            "nodes": nodes,
            "edges": edges,
            "adj": adj,
            "depth": depth,
            "truncated": truncated,
            "reasons": reasons,
            "reason": None,
        }
        return walk

    def _walk_bidirectional(
        self,
        source: str,
        target: str,
        *,
        hops: int,
        graphs: list[str],
        max_nodes: int,
        max_edges: int,
        started: float,
        trace: dict[str, float],
        predicate_kinds: frozenset[str] | None,
    ) -> dict[str, Any]:
        """Bidirectional BFS: each side expands ceil(hops/2) undirected layers.

        For any simple path v0..vL (L <= hops), the node at position ceil(L/2)
        is within ceil(hops/2) of both ends, so the union of both balls contains
        every node and edge of every such path. Path enumeration then runs over
        the merged adjacency and can therefore return longer alternatives.
        """
        if not graphs:
            return _empty_walk(source, "E_CANVAS_NO_GRAPH")
        predicates = self._filtered_predicates(started, trace, predicate_kinds)
        if not predicates:
            reason = (
                "E_CANVAS_PREDICATE_EMPTY"
                if predicate_kinds
                else "E_CANVAS_TBOX_EMPTY"
            )
            return _empty_walk(source, reason)
        nodes: dict[str, dict[str, Any]] = {source: self._node(source, None)}
        if target != source:
            nodes[target] = self._node(target, None)
        edges: list[dict[str, Any]] = []
        adj: dict[str, list[dict[str, Any]]] = {}
        depth: dict[str, int] = {source: 0}
        if target != source:
            depth[target] = hops
        seen: set[tuple[str, str, str]] = set()
        expanded: set[str] = set()
        reasons: list[str] = []
        state = {
            "truncated": False,
            "reasons": reasons,
        }
        side_depth = max(1, int(math.ceil(hops / 2)))
        self._expand_side(
            source, "source", side_depth, graphs, predicates, nodes, edges, adj,
            depth, seen, expanded, max_nodes, max_edges, started, trace, state,
        )
        self._expand_side(
            target, "target", side_depth, graphs, predicates, nodes, edges, adj,
            depth, seen, expanded, max_nodes, max_edges, started, trace, state,
        )
        return {
            "nodes": nodes,
            "edges": edges,
            "adj": adj,
            "depth": depth,
            "truncated": bool(state["truncated"]),
            "reasons": reasons,
            "reason": None,
        }

    def _expand_side(
        self,
        seed: str,
        side: str,
        side_depth: int,
        graphs: list[str],
        predicates: dict[str, frozenset[str]],
        nodes: dict[str, dict[str, Any]],
        edges: list[dict[str, Any]],
        adj: dict[str, list[dict[str, Any]]],
        depth: dict[str, int],
        seen: set[tuple[str, str, str]],
        expanded: set[str],
        max_nodes: int,
        max_edges: int,
        started: float,
        trace: dict[str, float],
        state: dict[str, Any],
    ) -> None:
        local_depth: dict[str, int] = {seed: 0}
        frontier = [seed]
        for layer in range(1, side_depth + 1):
            if not frontier:
                break
            if state["truncated"]:
                break
            next_frontier: list[str] = []
            pending = [node for node in frontier if node not in expanded]
            for node in pending:
                expanded.add(node)
            for batch in _batches(pending):
                rows, directions = self._fetch_layer(
                    batch,
                    graphs,
                    predicates,
                    remaining=max(1, max_edges - len(edges) + 1),
                    started=started,
                    trace=trace,
                )
                for s, p, o, graph in rows:
                    direction = directions[(s, p, o)]
                    if len(edges) >= max_edges:
                        state["truncated"] = True
                        _reason(state["reasons"], "E_CANVAS_EDGES_TRUNCATED")
                        break
                    entry = {"s": s, "p": p, "o": o, "g": graph}
                    if (s, p, o) not in seen:
                        seen.add((s, p, o))
                        edges.append(
                            {
                                "s": s,
                                "p": p,
                                "o": o,
                                "dir": direction,
                                "source": {"graph": graph, "hasRef": False},
                            }
                        )
                        adj.setdefault(s, []).append(entry)
                        adj.setdefault(o, []).append(entry)
                    other = o if direction == "out" else s
                    parent = s if direction == "out" else o
                    touched = nodes.get(parent)
                    if touched is not None and touched["source"]["graph"] is None:
                        touched["source"]["graph"] = graph
                    if other not in local_depth:
                        local_depth[other] = layer
                        if other not in nodes:
                            if len(nodes) >= max_nodes:
                                state["truncated"] = True
                                _reason(state["reasons"], "E_CANVAS_NODES_TRUNCATED")
                                continue
                            nodes[other] = self._node(other, graph)
                            # Layout-only cluster hint; the path depth comes
                            # from the returned path itself.
                            depth.setdefault(other, layer)
                        next_frontier.append(other)
                if len(edges) >= max_edges or len(nodes) >= max_nodes:
                    state["truncated"] = True
                    _reason(
                        state["reasons"],
                        "E_CANVAS_EDGES_TRUNCATED"
                        if len(edges) >= max_edges
                        else "E_CANVAS_NODES_TRUNCATED",
                    )
                    break
            frontier = next_frontier

    def _filtered_predicates(
        self,
        started: float,
        trace: dict[str, float],
        predicate_kinds: frozenset[str] | None,
    ) -> dict[str, frozenset[str]]:
        predicates = self._predicates(started, trace)
        if predicate_kinds:
            return {
                p: kinds
                for p, kinds in predicates.items()
                if kinds & predicate_kinds
            }
        return predicates

    def _fetch_layer(
        self,
        frontier: list[str],
        graphs: list[str],
        predicates: dict[str, frozenset[str]],
        *,
        remaining: int,
        started: float,
        trace: dict[str, float],
    ) -> tuple[list[tuple[str, str, str, str | None]], dict[tuple[str, str, str], str]]:
        """Two plain queries (outgoing/incoming). No UNION under a variable graph."""
        graph_values = " ".join(f"<{graph}>" for graph in graphs)
        predicate_values = " ".join(f"<{predicate}>" for predicate in sorted(predicates))
        point_values = " ".join(f"<{point}>" for point in frontier)
        outgoing = self._query(
            f"""
            SELECT ?s ?p ?o ?g WHERE {{
              VALUES ?g {{ {graph_values} }}
              VALUES ?p {{ {predicate_values} }}
              GRAPH ?g {{ VALUES ?s {{ {point_values} }} ?s ?p ?o }}
            }}
            LIMIT {remaining}
            """,
            started,
            "outgoing",
            trace,
        )
        incoming = self._query(
            f"""
            SELECT ?s ?p ?o ?g WHERE {{
              VALUES ?g {{ {graph_values} }}
              VALUES ?p {{ {predicate_values} }}
              GRAPH ?g {{ VALUES ?o {{ {point_values} }} ?s ?p ?o }}
            }}
            LIMIT {remaining}
            """,
            started,
            "incoming",
            trace,
        )
        rows: list[tuple[str, str, str, str | None]] = []
        directions: dict[tuple[str, str, str], str] = {}
        for direction, result in (("out", outgoing), ("in", incoming)):
            for row in result.get("bindings", []):
                s = _binding(row, "s")
                p = _binding(row, "p")
                o = _binding(row, "o")
                if not (s and p and o):
                    continue  # literal values never become canvas nodes
                rows.append((s, p, o, _binding(row, "g")))
                directions.setdefault((s, p, o), direction)
        return rows, directions

    def _query(
        self,
        sparql: str,
        started: float,
        stage: str,
        trace: dict[str, float],
    ) -> dict[str, Any]:
        self._guard(started, stage)
        begin = time.monotonic()
        result = self._graph.query(sparql)
        elapsed = (time.monotonic() - begin) * 1000
        trace[stage] = round(trace.get(stage, 0.0) + elapsed, 1)
        self._guard(started, stage)
        return result

    def _guard(self, started: float, stage: str) -> None:
        if time.monotonic() - started > self.timeout_ms / 1000:
            raise PortError(
                code="DeadlineExceeded",
                message=f"canvas budget of {self.timeout_ms}ms expired during {stage}",
                provider="full",
                provider_code="E_CANVAS_TIMEOUT",
                details={"stage": stage, "timeoutMs": self.timeout_ms},
            )

    # ---- path enumeration ---------------------------------------------

    def _enumerate_paths(
        self,
        source: str,
        target: str,
        adj: dict[str, list[dict[str, Any]]],
        max_paths: int,
        max_hops: int,
        started: float,
        trace: dict[str, float],
    ) -> tuple[list[dict[str, Any]], bool]:
        """DFS over the merged bidirectional adjacency (all simple paths <= hops)."""
        if source == target:
            return [
                {"nodes": [source], "edges": [], "length": 0}
            ], False
        begin = time.monotonic()
        results: list[dict[str, Any]] = []
        seen_sequences: set[tuple[str, ...]] = set()
        visits = 0
        capped = False

        def walk(
            current: str,
            node_chain: list[str],
            edge_chain: list[dict[str, Any]],
            visited: set[str],
        ) -> None:
            nonlocal visits, capped
            if capped:
                return
            visits += 1
            if visits >= PATH_VISIT_CAP:
                capped = True
                return
            if visits % 200 == 0:
                self._guard(started, "path-enumeration")
            if current == target:
                sequence = tuple(node_chain)
                if sequence not in seen_sequences:
                    seen_sequences.add(sequence)
                    results.append(
                        {
                            "nodes": list(sequence),
                            "edges": list(edge_chain),
                            "length": len(sequence) - 1,
                        }
                    )
                return
            if len(edge_chain) >= max_hops:
                return
            for entry in adj.get(current, []):
                if entry["s"] == current:
                    nxt = entry["o"]
                    direction = "out"
                else:
                    nxt = entry["s"]
                    direction = "in"
                if nxt in visited:
                    continue  # cycle guard: a path never repeats a node
                walk(
                    nxt,
                    node_chain + [nxt],
                    edge_chain
                    + [
                        {
                            "s": entry["s"],
                            "p": entry["p"],
                            "o": entry["o"],
                            "dir": direction,
                            "source": {
                                "graph": entry["g"],
                                "hasRef": False,
                            },
                        }
                    ],
                    visited | {nxt},
                )

        walk(source, [source], [], {source})
        trace["path-enumeration"] = round(
            trace.get("path-enumeration", 0.0) + (time.monotonic() - begin) * 1000, 1
        )
        results.sort(
            key=lambda item: (
                item["length"],
                _path_weight(item["edges"]),
                tuple(item["nodes"]),
            )
        )
        truncated = capped or len(results) > max_paths
        return results[:max_paths], truncated

    # ---- enrichment and provenance ------------------------------------

    def _enrich(
        self,
        nodes: dict[str, dict[str, Any]],
        graphs: list[str],
        include_types: bool,
        started: float,
        trace: dict[str, float],
    ) -> None:
        if not graphs or not nodes:
            return
        # Two plain queries per readable graph, never ``OPTIONAL`` under a
        # variable graph: Oxigraph does not finish that shape (measured 35s
        # timeout on 50 subjects), while ``GRAPH <g> { VALUES ?s {..} .. }``
        # answers in ~3ms. The whitelist is still explicit: ``graphs`` is the
        # server-side set, one constant graph IRI per query.
        iri_batch = ENRICH_BATCH
        for batch in _batches(list(nodes.keys()), iri_batch):
            point_values = " ".join(f"<{iri}>" for iri in batch)
            limit = len(batch) * 3
            lookups = [("label", RDFS_LABEL)]
            if include_types:
                lookups.append(("type", RDF_TYPE))
            for key, predicate in lookups:
                for graph in graphs:
                    result = self._query(
                        f"""
                        SELECT ?s ?value WHERE {{
                          VALUES ?s {{ {point_values} }}
                          GRAPH <{graph}> {{ ?s <{predicate}> ?value }}
                        }}
                        LIMIT {limit}
                        """,
                        started,
                        "enrich",
                        trace,
                    )
                    for row in result.get("bindings", []):
                        subject = _binding(row, "s")
                        entry = nodes.get(subject or "")
                        if entry is None:
                            continue
                        value = _literal(row, "value")
                        if not value:
                            continue
                        if key == "label":
                            entry["label"] = value
                        else:
                            type_iri = _binding(row, "value")
                            if type_iri and type_iri not in entry["types"]:
                                entry["types"].append(type_iri)

    def _attach_refs(
        self,
        nodes: dict[str, dict[str, Any]],
        edges: list[dict[str, Any]],
        graphs: list[str],
        include_source: bool,
        started: float,
        trace: dict[str, float],
    ) -> dict[str, Any]:
        node_total = len(nodes)
        edge_total = len(edges)
        if not include_source:
            # The caller explicitly opted out of source summaries; do not spend
            # a provenance round-trip and never claim coverage.
            for node in nodes.values():
                node["source"] = {"graph": None, "hasRef": False}
            for edge in edges:
                edge["source"] = {"graph": None}
            return {
                "nodes": node_total,
                "nodesWithRef": 0,
                "edges": edge_total,
                "edgesWithRef": 0,
                "nodeRatio": 0.0,
                "edgeRatio": 0.0,
                "source": "skipped(includeSource=false)",
            }
        node_refs, edge_refs, info = self._refs_for(
            list(nodes.keys()), edges, graphs, started, trace
        )
        for iri, node in nodes.items():
            ref = node_refs.get(iri)
            source = node.setdefault("source", {"graph": None, "hasRef": False})
            if include_source and ref:
                source["hasRef"] = True
                source["ref"] = ref["ref"]
                source["refType"] = ref["type"]
                source["resolveUrl"] = ref["resolveUrl"]
            else:
                source["hasRef"] = False
        for edge in edges:
            key = (edge["s"], edge["p"], edge["o"])
            ref = edge_refs.get(key)
            source = edge.setdefault("source", {"graph": edge.get("graph"), "hasRef": False})
            if include_source and ref:
                source["hasRef"] = True
                source["ref"] = ref["ref"]
                source["refType"] = ref["type"]
                source["resolveUrl"] = ref["resolveUrl"]
            else:
                source["hasRef"] = False
        nodes_with_ref = sum(1 for iri in nodes if iri in node_refs)
        edges_with_ref = sum(
            1
            for edge in edges
            if (edge["s"], edge["p"], edge["o"]) in edge_refs
        )
        coverage = {
            "nodes": node_total,
            "nodesWithRef": nodes_with_ref,
            "edges": edge_total,
            "edgesWithRef": edges_with_ref,
            "nodeRatio": round(nodes_with_ref / node_total, 4) if node_total else 0.0,
            "edgeRatio": round(edges_with_ref / edge_total, 4) if edge_total else 0.0,
            "source": "extraction_candidate(approved,current-graph)+urn:platform:prov",
            **info,
        }
        return coverage

    def _refs_for(
        self,
        node_iris: list[str],
        edges: list[dict[str, Any]],
        graphs: list[str],
        started: float,
        trace: dict[str, float],
    ) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str, str], dict[str, Any]], dict[str, Any]]:
        node_refs: dict[str, dict[str, Any]] = {}
        edge_refs: dict[tuple[str, str, str], dict[str, Any]] = {}
        info: dict[str, Any] = {"refsMs": 0.0}
        if not node_iris and not edges:
            return node_refs, edge_refs, info
        begin = time.monotonic()
        # 1) PROV src:// refs (authoritative when present).
        if graphs:
            for batch in _batches(node_iris, REF_BATCH):
                try:
                    rows = self._prov_refs(batch, started, trace)
                except PortError:
                    raise
                except Exception as exc:  # noqa: BLE001 - provenance degrades, never breaks
                    log.warning("canvas PROV ref lookup failed: %s", exc)
                    info["error"] = "prov_unavailable"
                    rows = []
                for subject, ref in rows:
                    node_refs.setdefault(subject, ref)
        # 2) Approved extraction candidates (document-chunk evidence).
        if self._metadata is not None and graphs:
            try:
                node_refs = self._candidate_refs(
                    node_iris, edges, graphs, started, trace, node_refs, edge_refs
                )
            except PortError:
                raise
            except Exception as exc:  # noqa: BLE001 - provenance degrades, never breaks
                log.warning("canvas candidate ref lookup failed: %s", exc)
                info["error"] = "metadata_unavailable"
        info["refsMs"] = round((time.monotonic() - begin) * 1000, 1)
        return node_refs, edge_refs, info

    def _prov_refs(
        self, batch: list[str], started: float, trace: dict[str, float]
    ) -> list[tuple[str, dict[str, Any]]]:
        points = " ".join(f"<{iri}>" for iri in batch)
        result = self._query(
            f"""
            SELECT ?subject ?ref WHERE {{
              VALUES ?g {{ <{PROV_GRAPH}> }}
              VALUES ?subject {{ {points} }}
              GRAPH ?g {{
                ?activity <{PROV_USED}> ?subject .
                ?activity <{PROV_USED}> ?evidence .
                ?evidence <{RDFS_SEE_ALSO}> ?ref .
                FILTER(?subject != ?evidence)
              }}
            }}
            LIMIT {len(batch) * 10 + 10}
            """,
            started,
            "prov-refs",
            trace,
        )
        found: list[tuple[str, dict[str, Any]]] = []
        for row in result.get("bindings", []):
            subject = _binding(row, "subject")
            ref = _literal(row, "ref")
            if not subject or not ref or not ref.startswith("src://"):
                continue
            try:
                descriptor = _ref_summary(ref)
            except PortError:
                continue
            found.append((subject, descriptor))
        return found

    def _candidate_refs(
        self,
        node_iris: list[str],
        edges: list[dict[str, Any]],
        graphs: list[str],
        started: float,
        trace: dict[str, float],
        node_refs: dict[str, dict[str, Any]],
        edge_refs: dict[tuple[str, str, str], dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        begin = time.monotonic()
        wanted = set(node_iris)
        node_set = set(node_iris)
        wanted_edges = {(edge["s"], edge["p"], edge["o"]) for edge in edges}
        for edge in edges:
            wanted.add(edge["s"])
        if not wanted:
            return node_refs
        for batch in _batches(sorted(wanted), REF_BATCH):
            self._guard(started, "refs")
            rows = self._metadata.query(
                """
                SELECT c.subject_iri, c.predicate_iri, c.object_value,
                       c.document_id, c.chunk_id, ch.seq
                  FROM platform.extraction_candidate c
                  JOIN platform.document_chunk ch ON ch.chunk_id = c.chunk_id
                 WHERE c.state = 'approved'
                   AND c.object_kind = 'iri'
                   AND c.subject_iri = ANY(%s)
                   AND c.graph_iri = ANY(%s)
                 ORDER BY c.subject_iri, c.decided_at DESC NULLS LAST,
                          c.created_at DESC
                 LIMIT %s
                """,
                (batch, graphs, len(batch) * 20 + 1),
            )
            self._guard(started, "refs")
            for row in rows:
                subject = str(row["subject_iri"])
                predicate = str(row["predicate_iri"])
                obj = str(row["object_value"])
                descriptor = _chunk_ref_summary(row)
                if descriptor is None:
                    continue
                if subject in node_set:
                    node_refs.setdefault(subject, descriptor)
                key = (subject, predicate, obj)
                if key in wanted_edges:
                    edge_refs.setdefault(key, descriptor)
        trace["refs"] = round(trace.get("refs", 0.0) + (time.monotonic() - begin) * 1000, 1)
        return node_refs

    # ---- result shaping ----------------------------------------------

    def _node(self, iri: str, graph: str | None) -> dict[str, Any]:
        return {
            "iri": iri,
            "label": _local_name(iri),
            "types": [],
            "source": {"graph": graph, "hasRef": False},
        }

    def _cached_full(
        self,
        fingerprint: str,
        start: str,
        target: str | None,
        hops: int,
        max_nodes: int,
        max_edges: int,
        max_paths: int,
        include_types: bool,
        include_source: bool,
        graphs: list[str] | None,
        kinds: list[str] | None,
    ) -> dict[str, Any]:
        now = time.monotonic()
        cached = self._page_cache.get(fingerprint)
        if cached and now - cached[0] <= PAGE_CACHE_TTL_S:
            return _copy_result(cached[1])
        if target:
            result = self._path_impl(
                start,
                target,
                max_hops=hops,
                max_paths=max_paths,
                max_nodes=max_nodes,
                include_types=include_types,
                include_source=include_source,
                graphs=graphs,
                predicate_types=frozenset(kinds) if kinds else None,
            )
        else:
            result = self._subgraph_impl(
                start,
                hops=hops,
                max_nodes=max_nodes,
                max_edges=max_edges,
                include_types=include_types,
                include_source=include_source,
                graphs=graphs,
                predicate_types=frozenset(kinds) if kinds else None,
            )
        # Keep at most two queries; page cursors reuse the same compute.
        if len(self._page_cache) >= 2:
            oldest = min(self._page_cache.items(), key=lambda item: item[1][0])[0]
            self._page_cache.pop(oldest, None)
        self._page_cache[fingerprint] = (time.monotonic(), result)
        return _copy_result(result)

    def _aggregate(
        self,
        page_nodes: list[dict[str, Any]],
        all_nodes: list[dict[str, Any]],
        all_edges: list[dict[str, Any]],
        page_edges: list[dict[str, Any]],
    ) -> dict[str, Any]:
        degree: dict[str, dict[str, int]] = {}
        for edge in all_edges:
            degree.setdefault(edge["s"], {"in": 0, "out": 0})["out"] += 1
            degree.setdefault(edge["o"], {"in": 0, "out": 0})["in"] += 1
        node_degree = []
        for node in page_nodes:
            item = degree.get(node["iri"], {"in": 0, "out": 0})
            node_degree.append(
                {
                    "iri": node["iri"],
                    "in": item["in"],
                    "out": item["out"],
                    "total": item["in"] + item["out"],
                }
            )
        edge_weights = [
            {
                "s": edge["s"],
                "p": edge["p"],
                "o": edge["o"],
                "weight": _edge_weight(edge["p"]),
            }
            for edge in page_edges
        ]
        class_buckets: dict[str, int] = {}
        for node in all_nodes:
            for type_iri in node.get("types") or []:
                class_buckets[type_iri] = class_buckets.get(type_iri, 0) + 1
        predicate_buckets: dict[str, int] = {}
        for edge in all_edges:
            predicate_buckets[edge["p"]] = predicate_buckets.get(edge["p"], 0) + 1
        return {
            "nodeDegree": node_degree,
            "edgeWeights": edge_weights,
            "classBuckets": _buckets(class_buckets),
            "predicateBuckets": _buckets(predicate_buckets),
        }

    def _result(
        self,
        *,
        mode: str,
        start: str,
        target: str | None,
        graphs: list[str],
        walk: dict[str, Any],
        nodes: dict[str, dict[str, Any]],
        edges: list[dict[str, Any]],
        paths: list[dict[str, Any]],
        include_source: bool,
        hops: int,
        started: float,
        trace: dict[str, float],
        coverage: dict[str, Any],
        paths_cap: int,
        empty_reason: str | None = None,
        extra_truncated: bool = False,
        extra_reasons: list[str] | None = None,
        nodes_cap: int | None = None,
        edges_cap: int | None = None,
    ) -> dict[str, Any]:
        elapsed_ms = int(round((time.monotonic() - started) * 1000))
        nodes_cap = self.max_nodes if nodes_cap is None else nodes_cap
        edges_cap = self.max_edges if edges_cap is None else edges_cap
        reasons = list(dict.fromkeys((extra_reasons or []) + list(walk["reasons"])))
        truncated = bool(walk["truncated"] or extra_truncated)
        layout = self._layout(nodes, edges, walk.get("depth") or {})
        return {
            "provider": "full",
            "mode": mode,
            "start": start,
            "target": target,
            "graphs": graphs,
            "nodes": list(nodes.values()),
            "edges": list(edges),
            "paths": paths,
            "layout": layout,
            "truncated": truncated,
            "limits": {
                "hops": hops,
                "maxNodes": nodes_cap,
                "maxEdges": edges_cap,
                "maxPaths": paths_cap,
            },
            "stats": {
                "nodes": len(nodes),
                "edges": len(edges),
                "paths": len(paths),
                "elapsedMs": elapsed_ms,
                "timings": {key: round(value, 1) for key, value in trace.items()},
                "refCoverage": coverage,
                "truncation": {
                    "truncated": truncated,
                    "reasons": reasons,
                    "maxHops": hops,
                    "maxNodes": nodes_cap,
                    "maxEdges": edges_cap,
                    "maxPaths": paths_cap,
                },
            },
            "emptyReason": empty_reason or walk["reason"],
            "degraded": False,
        }

    def _layout(
        self,
        nodes: dict[str, dict[str, Any]],
        edges: list[dict[str, Any]],
        depth: dict[str, int],
    ) -> dict[str, Any]:
        degree: dict[str, int] = {}
        for edge in edges:
            degree[edge["s"]] = degree.get(edge["s"], 0) + 1
            degree[edge["o"]] = degree.get(edge["o"], 0) + 1
        items = [
            {
                "iri": iri,
                "degree": degree.get(iri, 0),
                "cluster": int(depth.get(iri, -1)),
            }
            for iri in nodes
        ]
        items.sort(key=lambda item: item["iri"])
        seed = int(
            hashlib.sha1("|".join(item["iri"] for item in items).encode("utf-8"))
            .hexdigest()[:8],
            16,
        )
        return {"mode": "force", "nodes": items, "seed": seed}


# ---- helpers ----------------------------------------------------------


def _copy_result(result: dict[str, Any]) -> dict[str, Any]:
    """Shallow copy with fresh page-level containers for cursor reuse."""
    copy = dict(result)
    copy["nodes"] = list(result.get("nodes") or [])
    copy["edges"] = list(result.get("edges") or [])
    copy["paths"] = list(result.get("paths") or [])
    copy["stats"] = dict(result.get("stats") or {})
    return copy


def _reason(reasons: list[str], code: str) -> None:
    if code not in reasons:
        reasons.append(code)


def _normalize_predicate_types(values: list[str] | None) -> list[str] | None:
    if not values:
        return None
    selected: list[str] = []
    for raw in values:
        token = str(raw or "").strip()
        if not token:
            continue
        if token in PROPERTY_KINDS:
            kind = token
        else:
            key = token.lower().replace("_", "").replace("-", "")
            kind = _KIND_ALIASES.get(key)
        if not kind:
            raise PortError(
                code="InvalidArgument",
                message=(
                    f"predicateTypes value {token!r} is not a known property kind; "
                    "use object/datatype/annotation/rdf or a full OWL kind IRI"
                ),
                provider="full",
                provider_code="E_CANVAS_BAD_PREDICATE_TYPE",
                details={"value": token},
            )
        if kind not in selected:
            selected.append(kind)
    return selected or None


def _fingerprint(*parts: Any) -> str:
    payload = json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def _edge_weight(predicate: str) -> float:
    if predicate == RDF_TYPE:
        return 0.5
    if predicate == RDFS_LABEL:
        return 0.75
    return 1.0


def _path_weight(edges: list[dict[str, Any]]) -> float:
    return round(sum(_edge_weight(str(edge["p"])) for edge in edges), 3)


def _buckets(counts: dict[str, int]) -> list[dict[str, Any]]:
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [
        {"iri": iri, "count": count}
        for iri, count in ordered[:BUCKET_LIMIT]
    ]


def _ref_summary(ref: str) -> dict[str, Any]:
    parsed = source_ref.parse_ref(ref)
    kind = parsed["kind"]
    return {
        "type": {
            "doc": source_ref.DOCUMENT_CHUNK,
            "fact": source_ref.FACT_ROW,
            "obs": source_ref.OBSERVATION_ROW,
            "obs-set": source_ref.OBSERVATION_SET,
        }[kind],
        "ref": ref,
        "resolveUrl": "/source/resolve?ref=" + _quote(ref),
    }


def _chunk_ref_summary(row: dict[str, Any]) -> dict[str, Any] | None:
    document_id = str(row.get("document_id") or "")
    seq = row.get("seq")
    if not document_id or seq is None:
        return None
    try:
        descriptor = source_ref.chunk_descriptor(document_id, int(seq))
        source_ref.parse_ref(str(descriptor["ref"]))
    except Exception:  # noqa: BLE001 - malformed row is skipped, never invented
        return None
    return descriptor


def _quote(value: str) -> str:
    from urllib.parse import quote

    return quote(value, safe="")
