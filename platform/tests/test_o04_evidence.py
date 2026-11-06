"""O-04 publish gate evidence pack tests (fakes + tmpdir, no postgres)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

sys.path.insert(0, "/hostsrc")
sys.path.insert(0, "../src")

import platform_core.api as api_module
from platform_core import evidence
from platform_core.adapters.ontology_pg import OntologyRegistry
from platform_core.errors import PortError


VERSION = {"version_id": "ont-new", "semver": "2.0.0", "content_hash": "hash-new",
           "triple_count": 104}
AGAINST = {"version_id": "ont-old", "semver": "1.0.0", "content_hash": "hash-old",
           "triple_count": 100}
PROPOSAL = {"proposal_id": "p-1"}
GATES = {
    "shacl": {"conforms": True, "violations": []},
    "consistency": {"consistent": True},
    "breaking": {"breaking": False, "acknowledged": False},
    "materialization": {"jobId": "job-1", "inferred": 3},
}
DIFF = {"from": "ont-old", "to": "ont-new", "summary": {"addedTriples": 4}}


class PackTests(unittest.TestCase):
    def test_pass_pack_contains_gates_and_fingerprints(self):
        pack = evidence.build_pack(
            version=VERSION, against=AGAINST, proposal=PROPOSAL, mode="governed",
            gates=GATES, verdict="pass", actor="alice", reason="release", diff=DIFF,
        )
        self.assertEqual(pack["verdict"], "pass")
        self.assertEqual(pack["versionId"], "ont-new")
        self.assertEqual(pack["inputFingerprint"]["against"]["contentHash"], "hash-old")
        self.assertEqual(pack["inputFingerprint"]["version"]["contentHash"], "hash-new")
        self.assertEqual(pack["inputFingerprint"]["diff"]["sha256"],
                         evidence._sha256(DIFF))
        self.assertIn("shacl", pack["gates"])
        self.assertEqual(len(pack["sha256"]), 64)

    def test_fail_pack_keeps_gate_error(self):
        error = PortError(code="Conflict", message="SHACL validation failed",
                          provider="pyshacl", provider_code="E_ONTOLOGY_SHACL_FAILED",
                          details={"violations": [{"focusNode": "urn:x"}]})
        pack = evidence.build_pack(
            version=VERSION, against=None, proposal=None, mode="direct_publish",
            gates={"shacl": {"conforms": False}}, verdict="fail", actor="alice",
            reason="import", diff=DIFF, error=error,
        )
        self.assertEqual(pack["verdict"], "fail")
        self.assertEqual(pack["error"]["providerCode"], "E_ONTOLOGY_SHACL_FAILED")
        self.assertEqual(pack["error"]["details"]["violations"][0]["focusNode"], "urn:x")

    def test_bad_verdict_is_rejected(self):
        with self.assertRaises(ValueError):
            evidence.build_pack(version=VERSION, against=None, proposal=None, mode="x",
                                gates={}, verdict="maybe", actor="a", reason=None)


class StorageTests(unittest.TestCase):
    def test_materialize_and_checksum_roundtrip(self):
        pack = evidence.build_pack(version=VERSION, against=AGAINST, proposal=None,
                                   mode="governed", gates=GATES, verdict="pass",
                                   actor="alice", reason=None, diff=DIFF)
        with tempfile.TemporaryDirectory() as tmp:
            path = evidence.materialize(tmp, pack)
            self.assertTrue(path.exists())
            self.assertEqual(path.parent.name, "ont-new")
            body = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(body["evidenceId"], pack["evidenceId"])
            evidence.check_download(body)
            body["gates"]["shacl"]["conforms"] = True
            body["tampered"] = True
            with self.assertRaises(PortError) as ctx:
                evidence.check_download(body)
            self.assertEqual(ctx.exception.provider_code, "E_ONTOLOGY_EVIDENCE_CORRUPT")


class FakeMetadata:
    def __init__(self, rows=None):
        self.inserted: list[tuple] = []
        self.deleted: list[tuple] = []
        self.rows = rows or []

    def query(self, sql, params=()):
        if "INSERT INTO platform.ontology_evidence" in sql:
            self.inserted.append(params)
            return [{"evidence_id": params[0]}]
        if "FROM platform.ontology_evidence" in sql:
            return self.rows
        return []

    def execute(self, sql, params=()):
        self.deleted.append(params)
        return 1


def _pack():
    return evidence.build_pack(version=VERSION, against=None, proposal=None,
                               mode="direct_publish", gates=GATES, verdict="fail",
                               actor="alice", reason="gate", diff=DIFF,
                               error=PortError(code="Conflict", message="boom",
                                                provider="platform",
                                                provider_code="E_ONTOLOGY_BREAKING"))


class PublishHookTests(unittest.TestCase):
    def test_hook_records_pack_without_raising(self):
        registry = SimpleNamespace(_meta=FakeMetadata(), _validator=None,
                                   _graph=SimpleNamespace(), _reasoner=None, _abox_graphs=())
        result = OntologyRegistry._publish_evidence(
            registry, version_id="ont-new", row=VERSION, proposal=PROPOSAL,
            mode="governed", gates=GATES, verdict="pass", actor="alice",
            reason="release", diff=DIFF,
        )
        self.assertEqual(result["verdict"], "pass")
        self.assertEqual(len(registry._meta.inserted), 1)
        self.assertEqual(result["downloadUrl"],
                         f"/ontology/evidence/{result['evidenceId']}/download")

    def test_hook_swallows_storage_failure(self):
        class BoomMeta(FakeMetadata):
            def query(self, sql, params=()):
                raise RuntimeError("db down")

        registry = SimpleNamespace(_meta=BoomMeta(), _validator=None)
        result = OntologyRegistry._publish_evidence(
            registry, version_id="ont-new", row=VERSION, proposal=None,
            mode="governed", gates=GATES, verdict="pass", actor="alice",
            reason=None, diff=DIFF,
        )
        self.assertIn("error", result)
        self.assertEqual(result["verdict"], "pass")
        self.assertNotIn("evidenceId", result)


class EvidenceRouteTests(unittest.TestCase):
    def test_list_and_download(self):
        pack = _pack()
        row = {"evidence_id": pack["evidenceId"], "version_id": "ont-new",
               "proposal_id": None, "verdict": "fail", "path": None,
               "sha256": pack["sha256"], "created_at": "2026-01-01T00:00:00+00:00",
               "payload": pack}
        with tempfile.TemporaryDirectory() as tmp:
            runtime = SimpleNamespace(
                metadata=FakeMetadata(rows=[row]), graph=SimpleNamespace(),
                ontology=SimpleNamespace(), bundle=object(),
                config=SimpleNamespace(storage=SimpleNamespace(root=tmp)),
            )
            client = TestClient(api_module.create_app(runtime, []))
            with client:
                listing = client.get("/ontology/evidence", params={"versionId": "ont-new"})
                self.assertEqual(listing.status_code, 200)
                self.assertEqual(listing.json()["count"], 1)
                self.assertEqual(listing.json()["items"][0]["verdict"], "fail")

                download = client.get(f"/ontology/evidence/{pack['evidenceId']}/download")
                self.assertEqual(download.status_code, 200)
                self.assertIn("attachment; filename=", download.headers["content-disposition"])
                self.assertEqual(download.headers["x-evidence-sha256"], pack["sha256"])
                written = Path(tmp) / "evidence" / "ont-new" / f"{pack['evidenceId']}.json"
                self.assertTrue(written.exists())
                self.assertEqual(json.loads(download.text)["verdict"], "fail")

    def test_missing_pack_is_404(self):
        runtime = SimpleNamespace(
            metadata=FakeMetadata(rows=[]), graph=SimpleNamespace(),
            ontology=SimpleNamespace(), bundle=object(),
            config=SimpleNamespace(storage=SimpleNamespace(root=tempfile.gettempdir())),
        )
        client = TestClient(api_module.create_app(runtime, []))
        with client:
            response = client.get("/ontology/evidence/ev-missing/download")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["providerCode"],
                         evidence.E_EVIDENCE_NOT_FOUND)


if __name__ == "__main__":
    unittest.main(verbosity=2)
