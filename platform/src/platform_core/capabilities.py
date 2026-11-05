"""Oxigraph capability measurement (S1).

This is a measurement tool, not a product feature: it probes the exact GSP and
SPARQL 1.1 surface that the platform contract (04 section 4.2, 03 section 5.2.1)
depends on, and reports facts. `GSP_SUPPORT` must come from this run, never from
documentation.

Run inside the platform container:
    platform graph-capabilities --endpoint http://oxigraph:7878 --json
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import httpx

TURTLE = "text/turtle"
NT = "application/n-triples"
SRJ = "application/sparql-results+json"
SPARQL_QUERY = "application/sparql-query"
SPARQL_UPDATE = "application/sparql-update"

PREFIX = "urn:platform:capability"
BODY_LIMIT = 400


def _iri(kind: str, suffix: str) -> str:
    return f"{PREFIX}:{kind}:{suffix}"


def _marker(value: str) -> str:
    return f'<{PREFIX}:s> <{PREFIX}:p> "{value}" .'


class CapabilityProbe:
    def __init__(self, endpoint: str, allow_destructive: bool = False, timeout_s: float = 10.0) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.allow_destructive = allow_destructive
        self.run_id = uuid.uuid4().hex[:10]
        self.client = httpx.Client(base_url=self.endpoint, timeout=timeout_s)
        self.records: list[dict[str, Any]] = []

    def close(self) -> None:
        self.client.close()

    # ---- plumbing --------------------------------------------------------

    def _record(
        self,
        identity: str,
        group: str,
        request: str,
        passed: bool,
        detail: str,
        status: int | None = None,
        content_type: str | None = None,
        body: str | None = None,
        skipped: bool = False,
    ) -> dict[str, Any]:
        record = {
            "id": identity,
            "group": group,
            "request": request,
            "status": status,
            "content_type": content_type,
            "passed": passed,
            "skipped": skipped,
            "detail": detail,
            "body": (body or "")[:BODY_LIMIT] or None,
        }
        self.records.append(record)
        return record

    def _send(
        self,
        identity: str,
        group: str,
        method: str,
        path: str,
        params: dict[str, str] | None = None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
        expect_contains: str | None = None,
        expect_empty: bool = False,
        missing_ok: bool = False,
    ) -> dict[str, Any]:
        request_label = f"{method} {path}"
        if params:
            request_label += "?" + "&".join(f"{k}={v}" for k, v in params.items())
        try:
            response = self.client.request(method, path, params=params, content=content, headers=headers)
        except Exception as exc:  # noqa: BLE001 - measurement must record every failure
            return self._record(
                identity, group, request_label, False, f"{type(exc).__name__}: {exc}"
            )

        body = response.text
        passed = response.status_code < 400
        detail = f"HTTP {response.status_code}"
        if not passed and missing_ok and response.status_code == 404:
            # GSP semantics: reading a graph that does not exist answers 404,
            # which the platform maps to "empty graph".
            passed = True
            detail += " (graph absent, mapped to empty by the platform)"
        if passed and expect_contains is not None and expect_contains not in body:
            passed = False
            detail += f", body missing {expect_contains!r}"
        if passed and expect_empty and body.strip():
            # An empty graph may still serialize as an empty document; only reject
            # when a statement is present.
            passed = len([ln for ln in body.splitlines() if ln.strip() and not ln.startswith("@")]) == 0
            detail += ", expected empty graph"
        if not passed:
            detail += f", body: {body[:200]!r}"
        return self._record(
            identity,
            group,
            request_label,
            passed,
            detail,
            status=response.status_code,
            content_type=response.headers.get("content-type"),
            body=body,
        )

    def _query(self, sparql: str) -> tuple[int | None, Any]:
        try:
            response = self.client.post(
                "/query",
                content=sparql.encode(),
                headers={"Content-Type": SPARQL_QUERY, "Accept": SRJ},
            )
        except Exception as exc:  # noqa: BLE001
            return None, f"{type(exc).__name__}: {exc}"
        if response.status_code >= 400:
            return response.status_code, response.text
        try:
            return response.status_code, response.json()
        except ValueError:
            # Observed with SERVICE: Oxigraph answers 200 but writes an error
            # sentence inside the JSON stream. Keep the raw text as evidence.
            return response.status_code, f"__NON_JSON__ {response.text[:300]}"

    def _update(self, sparql: str) -> tuple[int | None, str]:
        try:
            response = self.client.post(
                "/update",
                content=sparql.encode(),
                headers={"Content-Type": SPARQL_UPDATE},
            )
            return response.status_code, response.text
        except Exception as exc:  # noqa: BLE001
            return None, f"{type(exc).__name__}: {exc}"

    def _expect_rows(
        self,
        identity: str,
        sparql: str,
        expected: list[dict[str, str]],
        note: str,
    ) -> dict[str, Any]:
        status, payload = self._query(sparql)
        if status is None or not isinstance(payload, dict):
            return self._record(identity, "sparql", "POST /query", False, f"status={status} {payload}")
        rows = [
            {name: term.get("value") for name, term in row.items()}
            for row in payload.get("results", {}).get("bindings", [])
        ]
        passed = rows == expected
        return self._record(
            identity,
            "sparql",
            "POST /query",
            passed,
            f"HTTP {status}, rows={json.dumps(rows, ensure_ascii=False)[:300]} {note}".strip(),
            status=status,
            content_type=SRJ,
            body=json.dumps(payload)[:BODY_LIMIT],
        )

    # ---- GSP -------------------------------------------------------------

    def probe_gsp(self) -> None:
        named = _iri("gsp", self.run_id)
        turtle = f"@prefix p: <{PREFIX}:> .\np:s p:p \"v1\" .\n"

        default_empty = False
        status, payload = self._query("ASK { ?s ?p ?o }")
        if isinstance(payload, dict):
            default_empty = payload.get("boolean") is False

        destructive_ok = default_empty or self.allow_destructive
        note = "" if destructive_ok else "skipped (default graph is not empty; use --allow-destructive)"

        # Measured on 0.5.7: bare /store addresses the whole dataset (GET with
        # Turtle fails), while ?default addresses the default graph only.
        if destructive_ok:
            self._send("gsp.put.default", "gsp", "PUT", "/store", params={"default": ""},
                       content=turtle.encode(), headers={"Content-Type": TURTLE})
            self._send("gsp.get.default", "gsp", "GET", "/store", params={"default": ""},
                       headers={"Accept": TURTLE}, expect_contains="v1")
            self._send("gsp.post.default", "gsp", "POST", "/store", params={"default": ""},
                       content=f'<{PREFIX}:s2> <{PREFIX}:p> "v2" .'.encode(),
                       headers={"Content-Type": TURTLE})
            self._send("gsp.get.default.after_post", "gsp", "GET", "/store", params={"default": ""},
                       headers={"Accept": TURTLE}, expect_contains="v2")
            self._send("gsp.delete.default", "gsp", "DELETE", "/store", params={"default": ""})
            self._send("gsp.get.default.after_delete", "gsp", "GET", "/store", params={"default": ""},
                       headers={"Accept": TURTLE}, expect_empty=True)
        else:
            for identity in (
                "gsp.put.default",
                "gsp.get.default",
                "gsp.post.default",
                "gsp.get.default.after_post",
                "gsp.delete.default",
                "gsp.get.default.after_delete",
            ):
                self._record(identity, "gsp", "-", False, note, skipped=True)

        # bare /store addresses the full dataset, not the default graph.
        self._send("gsp.get.whole_store", "gsp", "GET", "/store", headers={"Accept": "application/n-quads"})

        # named graph identification: query parameter style is GSP; path style is not.
        self._send("gsp.put.named", "gsp", "PUT", "/store", params={"graph": named},
                   content=turtle.encode(), headers={"Content-Type": TURTLE})
        self._send("gsp.get.named", "gsp", "GET", "/store", params={"graph": named},
                   headers={"Accept": TURTLE}, expect_contains="v1")
        self._send("gsp.post.named", "gsp", "POST", "/store", params={"graph": named},
                   content=f'<{PREFIX}:s2> <{PREFIX}:p> "v2" .'.encode(),
                   headers={"Content-Type": TURTLE})
        self._send("gsp.get.named.after_post", "gsp", "GET", "/store", params={"graph": named},
                   headers={"Accept": TURTLE}, expect_contains="v2")

        # content negotiation (before deleting the graph)
        self._send("gsp.get.named.negotiate.nt", "gsp", "GET", "/store", params={"graph": named},
                   headers={"Accept": NT})
        self._send("gsp.get.named.negotiate.jsonld", "gsp", "GET", "/store", params={"graph": named},
                   headers={"Accept": "application/ld+json"})
        self._send("gsp.get.named.negotiate.unsupported", "gsp", "GET", "/store", params={"graph": named},
                   headers={"Accept": "application/x-unknown"})

        self._send("gsp.delete.named", "gsp", "DELETE", "/store", params={"graph": named})
        self._send("gsp.get.named.after_delete", "gsp", "GET", "/store", params={"graph": named},
                   headers={"Accept": TURTLE}, missing_ok=True)

        # alternative identification styles (only one should work)
        self._send("gsp.named.path_style", "gsp", "GET", f"/store/{named.replace(':', '%3A')}")
        self._send("gsp.default.param_style", "gsp", "GET", "/store", params={"default": ""},
                   headers={"Accept": TURTLE})

        # failure body for bad payload on PUT
        self._send("gsp.put.named.bad_turtle", "gsp", "PUT", "/store", params={"graph": named},
                   content=b"this is not turtle", headers={"Content-Type": TURTLE})

        # cleanup
        self._update(f"DROP SILENT GRAPH <{named}>")

    # ---- SPARQL ----------------------------------------------------------

    def probe_sparql(self) -> None:
        g = _iri("pp", self.run_id)
        g2 = _iri("plus", self.run_id)
        g3 = _iri("update", self.run_id)

        setup = (
            f"INSERT DATA {{ GRAPH <{g}> {{ "
            f"<{PREFIX}:a> <{PREFIX}:p1> <{PREFIX}:o1> . "
            f"<{PREFIX}:o1> <{PREFIX}:p2> <{PREFIX}:o2> }} "
            f"GRAPH <{g2}> {{ <{PREFIX}:n1> <{PREFIX}:next> <{PREFIX}:n2> . "
            f"<{PREFIX}:n2> <{PREFIX}:next> <{PREFIX}:n3> }} "
            f"GRAPH <{g3}> {{ <{PREFIX}:u> <{PREFIX}:p> \"u1\" }} }}"
        )
        status, body = self._update(setup)
        self._record(
            "sparql.update.insert_data", "sparql", "POST /update", status is not None and status < 400,
            f"HTTP {status} {body[:150]}", status=status, body=body,
        )

        self._expect_rows(
            "sparql.property_path.sequence",
            f"SELECT ?x WHERE {{ GRAPH <{g}> {{ <{PREFIX}:a> <{PREFIX}:p1>/<{PREFIX}:p2> ?x }} }}",
            [{"x": f"{PREFIX}:o2"}],
            "expect o2",
        )
        self._expect_rows(
            "sparql.property_path.plus",
            f"SELECT ?s ?o WHERE {{ GRAPH <{g2}> {{ ?s <{PREFIX}:next>+ ?o }} }} ORDER BY ?s ?o",
            [
                {"s": f"{PREFIX}:n1", "o": f"{PREFIX}:n2"},
                {"s": f"{PREFIX}:n1", "o": f"{PREFIX}:n3"},
                {"s": f"{PREFIX}:n2", "o": f"{PREFIX}:n3"},
            ],
            "expect 3 closure pairs",
        )
        self._expect_rows(
            "sparql.property_path.inverse",
            f"SELECT ?x WHERE {{ GRAPH <{g}> {{ <{PREFIX}:o2> ^<{PREFIX}:p2> ?x }} }}",
            [{"x": f"{PREFIX}:o1"}],
            "expect o1",
        )
        self._expect_rows(
            "sparql.from_clause",
            f"SELECT ?s FROM <{g}> WHERE {{ ?s <{PREFIX}:p1> <{PREFIX}:o1> }}",
            [{"s": f"{PREFIX}:a"}],
            "FROM as default graph",
        )
        self._expect_rows(
            "sparql.from_named_clause",
            f"SELECT ?g FROM NAMED <{g2}> WHERE {{ GRAPH ?g {{ <{PREFIX}:n1> <{PREFIX}:next> <{PREFIX}:n2> }} }}",
            [{"g": g2}],
            "FROM NAMED overlay",
        )

        status, payload = self._query(
            "SELECT ?s WHERE { SERVICE <http://127.0.0.1:9/sparql> { ?s ?p ?o } } LIMIT 1"
        )
        reliable = (
            status is not None
            and status < 400
            and not (isinstance(payload, str) and payload.startswith("__NON_JSON__"))
        )
        self._record(
            "sparql.service", "sparql", "POST /query SERVICE", reliable,
            f"HTTP {status}; SERVICE is blocked by the platform guardrail regardless. raw={str(payload)[:200]}",
            status=status, body=str(payload),
        )

        status, body = self._update(f"CLEAR GRAPH <{g3}>")
        status2, payload = self._query(f"ASK {{ GRAPH <{g3}> {{ ?s ?p ?o }} }}")
        cleared = (
            status is not None and status < 400 and isinstance(payload, dict) and payload.get("boolean") is False
        )
        self._record(
            "sparql.update.clear_graph", "sparql", "POST /update CLEAR GRAPH", cleared,
            f"clear HTTP {status}, ask HTTP {status2}", status=status, body=body,
        )

        status, body = self._update(f"DROP GRAPH <{g3}>")
        self._record(
            "sparql.update.drop_graph", "sparql", "POST /update DROP GRAPH",
            status is not None and status < 400, f"HTTP {status}", status=status, body=body,
        )

        self._update(f"DROP SILENT GRAPH <{g}>; DROP SILENT GRAPH <{g2}>")

    # ---- classification --------------------------------------------------

    def _gsp_support(self) -> str:
        by_id = {item["id"]: item for item in self.records if item["group"] == "gsp"}
        methods = ("get", "put", "post", "delete")
        default_ok = all(by_id.get(f"gsp.{m}.default", {}).get("passed") for m in methods)
        named_ok = all(by_id.get(f"gsp.{m}.named", {}).get("passed") for m in methods)
        default_skipped = all(by_id.get(f"gsp.{m}.default", {}).get("skipped") for m in methods)
        if default_skipped:
            return "partial" if named_ok else "none"
        if default_ok and named_ok:
            return "full"
        any_read = any(
            by_id.get(f"gsp.get.{scope}", {}).get("passed") for scope in ("default", "named")
        )
        return "partial" if any_read or named_ok else "none"

    def report(self) -> dict[str, Any]:
        gsp_by_id = {item["id"]: item for item in self.records if item["group"] == "gsp"}
        sparql = {item["id"]: item["passed"] for item in self.records if item["group"] == "sparql"}
        named_param = bool(
            gsp_by_id.get("gsp.get.named", {}).get("passed")
            or gsp_by_id.get("gsp.get.named.after_post", {}).get("passed")
        )
        return {
            "provider": "oxigraph-http",
            "endpoint": self.endpoint,
            "run_id": self.run_id,
            "gsp": {
                "support": self._gsp_support(),
                "named_graph_style": "query" if named_param else "none",
                "checks": [item for item in self.records if item["group"] == "gsp"],
            },
            "sparql": {
                "checks": [item for item in self.records if item["group"] == "sparql"],
                "summary": sparql,
            },
        }


def run_probe(endpoint: str, allow_destructive: bool = False) -> dict[str, Any]:
    probe = CapabilityProbe(endpoint, allow_destructive=allow_destructive)
    try:
        probe.probe_gsp()
        probe.probe_sparql()
        return probe.report()
    finally:
        probe.close()
