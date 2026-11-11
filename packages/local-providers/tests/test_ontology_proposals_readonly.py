"""P1-06: read-only platform proposals mapped into the engine item shape."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from coa_local_providers import ontology_proposals_pg as adapter

_ROW: dict[str, Any] = {
    "proposal_id": "prop-1",
    "version_id": "ont-abc",
    "against_version": "ont-000",
    "change_summary": "direct publish",
    "status": "published",
    "breaking": False,
    "acknowledged_breaking": False,
    "diff": {"from": "ont-000", "to": "ont-abc"},
    "impact": {"classes": 1},
    "created_by": "local-user",
    "created_at": datetime(2026, 11, 10, 11, 56, 13, tzinfo=UTC),
    "approved_by": "local-user",
    "approved_at": datetime(2026, 11, 10, 11, 56, 14, tzinfo=UTC),
    "published_at": datetime(2026, 11, 10, 11, 56, 15, tzinfo=UTC),
    "ontology_id": "ont-abc",
}


def test_map_row_keeps_missing_fields_explicit() -> None:
    item = adapter.map_row(_ROW, "demo")

    assert item["PK"] == "demo#PROPOSAL#prop-1"
    assert item["namespace"] is None  # PK prefix is an internal key, not data
    assert item["status"] == "accepted"  # platform "published"
    assert item["ontology_id"] == "ont-abc"
    assert item["updated_at"] == "2026-11-10T11:56:15+00:00"
    # Governance rows carry no namespace/type/source/artifact payload. Those
    # fields stay absent and are named, never invented.
    assert "namespace" in item["missing_fields"]
    assert "proposal_type" in item["missing_fields"]
    assert "source_type" in item["missing_fields"]
    assert "ontology_turtle" in item["missing_fields"]
    assert "r2rml_turtle" in item["missing_fields"]
    assert "matches" in item["missing_fields"]
    assert "ontology_turtle" not in item
    assert "proposal_type" not in item


def test_map_row_reports_a_missing_ontology_id() -> None:
    item = adapter.map_row({**_ROW, "ontology_id": None}, "demo")

    assert item["ontology_id"] is None
    assert "ontology_id" in item["missing_fields"]


def test_dsn_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COA_ONTOLOGY_PROPOSALS_PG_DSN", raising=False)
    monkeypatch.delenv("PLATFORM__DATABASE__URL", raising=False)

    with pytest.raises(RuntimeError, match="COA_ONTOLOGY_PROPOSALS_PG_DSN is required"):
        adapter.proposals_dsn()


def test_dsn_falls_back_to_platform_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COA_ONTOLOGY_PROPOSALS_PG_DSN", raising=False)
    monkeypatch.setenv("PLATFORM__DATABASE__URL", "postgresql://x/serve_local")

    assert adapter.proposals_dsn() == "postgresql://x/serve_local"


def _install_rows(monkeypatch: pytest.MonkeyPatch, rows: list[dict[str, Any]]) -> None:
    monkeypatch.setenv("COA_ONTOLOGY_PROPOSALS_PG_DSN", "postgresql://x/serve_local")
    monkeypatch.setattr(adapter, "_rows", lambda dsn, sql, params=(): list(rows))


def test_list_proposals_filters_on_mapped_values(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_rows(monkeypatch, [_ROW])

    assert [i["proposal_id"] for i in adapter.list_proposals()] == ["prop-1"]
    assert adapter.list_proposals(status="accepted")[0]["proposal_id"] == "prop-1"
    assert adapter.list_proposals(status="pending") == []
    assert adapter.list_proposals(ontology_id="ont-abc")[0]["proposal_id"] == "prop-1"
    assert adapter.list_proposals(ontology_id="ont-other") == []
    # Not a platform concept: a type filter matches nothing instead of guessing.
    assert adapter.list_proposals(proposal_type="INDUCED") == []
    assert adapter.list_proposals(source_type="UNSTRUCTURED") == []
    assert len(adapter.list_proposals(source_type="STRUCTURED")) == 1
    assert adapter.list_proposals(limit=0) == []


def test_get_proposal_by_id_returns_none_for_unknown_id(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_rows(monkeypatch, [])

    assert adapter.get_proposal_by_id("prop-unknown", namespace="demo") is None


def test_get_proposal_by_id_returns_the_mapped_item(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_rows(monkeypatch, [_ROW])

    item = adapter.get_proposal_by_id("prop-1", namespace="demo")

    assert item is not None
    assert item["proposal_id"] == "prop-1"
    assert item["status"] == "accepted"
