"""``ObjectStorePort`` on the local filesystem.

This is a real provider, not a shell: it stores bytes under
``<root>/<bucket>/<key>`` and keeps one JSON sidecar per object under
``<root>/.coa-meta/<bucket>/<key>.json``. It needs neither PostgreSQL nor S3,
which is what the plan's local stack requires (plan §5 stage 1).

Semantics follow the port:

- ``get``/``head`` of a missing key raise ``PortError(not_found)``;
- ``delete`` of an absent key is a no-op;
- ``etag`` is the SHA-256 of the body, stable across reads;
- ``probe`` never raises.

There is no presigning and no multipart upload; both are outside the port.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

from coa_ports import ObjectInfo, PortError, PortErrorCode

_BUCKET_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")


def _invalid(message: str, details: Mapping[str, Any] | None = None) -> PortError:
    return PortError(
        PortErrorCode.INVALID_ARGUMENT,
        message,
        provider="fs",
        provider_code="E_OBJECT_BAD_KEY",
        details=details,
    )


class FsObjectStore:
    """A filesystem-backed ``ObjectStorePort``."""

    provider = "fs"

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)
        self._meta = self._root / ".coa-meta"
        self._meta.mkdir(parents=True, exist_ok=True)

    # ── ObjectStorePort ─────────────────────────────────────────────────────

    def put(
        self,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str = "application/octet-stream",
        metadata: Mapping[str, str] | None = None,
    ) -> ObjectInfo:
        """Store ``body`` and return its metadata."""
        path = self._path(bucket, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.part")
        tmp.write_bytes(body)
        os.replace(tmp, path)

        digest = hashlib.sha256(body).hexdigest()
        info = ObjectInfo(
            bucket=bucket,
            key=key,
            size=len(body),
            content_type=content_type,
            metadata=dict(metadata or {}),
            etag=digest,
        )
        self._write_meta(info)
        return info

    def get(self, bucket: str, key: str) -> tuple[bytes, ObjectInfo]:
        """Return ``(body, metadata)``; a missing key raises ``not_found``."""
        info = self.head(bucket, key)
        try:
            return self._path(bucket, key).read_bytes(), info
        except OSError as exc:
            raise PortError(
                PortErrorCode.INTERNAL,
                f"cannot read object: {exc}",
                provider="fs",
                provider_code="E_OBJECT_READ",
            ) from exc

    def head(self, bucket: str, key: str) -> ObjectInfo:
        """Return metadata only; a missing key raises ``not_found``."""
        meta_path = self._meta_path(bucket, key)
        try:
            payload = json.loads(meta_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise PortError(
                PortErrorCode.NOT_FOUND,
                f"object {bucket}/{key} does not exist",
                provider="fs",
                provider_code="E_OBJECT_NOT_FOUND",
                details={"bucket": bucket, "key": key},
            ) from exc
        return ObjectInfo(
            bucket=str(payload.get("bucket", bucket)),
            key=str(payload.get("key", key)),
            size=int(payload.get("size", 0)),
            content_type=str(payload.get("content_type", "application/octet-stream")),
            metadata=dict(payload.get("metadata") or {}),
            etag=str(payload.get("etag", "")),
        )

    def delete(self, bucket: str, key: str) -> None:
        """Delete one object; deleting an absent key is a no-op."""
        self._path(bucket, key).unlink(missing_ok=True)
        self._meta_path(bucket, key).unlink(missing_ok=True)

    def list(self, bucket: str, prefix: str = "", limit: int = 100) -> tuple[ObjectInfo, ...]:
        """List objects under ``prefix``, sorted by key."""
        if limit <= 0:
            return ()
        base = self._bucket_dir(bucket)
        if not base.exists():
            return ()
        found: list[ObjectInfo] = []
        for path in sorted(p for p in base.rglob("*") if p.is_file()):
            key = path.relative_to(base).as_posix()
            if not key.startswith(prefix):
                continue
            try:
                found.append(self.head(bucket, key))
            except PortError:
                continue  # a body without a sidecar is not a complete object
            if len(found) >= limit:
                break
        return tuple(found)

    def probe(self) -> Mapping[str, Any]:
        """Reachability snapshot; never raises."""
        try:
            if not self._root.is_dir():
                raise OSError(f"{self._root} is not a directory")
            os.access(self._root, os.W_OK)
            return {"status": "ok", "provider": "fs", "root": str(self._root)}
        except Exception as exc:  # noqa: BLE001 - probe must never raise
            return {
                "status": "unavailable",
                "provider": "fs",
                "provider_code": type(exc).__name__,
            }

    # ── internals ───────────────────────────────────────────────────────────

    def _bucket_dir(self, bucket: str) -> Path:
        if not bucket or any(ch not in _BUCKET_CHARS for ch in bucket):
            raise _invalid(f"invalid bucket name: {bucket!r}", {"bucket": bucket})
        return self._root / bucket

    def _path(self, bucket: str, key: str) -> Path:
        parts = self._key_parts(key)
        return self._bucket_dir(bucket).joinpath(*parts)

    def _meta_path(self, bucket: str, key: str) -> Path:
        parts = self._key_parts(key)
        return self._meta.joinpath(bucket, *parts[:-1], f"{parts[-1]}.json")

    @staticmethod
    def _key_parts(key: str) -> tuple[str, ...]:
        if not key or "\\" in key:
            raise _invalid(f"invalid object key: {key!r}", {"key": key})
        pure = PurePosixPath(key)
        if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
            raise _invalid(f"invalid object key: {key!r}", {"key": key})
        return pure.parts

    def _write_meta(self, info: ObjectInfo) -> None:
        path = self._meta_path(info.bucket, info.key)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "bucket": info.bucket,
            "key": info.key,
            "size": info.size,
            "content_type": info.content_type,
            "metadata": dict(info.metadata),
            "etag": info.etag,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


__all__ = ["FsObjectStore"]
