"""B-05 metric vocabulary tests: SKOS generation, shapes, lexicon coverage.

Unit cases use an in-memory rdflib fixture (no services). Live cases read the
published T-Box pointer from postgres and query Oxigraph; they are skipped when
the acceptance stack is not reachable.

Run inside the platform image:
  docker run --rm --network agent-platform_default --entrypoint python \
    -e TEST_PG_DSN=... -e TEST_OXIGRAPH_URL=... -v <repo>/src:/app/src:ro \
    -v <repo>/tests:/hosttests:ro -v D:/agentABC/data:/data \
    agent-platform:0.1-s5 -m unittest discover -s /hosttests -t /hosttests -k metric
"""

from __future__ import annotations

import os
import sys
import unittest

import rdflib

sys.path.insert(0, os.environ.get("PLATFORM_SRC", "/app/src"))
sys.path.insert(0, "../src")

from platform_core.termlex import TermLexicon

SKOS = rdflib.Namespace("http://www.w3.org/2004/02/skos/core#")
RDF = rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
TERM = rdflib.Namespace("https://w3id.org/fsldm/terms#")
METRIC = rdflib.Namespace("https://w3id.org/fsldm/metrics#")
SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")

SHAPES_PATH = os.environ.get("B05_SHAPES", "/data/shapes/fsldm/metrics.ttl")
PG_DSN = os.environ.get("TEST_PG_DSN", "")
OXIGRAPH = os.environ.get("TEST_OXIGRAPH_URL", "http://oxigraph:7878")

FIXTURE = """
@prefix skos:   <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs:   <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:    <http://www.w3.org/2002/07/owl#> .
@prefix term:   <https://w3id.org/fsldm/terms#> .
@prefix metric: <https://w3id.org/fsldm/metrics#> .

term:MetricScheme a skos:ConceptScheme ;
    skos:prefLabel "FS-LDM 指标词表"@zh .

term:M-FIN-BANK-001 a skos:Concept ;
    skos:inScheme term:MetricScheme ;
    skos:prefLabel "逾期天数（DPD）"@zh ;
    skos:altLabel "逾期天数"@zh ;
    skos:notation "FIN-BANK-001" ;
    skos:definition "贷款合同到期未归还时，自到期日次日起至观察日累计的自然日天数。"@zh .

term:M-FIN-BANK-036 a skos:Concept ;
    skos:inScheme term:MetricScheme ;
    skos:prefLabel "不良处置率/处置回收率"@zh ;
    skos:notation "FIN-BANK-036" ;
    skos:definition "口径族索引。"@zh .

term:M-FIN-BANK-036-v1 a skos:Concept ;
    skos:inScheme term:MetricScheme ;
    skos:prefLabel "不良处置率"@zh ;
    skos:notation "FIN-BANK-036-v1" ;
    skos:definition "期内完成处置的不良资产账面金额占期初不良资产余额的比例。"@zh ;
    skos:broader term:M-FIN-BANK-036 ;
    metric:variant true .

term:Anchor a <http://www.w3.org/2002/07/owl#Class> ;
    term:termBatch term:batch-1 ;
    rdfs:label "锚点类"@zh ;
    skos:prefLabel "锚点类"@zh ;
    skos:prefLabel "Anchor"@en .
"""

BAD_FIXTURE = """
@prefix skos:   <http://www.w3.org/2004/02/skos/core#> .
@prefix term:   <https://w3id.org/fsldm/terms#> .
@prefix metric: <https://w3id.org/fsldm/metrics#> .

term:M-CUST-001 a skos:Concept ;
    skos:notation "CUST-001" ;
    skos:notation "CUST-002" .

term:M-CUST-002 a skos:Concept ;
    skos:prefLabel "客户流失率"@zh ;
    skos:notation "CUST-001" .

term:M-CUST-003 a skos:Concept ;
    skos:prefLabel "变体无上界"@zh ;
    skos:notation "CUST-003" ;
    skos:definition "缺少 broader 的变体。"@zh ;
    metric:variant true .
"""


class FakeGraph:
    """GraphStorePort-shaped adapter over an rdflib graph."""

    def __init__(self, turtle: str) -> None:
        self.graph = rdflib.Graph()
        self.graph.parse(data=turtle, format="turtle")

    def query(self, sparql: str) -> dict:
        import re

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
                        "lang": getattr(term, "language", None),
                    }
            bindings.append({"values": values})
        return {"bindings": bindings}


def _query_sparql(statement: str) -> list[dict]:
    import httpx

    response = httpx.post(
        f"{OXIGRAPH}/query",
        data={"query": statement},
        headers={"Accept": "application/sparql-results+json"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("results", {}).get("bindings", [])


def _tbox_graph() -> str | None:
    import psycopg

    try:
        with psycopg.connect(PG_DSN, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT version_id FROM platform.graph_pointer WHERE name='tbox/current'"
                )
                row = cur.fetchone()
        return f"urn:platform:graph:tbox:{row[0]}" if row else None
    except Exception:
        return None


class MetricLexiconTests(unittest.TestCase):
    def test_1_metric_concept_pref_becomes_seed(self):
        lexicon = TermLexicon.build(FakeGraph(FIXTURE), "urn:test:tbox")
        hits = lexicon.match("逾期天数（DPD）怎么算")
        self.assertTrue(hits)
        self.assertEqual(hits[0].canonical, "https://w3id.org/fsldm/terms#M-FIN-BANK-001")
        self.assertEqual(hits[0].source, "pref")

    def test_2_metric_altlabel_becomes_seed(self):
        lexicon = TermLexicon.build(FakeGraph(FIXTURE), "urn:test:tbox")
        hits = lexicon.match("逾期天数如何定义")
        self.assertTrue(hits)
        self.assertEqual(hits[0].canonical, "https://w3id.org/fsldm/terms#M-FIN-BANK-001")
        self.assertEqual(hits[0].surface, "逾期天数")
        self.assertEqual(hits[0].source, "alt")

    def test_3_class_alias_lexicon_still_works(self):
        lexicon = TermLexicon.build(FakeGraph(FIXTURE), "urn:test:tbox")
        hits = lexicon.match("锚点类是什么")
        self.assertTrue(hits)
        self.assertEqual(hits[0].canonical, "https://w3id.org/fsldm/terms#Anchor")


class MetricShaclTests(unittest.TestCase):
    def _validate(self, turtle: str) -> tuple[bool, int]:
        from pyshacl import validate

        data = rdflib.Graph()
        data.parse(data=turtle, format="turtle")
        shapes = rdflib.Graph()
        shapes.parse(SHAPES_PATH, format="turtle")
        conforms, report, _ = validate(
            data,
            shacl_graph=shapes,
            inference="rdfs",
            allow_infos=True,
            allow_warnings=True,
        )
        count = len(list(report.subjects(RDF.type, SH.ValidationResult)))
        return bool(conforms), count

    @unittest.skipUnless(os.path.exists(SHAPES_PATH), "metric shapes not deployed")
    def test_4_valid_vocabulary_passes_shapes(self):
        conforms, count = self._validate(FIXTURE)
        self.assertTrue(conforms)
        self.assertEqual(count, 0)

    @unittest.skipUnless(os.path.exists(SHAPES_PATH), "metric shapes not deployed")
    def test_5_broken_vocabulary_reports_warnings_only(self):
        conforms, count = self._validate(BAD_FIXTURE)
        # allow_warnings=True keeps Warning results non-blocking (conforms stays true).
        self.assertTrue(conforms)
        self.assertGreaterEqual(count, 3)


class LiveVocabularyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph_iri = _tbox_graph() if PG_DSN else None
        if cls.graph_iri is None:
            raise unittest.SkipTest("live T-Box pointer unavailable")

    def _rows(self, body: str) -> list[dict]:
        return _query_sparql(
            f"""
            SELECT * WHERE {{ GRAPH <{self.graph_iri}> {{ {body} }} }}
            """
        )

    def test_6_published_vocabulary_has_85_concepts(self):
        rows = self._rows(
            "?c <http://www.w3.org/2004/02/skos/core#inScheme> "
            "<https://w3id.org/fsldm/terms#MetricScheme> ; "
            "<http://www.w3.org/2004/02/skos/core#notation> ?n ."
        )
        notations = {row["n"]["value"] for row in rows}
        self.assertEqual(len(notations), 85)
        self.assertIn("FIN-BANK-001", notations)
        self.assertIn("FIN-BANK-036-v2", notations)

    def test_7_every_concept_has_pref_and_definition(self):
        rows = self._rows("""
            ?c <http://www.w3.org/2004/02/skos/core#inScheme> <https://w3id.org/fsldm/terms#MetricScheme> ;
               <http://www.w3.org/2004/02/skos/core#notation> ?n .
            OPTIONAL { ?c <http://www.w3.org/2004/02/skos/core#prefLabel> ?p .
                       FILTER(lang(?p) = "zh") }
            OPTIONAL { ?c <http://www.w3.org/2004/02/skos/core#definition> ?d .
                       FILTER(lang(?d) = "zh") }
        """)
        missing_pref = [row["n"]["value"] for row in rows if "p" not in row]
        missing_def = [row["n"]["value"] for row in rows if "d" not in row]
        self.assertEqual(missing_pref, [])
        self.assertEqual(missing_def, [])

    def test_8_six_variants_point_at_a_broader(self):
        rows = self._rows("""
            ?c <https://w3id.org/fsldm/metrics#variant> ?v .
            OPTIONAL { ?c <http://www.w3.org/2004/02/skos/core#broader> ?b }
        """)
        self.assertEqual(len(rows), 6)
        orphans = [
            row["c"]["value"] for row in rows if "b" not in row
        ]
        self.assertEqual(orphans, [])

    def test_9_calculation_fields_stay_out_of_skos(self):
        forbidden = ("formula", "window", "aggregate", "numerator", "denominator", "grain")
        rows = self._rows("""
            ?c <http://www.w3.org/2004/02/skos/core#inScheme> <https://w3id.org/fsldm/terms#MetricScheme> ;
               <http://www.w3.org/2004/02/skos/core#notation> ?n ;
               ?p ?o .
        """)
        leaked = [
            row["p"]["value"]
            for row in rows
            if any(word in row["p"]["value"].lower() for word in forbidden)
        ]
        self.assertEqual(leaked, [])
