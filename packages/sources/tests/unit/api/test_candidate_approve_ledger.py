# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Approval must write the platform ledger and the A-Box projection together.

These tests pin the all-or-nothing contract of ``handle_approve_candidate``:
no ledger -> no approval, ledger failure -> nothing written, projection failure
-> the row this request created is retracted.
"""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("SOURCES_TABLE", "test-sources")
os.environ.setdefault("NAMESPACES_TABLE", "test-namespaces")
os.environ.setdefault("DOCUMENTS_TABLE", "test-documents")
os.environ.setdefault("FACT_CANDIDATES_TABLE", "test-candidates")
os.environ.setdefault("FACTS_TABLE", "test-facts")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

import coa_sources.api.sources_handler  # noqa: F401,E402  (circular import order)
import coa_sources.api.candidate_routes as routes  # noqa: E402

_NAMESPACE_ID = "550e8400-e29b-41d4-a716-446655440000"
_CANDIDATE_ID = "7337c612-9cd4-46a5-9daf-31639e3fd38d"


def _parse(result):
    return result["statusCode"], json.loads(result["body"]) if result.get("body") else {}


def _event():
    return {
        "httpMethod": "POST",
        "pathParameters": {"namespaceId": _NAMESPACE_ID, "candidateId": _CANDIDATE_ID},
        "body": json.dumps({"actor": "reviewer-1"}),
    }


@pytest.fixture
def candidate():
    return {
        "candidateId": _CANDIDATE_ID,
        "namespaceId": _NAMESPACE_ID,
        "status": "PENDING",
        "subject": "合同台账",
        "predicate": "属于",
        "object": "档案资料",
        "documentId": "322e9b93-1f9e-4836-a141-4734cf551707",
        "chunkId": "f0b7ed6a-8afd-498b-900d-81067c4f2df9",
    }


@pytest.fixture
def stores(candidate):
    fake_store = MagicMock()
    fake_store.pk.return_value = f"NS#{_NAMESPACE_ID}"
    fake_store.get_candidate.return_value = candidate
    with patch.object(routes, "store", fake_store), patch.object(routes, "_project") as project:
        yield fake_store, project


@pytest.fixture(autouse=True)
def reset_ledger():
    routes._LEDGER_RECORD = None
    routes._LEDGER_RETRACT = None
    with patch.dict(os.environ, {"NDB_GRAPH_URI_BASE": "https://coa.local/graph"}):
        yield
    routes._LEDGER_RECORD = None
    routes._LEDGER_RETRACT = None


def test_approve_without_ledger_fails_closed(stores):
    fake_store, project = stores
    status, body = _parse(routes.handle_approve_candidate(_event(), _NAMESPACE_ID, _CANDIDATE_ID))

    assert status == 503
    assert body["code"] == "fact_ledger_unavailable"
    fake_store.put_fact.assert_not_called()
    fake_store.update_candidate.assert_not_called()
    project.assert_not_called()


def test_ledger_failure_writes_nothing(stores):
    fake_store, project = stores

    def boom(**_):
        raise RuntimeError("ledger down")

    routes.install_fact_ledger(boom, MagicMock())
    status, body = _parse(routes.handle_approve_candidate(_event(), _NAMESPACE_ID, _CANDIDATE_ID))

    assert status == 502
    assert body["code"] == "fact_ledger_write_failed"
    fake_store.put_fact.assert_not_called()
    fake_store.update_candidate.assert_not_called()
    project.assert_not_called()


def test_projection_failure_retracts_the_new_row(stores):
    fake_store, project = stores
    retract = MagicMock()
    record = MagicMock(return_value={"factId": "fact-abc123", "duplicate": False})
    routes.install_fact_ledger(record, retract)

    def project_boom(*_):
        raise RuntimeError("oxigraph down")

    project.side_effect = project_boom
    status, body = _parse(routes.handle_approve_candidate(_event(), _NAMESPACE_ID, _CANDIDATE_ID))

    assert status == 500
    assert body["compensated"] is True
    retract.assert_called_once()
    assert retract.call_args.args[0] == "fact-abc123"
    fake_store.update_candidate.assert_not_called()


def test_duplicate_row_is_not_retracted(stores):
    fake_store, project = stores
    retract = MagicMock()
    record = MagicMock(return_value={"factId": "fact-abc123", "duplicate": True})
    routes.install_fact_ledger(record, retract)
    fake_store.put_fact.side_effect = RuntimeError("dynamo stuck")

    status, body = _parse(routes.handle_approve_candidate(_event(), _NAMESPACE_ID, _CANDIDATE_ID))

    assert status == 500
    assert body["compensated"] is False
    retract.assert_not_called()


def test_happy_path_uses_ledger_fact_id(stores):
    fake_store, project = stores
    record = MagicMock(return_value={"factId": "fact-abc123", "duplicate": False})
    retract = MagicMock()
    routes.install_fact_ledger(record, retract)

    status, body = _parse(routes.handle_approve_candidate(_event(), _NAMESPACE_ID, _CANDIDATE_ID))

    assert status == 200
    assert body["factId"] == "fact-abc123"
    fields = record.call_args.kwargs
    assert fields["subject"].startswith("urn:coa:entity:")
    assert fields["predicate"].startswith("urn:coa:predicate:")
    assert fields["object_kind"] == "literal"
    assert fields["graph"].endswith("/urn%3Acoa%3Aabox%3Adocuments")
    assert fields["candidate_id"] == _CANDIDATE_ID
    assert fields["source_document_id"] == "322e9b93-1f9e-4836-a141-4734cf551707"
    assert fields["actor"] == "reviewer-1"

    project.assert_called_once()
    put = fake_store.put_fact.call_args.args[0]
    assert put["SK"] == "FACT#fact-abc123"
    update = fake_store.update_candidate.call_args
    assert update.args[2]["status"] == "APPROVED"
    assert update.args[2]["factId"] == "fact-abc123"
    retract.assert_not_called()
