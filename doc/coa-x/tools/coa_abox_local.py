"""Read-only A-Box export from the running 8080 platform into the local COA graph.

The platform instance at ``127.0.0.1:8080`` keeps its materialised A-Box in a
named graph of its own Oxigraph (``urn:platform:graph:abox:synthetic``,
304,919 triples / 60,525 subjects on 2026-11-09). That graph is only reachable
from inside the compose network, so this tool runs *queries* through
``docker exec`` against the already-running ``agent-platform-api`` container and
never writes to it, restarts it, or publishes ports.

What gets imported is a class-scoped slice of the agreement namespace — the four
classes whose per-class instance counts can be checked one-for-one against the
platform's own PostgreSQL tables:

    https://w3id.org/fsldm/agreement#Policy             <- platform.ins_policy             (6000)
    https://w3id.org/fsldm/agreement#CreditAgreement    <- platform.bank_loan_account       (5020)
    https://w3id.org/fsldm/agreement#Account            <- platform.bank_deposit_account    (5000)
    https://w3id.org/fsldm/agreement#Application        <- platform.bank_credit_application (2000)

Only triples whose *subject* is an instance of one of those classes are taken.
Object references (``core#hasParty``, ``core#hasMetric``, ...) therefore point
at instances outside the slice that are deliberately left unloaded; nothing is
invented to close them.

Verification is symmetric and fails closed:

    1. per-class counts read from the source graph   == per-class counts in PG
    2. per-class counts parsed from the exported TTL == per-class counts in the source graph
    3. per-class counts read back from the COA store == per-class counts in the TTL

Any inequality aborts with a non-zero exit before/after the write. The COA
target is its own named graph; it never mixes with the FSLDM T-Box graph or
``urn:coa-metrics:``.

Usage (host, from the repo root, with the local stack up):

    .\\.venv-coa-local\\Scripts\\python.exe doc/coa-x/tools/coa_abox_local.py --namespace <uuid>
    ... --dry-run        # export + verify, do not write to the COA graph
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

import httpx

REPO = Path(__file__).resolve().parents[3]

# Source (8080) — read-only.
SOURCE_CONTAINER = "agent-platform-api"
SOURCE_OXIGRAPH = "http://oxigraph:7878"
SOURCE_GRAPH = "urn:platform:graph:abox:synthetic"
PG_CONTAINER = "agent-platform-postgres"
PG_DATABASE = "platform"

# Target (local COA) — must match NDB_GRAPH_URI_BASE in 10-本地起栈.ps1.
COA_OXIGRAPH_URL = os.environ.get("COA_ONTOLOGY_OXIGRAPH_URL", "http://127.0.0.1:7878")
COA_GRAPH_URI_BASE = os.environ.get("NDB_GRAPH_URI_BASE", "https://coa.local/graph")

ABOX_ONTOLOGY_ID = "urn:coa:abox:platform-synthetic"

PREFIX = "https://w3id.org/fsldm/agreement#"

# class IRI -> platform table whose row count must equal the instance count.
CLASSES: dict[str, str] = {
    f"{PREFIX}Policy": "ins_policy",
    f"{PREFIX}CreditAgreement": "bank_loan_account",
    f"{PREFIX}Account": "bank_deposit_account",
    f"{PREFIX}Application": "bank_credit_application",
}

# Fixed on 2026-11-09; a change here means the platform data moved, which must
# be reported rather than absorbed silently.
EXPECTED_COUNTS = {
    f"{PREFIX}Policy": 6000,
    f"{PREFIX}CreditAgreement": 5020,
    f"{PREFIX}Account": 5000,
    f"{PREFIX}Application": 2000,
}

_RUNNER = """
import sys, urllib.request
query = sys.stdin.buffer.read()
accept = sys.argv[1] if len(sys.argv) > 1 else "application/sparql-results+json"
req = urllib.request.Request(
    "%(endpoint)s/query",
    data=query,
    headers={"Content-Type": "application/sparql-query", "Accept": accept},
)
sys.stdout.buffer.write(urllib.request.urlopen(req, timeout=600).read())
""" % {"endpoint": SOURCE_OXIGRAPH}


def _fail(message: str) -> None:
    raise SystemExit(f"FATAL: {message}")


def _run_source_query(sparql: str, accept: str) -> str:
    """Run one read-only SPARQL query inside the platform network."""
    proc = subprocess.run(
        ["docker", "exec", "-i", SOURCE_CONTAINER, "python", "-c", _RUNNER, accept],
        input=sparql.encode("utf-8"),
        capture_output=True,
    )
    if proc.returncode != 0:
        _fail(f"source query failed: {proc.stderr.decode('utf-8', 'replace')[:800]}")
    return proc.stdout.decode("utf-8")


def _values() -> str:
    return " ".join(f"<{c}>" for c in CLASSES)


def source_counts() -> dict[str, int]:
    sparql = (
        "SELECT ?c (COUNT(DISTINCT ?s) AS ?n) WHERE { "
        f"GRAPH <{SOURCE_GRAPH}> {{ ?s a ?c . VALUES ?c {{ {_values()} }} }} "
        "} GROUP BY ?c"
    )
    body = json.loads(_run_source_query(sparql, "application/sparql-results+json"))
    return {b["c"]["value"]: int(b["n"]["value"]) for b in body["results"]["bindings"]}


def source_triples() -> int:
    sparql = (
        "SELECT (COUNT(*) AS ?n) WHERE { "
        f"GRAPH <{SOURCE_GRAPH}> {{ ?s a ?c . VALUES ?c {{ {_values()} }} }} "
        f"GRAPH <{SOURCE_GRAPH}> {{ ?s ?p ?o }} "
        "}"
    )
    body = json.loads(_run_source_query(sparql, "application/sparql-results+json"))
    return int(body["results"]["bindings"][0]["n"]["value"])


def export_turtle() -> str:
    """Every triple whose subject instantiates one of the selected classes."""
    sparql = (
        f"CONSTRUCT {{ ?s ?p ?o }} WHERE {{ "
        f"GRAPH <{SOURCE_GRAPH}> {{ ?s a ?c . VALUES ?c {{ {_values()} }} }} "
        f"GRAPH <{SOURCE_GRAPH}> {{ ?s ?p ?o }} "
        "}"
    )
    turtle = _run_source_query(sparql, "text/turtle")
    if not turtle.strip():
        _fail("source CONSTRUCT returned no triples")
    return turtle


def pg_counts() -> dict[str, int]:
    union = " UNION ALL ".join(
        f"SELECT '{table}' AS t, COUNT(*) AS n FROM {PG_DATABASE}.{table}" for table in CLASSES.values()
    )
    proc = subprocess.run(
        ["docker", "exec", PG_CONTAINER, "psql", "-U", "platform", "-d", PG_DATABASE, "-Atc", union],
        capture_output=True,
    )
    if proc.returncode != 0:
        _fail(f"postgres count failed: {proc.stderr.decode('utf-8', 'replace')[:800]}")
    by_table = {}
    for line in proc.stdout.decode("utf-8").splitlines():
        table, _, n = line.partition("|")
        if table:
            by_table[table] = int(n)
    return {cls: by_table[table] for cls, table in CLASSES.items()}


def ttl_counts(turtle: str) -> tuple[dict[str, int], int]:
    from rdflib import RDF, Graph, URIRef

    g = Graph()
    g.parse(data=turtle, format="turtle")
    counts: dict[str, int] = {}
    for cls in CLASSES:
        counts[cls] = sum(1 for _ in g.subjects(RDF.type, URIRef(cls)))
    return counts, len(g)


def _diff(label: str, left: dict[str, int], right: dict[str, int]) -> None:
    if left != right:
        _fail(f"{label} mismatch: {left} != {right}")


def graph_uri(namespace: str) -> str:
    return f"{COA_GRAPH_URI_BASE}/{namespace}/{quote(ABOX_ONTOLOGY_ID, safe='')}"


def write_coa_graph(graph_uri_: str, turtle: str) -> None:
    url = f"{COA_OXIGRAPH_URL.rstrip('/')}/store?graph={quote(graph_uri_, safe='')}"
    reply = httpx.put(url, content=turtle.encode("utf-8"), headers={"Content-Type": "text/turtle"}, timeout=120)
    if reply.status_code >= 400:
        _fail(f"COA graph write failed ({reply.status_code}): {reply.text[:800]}")


def coa_counts(graph_uri_: str) -> tuple[dict[str, int], int]:
    def query(sparql: str) -> list[dict]:
        reply = httpx.post(
            f"{COA_OXIGRAPH_URL.rstrip('/')}/query",
            content=sparql.encode("utf-8"),
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/sparql-results+json",
            },
            timeout=120,
        )
        if reply.status_code >= 400:
            _fail(f"COA graph query failed ({reply.status_code}): {reply.text[:800]}")
        return reply.json()["results"]["bindings"]

    counts = {}
    for cls in CLASSES:
        rows = query(
            "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { "
            f"GRAPH <{graph_uri_}> {{ ?s a <{cls}> }} }}"
        )
        counts[cls] = int(rows[0]["n"]["value"])
    total = query(f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{graph_uri_}> {{ ?s ?p ?o }} }}")
    return counts, int(total[0]["n"]["value"])


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--namespace", required=True, help="COA namespace UUID")
    parser.add_argument("--dry-run", action="store_true", help="verify the export without writing")
    args = parser.parse_args(argv)

    src = source_counts()
    src_triples = source_triples()
    _diff("source class counts vs pinned expectations", src, EXPECTED_COUNTS)
    _diff("source class counts vs platform PostgreSQL rows", src, pg_counts())
    print(f"[source] {sum(src.values())} instances / {src_triples} triples: {src}", flush=True)

    turtle = export_turtle()
    exported, exported_triples = ttl_counts(turtle)
    _diff("exported TTL vs source graph", exported, src)
    if exported_triples != src_triples:
        _fail(f"exported TTL triples {exported_triples} != source {src_triples}")
    print(f"[export] {exported_triples} triples verified against the source graph", flush=True)

    target = graph_uri(args.namespace)
    if args.dry_run:
        print(f"[dry-run] would write {target}", flush=True)
        return

    write_coa_graph(target, turtle)
    stored, stored_triples = coa_counts(target)
    _diff("COA store vs exported TTL", stored, exported)
    if stored_triples != exported_triples:
        _fail(f"COA store triples {stored_triples} != exported {exported_triples}")

    print(
        json.dumps(
            {
                "namespace": args.namespace,
                "graph_uri": target,
                "ontology_id": ABOX_ONTOLOGY_ID,
                "instances": stored,
                "total_instances": sum(stored.values()),
                "triples": stored_triples,
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
