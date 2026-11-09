"""COA ``MetricIndexPort`` backed by ``platform.metric_definition``.

The platform already stores every metric definition in PostgreSQL, and the
metric-service that used to keep a derived OpenSearch index writes those same
rows through the control plane. So the local provider answers ``search`` from
the system of record and does not maintain a second copy: ``index`` / ``remove``
are documented no-ops, not silent fallbacks — there is nothing to keep in sync.

PostgreSQL is single-tenant here, so ``namespace`` is echoed back rather than
filtering rows. That is stated in :meth:`PgMetricIndex.search` instead of being
hidden, because a multi-tenant deployment must use the AOSS provider.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

from coa_ports import MetricHit, MetricRecord, PortError, PortErrorCode
from platform_core.adapters.metadata_pg import MetadataPg

# Trigram similarity floor. Kept low because a metric description is short and
# the caller orders by score itself; a high floor silently drops real matches.
_MIN_SIMILARITY = 0.1

_SEARCH_SQL = """
SELECT metric_id,
       name_zh,
       COALESCE(display_name, '') AS display_name,
       COALESCE(definition, '')   AS definition,
       COALESCE(formula_text, '') AS formula_text,
       GREATEST(
           word_similarity(%s, name_zh),
           word_similarity(%s, COALESCE(display_name, '')),
           word_similarity(%s, COALESCE(definition, '')),
           word_similarity(%s, COALESCE(formula_text, ''))
       ) AS score
  FROM platform.metric_definition
 WHERE GREATEST(
           word_similarity(%s, name_zh),
           word_similarity(%s, COALESCE(display_name, '')),
           word_similarity(%s, COALESCE(definition, '')),
           word_similarity(%s, COALESCE(formula_text, ''))
       ) >= %s
 ORDER BY score DESC, metric_id
 LIMIT %s
"""


class PgMetricIndex:
    """``MetricIndexPort`` over the platform metric catalogue."""

    backend = "platform-pg"

    def __init__(
        self,
        dsn: str,
        *,
        pool_max: int = 4,
        open_timeout_seconds: float = 10.0,
    ) -> None:
        self._meta = MetadataPg(dsn, pool_max=pool_max)
        self._meta.open(retry_seconds=open_timeout_seconds)

    async def index(self, record: MetricRecord) -> None:
        """No-op: the row this record describes is the index.

        A metric is written by the control plane into ``platform.metric_definition``
        before this method is called, so there is no derived copy that could go
        stale. Kept in the protocol because an external-index provider needs it.
        """
        if not record.name or not record.namespace:
            raise PortError(
                PortErrorCode.INVALID_ARGUMENT,
                "metric record needs a namespace and a name",
                provider=self.backend,
                provider_code="E_METRIC_RECORD_INCOMPLETE",
            )

    async def remove(self, namespace: str, name: str) -> None:
        """No-op: deleting the metric row removes it from search results."""
        return None

    async def search(self, namespace: str, query: str, *, top_k: int = 5) -> tuple[MetricHit, ...]:
        """Trigram match over name / display name / definition / formula.

        ``namespace`` is echoed, not filtered: the local PostgreSQL holds one
        tenant. A deployment that needs namespace isolation must configure the
        ``aoss`` provider.
        """
        if top_k <= 0 or not query.strip():
            return ()
        rows = await asyncio.to_thread(self._search_rows, query, top_k)
        return tuple(
            MetricHit(
                namespace=namespace,
                name=str(row["metric_id"]),
                text=" ".join(
                    part
                    for part in (
                        str(row["name_zh"]),
                        str(row["display_name"]),
                        str(row["definition"]),
                        str(row["formula_text"]),
                    )
                    if part
                ),
                score=float(row["score"] or 0.0),
            )
            for row in rows
        )

    async def probe(self) -> Mapping[str, Any]:
        """Reachability snapshot; never raises."""
        try:
            await asyncio.to_thread(self._meta.query, "SELECT 1 AS ok")
            return {"ok": True, "backend": self.backend}
        except Exception as exc:  # noqa: BLE001 - probe must not raise
            return {"ok": False, "backend": self.backend, "error": f"{type(exc).__name__}: {exc}"}

    async def close(self) -> None:
        await asyncio.to_thread(self._meta.close)

    def _search_rows(self, query: str, top_k: int) -> list[dict[str, Any]]:
        params = (query, query, query, query, query, query, query, query, _MIN_SIMILARITY, top_k)
        return self._meta.query(_SEARCH_SQL, params)


__all__ = ["PgMetricIndex"]
