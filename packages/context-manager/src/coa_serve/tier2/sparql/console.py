# SPDX-License-Identifier: Apache-2.0

"""SPARQL console execution for one namespace (P6 F72–F74).

This is the read-only console behind ``POST /namespaces/{namespaceId}/sparql``. The
statement is untrusted, so it passes the same :class:`SPARQLFirewall` as generated
SPARQL, extended to a namespace's graph set: the query is confined to the union of
the namespace's graphs (default graph) and to each graph by name, and only SELECT
and ASK are admitted.

Limits, all enforced here rather than trusted to the engine:

* query text ≤ 6,000 bytes;
* wall clock ≤ 10 s (the HTTP client gets the same budget);
* response body ≤ 4 MiB while it streams;
* at most 5,000 rows returned; the query is sent with ``LIMIT 5001`` so one extra
  row proves truncation;
* at most 200 graphs in the namespace scope.

Nothing here guesses a backend: an unset or unknown provider fails explicitly.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
import structlog

from ...clients.neptune import (
    NeptuneGraphClient,
    SPARQLResponseTooLargeError,
)
from .firewall import (
    FirewallRule,
    QueryForm,
    SPARQLFirewall,
    UnsafeSPARQLError,
    mentions_keyword,
)

logger = structlog.get_logger(__name__)

MAX_ROWS = 5_000
MAX_QUERY_BYTES = 6_000
TIMEOUT_S = 10.0
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_GRAPHS = 200
GRAPHS_TTL_S = 60.0

# Only the namespace's own data graphs are in scope. The T-Box graph
# (``urn:coa:ontology:<id>``) and inferred/import graphs deliberately do not match,
# so class definitions are not exposed through the console in this version.
_GRAPH_PREFIXES = (
    "https://coa.local/graph/",
    "https://ontology-workbench.local/",
)
_NAMESPACE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_GRAPHS_QUERY = (
    "SELECT DISTINCT ?g WHERE {{ GRAPH ?g {{ ?s ?p ?o }} "
    'FILTER(STRSTARTS(STR(?g), "{first}") || STRSTARTS(STR(?g), "{second}")) }} LIMIT {limit}'
)


class SparqlConsoleError(Exception):
    """A refusal or failure that maps to one public ``E_SPARQL_*`` code."""

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        *,
        provider_code: str | None = None,
        provider_message: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.provider_code = provider_code
        self.provider_message = provider_message

    def to_dict(self) -> dict[str, Any]:
        """The in-band error body the port and the API preserve verbatim."""
        body: dict[str, Any] = {"statusCode": self.status, "error": self.code, "message": self.message}
        if self.provider_code:
            body["providerCode"] = self.provider_code
        if self.provider_message:
            body["providerMessage"] = self.provider_message
        return body


class _ProviderRejected(Exception):
    def __init__(self, status: int, provider_code: str, provider_message: str) -> None:
        super().__init__(provider_message)
        self.status = status
        self.provider_code = provider_code
        self.provider_message = provider_message


class _ProviderUnavailable(Exception):
    pass


class SparqlBackend(Protocol):
    """The transport the console needs; there is no default implementation."""

    name: str

    async def select(self, sparql: str) -> tuple[list[str], list[list[str]]]: ...

    async def ask(self, sparql: str) -> bool: ...

    async def list_graphs(self, namespace: str) -> list[str]: ...


async def _list_graphs(backend: SparqlBackend, namespace: str) -> list[str]:
    """The namespace's graph IRIs, looked up by one bounded DISTINCT query."""
    query = _GRAPHS_QUERY.format(
        first=f"{_GRAPH_PREFIXES[0]}{namespace}/",
        second=f"{_GRAPH_PREFIXES[1]}{namespace}/",
        limit=MAX_GRAPHS + 2,
    )
    variables, rows = await backend.select(query)
    if "g" not in variables:
        return []
    at = variables.index("g")
    return [row[at] for row in rows if at < len(row) and row[at]]


def _term(binding: dict[str, Any]) -> str:
    """One SPARQL JSON binding as display text (IRI as-is, literal with its language/datatype)."""
    value = str(binding.get("value", ""))
    kind = binding.get("type")
    if kind == "literal":
        lang = binding.get("xml:lang")
        if lang:
            return f'"{value}"@{lang}'
        datatype = binding.get("datatype")
        if datatype:
            return f'"{value}"^^<{datatype}>'
        return value
    if kind == "bnode":
        return f"_:{value}"
    return value


class OxigraphBackend:
    """Oxigraph's SPARQL HTTP protocol, streamed so the byte cap is real."""

    name = "oxigraph"

    def __init__(self, url: str) -> None:
        if not url:
            raise ValueError("Oxigraph URL is required")
        self._url = url.rstrip("/")

    async def _post(self, query: str) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/sparql-query",
            "Accept": "application/sparql-results+json",
        }
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(TIMEOUT_S, connect=2.0)) as client:
                async with client.stream("POST", f"{self._url}/query", content=query.encode(), headers=headers) as resp:
                    if resp.status_code >= 400:
                        raw = bytearray()
                        async for chunk in resp.aiter_bytes():
                            raw.extend(chunk)
                            if len(raw) >= 64 * 1024:
                                break
                        raise _ProviderRejected(
                            resp.status_code,
                            f"HTTP_{resp.status_code}",
                            raw[:64 * 1024].decode("utf-8", "replace"),
                        )
                    declared = resp.headers.get("content-length")
                    if declared is not None and declared.isdigit() and int(declared) > MAX_RESPONSE_BYTES:
                        raise _ProviderUnavailable(f"response Content-Length {declared} exceeds the 4 MiB cap")
                    body = bytearray()
                    async for chunk in resp.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > MAX_RESPONSE_BYTES:
                            raise _TooLarge
        except httpx.TimeoutException as exc:
            raise _ProviderUnavailable(f"provider timed out: {type(exc).__name__}") from exc
        except httpx.HTTPError as exc:
            raise _ProviderUnavailable(f"provider unreachable: {type(exc).__name__}") from exc
        try:
            parsed = json.loads(body)
        except ValueError as exc:
            raise _ProviderUnavailable("provider returned a body that is not SPARQL JSON") from exc
        if not isinstance(parsed, dict):
            raise _ProviderUnavailable("provider returned a JSON value that is not an object")
        return parsed

    async def select(self, sparql: str) -> tuple[list[str], list[list[str]]]:
        data = await self._post(sparql)
        head = data.get("head") if isinstance(data.get("head"), dict) else {}
        results = data.get("results") if isinstance(data.get("results"), dict) else {}
        variables = [str(v) for v in head.get("vars") or []]
        rows = [
            [_term(row.get(var) or {}) for var in variables] for row in results.get("bindings") or [] if isinstance(row, dict)
        ]
        return variables, rows

    async def ask(self, sparql: str) -> bool:
        return bool((await self._post(sparql)).get("boolean", False))

    async def list_graphs(self, namespace: str) -> list[str]:
        return await _list_graphs(self, namespace)


class NeptuneBackend:
    """Neptune DB through the existing client, which already bounds the body and time."""

    name = "neptune"

    def __init__(self, endpoint: str, *, region: str | None = None) -> None:
        self._client = NeptuneGraphClient(
            endpoint=endpoint,
            region=region,
            enforce_read_only=False,
            retry_timeouts=False,
            max_body_bytes=MAX_RESPONSE_BYTES,
        )

    async def select(self, sparql: str) -> tuple[list[str], list[list[str]]]:
        data = await self._client.query_json(sparql)
        head = data.get("head") if isinstance(data.get("head"), dict) else {}
        results = data.get("results") if isinstance(data.get("results"), dict) else {}
        variables = [str(v) for v in head.get("vars") or []]
        rows = [
            [_term(row.get(var) or {}) for var in variables]
            for row in results.get("bindings") or []
            if isinstance(row, dict)
        ]
        return variables, rows

    async def ask(self, sparql: str) -> bool:
        return await self._client.ask(sparql)

    async def list_graphs(self, namespace: str) -> list[str]:
        return await _list_graphs(self, namespace)

    async def aclose(self) -> None:
        await self._client.close()


class _TooLarge(Exception):
    pass


@dataclass(frozen=True)
class SparqlRun:
    """One executed console statement."""

    form: str
    answer: bool | None
    variables: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    row_count: int
    returned_rows: int
    truncated: bool
    graph_count: int
    elapsed_ms: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "form": self.form,
            "answer": self.answer,
            "variables": list(self.variables),
            "rows": [list(row) for row in self.rows],
            "rowCount": self.row_count,
            "returnedRows": self.returned_rows,
            "truncated": self.truncated,
            "graphCount": self.graph_count,
            "elapsedMs": self.elapsed_ms,
        }


class SparqlConsole:
    """Validate, scope, execute and bound one console query."""

    def __init__(self, backend: SparqlBackend, *, firewall: SPARQLFirewall | None = None) -> None:
        self._backend = backend
        self._firewall = firewall or SPARQLFirewall()
        self._graphs_cache: dict[str, tuple[float, tuple[str, ...]]] = {}

    async def run(self, namespace: str, sparql: str) -> SparqlRun:
        """Run one statement for ``namespace``; always returns or raises ``SparqlConsoleError``."""
        started = time.perf_counter()
        if not _NAMESPACE_RE.fullmatch(namespace or ""):
            raise SparqlConsoleError(400, "E_SPARQL_BAD_NAMESPACE", "namespaceId is not a valid namespace identifier")
        text = (sparql or "").strip()
        if not text:
            raise SparqlConsoleError(400, "E_SPARQL_EMPTY", "sparql must not be empty")
        if len(text.encode("utf-8")) > MAX_QUERY_BYTES:
            raise SparqlConsoleError(
                400, "E_SPARQL_TOO_LONG", f"sparql exceeds {MAX_QUERY_BYTES} bytes; shorten the query"
            )
        if mentions_keyword(text, "LOAD"):
            raise SparqlConsoleError(400, "E_SPARQL_LOAD_NOT_ALLOWED", "LOAD is not allowed in the SPARQL console")

        form = ""
        try:
            graphs = await self._namespace_graphs(namespace)
            safe = self._firewall.check(
                text,
                named_graphs=graphs,
                max_results=MAX_ROWS + 1,
                allowed_forms=frozenset({QueryForm.SELECT, QueryForm.ASK}),
            )
            form = safe.form.value
            try:
                if safe.form == QueryForm.ASK:
                    answer = await asyncio.wait_for(self._backend.ask(safe.sparql), TIMEOUT_S)
                    result = SparqlRun(
                        form="ASK",
                        answer=answer,
                        variables=(),
                        rows=(),
                        row_count=0,
                        returned_rows=0,
                        truncated=False,
                        graph_count=len(graphs),
                        elapsed_ms=int((time.perf_counter() - started) * 1000),
                    )
                    logger.info(
                        "sparql_console",
                        namespace=namespace,
                        form=form,
                        graph_count=len(graphs),
                        answer=answer,
                        elapsed_ms=result.elapsed_ms,
                    )
                    return result
                variables, rows = await asyncio.wait_for(self._backend.select(safe.sparql), TIMEOUT_S)
                shown_variables = tuple(variables) or safe.variables
                row_count = len(rows)
                truncated = row_count > MAX_ROWS
                returned = rows[:MAX_ROWS]
                result = SparqlRun(
                    form="SELECT",
                    answer=None,
                    variables=shown_variables,
                    rows=tuple(tuple(row) for row in returned),
                    row_count=row_count,
                    returned_rows=len(returned),
                    truncated=truncated,
                    graph_count=len(graphs),
                    elapsed_ms=int((time.perf_counter() - started) * 1000),
                )
            except asyncio.TimeoutError as exc:
                raise SparqlConsoleError(
                    504,
                    "E_SPARQL_TIMEOUT",
                    f"SPARQL execution exceeded the {int(TIMEOUT_S)} s limit",
                ) from exc
            except _TooLarge as exc:
                raise SparqlConsoleError(
                    413,
                    "E_SPARQL_RESULT_TOO_LARGE",
                    "SPARQL result exceeds the 4 MiB response cap; add filters or a smaller LIMIT",
                ) from exc
            except SPARQLResponseTooLargeError as exc:
                raise SparqlConsoleError(
                    413,
                    "E_SPARQL_RESULT_TOO_LARGE",
                    "SPARQL result exceeds the 4 MiB response cap; add filters or a smaller LIMIT",
                ) from exc
            except _ProviderRejected as exc:
                status = 400 if 400 <= exc.status < 500 else 502
                raise SparqlConsoleError(
                    status,
                    "E_SPARQL_PROVIDER_REJECTED" if status == 400 else "E_SPARQL_PROVIDER_ERROR",
                    "The graph provider rejected the query",
                    provider_code=exc.provider_code,
                    provider_message=exc.provider_message[:2_000],
                ) from exc
            except httpx.HTTPStatusError as exc:
                body = exc.response.text[:2_000]
                status = 400 if 400 <= exc.response.status_code < 500 else 502
                raise SparqlConsoleError(
                    status,
                    "E_SPARQL_PROVIDER_REJECTED" if status == 400 else "E_SPARQL_PROVIDER_ERROR",
                    "The graph provider rejected the query",
                    provider_code=f"HTTP_{exc.response.status_code}",
                    provider_message=body,
                ) from exc
            except _ProviderUnavailable as exc:
                raise SparqlConsoleError(
                    502, "E_SPARQL_PROVIDER_ERROR", "The graph provider is unavailable"
                ) from exc
        except UnsafeSPARQLError as exc:
            logger.warning(
                "sparql_console_rejected",
                namespace=namespace,
                form=form,
                rule=str(exc.rule),
                code=exc.code,
                elapsed_ms=int((time.perf_counter() - started) * 1000),
            )
            raise self._from_firewall(exc) from exc
        except SparqlConsoleError as exc:
            logger.warning(
                "sparql_console_rejected",
                namespace=namespace,
                form=form,
                code=exc.code,
                elapsed_ms=int((time.perf_counter() - started) * 1000),
            )
            raise

        logger.info(
            "sparql_console",
            namespace=namespace,
            form=form,
            graph_count=result.graph_count,
            row_count=result.row_count,
            returned_rows=result.returned_rows,
            truncated=result.truncated,
            elapsed_ms=result.elapsed_ms,
        )
        return result

    async def _namespace_graphs(self, namespace: str) -> tuple[str, ...]:
        """The namespace's graphs, cached for 60 s; never the endpoint's other data."""
        now = time.monotonic()
        cached = self._graphs_cache.get(namespace)
        if cached is not None and cached[0] > now:
            return cached[1]
        try:
            graphs = await asyncio.wait_for(self._backend.list_graphs(namespace), TIMEOUT_S)
        except asyncio.TimeoutError as exc:
            raise SparqlConsoleError(
                504, "E_SPARQL_TIMEOUT", f"Resolving the namespace graphs exceeded the {int(TIMEOUT_S)} s limit"
            ) from exc
        except _ProviderRejected as exc:
            raise SparqlConsoleError(
                502,
                "E_SPARQL_PROVIDER_ERROR",
                "The graph provider rejected the namespace graph lookup",
                provider_code=exc.provider_code,
                provider_message=exc.provider_message[:2_000],
            ) from exc
        except (_ProviderUnavailable, httpx.HTTPError, SPARQLResponseTooLargeError) as exc:
            raise SparqlConsoleError(
                502, "E_SPARQL_PROVIDER_ERROR", "The graph provider is unavailable"
            ) from exc
        if len(graphs) > MAX_GRAPHS:
            raise SparqlConsoleError(
                503,
                "E_SPARQL_SCOPE_TOO_LARGE",
                f"The namespace has {len(graphs)} graphs; the console is limited to {MAX_GRAPHS}",
            )
        if not graphs:
            raise SparqlConsoleError(
                503, "E_SPARQL_SCOPE_EMPTY", "The namespace has no data graphs to query"
            )
        kept = tuple(graphs)
        self._graphs_cache[namespace] = (now + GRAPHS_TTL_S, kept)
        return kept

    @staticmethod
    def _from_firewall(exc: UnsafeSPARQLError) -> SparqlConsoleError:
        """Map one firewall rejection to its public status and code."""
        code = exc.code or {
            FirewallRule.READ_ONLY: "E_SPARQL_SYNTAX",
            FirewallRule.FAIL_CLOSED: "E_SPARQL_SYNTAX",
            FirewallRule.STATEMENT: "E_SPARQL_STATEMENT_NOT_ALLOWED",
            FirewallRule.FEDERATED: "E_SPARQL_FEDERATED",
            FirewallRule.GRAPH_SCOPE: "E_SPARQL_GRAPH_FORBIDDEN",
            FirewallRule.RESULT_BOUND: "E_SPARQL_RESULT_BOUND",
            FirewallRule.WORK_BOUND: "E_SPARQL_SYNTAX",
            FirewallRule.GRANT: "E_SPARQL_FORBIDDEN",
        }.get(exc.rule, "E_SPARQL_SYNTAX")
        if code == "E_SPARQL_FORBIDDEN":
            return SparqlConsoleError(403, code, str(exc))
        return SparqlConsoleError(400, code, str(exc))


def build_console_from_env() -> SparqlConsole | None:
    """Build the console from the runtime's graph provider; ``None`` when unset.

    An unknown provider raises instead of falling back: a deployment that has not
    chosen a backend must get a clear 503, not a silent query against some default.
    """
    provider = (os.environ.get("COA_SPARQL_BACKEND") or os.environ.get("COA_PROVIDER_GRAPH") or "").strip().lower()
    if not provider:
        return None
    if provider == "oxigraph":
        url = os.environ.get("COA_GRAPH_OXIGRAPH_URL", "").strip()
        if not url:
            raise SparqlConsoleError(
                503,
                "E_SPARQL_BACKEND_NOT_CONFIGURED",
                "COA_PROVIDER_GRAPH=oxigraph requires COA_GRAPH_OXIGRAPH_URL",
            )
        return SparqlConsole(OxigraphBackend(url))
    if provider == "neptune":
        endpoint = os.environ.get("NEPTUNE_ENDPOINT", "").strip()
        if not endpoint:
            raise SparqlConsoleError(
                503,
                "E_SPARQL_BACKEND_NOT_CONFIGURED",
                "COA_PROVIDER_GRAPH=neptune requires NEPTUNE_ENDPOINT",
            )
        return SparqlConsole(NeptuneBackend(endpoint))
    raise SparqlConsoleError(
        503,
        "E_SPARQL_BACKEND_NOT_CONFIGURED",
        f"unsupported graph provider '{provider}'; expected oxigraph or neptune",
    )


__all__ = ["SparqlConsole", "SparqlConsoleError", "SparqlRun", "build_console_from_env"]
