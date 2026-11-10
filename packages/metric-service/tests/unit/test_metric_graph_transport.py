"""The metric graph client talks to whichever transport the catalog resolved."""

from __future__ import annotations

from typing import Any

import pytest

from coa_metrics.neptune_client import MetricDefinition, MetricDialect, MetricNeptuneClient

pytestmark = pytest.mark.unit


class RecordingTransport:
    def __init__(self) -> None:
        self.queries: list[str] = []
        self.updates: list[str] = []

    def query(self, sparql: str) -> dict[str, Any]:
        self.queries.append(sparql)
        return {"results": {"bindings": []}}

    def update(self, sparql: str) -> None:
        self.updates.append(sparql)


def _metric() -> MetricDefinition:
    return MetricDefinition(
        name="revenue",
        description="Test metric",
        expression_dialects=[MetricDialect(dialect="trino", expression="SUM(x)")],
        data_source_id="ds-1",
        source_table="orders",
        defined_by="steward@example.com",
        effective_from="2026-05-01",
    )


def test_reads_go_through_the_injected_transport() -> None:
    transport = RecordingTransport()
    client = MetricNeptuneClient(transport=transport)

    assert client.get_metrics_bulk("demo") == []
    assert len(transport.queries) == 1
    assert transport.queries[0].lstrip().startswith("SELECT")


def test_writes_go_through_the_injected_transport() -> None:
    transport = RecordingTransport()
    client = MetricNeptuneClient(transport=transport)

    client.update_metric("demo", "revenue", _metric())

    assert len(transport.updates) == 1
    assert "INSERT" in transport.updates[0]
    assert transport.queries == []
