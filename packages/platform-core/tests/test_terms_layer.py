"""T1/T2 term-layer unit tests (no services; rdflib-backed fake graph adapter)."""

from __future__ import annotations

import re
import sys
import unittest

import rdflib

sys.path.insert(0, "/app/src")
sys.path.insert(0, "../src")

from platform_core.errors import PortError
from platform_core.termlex import (
    E_TERM_GUARD_INVALID,
    TermLexicon,
    assert_guards_compilable,
    compile_guards,
)

FIXTURE = """
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix term: <https://w3id.org/fsldm/terms#> .
@prefix ex:   <https://w3id.org/fsldm/test#> .

ex:Agreement a <http://www.w3.org/2002/07/owl#Class> ;
    term:termBatch term:batch-1 ;
    rdfs:label "保险合同（保单）"@zh ;
    skos:prefLabel "保险合同（保单）"@zh ;
    skos:prefLabel "Insurance Agreement"@en ;
    skos:altLabel "保险契约"@zh ;
    skos:altLabel "投保单"@zh ;
    term:canonicalFor ex:Policy ;
    term:suppressedSurface "保单"@zh .

ex:Policy a <http://www.w3.org/2002/07/owl#Class> ;
    term:termBatch term:batch-1 ;
    rdfs:label "保单"@zh ;
    skos:prefLabel "保单"@zh ;
    skos:prefLabel "Policy"@en .

ex:LegacyCode a <http://www.w3.org/2002/07/owl#Class> ;
    term:termBatch term:batch-1 ;
    rdfs:label "旧编码类"@zh ;
    skos:prefLabel "旧编码类"@zh ;
    skos:prefLabel "Legacy Code"@en ;
    skos:altLabel "K0001" .

ex:medium a term:TermEntry ;
    term:forClass ex:Agreement ;
    term:label "投保单"@zh ;
    term:status term:inferred ;
    term:confidence term:medium ;
    term:guardRegex "^投保单$" .
"""

BAD_GUARD = """
@prefix term: <https://w3id.org/fsldm/terms#> .
<https://w3id.org/fsldm/test#bad> a term:TermEntry ;
    term:guardRegex "([" .
"""


class FakeGraph:
    """Minimal GraphStorePort-shaped adapter over an rdflib graph."""

    def __init__(self, turtle: str) -> None:
        self.graph = rdflib.Graph()
        self.graph.parse(data=turtle, format="turtle")

    def query(self, sparql: str) -> dict:
        sparql = re.sub(r"FROM <[^>]+>", "", sparql)
        result = self.graph.query(sparql)
        bindings = []
        for row in result:
            values = {}
            for name in result.vars:
                term = getattr(row, str(name))
                if term is None:
                    continue
                if isinstance(term, rdflib.URIRef):
                    values[str(name)] = {"kind": "iri", "iri": str(term)}
                else:
                    values[str(name)] = {
                        "kind": "literal",
                        "value": str(term),
                        "lang": term.language,
                        "datatype": str(term.datatype) if term.datatype else None,
                    }
            bindings.append({"values": values})
        return {"kind": "select", "variables": [str(v) for v in result.vars], "bindings": bindings}


class TermLexiconTest(unittest.TestCase):
    def setUp(self) -> None:
        self.lexicon = TermLexicon.build(FakeGraph(FIXTURE), "urn:test:tbox")

    def test_1_alias_hits_canonical_class(self) -> None:
        hits = self.lexicon.match("保险契约的责任范围")
        self.assertEqual([hit.canonical for hit in hits], ["https://w3id.org/fsldm/test#Agreement"])
        self.assertEqual(self.lexicon.canonical_seeds(hits), ["https://w3id.org/fsldm/test#Agreement"])

    def test_2_canonical_for_does_not_redirect_remaining_aliases(self) -> None:
        # T6: Agreement keeps 保险契约; only 保单 (suppressedSurface) belongs to Policy.
        hits = self.lexicon.match("保单的免责条款")
        self.assertEqual([hit.canonical for hit in hits], ["https://w3id.org/fsldm/test#Policy"])
        self.assertEqual(self.lexicon.match("保险契约")[0].canonical,
                         "https://w3id.org/fsldm/test#Agreement")

    def test_3_untagged_legacy_alt_label_is_not_a_key(self) -> None:
        self.assertEqual(self.lexicon.match("K0001"), [])

    def test_4_guard_mismatch_is_counted_and_not_used(self) -> None:
        # 投保单 is a medium alias guarded by ^投保单$; the longer sentence trips it.
        good = self.lexicon.match("投保单")
        self.assertEqual([hit.canonical for hit in good],
                         ["https://w3id.org/fsldm/test#Agreement"])
        rejected = self.lexicon.match("投保单合同")
        # The guarded medium hit is dropped and counted; nothing else is claimed.
        self.assertEqual(rejected, [])
        self.assertEqual(self.lexicon.guard_rejected, 1)

    def test_5_longest_match_wins(self) -> None:
        hits = self.lexicon.match("保险合同（保单）与保单")
        self.assertEqual([hit.surface for hit in hits], ["保险合同（保单）", "保单"])

    def test_6_broken_guard_is_a_hard_error(self) -> None:
        with self.assertRaises(PortError) as caught:
            compile_guards([("urn:bad", "([")])
        self.assertEqual(caught.exception.provider_code, E_TERM_GUARD_INVALID)
        graph = rdflib.Graph()
        graph.parse(data=BAD_GUARD, format="turtle")
        with self.assertRaises(PortError) as caught:
            assert_guards_compilable(graph)
        self.assertEqual(caught.exception.provider_code, E_TERM_GUARD_INVALID)

    def test_7_lexical_queries_expand_only_lexical_route(self) -> None:
        hits = self.lexicon.match("保险契约")
        queries = self.lexicon.lexical_queries(hits, limit=4)
        self.assertIn("保险契约", queries)
        self.assertIn("保险合同（保单）", queries)
        self.assertIn("Insurance Agreement", queries)
        self.assertLessEqual(len(queries), 3)


if __name__ == "__main__":
    unittest.main()
