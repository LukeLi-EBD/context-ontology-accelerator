"""Local vector implementation of the COA ``VectorClient`` contract.

An in-memory index loaded from JSONL: cosine similarity is real arithmetic over
caller-supplied query vectors, so this is a working retriever (not a stub). The
lexical half of ``hybrid_search`` is token overlap, and says so in its scoring.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from coa_serve.clients.base import StructuredBackend, VectorHit

_TOKEN = re.compile(r"[0-9a-z\u4e00-\u9fff]+")


@dataclass(frozen=True)
class _Entry:
    id: str
    text: str
    vector: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    norm = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
    return dot / norm if norm else 0.0


def _tokens(text: str) -> set[str]:
    return set(_TOKEN.findall(text.lower()))


class InMemoryVectorClient:
    """Read-only ``VectorClient`` over a JSONL file of ``{id,text,vector,metadata}``."""

    backend = "in-memory"

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._entries: list[_Entry] | None = None

    def _load(self) -> list[_Entry]:
        if self._entries is not None:
            return self._entries
        entries: list[_Entry] = []
        with self._path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                entries.append(
                    _Entry(
                        id=str(record["id"]),
                        text=str(record.get("text", "")),
                        vector=[float(x) for x in record["vector"]],
                        metadata=dict(record.get("metadata") or {}),
                    )
                )
        self._entries = entries
        return entries

    def dimensions(self) -> list[int]:
        """Vector widths present in the file, so callers can refuse a foreign query."""
        return sorted({len(entry.vector) for entry in self._load()})

    def _rank(self, query_vector: list[float], *, keep) -> list[VectorHit]:
        hits: list[VectorHit] = []
        for entry in self._load():
            if not keep(entry.metadata):
                continue
            score = max(0.0, _cosine(query_vector, entry.vector))
            hits.append(VectorHit(id=entry.id, text=entry.text, score=round(score, 6), metadata=dict(entry.metadata)))
        hits.sort(key=lambda hit: (-hit.score, hit.id))
        return hits

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
        query_backend: StructuredBackend | None = None,
    ) -> list[VectorHit]:
        """Cosine k-NN with the contract's metadata filters."""
        wanted_ontologies = set(ontology_ids or [])
        query_backend_value = getattr(query_backend, "value", query_backend)

        def keep(meta: dict[str, Any]) -> bool:
            if namespace and meta.get("namespace") != namespace:
                return False
            if index and meta.get("index") != index:
                return False
            if entity_type and meta.get("entity_type") != entity_type:
                return False
            if require_mapped and not meta.get("data_source_id"):
                return False
            if wanted_ontologies and not wanted_ontologies & set(meta.get("ontology_ids") or []):
                return False
            if query_backend_value and meta.get("query_backend") != query_backend_value:
                return False
            return True

        return self._rank(query_vector, keep=keep)[: max(top_k, 0)]

    async def hybrid_search(
        self,
        query_text: str,
        query_vector: list[float],
        *,
        namespace: str = "",
        top_k: int = 5,
        index: str | None = None,
    ) -> list[VectorHit]:
        """0.5 * cosine + 0.5 * lexical token-overlap (documented, not BM25)."""
        query_tokens = _tokens(query_text)
        hits: list[VectorHit] = []
        for entry in self._load():
            meta = entry.metadata
            if namespace and meta.get("namespace") != namespace:
                continue
            if index and meta.get("index") != index:
                continue
            cosine = max(0.0, _cosine(query_vector, entry.vector))
            shared = len(query_tokens & _tokens(entry.text))
            lexical = shared / len(query_tokens) if query_tokens else 0.0
            score = round(0.5 * cosine + 0.5 * lexical, 6)
            hits.append(VectorHit(id=entry.id, text=entry.text, score=score, metadata=dict(meta)))
        hits.sort(key=lambda hit: (-hit.score, hit.id))
        return hits[: max(top_k, 0)]

    async def health_check(self) -> dict[str, Any]:
        """Report index availability; never raises (contract requirement)."""
        try:
            entries = self._load()
            return {"ok": True, "backend": self.backend, "path": str(self._path), "entries": len(entries)}
        except Exception as exc:  # noqa: BLE001 - health_check must not raise
            return {
                "ok": False,
                "backend": self.backend,
                "path": str(self._path),
                "error": f"{type(exc).__name__}: {exc}",
            }
