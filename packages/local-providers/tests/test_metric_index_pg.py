"""Contract tests for the PostgreSQL metric index."""

from __future__ import annotations

import asyncio

import pytest
from coa_ports import MetricIndexPort, MetricRecord, PortError
from coa_local_providers.metric_index_pg import PgMetricIndex


class _FakeMeta:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows
        self.params: tuple[object, ...] = ()
        self.closed = False

    def query(self, sql: str, params: tuple[object, ...] = ()) -> list[dict[str, object]]:
        self.params = params
        return self.rows

    def close(self) -> None:
        self.closed = True


def _client(rows: list[dict[str, object]] | None = None) -> PgMetricIndex:
    client = PgMetricIndex.__new__(PgMetricIndex)
    client._meta = _FakeMeta(rows or [])
    return client


def test_implements_the_port() -> None:
    assert isinstance(_client(), MetricIndexPort)


def test_index_rejects_incomplete_records() -> None:
    client = _client()
    with pytest.raises(PortError):
        asyncio.run(client.index(MetricRecord(namespace="", name="m", text="t")))


def test_index_and_remove_are_no_ops_for_the_system_of_record() -> None:
    client = _client()
    asyncio.run(client.index(MetricRecord(namespace="ns", name="m", text="t")))
    asyncio.run(client.remove("ns", "m"))


def test_search_projects_rows_and_passes_top_k() -> None:
    client = _client(
        [
            {
                "metric_id": "FIN-001",
                "name_zh": "存款余额",
                "display_name": "Deposit balance",
                "definition": "",
                "formula_text": "sum(balance)",
                "score": 0.42,
            }
        ]
    )
    hits = asyncio.run(client.search("ns", "存款余额", top_k=3))

    assert len(hits) == 1
    assert hits[0].name == "FIN-001"
    assert hits[0].namespace == "ns"
    assert "Deposit balance" in hits[0].text
    assert hits[0].score == pytest.approx(0.42)
    assert client._meta.params[-1] == 3


def test_search_without_query_does_not_touch_the_database() -> None:
    client = _client()

    assert asyncio.run(client.search("ns", "  ")) == ()
