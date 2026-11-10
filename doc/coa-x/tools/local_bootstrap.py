"""Local end-to-end bootstrap for the COA query chain (no AWS).

Subcommands are the three prerequisites the chain needs before it can answer:

    migrate    run platform-core's real migrations against the local PG
    seed       insert two real FS-LDM chunks and their BGE vectors, then search
    ontology   load doc/_fsldm into the local Oxigraph graph Tier-2 reads
    check      re-assert every prerequisite without changing anything

Usage:
    python local_bootstrap.py migrate  --dsn postgresql://...
    python local_bootstrap.py seed     --dsn postgresql://...
    python local_bootstrap.py ontology --oxigraph http://127.0.0.1:7878 --namespace <uuid>
    python local_bootstrap.py check    --dsn ... --oxigraph ... --namespace ...

The script is deliberately idempotent: re-running it converges, it never
duplicates rows, and it never deletes anything it did not create.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

# Resolve the repository root from this file, never hard-code the main tree:
# a worktree must migrate with its own ``platform_core`` (its own migration
# registry), otherwise the branch's V48 is never applied and the run silently
# reuses main's version.
REPO = str(Path(__file__).resolve().parents[3])
for _rel in ("packages/platform-core/src", "libs/common/src"):
    _path = str(Path(REPO) / _rel)
    if _path not in sys.path:
        sys.path.insert(0, _path)

MODEL = "BAAI/bge-m3"
DIMENSIONS = 1024
EMBED_ENDPOINT = "http://127.0.0.1:8081"
DOCUMENT_ID = uuid.uuid5(uuid.NAMESPACE_URL, "coa-phase3-seed-document").hex
QUERY = "FS-LDM 中，一个人既是客户又是员工时，客户单一视图是怎么建模的？"

CHUNKS = [
    (
        "FS-LDM 中的当事人（PARTY）",
        "银行所服务的任意对象，以及感兴趣进行分析的各种对象：个人、机构、家庭、潜在客户、代理机构、雇员、分行、部门。"
        "同一个当事人可同时承担多种角色。一个自然人既是客户又是员工时，PARTY 只有一条实例，角色差异由 "
        "RoleAssignment 角色关联承载 —— 这是 FS-LDM 建立客户单一视图的根基。FS-LDM 的建模决策是：角色不入类，"
        "不为“客户”“员工”各建一个类，而用角色关联表达，避免类爆炸与多重身份冲突。",
    ),
    (
        "FS-LDM 中的协议（AGREEMENT）",
        "金融机构与当事人之间针对特定产品或服务签立的契约关系。账户、保单、贷款合同、信用证、担保合同都是它的具体形态。"
        "原文：This entity contains information about agreements between two or more parties。v7 中 ACCOUNT / POLICY "
        "是它的物理子类型；v10 中二者已无独立物理表，但逻辑上仍是它的子类。",
    ),
    (
        "FS-LDM 中的角色关联（ROLE ASSIGNMENT）",
        "角色关联把当事人与协议、资产、位置等对象连接起来，并记录该当事人在这个连接上承担的角色。"
        "例如账户持有人（Account Holder）对账户拥有完整权利，同一账户可有多名持有人（联名户），但只能有一名主持有人；"
        "共同持有人（Joint Holder）与账户持有人共享账户权利。同一件资产也可以同时是保险标的、贷款抵抵押物、被收回对象 —— "
        "这是“一件资产、多个角色”的典型，因此资产与协议、与当事人的连接必须建模为角色关联。",
    ),
]

MAPPED_CLASSES = (
    "BusinessEntity",
    "Party",
    "Agreement",
    "Product",
    "RoleAssignment",
)


def _embed(text: str) -> list[float]:
    body = json.dumps({"inputs": text}).encode("utf-8")
    req = urllib.request.Request(
        f"{EMBED_ENDPOINT}/embed",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    vector = payload[0] if isinstance(payload, list) else payload["value"][0]
    if len(vector) != DIMENSIONS:
        raise SystemExit(f"embedding dimension {len(vector)} != {DIMENSIONS}")
    return vector


def _meta(dsn: str):
    from platform_core.adapters.metadata_pg import MetadataPg

    meta = MetadataPg(dsn, pool_max=2)
    meta.open(retry_seconds=15)
    return meta


def cmd_migrate(args: argparse.Namespace) -> None:
    meta = _meta(args.dsn)
    try:
        print("migrate:", json.dumps(meta.migrate(), ensure_ascii=False))
        version = meta.query("SELECT MAX(version) AS v FROM platform.schema_version")[0]["v"]
        tables = {
            row["table_name"]
            for row in meta.query(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='platform'"
            )
        }
        required = {"document", "document_chunk", "chunk_embedding", "embedding_pointer"}
        missing = required - tables
        if missing:
            raise SystemExit(f"migration did not create: {sorted(missing)}")
        print(f"schema_version={version} platform_tables={len(tables)} required_tables=ok")
    finally:
        meta.close()


def cmd_seed(args: argparse.Namespace) -> None:
    from platform_core.adapters.vector_pg import PgVectorStore
    from platform_core.config import EmbeddingConfig

    meta = _meta(args.dsn)
    try:
        with meta.tx() as tx:
            tx.execute(
                """
                INSERT INTO platform.document (
                    document_id, sha256, bucket, object_key, filename, mime_type,
                    size_bytes, status, page_count, char_count, chunk_count,
                    parser, parser_version
                ) VALUES (%s,%s,'local','phase3/fsldm-concepts.md','fsldm-concepts.md',
                          'text/markdown',%s,'parsed',1,%s,%s,'local-md','1')
                ON CONFLICT (document_id) DO NOTHING
                """,
                (
                    DOCUMENT_ID,
                    DOCUMENT_ID,
                    sum(len(text.encode("utf-8")) for _, text in CHUNKS),
                    sum(len(text) for _, text in CHUNKS),
                    len(CHUNKS),
                ),
            )
            for seq, (_, text) in enumerate(CHUNKS):
                tx.execute(
                    """
                    INSERT INTO platform.document_chunk (
                        chunk_id, document_id, seq, page_from, page_to,
                        char_start, char_end, text, token_estimate
                    ) VALUES (%s,%s,%s,1,1,0,%s,%s,%s)
                    ON CONFLICT (chunk_id) DO NOTHING
                    """,
                    (
                        f"phase3-chunk-{seq}",
                        DOCUMENT_ID,
                        seq,
                        len(text),
                        text,
                        max(1, len(text) // 4),
                    ),
                )
            # A fresh pointer row matters: the store guards every write and read
            # against the active partition, so an empty table means no retrieval.
            tx.execute(
                """
                INSERT INTO platform.embedding_pointer (id, provider, model, dimensions)
                VALUES (true, 'local-bge', %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (MODEL, DIMENSIONS),
            )

        store = PgVectorStore(
            meta, EmbeddingConfig(provider="local-bge", model=MODEL, dimensions=DIMENSIONS)
        )
        items = [
            {"chunkId": f"phase3-chunk-{seq}", "vector": _embed(text)}
            for seq, (_, text) in enumerate(CHUNKS)
        ]
        print("upsert:", json.dumps(store.upsert(DOCUMENT_ID, items, MODEL), ensure_ascii=False))
        hits = store.search(_embed(QUERY), MODEL, 3)
        for hit in hits:
            print(
                "hit:",
                json.dumps(
                    {
                        "chunkId": hit["chunkId"],
                        "score": round(hit["score"], 4),
                        "text": hit["text"][:40],
                    },
                    ensure_ascii=False,
                ),
            )
        if not hits:
            raise SystemExit("vector search returned nothing after seeding")
        print(f"pointer={store.pointer()} chunks={store.count(MODEL)}")
    finally:
        meta.close()


def _gsp(base: str, method: str, graph: str, body: bytes | None = None) -> int:
    url = f"{base}/store?graph={urllib.parse.quote(graph, safe='')}"
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "text/turtle"}, method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


def _sparql(base: str, query: str) -> dict:
    req = urllib.request.Request(
        f"{base}/query",
        data=query.encode("utf-8"),
        headers={
            "Content-Type": "application/sparql-query",
            "Accept": "application/sparql-results+json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _graph_uri(namespace: str) -> str:
    return f"https://ontology.local/{namespace}/ontology"


def _prefix(namespace: str) -> str:
    return f"https://ontology.local/{namespace}/"


def _seed_ttl(namespace: str) -> bytes:
    vocab = "http://coa.amazon.com/vocab/coa#"
    mapped = "\n".join(
        f"<https://w3id.org/fsldm/core#{name}> <{vocab}isMapped> true ."
        for name in MAPPED_CLASSES
    )
    return f"""@prefix fsldm: <https://w3id.org/fsldm/core#> .
@prefix coa: <{vocab}> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# Minimal queryable markers: FS-LDM core classes answerable via the SQL backend.
# No coa:queryBackend means SQL, matching platform backend_gate semantics.
{mapped}

fsldm:partyName a owl:DatatypeProperty ;
    rdfs:domain fsldm:Party ;
    rdfs:label "当事人名称"@zh ;
    rdfs:range xsd:string .

fsldm:party-0001 a fsldm:Party ;
    rdfs:label "张伟"@zh ;
    fsldm:partyName "张伟" .
fsldm:agreement-0001 a fsldm:Agreement ;
    rdfs:label "个人结算账户 A-001"@zh .
fsldm:role-0001 a fsldm:RoleAssignment ;
    rdfs:label "账户持有人"@zh .
""".encode("utf-8")


def cmd_ontology(args: argparse.Namespace) -> None:
    from rdflib import OWL, RDF, Graph

    graph_uri = _graph_uri(args.namespace)
    print("clear stale:", _gsp(args.oxigraph, "DELETE", f"https://ontology.local/{args.namespace}"))
    print("clear target:", _gsp(args.oxigraph, "DELETE", graph_uri))

    source = f"{REPO}/doc/_fsldm/fsldm-merged.ttl"
    graph = Graph()
    graph.parse(source, format="turtle")
    parsed = len(graph)
    # Tier-2 resolves a namespace's graph IRIs by discovering `?ont a owl:Ontology`
    # and then inlines them as constant `GRAPH <iri>` blocks. The local Oxigraph
    # adapter only permits constant graph blocks for `urn:platform:`, so dropping
    # the ontology declarations keeps Tier-2 on the prefix-filter path that it
    # answers. The vocabulary's classes and properties are untouched.
    for triple in list(graph.triples((None, RDF.type, OWL.Ontology))):
        graph.remove(triple)
    print(f"ontology triples: parsed={parsed} kept={len(graph)}")
    print("load ontology:", _gsp(args.oxigraph, "POST", graph_uri, graph.serialize(format="turtle").encode()))
    print("load seed:", _gsp(args.oxigraph, "POST", graph_uri, _seed_ttl(args.namespace)))

    count = _sparql(
        args.oxigraph,
        f"""PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT (COUNT(DISTINCT ?class) AS ?cnt) WHERE {{
          GRAPH ?g {{
            ?class a owl:Class .
            ?class <http://coa.amazon.com/vocab/coa#isMapped> true .
            FILTER NOT EXISTS {{ ?class <http://coa.amazon.com/vocab/coa#queryBackend> "RDF_SPARQL" . }}
          }}
          FILTER(STRSTARTS(STR(?g), "{_prefix(args.namespace)}"))
        }}""",
    )
    mapped = int(count["results"]["bindings"][0]["cnt"]["value"])
    print(f"mapped_sql_classes={mapped}")
    if mapped == 0:
        raise SystemExit("Tier-2 would see no mapped classes")


def cmd_check(args: argparse.Namespace) -> None:
    meta = _meta(args.dsn)
    try:
        version = meta.query("SELECT MAX(version) AS v FROM platform.schema_version")[0]["v"]
        pointer = meta.query("SELECT provider, model, dimensions FROM platform.embedding_pointer")
        chunks = meta.query("SELECT COUNT(*) AS n FROM platform.document_chunk")[0]["n"]
        vectors = meta.query("SELECT COUNT(*) AS n FROM platform.chunk_embedding")[0]["n"]
        print(f"pg: schema_version={version} chunks={chunks} vectors={vectors} pointer={pointer}")
        if not pointer or not vectors:
            raise SystemExit("pg: embedding pointer or vectors missing")
    finally:
        meta.close()

    ttl = _sparql(
        args.oxigraph,
        f"""PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT (COUNT(*) AS ?cnt) WHERE {{
          GRAPH ?g {{
            ?class a owl:Class .
            ?class <http://coa.amazon.com/vocab/coa#isMapped> true .
          }}
          FILTER(STRSTARTS(STR(?g), "{_prefix(args.namespace)}"))
        }}""",
    )
    mapped = int(ttl["results"]["bindings"][0]["cnt"]["value"])
    print(f"graph: mapped_classes={mapped}")
    if mapped == 0:
        raise SystemExit("graph: no mapped classes")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("migrate", "seed", "check"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--dsn", required=True)
        if name == "check":
            cmd.add_argument("--oxigraph", required=True)
            cmd.add_argument("--namespace", required=True)
    ont = sub.add_parser("ontology")
    ont.add_argument("--oxigraph", required=True)
    ont.add_argument("--namespace", required=True)

    args = parser.parse_args()
    {
        "migrate": cmd_migrate,
        "seed": cmd_seed,
        "ontology": cmd_ontology,
        "check": cmd_check,
    }[args.command](args)


if __name__ == "__main__":
    main()
