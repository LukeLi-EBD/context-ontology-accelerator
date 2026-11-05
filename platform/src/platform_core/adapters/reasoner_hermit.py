"""ReasoningService adapter: ROBOT/HermiT (Q8-b).

Only the DL-specific methods live here: ``check_consistency`` and ``classify``.
``materialize`` keeps the existing ROBOT/ELK path (ReasonerClient), exactly as
the Q8 brief requires. The reasoner container exposes /v1/consistency and
/v1/classify, each shelling `robot reason --reasoner HermiT`.
"""

from __future__ import annotations

from typing import Any

import httpx
from rdflib import Graph, URIRef

from ..errors import PortError
from ..ports import Manifest

OWL = "http://www.w3.org/2002/07/owl#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL_NOTHING = URIRef(f"{OWL}Nothing")
OWL_THING = URIRef(f"{OWL}Thing")
RDFS_SUBCLASS = URIRef(f"{RDFS}subClassOf")


class HermitReasoner:
    port = "ReasoningService"

    def __init__(self, endpoint: str, timeout_ms: int = 300000) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._timeout_ms = timeout_ms
        self._client = httpx.Client(
            base_url=self._endpoint, timeout=httpx.Timeout(max(timeout_ms / 1000, 1.0))
        )

    def manifest(self) -> Manifest:
        return Manifest(
            provider="robot/hermit",
            port=self.port,
            capabilities=["reason.consistent", "reason.classify", "reason.unsat"],
            limits={"timeout_ms": self._timeout_ms},
            notes={
                "backend": "robot",
                "reasoner": "HermiT",
                "profile": "OWL2DL",
                "materialize": "robot/ELK (unchanged default path)",
                "commands": ["robot reason --reasoner HermiT"],
            },
        )

    def close(self) -> None:
        self._client.close()

    def probe(self) -> dict[str, Any]:
        return self.health()

    def health(self) -> dict[str, Any]:
        try:
            response = self._client.get("/healthz")
        except httpx.HTTPError as exc:
            raise PortError(
                code="Unavailable",
                message=f"reasoner is unreachable at {self._endpoint}: {exc}",
                provider="robot/hermit",
                provider_code="E_CONSISTENCY_UNAVAILABLE",
                retryable=True,
            ) from exc
        if response.status_code != 200:
            raise PortError(
                code="Unavailable",
                message=f"reasoner healthz returned HTTP {response.status_code}",
                provider="robot/hermit",
                provider_code="E_CONSISTENCY_UNAVAILABLE",
            )
        return response.json()

    # ---- internals -------------------------------------------------------

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client.post(path, json=payload)
        except httpx.TimeoutException as exc:
            raise PortError(
                code="DeadlineExceeded",
                message=f"robot/hermit {path} timed out after {self._timeout_ms} ms",
                provider="robot/hermit",
                provider_code="E_CONSISTENCY_TIMEOUT",
            ) from exc
        except httpx.HTTPError as exc:
            raise PortError(
                code="Unavailable",
                message=f"reasoner is unreachable at {self._endpoint}: {exc}",
                provider="robot/hermit",
                provider_code="E_CONSISTENCY_UNAVAILABLE",
                retryable=True,
            ) from exc
        if response.status_code == 504:
            raise PortError(
                code="DeadlineExceeded",
                message="robot/hermit timed out",
                provider="robot/hermit",
                provider_code="E_CONSISTENCY_TIMEOUT",
            )
        if response.status_code >= 500:
            raise PortError(
                code="Unavailable",
                message=f"robot/hermit failed: HTTP {response.status_code} {response.text[:400]}",
                provider="robot/hermit",
                provider_code="E_CONSISTENCY_FAILED",
                details={"status": response.status_code, "body": response.text[:500]},
            )
        if response.status_code >= 400:
            raise PortError(
                code="InvalidArgument",
                message=f"robot/hermit rejected the request: HTTP {response.status_code} {response.text[:400]}",
                provider="robot/hermit",
                provider_code="E_CONSISTENCY_BAD_REQUEST",
                details={"status": response.status_code, "body": response.text[:500]},
            )
        return response.json()

    # ---- ReasoningService v1 --------------------------------------------

    def check_consistency(self, tbox_nt: bytes, abox_nt: bytes = b"") -> dict[str, Any]:
        """DL consistency gate. Returns the same shape as ReasoningService.check_consistency."""
        payload = self._post(
            "/v1/consistency",
            {
                "tbox": tbox_nt.decode("utf-8", errors="replace"),
                "abox": abox_nt.decode("utf-8", errors="replace"),
            },
        )
        return {
            "consistent": bool(payload.get("consistent", False)),
            "engine": "robot/hermit",
            "reasonCode": payload.get("reasonCode"),
            "ms": payload.get("ms"),
            "unsatisfiable": payload.get("unsatisfiable", []),
        }

    def classify(self, tbox_nt: bytes, abox_nt: bytes = b"") -> dict[str, Any]:
        """DL classification: parse ROBOT/HermiT's reasoned graph into axiom lists."""
        payload = self._post(
            "/v1/classify",
            {
                "tbox": tbox_nt.decode("utf-8", errors="replace"),
                "abox": abox_nt.decode("utf-8", errors="replace"),
            },
        )
        reasoned = payload.get("reasoned") or ""
        if not reasoned.strip():
            return {
                "subClassOf": [],
                "equivalentClasses": [],
                "disjointClasses": [],
                "unsatisfiable": [],
                "engine": "robot/hermit",
                "ms": payload.get("ms"),
            }
        graph = Graph()
        try:
            graph.parse(data=reasoned, format="turtle")
        except Exception as exc:  # rdflib raises several parser types
            raise PortError(
                code="Internal",
                message=f"cannot parse robot/hermit reasoned graph: {exc}",
                provider="robot/hermit",
                provider_code="E_CONSISTENCY_BAD_RESULT",
            ) from exc

        sub_class: list[dict[str, str]] = []
        equivalent: list[dict[str, str]] = []
        disjoint: list[dict[str, str]] = []
        unsatisfiable: list[str] = []
        for child, _, parent in graph.triples((None, RDFS_SUBCLASS, None)):
            if parent == OWL_NOTHING:
                unsatisfiable.append(str(child))
                continue
            if parent == OWL_THING or child == parent:
                continue
            sub_class.append({"sub": str(child), "super": str(parent)})
        for left, _, right in graph.triples((None, URIRef(f"{OWL}equivalentClass"), None)):
            if left == right or OWL_NOTHING in (left, right):
                continue
            equivalent.append({"left": str(left), "right": str(right)})
        for left, _, right in graph.triples((None, URIRef(f"{OWL}disjointWith"), None)):
            # ROBOT emits owl:Nothing owl:disjointWith <every named class>;
            # that is trivially true and must not be reported as a finding.
            if left == right or OWL_NOTHING in (left, right) or OWL_THING in (left, right):
                continue
            disjoint.append({"left": str(left), "right": str(right)})
        return {
            "subClassOf": sub_class,
            "equivalentClasses": equivalent,
            "disjointClasses": disjoint,
            "unsatisfiable": unsatisfiable,
            "engine": "robot/hermit",
            "ms": payload.get("ms"),
        }
