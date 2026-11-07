"""Q7-b contract guards: graph whitelist, real range_read, embedding identity.

Runs against the live postgres/oxigraph (no rebuild):
  docker compose exec -T -e PYTHONPATH=/app/src platform \
    python /tmp/hosttests/test_q7_contract.py
"""

import os
import unittest
import uuid
from types import SimpleNamespace

from platform_core.adapters.graph_oxigraph import OxigraphHttpStore
from platform_core.adapters.metadata_pg import MetadataPg
from platform_core.adapters.object_fs import FsCasBackend
from platform_core.adapters.object_layered import LayeredObjectStore
from platform_core.adapters.object_pg import PgByteaBackend
from platform_core.adapters.ontology_pg import OntologyRegistry
from platform_core.bootstrap import _check_embedding_identity
from platform_core.config import EmbeddingConfig, OntologyConfig, StorageConfig
from platform_core.errors import EXIT_CONFIG, PlatformError, PortError

DSN = os.environ.get("TEST_PG_DSN")
OXIGRAPH_URL = os.environ.get("TEST_OXIGRAPH_URL", "http://oxigraph:7878")
DATA_ROOT = os.environ.get("TEST_DATA_ROOT", "/data")


@unittest.skipUnless(DSN, "TEST_PG_DSN not set; refusing to fall back to a default database")
class ContractGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = MetadataPg(DSN)
        cls.meta.open(retry_seconds=15)
        cls.graph = OxigraphHttpStore(OXIGRAPH_URL)
        cls.registry = OntologyRegistry(cls.meta, cls.graph, None, OntologyConfig())

    @classmethod
    def tearDownClass(cls):
        cls.graph.close()
        cls.meta.close()

    # ---- Q7-b (1) named graph whitelist ---------------------------------

    def test_1_query_rejects_graph_outside_the_whitelist(self):
        with self.assertRaises(PortError) as ctx:
            self.graph.query(
                "SELECT * WHERE { GRAPH <https://evil.example/g> { ?s ?p ?o } } LIMIT 1"
            )
        self.assertEqual(ctx.exception.provider_code, "E_GRAPH_GRAPH_NOT_ALLOWED")
        self.assertEqual(ctx.exception.code, "PermissionDenied")
        self.assertEqual(ctx.exception.details["graph"], "https://evil.example/g")

        # A platform-managed graph still works through the FROM clause.
        graph_iri = self.registry.current()["graph"]
        payload = self.graph.query(
            f"SELECT (COUNT(*) AS ?n) FROM <{graph_iri}> WHERE {{ ?s ?p ?o }}"
        )
        self.assertGreater(
            int(payload["bindings"][0]["values"]["n"]["value"]), 0, payload
        )
        # Internal test graphs are whitelisted too (empty is a valid answer).
        self.assertFalse(
            self.graph.ask("ASK { GRAPH <urn:platform:test:q7:guard> { ?s ?p ?o } }")
        )

    # ---- Q7-b (2) real range_read ----------------------------------------

    def test_2_range_read_is_a_real_byte_range_for_fs(self):
        cfg = StorageConfig(root=DATA_ROOT, pg_blob_max_file_mb=1)
        store = LayeredObjectStore(
            cfg,
            self.meta,
            FsCasBackend(DATA_ROOT, f"{DATA_ROOT}/tmp"),
            PgByteaBackend(self.meta),
        )
        key = f"q7-range-{uuid.uuid4().hex}"
        big = bytes((i % 251 for i in range(1536 * 1024)))
        small = b"0123456789abcdef"
        try:
            store.put("q7test", key, big)
            self.assertEqual(store.head("q7test", key)["tier"], "fs")
            data, meta = store.range_read("q7test", key, 1024, 2047)
            self.assertEqual(data, big[1024:2048])
            self.assertEqual(
                meta["range"],
                {
                    "start": 1024,
                    "end": 2047,
                    "length": 1024,
                    "size": len(big),
                    "unit": "bytes",
                    "tier": "fs",
                },
            )
            # End beyond size is clamped, HTTP-style.
            tail, tail_meta = store.range_read("q7test", key, len(big) - 10, len(big) + 100)
            self.assertEqual(tail, big[-10:])
            self.assertEqual(tail_meta["range"]["end"], len(big) - 1)

            store.put("q7test", f"{key}-pg", small)
            self.assertEqual(store.head("q7test", f"{key}-pg")["tier"], "pg")
            with self.assertRaises(PortError) as ctx:
                store.range_read("q7test", f"{key}-pg", 0, 3)
            self.assertEqual(ctx.exception.provider_code, "E_OBJECT_RANGE_UNSUPPORTED")
            self.assertEqual(ctx.exception.code, "Unsupported")
        finally:
            for name in (key, f"{key}-pg"):
                try:
                    store.delete("q7test", name)
                except PortError:
                    pass

    # ---- Q7-b (3) embedding model/dimension startup validation -----------

    def test_3_embedding_model_or_dimension_mismatch_blocks_startup(self):
        class StubEmbedding:
            def __init__(self, model: str, width: int):
                self._model = model
                self._width = width

            def available(self):
                return True

            def service_info(self):
                return {"model": self._model}

            def model_name(self):
                return "BAAI/bge-m3"

            def dimensions(self):
                return 1024

            def embed(self, texts):
                return [[0.0] * self._width for _ in texts]

        def runtime(stub):
            return SimpleNamespace(
                config=SimpleNamespace(
                    embedding=EmbeddingConfig(provider="local-bge")
                ),
                embedding=stub,
            )

        # Wrong model -> 78, before any vector is produced.
        with self.assertRaises(PlatformError) as ctx:
            _check_embedding_identity(
                runtime(StubEmbedding("/data/models/all-minilm-l6", 1024)), []
            )
        self.assertEqual(ctx.exception.code, "E_EMBED_MODEL_MISMATCH")
        self.assertEqual(ctx.exception.exit_code, EXIT_CONFIG)
        self.assertEqual(ctx.exception.key, "embedding.model")

        # Same model, wrong width -> 78 on embedding.dimensions.
        with self.assertRaises(PlatformError) as ctx:
            _check_embedding_identity(
                runtime(StubEmbedding("/data/models/bge-m3", 768)), []
            )
        self.assertEqual(ctx.exception.code, "E_EMBED_MODEL_MISMATCH")
        self.assertEqual(ctx.exception.exit_code, EXIT_CONFIG)
        self.assertEqual(ctx.exception.key, "embedding.dimensions")

        # Matching identity -> ok check, no exception.
        checks = []
        _check_embedding_identity(runtime(StubEmbedding("/data/models/bge-m3", 1024)), checks)
        self.assertEqual(checks[-1].status, "ok")


if __name__ == "__main__":
    unittest.main(verbosity=2)
