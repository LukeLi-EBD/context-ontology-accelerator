"""Q7-a startup gate tests: missing T-Box blocks serve, benign paths still start.

Runs against the live postgres/oxigraph (no rebuild):
  docker compose exec -T -e PYTHONPATH=/app/src platform \
    python /tmp/hosttests/test_q7_ontology_init.py
"""

import os
import unittest
from types import SimpleNamespace

from platform_core.adapters.graph_oxigraph import OxigraphHttpStore
from platform_core.adapters.metadata_pg import MetadataPg
from platform_core.adapters.ontology_pg import OntologyRegistry
from platform_core.config import OntologyConfig
from platform_core.errors import EXIT_CONFIG, EXIT_UNAVAILABLE, PlatformError
from platform_core.ontology_init import start

DSN = os.environ.get("TEST_PG_DSN")
OXIGRAPH_URL = os.environ.get("TEST_OXIGRAPH_URL", "http://oxigraph:7878")
BOOTSTRAP_TTL = "/data/ontology/bootstrap.ttl"


class _NoPointerRegistry:
    """Real bootstrap, but pretending the DB has no published pointer."""

    def __init__(self, inner):
        self._inner = inner

    def bootstrap(self, *args, **kwargs):
        return self._inner.bootstrap(*args, **kwargs)

    def current(self):
        return None


@unittest.skipUnless(DSN, "TEST_PG_DSN not set; refusing to fall back to a default database")
class OntologyInitGateTests(unittest.TestCase):
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

    @staticmethod
    def _runtime(config, ontology):
        return SimpleNamespace(config=SimpleNamespace(ontology=config), ontology=ontology)

    def test_1_missing_tbox_blocks_startup_with_69(self):
        cfg = OntologyConfig(
            init_mode="once",
            init_source="/tmp/q7-missing-tbox.ttl",
            init_semver="0.0.0",
        )
        runtime = self._runtime(cfg, _NoPointerRegistry(self.registry))
        with self.assertRaises(PlatformError) as ctx:
            start(runtime)
        self.assertEqual(ctx.exception.code, "E_ONTOLOGY_TBOX_MISSING")
        self.assertEqual(ctx.exception.exit_code, EXIT_UNAVAILABLE)
        self.assertEqual(ctx.exception.key, "ontology.init_source")

    def test_2_benign_skip_does_not_block_startup(self):
        # The init watcher only owns versions whose semver equals init_semver, so
        # this case needs a semver that cannot match the live pointer. Derive it
        # from the pointer instead of assuming a historical value (a fresh DB
        # publishes the bootstrap as 0.0.0, which made the old hard-coded 0.0.0
        # look "unchanged" instead of "managed outside init source").
        live = self.registry.current() or {}
        live_semver = str(live.get("semver") or "0.0.0")
        init_semver = "9.9.9" if live_semver != "9.9.9" else "8.8.8"
        cfg = OntologyConfig(
            init_mode="once",
            init_source=BOOTSTRAP_TTL,
            init_semver=init_semver,
        )
        runtime = self._runtime(cfg, self.registry)
        state = start(runtime)
        self.assertEqual(state["mode"], "once")
        self.assertEqual(state["initial"]["status"], "skipped")
        self.assertEqual(state["initial"]["reason"], "pointer managed outside init source")


if __name__ == "__main__":
    unittest.main(verbosity=2)
