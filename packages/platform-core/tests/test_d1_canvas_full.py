"""D1-2 full canvas tests.

Pure unit tests (no postgres/oxigraph/reasoner). Run inside the existing image:
  docker run --rm --entrypoint python -e PYTHONPATH=/hostsrc \
    -v <worktree>/platform/src:/hostsrc:ro \
    -v <worktree>/platform/tests:/hosttests:ro \
    agent-platform:0.1-s5 /hosttests/test_d1_canvas_full.py

Covered: assembly + provider codes, >3 hops, multi-path/dedup/cycles,
predicate-kind filtering, graph whitelist, bidirectional search, pagination
cursor, hasRef true/false (candidate + PROV), no-UNION/LIMIT query shape,
truncation reasons, timeout, and the G10 routes.
"""

from __future__ import annotations

import inspect
import sys
import time
import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient

sys.path.insert(0, "/app/src")
sys.path.insert(0, "../src")
sys.path.insert(0, "/hostsrc")
sys.path.insert(0, "/hosttests")

import platform_core.api as api_module
from platform_core.adapters.canvas_full import FullCanvas
from platform_core.adapters.canvas_simple import SimpleCanvas
from platform_core.errors import PortError

from test_d1_canvas import (
    ABOX_GRAPH,
    BASE,  # noqa: F401 - keeps the fixture module importable
    FakeGraph,
    FakeOntology,
    FakeReasoning,
    _values,
    canvas_config,
    make_runtime,
)

OWL_OBJECT = "http://www.w3.org/2002/07/owl#ObjectProperty"
OWL_ANNOTATION = "http://www.w3.org/2002/07/owl#AnnotationProperty"
RDF_PROPERTY = "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property"
PRED = "urn:platform:pred:rel"
OTHER = "urn:platform:pred:other"
ANNOT = "urn:platform:pred:annot"
A = "urn:platform:test:a"
B = "urn:platform:test:b"
C = "urn:platform:test:c"
D = "urn:platform:test:d"
E = "urn:platform:test:e"
F = "urn:platform:test:f"
G = "urn:platform:test:g"
DOC = "a" * 32
DOC2 = "b" * 32


class FullFakeGraph(FakeGraph):
    """FakeGraph plus T-Box kinds and the PROV src:// lookup shape."""

    def __init__(self, triples, kinds=None, labels=None, types=None, prov=None):
        kinds = dict(kinds or {PRED: OWL_OBJECT})
        super().__init__(triples, whitelist=kinds.keys(), labels=labels, types=types)
        self.kinds = kinds
        self.prov = list(prov or [])
        self.sleep_s = 0.0

    def query(self, sparql):
        self.calls.append(sparql)
        if self.sleep_s:
            time.sleep(self.sleep_s)
        if "?p a ?k" in sparql:
            return self._rows(
                [
                    {"p": predicate, "k": kind}
                    for predicate, kind in sorted(self.kinds.items())
                ]
            )
        if "urn:platform:prov" in sparql and "prov#used" in sparql:
            points = set(_values(sparql, "subject"))
            rows = [
                {"subject": subject, "ref": ref}
                for subject, ref in self.prov
                if subject in points
            ]
            return self._rows(rows, literals=("ref",))
        return super().query(sparql)


class FullFakeMeta:
    def __init__(self, candidates):
        self.candidates = list(candidates)
        self.calls: list[tuple[str, tuple]] = []

    def query(self, sql, params):
        self.calls.append((sql, params))
        subjects = set(params[0])
        graphs = set(params[1])
        limit = int(params[2])
        rows = []
        for row in self.candidates:
            if row["subject_iri"] in subjects and row["graph_iri"] in graphs:
                rows.append(row)
        return rows[:limit]


def make_full(
    triples,
    *,
    kinds=None,
    labels=None,
    types=None,
    metadata=None,
    prov=None,
    **config,
):
    graph = FullFakeGraph(triples, kinds=kinds, labels=labels, types=types, prov=prov)
    values = {"provider": "full", "full_max_hops": 4}
    values.update(config)
    cfg = SimpleNamespace(
        canvas=canvas_config(**values),
        reasoning=SimpleNamespace(abox_graphs=[ABOX_GRAPH]),
    )
    canvas = FullCanvas(cfg, graph, FakeOntology(), FakeReasoning(), metadata=metadata)
    return canvas, graph, cfg


CHAIN2 = [
    (A, PRED, B, ABOX_GRAPH),
    (B, PRED, C, ABOX_GRAPH),
]
SIX = CHAIN2 + [
    (C, PRED, D, ABOX_GRAPH),
    (D, PRED, E, ABOX_GRAPH),
    (E, PRED, F, ABOX_GRAPH),
    (F, PRED, G, ABOX_GRAPH),
]
MULTI = [
    (A, PRED, B, ABOX_GRAPH),
    (B, PRED, C, ABOX_GRAPH),
    (A, PRED, D, ABOX_GRAPH),
    (D, PRED, C, ABOX_GRAPH),
    (B, PRED, D, ABOX_GRAPH),
]
STAR = [(A, PRED, f"urn:platform:test:leaf{i}", ABOX_GRAPH) for i in range(10)]
CYCLE = [
    (A, PRED, B, ABOX_GRAPH),
    (B, PRED, C, ABOX_GRAPH),
    (C, PRED, B, ABOX_GRAPH),
    (B, PRED, A, ABOX_GRAPH),
]


def edge_keys(result):
    return [(edge["s"], edge["p"], edge["o"]) for edge in result["edges"]]


class FullContractTests(unittest.TestCase):
    def test_1_signatures_match_simple_and_manifest_is_full(self):
        canvas, _, _ = make_full(CHAIN2)
        for name in ("subgraph", "path", "expand"):
            self.assertEqual(
                str(inspect.signature(getattr(SimpleCanvas, name))),
                str(inspect.signature(getattr(FullCanvas, name))),
                name,
            )
        manifest = canvas.manifest()
        self.assertEqual(manifest.provider, "full")
        for capability in (
            "canvas.path",
            "canvas.multipath",
            "canvas.bidirectional",
            "canvas.predicate-filter",
            "canvas.aggregate",
            "canvas.pagination",
            "canvas.hasRef",
        ):
            self.assertIn(capability, manifest.capabilities)
        self.assertEqual(manifest.limits["hops"], 4)
        self.assertEqual(manifest.limits["page_size"], 200)

    def test_2_full_reaches_more_than_three_hops(self):
        canvas, _, _ = make_full(SIX, full_max_hops=6)
        result = canvas.path(A, G, max_hops=6)
        self.assertIsNone(result["emptyReason"])
        self.assertEqual(len(result["paths"]), 1)
        self.assertEqual(result["paths"][0]["length"], 6)
        self.assertEqual(result["paths"][0]["nodes"], [A, B, C, D, E, F, G])
        self.assertEqual(result["provider"], "full")
        self.assertEqual(result["layout"]["mode"], "force")
        with self.assertRaises(PortError) as ctx:
            canvas.path(A, G, max_hops=7)
        self.assertEqual(ctx.exception.provider_code, "E_CANVAS_HOPS_EXCEEDED")

    def test_3_bidirectional_enumeration_returns_non_shortest_paths(self):
        canvas, _, _ = make_full(MULTI)
        result = canvas.path(A, C, max_hops=3)
        sequences = [tuple(path["nodes"]) for path in result["paths"]]
        self.assertIn((A, B, C), sequences)
        self.assertIn((A, D, C), sequences)
        self.assertIn((A, B, D, C), sequences)
        self.assertEqual(len(sequences), len(set(sequences)))
        self.assertEqual(
            [path["length"] for path in result["paths"]],
            sorted(path["length"] for path in result["paths"]),
        )
        for path in result["paths"]:
            self.assertEqual(len(path["nodes"]), len(set(path["nodes"])))
        returned = {node["iri"] for node in result["nodes"]}
        self.assertEqual(returned, {A, B, C, D})

    def test_4_cycle_is_never_emitted_as_a_path(self):
        canvas, _, _ = make_full(CYCLE, full_max_hops=6)
        result = canvas.path(A, C, max_hops=6, max_paths=20)
        self.assertEqual(len(result["paths"]), 1)
        self.assertEqual(result["paths"][0]["nodes"], [A, B, C])
        keys = edge_keys(result)
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len(result["nodes"]), 3)

    def test_5_predicate_kind_filter_and_validation(self):
        canvas, graph, _ = make_full(
            CHAIN2 + [(A, ANNOT, C, ABOX_GRAPH)],
            kinds={PRED: OWL_OBJECT, ANNOT: OWL_ANNOTATION},
        )
        object_only = canvas.query(A, hops=2, predicate_types=["object"])
        self.assertEqual(
            {edge["p"] for edge in object_only["edges"]}, {PRED}
        )
        self.assertEqual(
            {node["iri"] for node in object_only["nodes"]}, {A, B, C}
        )
        annotation_only = canvas.query(A, hops=2, predicate_types=["annotation"])
        self.assertEqual(
            {edge["p"] for edge in annotation_only["edges"]}, {ANNOT}
        )
        self.assertEqual(
            {node["iri"] for node in annotation_only["nodes"]}, {A, C}
        )
        with self.assertRaises(PortError) as ctx:
            canvas.query(A, hops=1, predicate_types=["telephone"])
        self.assertEqual(
            ctx.exception.provider_code, "E_CANVAS_BAD_PREDICATE_TYPE"
        )
        # Every layer query still carries the explicit graph whitelist.
        for call in graph.calls:
            if "GRAPH ?g" in call and ("VALUES ?s" in call or "VALUES ?o" in call):
                self.assertIn("VALUES ?g", call)

    def test_6_unknown_graph_is_forbidden(self):
        canvas, _, _ = make_full(CHAIN2)
        with self.assertRaises(PortError) as ctx:
            canvas.subgraph(A, graphs=["urn:evil:graph"])
        self.assertEqual(ctx.exception.provider_code, "E_CANVAS_GRAPH_FORBIDDEN")
        self.assertEqual(ctx.exception.code, "PermissionDenied")


class FullPaginationAndAggregateTests(unittest.TestCase):
    def test_7_cursor_pagination_union_is_complete(self):
        canvas, _, _ = make_full(STAR)
        nodes = {}
        edges = {}
        cursor = None
        pages = 0
        while True:
            page = canvas.query(A, hops=1, page_size=5, cursor=cursor)
            nodes.update({node["iri"]: node for node in page["nodes"]})
            edges.update({(edge["s"], edge["p"], edge["o"]): edge for edge in page["edges"]})
            pages += 1
            self.assertEqual(page["page"]["totalNodes"], 11)
            self.assertEqual(page["page"]["totalEdges"], 10)
            cursor = page["page"]["nextCursor"]
            if not cursor:
                break
            self.assertLess(pages, 10)
        self.assertEqual(len(nodes), 11)
        self.assertEqual(len(edges), 10)
        self.assertEqual(pages, 3)
        # A fresh page-1 query still sees the pristine cached graph.
        again = canvas.query(A, hops=1, page_size=5)
        self.assertEqual(len(again["nodes"]), 5)
        self.assertEqual(len(again["edges"]), 5)
        self.assertTrue(again["page"]["nextCursor"])

    def test_8_bad_cursor_and_overlarge_page_are_structured(self):
        canvas, _, _ = make_full(STAR)
        with self.assertRaises(PortError) as ctx:
            canvas.query(A, hops=1, cursor="garbage")
        self.assertEqual(ctx.exception.provider_code, "E_CANVAS_BAD_CURSOR")
        with self.assertRaises(PortError) as ctx:
            canvas.query(A, hops=1, page_size=201)
        self.assertEqual(ctx.exception.provider_code, "E_CANVAS_PAGE_EXCEEDED")

    def test_9_server_aggregates_degree_weight_and_buckets(self):
        canvas, _, _ = make_full(STAR, types={A: "urn:platform:class:Entity"})
        page = canvas.query(A, hops=1, page_size=200)
        degree = {item["iri"]: item for item in page["aggregates"]["nodeDegree"]}
        self.assertEqual(degree[A]["out"], 10)
        self.assertEqual(degree[A]["total"], 10)
        self.assertEqual(
            {item["weight"] for item in page["aggregates"]["edgeWeights"]}, {1.0}
        )
        buckets = {item["iri"]: item["count"] for item in page["aggregates"]["classBuckets"]}
        self.assertEqual(buckets["urn:platform:class:Entity"], 1)
        predicates = {
            item["iri"]: item["count"] for item in page["aggregates"]["predicateBuckets"]
        }
        self.assertEqual(predicates[PRED], 10)
        # Layout is page-scoped so a 1000-node graph never sends 1000 entries.
        self.assertLessEqual(len(page["layout"]["nodes"]), len(page["nodes"]))


class FullRefAndShapeTests(unittest.TestCase):
    def test_10_hasref_true_and_false_are_real(self):
        candidates = [
            {
                "subject_iri": A,
                "predicate_iri": PRED,
                "object_value": B,
                "document_id": DOC,
                "chunk_id": DOC + ":0003",
                "seq": 3,
                "graph_iri": ABOX_GRAPH,
            },
            {
                "subject_iri": B,
                "predicate_iri": PRED,
                "object_value": C,
                "document_id": DOC2,
                "chunk_id": DOC2 + ":0001",
                "seq": 1,
                "graph_iri": ABOX_GRAPH,
            },
        ]
        canvas, _, _ = make_full(
            CHAIN2 + [(A, PRED, D, ABOX_GRAPH)],
            metadata=FullFakeMeta(candidates),
        )
        result = canvas.path(A, C, max_hops=3)
        nodes = {node["iri"]: node for node in result["nodes"]}
        self.assertTrue(nodes[A]["source"]["hasRef"])
        self.assertEqual(nodes[A]["source"]["ref"], f"src://doc/{DOC}#c3")
        self.assertEqual(nodes[A]["source"]["refType"], "document_chunk")
        self.assertTrue(nodes[A]["source"]["resolveUrl"].startswith("/source/resolve?ref="))
        self.assertTrue(nodes[B]["source"]["hasRef"])
        self.assertFalse(nodes[C]["source"]["hasRef"])
        edges = {(edge["s"], edge["p"], edge["o"]): edge for edge in result["edges"]}
        self.assertTrue(edges[(A, PRED, B)]["source"]["hasRef"])
        self.assertTrue(edges[(B, PRED, C)]["source"]["hasRef"])
        coverage = result["stats"]["refCoverage"]
        self.assertEqual(coverage["nodes"], 3)
        self.assertEqual(coverage["nodesWithRef"], 2)
        self.assertEqual(coverage["edgesWithRef"], 2)

        wide = canvas.subgraph(A, hops=1)
        wide_edges = {(edge["s"], edge["p"], edge["o"]): edge for edge in wide["edges"]}
        self.assertTrue(wide_edges[(A, PRED, B)]["source"]["hasRef"])
        self.assertFalse(wide_edges[(A, PRED, D)]["source"]["hasRef"])
        wide_coverage = wide["stats"]["refCoverage"]
        self.assertEqual(wide_coverage["nodes"], 3)
        self.assertEqual(wide_coverage["nodesWithRef"], 2)
        self.assertEqual(wide_coverage["edges"], 2)
        self.assertEqual(wide_coverage["edgesWithRef"], 1)

    def test_11_prov_refs_fill_nodes_but_never_edges(self):
        canvas, _, _ = make_full(
            CHAIN2, prov=[(A, f"src://doc/{DOC2}#c2")]
        )
        result = canvas.subgraph(A, hops=1)
        nodes = {node["iri"]: node for node in result["nodes"]}
        self.assertTrue(nodes[A]["source"]["hasRef"])
        self.assertFalse(nodes[B]["source"]["hasRef"])
        edges = {(edge["s"], edge["p"], edge["o"]): edge for edge in result["edges"]}
        self.assertFalse(edges[(A, PRED, B)]["source"]["hasRef"])
        coverage = result["stats"]["refCoverage"]
        self.assertEqual(coverage["nodesWithRef"], 1)
        self.assertEqual(coverage["edgesWithRef"], 0)

    def test_12_include_source_false_skips_refs_and_keeps_keys(self):
        canvas, _, _ = make_full(
            CHAIN2,
            metadata=FullFakeMeta(
                [
                    {
                        "subject_iri": A,
                        "predicate_iri": PRED,
                        "object_value": B,
                        "document_id": DOC,
                        "chunk_id": DOC + ":0000",
                        "seq": 0,
                        "graph_iri": ABOX_GRAPH,
                    }
                ]
            ),
        )
        result = canvas.path(A, C, max_hops=3, include_source=False)
        for node in result["nodes"]:
            self.assertEqual(node["source"], {"graph": None, "hasRef": False})
        for edge in result["edges"]:
            self.assertEqual(edge["source"], {"graph": None})
        self.assertEqual(result["stats"]["refCoverage"]["nodesWithRef"], 0)
        self.assertIn("skipped", result["stats"]["refCoverage"]["source"])

    def test_13_no_union_limit_and_values_graph_everywhere(self):
        canvas, graph, _ = make_full(CHAIN2)
        canvas.path(A, C, max_hops=3)
        self.assertTrue(graph.calls)
        for call in graph.calls:
            self.assertNotIn("UNION", call.upper())
            self.assertRegex(call, r"LIMIT \d+")
        for call in graph.calls:
            if "GRAPH ?g" in call:
                self.assertIn("VALUES ?g", call)
            self.assertNotIn("OPTIONAL", call.upper())
        layer_calls = [
            call
            for call in graph.calls
            if "VALUES ?g" in call and ("VALUES ?s" in call or "VALUES ?o" in call)
        ]
        self.assertTrue(layer_calls)
        for call in layer_calls:
            self.assertIn("GRAPH ?g", call)
        enrich_calls = [call for call in graph.calls if "?value" in call]
        self.assertTrue(enrich_calls)
        for call in enrich_calls:
            self.assertRegex(call, r"GRAPH <[^>]+>")

    def test_14_truncation_reasons_are_explicit(self):
        canvas, _, _ = make_full(STAR, max_nodes=200, max_edges=400)
        capped = canvas.query(A, hops=1, max_nodes=3, page_size=200)
        self.assertTrue(capped["truncation"]["truncated"])
        self.assertIn(
            "E_CANVAS_NODES_TRUNCATED", capped["truncation"]["reasons"]
        )
        self.assertEqual(len(capped["nodes"]), 3)
        edge_capped = canvas.subgraph(A, hops=1, max_edges=3)
        self.assertTrue(edge_capped["truncated"])
        self.assertIn(
            "E_CANVAS_EDGES_TRUNCATED",
            edge_capped["stats"]["truncation"]["reasons"],
        )
        self.assertEqual(len(edge_capped["edges"]), 3)

        multi, _, _ = make_full(MULTI)
        limited = multi.query(A, target=C, hops=3, max_paths=1, page_size=200)
        self.assertEqual(len(limited["paths"]), 1)
        self.assertTrue(limited["truncation"]["truncated"])
        self.assertIn(
            "E_CANVAS_PATHS_TRUNCATED", limited["truncation"]["reasons"]
        )

    def test_15_timeout_is_a_deadline_error(self):
        canvas, graph, cfg = make_full(CHAIN2, timeout_ms=100)
        graph.sleep_s = 0.3
        with self.assertRaises(PortError) as ctx:
            canvas.subgraph(A, hops=2)
        self.assertEqual(ctx.exception.code, "DeadlineExceeded")
        self.assertEqual(ctx.exception.provider_code, "E_CANVAS_TIMEOUT")

    def test_16_expand_marks_the_delta(self):
        canvas, _, _ = make_full(CHAIN2)
        result = canvas.expand(A, hops=1)
        self.assertIs(result["merged"], True)
        self.assertEqual(set(result["addedNodes"]), {A, B})
        self.assertEqual(len(result["addedEdges"]), 1)


class FullApiTests(unittest.TestCase):
    def test_17_manifest_and_full_route(self):
        canvas, graph, cfg = make_full(STAR)
        runtime = make_runtime(canvas, cfg, graph)
        with TestClient(api_module.create_app(runtime, [])) as client:
            manifest = client.get("/browse/canvas/manifest")
            page = client.get(
                "/browse/canvas/full",
                params={"from": A, "maxHops": 1, "pageSize": 5},
            )
            bad_cursor = client.get(
                "/browse/canvas/full", params={"from": A, "cursor": "garbage"}
            )
        self.assertEqual(manifest.status_code, 200)
        self.assertEqual(manifest.json()["provider"], "full")
        self.assertEqual(page.status_code, 200)
        payload = page.json()
        self.assertEqual(payload["provider"], "full")
        self.assertIn("page", payload)
        self.assertIn("aggregates", payload)
        self.assertEqual(payload["page"]["totalNodes"], 11)
        self.assertEqual(bad_cursor.status_code, 400)
        self.assertEqual(
            bad_cursor.json()["error"]["providerCode"], "E_CANVAS_BAD_CURSOR"
        )

    def test_18_full_route_rejects_non_full_provider(self):
        graph = FakeGraph(CHAIN2)
        cfg = SimpleNamespace(
            canvas=canvas_config(provider="simple"),
            reasoning=SimpleNamespace(abox_graphs=[ABOX_GRAPH]),
        )
        simple = SimpleCanvas(cfg, graph, FakeOntology(), FakeReasoning())
        runtime = make_runtime(simple, cfg, graph)
        with TestClient(api_module.create_app(runtime, [])) as client:
            response = client.get("/browse/canvas/full", params={"from": A})
            manifest = client.get("/browse/canvas/manifest")
        self.assertEqual(manifest.json()["provider"], "simple")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["providerCode"], "E_CANVAS_PROVIDER_MISMATCH"
        )

    def test_19_page_size_is_enforced_by_the_extension(self):
        canvas, graph, cfg = make_full(STAR)
        runtime = make_runtime(canvas, cfg, graph)
        with TestClient(api_module.create_app(runtime, [])) as client:
            response = client.get(
                "/browse/canvas/full", params={"from": A, "pageSize": 201}
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["providerCode"], "E_CANVAS_PAGE_EXCEEDED"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
