"""Synchronous view of ``MetricIndexPort`` for the metric write path.

``MetricIndexPort`` is async because the query path awaits it. Metric writes
run in synchronous handlers, so this adapter runs one coroutine per index or
remove call. It is not a second contract: ``embed_metric`` and
``delete_metric_embedding`` keep the names the call sites already use, and the
``MetricRecord`` text is built here because the port deliberately leaves the
searchable projection to the caller.

Resolution is lazy so that constructing the adapter cannot fail: the write
paths treat indexing as best-effort, and a provider that cannot be built must
surface inside their existing ``try`` block, not at handler entry.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from coa_ports import MetricRecord

from .neptune_client import MetricDefinition


def _projection(metric: MetricDefinition) -> str:
    """Name, description, synonyms and instructions — the old AOSS document text.

    Kept in step with ``opensearch_client._build_embedding_text``; the old
    module cannot be imported here because it pulls in the OpenSearch client.
    """
    parts = [metric.name, metric.description]
    if metric.ai_context:
        if metric.ai_context.synonyms:
            parts.append(" ".join(metric.ai_context.synonyms))
        if metric.ai_context.instructions:
            parts.append(metric.ai_context.instructions)
        if metric.ai_context.examples:
            parts.append(" ".join(metric.ai_context.examples))
    return " ".join(parts)


def _run(coro: Any) -> None:
    """Run one port coroutine from synchronous code.

    A handler that is already inside an event loop cannot call ``asyncio.run``;
    in that case the coroutine runs on a throwaway thread so the sync caller
    still blocks until it finishes.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(coro)
        return
    with ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(asyncio.run, coro).result()


class MetricIndexSync:
    """``embed_metric`` / ``delete_metric_embedding`` over ``MetricIndexPort``."""

    def __init__(self, port: Any | None = None) -> None:
        self._port = port

    def _resolve(self) -> Any:
        if self._port is None:
            from coa_runtime.registry import resolve

            self._port = resolve("MetricIndexPort").instance
        return self._port

    def embed_metric(self, namespace: str, metric: MetricDefinition) -> None:
        record = MetricRecord(namespace=namespace, name=metric.name, text=_projection(metric))
        _run(self._resolve().index(record))

    def delete_metric_embedding(self, namespace: str, name: str) -> None:
        _run(self._resolve().remove(namespace, name))


def build_metric_index() -> MetricIndexSync:
    """Build a lazy adapter; no provider is constructed until first use."""
    return MetricIndexSync()


__all__ = ["MetricIndexSync", "build_metric_index"]
