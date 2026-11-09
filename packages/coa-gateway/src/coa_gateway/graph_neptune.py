"""AWS Neptune implementation of the graph contract — SigV4-shaped, HTTP only.

This is a *thin* client: the request it builds is the one Neptune expects
(POST ``/sparql``, form-encoded query, SigV4 ``Authorization`` with service
``neptune-db``, ``Accept: application/sparql-results+json``), and it parses the
standard SPARQL JSON result set.

What it does **not** prove: real Neptune behaviour (IAM, VPC, engine quirks, cold
start). With no AWS account this is exercised against a local HTTP stub that
checks the signing shape and returns a canned SPARQL JSON body. See
``scripts/neptune_stub.py`` and ``scripts/prove_neptune_shape.py``.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

import httpx


class NeptuneGraphClient:
    """``GraphClient`` against a Neptune SPARQL endpoint using SigV4 request signing."""

    backend = "aws-neptune"
    service = "neptune-db"

    def __init__(
        self,
        endpoint: str,
        *,
        region: str,
        access_key: str,
        secret_key: str,
        session_token: str | None = None,
        timeout_s: float = 10.0,
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._region = region
        self._access_key = access_key
        self._secret_key = secret_key
        self._session_token = session_token
        self._timeout_s = timeout_s

    # -- SigV4 ---------------------------------------------------------
    def _sign(self, body: str, *, now: datetime) -> dict[str, str]:
        stamp = now.strftime("%Y%m%dT%H%M%SZ")
        day = now.strftime("%Y%m%d")
        host = httpx.URL(self._endpoint).host
        payload_hash = hashlib.sha256(body.encode()).hexdigest()

        headers = {"host": host, "x-amz-date": stamp, "content-type": "application/x-www-form-urlencoded"}
        if self._session_token:
            headers["x-amz-security-token"] = self._session_token
        signed_headers = ";".join(sorted(headers))
        canonical_headers = "".join(f"{name}:{headers[name]}\n" for name in sorted(headers))
        canonical_request = "\n".join(
            ["POST", "/sparql", "", canonical_headers, signed_headers, payload_hash]
        )
        scope = f"{day}/{self._region}/{self.service}/aws4_request"
        string_to_sign = "\n".join(
            [
                "AWS4-HMAC-SHA256",
                stamp,
                scope,
                hashlib.sha256(canonical_request.encode()).hexdigest(),
            ]
        )

        def _hmac(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode(), hashlib.sha256).digest()

        signing_key = _hmac(_hmac(_hmac(_hmac(f"AWS4{self._secret_key}".encode(), day), self._region), self.service),
                            "aws4_request")
        signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()
        credential = f"{self._access_key}/{scope}"

        out = {
            "Authorization": (
                f"AWS4-HMAC-SHA256 Credential={credential}, "
                f"SignedHeaders={signed_headers}, Signature={signature}"
            ),
            "X-Amz-Date": stamp,
            "X-Amz-Content-Sha256": payload_hash,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/sparql-results+json",
        }
        if self._session_token:
            out["X-Amz-Security-Token"] = self._session_token
        return out

    async def _post(self, sparql: str) -> dict[str, Any]:
        body = "query=" + quote(sparql, safe="")
        headers = self._sign(body, now=datetime.now(UTC))
        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            response = await client.post(
                f"{self._endpoint}/sparql",
                content=body,
                headers={k: v for k, v in headers.items() if not k.lower().startswith("host")},
            )
            response.raise_for_status()
            return response.json()

    # -- GraphClient ---------------------------------------------------
    async def query(self, sparql: str) -> list[dict[str, Any]]:
        payload = await self._post(sparql)
        bindings = (payload.get("results") or {}).get("bindings") or []
        return [
            {name: value.get("value") for name, value in row.items()}
            for row in bindings
        ]

    async def ask(self, sparql: str) -> bool:
        payload = await self._post(sparql)
        return bool(payload.get("boolean", False))

    async def health_check(self) -> dict[str, Any]:
        try:
            alive = await self.ask("ASK { ?s ?p ?o }")
            return {
                "ok": True,
                "backend": self.backend,
                "endpoint": self._endpoint,
                "region": self._region,
                "signed": True,
                "has_data": alive,
            }
        except Exception as exc:  # noqa: BLE001 - health_check must not raise
            return {
                "ok": False,
                "backend": self.backend,
                "endpoint": self._endpoint,
                "region": self._region,
                "error": f"{type(exc).__name__}: {exc}",
            }


__all__ = ["NeptuneGraphClient"]
