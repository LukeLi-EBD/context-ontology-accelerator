"""Local composition root for the COA ontology-engine (port 8101).

Upstream ``coa_ontology.main`` is an AWS service: DynamoDB registry, Neptune DB
graph store, OpenSearch Serverless vectors, Bedrock embeddings. Locally we keep
the same code paths and swap only the transports/providers at process start:

    COA_PROVIDER_ONTOLOGY_GRAPH     oxigraph | neptune     (required)
    COA_PROVIDER_ONTOLOGY_REGISTRY  postgres | dynamodb    (required)
    COA_PROVIDER_ONTOLOGY_JOBS      postgres | dynamodb    (required)
    COA_PROVIDER_ONTOLOGY_OBJECTS   fs | s3                (required)
    COA_PROVIDER_ONTOLOGY_VECTOR    pgvector | opensearch  (required)
    COA_PROVIDER_ONTOLOGY_EMBEDDING http | bedrock         (required)
    COA_ONTOLOGY_OXIGRAPH_URL       required for oxigraph
    COA_CONTROL_PLANE_PG_DSN        required for postgres/pgvector
    COA_LOCAL_OBJECT_ROOT           required for fs
    COA_EMBEDDING_URL               required for http (default 8081/v1)
    DYNAMODB_TABLE                  logical registry table name

No provider has a default: missing keys abort startup with an explicit error.
The graph transport reuses the Oxigraph instance already backing the metric
graph (7878). Ontologies live in their own named graph under
``NDB_GRAPH_URI_BASE``; they never mix with ``urn:coa-metrics:``.

Usage:
    python coa_ontology_local.py                    # serve on 127.0.0.1:8101
    python coa_ontology_local.py --seed --namespace <uuid>
                                                    # (re)load merged + terms + metrics
                                                    # folios and write the registry row

The seed is read-only from the engine's point of view: it writes the TTL into
one named graph and one registry row. Induction/ingest (write path) is out of
scope and keeps its upstream AWS implementation.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TOOLS = Path(__file__).resolve().parent

_PACKAGES = [
    REPO / "packages/ontology-engine/src",
    REPO / "packages/control-plane/src",
    REPO / "packages/sources/src",
    REPO / "packages/metric-service/src",
    REPO / "packages/platform-core/src",
    REPO / "packages/local-providers/src",
    REPO / "libs/common/src",
    REPO / "smithy-generated/control-plane-python-server",
]
for _p in reversed(_PACKAGES):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

_FSLDM = REPO / "doc/_fsldm"

# The T-Box is three folios, not one file. A total-only assertion (2675) passed
# while two folios were silently missing, so each folio is pinned on its own:
# triple count plus the predicates that make it useful. Missing or drifted
# folio aborts the seed before anything is written.
FOLIOS: tuple[dict, ...] = (
    {
        "name": "merged",
        "path": _FSLDM / "fsldm-merged.ttl",
        "triples": 2675,
        "assert": {
            "classes": ("?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class>", 156),
            "objectProperties": (
                "?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#ObjectProperty>",
                84,
            ),
            "datatypeProperties": (
                "?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#DatatypeProperty>",
                45,
            ),
            "altLabels": ("?s <http://www.w3.org/2004/02/skos/core#altLabel> ?o", 146),
        },
    },
    {
        "name": "terms",
        "path": _FSLDM / "fsldm-terms.ttl",
        "triples": 285,
        "assert": {
            "termEntries": (
                "?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://w3id.org/fsldm/terms#TermEntry>",
                18,
            ),
            "termLabels": ("?s <https://w3id.org/fsldm/terms#label> ?o", 18),
            "termForClass": ("?s <https://w3id.org/fsldm/terms#forClass> ?o", 18),
            "termStatus": ("?s <https://w3id.org/fsldm/terms#status> ?o", 18),
            "termGuardRegex": ("?s <https://w3id.org/fsldm/terms#guardRegex> ?o", 3),
            "altLabelSubjects": ("?s <http://www.w3.org/2004/02/skos/core#altLabel> ?o", 15),
        },
    },
    {
        "name": "metrics",
        "path": _FSLDM / "fsldm-metrics.ttl",
        "triples": 664,
        "assert": {
            "metricConcepts": (
                "?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> "
                "<http://www.w3.org/2004/02/skos/core#Concept> ; "
                "<http://www.w3.org/2004/02/skos/core#inScheme> "
                "<https://w3id.org/fsldm/terms#MetricScheme>",
                85,
            ),
            "metricNotations": (
                "?s <http://www.w3.org/2004/02/skos/core#notation> ?o ; "
                "<http://www.w3.org/2004/02/skos/core#inScheme> "
                "<https://w3id.org/fsldm/terms#MetricScheme>",
                85,
            ),
            "metricDefinitions": (
                "?s <http://www.w3.org/2004/02/skos/core#definition> ?o ; "
                "<http://www.w3.org/2004/02/skos/core#inScheme> "
                "<https://w3id.org/fsldm/terms#MetricScheme>",
                85,
            ),
        },
    },
)

# Union read-back: covers cross-folio totals that no single file can prove.
EXPECTED_UNION = {
    "triples": 3624,
    "termTriples": ("?s <https://w3id.org/fsldm/terms#label> ?o", 18),
    "metricConcepts": (
        "?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> "
        "<http://www.w3.org/2004/02/skos/core#Concept> ; "
        "<http://www.w3.org/2004/02/skos/core#inScheme> "
        "<https://w3id.org/fsldm/terms#MetricScheme>",
        85,
    ),
    "altLabels": ("?s <http://www.w3.org/2004/02/skos/core#altLabel> ?o", 217),
}


def _configure_environment() -> None:
    """Local, non-secret defaults. Provider selection is never defaulted."""
    defaults = {
        "AWS_REGION": "us-east-1",
        "RESOURCE_PREFIX": "coa-local-",
        # Avoid the STS account lookup in dynamo_store.resolve_ontology_bucket();
        # local runs never touch S3.
        "ONTOLOGY_ARTIFACTS_BUCKET": "coa-local-ontology-artifacts",
        "DYNAMODB_DEFAULT_NAMESPACE": "default",
        "ALLOWED_ORIGIN": "http://127.0.0.1:5173",
        "NDB_REGION": "us-east-1",
        # Local object store (COA_PROVIDER_ONTOLOGY_OBJECTS=fs). Keep artifact
        # bytes next to the stack's other run state instead of the repo.
        "COA_LOCAL_OBJECT_ROOT": str(Path(tempfile.gettempdir()) / "coa-local-stack" / "objects"),
        "COA_LOCAL_OBJECT_BASE": "http://127.0.0.1:8099/_local/objects",
        # Local embedding service (text-embeddings-inference on 8081).
        "COA_EMBEDDING_URL": "http://127.0.0.1:8081/v1",
        "COA_EMBEDDING_MODEL": "BAAI/bge-m3",
        "COA_EMBEDDING_DIMENSIONS": "1024",
        "COA_VECTOR_DIMENSIONS": "1024",
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)


def _require(key: str) -> str:
    value = os.environ.get(key, "").strip()
    if not value:
        raise SystemExit(f"FATAL: {key} is required (local ontology composition root)")
    return value


def _install_providers() -> tuple[str, str, str, str, str, str]:
    from coa_local_providers.local_s3 import install_local_s3
    from coa_local_providers.ontology_embedding_http import install_http_embeddings
    from coa_local_providers.ontology_jobs_pg import install_ontology_jobs
    from coa_local_providers.ontology_oxigraph import install_ontology_graph_transport
    from coa_local_providers.ontology_registry_pg import install_ontology_registry
    from coa_local_providers.ontology_vectors_pg import install_pg_vector_store

    graph = install_ontology_graph_transport()
    registry = install_ontology_registry()
    jobs = install_ontology_jobs()
    objects = install_local_s3()
    vectors = install_pg_vector_store()
    embeddings = install_http_embeddings()
    return graph, registry, jobs, objects, vectors, embeddings


def _sparql_count(graph_uri: str, pattern: str) -> int:
    from coa_local_providers.ontology_oxigraph import sparql_query

    query = (
        "PREFIX owl: <http://www.w3.org/2002/07/owl#>\n"
        f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{graph_uri}> {{ {pattern} }} }}"
    )
    body = sparql_query(query)
    return int(body["results"]["bindings"][0]["n"]["value"])


def _assert_folio(folio: dict) -> None:
    """Parse one folio and pin its triple count plus its key predicates."""
    from rdflib import Graph

    path: Path = folio["path"]
    if not path.is_file():
        raise SystemExit(f"FATAL: folio missing: {path.name} ({path})")
    g = Graph()
    g.parse(str(path), format="turtle")
    actual = {"triples": len(g)}
    for key, (pattern, _expected) in folio["assert"].items():
        actual[key] = _count_pattern(g, pattern)
    expected = {"triples": folio["triples"], **{k: v[1] for k, v in folio["assert"].items()}}
    if actual != expected:
        raise SystemExit(
            f"FATAL: folio {folio['name']} ({path.name}) does not match the pinned counts: "
            f"{actual} != {expected}"
        )


def _count_pattern(g, pattern: str) -> int:
    """Count subjects matching a fixed `?s <pred> ?o [; <pred> ?o]` pattern.

    Patterns come from FOLIOS constants, never from user input.
    """
    import re

    from rdflib import URIRef

    m = re.match(r"^(\?[a-z]+)\s+(.+)$", pattern.strip())
    if not m:
        raise SystemExit(f"FATAL: bad folio pattern: {pattern}")
    predicates: list[tuple[URIRef, URIRef | None]] = []
    for part in [p.strip() for p in m.group(2).split(" ; ")]:
        pm = re.match(r"^(<[^>]+>)\s+(<[^>]+>|\?[a-z]+)$", part)
        if not pm:
            raise SystemExit(f"FATAL: bad folio pattern: {pattern}")
        predicate = URIRef(pm.group(1)[1:-1])
        obj = pm.group(2)
        target = None if obj.startswith("?") else URIRef(obj[1:-1])
        predicates.append((predicate, target))
    matched = 0
    for subject in set(g.subjects()):
        if all(next(g.triples((subject, pred, target)), None) is not None for pred, target in predicates):
            matched += 1
    return matched


def seed(namespace: str) -> dict:
    """Load all FSLDM folios into one named graph, then register the version."""
    from rdflib import OWL, RDF, Graph

    from coa_local_providers.ontology_oxigraph import replace_graph_turtle
    from coa_local_providers.ontology_registry_pg import put_ontology_registry
    from coa_ontology.stores import neptune_db_graph as ndb

    merged = Graph()
    for folio in FOLIOS:
        _assert_folio(folio)
        merged.parse(str(folio["path"]), format="turtle")

    ontology_id = next((str(s) for s in merged.subjects(RDF.type, OWL.Ontology)), None)
    if not ontology_id:
        raise SystemExit("FATAL: FSLDM folios have no owl:Ontology subject")

    graph_uri = ndb._ontology_graph_uri(ontology_id, namespace)
    replace_graph_turtle(graph_uri, merged.serialize(format="turtle"))

    stored = {
        "triples": _sparql_count(graph_uri, "?s ?p ?o"),
        "classes": _sparql_count(graph_uri, "?s a <http://www.w3.org/2002/07/owl#Class>"),
        "object_properties": _sparql_count(graph_uri, "?s a <http://www.w3.org/2002/07/owl#ObjectProperty>"),
        "datatype_properties": _sparql_count(graph_uri, "?s a <http://www.w3.org/2002/07/owl#DatatypeProperty>"),
    }
    if stored["triples"] != EXPECTED_UNION["triples"]:
        raise SystemExit(
            f"FATAL: graph store read-back has {stored['triples']} triples, "
            f"expected {EXPECTED_UNION['triples']} (a folio was dropped)"
        )
    for key, spec in EXPECTED_UNION.items():
        if key == "triples":
            continue
        pattern, count = spec
        got = _sparql_count(graph_uri, pattern)
        if got != count:
            raise SystemExit(f"FATAL: union check {key} read back {got}, expected {count}")

    row = put_ontology_registry(
        namespace,
        ontology_id,
        {
            "uri": ontology_id,
            "title": "FSLDM merged ontology + terms/metrics folios",
            "description": (
                "FS-LDM 本体三分册合并：merged(2675) + terms(285) + metrics(664) = 3624 三元组，"
                "本地由单个命名图承载（读取链路）。"
            ),
            "ontology_type": "foundational",
            "format": "turtle",
            "source_registry": "local-fsldm",
            "class_count": stored["classes"],
            "property_count": stored["object_properties"] + stored["datatype_properties"],
            "axiom_count": stored["triples"],
            "graph_uri": graph_uri,
            "domain_tags": [],
        },
    )
    return {
        "namespace": namespace,
        "ontology_id": ontology_id,
        "graph_uri": graph_uri,
        "counts": stored,
        "registry": {k: row[k] for k in ("ontology_id", "uri", "title", "ontology_type", "class_count")},
    }


def _require_all_providers() -> None:
    for key in (
        "COA_PROVIDER_ONTOLOGY_GRAPH",
        "COA_PROVIDER_ONTOLOGY_REGISTRY",
        "COA_PROVIDER_ONTOLOGY_JOBS",
        "COA_PROVIDER_ONTOLOGY_OBJECTS",
        "COA_PROVIDER_ONTOLOGY_VECTOR",
        "COA_PROVIDER_ONTOLOGY_EMBEDDING",
    ):
        _require(key)


def serve() -> None:
    import uvicorn

    _require_all_providers()
    graph, registry, jobs, objects, vectors, embeddings = _install_providers()
    print(
        f"[coa-ontology-local] graph={graph} registry={registry} jobs={jobs} "
        f"objects={objects} vectors={vectors} embeddings={embeddings}",
        flush=True,
    )

    from coa_ontology.main import app

    host = os.environ.get("COA_ONTOLOGY_HOST", "127.0.0.1")
    port = int(os.environ.get("COA_ONTOLOGY_PORT", "8101"))
    uvicorn.run(app, host=host, port=port, log_level=os.environ.get("LOG_LEVEL", "info").lower())


def main(argv: list[str] | None = None) -> None:
    _configure_environment()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", action="store_true", help="load all FSLDM folios into its named graph")
    parser.add_argument("--namespace", default="", help="namespace UUID (required with --seed)")
    args = parser.parse_args(argv)

    if args.seed:
        if not args.namespace:
            raise SystemExit("FATAL: --namespace <uuid> is required with --seed")
        _require_all_providers()
        _install_providers()
        result = seed(args.namespace)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    serve()


if __name__ == "__main__":
    main()
