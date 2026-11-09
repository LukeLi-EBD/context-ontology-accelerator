# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""S3 artifacts (local) on the filesystem, served by the local API bridge.

``coa_ontology.dynamo_store`` keeps proposal artifacts, job datasource manifests
and generated ontology downloads in S3 through the boto3 calls below. This
module provides a filesystem-backed client with the same surface:

    put_object / get_object / head_object / delete_object / delete_objects
    copy_object / list_objects_v2 (+ get_paginator)
    generate_presigned_url("get_object" | "put_object", ...)

Objects live under ``COA_LOCAL_OBJECT_ROOT``. ``NoSuchKey`` is a real
``botocore.exceptions.ClientError`` with code ``NoSuchKey``, because upstream
callers branch on ``except ClientError`` when deciding "artifact absent" versus
"transport failure". Presigned URLs point at the local bridge
(``COA_LOCAL_OBJECT_BASE``, default ``http://127.0.0.1:8099/_local/objects``)
which serves bytes for GET (with the stored Content-Type and
Content-Disposition) and accepts them for PUT. That endpoint is object
transport, not a business route — the same role S3 plays in AWS.

Configuration (fails closed):

    COA_PROVIDER_ONTOLOGY_OBJECTS  fs | s3            (required)
    COA_LOCAL_OBJECT_ROOT          directory          (required for fs)
    COA_LOCAL_OBJECT_BASE          URL prefix         (default bridge route)
    COA_LOCAL_OBJECT_BUCKET        logical bucket     (default
                                   ``ONTOLOGY_ARTIFACTS_BUCKET`` when set)
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import quote

_PROVIDERS = ("fs", "s3")

try:  # boto3 is a hard dependency of the ontology engine; keep import defensive
    from botocore.exceptions import ClientError
except Exception:  # pragma: no cover - only for stripped-down environments

    class ClientError(Exception):  # type: ignore[no-redef]
        def __init__(self, error_response: dict | None = None, operation_name: str = "") -> None:
            super().__init__(str(error_response))
            self.response = error_response or {}


def _provider() -> str:
    raw = os.environ.get("COA_PROVIDER_ONTOLOGY_OBJECTS", "").strip().lower()
    if not raw:
        raise RuntimeError(
            "COA_PROVIDER_ONTOLOGY_OBJECTS is required (fs|s3); refusing to start "
            "without an explicitly selected ontology object store"
        )
    if raw not in _PROVIDERS:
        raise RuntimeError(f"Unknown COA_PROVIDER_ONTOLOGY_OBJECTS={raw!r}; expected one of {_PROVIDERS}")
    return raw


def object_root() -> Path:
    raw = os.environ.get("COA_LOCAL_OBJECT_ROOT", "").strip()
    if not raw:
        raise RuntimeError("COA_LOCAL_OBJECT_ROOT is required when COA_PROVIDER_ONTOLOGY_OBJECTS=fs")
    root = Path(raw).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def object_base() -> str:
    return os.environ.get("COA_LOCAL_OBJECT_BASE", "http://127.0.0.1:8099/_local/objects").rstrip("/")


def default_bucket() -> str:
    """One logical bucket for every local artifact write.

    ``ONTOLOGY_ARTIFACTS_BUCKET`` is what ``dynamo_store`` resolves at import
    time; reusing it keeps proposal artifacts, ontology downloads and the
    presigned-upload bucket in the same directory instead of silently creating
    a second bucket per call site.
    """
    return (
        os.environ.get("COA_LOCAL_OBJECT_BUCKET", "").strip()
        or os.environ.get("ONTOLOGY_ARTIFACTS_BUCKET", "").strip()
        or "coa-local-artifacts"
    )


def object_path(bucket: str, key: str) -> Path:
    """Resolve one object path, refusing traversal outside the root."""
    root = object_root()
    target = (root / bucket / key).resolve()
    if root not in target.parents and target != root:
        raise ValueError(f"object key escapes the object root: {bucket}/{key}")
    return target


class NoSuchKey(ClientError):
    """404 with the S3 error code upstream code branches on."""

    def __init__(self, message: str, operation: str = "GetObject") -> None:
        super().__init__(
            {
                "Error": {"Code": "NoSuchKey", "Message": message},
                "ResponseMetadata": {"HTTPStatusCode": 404},
            },
            operation,
        )


class _Body:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data

    def __bytes__(self) -> bytes:
        return self._data


def _meta_path(path: Path) -> Path:
    return path.with_name(path.name + ".meta")


def _read_meta(path: Path) -> dict[str, str]:
    meta = _meta_path(path)
    if not meta.is_file():
        return {}
    raw = meta.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except ValueError:  # older plain-text sidecar: holds only the content type
        return {"contentType": raw.strip()}
    return payload if isinstance(payload, dict) else {}


def _write_meta(path: Path, payload: dict[str, str]) -> None:
    _meta_path(path).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class _Paginator:
    """``client.get_paginator("list_objects_v2")`` subset (local, unpaged)."""

    def __init__(self, client: "LocalS3", operation: str) -> None:
        if operation != "list_objects_v2":
            raise ValueError(f"unsupported paginator: {operation}")
        self._client = client

    def paginate(self, **kwargs: Any) -> Iterator[dict[str, Any]]:
        yield self._client.list_objects_v2(**kwargs)


class LocalS3:
    """boto3 S3 client subset used by ``dynamo_store``."""

    class exceptions:  # noqa: N801 - mirrors boto3's attribute
        NoSuchKey = NoSuchKey

    def __init__(self) -> None:
        self._root = object_root()

    # -- writes ------------------------------------------------------------

    def put_object(
        self,
        Bucket: str,
        Key: str,
        Body: Any,
        ContentType: str | None = None,
        ContentDisposition: str | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        path = object_path(Bucket, Key)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = Body.encode("utf-8") if isinstance(Body, str) else bytes(Body)
        path.write_bytes(data)
        meta = {"contentType": ContentType or "application/octet-stream"}
        if ContentDisposition:
            meta["contentDisposition"] = ContentDisposition
        _write_meta(path, meta)
        return {"ETag": f'"{hashlib.md5(data).hexdigest()}"', "ContentLength": len(data)}

    def copy_object(
        self,
        Bucket: str,
        Key: str,
        CopySource: dict[str, Any] | str,
        **_: Any,
    ) -> dict[str, Any]:
        if isinstance(CopySource, str):
            src_bucket, _, src_key = CopySource.partition("/")
        else:
            src_bucket = str(CopySource["Bucket"])
            src_key = str(CopySource["Key"])
        source = object_path(src_bucket, src_key)
        if not source.is_file():
            raise NoSuchKey(f"object not found: {src_bucket}/{src_key}", "CopyObject")
        target = object_path(Bucket, Key)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        meta = _read_meta(source)
        _write_meta(target, meta or {"contentType": "application/octet-stream"})
        return {"CopyObjectResult": {"ETag": f'"{hashlib.md5(target.read_bytes()).hexdigest()}"'}}

    def delete_object(self, Bucket: str, Key: str, **_: Any) -> dict[str, Any]:
        path = object_path(Bucket, Key)
        if path.is_file():
            path.unlink()
        meta = _meta_path(path)
        if meta.is_file():
            meta.unlink()
        return {}

    def delete_objects(self, Bucket: str, Delete: dict[str, Any] | None = None, **_: Any) -> dict[str, Any]:
        deleted = []
        for obj in (Delete or {}).get("Objects") or []:
            key = obj.get("Key")
            if key:
                self.delete_object(Bucket=Bucket, Key=key)
                deleted.append({"Key": key})
        return {"Deleted": deleted}

    # -- reads -------------------------------------------------------------

    def get_object(self, Bucket: str, Key: str, **_: Any) -> dict[str, Any]:
        path = object_path(Bucket, Key)
        if not path.is_file():
            raise NoSuchKey(f"object not found: {Bucket}/{Key}")
        meta = _read_meta(path)
        return {
            "Body": _Body(path.read_bytes()),
            "ContentLength": path.stat().st_size,
            "ContentType": meta.get("contentType", "application/octet-stream"),
            "ContentDisposition": meta.get("contentDisposition"),
        }

    def head_object(self, Bucket: str, Key: str, **_: Any) -> dict[str, Any]:
        path = object_path(Bucket, Key)
        if not path.is_file():
            raise NoSuchKey(f"object not found: {Bucket}/{Key}", "HeadObject")
        meta = _read_meta(path)
        return {
            "ContentLength": path.stat().st_size,
            "ContentType": meta.get("contentType", "application/octet-stream"),
            "ContentDisposition": meta.get("contentDisposition"),
            "ETag": f'"{hashlib.md5(path.read_bytes()).hexdigest()}"',
        }

    def list_objects_v2(self, Bucket: str, Prefix: str = "", **_: Any) -> dict[str, Any]:
        bucket_dir = (object_root() / Bucket).resolve()
        base = (bucket_dir / Prefix).resolve() if Prefix else bucket_dir
        if bucket_dir not in base.parents and base != bucket_dir:
            raise ValueError(f"object prefix escapes the bucket: {Bucket}/{Prefix}")
        keys: list[str] = []
        if base.exists():
            candidates = [base] if base.is_file() else [p for p in base.rglob("*") if p.is_file()]
            for candidate in candidates:
                if candidate.name.endswith(".meta"):
                    continue
                keys.append(candidate.relative_to(bucket_dir).as_posix())
        return {"Contents": [{"Key": key} for key in keys], "KeyCount": len(keys)}

    def get_paginator(self, operation: str) -> _Paginator:
        return _Paginator(self, operation)

    def generate_presigned_url(
        self,
        ClientMethod: str,
        Params: dict[str, Any] | None = None,
        ExpiresIn: int = 3600,
        **_: Any,
    ) -> str:
        params = Params or {}
        bucket = params.get("Bucket") or default_bucket()
        key = params.get("Key") or ""
        return f"{object_base()}/{quote(str(bucket), safe='')}/{quote(str(key), safe='/')}"


def install_local_s3() -> str:
    """Patch ``dynamo_store``'s S3 seam; returns the selected provider."""
    provider = _provider()
    if provider == "s3":
        return provider

    root = object_root()
    bucket = default_bucket()

    from coa_ontology import dynamo_store

    client = LocalS3()
    dynamo_store._get_s3 = lambda: client  # type: ignore[assignment]
    dynamo_store.resolve_ontology_bucket = lambda: bucket  # type: ignore[assignment]
    dynamo_store._S3_BUCKET = bucket
    print(f"[coa-local-s3] root={root} bucket={bucket} base={object_base()}", flush=True)
    return provider
