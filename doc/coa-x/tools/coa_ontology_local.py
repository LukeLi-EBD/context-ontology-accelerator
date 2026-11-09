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
                                                    # (re)load fsldm-merged.ttl
                                                    # and write its registry row

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

TTL_PATH = REPO / "doc/_fsldm/fsldm-merged.ttl"

# Exact counts of doc/_fsldm/fsldm-merged.ttl (rdflib, 2026-11-09).
EXPECTED_TRIPLES = 2675
EXPECTED_CLASSES = 156
EXPECTED_OBJECT_PROPERTIES = 84
EXPECTED_DATATYPE_PROPERTIES = 45


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


def seed(namespace: str) -> dict:
    """Load the merged FSLDM TTL into its own named graph, then register it."""
    from rdflib import OWL, RDF, Graph

    from coa_local_providers.ontology_oxigraph import replace_graph_turtle
    from coa_local_providers.ontology_registry_pg import put_ontology_registry
    from coa_ontology.stores import neptune_db_graph as ndb

    if not TTL_PATH.is_file():
        raise SystemExit(f"FATAL: TTL not found: {TTL_PATH}")

    g = Graph()
    g.parse(str(TTL_PATH), format="turtle")
    triples = len(g)
    classes = sum(1 for _ in g.triples((None, RDF.type, OWL.Class)))
    object_properties = sum(1 for _ in g.triples((None, RDF.type, OWL.ObjectProperty)))
    datatype_properties = sum(1 for _ in g.triples((None, RDF.type, OWL.DatatypeProperty)))
    ontology_id = next((str(s) for s in g.subjects(RDF.type, OWL.Ontology)), None)
    if not ontology_id:
        raise SystemExit("FATAL: fsldm-merged.ttl has no owl:Ontology subject")

    actual = {
        "triples": triples,
        "classes": classes,
        "object_properties": object_properties,
        "datatype_properties": datatype_properties,
    }
    expected = {
        "triples": EXPECTED_TRIPLES,
        "classes": EXPECTED_CLASSES,
        "object_properties": EXPECTED_OBJECT_PROPERTIES,
        "datatype_properties": EXPECTED_DATATYPE_PROPERTIES,
    }
    if actual != expected:
        raise SystemExit(f"FATAL: fsldm-merged.ttl does not match the pinned counts: {actual} != {expected}")

    graph_uri = ndb._ontology_graph_uri(ontology_id, namespace)
    replace_graph_turtle(graph_uri, TTL_PATH.read_text(encoding="utf-8"))

    stored = {
        "triples": _sparql_count(graph_uri, "?s ?p ?o"),
        "classes": _sparql_count(graph_uri, "?c a owl:Class"),
        "object_properties": _sparql_count(graph_uri, "?p a owl:ObjectProperty"),
        "datatype_properties": _sparql_count(graph_uri, "?p a owl:DatatypeProperty"),
    }
    if stored != expected:
        raise SystemExit(f"FATAL: graph store read-back does not match the TTL: {stored} != {expected}")

    row = put_ontology_registry(
        namespace,
        ontology_id,
        {
            "uri": ontology_id,
            "title": "FSLDM merged ontology (15 modules)",
            "description": (
                "FS-LDM 合并本体：15 个 owl:Ontology 模块、2675 三元组，"
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
    parser.add_argument("--seed", action="store_true", help="load fsldm-merged.ttl into its named graph")
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
