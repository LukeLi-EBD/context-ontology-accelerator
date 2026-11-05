"""ReasonerClient adapter (S5): HTTP -> ROBOT/ELK container.

Boundary (D18): this adapter never classifies or checks consistency itself. It
forwards the two source graphs to the reasoner container, which shells out to
`robot reason`, and maps transport failures to stable port errors.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ..config import ReasoningConfig
from ..errors import PortError
from ..ports import Manifest

log = logging.getLogger(__name__)


class ReasonerClient:
    port = "ReasoningService"

    def __init__(self, config: ReasoningConfig, robot_version: str = "unknown") -> None:
        self._config = config
        self._robot_version = robot_version
        self._http: httpx.Client | None = None

    def manifest(self) -> Manifest:
        return Manifest(
            provider=f"robot/{self._config.profile}",
            port=self.port,
            provider_version=self._config.engine,
            capabilities=["reason.materialize", "reason.consistent", "reason.rdfs"],
            limits={
                "timeout_ms": self._config.timeout_ms,
                "max_input_bytes": self._config.max_input_bytes,
            },
            notes={
                "slice": "S5",
                "endpoint": self._config.endpoint,
                "engine": self._config.engine,
                "profile": self._config.profile,
                "inferred_graph_prefix": self._config.inferred_graph_prefix,
            },
        )

    def close(self) -> None:
        if self._http is not None:
            self._http.close()
            self._http = None

    def _client(self) -> httpx.Client:
        if self._http is None:
            self._http = httpx.Client(timeout=httpx.Timeout(self._config.timeout_ms / 1000.0))
        return self._http

    def health(self) -> dict[str, Any]:
        try:
            response = self._client().get(f"{self._config.endpoint.rstrip('/')}/healthz")
        except httpx.HTTPError as exc:
            raise PortError(
                code="Unavailable",
                message=f"reasoner is unreachable at {self._config.endpoint}: {exc}",
                provider="robot",
                provider_code="E_REASONER_UNAVAILABLE",
                retryable=True,
            ) from exc
        if response.status_code != 200:
            raise PortError(
                code="Unavailable",
                message=f"reasoner health returned HTTP {response.status_code}",
                provider="robot",
                provider_code="E_REASONER_UNAVAILABLE",
                retryable=True,
            )
        body = response.json() if response.content else {}
        return {
            "available": True,
            "robotVersion": body.get("robotVersion", self._robot_version),
            "engine": body.get("engine", self._config.engine),
        }

    def reason(
        self,
        tbox_nt: bytes,
        abox_nt: bytes,
        profile: str | None = None,
        consistency_first: bool | None = None,
    ) -> dict[str, Any]:
        payload_bytes = len(tbox_nt) + len(abox_nt)
        if payload_bytes > self._config.max_input_bytes:
            raise PortError(
                code="ResourceExhausted",
                message=(
                    f"reasoning input is {payload_bytes} bytes, "
                    f"limit reasoning.max_input_bytes={self._config.max_input_bytes}"
                ),
                provider="robot",
                provider_code="E_REASONING_INPUT_TOO_LARGE",
                details={"bytes": payload_bytes, "limit": self._config.max_input_bytes},
            )
        body = {
            "tbox": tbox_nt.decode("utf-8"),
            "abox": abox_nt.decode("utf-8"),
            "profile": profile or self._config.profile,
            "consistencyFirst": (
                self._config.consistency_first
                if consistency_first is None
                else consistency_first
            ),
        }
        try:
            response = self._client().post(
                f"{self._config.endpoint.rstrip('/')}/v1/reason", json=body
            )
        except httpx.TimeoutException as exc:
            raise PortError(
                code="DeadlineExceeded",
                message=f"reasoner timed out after {self._config.timeout_ms} ms",
                provider="robot",
                provider_code="E_REASONER_TIMEOUT",
                retryable=True,
            ) from exc
        except httpx.HTTPError as exc:
            raise PortError(
                code="Unavailable",
                message=f"reasoner is unreachable at {self._config.endpoint}: {exc}",
                provider="robot",
                provider_code="E_REASONER_UNAVAILABLE",
                retryable=True,
            ) from exc

        if response.status_code >= 400:
            raise PortError(
                code="DataLoss",
                message=(
                    f"reasoner returned HTTP {response.status_code}: {response.text[:300]}"
                ),
                provider="robot",
                provider_code="E_REASONER_BAD_RESPONSE",
                details={"status": response.status_code},
            )
        try:
            parsed = response.json()
        except ValueError as exc:
            raise PortError(
                code="DataLoss",
                message="reasoner returned a non-JSON body",
                provider="robot",
                provider_code="E_REASONER_BAD_RESPONSE",
            ) from exc
        if not all(key in parsed for key in ("consistent", "reasoned")):
            raise PortError(
                code="DataLoss",
                message="reasoner response lacks consistent/reasoned fields",
                provider="robot",
                provider_code="E_REASONER_BAD_RESPONSE",
                details={"keys": sorted(parsed)},
            )
        return parsed

    def rdfs_closure(self, tbox_nt: bytes, abox_nt: bytes) -> dict[str, Any]:
        """OQ-39 stage 1: run Jena's RDFS closure inside the reasoner container."""
        payload_bytes = len(tbox_nt) + len(abox_nt)
        if payload_bytes > self._config.max_input_bytes:
            raise PortError(
                code="ResourceExhausted",
                message=(
                    f"RDFS input is {payload_bytes} bytes, "
                    f"limit reasoning.max_input_bytes={self._config.max_input_bytes}"
                ),
                provider="jena",
                provider_code="E_REASONING_INPUT_TOO_LARGE",
                details={"bytes": payload_bytes, "limit": self._config.max_input_bytes},
            )
        body = {"tbox": tbox_nt.decode("utf-8"), "abox": abox_nt.decode("utf-8")}
        try:
            response = self._client().post(
                f"{self._config.endpoint.rstrip('/')}/v1/rdfs", json=body
            )
        except httpx.TimeoutException as exc:
            raise PortError(
                code="DeadlineExceeded",
                message=f"RDFS closure timed out after {self._config.timeout_ms} ms",
                provider="jena",
                provider_code="E_REASONER_TIMEOUT",
                retryable=True,
            ) from exc
        except httpx.HTTPError as exc:
            raise PortError(
                code="Unavailable",
                message=f"reasoner is unreachable at {self._config.endpoint}: {exc}",
                provider="robot",
                provider_code="E_REASONER_UNAVAILABLE",
                retryable=True,
            ) from exc

        if response.status_code >= 400:
            raise PortError(
                code="DataLoss",
                message=(
                    f"RDFS closure returned HTTP {response.status_code}: {response.text[:300]}"
                ),
                provider="jena",
                provider_code="E_RDFS_FAILED",
                details={"status": response.status_code},
            )
        try:
            parsed = response.json()
        except ValueError as exc:
            raise PortError(
                code="DataLoss",
                message="RDFS closure returned a non-JSON body",
                provider="jena",
                provider_code="E_RDFS_FAILED",
            ) from exc
        if "reasoned" not in parsed:
            raise PortError(
                code="DataLoss",
                message="RDFS closure response lacks 'reasoned'",
                provider="jena",
                provider_code="E_REASONER_BAD_RESPONSE",
                details={"keys": sorted(parsed)},
            )
        return parsed
