"""The embedding interface every embedding provider implements.

Embedding is a port with multiple implementations, not a hard-coded model:
``COA_PROVIDER_EMBEDDING`` selects one. A dimension mismatch is a contract
violation with both numbers attached; it is never averaged or truncated.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


class EmbeddingDimensionMismatch(ValueError):
    """The provider returned a vector whose width disagrees with its contract."""

    def __init__(self, *, provider: str, model: str, expected: int, actual: int) -> None:
        super().__init__(
            f"embedding dimension mismatch from {provider}/{model}: "
            f"configured {expected}, returned {actual}"
        )
        self.provider = provider
        self.model = model
        self.expected = expected
        self.actual = actual


class EmbeddingModelMismatch(ValueError):
    """The request names a model the active partition does not hold."""

    def __init__(self, *, got: str, expected: str) -> None:
        super().__init__(f"embedding model mismatch: got {got}, active partition is {expected}")
        self.got = got
        self.expected = expected


def check_dimensions(
    *, provider: str, model: str, expected: int, vectors: list[list[float]]
) -> None:
    """Reject the whole response if any vector width disagrees."""
    for vector in vectors:
        if len(vector) != expected:
            raise EmbeddingDimensionMismatch(
                provider=provider,
                model=model,
                expected=expected,
                actual=len(vector),
            )


@runtime_checkable
class EmbeddingProvider(Protocol):
    """One configured embedding implementation.

    ``dimensions`` and ``model`` are the declared partition identity used for
    guards; ``embed`` returns one vector per input text, in input order.
    """

    provider: str
    model: str
    dimensions: int

    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...

    async def health_check(self) -> dict[str, Any]:
        ...


__all__ = [
    "EmbeddingDimensionMismatch",
    "EmbeddingModelMismatch",
    "EmbeddingProvider",
    "check_dimensions",
]
