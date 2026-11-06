"""T1/T2 term layer: SKOS alias lexicon over the published T-Box.

Boundary: this module only reads annotations (skos:prefLabel / skos:altLabel /
rdfs:label plus the term: vocabulary) from the T-Box graph and turns them into
an in-memory surface lexicon. It never writes to the graph and never changes
ranking; the document side only feeds extra strings to the existing lexical
route (RRF stays two-route, k=60).

Design: _design/24-术语层落地-方案.md sections 4.2, 7-1, 7-2, 7-3.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import rdflib

from .errors import PortError

SKOS = "http://www.w3.org/2004/02/skos/core#"
RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
TERM = "https://w3id.org/fsldm/terms#"
TERM_ENTRY = f"{TERM}TermEntry"
E_TERM_GUARD_INVALID = "E_TERM_GUARD_INVALID"

def class_query(graph_iri: str) -> str:
    return f"""
SELECT ?s ?p ?o FROM <{graph_iri}> WHERE {{
  ?s <{TERM}termBatch> ?b .
  VALUES ?p {{
    <{SKOS}prefLabel> <{SKOS}altLabel> <{RDFS_LABEL}>
    <{TERM}suppressedSurface> <{TERM}canonicalFor>
  }}
  ?s ?p ?o .
}}
"""


def concept_query(graph_iri: str) -> str:
    """B-05: metric concepts in the term vocabulary (skos:Concept + notation).

    They live next to the class aliases in the T-Box but are not termBatch
    anchors, so they need their own read: surface -> concept IRI, which
    /context/resolve turns into a seed (the concept's definition triples).
    """
    return f"""
SELECT ?s ?p ?o FROM <{graph_iri}> WHERE {{
  ?s a <{SKOS}Concept> ;
     <{SKOS}notation> ?n ;
     <{SKOS}inScheme> <{TERM}MetricScheme> .
  VALUES ?p {{
    <{SKOS}prefLabel> <{SKOS}altLabel> <{RDFS_LABEL}>
  }}
  ?s ?p ?o .
}}
"""


def entry_query(graph_iri: str) -> str:
    return f"""
SELECT ?e ?c ?l ?conf ?guard ?status FROM <{graph_iri}> WHERE {{
  ?e <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <{TERM_ENTRY}> ;
     <{TERM}forClass> ?c ;
     <{TERM}label> ?l .
  OPTIONAL {{ ?e <{TERM}confidence> ?conf }}
  OPTIONAL {{ ?e <{TERM}guardRegex> ?guard }}
  OPTIONAL {{ ?e <{TERM}status> ?status }}
}}
"""


def compile_guard(pattern: str, owner: str = "") -> re.Pattern[str]:
    """One guardRegex; a broken pattern is a hard load-time failure."""
    try:
        return re.compile(pattern)
    except re.error as exc:
        raise PortError(
            code="InvalidArgument",
            message=f"term:guardRegex for {owner or pattern} does not compile: {exc}",
            provider="platform",
            provider_code=E_TERM_GUARD_INVALID,
            details={"entry": owner, "pattern": pattern, "error": str(exc)},
        ) from exc


def compile_guards(pairs: list[tuple[str, str]]) -> dict[str, re.Pattern[str]]:
    """Compile every guardRegex keyed by its owner (used by the import gate)."""
    return {owner: compile_guard(pattern, owner) for owner, pattern in pairs}


def assert_guards_compilable(graph: Any) -> None:
    """Load-time gate used by the ontology import path (rdflib graph)."""
    pairs = [
        (str(subject), str(pattern))
        for subject, pattern in graph.subject_objects(rdflib.URIRef(f"{TERM}guardRegex"))
    ]
    compile_guards(pairs)


@dataclass(frozen=True)
class TermHit:
    surface: str
    canonical: str
    label: str
    lang: str
    source: str  # "pref" | "alt" | "legacy-label"


def _absorb(result: Any, nodes: dict[str, dict[str, Any]]) -> None:
    """Merge annotation rows into the surface nodes (classes and concepts)."""
    for row in result.get("bindings", []):
        values = row.get("values", {})
        subject = (values.get("s") or {}).get("iri")
        predicate = (values.get("p") or {}).get("iri")
        obj = values.get("o") or {}
        if not subject or not predicate:
            continue
        node = nodes.setdefault(
            subject,
            {"pref": {}, "alt": {}, "label": {}, "suppressed": set(), "canonicalFor": None},
        )
        text = str(obj.get("value", ""))
        lang = str(obj.get("lang") or "")
        if predicate == f"{SKOS}prefLabel":
            node["pref"][lang] = text
        elif predicate == f"{SKOS}altLabel":
            if lang:
                node["alt"].setdefault(lang, set()).add(text)
            # untagged legacy machine codes stay out of the lexicon (L1-01)
        elif predicate == RDFS_LABEL:
            node["label"][lang] = text
        elif predicate == f"{TERM}suppressedSurface":
            node["suppressed"].add(text)
        elif predicate == f"{TERM}canonicalFor":
            node["canonicalFor"] = obj.get("iri")


class TermLexicon:
    """Surface -> canonical class dictionary built from one T-Box version."""

    def __init__(self, entries: list[dict[str, Any]]) -> None:
        self._entries = entries
        self._keys = sorted(entries, key=lambda item: (-len(item["surface"]), item["surface"]))
        self.guard_rejected = 0

    # ---- build -----------------------------------------------------------

    @classmethod
    def build(cls, graph: Any, tbox_graph: str) -> "TermLexicon":
        classes: dict[str, dict[str, Any]] = {}
        _absorb(graph.query(class_query(tbox_graph)), classes)
        # B-05: metric concepts share the namespace but are not class anchors;
        # their pref/alt labels become seeds pointing at the concept IRI.
        _absorb(graph.query(concept_query(tbox_graph)), classes)

        entries_result = graph.query(entry_query(tbox_graph))
        compiled_guards: dict[tuple[str, str], re.Pattern[str]] = {}
        for row in entries_result.get("bindings", []):
            values = row.get("values", {})
            entry_iri = (values.get("e") or {}).get("iri") or ""
            owner = (values.get("c") or {}).get("iri") or ""
            label = values.get("l") or {}
            guard = values.get("guard")
            if not owner or not label or guard is None:
                continue
            pattern = str(guard.get("value", ""))
            if pattern:
                compiled_guards[(owner, str(label.get("value", "")))] = compile_guard(
                    pattern, entry_iri
                )

        entries: list[dict[str, Any]] = []
        for owner, node in classes.items():
            # T6: a deferring class keeps its own aliases; only the surface it
            # gives away (term:suppressedSurface) is dropped. canonicalFor is
            # documentation, never a redirect of the remaining aliases.
            canonical = owner
            for lang, text in node["pref"].items():
                if not text or text in node["suppressed"]:
                    continue
                entries.append(
                    {
                        "surface": text,
                        "canonical": canonical,
                        "label": text,
                        "lang": lang,
                        "source": "pref",
                        "guard": compiled_guards.get((owner, text)),
                    }
                )
            for lang, texts in node["alt"].items():
                for text in texts:
                    if text in node["suppressed"]:
                        continue
                    entries.append(
                        {
                            "surface": text,
                            "canonical": canonical,
                            "label": text,
                            "lang": lang,
                            "source": "alt",
                            "guard": compiled_guards.get((owner, text)),
                        }
                    )
            for lang, text in node["label"].items():
                if not text:
                    continue
                entries.append(
                    {
                        "surface": text,
                        "canonical": canonical,
                        "label": text,
                        "lang": lang,
                        "source": "legacy-label"
                        if not node["pref"]
                        else "pref",
                        "guard": None,
                    }
                )
        # Deduplicate identical surfaces (prefLabel and rdfs:label usually match):
        # the first entry wins, pref beats alt beats legacy-label.
        merged: dict[tuple[str, str, str], dict[str, Any]] = {}
        order = {"pref": 0, "alt": 1, "legacy-label": 2}
        for entry in entries:
            key = (entry["surface"], entry["lang"], entry["canonical"])
            current = merged.get(key)
            if current is None or order[entry["source"]] < order[current["source"]]:
                merged[key] = entry
        return cls(list(merged.values()))

    # ---- query -----------------------------------------------------------

    def match(self, query: str, *, max_hits: int = 5) -> list[TermHit]:
        """Longest match first, non-overlapping; deterministic on ties."""
        text = query or ""
        hits: list[TermHit] = []
        position = 0
        length = len(text)
        while position < length and len(hits) < max_hits:
            found = None
            for entry in self._keys:
                surface = entry["surface"]
                if not surface:
                    continue
                end = position + len(surface)
                if end > length:
                    continue
                chunk = text[position:end]
                if entry["lang"].lower() == "en":
                    matched = chunk.lower() == surface.lower()
                else:
                    matched = chunk == surface
                if matched:
                    found = entry
                    break
            if found is None:
                position += 1
                continue
            guard = found.get("guard")
            if guard is not None and not guard.search(text):
                # Runtime guard: a medium alias outside its context is dropped,
                # counted, and never contributes to the seed list.
                self.guard_rejected += 1
                position += len(found["surface"])
                continue
            hits.append(
                TermHit(
                    surface=found["surface"],
                    canonical=found["canonical"],
                    label=found["label"],
                    lang=found["lang"],
                    source=found["source"],
                )
            )
            position += len(found["surface"])
        return hits

    def canonical_seeds(self, hits: list[TermHit]) -> list[str]:
        return list(dict.fromkeys(hit.canonical for hit in hits))

    def lexical_queries(self, hits: list[TermHit], *, limit: int = 4) -> list[str]:
        """Expanded lexical strings: canonical prefLabel + hit label + prefLabel@en."""
        output: list[str] = []
        for surface in (hit.label for hit in hits):
            if surface and surface not in output:
                output.append(surface)
        for hit in hits:
            if hit.lang != "zh":
                continue
            canonical = hit.canonical
            for entry in self._keys:
                if entry["canonical"] == canonical and entry["lang"] == "zh" and entry["source"] == "pref":
                    if entry["surface"] not in output:
                        output.append(entry["surface"])
                    break
        for hit in hits:
            for entry in self._keys:
                if entry["canonical"] == hit.canonical and entry["lang"] == "en":
                    if entry["surface"] not in output:
                        output.append(entry["surface"])
                    break
        return output[: max(0, limit - 1)]  # the caller always sends the raw query too
