"""D1-1 canvas tests: simple BFS/path, limits, cycles, provider codes, endpoint.

Pure unit tests: metadata/graph/ontology/reasoning are small fakes, so no
postgres/oxigraph/reasoner is required. Run inside the existing image (no
rebuild):
  docker run --rm --entrypoint python -e PYTHONPATH=/hostsrc \
    -v <worktree>/platform/src:/hostsrc:ro \
    -v <worktree>/platform/tests:/hosttests:ro \
    agent-platform:0.1-s5 /hosttests/test_d1_canvas.py
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import yaml
from fastapi.testclient import TestClient

sys.path.insert(0, "/app/src")
sys.path.insert(0, "../src")
sys.path.insert(0, "/hostsrc")  # mounted worktree wins over the image copy

import platform_core.api as api_module
from platform_core.adapters.canvas_disabled import DisabledCanvas
from platform_core.adapters.canvas_full import FullCanvas
from platform_core.adapters.canvas_simple import SimpleCanvas
from platform_core.config import load_config
from platform_core.errors import EXIT_CONFIG, PlatformError, PortError

TBOX_GRAPH = "urn:platform:graph:tbox:v1"
INFERRED_GRAPH = "urn:platform:graph:inferred:v1"
ABOX_GRAPH = "urn:platform:graph:abox:main"
PRED = "urn:platform:pred:rel"
OTHER_PRED = "urn:platform:pred:other"

DSN = os.environ.get("TEST_PG_DSN")
BASE = {"database": {"url": DSN or "postgresql://test@127.0.0.1:1/test_offline"}}


def load(overrides: dict, environ: dict | None = None):
    doc = dict(BASE)
    for key, value in overrides.items():
        if isinstance(value, dict):
            doc.setdefault(key, {}).update(value)
        else:
            doc[key] = value
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as handle:
        yaml.safe_dump(doc, handle)
        path = handle.name
    try:
        return load_config(path, environ=environ or {})
    finally:
        Path(path).unlink(missing_ok=True)


def _values(sparql: str, name: str) -> list[str]:
    match = re.search(rf"VALUES \?{name} \{{ ([^}}]*) \}}", sparql)
    if not match:
        return []
    return re.findall(r"<([^>]+)>", match.group(1))


class FakeGraph:
    """Serves the four query shapes SimpleCanvas emits, plus a generic fallback."""

    def __init__(self, triples, whitelist=(PRED,), labels=None, types=None):
        self.triples = list(triples)
        self.whitelist = set(whitelist)
        self.labels = dict(labels or {})
        self.types = dict(types or {})
        self.calls: list[str] = []

    @staticmethod
    def _iri(value):
        return {"kind": "iri", "iri": value}

    @staticmethod
    def _literal(value):
        return {"kind": "literal", "value": value}

    def _rows(self, rows, literals=()):
        bindings = []
        for row in rows:
            values = {}
            for name, value in row.items():
                values[name] = (
                    self._literal(value) if name in literals else self._iri(value)
                )
            bindings.append({"values": values})
        return {"kind": "select", "variables": list(rows[0]) if rows else [], "bindings": bindings}

    def query(self, sparql):
        self.calls.append(sparql)
        if "?p a ?k" in sparql:
            return self._rows([{"p": predicate} for predicate in sorted(self.whitelist)])
        if "?value" in sparql and "GRAPH <" in sparql:
            # Enrich shape: GRAPH <g> { VALUES ?s {..} ?s <label|type> ?value }
            is_label = "rdf-schema#label" in sparql
            rows = []
            for node in _values(sparql, "s"):
                value = self.labels.get(node) if is_label else self.types.get(node)
                if value:
                    rows.append({"s": node, "value": value})
            return self._rows(rows, literals=("value",) if is_label else ())
        limit = int((re.search(r"LIMIT (\d+)", sparql) or [None, "1000"])[1])
        rows = []
        if "VALUES ?o {" in sparql:
            points = set(_values(sparql, "o"))
            predicates = set(_values(sparql, "p"))
            graphs = set(_values(sparql, "g"))
            for s, p, o, g in self.triples:
                if o in points and p in predicates and g in graphs:
                    rows.append({"s": s, "p": p, "o": o, "g": g})
        else:
            points = set(_values(sparql, "s"))
            predicates = set(_values(sparql, "p"))
            graphs = set(_values(sparql, "g"))
            for s, p, o, g in self.triples:
                if s in points and p in predicates and g in graphs:
                    rows.append({"s": s, "p": p, "o": o, "g": g})
        rows = rows[:limit]
        return {"kind": "select", "variables": ["s", "p", "o", "g"], "bindings": [
            {"values": {key: self._iri(value) for key, value in row.items()}} for row in rows
        ]}


class FakeOntology:
    def __init__(self, graph=TBOX_GRAPH):
        self._graph = graph

    def current(self):
        if not self._graph:
            return None
        return {"graph": self._graph}


class FakeReasoning:
    def __init__(self, target=INFERRED_GRAPH):
        self._target = target

    def status(self):
        return {"pointer": {"targetGraph": self._target}}


def canvas_config(**overrides):
    values = {
        "provider": "simple",
        "simple_max_hops": 3,
        "full_max_hops": 4,
        "max_nodes": 200,
        "max_edges": 400,
        "max_paths": 20,
        "timeout_ms": 500,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def make_canvas(triples, *, whitelist=(PRED,), labels=None, types=None, **config):
    graph = FakeGraph(triples, whitelist=whitelist, labels=labels, types=types)
    cfg = SimpleNamespace(
        canvas=canvas_config(**config),
        reasoning=SimpleNamespace(abox_graphs=[ABOX_GRAPH]),
    )
    return SimpleCanvas(cfg, graph, FakeOntology(), FakeReasoning()), graph, cfg


def make_runtime(canvas, cfg, graph, ontology=None, reasoning=None):
    return SimpleNamespace(
        config=cfg,
        graph=graph,
        ontology=ontology or FakeOntology(),
        reasoning=reasoning or FakeReasoning(),
        canvas=canvas,
    )


CHAIN = [
    ("urn:platform:test:a", PRED, "urn:platform:test:b", ABOX_GRAPH),
    ("urn:platform:test:b", PRED, "urn:platform:test:c", ABOX_GRAPH),
]
LONG_CHAIN = CHAIN + [
    ("urn:platform:test:c", PRED, "urn:platform:test:d", ABOX_GRAPH),
    ("urn:platform:test:d", PRED, "urn:platform:test:e", ABOX_GRAPH),
]
CYCLE = [
    ("urn:platform:test:a", PRED, "urn:platform:test:b", ABOX_GRAPH),
    ("urn:platform:test:b", PRED, "urn:platform:test:c", ABOX_GRAPH),
    ("urn:platform:test:c", PRED, "urn:platform:test:b", ABOX_GRAPH),
    ("urn:platform:test:b", PRED, "urn:platform:test:a", ABOX_GRAPH),
]
A = "urn:platform:test:a"
B = "urn:platform:test:b"
C = "urn:platform:test:c"
E = "urn:platform:test:e"


class SimplePathTests(unittest.TestCase):
    def test_1_two_hop_path_and_contract_keys(self):
        canvas, graph, _ = make_canvas(
            CHAIN,
            labels={A: "起点 A", B: "中间 B", C: "终点 C"},
            types={A: "urn:platform:class:Entity"},
        )
        result = canvas.path(A, C, max_hops=3)
        self.assertEqual(result["provider"], "simple")
        self.assertEqual(result["mode"], "path")
        self.assertEqual(result["start"], A)
        self.assertEqual(result["target"], C)
        self.assertIsNone(result["emptyReason"])
        self.assertFalse(result["truncated"])
        self.assertFalse(result["degraded"])
        self.assertEqual(result["layout"], {"mode": "none", "nodes": [], "seed": None})
        self.assertEqual(result["limits"]["hops"], 3)
        self.assertEqual(result["limits"]["maxPaths"], 20)
        self.assertEqual(len(result["paths"]), 1)
        self.assertEqual(result["paths"][0]["nodes"], [A, B, C])
        self.assertEqual(result["paths"][0]["length"], 2)
        self.assertEqual(len(result["paths"][0]["edges"]), 2)
        self.assertEqual({node["iri"] for node in result["nodes"]}, {A, B, C})
        self.assertEqual(result["stats"]["nodes"], 3)
        self.assertEqual(result["stats"]["edges"], 2)
        self.assertEqual(len(result["edges"]), 2)
        node_a = next(node for node in result["nodes"] if node["iri"] == A)
        self.assertEqual(node_a["label"], "起点 A")
        self.assertEqual(node_a["types"], ["urn:platform:class:Entity"])
        self.assertEqual(node_a["source"]["graph"], ABOX_GRAPH)
        self.assertIs(node_a["source"]["hasRef"], False)
        self.assertIn(ABOX_GRAPH, result["graphs"])
        for query in graph.calls:
            self.assertNotIn("UNION", query.upper())
        layer_queries = [
            q
            for q in graph.calls
            if "VALUES ?g" in q and ("VALUES ?s" in q or "VALUES ?o" in q)
        ]
        self.assertTrue(layer_queries)
        for query in layer_queries:
            self.assertIn("VALUES ?g", query)
            self.assertIn("GRAPH ?g", query)

    def test_2_max_hops_is_effective_and_has_a_reason(self):
        canvas, _, _ = make_canvas(LONG_CHAIN)
        result = canvas.path(A, E, max_hops=3)
        self.assertEqual(result["paths"], [])
        self.assertEqual(result["edges"], [])
        self.assertEqual(result["emptyReason"], "E_PATH_NOT_FOUND")
        self.assertEqual(result["stats"]["paths"], 0)

    def test_3_request_beyond_the_provider_hard_cap_is_rejected(self):
        canvas, _, _ = make_canvas(LONG_CHAIN)
        with self.assertRaises(PortError) as ctx:
            canvas.path(A, E, max_hops=4)
        self.assertEqual(ctx.exception.provider_code, "E_CANVAS_HOPS_EXCEEDED")

    def test_4_cycles_are_deduped(self):
        canvas, _, _ = make_canvas(CYCLE)
        result = canvas.path(A, C, max_hops=3)
        self.assertEqual(len(result["paths"]), 1)
        self.assertEqual(result["paths"][0]["nodes"], [A, B, C])
        for path in result["paths"]:
            # A 2-cycle b<->c must not produce a repeating path.
            self.assertEqual(len(path["nodes"]), len(set(path["nodes"])))
        edge_keys = [(edge["s"], edge["p"], edge["o"]) for edge in result["edges"]]
        self.assertEqual(len(edge_keys), len(set(edge_keys)))
        self.assertEqual(len(result["edges"]), 2)
        wider = canvas.subgraph(A, hops=2, max_nodes=10, max_edges=10)
        wide_keys = [(edge["s"], edge["p"], edge["o"]) for edge in wider["edges"]]
        self.assertEqual(len(wide_keys), len(set(wide_keys)))
        self.assertEqual(len(wide_keys), 4)
        self.assertEqual(len(wider["nodes"]), 3)

    def test_5_subgraph_returns_bounded_neighbourhood(self):
        canvas, _, _ = make_canvas(LONG_CHAIN)
        result = canvas.subgraph(A, hops=2, max_nodes=3, max_edges=5)
        self.assertEqual(result["mode"], "subgraph")
        self.assertEqual(result["paths"], [])
        self.assertEqual(result["target"], None)
        self.assertEqual({node["iri"] for node in result["nodes"]}, {A, B, C})
        self.assertEqual(len(result["edges"]), 2)
        self.assertIs(result["truncated"], False)
        limited = canvas.subgraph(A, hops=3, max_nodes=2)
        self.assertIs(limited["truncated"], True)
        self.assertEqual(len(limited["nodes"]), 2)

    def test_6_include_flags_keep_the_keyset(self):
        canvas, _, _ = make_canvas(CHAIN, types={A: "urn:platform:class:Entity"})
        result = canvas.path(
            A, C, max_hops=3, include_types=False, include_source=False
        )
        node_a = next(node for node in result["nodes"] if node["iri"] == A)
        self.assertEqual(node_a["types"], [])
        self.assertEqual(node_a["source"], {"graph": None, "hasRef": False})
        self.assertEqual(result["edges"][0]["source"], {"graph": None})

    def test_7_empty_tbox_and_unknown_graph_are_structured(self):
        canvas, _, _ = make_canvas(CHAIN, whitelist=())
        empty = canvas.path(A, C, max_hops=3)
        self.assertEqual(empty["paths"], [])
        self.assertEqual(empty["emptyReason"], "E_CANVAS_TBOX_EMPTY")
        with self.assertRaises(PortError) as ctx:
            canvas.path(A, C, max_hops=3, graphs=["urn:evil:graph"])
        self.assertEqual(ctx.exception.provider_code, "E_CANVAS_GRAPH_FORBIDDEN")
        self.assertEqual(ctx.exception.code, "PermissionDenied")


class FullAssemblyTests(unittest.TestCase):
    def test_8_full_provider_is_assembled(self):
        # D1-2: full is no longer a skeleton. Detailed behaviour lives in
        # test_d1_canvas_full.py; here we only assert the switch is wired.
        cfg = SimpleNamespace(
            canvas=canvas_config(provider="full"),
            reasoning=SimpleNamespace(abox_graphs=[ABOX_GRAPH]),
        )
        full = FullCanvas(cfg, FakeGraph([]), FakeOntology(), FakeReasoning())
        manifest = full.manifest()
        self.assertEqual(manifest.provider, "full")
        self.assertIn("canvas.multipath", manifest.capabilities)
        self.assertEqual(manifest.limits["hops"], 4)
        self.assertNotIn("not_implemented", manifest.notes.get("status", ""))

    def test_9_disabled_canvas_is_a_structured_503(self):
        canvas = DisabledCanvas("canvas.provider=off")
        with self.assertRaises(PortError) as ctx:
            canvas.path(A, C)
        self.assertEqual(ctx.exception.code, "Unavailable")
        self.assertEqual(ctx.exception.provider_code, "E_CANVAS_DISABLED")


class CanvasConfigTests(unittest.TestCase):
    def _assert_error(self, overrides, code, key):
        with self.assertRaises(PlatformError) as ctx:
            load(overrides)
        self.assertEqual(ctx.exception.code, code, ctx.exception.detail)
        self.assertEqual(ctx.exception.key, key)
        self.assertEqual(ctx.exception.exit_code, EXIT_CONFIG)

    def test_10_provider_codes_follow_q8(self):
        self._assert_error(
            {"canvas": {"provider": "nope"}}, "E_PROVIDER_INVALID", "canvas.provider"
        )
        full = load({"canvas": {"provider": "full"}})
        self.assertEqual(full.config.canvas.provider, "full")

    def test_11_off_and_simple_are_accepted(self):
        default = load({})
        self.assertEqual(default.config.canvas.provider, "off")
        simple = load({"canvas": {"provider": "simple", "simple_max_hops": 4}})
        self.assertEqual(simple.config.canvas.provider, "simple")
        self.assertEqual(simple.config.canvas.simple_max_hops, 4)
        self.assertTrue(any("simple_max_hops" in item for item in simple.warnings))


class CanvasApiTests(unittest.TestCase):
    def test_12_endpoint_returns_path_payload(self):
        canvas, graph, cfg = make_canvas(CHAIN, labels={A: "A"})
        runtime = make_runtime(canvas, cfg, graph)
        with TestClient(api_module.create_app(runtime, [])) as client:
            response = client.get("/browse/path", params={"from": A, "to": C})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["provider"], "simple")
        self.assertEqual(payload["paths"][0]["nodes"], [A, B, C])

    def test_13_endpoint_rejects_bad_iri_hops_and_graph(self):
        canvas, graph, cfg = make_canvas(CHAIN)
        runtime = make_runtime(canvas, cfg, graph)
        with TestClient(api_module.create_app(runtime, [])) as client:
            bad_iri = client.get("/browse/path", params={"from": "relative/path"})
            too_many_hops = client.get(
                "/browse/path", params={"from": A, "to": C, "maxHops": 99}
            )
            forbidden = client.get(
                "/browse/path", params={"from": A, "graph": "urn:evil:graph"}
            )
        self.assertEqual(bad_iri.status_code, 400)
        self.assertEqual(bad_iri.json()["error"]["providerCode"], "E_CANVAS_BAD_IRI")
        self.assertEqual(too_many_hops.status_code, 400)
        self.assertEqual(
            too_many_hops.json()["error"]["providerCode"], "E_CANVAS_HOPS_EXCEEDED"
        )
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(
            forbidden.json()["error"]["providerCode"], "E_CANVAS_GRAPH_FORBIDDEN"
        )

    def test_14_off_returns_503_without_touching_other_endpoints(self):
        graph = FakeGraph([])
        cfg = SimpleNamespace(
            canvas=canvas_config(provider="off"),
            reasoning=SimpleNamespace(abox_graphs=[ABOX_GRAPH]),
        )
        runtime = make_runtime(DisabledCanvas("canvas.provider=off"), cfg, graph)
        with TestClient(api_module.create_app(runtime, [])) as client:
            disabled = client.get("/browse/path", params={"from": A})
            triples = client.get("/browse/triples", params={"limit": 5})
        self.assertEqual(disabled.status_code, 503)
        self.assertEqual(disabled.json()["error"]["providerCode"], "E_CANVAS_DISABLED")
        self.assertEqual(triples.status_code, 200)

    def test_15_full_provider_answers_over_http(self):
        graph = FakeGraph(CHAIN)
        cfg = SimpleNamespace(
            canvas=canvas_config(provider="full"),
            reasoning=SimpleNamespace(abox_graphs=[ABOX_GRAPH]),
        )
        full = FullCanvas(cfg, graph, FakeOntology(), FakeReasoning())
        runtime = make_runtime(full, cfg, graph)
        with TestClient(api_module.create_app(runtime, [])) as client:
            response = client.get("/browse/path", params={"from": A, "to": C})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["provider"], "full")
        self.assertEqual(response.json()["mode"], "path")


if __name__ == "__main__":
    unittest.main(verbosity=2)
