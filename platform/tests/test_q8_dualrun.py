"""Q8-c: dual-run evidence — oxigraph-http vs jena-fuseki, ELK vs HermiT.

Requires the graph-fuseki profile to be up:
  docker compose --profile graph-fuseki up -d fuseki
Run inside the platform container:
  docker compose exec -T -e PYTHONPATH=/app/src platform \
    python /tmp/hosttests/test_q8_dualrun.py
"""

import os
import unittest
import uuid

from platform_core.adapters.graph_fuseki import FusekiHttpStore
from platform_core.adapters.graph_oxigraph import OxigraphHttpStore
from platform_core.adapters.reasoner_hermit import HermitReasoner
from platform_core.adapters.reasoner_robot import ReasonerClient
from platform_core.config import ReasoningConfig
from platform_core.reasoning import ReasoningService

OXIGRAPH_URL = os.environ.get("TEST_OXIGRAPH_URL", "http://oxigraph:7878")
FUSEKI_URL = os.environ.get("TEST_FUSEKI_URL", "http://fuseki:3030")
REASONER_URL = os.environ.get("TEST_REASONER_URL", "http://reasoner:7879")

TURTLE = b"""@prefix ex: <urn:platform:q8:dual#> .
ex:s1 ex:p "one" .
ex:s2 ex:p "two" .
"""

CONSISTENT = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <urn:platform:q8:consistent#> .
ex:A a owl:Class .
ex:B a owl:Class .
ex:C a owl:Class .
ex:A rdfs:subClassOf ex:B .
ex:B rdfs:subClassOf ex:C .
ex:y a owl:NamedIndividual, ex:A .
"""

INCONSISTENT = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <urn:platform:q8:inconsistent#> .
ex:A a owl:Class .
ex:B a owl:Class .
ex:A owl:disjointWith ex:B .
ex:x a owl:NamedIndividual, ex:A, ex:B .
"""


class DualRunTests(unittest.TestCase):
    def test_1_graph_common_subset_is_equivalent(self):
        stores = {
            "oxigraph-http": OxigraphHttpStore(OXIGRAPH_URL),
            "jena-fuseki": FusekiHttpStore(FUSEKI_URL),
        }
        graph_iri = f"urn:platform:q8:dual:{uuid.uuid4().hex[:10]}"
        results: dict[str, dict] = {}
        try:
            for name, store in stores.items():
                item: dict = {}
                item["replace.triples"] = store.replace_graph(graph_iri, TURTLE, "turtle")["triples"]
                item["count.afterReplace"] = store.count_graph(graph_iri)
                item["ask"] = store.ask(
                    f"ASK {{ GRAPH <{graph_iri}> {{ <urn:platform:q8:dual#s1> ?p ?o }} }}"
                )
                rows = store.query(
                    f"SELECT ?s ?o WHERE {{ GRAPH <{graph_iri}> {{ ?s ?p ?o }} }}"
                )
                item["query.rows"] = sorted(
                    row["values"]["s"]["iri"] + "|" + row["values"]["o"]["value"]
                    for row in rows["bindings"]
                )
                store.update(
                    f'INSERT DATA {{ GRAPH <{graph_iri}> {{ '
                    f'<urn:platform:q8:dual#s3> <urn:platform:q8:dual#p> "three" }} }}'
                )
                item["count.afterUpdate"] = store.count_graph(graph_iri)
                exported = store.export_graph(graph_iri)
                item["export.lines"] = len(
                    [line for line in exported.decode("utf-8").splitlines() if line.strip()]
                )
                store.clear_graph(graph_iri)
                item["count.afterClear"] = store.count_graph(graph_iri)
                item["probe"] = store.probe()["cleaned"]
                results[name] = item
        finally:
            for store in stores.values():
                try:
                    store.clear_graph(graph_iri)
                except Exception:
                    pass
                store.close()

        print("\n=== graph dual-run table ===")
        print(f"{'item':22} {'oxigraph-http':18} {'jena-fuseki':18} equal")
        for key in results["oxigraph-http"]:
            left = results["oxigraph-http"][key]
            right = results["jena-fuseki"][key]
            print(
                f"{key:22} {str(left)[:18]:18} {str(right)[:18]:18} "
                f"{'yes' if left == right else 'NO'}"
            )
            self.assertEqual(left, right, f"{key} differs between backends")

    def test_2_consistency_elk_vs_hermit(self):
        elk_service = ReasoningService(
            ReasoningConfig(mode="validate", profile="EL"),
            None,
            None,
            ReasonerClient(ReasoningConfig(endpoint=REASONER_URL)),
            None,
            None,
        )
        hermit = HermitReasoner(REASONER_URL)
        try:
            cases = {"consistent": CONSISTENT, "inconsistent": INCONSISTENT}
            observed: dict[str, dict] = {}
            for label, ttl in cases.items():
                left = elk_service.check_consistency(ttl.encode("utf-8"))
                right = hermit.check_consistency(ttl.encode("utf-8"))
                observed[label] = {"elk": left, "hermit": right}
                print(
                    f"\nconsistency[{label}] elk={left['consistent']} "
                    f"(code={left.get('reasonCode')}) "
                    f"hermit={right['consistent']} (code={right.get('reasonCode')})"
                )
                self.assertIsInstance(left["consistent"], bool)
                self.assertIsInstance(right["consistent"], bool)
                if label == "inconsistent":
                    # HermiT is the DL gate and must catch the disjointness clash.
                    self.assertFalse(right["consistent"], right)
                else:
                    self.assertTrue(left["consistent"], left)
                    self.assertTrue(right["consistent"], right)
        finally:
            hermit.close()
            elk_service._reasoner.close()

    def test_3_classify_hermit_returns_axioms(self):
        hermit = HermitReasoner(REASONER_URL)
        try:
            payload = hermit.classify(CONSISTENT.encode("utf-8"))
            print(f"\nclassify subClassOf={len(payload['subClassOf'])} "
                  f"equivalent={len(payload['equivalentClasses'])} "
                  f"disjoint={len(payload['disjointClasses'])}")
            self.assertGreaterEqual(len(payload["subClassOf"]), 2, payload)
        finally:
            hermit.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
