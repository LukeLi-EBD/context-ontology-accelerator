"""V52 ownership: a new ontology_version row records its namespace when known.

Scope under test (the only four INSERTs into platform.ontology_version):
  * import_source   -- what the bridge calls on import
  * import_document -- bundle/restore path
  * publish_import  -- staged import publish path
  * rollback        -- restores a target's content, so it inherits its owner

Guarantees asserted here:
  1. a namespace uuid supplied by the caller is stored verbatim;
  2. an absent namespace stays NULL instead of being guessed;
  3. a non-uuid namespace is rejected instead of being stored as NULL;
  4. rollback inherits the target row's owner and does not invent one.

Runs against a real postgres + oxigraph + reasoner (no rebuild):
  docker run --rm --entrypoint python -e PYTHONPATH=/hostsrc \
    -v <repo>/packages/platform-core/src:/hostsrc:ro \
    -v <repo>/packages/platform-core/tests:/hosttests:ro \
    <image> /hosttests/test_ontology_version_namespace.py
"""

import contextlib
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import platform_core.api as api_module
from fastapi.testclient import TestClient
from platform_core.adapters.graph_oxigraph import OxigraphHttpStore
from platform_core.adapters.metadata_pg import MetadataPg
from platform_core.adapters.ontology_pg import (
    OntologyRegistry,
    build_import_document,
    persist_import,
)
from platform_core.adapters.reasoner_robot import ReasonerClient
from platform_core.config import OntologyConfig, ReasoningConfig
from platform_core.errors import PortError
from platform_core.validation import ShaclValidator

DSN = os.environ.get(
    "TEST_PG_DSN",
    os.environ.get(
        "PLATFORM__DATABASE__URL",
        "postgres://platform:***MASKED***@postgres:5432/platform",
    ),
)
OXIGRAPH_URL = os.environ.get("TEST_OXIGRAPH_URL", "http://oxigraph:7878")
REASONER_URL = os.environ.get("TEST_REASONER_URL", "http://reasoner:7879")
POINTER_NAME = "tbox/current"

# demo-ns, the only namespace registered in the local control plane.
DEMO_NAMESPACE_ID = "ed70a15c-2d42-4dc9-8c61-33b2584f05fd"
OTHER_NAMESPACE_ID = "cdfdc4f5-ebaa-414e-b243-c25b22a37ca5"
NAMESPACE = "urn:nsid:"

TTL = """\
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<urn:nsid:Widget> a owl:Class ;
    rdfs:label "Widget"@en .
"""

SHAPES_TTL = """\
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<urn:nsid:shape:ClassLabel> a sh:NodeShape ;
    sh:targetClass owl:Class ;
    sh:property [ sh:path rdfs:label ; sh:minCount 1 ] .
"""

ROOT_SHAPES_TTL = """\
@prefix sh: <http://www.w3.org/ns/shacl#> .

<urn:test:shape:Noop> a sh:NodeShape .
"""


class _FakeObjects:
    """CAS double; ownership lives in postgres, not in the object store."""

    def __init__(self):
        self.store: dict[tuple[str, str], bytes] = {}

    def put(self, bucket, key, body, content_type="application/octet-stream", metadata=None):
        self.store[(bucket, key)] = bytes(body)
        return {"bucket": bucket, "key": key, "size": len(self.store[(bucket, key)])}

    def get(self, bucket, key):
        return self.store[(bucket, key)], {}


class OntologyVersionNamespaceTest(unittest.TestCase):
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
                storage=SimpleNamespace(root=tempfile.mkdtemp()),
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
        segment = directory / "nsid"
        segment.mkdir()
        (segment / "shapes.ttl").write_text(SHAPES_TTL, encoding="utf-8")
        (segment / "manifest.json").write_text(
            '{"id": "nsid-shapes", "version": "0.1.0"}', encoding="utf-8"
        )
        return str(directory)

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        cls.reasoner.close()
        cls.graph.close()
        cls.meta.close()

    def setUp(self):
        self.version_ids: list[str] = []
        self.import_ids: list[str] = []
        self.graph_iris: set[str] = set()
        rows = self.meta.query(
            "SELECT version_id FROM platform.graph_pointer WHERE name = %s",
            (POINTER_NAME,),
        )
        self.original_pointer = rows[0]["version_id"] if rows else None
        self.original_status = None
        if self.original_pointer:
            status = self.meta.query(
                "SELECT status FROM platform.ontology_version WHERE version_id = %s",
                (self.original_pointer,),
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
                if self.original_status:
                    tx.execute(
                        "UPDATE platform.ontology_version SET status = %s WHERE version_id = %s",
                        (self.original_status, self.original_pointer),
                    )
        else:
            with self.meta.tx() as tx:
                tx.execute(
                    "DELETE FROM platform.graph_pointer WHERE name = %s", (POINTER_NAME,)
                )
        for version_id in self.version_ids:
            with self.meta.tx() as tx:
                # rollback rows point at their target; clear the FK before deleting
                tx.execute(
                    "UPDATE platform.ontology_version SET rollback_of = NULL "
                    "WHERE rollback_of = %s",
                    (version_id,),
                )
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
            self.graph_iris.add(f"urn:platform:graph:tbox:{version_id}")
        for import_id in self.import_ids:
            with self.meta.tx() as tx:
                tx.execute(
                    "DELETE FROM platform.ontology_import WHERE import_id = %s", (import_id,)
                )
        for graph_iri in self.graph_iris:
            with contextlib.suppress(Exception):
                self.graph.update(f"DROP SILENT GRAPH <{graph_iri}>")

    # ---- helpers ---------------------------------------------------------

    def _ttl_file(self) -> str:
        suffix = ".ttl"
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(TTL)
        return path

    def _row(self, version_id: str) -> dict:
        rows = self.meta.query(
            "SELECT version_id, namespace_id, attribution_source, status, label "
            "FROM platform.ontology_version WHERE version_id = %s",
            (version_id,),
        )
        self.assertTrue(rows, f"version {version_id} not found")
        return rows[0]

    def _import_source(self, namespace_id=None) -> dict:
        path = self._ttl_file()
        try:
            result = self.registry.import_source(
                path,
                "1.0.0",
                "nsid-local",
                "turtle",
                namespace_id=namespace_id,
            )
        finally:
            os.unlink(path)
        self.version_ids.append(result["versionId"])
        return result

    def _stage(self) -> dict:
        ttl = TTL.encode("utf-8")
        result, merged = build_import_document(
            ttl,
            target_namespace=NAMESPACE,
            author="nsid-test",
            change_summary="namespace ownership test",
            shapes_dir=self._namespace_shapes_dir(),
            consistency_checker=lambda tbox_nt: self.reasoner.reason(
                tbox_nt, b"", profile="EL", consistency_first=True
            ),
        )
        record = persist_import(result, merged, ttl, self.meta, self.graph)
        self.import_ids.append(record["importId"])
        self.graph_iris.add(record["stagingGraph"])
        return record

    def _publish(self, import_id: str, namespace_id: str | None) -> dict:
        body = {"dryRun": False, "acknowledgeBreaking": True}
        if namespace_id:
            body["namespaceId"] = namespace_id
        response = self.client.post(f"/ontology/imports/{import_id}/publish", json=body)
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.version_ids.append(payload["versionId"])
        return payload

    # ---- tests -----------------------------------------------------------

    def test_import_source_records_namespace_id(self):
        result = self._import_source(DEMO_NAMESPACE_ID)
        row = self._row(result["versionId"])
        self.assertEqual(str(row["namespace_id"]), DEMO_NAMESPACE_ID)
        self.assertEqual(row["attribution_source"], "platform")

    def test_import_source_without_namespace_stays_null(self):
        result = self._import_source()
        row = self._row(result["versionId"])
        self.assertIsNone(row["namespace_id"])
        self.assertIsNone(row["attribution_source"])

    def test_import_source_rejects_non_uuid_namespace(self):
        path = self._ttl_file()
        try:
            with self.assertRaises(PortError) as caught:
                self.registry.import_source(
                    path, "1.0.0", "nsid-local", "turtle", namespace_id="demo-ns"
                )
        finally:
            os.unlink(path)
        self.assertEqual(caught.exception.provider_code, "E_ONTOLOGY_BAD_NAMESPACE_ID")
        rows = self.meta.query(
            "SELECT count(*) AS n FROM platform.ontology_version WHERE label = %s",
            ("nsid-local",),
        )
        self.assertEqual(rows[0]["n"], 0, "a rejected import must not write a row")

    def test_publish_import_records_namespace_id(self):
        record = self._stage()
        payload = self._publish(record["importId"], OTHER_NAMESPACE_ID)
        row = self._row(payload["versionId"])
        self.assertEqual(str(row["namespace_id"]), OTHER_NAMESPACE_ID)
        self.assertEqual(row["attribution_source"], "platform")

    def test_publish_import_without_namespace_stays_null(self):
        record = self._stage()
        payload = self._publish(record["importId"], None)
        row = self._row(payload["versionId"])
        self.assertIsNone(row["namespace_id"])

    def test_publish_claims_unowned_version(self):
        # Publishing an older draft is where a caller can state its namespace.
        result = self._import_source()
        claimed = self.registry.claim_namespace(result["versionId"], DEMO_NAMESPACE_ID)
        self.assertTrue(claimed["claimed"])
        row = self._row(result["versionId"])
        self.assertEqual(str(row["namespace_id"]), DEMO_NAMESPACE_ID)
        self.assertEqual(row["attribution_source"], "platform")
        again = self.registry.claim_namespace(result["versionId"], DEMO_NAMESPACE_ID)
        self.assertFalse(again["claimed"])

    def test_claim_rejects_a_different_namespace(self):
        result = self._import_source(DEMO_NAMESPACE_ID)
        with self.assertRaises(PortError) as caught:
            self.registry.claim_namespace(result["versionId"], OTHER_NAMESPACE_ID)
        self.assertEqual(caught.exception.provider_code, "E_ONTOLOGY_NAMESPACE_CONFLICT")
        row = self._row(result["versionId"])
        self.assertEqual(str(row["namespace_id"]), DEMO_NAMESPACE_ID)

    def test_rollback_inherits_target_namespace(self):
        record = self._stage()
        published = self._publish(record["importId"], DEMO_NAMESPACE_ID)
        rolled = self.registry.rollback(published["versionId"])
        self.version_ids.append(rolled["id"])
        row = self._row(rolled["id"])
        self.assertEqual(str(row["namespace_id"]), DEMO_NAMESPACE_ID)
        self.assertEqual(row["attribution_source"], "platform")

    def test_rollback_of_legacy_row_does_not_invent_namespace(self):
        # A row written before V52 has no owner; its rollback must stay NULL.
        result = self._import_source()
        rolled = self.registry.rollback(result["versionId"])
        self.version_ids.append(rolled["id"])
        row = self._row(rolled["id"])
        self.assertIsNone(row["namespace_id"])
        self.assertIsNone(row["attribution_source"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
