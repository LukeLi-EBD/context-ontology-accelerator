"""The write path reaches ``MetricIndexPort`` from synchronous handlers."""

from __future__ import annotations

import asyncio

from coa_metrics.metric_index import MetricIndexSync
from coa_metrics.neptune_client import MetricAiContext, MetricDefinition, MetricDialect


class FakePort:
    def __init__(self) -> None:
        self.indexed: list[tuple[str, str, str]] = []
        self.removed: list[tuple[str, str]] = []

    async def index(self, record: object) -> None:
        self.indexed.append((record.namespace, record.name, record.text))  # type: ignore[attr-defined]

    async def remove(self, namespace: str, name: str) -> None:
        self.removed.append((namespace, name))


def _metric() -> MetricDefinition:
    return MetricDefinition(
        name="revenue",
        description="Total revenue",
        expression_dialects=[MetricDialect(dialect="trino", expression="SUM(x)")],
        data_source_id="ds-1",
        source_table="orders",
        defined_by="steward@example.com",
        effective_from="2026-05-01",
        ai_context=MetricAiContext(synonyms=["sales"], instructions="Use for topline", examples=[]),
    )


def test_embed_metric_indexes_the_same_projection_as_before() -> None:
    port = FakePort()

    MetricIndexSync(port).embed_metric("demo", _metric())

    namespace, name, text = port.indexed[0]
    assert (namespace, name) == ("demo", "revenue")
    assert "revenue" in text
    assert "Total revenue" in text
    assert "sales" in text
    assert "Use for topline" in text


def test_delete_metric_embedding_removes_the_record() -> None:
    port = FakePort()

    MetricIndexSync(port).delete_metric_embedding("demo", "revenue")

    assert port.removed == [("demo", "revenue")]


def test_calls_from_inside_an_event_loop_still_complete() -> None:
    port = FakePort()

    async def handler() -> None:
        MetricIndexSync(port).delete_metric_embedding("demo", "revenue")

    asyncio.run(handler())

    assert port.removed == [("demo", "revenue")]
