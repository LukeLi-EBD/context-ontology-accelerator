# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""A NOT_ANSWERABLE_RANGE row is a final Tier-2 answer; NOT_ANSWERABLE_FIELD and NOT_ANSWERABLE_CONCEPT rows are final only without documents."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from coa_serve.models import InvokeRequest
from coa_serve.tier2.strategy import (
    NOT_ANSWERABLE_CONCEPT,
    NOT_ANSWERABLE_FIELD,
    NOT_ANSWERABLE_RANGE,
    StrategyContext,
    StrategyOption,
    StrategyResult,
    StructuredQueryTier,
    is_not_answerable_result,
    not_answerable_kind,
)
from coa_serve.trace import TraceCollector

from .test_orchestrator import _make_orchestrator, _registry_with_composition

pytestmark = pytest.mark.unit


REFUSAL_SQL = "SELECT 'NOT_ANSWERABLE_FIELD: no cost field for service job' AS answer"


def _result(rows, confidence=0.1, sql=REFUSAL_SQL, strategy=StrategyOption.NL_TO_SQL):
    return StrategyResult(
        sql=sql,
        rows=rows,
        columns=list(rows[0]) if rows and isinstance(rows[0], dict) else [],
        confidence=confidence,
        strategy_name=strategy,
        trace_steps=[],
        row_count=len(rows),
        truncated=False,
        retrieved_tables=["plan"],
        expanded_tables=["plan"],
    )


@pytest.mark.parametrize(
    "rows, expected",
    [
        (
            [{"answer": "NOT_ANSWERABLE_RANGE: March 2031 is outside the data; the plan covers 2026-01 to 2029-12"}],
            True,
        ),
        ([{"answer": "  NOT_ANSWERABLE_FIELD: no cost field for service job"}], True),
        ([{"answer": "NOT_ANSWERABLE_CONCEPT: what does party mean?"}], True),
        ([{"answer": "NOT_ANSWERABLE: the old, kind-less refusal"}], True),
        ([{"ANSWER": "NOT_ANSWERABLE_RANGE: engines may upper-case the alias"}], True),
        ([["NOT_ANSWERABLE_RANGE: positional row"]], True),
        ([{"msg": "NOT_ANSWERABLE_RANGE: not the answer column"}], False),
        ([{"answer": "NOT_ANSWERABLE_RANGE: x", "other": 1}], False),
        ([{"answer": "not_answerable_range: wrong case"}], False),
        ([{"answer": "The note said NOT_ANSWERABLE_RANGE: in the middle"}], False),
        ([{"answer": 42}], False),
        ([{"count": 0}], False),
        ([], False),
    ],
)
def test_detects_the_sentinel_row(rows, expected):
    assert is_not_answerable_result(_result(rows)) is expected


def test_more_than_one_row_is_not_a_refusal():
    rows = [{"answer": "NOT_ANSWERABLE_RANGE: first row"}, {"answer": "42"}]
    assert is_not_answerable_result(_result(rows)) is False


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT answer FROM notes",
        "SELECT answer FROM notes WHERE id = 'NOT_ANSWERABLE_RANGE: x'",
        "SELECT 'NOT_ANSWERABLE_RANGE: x' AS answer FROM notes",
        "SELECT 'ok' AS answer",
        "",
    ],
)
def test_real_query_returning_a_prefixed_value_is_not_a_refusal(sql):
    # A data value that merely starts with the prefix must not skip the confidence floor.
    rows = [{"answer": "NOT_ANSWERABLE_RANGE: stored in a notes table"}]
    assert is_not_answerable_result(_result(rows, sql=sql)) is False


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 'NOT_ANSWERABLE_RANGE: x' AS answer;",
        "select 'NOT_ANSWERABLE_RANGE: it''s outside the data' as answer",
        "-- note\nSELECT 'NOT_ANSWERABLE_RANGE: x'\n  AS \"answer\"",
    ],
)
def test_bare_literal_select_shapes_are_accepted(sql):
    assert is_not_answerable_result(_result([{"answer": "NOT_ANSWERABLE_RANGE: x"}], sql=sql)) is True


def _make_strategy(name, result):
    strategy = MagicMock()
    strategy.name = name
    strategy.resolve = AsyncMock(return_value=result)
    return strategy


_REAL_ROWS = [{"total": 42}]


@pytest.mark.asyncio
async def test_parallel_selection_prefers_a_real_answer_over_a_refusal():
    refusal = _result([{"answer": "NOT_ANSWERABLE_FIELD: no cost field"}], confidence=0.9)
    real = _result(_REAL_ROWS, confidence=0.5, sql="SELECT 1 AS total", strategy=StrategyOption.ONTOP)
    # nl_to_sql has the higher precedence, so before the fix its refusal won.
    tier = StructuredQueryTier(
        strategies=[_make_strategy(StrategyOption.NL_TO_SQL, refusal), _make_strategy(StrategyOption.ONTOP, real)]
    )
    winner = await tier.resolve("q", "ns", StrategyContext(trace=TraceCollector()), option="best")
    assert winner is real


@pytest.mark.asyncio
async def test_parallel_selection_keeps_the_refusal_when_nothing_else_answered():
    refusal = _result([{"answer": "NOT_ANSWERABLE_FIELD: no cost field"}], confidence=0.9)
    empty = _result(
        [], confidence=0.1, sql="SELECT 1 AS total", strategy=StrategyOption.ONTOP
    )  # dropped as low-confidence empty
    tier = StructuredQueryTier(
        strategies=[_make_strategy(StrategyOption.NL_TO_SQL, refusal), _make_strategy(StrategyOption.ONTOP, empty)]
    )
    winner = await tier.resolve("q", "ns", StrategyContext(trace=TraceCollector()), option="best")
    assert winner is refusal


RANGE_ROW = [{"answer": "NOT_ANSWERABLE_RANGE: March 2031 is outside the data; the plan covers 2026-01 to 2029-12"}]
RANGE_SQL = (
    "SELECT 'NOT_ANSWERABLE_RANGE: March 2031 is outside the data; the plan covers 2026-01 to 2029-12' AS answer"
)
FIELD_ROW = [{"answer": "NOT_ANSWERABLE_FIELD: no cost field for service job"}]
CONCEPT_ROW = [{"answer": "NOT_ANSWERABLE_CONCEPT: why is one PARTY built per natural person?"}]
CONCEPT_SQL = "SELECT 'NOT_ANSWERABLE_CONCEPT: why is one PARTY built per natural person?' AS answer"
BARE_ROW = [
    {
        "answer": "NOT_ANSWERABLE: 该问题为 FS-LDM 建模概念问题，非数据查询；"
        "同一自然人只建一条 PARTY 实例，身份差异由 RoleAssignment 承载。"
    }
]
BARE_SQL = (
    "SELECT 'NOT_ANSWERABLE: 该问题为 FS-LDM 建模概念问题，非数据查询；"
    "同一自然人只建一条 PARTY 实例，身份差异由 RoleAssignment 承载。' AS answer"
)


def test_kind_is_read_from_the_prefix():
    assert not_answerable_kind(_result(RANGE_ROW, sql=RANGE_SQL)) == NOT_ANSWERABLE_RANGE
    assert not_answerable_kind(_result(FIELD_ROW)) == NOT_ANSWERABLE_FIELD
    assert not_answerable_kind(_result(CONCEPT_ROW, sql=CONCEPT_SQL)) == NOT_ANSWERABLE_CONCEPT
    assert not_answerable_kind(_result([{"answer": "42"}])) is None


def test_the_unkinded_prefix_is_read_as_concept():
    # Older prompts asked for a bare prefix. Such a row is still a refusal, and it takes the
    # document-capable route (concept) rather than being presented as a data answer.
    bare = "NOT_ANSWERABLE: no cost field for service job"
    sql = "SELECT 'NOT_ANSWERABLE: no cost field for service job' AS answer"
    result = _result([{"answer": bare}], sql=sql)
    assert is_not_answerable_result(result) is True
    assert not_answerable_kind(result) == NOT_ANSWERABLE_CONCEPT


@pytest.mark.asyncio
@pytest.mark.parametrize("confidence", [0.1, 0.9])
@pytest.mark.parametrize("has_unstructured_source", [True, False])
async def test_range_refusal_is_final_with_or_without_documents(has_unstructured_source, confidence):
    registry = _registry_with_composition(has_structured_source=True, has_unstructured_source=has_unstructured_source)
    orch, parts = _make_orchestrator(sources_registry=registry, return_parts=True)
    parts["strategy_resolve"].return_value = _result(RANGE_ROW, sql=RANGE_SQL, confidence=confidence)
    response = await orch.resolve(InvokeRequest(query="What was planned for March 2031?", namespace="demo"))

    assert response.result.tier == 2
    assert parts["knowledge_retriever"].resolve.await_count == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("confidence", [0.1, 0.9])
async def test_field_refusal_is_final_when_the_namespace_has_no_documents(confidence):
    registry = _registry_with_composition(has_structured_source=True, has_unstructured_source=False)
    orch, parts = _make_orchestrator(sources_registry=registry, return_parts=True)
    parts["strategy_resolve"].return_value = _result(FIELD_ROW, confidence=confidence)
    response = await orch.resolve(InvokeRequest(query="What did service job 1234 cost?", namespace="demo"))

    assert response.result.tier == 2
    assert parts["knowledge_retriever"].resolve.await_count == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("confidence", [0.1, 0.9])
@pytest.mark.parametrize("with_registry", [True, False])
async def test_field_refusal_falls_to_tier_3_when_documents_may_answer(with_registry, confidence):
    # With documents in the namespace, or with an unknown composition, a document may hold the
    # measure (a rate card), so the refusal falls through whatever confidence the writer reported.
    registry = (
        _registry_with_composition(has_structured_source=True, has_unstructured_source=True) if with_registry else None
    )
    orch, parts = _make_orchestrator(sources_registry=registry, return_parts=True)
    parts["strategy_resolve"].return_value = _result(FIELD_ROW, confidence=confidence)
    response = await orch.resolve(InvokeRequest(query="What did service job 1234 cost?", namespace="demo"))

    assert response.result.tier == 3
    assert parts["knowledge_retriever"].resolve.await_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("confidence", [0.1, 0.9])
@pytest.mark.parametrize("with_registry", [True, False])
async def test_concept_refusal_falls_to_tier_3_when_documents_may_answer(with_registry, confidence):
    # A concept question is not a data answer; a document (or the synthesis tier) may still
    # explain it, so it must not stop at Tier 2 with a refusal row.
    registry = (
        _registry_with_composition(has_structured_source=True, has_unstructured_source=True) if with_registry else None
    )
    orch, parts = _make_orchestrator(sources_registry=registry, return_parts=True)
    parts["strategy_resolve"].return_value = _result(CONCEPT_ROW, sql=CONCEPT_SQL, confidence=confidence)
    response = await orch.resolve(InvokeRequest(query="Why is one PARTY built per person?", namespace="demo"))

    assert response.result.tier == 3
    assert parts["knowledge_retriever"].resolve.await_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("confidence", [0.1, 0.9])
async def test_concept_refusal_is_final_when_the_namespace_has_no_documents(confidence):
    registry = _registry_with_composition(has_structured_source=True, has_unstructured_source=False)
    orch, parts = _make_orchestrator(sources_registry=registry, return_parts=True)
    parts["strategy_resolve"].return_value = _result(CONCEPT_ROW, sql=CONCEPT_SQL, confidence=confidence)
    response = await orch.resolve(InvokeRequest(query="Why is one PARTY built per person?", namespace="demo"))

    assert response.result.tier == 2
    assert parts["knowledge_retriever"].resolve.await_count == 0


@pytest.mark.asyncio
async def test_bare_prefix_answer_from_an_older_prompt_now_falls_to_tier_3():
    # The Ark request that exposed this bug returned a bare NOT_ANSWERABLE: row carrying the
    # whole explanation; it was ranked as a confident data answer. With documents present it
    # must now be recognised as a refusal and fall through to Tier 3.
    registry = _registry_with_composition(has_structured_source=True, has_unstructured_source=True)
    orch, parts = _make_orchestrator(sources_registry=registry, return_parts=True)
    parts["strategy_resolve"].return_value = _result(BARE_ROW, sql=BARE_SQL, confidence=0.5)
    response = await orch.resolve(InvokeRequest(query="为什么同一自然人只建一条 PARTY？", namespace="demo"))

    assert response.result.tier == 3
    assert parts["knowledge_retriever"].resolve.await_count == 1


@pytest.mark.asyncio
async def test_low_confidence_ordinary_row_still_falls_to_tier_3():
    orch, parts = _make_orchestrator(return_parts=True)
    parts["strategy_resolve"].return_value = _result([{"answer": "42"}])
    response = await orch.resolve(InvokeRequest(query="What does the handbook recommend?", namespace="demo"))

    assert response.result.tier == 3
    assert parts["knowledge_retriever"].resolve.await_count == 1
