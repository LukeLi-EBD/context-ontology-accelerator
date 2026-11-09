"""G-01 persistence tests: import record + staging graph + rollback.

These hit the already-running postgres/oxigraph (no rebuild, no lock):
  docker run --rm --entrypoint python -e PYTHONPATH=/hostsrc \
    -v <repo>/src:/hostsrc:ro -v <repo>/tests:/hosttests:ro \
    agent-platform:0.1-s5 /hosttests/test_g01_import_persist.py
"""

import os
import unittest

from platform_core.adapters.graph_oxigraph import OxigraphHttpStore
from platform_core.adapters.metadata_pg import MetadataPg
from platform_core.adapters.ontology_pg import (
    build_import_document,
    get_import_record,
    persist_import,
)
from platform_core.errors import PortError

DSN = os.environ.get("TEST_PG_DSN")
OXIGRAPH_URL = os.environ.get("TEST_OXIGRAPH_URL", "http://oxigraph:7878")
NAMESPACE = "https://w3id.org/fsldm/"
TTL = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<https://w3id.org/fsldm/Agreement> a owl:Class ;
    rdfs:label "Agreement"@en .
"""


@unittest.skipUnless(DSN, "TEST_PG_DSN not set; refusing to fall back to PLATFORM__DATABASE__URL")
class PersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = MetadataPg(DSN)
        cls.meta.open(retry_seconds=15)
        cls.graph = OxigraphHttpStore(OXIGRAPH_URL)
        cls.created: list[tuple[str, str]] = []

    @classmethod
    def tearDownClass(cls):
        for import_id, staging in cls.created:
            try:
                with cls.meta.tx() as tx:
                    tx.execute("DELETE FROM platform.ontology_import WHERE import_id = %s", (import_id,))
            except Exception:
                pass
            try:
                cls.graph.update(f"DROP SILENT GRAPH <{staging}>")
            except Exception:
                pass
        cls.graph.close()
        cls.meta.close()

    def _persist(self, author: str, change_summary: str):
        result, merged = build_import_document(
            TTL.encode("utf-8"),
            target_namespace=NAMESPACE,
            author=author,
            change_summary=change_summary,
            shapes_dir="/nonexistent",
        )
        record = persist_import(result, merged, TTL.encode("utf-8"), self.meta, self.graph)
        self.__class__.created.append((record["importId"], record["stagingGraph"]))
        return record

    def test_record_is_queryable_with_author_and_created_at(self):
        record = self._persist("alice", "record test")
        stored = get_import_record(self.meta, record["importId"])
        self.assertIsNotNone(stored)
        self.assertEqual(stored["author"], "alice")
        self.assertEqual(stored["change_summary"], "record test")
        self.assertTrue(stored["created_at"])
        self.assertEqual(stored["target_namespace"], NAMESPACE)
        self.assertTrue(stored["version_id"].startswith("ont-draft-"))
        self.assertFalse(stored["usable"])
        self.assertEqual(stored["reason"], "E_SHACL_NOT_DEPLOYED")
        self.assertEqual(stored["staging_graph"], record["stagingGraph"])

    def test_staging_graph_is_sparql_queryable(self):
        record = self._persist("bob", "graph test")
        query = (
            "SELECT ?s ?p ?o WHERE { GRAPH <%s> { ?s ?p ?o } } LIMIT 10"
            % record["stagingGraph"]
        )
        payload = self.graph.query(query)
        bindings = payload.get("bindings", [])
        self.assertEqual(len(bindings), 2)
        subjects = {
            row["values"]["s"].get("iri") or row["values"]["s"].get("value")
            for row in bindings
        }
        self.assertEqual(subjects, {"https://w3id.org/fsldm/Agreement"})

    def test_graph_failure_leaves_no_record(self):
        result, merged = build_import_document(
            TTL.encode("utf-8"),
            target_namespace=NAMESPACE,
            author="carol",
            shapes_dir="/nonexistent",
        )
        bad_graph = "urn:platform:graph:import:bad graph"
        with self.assertRaises(PortError) as ctx:
            persist_import(
                result, merged, TTL.encode("utf-8"), self.meta, self.graph, graph_iri=bad_graph
            )
        self.assertEqual(ctx.exception.provider_code, "E_ONTOLOGY_STAGE_FAILED")
        self.assertIsNone(get_import_record(self.meta, result["importId"]))
        rows = self.meta.query(
            "SELECT count(*) AS n FROM platform.ontology_import WHERE import_id = %s",
            (result["importId"],),
        )
        self.assertEqual(rows[0]["n"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
