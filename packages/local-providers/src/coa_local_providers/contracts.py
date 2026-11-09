"""Local equivalents of the COA client contracts.

Why this module exists
----------------------
``local-providers`` implements the ports consumed by ``context-manager``. It
used to import the protocols and DTOs from ``coa_serve.clients.base`` (the
consumer), which inverts the dependency direction: an implementation package
must not import a service package.

The second option from the plan (move the contracts into ``coa-ports``) was not
taken yet because it would touch every consumer at once; this module is the
smaller change. The definitions below are **structurally identical** to
``coa_serve.clients.base`` and must be kept so; they carry no behaviour beyond
the DTO properties the consumers read.

``coa-ports`` remains the place for cross-service ports. These four are the
legacy COA client contracts and will migrate there when the consumers migrate
(recorded in ``doc/coa-x/00-总计划.md`` §7.1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import AsyncIterator
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

# ── Vector ───────────────────────────────────────────────────────────────────


@dataclass
class VectorHit:
    """One nearest-neighbour search result (mirror of the COA DTO)."""

    id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def data_source_id(self) -> str:
        """Provenance of this hit's entity, or "" if absent."""
        return self.metadata.get("data_source_id", "")


@runtime_checkable
class VectorClient(Protocol):
    """Vector search contract (methods only; no defaults at runtime)."""

    async def search(
        self,
        query_vector: list[float],
        *,
        namespace: str = "",
        top_k: int = 5,
        index: str | None = None,
        entity_type: str | None = None,
        require_mapped: bool = False,
        ontology_ids: list[str] | None = None,
        query_backend: str | None = None,
    ) -> list[VectorHit]: ...

    async def hybrid_search(
        self,
        query_text: str,
        query_vector: list[float],
        *,
        namespace: str = "",
        top_k: int = 5,
        index: str | None = None,
    ) -> list[VectorHit]: ...

    async def health_check(self) -> dict[str, Any]: ...


# ── SQL ──────────────────────────────────────────────────────────────────────


@dataclass
class QueryResult:
    """Result of a SQL query execution (mirror of the COA DTO)."""

    rows: list[dict[str, Any]]
    columns: list[str]
    row_count: int
    truncated: bool
    duration_ms: int = 0
    engine: str = ""


@runtime_checkable
class QueryExecutor(Protocol):
    """SQL execution contract."""

    async def execute(
        self,
        sql: str,
        *,
        namespace: str,
        data_source_id: str,
        params: dict[str, Any] | None = None,
        max_rows: int = 1000,
        timeout_seconds: int = 10,
    ) -> QueryResult: ...

    async def health_check(self) -> dict[str, Any]: ...


# ── LLM ──────────────────────────────────────────────────────────────────────


class GuardrailOutcome(StrEnum):
    """What a guardrail did to a Converse call (mirror of the COA enum)."""

    NONE = "none"
    ANONYMIZED = "anonymized"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


STOP_REASON_MAX_TOKENS = "max_tokens"


@dataclass(frozen=True)
class ConverseResult:
    """Result of a Converse call (mirror of the COA DTO)."""

    text: str
    guardrail_blocked: bool = False
    outcome: GuardrailOutcome | None = None
    stop_reason: str = ""

    def __post_init__(self) -> None:
        if self.outcome is None:
            derived = (
                GuardrailOutcome.BLOCKED
                if self.guardrail_blocked
                else GuardrailOutcome.NONE
            )
            object.__setattr__(self, "outcome", derived)
        else:
            object.__setattr__(
                self,
                "guardrail_blocked",
                self.outcome in (GuardrailOutcome.BLOCKED, GuardrailOutcome.UNKNOWN),
            )

    @property
    def truncated(self) -> bool:
        """True when the model stopped because it hit the output-token cap."""
        return self.stop_reason == STOP_REASON_MAX_TOKENS


@runtime_checkable
class LLMClient(Protocol):
    """LLM inference contract (methods only; no defaults at runtime)."""

    async def converse(
        self,
        prompt: str,
        *,
        system: str | None = None,
        guardrail_id: str | None = None,
        max_tokens: int = 4096,
        temperature: float | None = None,
        top_p: float | None = None,
        guard_content: str | None = None,
        model_id: str | None = None,
    ) -> ConverseResult: ...

    def converse_stream(
        self,
        prompt: str,
        *,
        system: str | None = None,
        guardrail_id: str | None = None,
        max_tokens: int = 4096,
        guard_content: str | None = None,
        model_id: str | None = None,
    ) -> AsyncIterator[str]: ...

    async def embed(self, text: str) -> list[float]: ...

    async def health_check(self) -> dict[str, Any]: ...


__all__ = [
    "ConverseResult",
    "GuardrailOutcome",
    "LLMClient",
    "QueryExecutor",
    "QueryResult",
    "VectorClient",
    "VectorHit",
]
