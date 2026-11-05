"""Governance console API tests.

Pure unit tests: the ontology/metadata ports are fakes, so no postgres,
oxigraph, reasoner or bundle directory is required. Run them with:
  docker run --rm --entrypoint python -e PYTHONPATH=/hostsrc \
    -v <repo>/src:/hostsrc:ro -v <repo>/tests:/hosttests:ro \
    agent-platform:0.1-s5 /hosttests/test_governance_api.py
"""

from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient

sys.path.insert(0, "/hostsrc")
sys.path.insert(0, "../src")

import platform_core.api as api_module
from platform_core.errors import PortError


def _port(code: str, provider_code: str, message: str = "gate failed") -> PortError:
    return PortError(
        code=code,
        message=message,
        provider="platform",
        provider_code=provider_code,
        details={"gate": provider_code},
    )


class FakeOntology:
    def __init__(self) -> None:
        self.versions = {
            "ont-current": {
                "id": "ont-current", "semver": "2.0.0", "status": "published",
                "graph": "urn:g:current", "tripleCount": 10,
            },
            "ont-b": {
                "id": "ont-b", "semver": "3.0.0", "status": "draft",
                "graph": "urn:g:b", "tripleCount": 12,
            },
            "ont-c": {
                "id": "ont-c", "semver": "1.0.0", "status": "superseded",
                "graph": "urn:g:c", "tripleCount": 8,
            },
        }
        self.proposals = {
            "p-approved": {
                "proposalId": "p-approved", "versionId": "ont-b", "status": "approved",
                "changeSummary": "add class", "breaking": False,
                "acknowledgedBreaking": False, "againstVersion": "ont-current",
                "diff": {"summary": {"addedTriples": 3, "removedTriples": 0}},
                "impact": {"addedTriples": 3, "removedTriples": 0, "breakingItems": 0},
            },
            "p-proposed": {
                "proposalId": "p-proposed", "versionId": "ont-b", "status": "proposed",
                "changeSummary": "unapproved", "breaking": False,
                "acknowledgedBreaking": False, "againstVersion": "ont-current",
                "diff": {"summary": {"addedTriples": 4}}, "impact": {"addedTriples": 4},
            },
        }
        self.events_list = [
            {"eventId": 1, "versionId": "ont-current", "proposalId": None,
             "action": "published", "actor": "alice", "reason": "seed",
             "payload": {}, "createdAt": "2026-01-01T00:00:00+00:00"},
            {"eventId": 2, "versionId": "ont-b", "proposalId": "p-approved",
             "action": "approved", "actor": "bob", "reason": "ok",
             "payload": {}, "createdAt": "2026-01-02T00:00:00+00:00"},
            {"eventId": 3, "versionId": "ont-current", "proposalId": None,
             "action": "rolled_back", "actor": "carol", "reason": "rollback",
             "payload": {}, "createdAt": "2026-01-03T00:00:00+00:00"},
            {"eventId": 4, "versionId": "ont-c", "proposalId": None,
             "action": "superseded", "actor": "alice", "reason": "new version",
             "payload": {}, "createdAt": "2026-01-04T00:00:00+00:00"},
        ]
        self.pointer = {"versionId": "ont-current"}
        self.audit: list[dict] = []
        self.propose_calls: list[dict] = []
        self.publish_calls: list[dict] = []
        self.rollback_calls: list[dict] = []
        self.shacl_error: PortError | None = None
        self.consistency_error: PortError | None = None
        self.publish_error: PortError | None = None
        self.rollback_error: PortError | None = None

    # ---- reads ---------------------------------------------------------
    def current(self):
        return self.pointer

    def list_versions(self):
        return list(self.versions.values())

    def get(self, version_id):
        if version_id not in self.versions:
            raise _port("NotFound", "E_ONTOLOGY_VERSION_NOT_FOUND", f"unknown version: {version_id}")
        return self.versions[version_id]

    def graph_count(self, version_id):
        return self.versions[version_id]["tripleCount"]

    def diff(self, from_id, to_id):
        return {"summary": {"addedTriples": 3, "removedTriples": 0}, "breaking": False,
                "breakingItems": []}

    def list_proposals(self, version_id=None):
        items = [item for item in self.proposals.values()
                 if version_id is None or item["versionId"] == version_id]
        return {"items": items, "count": len(items)}

    def get_proposal(self, proposal_id):
        if proposal_id not in self.proposals:
            raise _port("NotFound", "E_ONTOLOGY_PROPOSAL_NOT_FOUND", f"unknown proposal: {proposal_id}")
        return self.proposals[proposal_id]

    def events(self, version_id=None, limit=200):
        items = [item for item in self.events_list
                 if version_id is None or item["versionId"] == version_id]
        return {"items": items[:limit], "count": len(items[:limit])}

    # ---- writes --------------------------------------------------------
    def propose(self, version_id, summary, actor="operator", against_version=None):
        self.propose_calls.append(
            {"versionId": version_id, "summary": summary, "actor": actor,
             "againstVersion": against_version}
        )
        proposal_id = f"p-{len(self.propose_calls)}"
        self.proposals[proposal_id] = {
            "proposalId": proposal_id, "versionId": version_id, "status": "proposed",
            "changeSummary": summary, "breaking": False,
            "acknowledgedBreaking": False, "againstVersion": against_version,
            "diff": {"summary": {"addedTriples": 2}}, "impact": {"addedTriples": 2},
        }
        self.versions[version_id]["status"] = "proposed"
        return {"proposalId": proposal_id, "versionId": version_id, "status": "proposed",
                "breaking": False, "diff": self.proposals[proposal_id]["diff"],
                "impact": self.proposals[proposal_id]["impact"]}

    def approve(self, proposal_id, actor="operator", reason=None):
        proposal = self.get_proposal(proposal_id)
        if proposal["status"] != "proposed":
            raise _port("Conflict", "E_ONTOLOGY_PROPOSAL_STATUS",
                        f"proposal is {proposal['status']}")
        proposal["status"] = "approved"
        self.versions[proposal["versionId"]]["status"] = "approved"
        self.audit.append({"proposalId": proposal_id, "action": "approved",
                           "actor": actor, "reason": reason})
        return {"proposalId": proposal_id, "versionId": proposal["versionId"],
                "status": "approved", "approvedBy": actor, "reason": reason}

    def publish(self, version_id, proposal_id=None, acknowledge_breaking=False,
                actor="operator", reason=None, activate_existing=False):
        self.publish_calls.append(
            {"versionId": version_id, "proposalId": proposal_id,
             "acknowledgeBreaking": acknowledge_breaking, "actor": actor,
             "reason": reason, "publishExisting": activate_existing}
        )
        if self.publish_error:
            raise self.publish_error
        if proposal_id:
            proposal = self.get_proposal(proposal_id)
            if proposal["status"] != "approved":
                raise _port("Conflict", "E_ONTOLOGY_PROPOSAL_NOT_APPROVED",
                            f"proposal is {proposal['status']}; approval required")
        version = self.get(version_id)
        self.pointer = {"versionId": version_id}
        version["status"] = "published"
        return {
            "versionId": version_id, "status": "published", "previous": "ont-current",
            "gates": {
                "shacl": {"conforms": True},
                "consistency": {"consistent": True, "profile": "abox"},
                "breaking": {"breaking": False, "acknowledged": acknowledge_breaking},
            },
        }

    def rollback_to(self, version_id, actor="operator", reason=None):
        self.rollback_calls.append({"mode": "to", "versionId": version_id,
                                    "actor": actor, "reason": reason})
        if self.rollback_error:
            raise self.rollback_error
        version = self.get(version_id)
        self.pointer = {"versionId": version_id}
        return {"versionId": version_id, "status": version["status"],
                "triples": version["tripleCount"], "publishedBy": actor}

    def rollback(self, version_id):
        self.rollback_calls.append({"mode": "new", "versionId": version_id})
        if self.rollback_error:
            raise self.rollback_error
        new_id = f"{version_id}-rb1"
        self.versions[new_id] = {
            "id": new_id, "semver": "2.1.0", "status": "published",
            "graph": f"urn:g:{new_id}", "tripleCount": self.versions[version_id]["tripleCount"],
        }
        previous = self.pointer
        self.pointer = {"versionId": new_id}
        return {"id": new_id, "rollbackOf": version_id, "status": "published",
                "publishedBy": "operator", "previous": (previous or {}).get("versionId")}

    # ---- gate helpers reused by the dry-run ----------------------------
    def _gate_shacl(self, nt, graph):
        if self.shacl_error:
            raise self.shacl_error
        return {"conforms": True}

    def _gate_consistency(self, nt):
        if self.consistency_error:
            raise self.consistency_error
        return {"consistent": True, "profile": "abox"}

    def _append_event(self, tx, version_id, proposal_id, action, actor, reason, payload):
        self.audit.append({"versionId": version_id, "proposalId": proposal_id,
                           "action": action, "actor": actor, "reason": reason,
                           "payload": payload})


class FakeGraph:
    def export_graph(self, graph_iri):
        return b"<urn:s> <urn:p> <urn:o> ."

    def query(self, sparql):
        return {"kind": "select", "variables": [], "bindings": []}


class FakeTx:
    def __init__(self, ontology):
        self.ontology = ontology
        self.statements = []

    def execute(self, sql, params=()):
        self.statements.append((sql, params))
        if "SET status = 'rejected'" in sql:
            version_id = params[0]
            if version_id in self.ontology.versions:
                self.ontology.versions[version_id]["status"] = "rejected"

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeMetadata:
    def __init__(self, ontology):
        self.ontology = ontology

    def tx(self):
        return FakeTx(self.ontology)

    def query(self, sql, params=()):
        return []


def _client(ontology=None):
    ontology = ontology or FakeOntology()
    runtime = SimpleNamespace(
        metadata=FakeMetadata(ontology),
        graph=FakeGraph(),
        ontology=ontology,
        bundle=object(),
    )
    return TestClient(api_module.create_app(runtime, [])), ontology


def _error_code(response) -> str:
    return response.json()["error"]["providerCode"]


class GovernanceConsoleTests(unittest.TestCase):
    def test_1_create_proposal_requires_actor(self):
        client, ontology = _client()
        with client:
            for actor in (None, "", "   "):
                body = {"versionId": "ont-b", "changeSummary": "add class"}
                if actor is not None:
                    body["actor"] = actor
                response = client.post("/governance/proposals", json=body)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(_error_code(response), api_module.ACTOR_REQUIRED)
        self.assertEqual(ontology.propose_calls, [])

    def test_2_create_proposal_forwards_actor_and_against(self):
        client, ontology = _client()
        with client:
            response = client.post("/governance/proposals", json={
                "actor": "alice", "versionId": "ont-b",
                "changeSummary": "add class", "againstVersion": "ont-current",
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["proposalId"], "p-1")
        self.assertEqual(ontology.propose_calls[0]["actor"], "alice")
        self.assertEqual(ontology.propose_calls[0]["againstVersion"], "ont-current")

    def test_3_approve_and_reject_require_actor_and_reason(self):
        client, ontology = _client()
        with client:
            for path in ("approve", "reject"):
                response = client.post(f"/governance/proposals/p-proposed/{path}",
                                       json={"reason": "looks fine"})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(_error_code(response), api_module.ACTOR_REQUIRED)
                response = client.post(f"/governance/proposals/p-proposed/{path}",
                                       json={"actor": "alice"})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(_error_code(response), api_module.REASON_REQUIRED)
        self.assertEqual(ontology.audit, [])

    def test_4_reject_marks_version_rejected_and_appends_audit(self):
        client, ontology = _client()
        with client:
            response = client.post("/governance/proposals/p-proposed/reject",
                                   json={"actor": "alice", "reason": "out of scope"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["versionStatus"], "rejected")
        self.assertEqual(ontology.versions["ont-b"]["status"], "rejected")
        event = ontology.audit[-1]
        self.assertEqual(event["action"], "rejected")
        self.assertEqual(event["actor"], "alice")
        self.assertEqual(event["reason"], "out of scope")

    def test_5_reject_published_proposal_is_conflict(self):
        client, _ = _client()
        with client:
            response = client.post("/governance/proposals/p-approved/reject",
                                   json={"actor": "alice", "reason": "too late"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(_error_code(response), "E_ONTOLOGY_PROPOSAL_STATUS")

    def test_6_publish_dry_run_lists_gates_without_writing(self):
        ontology = FakeOntology()
        ontology.versions["ont-b"]["status"] = "approved"
        client, _ = _client(ontology)
        with client:
            response = client.post("/governance/publish", json={
                "actor": "alice", "versionId": "ont-b", "proposalId": "p-approved",
                "dryRun": True,
            })
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["wouldPublish"])
        for gate in ("integrity", "breaking", "graph", "shacl", "consistency"):
            self.assertIn(gate, payload["gates"])
        self.assertEqual(payload["blockers"], [])
        self.assertEqual(ontology.publish_calls, [])

    def test_7_publish_dry_run_surfaces_gate_error_verbatim(self):
        ontology = FakeOntology()
        ontology.versions["ont-b"]["status"] = "approved"
        ontology.shacl_error = _port("PolicyRejected", "E_ONTOLOGY_SHACL_FAILED",
                                     "SHACL violation: missing label")
        client, _ = _client(ontology)
        with client:
            response = client.post("/governance/publish", json={
                "actor": "alice", "versionId": "ont-b", "proposalId": "p-approved",
                "dryRun": True,
            })
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["wouldPublish"])
        self.assertFalse(payload["gates"]["shacl"]["ok"])
        self.assertEqual(payload["gates"]["shacl"]["code"], "E_ONTOLOGY_SHACL_FAILED")
        self.assertEqual(payload["blockers"][0]["code"], "E_ONTOLOGY_SHACL_FAILED")
        self.assertEqual(ontology.publish_calls, [])

    def test_8_real_publish_requires_actor_and_version(self):
        client, _ = _client()
        with client:
            response = client.post("/governance/publish", json={"versionId": "ont-b"})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(_error_code(response), api_module.ACTOR_REQUIRED)
            response = client.post("/governance/publish", json={"actor": "alice"})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(_error_code(response), "E_ONTOLOGY_VERSION_REQUIRED")

    def test_9_publish_unapproved_proposal_is_rejected_with_code(self):
        client, _ = _client()
        with client:
            response = client.post("/governance/publish", json={
                "actor": "alice", "versionId": "ont-b", "proposalId": "p-proposed",
            })
        self.assertEqual(response.status_code, 409)
        self.assertEqual(_error_code(response), "E_ONTOLOGY_PROPOSAL_NOT_APPROVED")

    def test_10_publish_returns_gates(self):
        client, ontology = _client()
        with client:
            response = client.post("/governance/publish", json={
                "actor": "alice", "versionId": "ont-b", "proposalId": "p-approved",
            })
        self.assertEqual(response.status_code, 200)
        self.assertIn("shacl", response.json()["gates"])
        self.assertEqual(ontology.publish_calls[0]["actor"], "alice")

    def test_11_rollback_plan_shows_replaced_version(self):
        client, _ = _client()
        with client:
            response = client.get("/governance/rollback/plan?versionId=ont-c")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["target"]["id"], "ont-c")
        self.assertEqual(payload["replacedVersion"]["versionId"], "ont-current")
        self.assertTrue(payload["wouldChangePointer"])
        self.assertEqual(payload["targetTriples"], 8)

    def test_12_rollback_endpoints_require_actor_and_report_previous(self):
        client, ontology = _client()
        with client:
            response = client.post("/governance/rollback-to", json={"versionId": "ont-c"})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(_error_code(response), api_module.ACTOR_REQUIRED)
            response = client.post("/governance/rollback-to",
                                   json={"actor": "alice", "versionId": "ont-c"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["replacedVersionId"], "ont-current")
            self.assertEqual(ontology.rollback_calls[0]["mode"], "to")
            response = client.post("/governance/rollback",
                                   json={"actor": "bob", "versionId": "ont-c", "reason": "redo"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["replacedVersionId"], "ont-c")
            self.assertEqual(ontology.audit[-1]["action"], "rolled_back")

    def test_13_rollback_to_unknown_version_is_rejected(self):
        client, _ = _client()
        with client:
            response = client.post("/governance/rollback-to",
                                   json={"actor": "alice", "versionId": "ont-missing"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(_error_code(response), "E_ONTOLOGY_VERSION_NOT_FOUND")

    def test_14_events_filter_by_version_and_category(self):
        client, _ = _client()
        with client:
            response = client.get("/governance/events?versionId=ont-current")
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["count"], 2)
            self.assertEqual(payload["categories"]["published"], 1)
            self.assertEqual(payload["categories"]["rolled_back"], 1)
            self.assertEqual({item["versionId"] for item in payload["items"]}, {"ont-current"})
            response = client.get("/governance/events?action=superseded")
            self.assertEqual(response.json()["items"][0]["category"], "superseded")

    def test_15_proposal_list_annotates_version_status(self):
        client, _ = _client()
        with client:
            response = client.get("/governance/proposals?status=proposed")
        self.assertEqual(response.status_code, 200)
        item = response.json()["items"][0]
        self.assertEqual(item["proposalId"], "p-proposed")
        self.assertEqual(item["versionStatus"], "draft")

    def test_16_bundle_write_endpoints_require_actor(self):
        client, _ = _client()
        with client:
            response = client.post("/governance/bundle/export",
                                   json={"out": "/data/freeze", "tag": "t1"})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(_error_code(response), api_module.ACTOR_REQUIRED)
            response = client.post("/governance/bundle/import",
                                   json={"actor": "", "bundle": "/data/freeze/t1"})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(_error_code(response), api_module.ACTOR_REQUIRED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
