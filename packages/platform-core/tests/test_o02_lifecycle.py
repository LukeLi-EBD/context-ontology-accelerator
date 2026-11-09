"""O-02 T-Box lifecycle state machine tests.

Pure unit tests: fakes only, no postgres/oxigraph/reasoner. Run with:
  docker run --rm --entrypoint python -e PYTHONPATH=/hostsrc \
    -v <repo>/src:/hostsrc:ro -v <repo>/tests:/hosttests:ro \
    agent-platform:0.1-s5 /hosttests/test_o02_lifecycle.py
"""

from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient

sys.path.insert(0, "/hostsrc")
sys.path.insert(0, "../src")

import platform_core.api as api_module
from platform_core import ontology_lifecycle as lc
from platform_core.errors import PortError


def _conflict(code: str, message: str = "illegal transition") -> PortError:
    return PortError(
        code="Conflict", message=message, provider="platform", provider_code=code,
    )


class StateMachineTests(unittest.TestCase):
    def test_all_four_documented_transitions_are_allowed(self):
        edges = [
            ("proposal", "proposed", "review"),
            ("proposal", "review", "approved"),
            ("proposal", "approved", "published"),
            ("proposal", "published", "superseded"),
        ]
        for kind, src, dst in edges:
            with self.subTest(edge=f"{src}->{dst}"):
                lc.validate_transition(kind, src, dst)

    def test_illegal_transitions_are_rejected(self):
        illegal = [
            ("proposal", "published", "review"),
            ("proposal", "approved", "proposed"),
            ("proposal", "review", "published"),
            ("proposal", "superseded", "approved"),
            ("version", "published", "approved"),
            ("version", "superseded", "review"),
            ("version", "rejected", "published"),
        ]
        for kind, src, dst in illegal:
            with self.subTest(edge=f"{src}->{dst}"):
                with self.assertRaises(PortError) as ctx:
                    lc.validate_transition(kind, src, dst)
                self.assertEqual(ctx.exception.code, "Conflict")
                self.assertEqual(ctx.exception.provider_code, lc.E_LIFECYCLE_INVALID)
                self.assertEqual(ctx.exception.details["from"], src)
                self.assertEqual(ctx.exception.details["to"], dst)

    def test_unknown_entity_kind_is_invalid_argument(self):
        with self.assertRaises(PortError) as ctx:
            lc.validate_transition("metric", "proposed", "approved")
        self.assertEqual(ctx.exception.code, "InvalidArgument")
        self.assertEqual(ctx.exception.provider_code, lc.E_LIFECYCLE_INVALID)

    def test_allowed_targets_matches_declared_graph(self):
        self.assertEqual(lc.allowed_targets("proposal", "proposed"), ("review", "approved", "rejected"))
        self.assertEqual(lc.allowed_targets("proposal", "published"), ("superseded",))
        self.assertEqual(lc.allowed_targets("proposal", "nope"), ())


class FakeOntology:
    def __init__(self) -> None:
        self.versions = {
            "ont-a": {"id": "ont-a", "versionId": "ont-a", "semver": "1.0.0",
                      "status": "published", "graph": "urn:g:a", "tripleCount": 5},
            "ont-b": {"id": "ont-b", "versionId": "ont-b", "semver": "2.0.0",
                      "status": "review", "graph": "urn:g:b", "tripleCount": 7},
        }
        self.transition_items = {
            "p-1": [
                {"seq": 1, "entityKind": "proposal", "entityId": "p-1",
                 "versionId": "ont-b", "proposalId": "p-1", "from": None,
                 "to": "proposed", "actor": "alice", "reason": "submit",
                 "at": "2026-01-01T00:00:00+00:00", "payload": {}},
                {"seq": 2, "entityKind": "proposal", "entityId": "p-1",
                 "versionId": "ont-b", "proposalId": "p-1", "from": "proposed",
                 "to": "review", "actor": "bob", "reason": "start review",
                 "at": "2026-01-02T00:00:00+00:00", "payload": {}},
            ],
        }
        self.review_error: PortError | None = None
        self.review_calls: list[dict] = []

    def current(self):
        return {"versionId": "ont-a"}

    def list_versions(self):
        return list(self.versions.values())

    def get(self, version_id):
        return self.versions[version_id]

    def diff(self, from_id, to_id):
        return {"summary": {"addedTriples": 2, "removedTriples": 0},
                "breaking": False, "breakingItems": []}

    def review(self, proposal_id, actor="operator", reason=None):
        self.review_calls.append({"proposalId": proposal_id, "actor": actor, "reason": reason})
        if self.review_error:
            raise self.review_error
        return {"proposalId": proposal_id, "versionId": "ont-b", "status": "review",
                "reviewedBy": actor, "reason": reason, "unchanged": False}

    def transitions(self, proposal_id=None, version_id=None, limit=200):
        items = list(self.transition_items.get(proposal_id or "", []))
        if version_id and not proposal_id:
            items = [item for group in self.transition_items.values() for item in group
                     if item["versionId"] == version_id]
        return {"items": items[:limit], "count": len(items[:limit]),
                "empty": not items, "emptyReason": None if items else "无流转记录",
                "readOnly": True}


class FakeGraph:
    def export_graph(self, graph_iri):
        return b"<urn:s> <urn:p> <urn:o> ."

    def query(self, sparql):
        return {"kind": "select", "variables": [], "bindings": []}


class FakeMetadata:
    def query(self, sql, params=()):
        return []


def _client(ontology=None):
    ontology = ontology or FakeOntology()
    runtime = SimpleNamespace(metadata=FakeMetadata(), graph=FakeGraph(),
                              ontology=ontology, bundle=object())
    return TestClient(api_module.create_app(runtime, [])), ontology


def _error_code(response) -> str:
    return response.json()["error"]["providerCode"]


class ReviewRouteTests(unittest.TestCase):
    def test_review_requires_actor_and_reason(self):
        client, ontology = _client()
        with client:
            response = client.post("/governance/proposals/p-1/review",
                                   json={"reason": "checking"})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(_error_code(response), api_module.ACTOR_REQUIRED)
            response = client.post("/governance/proposals/p-1/review",
                                   json={"actor": "alice"})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(_error_code(response), api_module.REASON_REQUIRED)
        self.assertEqual(ontology.review_calls, [])

    def test_review_forwarding_and_transition_read(self):
        client, ontology = _client()
        with client:
            response = client.post("/governance/proposals/p-1/review",
                                   json={"actor": "bob", "reason": "ready for review"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "review")
            self.assertEqual(ontology.review_calls[0]["actor"], "bob")

            response = client.get("/governance/proposals/p-1/transitions")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["count"], 2)
            self.assertEqual(response.json()["items"][1]["to"], "review")

            response = client.get("/governance/versions/ont-b/transitions")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["count"], 2)

    def test_illegal_review_is_conflict(self):
        ontology = FakeOntology()
        ontology.review_error = _conflict(lc.E_LIFECYCLE_INVALID,
                                          "illegal proposal transition: published -> review")
        client, _ = _client(ontology)
        with client:
            response = client.post("/governance/proposals/p-1/review",
                                   json={"actor": "bob", "reason": "retry"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(_error_code(response), lc.E_LIFECYCLE_INVALID)

    def test_flow_endpoint_empty_state_is_explicit(self):
        client, _ = _client()
        with client:
            response = client.get("/health/ontology-diff/flow", params={"versionId": "ont-z"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["empty"])
        self.assertEqual(payload["count"], 0)
        self.assertIn("尚无流转记录", payload["emptyReason"])
        self.assertTrue(payload["readOnly"])

    def test_diff_payload_carries_lifecycle_block(self):
        client, _ = _client()
        with client:
            response = client.get("/health/ontology-diff",
                                  params={"from": "ont-a", "to": "ont-b"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("lifecycle", payload)
        self.assertTrue(payload["lifecycle"]["empty"])
        self.assertEqual(payload["lifecycle"]["items"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
