"""Q4 answerability pre-check: is the question covered by the published T-Box?

Boundary (D18): this is a deterministic, lexical gate. It reads ontology term
labels (SKOS prefLabel/altLabel when the term layer exists, plus the rdfs:label
baseline), measures how much of the question those labels cover, and returns
answerable / not-answerable plus the uncovered fragments. It never turns a
coverage gap into an affirmative answer and never invents a concept the T-Box
does not declare.

The response shape is stable: adding the SKOS term layer only switches
``termSource``; callers keep reading ``answerable``/``coverage``/``missing``.

Coverage basis: ``answerable`` is decided on entity coverage (matched entities /
mentioned entities, 1/n), not on character overlap. ``coverage`` and
``coverageChars`` are kept unchanged as the character-level diagnostic so
existing callers and the published contract stay wire-compatible; the entity
numbers live in the added ``entityCoverage``/``entityCount``/
``matchedEntityCount``/``entityMentions`` fields.

Entity extraction is lexicon-driven, not an NLP pipeline: known entities come
from the same SKOS prefLabel/altLabel/rdfs:label longest-match used for char
coverage; every remaining content fragment is one unresolved entity mention.
No ontology entity recognised means coverage 0.0 with
``entityDegraded``/``entityDegradeReason`` set, never a silent 100%.
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

# Question-meta words that are not entities on their own. They are removed from
# the entity denominator only (the character mask keeps them), so "口径/处理"
# do not turn a one-entity question into a 1/2 coverage miss. Kept deliberately
# short: this is a stoplist, not a segmentation model.
ENTITY_META_WORDS = (
    "口径", "定义", "含义", "意思", "解释", "说明", "规则", "标准", "方法",
    "流程", "处理", "怎么办", "多久", "多大", "多高", "多长",
)
ENTITY_META_CHARS = set("".join(ENTITY_META_WORDS))

# Connectors used only to cut an unresolved fragment into candidate mentions:
# "价值发生巨大变化时银行" must count as two missing entities, not one.
# Categories, all from the Chinese question wording in the corpus:
#   并列/选择  以及 或者 还是 及其 和 与 及 或 并 且 而
#   结构助词    的 地 得 之
#   介词/对象  对于 关于 针对 按照 根据 通过 对 在 把 被
#   因果/条件  由于 因为 所以 如果 若是
#   时间/处所  之后 之前 期间 时
#   疑问/程度  如何 怎么 怎样 多少 多久 多大 多高 多长 什么 是否
# Single chars that are common inside entity names (为/中/内/前/后/上/下/里)
# stay out on purpose, so "上市公司" is not shredded.
SEGMENT_CONNECTORS = (
    "以及", "或者", "还是", "及其", "对于", "关于", "针对", "按照", "根据",
    "通过", "由于", "因为", "所以", "如果", "若是", "之后", "之前", "期间",
    "如何", "怎么", "怎样", "多少", "多久", "多大", "多高", "多长", "什么",
    "是否", "和", "与", "及", "或", "并", "且", "而", "的", "地", "得", "之",
    "对", "在", "把", "被", "时",
)
_SEGMENT_CONNECTORS_SORTED = tuple(
    sorted(SEGMENT_CONNECTORS, key=len, reverse=True)
)




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

        entities = self._entities(normalized, mask, matched, taken, terms)
        missing = self._missing(normalized, mask, taken, terms)
        answerable = (
            entities["coverage"] >= threshold and entities["matched"] > 0
        )
        result: dict[str, Any] = {
            "query": text,
            "answerable": answerable,
            "coverage": round(coverage, 4),
            "threshold": threshold,
            "coverageChars": {"covered": covered, "total": content_count},
            "entityCoverage": round(entities["coverage"], 4),
            "entityCount": entities["count"],
            "matchedEntityCount": entities["matched"],
            "entityMentions": entities["mentions"],
            "entityDegraded": entities["degraded"],
            "entityDegradeReason": entities["degradeReason"],
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
    def _fragments(mask: list[bool], taken: list[bool]) -> list[tuple[int, int]]:
        """Maximal content runs no ontology term covers, in question order."""
        fragments: list[tuple[int, int]] = []
        start: int | None = None
        for index in range(len(mask)):
            uncovered = mask[index] and not taken[index]
            if uncovered and start is None:
                start = index
            elif not uncovered and start is not None:
                fragments.append((start, index))
                start = None
        if start is not None:
            fragments.append((start, len(mask)))
        return fragments

    @staticmethod
    def _split_unresolved(text: str) -> list[tuple[str, int, int]]:
        """Cut one unresolved fragment at connectors, keeping offsets.

        Segments shorter than two characters are merged into a neighbour: a
        lone char is almost always half of a word that merely contains a
        connector character (利率对冲 -> 利率|冲), so merging keeps the rule
        from shredding real terms. The rule can only add segments relative to
        one-fragment-one-entity, never remove one, so it cannot loosen a
        decision. Returns (surface, start, end) in fragment coordinates.
        """
        raw: list[tuple[int, int]] = []
        start = 0
        index = 0
        while index < len(text):
            connector = next(
                (
                    item
                    for item in _SEGMENT_CONNECTORS_SORTED
                    if text.startswith(item, index)
                ),
                None,
            )
            if connector is not None or text[index] in PUNCT:
                if index > start:
                    raw.append((start, index))
                    index += len(connector) if connector else 1
                    start = index
                    continue
                # Leading connector: keep it with the following text so
                # "时速" is not reduced to "速".
                index += len(connector) if connector else 1
                continue
            index += 1
        if start < len(text):
            raw.append((start, len(text)))

        merged: list[tuple[int, int]] = []
        carry: tuple[int, int] | None = None
        for begin, end in raw:
            if carry is not None:
                begin, carry = carry[0], None
            if end - begin < 2:
                carry = (begin, end)
                continue
            merged.append((begin, end))
        if carry is not None:
            if merged:
                merged[-1] = (merged[-1][0], carry[1])
            else:
                merged.append(carry)
        if not merged and text:
            # A fragment made only of connectors still counted as one entity
            # before this rule; keep that so splitting never lowers the
            # denominator on its own.
            merged.append((0, len(text)))
        return [(text[begin:end], begin, end) for begin, end in merged]

    @staticmethod
    def _entities(
        normalized: str,
        mask: list[bool],
        matched: list[dict[str, Any]],
        taken: list[bool],
        terms: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """1/n entity coverage over lexicon hits plus unresolved fragments.

        A known entity is one distinct ontology IRI hit by any of its labels
        (prefLabel/altLabel/rdfs:label alike). An unresolved entity is one
        connector-delimited segment of an uncovered content fragment, so
        several missing concepts glued together still count separately;
        segments made only of question meta words (口径/处理/多久 ...) are not
        entities and stay out of the denominator. Same surface counts once.
        """
        predicates: dict[str, set[str]] = {}
        for term in terms:
            predicates.setdefault(term["iri"], set()).add(term["predicate"])

        known: dict[str, dict[str, Any]] = {}
        for item in sorted(matched, key=lambda row: row["span"][0]):
            iri = str(item["term"])
            if iri in known:
                continue
            known[iri] = {
                "text": item["label"],
                "span": list(item["span"]),
                "kind": "ontology",
                "term": iri,
                "label": item["label"],
                "source": "skos"
                if predicates.get(iri, set()) & set(SKOS_PREDICATES)
                else "rdfs:label",
            }

        unknown: dict[str, dict[str, Any]] = {}
        for begin, end in AnswerabilityService._fragments(mask, taken):
            fragment = normalized[begin:end]
            for text, offset, stop in AnswerabilityService._split_unresolved(fragment):
                if not text or all(char in ENTITY_META_CHARS for char in text):
                    continue
                if text in unknown:
                    continue
                unknown[text] = {
                    "text": text,
                    "span": [begin + offset, begin + stop],
                    "kind": "unknown",
                }

        mentions = sorted(
            list(known.values()) + list(unknown.values()),
            key=lambda row: (row["span"][0], row["span"][1]),
        )
        count = len(known) + len(unknown)
        matched_count = len(known)
        if count == 0:
            coverage, degraded, reason = 0.0, True, "no_entity_mention"
        elif matched_count == 0:
            coverage, degraded, reason = 0.0, True, "no_ontology_entity"
        else:
            coverage, degraded, reason = matched_count / count, False, None
        return {
            "coverage": coverage,
            "count": count,
            "matched": matched_count,
            "mentions": mentions,
            "degraded": degraded,
            "degradeReason": reason,
        }

    @staticmethod
    def _missing(
        normalized: str,
        mask: list[bool],
        taken: list[bool],
        terms: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        fragments = AnswerabilityService._fragments(mask, taken)

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
