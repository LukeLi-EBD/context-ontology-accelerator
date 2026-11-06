# -*- coding: utf-8 -*-
"""静态校验两个 seed 草稿：能否解析 + 是否真的不移动/移动特定计数。"""
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, SKOS

TERM = "https://w3id.org/fsldm/terms#"
TARGET = "https://w3id.org/fsldm/policy#"

for path in ("01-knowledge-gap.proposed.ttl", "02-knowledge-gap.retrieval.proposed.ttl"):
    g = Graph()
    g.parse("D:/agentABC/wt/r-qa-integration/doc/_qa/knowledge-gap/" + path, format="turtle")
    subjects = {s for s in g.subjects() if str(s).startswith(TARGET)}
    classes = {s for s in g.subjects(RDF.type, URIRef("http://www.w3.org/2002/07/owl#Class"))
               if str(s).startswith(TARGET)}
    props = {s for s in g.subjects(RDF.type, URIRef("http://www.w3.org/2002/07/owl#ObjectProperty"))
             if str(s).startswith(TARGET)} | \
            {s for s in g.subjects(RDF.type, URIRef("http://www.w3.org/2002/07/owl#DatatypeProperty"))
             if str(s).startswith(TARGET)}
    anchors = list(g.subject_objects(URIRef(TERM + "termBatch")))
    tagged = [o for _, o in g.subject_objects(SKOS.altLabel) if isinstance(o, Literal) and o.language]
    untagged = [o for _, o in g.subject_objects(SKOS.altLabel) if isinstance(o, Literal) and not o.language]
    entries = list(g.subjects(RDF.type, URIRef(TERM + "TermEntry")))
    print(f"{path}: triples={len(g)} classes={len(classes)} props={len(props)} "
          f"anchors={len(anchors)} taggedAlt={len(tagged)} untaggedAlt={len(untagged)} entries={len(entries)}")
    print("  classes:", sorted(str(c).rsplit('#', 1)[-1] for c in classes))
    print("  props  :", sorted(str(p).rsplit('#', 1)[-1] for p in props))
