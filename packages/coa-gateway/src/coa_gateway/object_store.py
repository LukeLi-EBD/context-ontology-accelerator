"""Local filesystem implementation of the COA ``ObjectStore`` (N8).

Contract source: ``doc/_design/81-COA契约与platform_core整合方案-2026-11-08.md`` N8
and ``packages/platform-core/src/platform_core/ports.py::ObjectStorePort``
(put/get/head/delete/list + capabilities). The port is not imported on purpose:
``platform_core`` drags pydantic/psycopg into a gateway that must stay light.

Content is stored as raw bytes plus a JSON sidecar. No presigning here, and
``capabilities()`` says so instead of returning a fake URL.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ObjectStoreError(RuntimeError):
    """Base class for the N8 error names."""


class ObjectNotFound(ObjectStoreError, KeyError):
    """The bucket/key does not exist."""


class PreconditionFailed(ObjectStoreError):
    """A caller-supplied precondition did not hold."""


class ObjectTooLarge(ObjectStoreError):
    """Body exceeds the configured limit."""


class UnsupportedOperation(ObjectStoreError):
    """The capability is not provided (e.g. presign on a local store)."""


def _now() -> str:
    return datetime.now(UTC).isoformat()


class FsObjectStore:
    """``ObjectStore`` over a directory: ``<root>/<bucket>/<key>`` plus ``<key>.meta.json``."""

    def __init__(self, root: str | Path, *, max_bytes: int = 64 * 1024 * 1024) -> None:
        self._root = Path(root)
        self._max_bytes = max_bytes

    @property
    def backend(self) -> str:
        return "fs"

    def _path(self, bucket: str, key: str) -> tuple[Path, Path]:
        for part in (bucket, key):
            if not part or part in {".", ".."} or ".." in Path(part).parts:
                raise PreconditionFailed(f"unsafe bucket/key component: {part!r}")
        body = self._root / bucket / key
        meta = body.with_name(body.name + ".meta.json")
        return body, meta

    # -- N8 ------------------------------------------------------------
    def put(
        self,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if len(body) > self._max_bytes:
            raise ObjectTooLarge(f"body is {len(body)} bytes, limit is {self._max_bytes}")
        path, meta_path = self._path(bucket, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(body).hexdigest()
        path.write_bytes(body)
        record = {
            "bucket": bucket,
            "key": key,
            "size": len(body),
            "sha256": digest,
            "content_type": content_type,
            "metadata": dict(metadata or {}),
            "updated_at": _now(),
        }
        meta_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        return record

    def get(self, bucket: str, key: str) -> tuple[bytes, dict[str, Any]]:
        path, meta_path = self._path(bucket, key)
        if not path.is_file():
            raise ObjectNotFound(f"{bucket}/{key}")
        return path.read_bytes(), json.loads(meta_path.read_text(encoding="utf-8"))

    def head(self, bucket: str, key: str) -> dict[str, Any]:
        path, meta_path = self._path(bucket, key)
        if not path.is_file():
            raise ObjectNotFound(f"{bucket}/{key}")
        return json.loads(meta_path.read_text(encoding="utf-8"))

    def delete(self, bucket: str, key: str) -> None:
        path, meta_path = self._path(bucket, key)
        path.unlink(missing_ok=True)
        meta_path.unlink(missing_ok=True)

    def list(self, bucket: str, prefix: str = "", limit: int = 100) -> list[dict[str, Any]]:
        base = self._root / bucket
        if not base.is_dir():
            return []
        rows: list[dict[str, Any]] = []
        for meta_path in sorted(base.rglob("*.meta.json")):
            key = str(meta_path.relative_to(base))[: -len(".meta.json")]
            if prefix and not key.startswith(prefix):
                continue
            rows.append(json.loads(meta_path.read_text(encoding="utf-8")))
            if len(rows) >= max(limit, 0):
                break
        return rows

    def capabilities(self) -> dict[str, Any]:
        return {"backend": "fs", "presign": False, "range": True, "versioning": False, "upload_mode": "proxy"}

    def presign_put(self, key: str, ttl: int, content_type: str) -> dict[str, Any]:
        raise UnsupportedOperation(
            "local fs object store has no presign capability; upload_mode is 'proxy'"
        )

    def presign_get(self, key: str, ttl: int) -> str:
        raise UnsupportedOperation(
            "local fs object store has no presign capability; fetch through the proxy endpoint"
        )

    def health_check(self) -> dict[str, Any]:
        try:
            self._root.mkdir(parents=True, exist_ok=True)
            usage = shutil.disk_usage(self._root)
            return {
                "ok": True,
                "backend": self.backend,
                "root": str(self._root),
                "buckets": sorted(p.name for p in self._root.iterdir() if p.is_dir()),
                "free_pct": round(usage.free / usage.total * 100, 1),
            }
        except Exception as exc:  # noqa: BLE001 - health_check must not raise
            return {"ok": False, "backend": self.backend, "root": str(self._root), "error": f"{type(exc).__name__}: {exc}"}


__all__ = [
    "FsObjectStore",
    "ObjectNotFound",
    "ObjectStoreError",
    "ObjectTooLarge",
    "PreconditionFailed",
    "UnsupportedOperation",
]
