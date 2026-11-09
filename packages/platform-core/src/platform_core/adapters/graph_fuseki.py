"""GraphStore adapter: Apache Jena Fuseki over SPARQL 1.1 + GSP (Q8-b).

Only the common subset shared with OxigraphHttpStore is implemented:
query / ask / update / clear_graph / replace_graph / export_graph / probe
(plus count_graph and load, which are thin wrappers over the same subset).
``SERVICE`` is rejected exactly like the Oxigraph adapter; the dataset
whitelist is shared with it.
"""

from __future__ import annotations

import uuid
from typing import Any
from urllib.parse import quote

import httpx
from rdflib import Graph, Dataset

from ..errors import PortError, UNSUPPORTED_PORT
from ..ports import Manifest
from .graph_oxigraph import (
    DEFAULT_ALLOWED_GRAPH_PREFIXES,
    IRI_RE,
    PROBE,
    RDF_FORMATS,
    SERVICE_RE,
    _strip_string_literals,
    parse_rdf,
)

class FusekiHttpStore:
    port = "GraphStore"

    def __init__(
        self,
        endpoint: str,
        dataset: str = "ds",
        timeout_ms: int = 30000,
        max_rows: int = 10000,
        allowed_graph_prefixes: tuple[str, ...] = DEFAULT_ALLOWED_GRAPH_PREFIXES,
        allowed_graphs: tuple[str, ...] = (),
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._dataset = dataset.strip("/")
        self._timeout_ms = timeout_ms
        self._max_rows = max_rows
        self._allowed_prefixes = tuple(allowed_graph_prefixes)
        self._allowed_graphs = tuple(allowed_graphs)
        self._client = httpx.Client(
            base_url=f"{self._endpoint}/{self._dataset}",
            timeout=httpx.Timeout(max(timeout_ms / 1000, 1.0)),
        )

    def manifest(self) -> Manifest:
        return Manifest(
            provider="jena-fuseki",
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
            provider_version="5.5.0",
            limits={"timeout_ms": self._timeout_ms, "max_rows": self._max_rows},
            notes={
                "backend": "jena-fuseki",
                "dataset": self._dataset,
                "gsp_named_graph_style": "?graph=",
                "gsp_default_style": "?default",
                "content_negotiation": True,
                "text_index": False,
                "federation_service": False,
                "from_clause": True,
                "from_named": True,
                "graph_whitelist": {
                    "prefixes": list(self._allowed_prefixes),
                    "graphs": list(self._allowed_graphs),
                    "error": "E_GRAPH_GRAPH_NOT_ALLOWED",
                },
                "update": {"insert_data": True, "clear_graph": True, "drop_graph": True},
                "common_subset_only": True,
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
                message=f"fuseki request timed out after {self._timeout_ms} ms",
                provider="jena-fuseki",
                provider_code="E_GRAPH_TIMEOUT",
            ) from exc
        except httpx.HTTPError as exc:
            raise PortError(
                code="Unavailable",
                message=f"fuseki is unreachable at {self._endpoint}: {exc}",
                provider="jena-fuseki",
                provider_code="E_GRAPH_UNAVAILABLE",
                retryable=True,
            ) from exc
        if response.status_code >= 400:
            body = response.text[:500]
            raise PortError(
                code="InvalidArgument",
                message=f"fuseki returned HTTP {response.status_code}: {body}",
                provider="jena-fuseki",
                provider_code="E_GRAPH_BAD_REQUEST",
                details={"status": response.status_code, "body": body},
            )
        return response

    def _assert_allowed_graphs(self, sparql: str) -> None:
        from .graph_oxigraph import _FROM_RE, _GRAPH_RE

        stripped = _strip_string_literals(sparql)
        for iri in _FROM_RE.findall(stripped) + _GRAPH_RE.findall(stripped):
            if iri in self._allowed_graphs:
                continue
            if any(iri.startswith(prefix) for prefix in self._allowed_prefixes):
                continue
            raise PortError(
                code="PermissionDenied",
                message=f"graph {iri} is outside the platform whitelist",
                provider="jena-fuseki",
                provider_code="E_GRAPH_GRAPH_NOT_ALLOWED",
                details={
                    "graph": iri,
                    "allowedPrefixes": list(self._allowed_prefixes),
                    "allowedGraphs": list(self._allowed_graphs),
                },
            )

    @staticmethod
    def _guard_sparql(sparql: str) -> None:
        if SERVICE_RE.search(_strip_string_literals(sparql)):
            raise PortError(
                code="Unsupported",
                message="SPARQL SERVICE is not allowed by the platform guardrail",
                provider="jena-fuseki",
                provider_code="E_SPARQL_SERVICE",
            )

    def _run_query(self, sparql: str) -> dict[str, Any]:
        self._guard_sparql(sparql)
        self._assert_allowed_graphs(sparql)
        response = self._request(
            "POST",
            "/sparql",
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
                message="fuseki returned a non-JSON SPARQL result",
                provider="jena-fuseki",
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
                provider="jena-fuseki",
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
        self._guard_sparql(sparql)
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
                provider="jena-fuseki",
                provider_code="E_GRAPH_BAD_IRI",
            )
        self.update(f"DROP SILENT GRAPH <{graph_iri}>")

    # ---- GSP-backed named graph load ------------------------------------

    @staticmethod
    def _insert_data(graph_iri: str, triples: list[Any]) -> str:
        body = "\n".join(f"{s.n3()} {p.n3()} {o.n3()} ." for s, p, o in triples)
        return f"INSERT DATA {{ GRAPH <{graph_iri}> {{\n{body}\n}} }}"

    def replace_graph(self, graph_iri: str, data: bytes, rdf_format: str = "turtle") -> dict[str, Any]:
        """GSP PUT of the whole named graph (Fuseki replaces atomically)."""
        if not IRI_RE.match(graph_iri):
            raise PortError(
                code="InvalidArgument",
                message=f"invalid graph IRI: {graph_iri!r}",
                provider="jena-fuseki",
                provider_code="E_GRAPH_BAD_IRI",
            )
        fmt = RDF_FORMATS.get(rdf_format.lower())
        if fmt is None:
            raise PortError(
                code="Unsupported",
                message=f"RDF format {rdf_format!r} is not supported",
                provider="jena-fuseki",
                provider_code="E_GRAPH_FORMAT",
                details={"supported": sorted(RDF_FORMATS)},
            )
        triples = parse_rdf(data, rdf_format)
        content_type = {
            "turtle": "text/turtle",
            "trig": "application/trig",
            "nt": "application/n-triples",
        }[fmt]
        self._request(
            "PUT",
            f"/data?graph={quote(graph_iri, safe='')}",
            content=data,
            headers={"Content-Type": content_type},
        )
        return {"graph": graph_iri, "triples": len(triples), "format": rdf_format}

    def count_graph(self, graph_iri: str) -> int:
        if not IRI_RE.match(graph_iri):
            raise PortError(
                code="InvalidArgument",
                message=f"invalid graph IRI: {graph_iri!r}",
                provider="jena-fuseki",
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

    # ---- whole-graph export ---------------------------------------------

    def export_graph(self, graph_iri: str, rdf_format: str = "nt") -> bytes:
        if not IRI_RE.match(graph_iri):
            raise PortError(
                code="InvalidArgument",
                message=f"invalid graph IRI: {graph_iri!r}",
                provider="jena-fuseki",
                provider_code="E_GRAPH_BAD_IRI",
            )
        if rdf_format != "nt":
            raise PortError(
                code="Unsupported",
                message=f"export_graph only supports N-Triples, got {rdf_format!r}",
                provider="jena-fuseki",
                provider_code=UNSUPPORTED_PORT,
            )
        response = self._request(
            "GET",
            f"/data?graph={quote(graph_iri, safe='')}",
            headers={"Accept": "application/n-triples"},
        )
        return response.content

    # ---- explicit placeholders (not part of the common subset) ----------

    def construct(self, _sparql: str) -> Any:
        raise PortError(
            code="Unsupported",
            message="GraphStore.construct is not implemented for fuseki (common subset only)",
            provider="jena-fuseki",
            provider_code=UNSUPPORTED_PORT,
        )

    def dump(self, *_args: Any, **_kwargs: Any) -> Any:
        raise PortError(
            code="Unsupported",
            message="GraphStore.dump is not implemented for fuseki (common subset only)",
            provider="jena-fuseki",
            provider_code=UNSUPPORTED_PORT,
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
                    provider="jena-fuseki",
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
                    provider="jena-fuseki",
                    provider_code="E_GRAPH_WRITE_PROBE",
                )
        finally:
            try:
                self.clear_graph(PROBE)
            except PortError:
                pass
        return {"written": 1, "read": 1, "cleaned": True}
