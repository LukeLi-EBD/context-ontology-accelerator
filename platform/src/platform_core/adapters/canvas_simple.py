"""D1-1 canvas provider: bounded multi-hop BFS over the platform graph (read-only).

Design: doc/_design/53 (contract) and doc/_design/55 (landing notes).

Query shape is deliberately restricted (design 53 §4.3, C-01/C-02):
- two plain queries per BFS layer (outgoing + incoming), each batching the
  frontier with ``VALUES``; ``GRAPH ?g { ... UNION ... }`` is never generated
  because Oxigraph hangs on that shape (see ``webui.neighbors`` L271-L293).
- predicates come from the current T-Box whitelist (declared property kinds).
- only ``urn:platform:`` named graphs are readable.
- limits are truncated before the query is built, and one request has a
  whole-walk budget (``canvas.timeout_ms``, hard-capped at 500ms for simple).
"""

from __future__ import annotations

import re
import time
from typing import Any, Iterable

from ..errors import PortError
from ..ports import Manifest

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
RDF_TYPE = RDF + "type"
RDFS_LABEL = RDFS + "label"
IRI_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:[^<>\"{}|^`\\\s]+$")
PLATFORM_GRAPH_PREFIX = "urn:platform:"
PROPERTY_KINDS = (
    OWL + "ObjectProperty",
    OWL + "DatatypeProperty",
    OWL + "AnnotationProperty",
    RDF + "Property",
)

HARD_HOPS = 3
HARD_NODES = 200
HARD_EDGES = 400
HARD_PATHS = 20
HARD_TIMEOUT_MS = 500
FRONTIER_BATCH = 50


def _iri(value: Any) -> bool:
    return bool(IRI_RE.match(str(value or "")))


def _binding(row: dict[str, Any], name: str) -> str | None:
    """Return an IRI binding; literals and bnodes are not canvas nodes."""
    term = (row.get("values") or {}).get(name)
    if not isinstance(term, dict):
        return None
    if term.get("kind") == "iri":
        return term.get("iri")
    return None


def _literal(row: dict[str, Any], name: str) -> str | None:
    term = (row.get("values") or {}).get(name)
    if not isinstance(term, dict):
        return None
    if term.get("kind") == "iri":
        return term.get("iri")
    return term.get("value")


def _local_name(iri: str) -> str:
    for sep in ("#", "/"):
        if sep in iri:
            return iri.rsplit(sep, 1)[-1] or iri
    return iri


def _batches(items: list[str], size: int = FRONTIER_BATCH) -> Iterable[list[str]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


class SimpleCanvas:
    """D1-1 simple implementation (design 53 §4.1)."""

    port = "CanvasPort"

    def __init__(self, config: Any, graph: Any, ontology: Any, reasoning: Any) -> None:
        # ``config`` is the whole PlatformConfig so the readable graph set can
        # include cfg.reasoning.abox_graphs (design 53 §3.2, webui._graphs).
        self._config = config.canvas
        self._abox_graphs = list(config.reasoning.abox_graphs)
        self._graph = graph
        self._ontology = ontology
        self._reasoning = reasoning
        self._whitelist_cache: tuple[str, frozenset[str]] | None = None

    # ---- manifest -----------------------------------------------------

    def manifest(self) -> Manifest:
        return Manifest(
            provider="simple",
            port=self.port,
            capabilities=["canvas.subgraph", "canvas.path", "canvas.expand"],
            limits={
                "hops": self.max_hops,
                "nodes": self.max_nodes,
                "edges": self.max_edges,
                "paths": self.max_paths,
                "timeout_ms": self.timeout_ms,
            },
            notes={
                "slice": "D1-1",
                "query_shape": "values-graph, two plain queries per layer, no union",
                "layout": "none",
                "read_only": True,
            },
        )

    # ---- effective limits (config clamped to simple hard caps) --------

    @property
    def max_hops(self) -> int:
        return max(1, min(int(self._config.simple_max_hops), HARD_HOPS))

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

    # ---- public contract ---------------------------------------------

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
        started = time.monotonic()
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
        )
        return self._result(
            mode="subgraph",
            start=start,
            target=None,
            graphs=allowed,
            walk=walk,
            path_nodes=None,
            path_edges=None,
            paths=[],
            include_types=include_types,
            include_source=include_source,
            hops=hops,
            started=started,
            nodes_cap=nodes_cap,
            edges_cap=edges_cap,
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
        started = time.monotonic()
        self._require_iri(source, "source")
        self._require_iri(target, "target")
        hops = self._clamp_hops(max_hops)
        paths_cap = max(1, min(int(max_paths), self.max_paths))
        allowed = self._allowed_graphs(graphs)
        nodes_cap = max(1, min(int(max_nodes), self.max_nodes))
        walk = self._walk(
            source,
            hops=hops,
            graphs=allowed,
            max_nodes=nodes_cap,
            max_edges=self.max_edges,
            started=started,
            target=target,
        )
        paths = self._enumerate_paths(
            source, target, walk["parents"], paths_cap, hops
        )
        path_nodes: list[str] = []
        path_edges: list[dict[str, Any]] = []
        for item in paths:
            for node in item["nodes"]:
                if node not in path_nodes:
                    path_nodes.append(node)
            for edge in item["edges"]:
                if edge not in path_edges:
                    path_edges.append(edge)
        empty_reason: str | None = None
        if not paths:
            empty_reason = walk["reason"] or (
                "E_CANVAS_TRUNCATED" if walk["truncated"] else "E_PATH_NOT_FOUND"
            )
        return self._result(
            mode="path",
            start=source,
            target=target,
            graphs=allowed,
            walk=walk,
            path_nodes=path_nodes,
            path_edges=path_edges,
            paths=paths,
            include_types=include_types,
            include_source=include_source,
            hops=hops,
            started=started,
            paths_cap=paths_cap,
            empty_reason=empty_reason,
            nodes_cap=nodes_cap,
            edges_cap=self.max_edges,
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
        return self.subgraph(
            node,
            hops=hops,
            max_nodes=max_nodes,
            max_edges=max_edges,
            include_types=include_types,
            include_source=include_source,
            graphs=graphs,
        )

    # ---- validation and graph selection -----------------------------

    def _require_iri(self, value: str, field: str) -> None:
        if not _iri(value):
            raise PortError(
                code="InvalidArgument",
                message=f"{field} is not a safe absolute IRI",
                provider="simple",
                provider_code="E_CANVAS_BAD_IRI",
                details={"field": field, "value": value},
            )

    def _clamp_hops(self, hops: int) -> int:
        if hops < 1 or hops > self.max_hops:
            raise PortError(
                code="InvalidArgument",
                message=(
                    f"maxHops={hops} is outside the simple provider range "
                    f"1..{self.max_hops}"
                ),
                provider="simple",
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
                    provider="simple",
                    provider_code="E_CANVAS_GRAPH_FORBIDDEN",
                    details={"graphs": bad, "allowed": allowed},
                )
            return list(dict.fromkeys(requested))
        return allowed

    def _graphs(self) -> list[str]:
        """Same graph set as ``webui._graphs``: T-Box + inferred + config ABox."""
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

    def _whitelist(self, started: float) -> frozenset[str]:
        pointer = self._ontology.current()
        tbox = str((pointer or {}).get("graph") or "")
        if not tbox.startswith(PLATFORM_GRAPH_PREFIX):
            return frozenset()
        if self._whitelist_cache and self._whitelist_cache[0] == tbox:
            return self._whitelist_cache[1]
        # Oxigraph requires commas inside IN(...); without them the whole
        # whitelist query 400s. Also bound the T-Box read.
        kinds = ", ".join(f"<{kind}>" for kind in PROPERTY_KINDS)
        result = self._query(
            f"""
            SELECT DISTINCT ?p WHERE {{
              GRAPH <{tbox}> {{ ?p a ?k }}
              FILTER(?k IN ({kinds}))
            }}
            LIMIT 20000
            """,
            started,
            "whitelist",
        )
        predicates = frozenset(
            p for row in result.get("bindings", []) if (p := _binding(row, "p"))
        )
        self._whitelist_cache = (tbox, predicates)
        return predicates

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
        target: str | None = None,
    ) -> dict[str, Any]:
        """Layer BFS with predecessor tracking (cycles cannot repeat a node)."""
        nodes: dict[str, dict[str, Any]] = {start: self._node(start, None)}
        edges: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        depth: dict[str, int] = {start: 0}
        parents: dict[str, list[tuple[str, str, str | None]]] = {}
        truncated = False
        if not graphs:
            return {
                "nodes": nodes,
                "edges": edges,
                "parents": parents,
                "truncated": truncated,
                "reason": "E_CANVAS_NO_GRAPH",
            }
        whitelist = self._whitelist(started)
        if not whitelist:
            return {
                "nodes": nodes,
                "edges": edges,
                "parents": parents,
                "truncated": truncated,
                "reason": "E_CANVAS_TBOX_EMPTY",
            }
        frontier = [start]
        for layer in range(1, hops + 1):
            if not frontier:
                break
            if len(nodes) >= max_nodes or len(edges) >= max_edges:
                truncated = True
                break
            next_frontier: list[str] = []
            for batch in _batches(frontier):
                rows, directions = self._fetch_layer(
                    batch,
                    graphs,
                    whitelist,
                    remaining=max(1, max_edges - len(edges) + 1),
                    started=started,
                )
                for (s, p, o, graph) in rows:
                    direction = directions[(s, p, o)]
                    if len(edges) >= max_edges:
                        truncated = True
                        break
                    if (s, p, o) not in seen:
                        seen.add((s, p, o))
                        edges.append(
                            {
                                "s": s,
                                "p": p,
                                "o": o,
                                "dir": direction,
                                "source": {"graph": graph},
                            }
                        )
                    other = o if direction == "out" else s
                    parent = s if direction == "out" else o
                    touched = nodes.get(parent)
                    if touched is not None and touched["source"]["graph"] is None:
                        touched["source"]["graph"] = graph
                    if other not in depth:
                        if len(nodes) >= max_nodes:
                            truncated = True
                            continue
                        depth[other] = layer
                        nodes[other] = self._node(other, graph)
                        next_frontier.append(other)
                        parents.setdefault(other, []).append((parent, p, graph))
                    elif depth[other] == layer:
                        # Same-length shortest path: keep every predecessor so
                        # path() can enumerate alternatives (no cycles).
                        if (parent, p, graph) not in parents.setdefault(other, []):
                            parents[other].append((parent, p, graph))
                if len(edges) >= max_edges or len(nodes) >= max_nodes:
                    break
            frontier = next_frontier
            if target is not None and target in depth:
                break
        reason = None
        if not graphs:
            reason = "E_CANVAS_NO_GRAPH"
        elif not whitelist:
            reason = "E_CANVAS_TBOX_EMPTY"
        return {
            "nodes": nodes,
            "edges": edges,
            "parents": parents,
            "truncated": truncated,
            "reason": reason,
        }

    def _fetch_layer(
        self,
        frontier: list[str],
        graphs: list[str],
        whitelist: frozenset[str],
        *,
        remaining: int,
        started: float,
    ) -> tuple[list[tuple[str, str, str, str | None]], dict[tuple[str, str, str], str]]:
        """Two plain queries (outgoing/incoming). No UNION under a variable graph."""
        graph_values = " ".join(f"<{graph}>" for graph in graphs)
        predicate_values = " ".join(f"<{predicate}>" for predicate in sorted(whitelist))
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

    def _query(self, sparql: str, started: float, stage: str) -> dict[str, Any]:
        if time.monotonic() - started > self.timeout_ms / 1000:
            raise PortError(
                code="DeadlineExceeded",
                message=f"canvas budget of {self.timeout_ms}ms expired before {stage}",
                provider="simple",
                provider_code="E_CANVAS_TIMEOUT",
                details={"stage": stage, "timeoutMs": self.timeout_ms},
            )
        result = self._graph.query(sparql)
        if time.monotonic() - started > self.timeout_ms / 1000:
            # The graph adapter owns its HTTP timeout and does not expose a
            # per-query override, so the budget is verified right after return:
            # a slow answer is never returned as a half-finished subgraph.
            raise PortError(
                code="DeadlineExceeded",
                message=f"canvas budget of {self.timeout_ms}ms expired during {stage}",
                provider="simple",
                provider_code="E_CANVAS_TIMEOUT",
                details={"stage": stage, "timeoutMs": self.timeout_ms},
            )
        return result

    # ---- path enumeration ---------------------------------------------

    def _enumerate_paths(
        self,
        source: str,
        target: str,
        parents: dict[str, list[tuple[str, str, str | None]]],
        max_paths: int,
        max_hops: int,
    ) -> list[dict[str, Any]]:
        if target not in parents and target != source:
            return []
        paths: list[dict[str, Any]] = []
        seen_sequences: set[tuple[str, ...]] = set()
        stack: list[tuple[str, list[str], list[dict[str, Any]]]] = [(target, [target], [])]
        while stack and len(paths) < max_paths:
            current, node_chain, edge_chain = stack.pop()
            if current == source:
                sequence = tuple(reversed(node_chain))
                if sequence not in seen_sequences:
                    seen_sequences.add(sequence)
                    paths.append(
                        {
                            "nodes": list(sequence),
                            "edges": list(reversed(edge_chain)),
                            "length": len(sequence) - 1,
                        }
                    )
                continue
            if len(node_chain) > max_hops:
                continue
            for previous, predicate, graph in parents.get(current, []):
                if previous in node_chain:
                    continue  # cycle guard: a path never repeats a node
                stack.append(
                    (
                        previous,
                        node_chain + [previous],
                        edge_chain
                        + [
                            {
                                "s": previous,
                                "p": predicate,
                                "o": current,
                                "dir": "out",
                                "source": {"graph": graph},
                            }
                        ],
                    )
                )
        return paths

    # ---- result shaping ----------------------------------------------

    def _node(self, iri: str, graph: str | None) -> dict[str, Any]:
        return {
            "iri": iri,
            "label": _local_name(iri),
            "types": [],
            "source": {"graph": graph, "hasRef": False},
        }

    def _result(
        self,
        *,
        mode: str,
        start: str,
        target: str | None,
        graphs: list[str],
        walk: dict[str, Any],
        path_nodes: list[str] | None,
        path_edges: list[dict[str, Any]] | None,
        paths: list[dict[str, Any]],
        include_types: bool,
        include_source: bool,
        hops: int,
        started: float,
        paths_cap: int | None = None,
        empty_reason: str | None = None,
        nodes_cap: int | None = None,
        edges_cap: int | None = None,
    ) -> dict[str, Any]:
        if path_nodes is not None:
            node_iris = path_nodes or [start]
            edges = path_edges or []
        else:
            node_iris = list(walk["nodes"].keys())
            edges = walk["edges"]
        nodes = {iri: dict(walk["nodes"].get(iri) or self._node(iri, None)) for iri in node_iris}
        if nodes:
            self._enrich(nodes, graphs, include_types, started)
        for node in nodes.values():
            if not include_source:
                node["source"] = {"graph": None, "hasRef": False}
        if not include_source:
            for edge in edges:
                edge["source"] = {"graph": None}
        elapsed_ms = int(round((time.monotonic() - started) * 1000))
        nodes_cap = self.max_nodes if nodes_cap is None else nodes_cap
        edges_cap = self.max_edges if edges_cap is None else edges_cap
        return {
            "provider": "simple",
            "mode": mode,
            "start": start,
            "target": target,
            "graphs": graphs,
            "nodes": list(nodes.values()),
            "edges": list(edges),
            "paths": paths,
            "layout": {"mode": "none", "nodes": [], "seed": None},
            "truncated": bool(walk["truncated"]),
            "limits": {
                "hops": hops,
                "maxNodes": nodes_cap,
                "maxEdges": edges_cap,
                "maxPaths": paths_cap or self.max_paths,
            },
            "stats": {
                "nodes": len(nodes),
                "edges": len(edges),
                "paths": len(paths),
                "elapsedMs": elapsed_ms,
            },
            "emptyReason": empty_reason or walk["reason"],
            "degraded": False,
        }

    def _enrich(
        self,
        nodes: dict[str, dict[str, Any]],
        graphs: list[str],
        include_types: bool,
        started: float,
    ) -> None:
        """One batched query per readable graph for labels (+ types).

        No ``OPTIONAL`` and no variable graph: Oxigraph never finishes
        ``GRAPH ?g { OPTIONAL ... }`` (measured 35s timeout on 50 subjects),
        while ``GRAPH <g> { VALUES ?s {..} .. }`` answers in ~3ms. Every query
        carries a ``LIMIT``.
        """
        if not graphs:
            return
        for batch in _batches(list(nodes.keys())):
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
