"""Entity view hides meta-level inferred types without touching the graphs."""

import unittest
from types import SimpleNamespace

from platform_core.entity_view import entity_detail

E = "urn:platform:test:e1"
TBOX = "urn:platform:graph:tbox:ont-1"
ABOX = "urn:platform:graph:abox:main"
INFERRED = "urn:platform:inferred:ont-1"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
CORE = "https://w3id.org/fsldm/core#"
OWL = "http://www.w3.org/2002/07/owl#"

ASSERTED = [
    (ABOX, E, RDF_TYPE, CORE + "Product"),
    (ABOX, E, RDFS_LABEL, "literal:Widget"),
]
INFERRED_EDGES = [
    (INFERRED, E, RDF_TYPE, CORE + "TimeBound"),
    (INFERRED, E, RDF_TYPE, CORE + "BusinessEntity"),
    (INFERRED, E, RDF_TYPE, OWL + "NamedIndividual"),
    (INFERRED, E, RDF_TYPE, OWL + "Thing"),
]


def _row(graph, subject, predicate, obj):
    value = {"kind": "literal", "value": obj.split(":", 1)[1]} if obj.startswith("literal:") else {
        "kind": "iri",
        "iri": obj,
    }
    return {
        "values": {
            "g": {"kind": "iri", "iri": graph},
            "s": {"kind": "iri", "iri": subject},
            "p": {"kind": "iri", "iri": predicate},
            "o": value,
        }
    }


class _Graph:
    def ask(self, query):
        return False

    def query(self, query):
        if f"BIND(<{E}> AS ?s)" in query:
            rows = INFERRED_EDGES if INFERRED in query else ASSERTED
            return {"bindings": [_row(*row) for row in rows]}
        return {"bindings": []}


class _Ontology:
    def current(self):
        return {"versionId": "ont-1", "semver": "1.0.0", "graph": TBOX}


class _Reasoning:
    def status(self):
        return {
            "aboxGraphs": [ABOX],
            "pointer": {"targetGraph": INFERRED},
            "profile": "EL",
        }


def _runtime(ignore_types=None):
    if ignore_types is None:
        ignore_types = [OWL + "Thing", OWL + "NamedIndividual"]
    entity_view = SimpleNamespace(ignore_types=ignore_types)
    return SimpleNamespace(
        config=SimpleNamespace(entity_view=entity_view),
        ontology=_Ontology(),
        reasoning=_Reasoning(),
        graph=_Graph(),
        metadata=SimpleNamespace(query=lambda *a, **k: []),
    )


class EntityViewFilterTest(unittest.TestCase):
    def test_default_filter_drops_meta_types_keeps_business_parents(self):
        payload = entity_detail(_runtime(), E)
        classes = {entry["iri"] for entry in payload["classes"]}
        self.assertIn(CORE + "TimeBound", classes)
        self.assertIn(CORE + "BusinessEntity", classes)
        self.assertNotIn(OWL + "Thing", classes)
        self.assertNotIn(OWL + "NamedIndividual", classes)

        objects = {edge["o"] for edge in payload["neighbors"]["edges"]}
        self.assertNotIn(OWL + "Thing", objects)
        self.assertNotIn(OWL + "NamedIndividual", objects)
        self.assertIn(CORE + "TimeBound", objects)
        node_iris = {node["iri"] for node in payload["neighbors"]["nodes"]}
        self.assertNotIn(OWL + "Thing", node_iris)
        self.assertNotIn(OWL + "NamedIndividual", node_iris)

    def test_ignore_list_is_configurable(self):
        payload = entity_detail(_runtime([OWL + "Thing", OWL + "NamedIndividual", CORE + "TimeBound"]), E)
        classes = {entry["iri"] for entry in payload["classes"]}
        self.assertIn(CORE + "BusinessEntity", classes)
        self.assertNotIn(CORE + "TimeBound", classes)


if __name__ == "__main__":
    unittest.main()
