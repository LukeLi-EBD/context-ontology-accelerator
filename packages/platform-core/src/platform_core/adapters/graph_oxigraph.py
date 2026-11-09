"""GraphStore adapter: Oxigraph over HTTP (SPARQL 1.1)."""

from __future__ import annotations

import re
import uuid
from typing import Any

import httpx
from rdflib import Graph, Dataset

from ..errors import PortError, UNSUPPORTED_PORT
from ..ports import Manifest

RDF_FORMATS = {"turtle": "turtle", "ttl": "turtle", "trig": "trig", "nt": "nt", "ntriples": "nt"}

SERVICE_RE = re.compile(r"\bSERVICE\b", re.IGNORECASE)
IRI_RE = re.compile(r"^[^<>\"{}|^`\\\s]+$")
PROBE = "urn:platform:selfcheck:graph"

# Q7-b: only platform-managed graphs may appear in a dataset clause or a
# GRAPH <iri> pattern. Any other IRI (another product's store, an external
# dataset) is rejected with a dedicated code instead of being forwarded.
DEFAULT_ALLOWED_GRAPH_PREFIXES = ("urn:platform:",)
_FROM_RE = re.compile(r"\bFROM\s+(?:NAMED\s+)?<([^>]+)>", re.IGNORECASE)
_GRAPH_RE = re.compile(r"\bGRAPH\s*<([^>]+)>", re.IGNORECASE)

# Strip RDF/SPARQL string literals (quoted strings + optional lang/datatype)
# so that the SERVICE guardrail only fires on the SPARQL SERVICE keyword, not
# on the word "Service" inside a literal such as "Legal Service Address"@en.
_STRING_LITERAL_RE = re.compile(
    r'"""(?:\\.|[^\\])*?"""(?:\^\^<[^>]*>|@[a-zA-Z]+(?:-[a-zA-Z0-9]+)*)?'
    r"|'''(?:\\.|[^\\])*?'''(?:\^\^<[^>]*>|@[a-zA-Z]+(?:-[a-zA-Z0-9]+)*)?"
    r'|"(?:\\.|[^\\"])*?"(?:\^\^<[^>]*>|@[a-zA-Z]+(?:-[a-zA-Z0-9]+)*)?'
    r"|'(?:\\.|[^\\'])*?'(?:\^\^<[^>]*>|@[a-zA-Z]+(?:-[a-zA-Z0-9]+)*)?"
)


def _strip_string_literals(sparql: str) -> str:
    """Remove quoted string literals (and their lang/datatype suffixes) from SPARQL."""
    return _STRING_LITERAL_RE.sub("", sparql)


def parse_rdf(data: bytes, rdf_format: str) -> list[Any]:
    """Parse Turtle/TriG into a plain triple list (rdflib does the parsing)."""
    fmt = RDF_FORMATS.get(rdf_format.lower())
    if fmt is None:
        raise PortError(
            code="Unsupported",
            message=f"RDF format {rdf_format!r} is not supported",
            provider="rdflib",
            provider_code="E_GRAPH_FORMAT",
            details={"supported": sorted(RDF_FORMATS)},
        )
    try:
        if fmt == "trig":
            dataset = Dataset()
            dataset.parse(data=data, format="trig")
            return [(s, p, o) for s, p, o, _ in dataset.quads((None, None, None, None))]
        graph = Graph()
        graph.parse(data=data, format=fmt)
        return list(graph)
    except Exception as exc:  # rdflib raises several parser-specific types
        raise PortError(
            code="InvalidArgument",
            message=f"RDF parse failed ({rdf_format}): {exc}",
            provider="rdflib",
            provider_code="E_GRAPH_PARSE",
        ) from exc


class OxigraphHttpStore:
    port = "GraphStore"

    def __init__(
        self,
        endpoint: str,
        timeout_ms: int = 30000,
        max_rows: int = 10000,
        allowed_graph_prefixes: tuple[str, ...] = DEFAULT_ALLOWED_GRAPH_PREFIXES,
        allowed_graphs: tuple[str, ...] = (),
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._timeout_ms = timeout_ms
        self._max_rows = max_rows
        self._allowed_prefixes = tuple(allowed_graph_prefixes)
        self._allowed_graphs = tuple(allowed_graphs)
        self._client = httpx.Client(
            base_url=self._endpoint,
            timeout=httpx.Timeout(max(timeout_ms / 1000, 1.0)),
        )

    def manifest(self) -> Manifest:
        return Manifest(
            provider="oxigraph-http",
            port=self.port,
            capabilities=[
                "graph.sparql",
                "graph.ask",
                "graph.update",
                "graph.named_graphs",
                "graph.clear",
                "graph.load",
                "graph.gsp.get",
                "graph.gsp.put",
                "graph.gsp.post",
                "graph.gsp.delete",
                "graph.property_path",
                "graph.from_named",
            ],
            provider_version="0.5.7",
            limits={"timeout_ms": self._timeout_ms, "max_rows": self._max_rows},
            # Measured by `platform graph-capabilities` on 2026-11-04 (see
            # _design/impl/S1-本体存储与版本-设计.md section 3). Do not copy
            # documentation values here: GSP_SUPPORT must stay measured.
            notes={
                "backend": "oxigraph",
                # Platform-exposed GSP: measured 2026-11-05, GET /store=405,
                # POST/PUT/DELETE /store=403 E_GSP_GOVERNANCE_REQUIRED on every
                # graph (fsldm/tbox/staging). So the platform surface is "none".
                "gsp_support": "none",
                "gsp_platform": {
                    "read": "unavailable (GET /store -> 405)",
                    "write": "forbidden (POST /store -> 403 E_GSP_GOVERNANCE_REQUIRED)",
                },
                # Direct backend probe (bypassing the platform gate) still sees
                # full GSP; this is the value smoke-s1 compares against.
                "gsp_backend_support": "full",
                "gsp_named_graph_style": "query",  # ?graph=
                "gsp_default_style": "?default",   # bare /store is the whole dataset
                "gsp_whole_store": "dataset",
                "content_negotiation": True,
                "text_index": False,
                "federation_service": False,
                "service_probe": "malformed-json",
                "property_path": {"sequence": True, "plus": True, "inverse": True},
                "from_clause": True,
                "from_named": True,
                "graph_whitelist": {
                    "prefixes": list(self._allowed_prefixes),
                    "graphs": list(self._allowed_graphs),
                    "error": "E_GRAPH_GRAPH_NOT_ALLOWED",
                },
                "update": {"insert_data": True, "clear_graph": True, "drop_graph": True},
            },
        )

    def close(self) -> None:
        self._client.close()

    # ---- internals -------------------------------------------------------

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            raise PortError(
                code="DeadlineExceeded",
                message=f"oxigraph request timed out after {self._timeout_ms} ms",
                provider="oxigraph-http",
                provider_code="E_GRAPH_TIMEOUT",
            ) from exc
        except httpx.HTTPError as exc:
            raise PortError(
                code="Unavailable",
                message=f"oxigraph is unreachable at {self._endpoint}: {exc}",
                provider="oxigraph-http",
                provider_code="E_GRAPH_UNAVAILABLE",
                retryable=True,
            ) from exc
        if response.status_code >= 400:
            body = response.text[:500]
            raise PortError(
                code="InvalidArgument",
                message=f"oxigraph returned HTTP {response.status_code}: {body}",
                provider="oxigraph-http",
                provider_code="E_GRAPH_BAD_REQUEST",
                details={"status": response.status_code, "body": body},
            )
        return response

    def _assert_allowed_graphs(self, sparql: str) -> None:
        """Reject dataset clauses / GRAPH patterns outside the platform whitelist."""
        stripped = _strip_string_literals(sparql)
        for iri in _FROM_RE.findall(stripped) + _GRAPH_RE.findall(stripped):
            if iri in self._allowed_graphs:
                continue
            if any(iri.startswith(prefix) for prefix in self._allowed_prefixes):
                continue
            raise PortError(
                code="PermissionDenied",
                message=f"graph {iri} is outside the platform whitelist",
                provider="oxigraph-http",
                provider_code="E_GRAPH_GRAPH_NOT_ALLOWED",
                details={
                    "graph": iri,
                    "allowedPrefixes": list(self._allowed_prefixes),
                    "allowedGraphs": list(self._allowed_graphs),
                },
            )

    def _run_query(self, sparql: str) -> dict[str, Any]:
        if SERVICE_RE.search(_strip_string_literals(sparql)):
            raise PortError(
                code="Unsupported",
                message="SPARQL SERVICE is not allowed by the platform guardrail",
                provider="oxigraph-http",
                provider_code="E_SPARQL_SERVICE",
            )
        self._assert_allowed_graphs(sparql)
        response = self._request(
            "POST",
            "/query",
            content=sparql.encode("utf-8"),
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/sparql-results+json",
            },
        )
        try:
            return response.json()
        except ValueError as exc:
            raise PortError(
                code="Internal",
                message="oxigraph returned a non-JSON SPARQL result",
                provider="oxigraph-http",
                provider_code="E_GRAPH_BAD_RESULT",
            ) from exc

    @staticmethod
    def _term(value: dict[str, Any]) -> dict[str, Any]:
        kind = value.get("type")
        if kind == "uri":
            return {"kind": "iri", "iri": value.get("value")}
        if kind == "bnode":
            return {"kind": "bnode", "label": value.get("value")}
        return {
            "kind": "literal",
            "value": value.get("value", ""),
            "datatype": value.get("datatype"),
            "lang": value.get("xml:lang") or value.get("lang"),
        }

    # ---- GraphStore v1 ---------------------------------------------------

    def ask(self, sparql: str) -> bool:
        payload = self._run_query(sparql)
        if "boolean" not in payload:
            raise PortError(
                code="InvalidArgument",
                message="ask() expected an ASK result",
                provider="oxigraph-http",
                provider_code="E_GRAPH_RESULT_KIND",
            )
        return bool(payload["boolean"])

    def query(self, sparql: str) -> dict[str, Any]:
        payload = self._run_query(sparql)
        if "boolean" in payload:
            return {"kind": "ask", "variables": [], "bindings": [], "boolean": payload["boolean"], "truncated": False}
        variables = list(payload.get("head", {}).get("vars", []))
        raw_bindings = list(payload.get("results", {}).get("bindings", []))
        truncated = len(raw_bindings) > self._max_rows
        bindings = [
            {"values": {name: self._term(value) for name, value in row.items()}}
            for row in raw_bindings[: self._max_rows]
        ]
        return {"kind": "select", "variables": variables, "bindings": bindings, "truncated": truncated}

    def update(self, sparql: str) -> None:
        if SERVICE_RE.search(_strip_string_literals(sparql)):
            raise PortError(
                code="Unsupported",
                message="SPARQL SERVICE is not allowed by the platform guardrail",
                provider="oxigraph-http",
                provider_code="E_SPARQL_SERVICE",
            )
        self._request(
            "POST",
            "/update",
            content=sparql.encode("utf-8"),
            headers={"Content-Type": "application/sparql-update"},
        )

    def clear_graph(self, graph_iri: str) -> None:
        if not IRI_RE.match(graph_iri):
            raise PortError(
                code="InvalidArgument",
                message=f"invalid graph IRI: {graph_iri!r}",
                provider="oxigraph-http",
                provider_code="E_GRAPH_BAD_IRI",
            )
        self.update(f"DROP SILENT GRAPH <{graph_iri}>")

    # ---- S1: named graph load -------------------------------------------

    @staticmethod
    def _insert_data(graph_iri: str, triples: list[Any]) -> str:
        body = "\n".join(f"{s.n3()} {p.n3()} {o.n3()} ." for s, p, o in triples)
        return f"INSERT DATA {{ GRAPH <{graph_iri}> {{\n{body}\n}} }}"

    def replace_graph(self, graph_iri: str, data: bytes, rdf_format: str = "turtle") -> dict[str, Any]:
        """Replace one named graph atomically from the platform's point of view.

        Measured Oxigraph behavior: DROP GRAPH + INSERT DATA converge on retry,
        so a crash between the two steps is fixed by the next publish.
        """
        if not IRI_RE.match(graph_iri):
            raise PortError(
                code="InvalidArgument",
                message=f"invalid graph IRI: {graph_iri!r}",
                provider="oxigraph-http",
                provider_code="E_GRAPH_BAD_IRI",
            )
        triples = parse_rdf(data, rdf_format)
        self.update(f"DROP SILENT GRAPH <{graph_iri}>")
        if triples:
            self.update(self._insert_data(graph_iri, triples))
        return {"graph": graph_iri, "triples": len(triples), "format": rdf_format}

    def count_graph(self, graph_iri: str) -> int:
        if not IRI_RE.match(graph_iri):
            raise PortError(
                code="InvalidArgument",
                message=f"invalid graph IRI: {graph_iri!r}",
                provider="oxigraph-http",
                provider_code="E_GRAPH_BAD_IRI",
            )
        result = self.query(
            f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{graph_iri}> {{ ?s ?p ?o }} }}"
        )
        if not result["bindings"]:
            return 0
        return int(result["bindings"][0]["values"]["n"]["value"])

    def load(self, data: bytes, graph: str, rdf_format: str = "turtle") -> dict[str, Any]:
        return self.replace_graph(graph, data, rdf_format)

    # ---- S5: whole-graph export -----------------------------------------

    def export_graph(self, graph_iri: str, rdf_format: str = "nt") -> bytes:
        """Export one named graph as N-Triples (used by reasoning + SHACL)."""
        if not IRI_RE.match(graph_iri):
            raise PortError(
                code="InvalidArgument",
                message=f"invalid graph IRI: {graph_iri!r}",
                provider="oxigraph-http",
                provider_code="E_GRAPH_BAD_IRI",
            )
        if rdf_format != "nt":
            raise PortError(
                code="Unsupported",
                message=f"export_graph only supports N-Triples, got {rdf_format!r}",
                provider="oxigraph-http",
                provider_code=UNSUPPORTED_PORT,
            )
        sparql = (
            f"CONSTRUCT {{ ?s ?p ?o }} WHERE {{ GRAPH <{graph_iri}> {{ ?s ?p ?o }} }}"
        )
        response = self._request(
            "POST",
            "/query",
            content=sparql.encode("utf-8"),
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/n-triples",
            },
        )
        return response.content

    # ---- explicit placeholders (later slices fill them) ------------------

    def construct(self, _sparql: str) -> Any:
        raise PortError(
            code="Unsupported",
            message="GraphStore.construct is not implemented in S3",
            provider="oxigraph-http",
            provider_code=UNSUPPORTED_PORT,
            details={"slice": "S3"},
        )

    def dump(self, *_args: Any, **_kwargs: Any) -> Any:
        raise PortError(
            code="Unsupported",
            message="GraphStore.dump is not implemented yet",
            provider="oxigraph-http",
            provider_code=UNSUPPORTED_PORT,
            details={"slice": "later"},
        )

    # ---- self-check ------------------------------------------------------

    def probe(self) -> dict[str, Any]:
        marker = uuid.uuid4().hex
        subject = f"{PROBE}:subject"
        predicate = f"{PROBE}:predicate"
        try:
            if not self.ask("ASK {}"):
                raise PortError(
                    code="Unavailable",
                    message="ASK {} returned false",
                    provider="oxigraph-http",
                    provider_code="E_GRAPH_READONLY",
                )
            self.update(
                f'INSERT DATA {{ GRAPH <{PROBE}> {{ <{subject}> <{predicate}> "{marker}" }} }}'
            )
            rows = self.query(
                f"SELECT ?o WHERE {{ GRAPH <{PROBE}> {{ <{subject}> <{predicate}> ?o }} }}"
            )
            values = [row["values"]["o"]["value"] for row in rows["bindings"]]
            if values != [marker]:
                raise PortError(
                    code="DataLoss",
                    message="graph write probe did not read back the written value",
                    provider="oxigraph-http",
                    provider_code="E_GRAPH_WRITE_PROBE",
                )
        finally:
            try:
                self.clear_graph(PROBE)
            except PortError:
                pass
        return {"written": 1, "read": 1, "cleaned": True}
