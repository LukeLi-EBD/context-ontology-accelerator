"""S7 read-mostly views for the minimal Web UI.

Boundary: this module only reads existing services (MetadataPg, Oxigraph,
SearchService, ExtractionService). It never writes triples and never duplicates
search fusion — the search page calls /context/resolve.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from .assembly import Runtime
from .errors import PortError

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
IRI_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:[^<>\"{}|^`\\\s]+$")


def _iri(value: str) -> bool:
    return bool(IRI_RE.match(value or ""))


def _local(iri: str) -> str:
    return re.split(r"[#/]", iri)[-1] or iri


def _values(binding: dict[str, Any]) -> dict[str, str]:
    result = {}
    for key, item in binding.get("values", {}).items():
        result[key] = str(item.get("value", item.get("iri", "")) or "")
    return result


def _graphs(runtime: Runtime, include_inferred: bool = True) -> list[str]:
    graphs: list[str] = []
    try:
        pointer = runtime.ontology.current()
        if pointer:
            graphs.append(str(pointer["graph"]))
    except PortError:
        pass
    if include_inferred:
        try:
            status = runtime.reasoning.status()
            pointer = status.get("pointer") or {}
            if pointer.get("targetGraph"):
                graphs.append(str(pointer["targetGraph"]))
        except PortError:
            pass
    graphs.extend(str(iri) for iri in runtime.config.reasoning.abox_graphs)
    return list(dict.fromkeys(graphs))


def _source_graphs(runtime: Runtime) -> list[str]:
    return _graphs(runtime, include_inferred=False)


def overview(runtime: Runtime) -> dict[str, Any]:
    named: list[dict[str, Any]] = []
    try:
        result = runtime.graph.query(
            "SELECT ?g (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } } GROUP BY ?g"
        )
        for binding in result["bindings"]:
            row = _values(binding)
            named.append({"iri": row.get("g", ""), "triples": int(row.get("n", 0) or 0)})
        named.sort(key=lambda item: item["triples"], reverse=True)
    except PortError as exc:
        named = [{"iri": "unavailable", "triples": 0, "error": exc.provider_code}]

    services = [
        _service("postgres", lambda: _probe_db(runtime)),
        _service("oxigraph", lambda: runtime.graph.ask("ASK {}")),
        _service("embedding", lambda: _probe_embedding(runtime)),
        _service("reasoner", lambda: bool(runtime.reasoner.health().get("available"))),
        _service("storage", lambda: _probe_storage(runtime)),
    ]

    ontology: dict[str, Any] = {}
    try:
        current = runtime.ontology.current()
        versions = runtime.ontology.list_versions()
        ontology = {
            "pointer": current,
            "versions": len(versions),
            "latest": versions[0] if versions else None,
        }
    except Exception as exc:  # keep the page usable when metadata is down
        ontology = {"error": str(exc)}

    counts: dict[str, Any] = {}
    try:
        documents = runtime.documents.counts()
        candidates = runtime.extraction.counts()
        search = runtime.search.counts()
        counts = {
            "documents": documents.get("documents", 0),
            "chunks": search.get("chunks", 0),
            "embeddings": search.get("embeddings", 0),
            "candidatesPending": candidates.get("pending", 0),
            "candidatesTotal": candidates.get("total", 0),
        }
    except Exception as exc:
        counts = {"error": str(exc)}

    reasoning: dict[str, Any] = {}
    try:
        reasoning = runtime.reasoning.status()
    except Exception as exc:
        reasoning = {"error": str(exc)}

    llm: dict[str, Any] = {}
    try:
        llm = {
            "provider": runtime.config.llm.provider,
            "model": runtime.config.llm.model or None,
            "baseUrl": runtime.config.llm.base_url or None,
            "configured": bool(runtime.llm.configured()),
        }
    except Exception as exc:  # keep the page usable when config is partial
        llm = {"error": str(exc)}

    return {
        "ontology": ontology,
        "graphs": named,
        "services": services,
        "counts": counts,
        "reasoning": reasoning,
        "llm": llm,
        "mode": runtime.config.mode,
        "degraded": runtime.degraded,
    }


def ontology(runtime: Runtime) -> dict[str, Any]:
    graphs = _source_graphs(runtime)
    points = " ".join(f"<{graph}>" for graph in graphs)
    classes: dict[str, dict[str, Any]] = {}
    if graphs:
        result = runtime.graph.query(
            f"""
            SELECT ?c ?label ?parent WHERE {{
              VALUES ?g {{ {points} }}
              GRAPH ?g {{
                ?c a ?kind .
                FILTER(?kind = <{OWL}Class> || ?kind = <{RDFS}Class>)
                OPTIONAL {{ ?c <{RDFS}label> ?label }}
                OPTIONAL {{ ?c <{RDFS}subClassOf> ?parent }}
              }}
            }}
            """
        )
        for binding in result["bindings"]:
            row = _values(binding)
            iri = row.get("c", "")
            if not iri:
                continue
            entry = classes.setdefault(
                iri, {"iri": iri, "label": row.get("label") or _local(iri), "parents": []}
            )
            if row.get("parent") and row["parent"] not in entry["parents"]:
                entry["parents"].append(row["parent"])
    properties: dict[str, dict[str, Any]] = {}
    if graphs:
        result = runtime.graph.query(
            f"""
            SELECT ?p ?label ?kind ?domain ?range WHERE {{
              VALUES ?g {{ {points} }}
              GRAPH ?g {{
                ?p a ?kind .
                FILTER(?kind = <{OWL}ObjectProperty> || ?kind = <{OWL}DatatypeProperty>
                       || ?kind = <{OWL}AnnotationProperty> || ?kind = <{RDF}Property>)
                OPTIONAL {{ ?p <{RDFS}label> ?label }}
                OPTIONAL {{ ?p <{RDFS}domain> ?domain }}
                OPTIONAL {{ ?p <{RDFS}range> ?range }}
              }}
            }}
            """
        )
        for binding in result["bindings"]:
            row = _values(binding)
            iri = row.get("p", "")
            if not iri:
                continue
            entry = properties.setdefault(
                iri,
                {
                    "iri": iri,
                    "label": row.get("label") or _local(iri),
                    "kind": _local(row.get("kind", "")),
                    "domain": [],
                    "range": [],
                },
            )
            if row.get("domain") and row["domain"] not in entry["domain"]:
                entry["domain"].append(row["domain"])
            if row.get("range") and row["range"] not in entry["range"]:
                entry["range"].append(row["range"])
    return {
        "graphs": graphs,
        "classes": sorted(classes.values(), key=lambda item: item["label"].lower()),
        "properties": sorted(properties.values(), key=lambda item: item["label"].lower()),
    }


def entities(runtime: Runtime, query: str, limit: int = 20) -> dict[str, Any]:
    graphs = _source_graphs(runtime)
    if not graphs:
        return {"query": query, "items": [], "graphs": []}
    points = " ".join(f"<{graph}>" for graph in graphs)
    text = (query or "").strip()
    if text:
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        filter_clause = (
            f'FILTER(CONTAINS(LCASE(STR(?label)), LCASE("{escaped}")) '
            f'|| CONTAINS(LCASE(STR(?s)), LCASE("{escaped}")))'
        )
        statement = f"""
            SELECT DISTINCT ?s ?label ?type WHERE {{
              VALUES ?g {{ {points} }}
              GRAPH ?g {{
                ?s <{RDFS}label> ?label .
                {filter_clause}
              }}
              OPTIONAL {{ GRAPH ?g2 {{ ?s a ?type }} }}
            }}
            LIMIT {max(1, min(limit, 100))}
        """
    else:
        statement = f"""
            SELECT DISTINCT ?s ?label ?type WHERE {{
              VALUES ?g {{ {points} }}
              GRAPH ?g {{ ?s a ?type . OPTIONAL {{ ?s <{RDFS}label> ?label }} }}
            }}
            LIMIT {max(1, min(limit, 100))}
        """
    result = runtime.graph.query(statement)
    items: dict[str, dict[str, Any]] = {}
    for binding in result["bindings"]:
        row = _values(binding)
        iri = row.get("s", "")
        if not iri:
            continue
        entry = items.setdefault(
            iri, {"iri": iri, "label": row.get("label") or _local(iri), "types": []}
        )
        if row.get("type") and row["type"] not in entry["types"]:
            entry["types"].append(row["type"])
    return {"query": text, "graphs": graphs, "items": list(items.values())}


def neighbors(runtime: Runtime, iri: str, limit: int = 50) -> dict[str, Any]:
    if not _iri(iri):
        raise PortError(
            code="InvalidArgument",
            message="entity must be an absolute IRI",
            provider="platform",
            provider_code="E_UI_BAD_IRI",
            details={"iri": iri},
        )
    graphs = _graphs(runtime)
    if not graphs:
        return {"iri": iri, "edges": [], "nodes": [], "graphs": []}
    points = " ".join(f"<{graph}>" for graph in graphs)
    result = runtime.graph.query(
        f"""
        SELECT ?s ?p ?o WHERE {{
          VALUES ?g {{ {points} }}
          GRAPH ?g {{
            {{ BIND(<{iri}> AS ?s) ?s ?p ?o }}
            UNION
            {{ ?s ?p <{iri}> }}
          }}
        }}
        LIMIT {max(1, min(limit, 200))}
        """
    )
    edges = []
    nodes: dict[str, dict[str, Any]] = {iri: {"iri": iri, "label": _local(iri)}}
    for binding in result["bindings"]:
        row = _values(binding)
        edge = {"s": row.get("s", ""), "p": row.get("p", ""), "o": row.get("o", "")}
        edges.append(edge)
        for key in ("s", "o"):
            term = edge[key]
            if term.startswith("http") or term.startswith("urn:"):
                nodes.setdefault(term, {"iri": term, "label": _local(term)})
    if nodes:
        values = " ".join(f"<{node}>" for node in nodes if _iri(node))
        labels = runtime.graph.query(
            f"""
            SELECT ?s ?label WHERE {{
              VALUES ?g {{ {points} }}
              VALUES ?s {{ {values} }}
              GRAPH ?g {{ ?s <{RDFS}label> ?label }}
            }}
            """
        )
        for binding in labels["bindings"]:
            row = _values(binding)
            if row.get("s") in nodes:
                nodes[row["s"]]["label"] = row.get("label") or nodes[row["s"]]["label"]
    return {"iri": iri, "graphs": graphs, "edges": edges, "nodes": list(nodes.values())}


def candidates_with_evidence(
    runtime: Runtime, state: str | None = "pending", limit: int = 50
) -> dict[str, Any]:
    items = runtime.extraction.list_candidates(state=state, limit=limit)
    chunk_ids = sorted({item["chunkId"] for item in items if item.get("chunkId")})
    texts: dict[str, dict[str, Any]] = {}
    if chunk_ids:
        rows = runtime.metadata.query(
            """
            SELECT chunk_id, document_id, seq, page_from, page_to, text
              FROM platform.document_chunk
             WHERE chunk_id = ANY(%s)
            """,
            (chunk_ids,),
        )
        texts = {row["chunk_id"]: row for row in rows}
    enriched = []
    for item in items:
        chunk = texts.get(item.get("chunkId") or "")
        enriched.append(
            {
                **item,
                "evidence": {
                    "chunkId": item.get("chunkId"),
                    "text": (chunk or {}).get("text", ""),
                    "pageFrom": (chunk or {}).get("page_from"),
                    "pageTo": (chunk or {}).get("page_to"),
                    "seq": (chunk or {}).get("seq"),
                },
            }
        )
    return {"candidates": enriched, "count": len(enriched), "state": state}


def _service(name: str, probe) -> dict[str, Any]:
    try:
        detail = probe()
        return {"name": name, "ok": True, "detail": detail}
    except Exception as exc:  # the overview must render even with outages
        return {"name": name, "ok": False, "detail": str(exc)[:200]}


def _probe_db(runtime: Runtime) -> str:
    rows = runtime.metadata.query("SELECT 1 AS ok")
    return "ok" if rows else "no rows"


def _probe_embedding(runtime: Runtime) -> int:
    """Report embedding readiness honestly: an unreachable TEI is not 'ok'."""
    if not runtime.embedding.available():
        raise PortError(
            code="Unavailable",
            message="embedding endpoint is not ready (model may still be loading)",
            provider="platform",
            provider_code="E_EMBED_UNAVAILABLE",
        )
    return int(runtime.search.counts().get("embeddings", 0) or 0)


def _probe_storage(runtime: Runtime) -> dict[str, Any]:
    root = Path(runtime.config.storage.root)
    usage = shutil.disk_usage(root)
    return {
        "root": str(root),
        "freePct": round((usage.free / usage.total) * 100, 2) if usage.total else 0,
    }
