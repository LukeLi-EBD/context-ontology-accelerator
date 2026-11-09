"""``coa_ports.ObjectStorePort`` over S3.

Kept byte-for-byte equivalent to the boto3 calls the services used before:
``put_object`` / ``get_object`` / ``head_object`` / ``delete_object`` /
``list_objects_v2`` with the same arguments. The only conversion is the return
shape (dict -> ``ObjectInfo``).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from coa_ports import ObjectInfo

from .errors import to_port_error


def _info(
    bucket: str,
    key: str,
    *,
    size: int | None,
    etag: str,
    content_type: str,
    metadata: Mapping[str, str] | None,
) -> ObjectInfo:
    return ObjectInfo(
        bucket=bucket,
        key=key,
        size=int(size or 0),
        content_type=content_type,
        metadata=dict(metadata or {}),
        etag=etag.strip('"'),
    )


class S3ObjectStore:
    """S3 implementation of the object-store port (sync, as S3 is)."""

    def __init__(
        self,
        client: Any = None,
        *,
        region: str | None = None,
        probe_bucket: str = "",
        client_config: Any = None,
    ) -> None:
        self._client_obj = client
        self._region = region
        self._probe_bucket = probe_bucket
        self._client_config = client_config

    # ── port ───────────────────────────────────────────────────────────────

    def put(
        self,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str = "application/octet-stream",
        metadata: Mapping[str, str] | None = None,
    ) -> ObjectInfo:
        kwargs: dict[str, Any] = {
            "Bucket": bucket,
            "Key": key,
            "Body": body,
            "ContentType": content_type,
        }
        if metadata:
            kwargs["Metadata"] = {str(k): str(v) for k, v in metadata.items()}
        try:
            response = self._client().put_object(**kwargs)
        except Exception as exc:  # noqa: BLE001
            raise to_port_error(exc, provider="s3", message=f"put {bucket}/{key}") from exc
        return _info(
            bucket,
            key,
            size=len(body),
            etag=str(response.get("ETag", "")),
            content_type=content_type,
            metadata=metadata,
        )

    def get(self, bucket: str, key: str) -> tuple[bytes, ObjectInfo]:
        try:
            response = self._client().get_object(Bucket=bucket, Key=key)
            body = response["Body"].read()
        except Exception as exc:  # noqa: BLE001
            raise to_port_error(exc, provider="s3", message=f"get {bucket}/{key}") from exc
        return body, _info(
            bucket,
            key,
            size=response.get("ContentLength", len(body)),
            etag=str(response.get("ETag", "")),
            content_type=str(response.get("ContentType", "application/octet-stream")),
            metadata=response.get("Metadata"),
        )

    def head(self, bucket: str, key: str) -> ObjectInfo:
        try:
            response = self._client().head_object(Bucket=bucket, Key=key)
        except Exception as exc:  # noqa: BLE001
            raise to_port_error(exc, provider="s3", message=f"head {bucket}/{key}") from exc
        return _info(
            bucket,
            key,
            size=response.get("ContentLength"),
            etag=str(response.get("ETag", "")),
            content_type=str(response.get("ContentType", "application/octet-stream")),
            metadata=response.get("Metadata"),
        )

    def delete(self, bucket: str, key: str) -> None:
        try:
            self._client().delete_object(Bucket=bucket, Key=key)
        except Exception as exc:  # noqa: BLE001
            raise to_port_error(exc, provider="s3", message=f"delete {bucket}/{key}") from exc

    def list(self, bucket: str, prefix: str = "", limit: int = 100) -> tuple[ObjectInfo, ...]:
        try:
            response = self._client().list_objects_v2(
                Bucket=bucket, Prefix=prefix, MaxKeys=limit
            )
        except Exception as exc:  # noqa: BLE001
            raise to_port_error(exc, provider="s3", message=f"list {bucket}/{prefix}") from exc
        return tuple(
            _info(
                bucket,
                str(item.get("Key", "")),
                size=item.get("Size"),
                etag=str(item.get("ETag", "")),
                # list_objects_v2 does not return content type or user metadata
                content_type="",
                metadata=None,
            )
            for item in response.get("Contents", ())
        )

    def probe(self) -> Mapping[str, Any]:
        """Reachability snapshot; never raises.

        Without a configured probe bucket S3 cannot be checked anonymously, so
        the honest answer is ``unknown`` rather than a fake ``ok``.
        """
        bucket = getattr(self, "_probe_bucket", "")
        if not bucket:
            return {
                "status": "unknown",
                "provider": "s3",
                "detail": "no probe bucket configured",
            }
        try:
            self._client().head_bucket(Bucket=bucket)
        except Exception as exc:  # noqa: BLE001 - probe must never raise
            return {
                "status": "unavailable",
                "provider": "s3",
                "provider_code": str(
                    getattr(exc, "response", {}).get("Error", {}).get("Code", type(exc).__name__)
                ),
            }
        return {"status": "ok", "provider": "s3"}

    # ── internals ──────────────────────────────────────────────────────────

    def _client(self) -> Any:
        if self._client_obj is None:
            import boto3

            self._client_obj = boto3.client(
                "s3", region_name=self._region, config=self._client_config
            )
        return self._client_obj


__all__ = ["S3ObjectStore"]
