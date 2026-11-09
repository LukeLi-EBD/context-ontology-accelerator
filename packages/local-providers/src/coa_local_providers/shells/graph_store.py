"""``platform_core`` synchronous GraphStore -> ``coa_ports.GraphStorePort``.

Signature differences (S10, measured in ``doc/coa-x/02-薄壳清点.md``):

- both sides are synchronous and expose ``query``/``ask``/``update``/
  ``clear_graph``; nothing has to be wrapped in ``to_thread``;
- ``query`` returns the platform envelope
  ``{"kind", "variables", "bindings": [{"values": {name: term}}]}`` while the
  port promises :class:`~coa_ports.GraphQueryResult` with flat ``rows``;
- the port adds ``probe``; the adapter's own ``probe`` writes and clears a
  self-check graph, so it is used when present, with ``ASK {}`` as fallback.

No business rule lives here: term flattening and error translation only.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from coa_ports import GraphQueryResult, PortError

from .errors import to_port_error

_REQUIRED_METHODS = ("query", "ask", "update", "clear_graph")


def _flat(term: Any) -> Any:
    """One platform term dict -> the plain value a COA binding row carries."""
    if not isinstance(term, Mapping):
        return term
    kind = term.get("kind")
    if kind == "iri":
        return term.get("iri")
    if kind == "bnode":
        return term.get("label")
    return term.get("value")


class GraphStoreShell:
    """Adapt a platform graph store to the COA ``GraphStorePort``.

    Args:
        inner: A platform store exposing ``query``/``ask``/``update``/
            ``clear_graph``. Typed ``object`` so importing this module does
            not drag in the httpx/rdflib adapter stack.
        provider: Provider name recorded on translated errors.
    """

    def __init__(self, inner: object, *, provider: str = "oxigraph") -> None:
        missing = [
            name for name in _REQUIRED_METHODS if not callable(getattr(inner, name, None))
        ]
        if missing:
            raise TypeError(f"inner must expose callable {', '.join(missing)}")
        self._inner = inner
        self._provider = provider

    def query(self, sparql: str) -> GraphQueryResult:
        """Run a SELECT/ASK query and flatten the bindings."""
        return self._result(self._call("query", sparql))

    def ask(self, sparql: str) -> bool:
        """Run an ASK query."""
        return bool(self._call("ask", sparql))

    def update(self, sparql: str) -> None:
        """Apply one SPARQL Update statement."""
        self._call("update", sparql)

    def clear_graph(self, graph_uri: str) -> None:
        """Remove one named graph."""
        self._call("clear_graph", graph_uri)

    def probe(self) -> Mapping[str, Any]:
        """Reachability snapshot; never raises.

        Prefers the adapter's own ``probe`` (it writes and clears a dedicated
        self-check graph), then one ``ASK {}`` read.
        """
        snapshot: dict[str, Any] = {"status": "ok", "provider": self._provider}
        try:
            native = getattr(self._inner, "probe", None)
            if callable(native):
                extra = native()
                if isinstance(extra, Mapping):
                    snapshot.update(extra)
            else:
                self._inner.ask("ASK {}")  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001 - probe must never raise
            return {
                "status": "unavailable",
                "provider": self._provider,
                "provider_code": str(
                    getattr(exc, "provider_code", "") or type(exc).__name__
                ),
            }
        return snapshot

    # ── internals ───────────────────────────────────────────────────────────

    def _call(self, method: str, *args: Any) -> Any:
        try:
            return getattr(self._inner, method)(*args)
        except PortError:
            raise
        except Exception as exc:  # noqa: BLE001 - platform error class is not importable here
            raise to_port_error(
                exc, provider=self._provider, message=f"graph {method} failed"
            ) from exc

    @staticmethod
    def _result(payload: Any) -> GraphQueryResult:
        if isinstance(payload, GraphQueryResult):
            return payload
        envelope = payload if isinstance(payload, Mapping) else {}
        rows = tuple(
            {
                str(name): _flat(term)
                for name, term in (row.get("values") or {}).items()
            }
            for row in (envelope.get("bindings") or ())
        )
        boolean = envelope.get("boolean")
        return GraphQueryResult(
            kind=str(envelope.get("kind") or "select"),
            rows=rows,
            boolean=None if boolean is None else bool(boolean),
        )


__all__ = ["GraphStoreShell"]
