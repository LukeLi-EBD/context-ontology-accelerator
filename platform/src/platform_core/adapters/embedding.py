"""EmbeddingClient adapter (S3): local BGE-M3 over HTTP, OpenAI-compatible, fake, disabled.

Boundary (D18): no embedding math here. `local-bge` / `openai-compatible` delegate
to an OpenAI-compatible `/v1/embeddings` endpoint (TEI / any provider). The `fake`
provider exists only for acceptance tests and is isolated by model name.
"""

from __future__ import annotations

import hashlib
import logging
import math
import threading
import time
from typing import Any

import httpx

from ..config import EmbeddingConfig
from ..errors import PortError
from ..ports import EnvSecretProvider, Manifest

log = logging.getLogger(__name__)

FAKE_MODEL = "fake-hash-1024"


class EmbeddingClient:
    port = "EmbeddingClient"

    def __init__(self, config: EmbeddingConfig, secrets: EnvSecretProvider) -> None:
        self._config = config
        self._secrets = secrets
        self._http: httpx.Client | None = None
        # R5/S13H-11: one batch request in flight at a time. FastAPI runs sync
        # adapters in a thread pool, so a plain semaphore is enough and it keeps
        # the local CPU model from being fed by several documents at once.
        self._gate = threading.BoundedSemaphore(1)
        # S14H-CORES: per-batch timing samples (reset/drain by the bench command).
        self.metrics: list[dict[str, Any]] = []

    def reset_metrics(self) -> None:
        self.metrics.clear()

    def drain_metrics(self) -> list[dict[str, Any]]:
        out = list(self.metrics)
        self.metrics.clear()
        return out

    def manifest(self) -> Manifest:
        return Manifest(
            provider=self._config.provider,
            port=self.port,
            provider_version="s3.1",
            capabilities=[]
            if self._config.provider == "disabled"
            else ["embedding.embed"],
            limits={
                "dimensions": self._config.dimensions,
                "batch_size": self._config.batch_size,
                "batch_max": self._config.batch_max,
                "chunk_per_request_max": self._config.chunk_per_request_max,
                "request_max_chars": self._config.request_max_chars,
                "request_timeout_s": self._config.request_timeout_s,
                "max_chunks_per_sec": self._config.max_chunks_per_sec,
                "max_in_flight": 1,
            },
            notes={
                "slice": "S3",
                "model": self.model_name(),
                "endpoint": self._endpoint(self._config.provider) if self._http_provider() else None,
                "fake": self._config.provider == "fake",
                "service_enabled": self._config.service_enabled,
            },
        )

    # ---- identity --------------------------------------------------------

    def _http_provider(self) -> bool:
        return self._config.provider in ("local-bge", "openai-compatible", "ark")

    def model_name(self) -> str:
        if self._config.provider == "fake":
            return FAKE_MODEL
        if self._config.provider == "ark":
            return self._config.ark_model
        return self._config.model

    def dimensions(self) -> int:
        if self._config.provider == "ark":
            return self._config.ark_dimensions
        return self._config.dimensions

    def partition(self, provider: str | None = None) -> dict[str, Any]:
        """Describe one embedding partition without loading any secret."""
        name = provider or self._config.provider
        if name == "ark":
            return {
                "provider": "ark",
                "model": self._config.ark_model,
                "dimensions": self._config.ark_dimensions,
                "batchSize": self._config.batch_size,
            }
        if name == "fake":
            return {
                "provider": "fake",
                "model": FAKE_MODEL,
                "dimensions": self._config.dimensions,
                "batchSize": self._config.batch_size,
            }
        return {
            "provider": "local-bge",
            "model": self._config.model,
            "dimensions": self._config.dimensions,
            "batchSize": self._config.batch_size,
        }

    # ---- EmbeddingClient v1 ---------------------------------------------

    def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        return self.embed_with(
            self._config.provider, model or self.model_name(), texts, self.dimensions()
        )

    def embed_with(
        self,
        provider: str,
        model: str,
        texts: list[str],
        dimensions: int,
    ) -> list[list[float]]:
        """Embed against an explicit partition (used by reindex and the pointer)."""
        if not texts:
            return []
        if provider == "disabled":
            raise PortError(
                code="Unsupported",
                message="embedding.provider=disabled: no embedding client is assembled",
                provider="disabled",
                provider_code="E_EMBED_DISABLED",
                details={"key": "embedding.provider"},
            )
        if provider == "fake":
            return [self._fake_vector(text, dimensions) for text in texts]

        vectors: list[list[float]] = []
        limit = float(self._config.max_chunks_per_sec)
        started = time.monotonic()
        done = 0
        for batch in self._batches(texts):
            timeout_s = self._batch_timeout(batch)
            attempt = 0
            while True:
                try:
                    gate_started = time.monotonic()
                    with self._gate:
                        wait_ms = (time.monotonic() - gate_started) * 1000.0
                        service_started = time.monotonic()
                        vectors.extend(
                            self._request(batch, model, provider, dimensions, timeout_s)
                        )
                        service_ms = (time.monotonic() - service_started) * 1000.0
                    self.metrics.append(
                        {
                            "chunks": len(batch),
                            "chars": max((len(text) for text in batch), default=0),
                            "waitMs": round(wait_ms, 3),
                            "serviceMs": round(service_ms, 3),
                        }
                    )
                    break
                except PortError as exc:
                    # S14H-17: only timeouts are retried (2x with linear backoff);
                    # auth/dimension/parse errors stay terminal.
                    if exc.provider_code != "E_EMBED_TIMEOUT" or attempt >= self._config.retry_max:
                        raise
                    attempt += 1
                    delay = self._config.retry_backoff_s * attempt
                    log.warning(
                        "embedding timeout, retrying",
                        extra={
                            "event": {
                                "event": "embed_retry",
                                "attempt": attempt,
                                "timeoutS": round(timeout_s, 2),
                                "chars": max(len(text) for text in batch),
                            }
                        },
                    )
                    time.sleep(delay)
                    timeout_s = min(timeout_s * 1.5, float(self._config.timeout_max_s))
            done += len(batch)
            # 保底限速：给同机的 API/PG/文件 IO 留时间。0 表示不限。
            if limit > 0:
                ahead = done / limit - (time.monotonic() - started)
                if ahead > 0:
                    time.sleep(min(ahead, 5.0))
        return vectors

    def _batch_timeout(self, batch: list[str]) -> float:
        """Adaptive timeout: base + perChar * longest chunk, capped at 120s."""
        base = float(self._config.timeout_ms) / 1000.0
        longest = max((len(text) for text in batch), default=0)
        return min(
            base + self._config.adaptive_timeout_per_char_s * longest,
            float(self._config.timeout_max_s),
        )

    def _batches(self, texts: list[str]) -> list[list[str]]:
        """Group texts by count AND total chars; long chunks always go solo.

        TEI cpu-1.8 panics (`queue.rs: Full(..)`) when an incoming batch has to be
        split because it exceeds --max-batch-tokens (2048 in compose). Keeping each
        request under a char budget avoids that split path entirely.
        """
        size = self.effective_batch_size()
        budget = int(self._config.request_max_chars)
        long_chars = int(self._config.long_chunk_chars)
        groups: list[list[str]] = []
        current: list[str] = []
        current_chars = 0
        for text in texts:
            width = len(text)
            if width >= long_chars:
                if current:
                    groups.append(current)
                    current, current_chars = [], 0
                groups.append([text])
                continue
            if current and (len(current) >= size or current_chars + width > budget):
                groups.append(current)
                current, current_chars = [], 0
            current.append(text)
            current_chars += width
        if current:
            groups.append(current)
        return groups

    def effective_batch_size(self) -> int:
        """Smallest of the configured caps; never exceeds the per-request limit."""
        return max(
            1,
            min(
                self._config.batch_size,
                self._config.batch_max,
                self._config.chunk_per_request_max,
            ),
        )

    def available(self) -> bool:
        if self._config.provider == "fake":
            return True
        if self._config.provider == "disabled":
            return False
        if self._config.provider == "ark":
            try:
                return bool(self._secrets.get(self._config.ark_api_key_env))
            except PortError:
                return False
        base = self._config.endpoint.rstrip("/")
        root = base[:-3] if base.endswith("/v1") else base
        probes = [f"{root}/health", f"{base}/models"]
        for url in probes:
            try:
                if self._client().get(url).status_code == 200:
                    return True
            except httpx.HTTPError:
                continue
        return False

    # ---- internals -------------------------------------------------------

    def _endpoint(self, provider: str) -> str:
        if provider == "ark":
            return self._config.ark_base_url
        return self._config.endpoint

    def _url(self, suffix: str, provider: str | None = None) -> str:
        return f"{self._endpoint(provider or self._config.provider).rstrip('/')}/{suffix}"

    def _client(self) -> httpx.Client:
        if self._http is None:
            timeout_s = max(self._config.timeout_ms / 1000.0, float(self._config.request_timeout_s))
            self._http = httpx.Client(timeout=httpx.Timeout(timeout_s))
        return self._http

    def close(self) -> None:
        if self._http is not None:
            self._http.close()
            self._http = None

    def _headers(self, provider: str | None = None) -> dict[str, str]:
        key_env = (
            self._config.ark_api_key_env
            if (provider or self._config.provider) == "ark"
            else self._config.api_key_env
        )
        try:
            key = self._secrets.get(key_env)
        except PortError:
            return {}
        return {"Authorization": f"Bearer {key}"}

    def _request(
        self,
        texts: list[str],
        model: str | None,
        provider: str | None = None,
        dimensions: int | None = None,
        timeout_s: float | None = None,
    ) -> list[list[float]]:
        active = provider or self._config.provider
        expected = dimensions if dimensions is not None else self.dimensions()
        payload = {"model": model or self.model_name(), "input": texts}
        try:
            response = self._client().post(
                self._url("embeddings", active),
                json=payload,
                headers=self._headers(active),
                timeout=httpx.Timeout(timeout_s) if timeout_s else None,
            )
        except httpx.TimeoutException as exc:
            raise PortError(
                code="DeadlineExceeded",
                message=f"embedding request timed out after {self._config.timeout_ms} ms",
                provider=self._config.provider,
                provider_code="E_EMBED_TIMEOUT",
                retryable=True,
            ) from exc
        except httpx.HTTPError as exc:
            raise PortError(
                code="Unavailable",
                message=f"cannot reach embedding endpoint {self._config.endpoint}: {exc}",
                provider=self._config.provider,
                provider_code="E_EMBED_UNAVAILABLE",
                retryable=True,
            ) from exc

        if response.status_code in (401, 403):
            raise PortError(
                code="PermissionDenied",
                message=f"embedding endpoint rejected credentials (HTTP {response.status_code})",
                provider=self._config.provider,
                provider_code="E_EMBED_AUTH",
            )
        if response.status_code == 429:
            raise PortError(
                code="ResourceExhausted",
                message="embedding endpoint rate-limited the request (HTTP 429)",
                provider=self._config.provider,
                provider_code="E_EMBED_RATE",
                retryable=True,
            )
        if response.status_code >= 400:
            raise PortError(
                code="Unavailable",
                message=(
                    f"embedding endpoint returned HTTP {response.status_code}: "
                    f"{response.text[:200]}"
                ),
                provider=self._config.provider,
                provider_code="E_EMBED_UNAVAILABLE",
            )

        try:
            body: dict[str, Any] = response.json()
            data = body["data"]
            vectors = [item["embedding"] for item in data]
        except (ValueError, KeyError, TypeError) as exc:
            raise PortError(
                code="DataLoss",
                message="embedding endpoint returned a malformed OpenAI-compatible payload",
                provider=self._config.provider,
                provider_code="E_EMBED_BAD_RESPONSE",
                details={"body": response.text[:200]},
            ) from exc

        if len(vectors) != len(texts):
            raise PortError(
                code="DataLoss",
                message=(
                    f"embedding endpoint returned {len(vectors)} vectors for "
                    f"{len(texts)} inputs"
                ),
                provider=self._config.provider,
                provider_code="E_EMBED_BAD_RESPONSE",
            )
        for vector in vectors:
            self._check_dimensions(vector, expected)
        return vectors

    def _check_dimensions(self, vector: list[float], expected: int | None = None) -> None:
        target = expected if expected is not None else self.dimensions()
        if len(vector) != target:
            raise PortError(
                code="InvalidArgument",
                message=(
                    f"embedding dimension mismatch: got {len(vector)}, "
                    f"expected {target}"
                ),
                provider=self._config.provider,
                provider_code="E_EMBED_DIM_MISMATCH",
                details={"got": len(vector), "expected": target},
            )

    def _fake_vector(self, text: str, dimensions: int | None = None) -> list[float]:
        """Deterministic char-trigram hashing for tests; never used for real indexing.

        Hashed character trigrams (not an embedding model) keep acceptance queries
        meaningful while staying deterministic and dependency-free.
        """
        size = dimensions if dimensions is not None else self._config.dimensions
        values = [0.0] * size
        compact = "".join(ch for ch in text if not ch.isspace())
        tokens = (
            [compact]
            if len(compact) <= 3
            else [compact[index : index + 3] for index in range(len(compact) - 2)]
        )
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            values[int.from_bytes(digest[:4], "big") % size] += 1.0
        norm = math.sqrt(sum(value * value for value in values)) or 1.0
        return [value / norm for value in values]
