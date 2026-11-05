"""G-01 publish tests: dry-run, governed publish, idempotency, unusable refusal.

Runs against the already-running postgres/oxigraph/reasoner (no rebuild):
  docker run --rm --entrypoint python -e PYTHONPATH=/hostsrc \
    -v <repo>/src:/hostsrc:ro -v <repo>/tests:/hosttests:ro \
    agent-platform:0.1-s5 /hosttests/test_g01_import_publish.py

The temporary namespace is urn:s14pub:; the active pointer is captured before
each test and restored afterwards, so urn:fsldm:tbox versions are never left
switched.
"""

import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

import platform_core.api as api_module
from platform_core.adapters.graph_oxigraph import OxigraphHttpStore
from platform_core.adapters.metadata_pg import MetadataPg
from platform_core.adapters.ontology_pg import (
    OntologyRegistry,
    build_import_document,
    persist_import,
    publish_import,
)
from platform_core.adapters.reasoner_robot import ReasonerClient
from platform_core.config import OntologyConfig, ReasoningConfig
from platform_core.validation import ShaclValidator

DSN = os.environ.get(
    "TEST_PG_DSN",
    os.environ.get(
        "PLATFORM__DATABASE__URL",
        "postgres://platform:***MASKED***@host.docker.internal:5432/platform",
    ),
)
OXIGRAPH_URL = os.environ.get("TEST_OXIGRAPH_URL", "http://host.docker.internal:7878")
REASONER_URL = os.environ.get("TEST_REASONER_URL", "http://host.docker.internal:7879")
POINTER_NAME = "tbox/current"
NAMESPACE = "urn:s14pub:"

TTL = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<urn:s14pub:Widget> a owl:Class ;
    rdfs:label "Widget"@en .
"""

SHAPES_TTL = """\
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<urn:s14pub:shape:ClassLabel> a sh:NodeShape ;
    sh:targetClass owl:Class ;
    sh:property [ sh:path rdfs:label ; sh:minCount 1 ] .
"""

ROOT_SHAPES_TTL = """\
@prefix sh: <http://www.w3.org/ns/shacl#> .

<urn:test:shape:Noop> a sh:NodeShape .
"""

TTL_VARIANT = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<urn:s14pub:Widget> a owl:Class ;
    rdfs:label "Widget"@en .

<urn:s14pub:Gadget> a owl:Class ;
    rdfs:label "Gadget"@en .
"""


class _FakeObjects:
    """CAS double: publish copies the staging graph through the object store."""

    def __init__(self):
        self.store: dict[tuple[str, str], bytes] = {}

    def put(self, bucket, key, body, content_type="application/octet-stream", metadata=None):
        self.store[(bucket, key)] = bytes(body)
        return {"bucket": bucket, "key": key, "size": len(self.store[(bucket, key)])}

    def get(self, bucket, key):
        return self.store[(bucket, key)], {}


class _BrokenTx:
    """Tx double that fails on the import-record INSERT only."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, *args, **kwargs):
        raise RuntimeError("injected record failure")

    def execute_returning(self, *args, **kwargs):
        raise RuntimeError("injected record failure")


class _BrokenMeta:
    def __init__(self, real):
        self.real = real

    def tx(self):
        return _BrokenTx()


class PublishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = MetadataPg(DSN)
        cls.meta.open(retry_seconds=15)
        cls.graph = OxigraphHttpStore(OXIGRAPH_URL)
        cls.objects = _FakeObjects()
        cls.registry = OntologyRegistry(cls.meta, cls.graph, cls.objects, OntologyConfig())
        cls.reasoner = ReasonerClient(
            ReasoningConfig(endpoint=REASONER_URL, timeout_ms=120000, profile="EL")
        )
        cls.registry.set_governance(
            validator=ShaclValidator(ReasoningConfig(shapes_dir=cls._root_shapes_dir())),
            reasoner=cls.reasoner,
            materializer=lambda: {"jobId": "job-stub", "inferred": 0, "skipped": True},
            abox_graphs=[],
            reason_profile="EL",
        )
        cls.reasoning_config = ReasoningConfig(
            endpoint=REASONER_URL, timeout_ms=120000, profile="EL", abox_graphs=[]
        )
        runtime = SimpleNamespace(
            metadata=cls.meta,
            graph=cls.graph,
            objects=cls.objects,
            ontology=cls.registry,
            config=SimpleNamespace(
                mode="test",
                config_version=1,
                runtime=SimpleNamespace(mode="test"),
                reasoning=cls.reasoning_config,
            ),
        )
        cls.client = TestClient(api_module.create_app(runtime, []))
        cls.client.__enter__()

    @classmethod
    def _root_shapes_dir(cls) -> str:
        directory = Path(tempfile.mkdtemp())
        (directory / "core.ttl").write_text(ROOT_SHAPES_TTL, encoding="utf-8")
        return str(directory)

    @classmethod
    def _namespace_shapes_dir(cls) -> str:
        directory = Path(tempfile.mkdtemp())
        segment = directory / "s14pub"
        segment.mkdir()
        (segment / "shapes.ttl").write_text(SHAPES_TTL, encoding="utf-8")
        (segment / "manifest.json").write_text(
            '{"id": "s14pub-shapes", "version": "0.2.0"}', encoding="utf-8"
        )
        return str(directory)

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        cls.reasoner.close()
        cls.graph.close()
        cls.meta.close()

    def setUp(self):
        self.created: list[dict] = []
        rows = self.meta.query(
            "SELECT version_id, updated_by FROM platform.graph_pointer WHERE name = %s",
            (POINTER_NAME,),
        )
        self.original_pointer = rows[0]["version_id"] if rows else None
        status = self.meta.query(
            "SELECT status FROM platform.ontology_version WHERE version_id = %s",
            (self.original_pointer,) if self.original_pointer else (None,),
        )
        self.original_status = status[0]["status"] if status else "published"

    def tearDown(self):
        if self.original_pointer:
            with self.meta.tx() as tx:
                tx.execute(
                    """
                    INSERT INTO platform.graph_pointer (name, version_id, updated_at, updated_by)
                    VALUES (%s, %s, now(), 'test-cleanup')
                    ON CONFLICT (name) DO UPDATE
                      SET version_id = EXCLUDED.version_id, updated_at = now()
                    """,
                    (POINTER_NAME, self.original_pointer),
                )
                tx.execute(
                    "UPDATE platform.ontology_version SET status = %s WHERE version_id = %s",
                    (self.original_status, self.original_pointer),
                )
        for record in self.created:
            version_id = publish_import_version(record["importId"])
            with self.meta.tx() as tx:
                tx.execute(
                    "DELETE FROM platform.ontology_proposal WHERE version_id = %s", (version_id,)
                )
                tx.execute(
                    "DELETE FROM platform.ontology_event WHERE version_id = %s", (version_id,)
                )
                tx.execute(
                    "DELETE FROM platform.ontology_event WHERE action = 'superseded' "
                    "AND payload->>'replacedBy' = %s",
                    (version_id,),
                )
                tx.execute(
                    "DELETE FROM platform.ontology_version WHERE version_id = %s", (version_id,)
                )
                tx.execute(
                    "DELETE FROM platform.ontology_import WHERE import_id = %s",
                    (record["importId"],),
                )
            for graph_iri in (record["stagingGraph"], f"urn:platform:graph:tbox:{version_id}"):
                try:
                    self.graph.update(f"DROP SILENT GRAPH <{graph_iri}>")
                except Exception:
                    pass
        self.created = []

    def _consistency(self, tbox_nt: bytes):
        return self.reasoner.reason(tbox_nt, b"", profile="EL", consistency_first=True)

    def _import(self, author: str, usable: bool = True):
        return self._import_ttl(TTL, author, usable=usable)

    def _import_ttl(self, ttl: str, author: str, usable: bool = True):
        kwargs = dict(
            target_namespace=NAMESPACE,
            author=author,
            change_summary="G-01 publish test",
            shapes_dir=self._namespace_shapes_dir(),
        )
        if usable:
            kwargs["consistency_checker"] = self._consistency
        else:
            kwargs["shapes_dir"] = "/nonexistent"
        result, merged = build_import_document(ttl.encode("utf-8"), **kwargs)
        record = persist_import(result, merged, ttl.encode("utf-8"), self.meta, self.graph)
        self.created.append(record)
        return record

    def _publish(self, import_id: str, dry_run: bool, publish_existing: bool = False):
        body = {"dryRun": dry_run}
        if not dry_run:
            body["acknowledgeBreaking"] = True
        if publish_existing:
            body["publishExisting"] = True
        response = self.client.post(
            f"/api/ontology/imports/{import_id}/publish", json=body
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def _events(self, version_id: str) -> list[dict]:
        rows = self.meta.query(
            "SELECT event_id, action, actor, payload FROM platform.ontology_event "
            "WHERE version_id = %s ORDER BY event_id",
            (version_id,),
        )
        return rows

    def _publish_superseded(self, author: str) -> str:
        """Publish content X, then content Y, leaving X's version superseded."""
        first = self._import(author + "x")
        version_x = self._publish(first["importId"], dry_run=False)["versionId"]
        second = self._import_ttl(TTL_VARIANT, author + "y")
        version_y = self._publish(second["importId"], dry_run=False)["versionId"]
        self.assertNotEqual(version_x, version_y)
        self.assertEqual(self.registry.current()["versionId"], version_y)
        return version_x

    def test_1_unusable_import_is_refused(self):
        record = self._import("p1", usable=False)
        before = self.registry.current()["versionId"]
        response = self.client.post(
            f"/ontology/imports/{record['importId']}/publish", json={"dryRun": False}
        )
        self.assertEqual(response.status_code, 409, response.text)
        error = response.json()["error"]
        self.assertEqual(error["providerCode"], "E_IMPORT_NOT_USABLE")
        self.assertEqual(error["details"]["reason"], record["reason"])
        self.assertEqual(self.registry.current()["versionId"], before)

    def test_2_dry_run_returns_diff_and_impact_without_switching(self):
        record = self._import("p2")
        before = self.registry.current()["versionId"]
        payload = self._publish(record["importId"], dry_run=True)
        self.assertFalse(payload["published"])
        self.assertIsNone(payload["publishedAt"])
        self.assertEqual(payload["previousVersionId"], before)
        self.assertEqual(payload["diff"]["addedClasses"], 1)
        self.assertGreaterEqual(payload["diff"]["removedClasses"], 0)
        self.assertGreaterEqual(payload["diff"]["addedTriples"], 2)
        self.assertLessEqual(len(payload["diff"]["examples"]["addedClasses"]), 5)
        self.assertEqual(payload["impact"]["addedTriples"], payload["diff"]["addedTriples"])
        self.assertEqual(payload["impact"]["affectedEntities"], 0)
        self.assertEqual(self.registry.current()["versionId"], before)

    def test_3_publish_switches_pointer_to_versioned_graph(self):
        record = self._import("p3")
        before = self.registry.current()["versionId"]
        payload = self._publish(record["importId"], dry_run=False)
        self.assertTrue(payload["published"])
        self.assertEqual(payload["previousVersionId"], before)
        self.assertEqual(payload["pointer"], f"urn:platform:graph:tbox:{payload['versionId']}")
        self.assertTrue(payload["publishedAt"])
        current = self.registry.current()
        self.assertEqual(current["versionId"], payload["versionId"])
        self.assertEqual(current["graph"], payload["pointer"])
        self.assertNotEqual(payload["versionId"], before)

    def test_4_repeat_publish_returns_same_version(self):
        record = self._import("p4")
        first = self._publish(record["importId"], dry_run=False)
        second = self._publish(record["importId"], dry_run=False)
        self.assertEqual(first["versionId"], second["versionId"])
        self.assertTrue(second["idempotent"])
        rows = self.meta.query(
            "SELECT count(*) AS n FROM platform.ontology_version WHERE version_id = %s",
            (first["versionId"],),
        )
        self.assertEqual(rows[0]["n"], 1)
        self.assertEqual(self.registry.current()["versionId"], first["versionId"])


    def test_5_record_failure_drops_staging_graph(self):
        result, merged = build_import_document(
            TTL.encode("utf-8"),
            target_namespace=NAMESPACE,
            author="p5",
            change_summary="record-failure branch",
            shapes_dir="/nonexistent",
        )
        import_id = result["importId"]
        staging = f"urn:platform:graph:import:{import_id}"
        with self.assertRaises(Exception) as caught:
            persist_import(
                result, merged, TTL.encode("utf-8"), _BrokenMeta(self.meta), self.graph
            )
        self.assertEqual(
            getattr(caught.exception, "provider_code", None), "E_ONTOLOGY_RECORD_FAILED"
        )
        self.assertEqual(self.graph.count_graph(staging), 0)
        rows = self.meta.query(
            "SELECT count(*) AS n FROM platform.ontology_import WHERE import_id = %s",
            (import_id,),
        )
        self.assertEqual(rows[0]["n"], 0)


    def test_6_publish_existing_same_content(self):
        """Same canonical content re-publishes the existing version (OQ-65)."""
        version_x = self._publish_superseded("p6")
        repeat = self._import("p6c")
        payload = self._publish(repeat["importId"], dry_run=False, publish_existing=True)

        self.assertEqual(payload["mode"], "activate_existing")
        self.assertEqual(payload["versionId"], version_x)
        self.assertEqual(payload["canonicalEqualTo"], version_x)
        self.assertNotEqual(payload["previousVersionId"], version_x)
        self.assertEqual(payload["publishedBy"], "operator")
        self.assertFalse(payload["idempotent"])
        self.assertIn("shacl", payload["gates"])
        self.assertIn("consistency", payload["gates"])
        self.assertEqual(self.registry.current()["versionId"], version_x)

        published_events = [
            e for e in self._events(version_x) if e["action"] == "published"
        ]
        last = published_events[-1]["payload"]
        if isinstance(last, str):
            import json as _json
            last = _json.loads(last)
        self.assertEqual(last["mode"], "activate_existing")
        self.assertEqual(last["publishedBy"], "operator")
        self.assertEqual(last["previousVersionId"], payload["previousVersionId"])

    def test_7_publish_existing_is_idempotent(self):
        """A second forward publish is a no-op and adds no audit event."""
        version_x = self._publish_superseded("p7")
        repeat = self._import("p7c")
        first = self._publish(repeat["importId"], dry_run=False, publish_existing=True)
        second = self._publish(repeat["importId"], dry_run=False, publish_existing=True)

        self.assertEqual(first["versionId"], version_x)
        self.assertTrue(second["idempotent"])
        self.assertTrue(second["unchanged"])
        self.assertEqual(second["versionId"], version_x)
        self.assertEqual(self.registry.current()["versionId"], version_x)
        published = [e for e in self._events(version_x) if e["action"] == "published"]
        # 1 = original publish in _publish_superseded; repeated forward publish
        # is idempotent and must not append another event.
        self.assertEqual(len(published), 2)

    def test_8_concurrent_forward_publish_only_one_wins(self):
        """Two simultaneous forward publishes append exactly one published event."""
        version_x = self._publish_superseded("p8")
        left = self._import("p8a")
        right = self._import("p8b")

        def call(import_id: str, actor: str) -> dict:
            return publish_import(
                self.meta, self.graph, self.objects, self.registry,
                import_id,
                dry_run=False,
                actor=actor,
                change_summary="concurrent forward publish",
                acknowledge_breaking=True,
                publish_existing=True,
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(
                lambda pair: call(*pair),
                [(left["importId"], "t-left"), (right["importId"], "t-right")],
            ))

        wins = [r for r in results if not r.get("idempotent")]
        losses = [r for r in results if r.get("idempotent")]
        self.assertEqual(len(wins), 1, results)
        self.assertEqual(len(losses), 1, results)
        self.assertEqual(self.registry.current()["versionId"], version_x)
        published = [e for e in self._events(version_x) if e["action"] == "published"]
        # 1 = original publish in _publish_superseded; the two concurrent
        # forward publishes must append exactly one more, not two.
        self.assertEqual(len(published), 2)

    def test_9_publish_after_rollback(self):
        """After rolling back, the forward publish path can activate the version again."""
        first = self._import("p9x")
        version_x = self._publish(first["importId"], dry_run=False)["versionId"]
        second = self._import_ttl(TTL_VARIANT, "p9y")
        version_y = self._publish(second["importId"], dry_run=False)["versionId"]

        self.registry.rollback_to(version_x, actor="t-rollback", reason="revert for test")
        self.assertEqual(self.registry.current()["versionId"], version_x)
        self.assertIn(
            "rolled_back", [e["action"] for e in self._events(version_x)]
        )

        third = self._import_ttl(TTL_VARIANT, "p9z")
        payload = self._publish(third["importId"], dry_run=False, publish_existing=True)
        self.assertEqual(payload["versionId"], version_y)
        self.assertEqual(payload["mode"], "activate_existing")
        self.assertEqual(payload["previousVersionId"], version_x)
        self.assertEqual(self.registry.current()["versionId"], version_y)
        self.assertIn(
            "published", [e["action"] for e in self._events(version_y)]
        )


def publish_import_version(import_id: str) -> str:
    import hashlib

    return "ont-" + hashlib.sha256(f"g01-import:{import_id}".encode("utf-8")).hexdigest()[:12]


if __name__ == "__main__":
    unittest.main(verbosity=2)
