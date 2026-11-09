"""Q4 answerability pre-check: is the question covered by the published T-Box?

Boundary (D18): this is a deterministic, lexical gate. It reads ontology term
labels (SKOS prefLabel/altLabel when the term layer exists, plus the rdfs:label
baseline), measures how much of the question those labels cover, and returns
answerable / not-answerable plus the uncovered fragments. It never turns a
coverage gap into an affirmative answer and never invents a concept the T-Box
does not declare.

The response shape is stable: adding the SKOS term layer only switches
``termSource``; callers keep reading ``answerable``/``coverage``/``missing``.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from .adapters.ontology_pg import OntologyRegistry
from .config import ContextConfig
from .errors import PortError
from .ports import Manifest

RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
SKOS_PREF = "http://www.w3.org/2004/02/skos/core#prefLabel"
SKOS_ALT = "http://www.w3.org/2004/02/skos/core#altLabel"
SKOS_PREDICATES = (SKOS_PREF, SKOS_ALT)

MIN_TERM_CHARS = 2
MAX_QUERY_CHARS = 2000
NEARBY_LIMIT = 3
NEARBY_RATIO = 0.34

# Question/grammar words only. Content words stay in the denominator on
# purpose, so a vague question still scores low instead of looking covered.
STOPWORDS = (
    "为什么", "怎么样", "怎么", "如何", "什么", "哪些", "哪个", "哪里", "多少",
    "几个", "是否", "有没有", "能否", "请问", "告诉我", "一下", "以及", "关于",
    "根据", "的", "了", "是", "在", "和", "与", "及", "并", "或", "有", "吗",
    "呢", "啊", "请", "帮", "我", "你", "它", "都", "也", "还", "就", "很",
)
PUNCT = set(" \t\r\n，。？！、；：\"'“”‘’（）《》〈〉…—,.;:?!()[]{}<>-_/\\|@#$%^&*+=~`")


class AnswerabilityService:
    port = "Answerability"

    def __init__(
        self,
        config: ContextConfig,
        ontology: OntologyRegistry,
        graph: Any,
    ) -> None:
        self._config = config
        self._ontology = ontology
        self._graph = graph

    def manifest(self) -> Manifest:
        return Manifest(
            provider="platform",
            port=self.port,
            provider_version="q4.1",
            capabilities=["answerability.check"],
            limits={
                "minCoverage": self._config.answerable_min_coverage,
                "maxQueryChars": MAX_QUERY_CHARS,
            },
            notes={
                "slice": "Q4",
                "termSource": "skos(prefLabel/altLabel) when present + rdfs:label baseline",
                "negative": "coverage < minCoverage -> answerable=false + missing fragments",
            },
        )

    def check(
        self,
        query: str,
        ontology_version: str | None = None,
        min_coverage: float | None = None,
    ) -> dict[str, Any]:
        text = (query or "").strip()
        if not text:
            raise PortError(
                code="InvalidArgument",
                message="answerability query must not be empty",
                provider="platform",
                provider_code="E_ANSWER_QUERY_EMPTY",
            )
        if len(text) > MAX_QUERY_CHARS:
            raise PortError(
                code="InvalidArgument",
                message=f"query has {len(text)} chars, limit is {MAX_QUERY_CHARS}",
                provider="platform",
                provider_code="E_ANSWER_QUERY_TOO_LONG",
                details={"chars": len(text), "max": MAX_QUERY_CHARS},
            )
        threshold = self._config.answerable_min_coverage if min_coverage is None else float(
            min_coverage
        )
        if threshold < 0.0 or threshold > 1.0:
            raise PortError(
                code="InvalidArgument",
                message=f"minCoverage must be within 0..1, got {threshold}",
                provider="platform",
                provider_code="E_ANSWER_THRESHOLD",
                details={"minCoverage": threshold},
            )

        version = self._version(ontology_version)
        terms = self._terms(version["graph"])

        normalized = re.sub(r"\s+", "", text.lower())
        mask, content_count = self._content_mask(normalized)
        if content_count == 0:
            raise PortError(
                code="InvalidArgument",
                message="query has no content characters to check (only stopwords/punctuation)",
                provider="platform",
                provider_code="E_ANSWER_QUERY_EMPTY",
                details={"query": text},
            )

        matched, taken = self._match(normalized, terms)
        covered = sum(1 for index, is_content in enumerate(mask) if is_content and taken[index])
        coverage = covered / content_count

        missing = self._missing(normalized, mask, taken, terms)
        answerable = coverage >= threshold and bool(matched)
        result: dict[str, Any] = {
            "query": text,
            "answerable": answerable,
            "coverage": round(coverage, 4),
            "threshold": threshold,
            "coverageChars": {"covered": covered, "total": content_count},
            "ontologyVersion": version["versionId"],
            "ontologyGraph": version["graph"],
            "termSource": self._term_source(terms),
            "termCount": len({t["iri"] for t in terms}),
            "matchedTerms": matched,
            "missing": missing,
            "reasonCode": None if answerable else "E_ANSWER_NOT_COVERED",
            "hint": None
            if answerable
            else (
                "本体未覆盖问题中的这些概念："
                + "、".join(item["text"] for item in missing[:NEARBY_LIMIT])
                + "；请先补充术语（T-Box）或缩小问题范围"
            ),
            "degraded": False,
            "reasons": [],
        }
        return result

    # ---- helpers ---------------------------------------------------------

    def _version(self, version_id: str | None) -> dict[str, Any]:
        try:
            if version_id:
                row = self._ontology.get(str(version_id))
                return {"versionId": row["id"], "graph": row["graph"]}
            current = self._ontology.current()
        except PortError as exc:
            if exc.code == "NotFound":
                raise PortError(
                    code="NotFound",
                    message=f"ontology version not found: {version_id}",
                    provider="platform",
                    provider_code="E_ANSWER_VERSION",
                    details={"ontologyVersion": version_id},
                ) from exc
            raise
        if not current:
            raise PortError(
                code="NotFound",
                message="no published ontology version: answerability needs a T-Box",
                provider="platform",
                provider_code="E_ANSWER_VERSION",
            )
        return {"versionId": current["versionId"], "graph": current["graph"]}

    def _terms(self, graph_iri: str) -> list[dict[str, Any]]:
        sparql = (
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
            "PREFIX skos: <http://www.w3.org/2004/02/skos/core#> "
            f"SELECT ?s ?p ?l FROM <{graph_iri}> WHERE {{ "
            f"?s ?p ?l . FILTER(?p IN (skos:prefLabel, skos:altLabel, rdfs:label)) }}"
        )
        try:
            payload = self._graph.query(sparql)
        except PortError as exc:
            raise PortError(
                code="Unavailable",
                message=f"cannot read ontology terms: {exc.message}",
                provider="platform",
                provider_code="E_ANSWER_ONTOLOGY_UNAVAILABLE",
                details={"ontologyGraph": graph_iri, "cause": exc.provider_code or exc.code},
            ) from exc

        rows: list[dict[str, Any]] = []
        for binding in payload.get("bindings", []):
            values = binding.get("values", {})
            subject, predicate, label = (
                values.get("s"),
                values.get("p"),
                values.get("l"),
            )
            if not (subject and predicate and label):
                continue
            if subject.get("kind") != "iri" or label.get("kind") != "literal":
                continue
            rows.append(
                {
                    "iri": str(subject["iri"]),
                    "predicate": str(predicate["iri"]),
                    "label": str(label.get("value") or ""),
                }
            )
        # The term layer (SKOS) is additive: it supplements the rdfs:label
        # baseline instead of hiding entries that only carry rdfs:label.
        deduped: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for row in rows:
            key = (row["iri"], row["label"].strip().lower())
            if not row["label"].strip() or key in seen:
                continue
            seen.add(key)
            deduped.append(row)
        return deduped

    @staticmethod
    def _term_source(terms: list[dict[str, Any]]) -> str:
        has_skos = any(t["predicate"] in SKOS_PREDICATES for t in terms)
        has_rdfs = any(t["predicate"] == RDFS_LABEL for t in terms)
        if has_skos and has_rdfs:
            return "skos+rdfs:label"
        if has_skos:
            return "skos"
        return "rdfs:label"

    @staticmethod
    def _content_mask(normalized: str) -> tuple[list[bool], int]:
        mask = [char not in PUNCT for char in normalized]
        for stopword in sorted(STOPWORDS, key=len, reverse=True):
            start = normalized.find(stopword)
            while start != -1:
                for index in range(start, start + len(stopword)):
                    mask[index] = False
                start = normalized.find(stopword, start + 1)
        return mask, sum(1 for flag in mask if flag)

    @staticmethod
    def _match(
        normalized: str, terms: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[bool]]:
        taken = [False] * len(normalized)
        matched: list[dict[str, Any]] = []
        seen: set[tuple[str, int]] = set()
        labeled = sorted(
            (
                (term["iri"], term["label"], re.sub(r"\s+", "", term["label"].lower()))
                for term in terms
            ),
            key=lambda item: len(item[2]),
            reverse=True,
        )
        for iri, label, key in labeled:
            if len(key) < MIN_TERM_CHARS or not key:
                continue
            start = normalized.find(key)
            while start != -1:
                end = start + len(key)
                if not any(taken[start:end]):
                    for index in range(start, end):
                        taken[index] = True
                    if (iri, start) not in seen:
                        seen.add((iri, start))
                        matched.append(
                            {
                                "term": iri,
                                "label": label,
                                "span": [start, end],
                            }
                        )
                start = normalized.find(key, start + 1)
        return matched, taken

    @staticmethod
    def _missing(
        normalized: str,
        mask: list[bool],
        taken: list[bool],
        terms: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        fragments: list[tuple[int, int]] = []
        start: int | None = None
        for index in range(len(normalized)):
            uncovered = mask[index] and not taken[index]
            if uncovered and start is None:
                start = index
            elif not uncovered and start is not None:
                fragments.append((start, index))
                start = None
        if start is not None:
            fragments.append((start, len(normalized)))

        missing: list[dict[str, Any]] = []
        labels = list(
            {
                term["label"]: term["iri"]
                for term in terms
                if term["label"]
            }.items()
        )
        for begin, end in fragments:
            text = normalized[begin:end]
            if not text:
                continue
            nearby = sorted(
                (
                    (SequenceMatcher(None, text, label).ratio(), label, iri)
                    for label, iri in labels
                ),
                reverse=True,
            )
            entry: dict[str, Any] = {
                "text": text,
                "span": [begin, end],
                "reason": "no_ontology_term",
            }
            suggestions = [
                {"term": iri, "label": label, "similarity": round(ratio, 4)}
                for ratio, label, iri in nearby[:NEARBY_LIMIT]
                if ratio >= NEARBY_RATIO
            ]
            if suggestions:
                entry["nearbyTerms"] = suggestions
            missing.append(entry)
        return missing
