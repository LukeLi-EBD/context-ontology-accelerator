"""ObjectStore adapter: size-based routing between PG bytea and FS CAS.

Write order is fixed by 07 section 4.4: bytes -> metadata row -> reference -> commit.
"""

from __future__ import annotations

import hashlib
import logging
import shutil
from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb

from ..config import StorageConfig
from ..errors import PortError
from ..ports import Manifest
from .metadata_pg import MetadataPg
from .object_fs import FsCasBackend
from .object_pg import PgByteaBackend

log = logging.getLogger(__name__)

OWNER_TYPE = "object"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class LayeredObjectStore:
    port = "ObjectStore"

    def __init__(
        self,
        config: StorageConfig,
        metadata: MetadataPg,
        fs_backend: FsCasBackend,
        pg_backend: PgByteaBackend,
    ) -> None:
        self._config = config
        self._meta = metadata
        self._fs = fs_backend
        self._pg = pg_backend
        self._root = Path(config.root)
        self._threshold = config.pg_blob_max_file_mb * 1024 * 1024

    def manifest(self) -> Manifest:
        return Manifest(
            provider=f"layered({self._config.small_object_provider}+{self._config.large_object_provider})",
            port=self.port,
            capabilities=[
                "object.put",
                "object.get",
                "object.head",
                "object.delete",
                "object.list",
            ],
            notes={
                "presign": False,
                "multipart": False,
                "versioning": "content_hash",
                "small_object_provider": self._config.small_object_provider,
                "large_object_provider": self._config.large_object_provider,
                "small_object_max_bytes": self._threshold,
                "range_read": {"fs": True, "pg": False},
            },
        )

    # ---- internals -------------------------------------------------------

    @staticmethod
    def _owner_id(bucket: str, key: str) -> str:
        return f"{bucket}/{key}"

    def _route(self, size: int) -> str:
        if size <= self._threshold and self._config.small_object_provider == "pg":
            return "pg"
        return "fs"

    def _check_disk(self) -> None:
        try:
            usage = shutil.disk_usage(self._root)
        except OSError as exc:
            raise PortError(
                code="Unavailable",
                message=f"cannot read disk usage for {self._root}: {exc}",
                provider="fs",
                provider_code="E_STORAGE_DISK",
            ) from exc
        free_pct = (usage.free / usage.total) * 100 if usage.total else 0
        if free_pct < self._config.min_free_pct:
            raise PortError(
                code="ResourceExhausted",
                message=(
                    f"disk free {free_pct:.1f}% is below storage.min_free_pct="
                    f"{self._config.min_free_pct}%"
                ),
                provider="fs",
                provider_code="E_DISK_LOW",
                details={"available_pct": round(free_pct, 2), "required_pct": self._config.min_free_pct},
            )

    def _row(self, bucket: str, key: str) -> dict[str, Any] | None:
        rows = self._meta.query(
            """
            SELECT b.hash, b.size, b.mime, b.tier, b.path, b.state, b.metadata, b.created_at
              FROM platform.blob_ref r
              JOIN platform.blob b ON b.hash = r.hash
             WHERE r.owner_type = %s AND r.owner_id = %s
            """,
            (OWNER_TYPE, self._owner_id(bucket, key)),
        )
        return rows[0] if rows else None

    @staticmethod
    def _object_meta(row: dict[str, Any], bucket: str, key: str) -> dict[str, Any]:
        return {
            "ref": {
                "bucket": bucket,
                "key": key,
                "etag": row["hash"],
                "size": row["size"],
                "checksum": {"algorithm": "sha256", "value": row["hash"]},
            },
            "contentType": row["mime"],
            "lastModified": row["created_at"].isoformat(),
            "metadata": row.get("metadata") or {},
            "tier": row["tier"],
        }

    # ---- ObjectStore v1 --------------------------------------------------

    def put(
        self,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        self._check_disk()
        data = bytes(body)
        hash_hex = sha256_hex(data)
        tier = self._route(len(data))
        path = None
        if tier == "fs":
            if not self._fs.exists(hash_hex):
                self._fs.write(hash_hex, data)
            path = self._fs.relative_path(hash_hex)
        return self._commit(
            bucket=bucket,
            key=key,
            hash_hex=hash_hex,
            size=len(data),
            content_type=content_type,
            metadata=metadata or {},
            tier=tier,
            path=path,
            pg_data=data if tier == "pg" else None,
        )

    def put_from_path(
        self,
        bucket: str,
        key: str,
        path: str | Path,
        content_type: str,
        metadata: dict[str, str] | None,
        sha256: str,
        size: int,
    ) -> dict[str, Any]:
        """Commit an already-written temp file without loading it into memory.

        The temp file must live under storage.tmp_dir (same volume as the CAS).
        `sha256`/`size` are produced by the streaming writer; this method does
        not re-read the payload for large objects.
        """
        self._check_disk()
        source = Path(path)
        tier = self._route(size)
        blob_path = None
        pg_data = None
        if tier == "fs":
            blob_path = self._fs.commit_from_path(sha256, source)
        else:
            pg_data = source.read_bytes()
            if len(pg_data) != size or sha256_hex(pg_data) != sha256:
                try:
                    source.unlink(missing_ok=True)
                except OSError:
                    pass
                raise PortError(
                    code="DataLoss",
                    message="temp upload changed between hashing and CAS commit",
                    provider="layered",
                    provider_code="E_STORAGE_HASH_MISMATCH",
                )
            try:
                source.unlink(missing_ok=True)
            except OSError:
                pass
        return self._commit(
            bucket=bucket,
            key=key,
            hash_hex=sha256,
            size=size,
            content_type=content_type,
            metadata=metadata or {},
            tier=tier,
            path=blob_path,
            pg_data=pg_data,
        )

    def _commit(
        self,
        *,
        bucket: str,
        key: str,
        hash_hex: str,
        size: int,
        content_type: str,
        metadata: dict[str, str],
        tier: str,
        path: str | None,
        pg_data: bytes | None,
    ) -> dict[str, Any]:
        owner_id = self._owner_id(bucket, key)
        with self._meta.tx() as tx:
            tx.execute(
                """
                INSERT INTO platform.blob (hash, size, mime, tier, path, state, metadata)
                VALUES (%s, %s, %s, %s, %s, 'committed', %s)
                ON CONFLICT (hash) DO NOTHING
                """,
                (hash_hex, size, content_type, tier, path, Jsonb(metadata)),
            )
            row = tx.query(
                "SELECT state, tier FROM platform.blob WHERE hash = %s", (hash_hex,)
            )[0]
            if row["state"] != "committed" or row["tier"] != tier:
                tx.execute(
                    "UPDATE platform.blob SET state = 'committed', tier = %s, path = %s, "
                    "deleted_at = NULL WHERE hash = %s",
                    (tier, path, hash_hex),
                )
            if tier == "pg" and pg_data is not None:
                self._pg.write(tx, hash_hex, pg_data)

            old_refs = tx.query(
                "SELECT hash FROM platform.blob_ref WHERE owner_type = %s AND owner_id = %s",
                (OWNER_TYPE, owner_id),
            )
            for old in old_refs:
                if old["hash"] == hash_hex:
                    continue
                tx.execute(
                    "DELETE FROM platform.blob_ref WHERE hash = %s AND owner_type = %s AND owner_id = %s",
                    (old["hash"], OWNER_TYPE, owner_id),
                )
                tx.execute(
                    """
                    UPDATE platform.blob
                       SET refcount = GREATEST(refcount - 1, 0),
                           state = CASE WHEN refcount - 1 <= 0 THEN 'deleting' ELSE state END,
                           deleted_at = CASE WHEN refcount - 1 <= 0 THEN now() ELSE deleted_at END
                     WHERE hash = %s
                    """,
                    (old["hash"],),
                )

            inserted = tx.execute_returning(
                """
                INSERT INTO platform.blob_ref (hash, owner_type, owner_id)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING hash
                """,
                (hash_hex, OWNER_TYPE, owner_id),
            )
            if inserted:
                tx.execute(
                    "UPDATE platform.blob SET refcount = refcount + 1 WHERE hash = %s",
                    (hash_hex,),
                )

        log.info(
            "object put",
            extra={
                "event": {
                    "event": "object_put",
                    "bucket": bucket,
                    "key": key,
                    "hash": hash_hex,
                    "size": size,
                    "tier": tier,
                }
            },
        )
        return {
            "ref": {
                "bucket": bucket,
                "key": key,
                "etag": hash_hex,
                "size": size,
                "checksum": {"algorithm": "sha256", "value": hash_hex},
            },
            "tier": tier,
        }

    def get(self, bucket: str, key: str) -> tuple[bytes, dict[str, Any]]:
        row = self._row(bucket, key)
        if row is None:
            raise PortError(
                code="NotFound",
                message=f"object not found: {bucket}/{key}",
                provider="layered",
                provider_code="E_OBJECT_NOT_FOUND",
            )
        if row["state"] == "missing":
            raise PortError(
                code="DataLoss",
                message=f"object state=missing: {bucket}/{key}",
                provider="layered",
                provider_code="E_STORAGE_BLOB_MISSING",
            )
        if row["tier"] == "fs":
            data = self._fs.read(row["hash"])
        else:
            data = self._pg.read(row["hash"])
            if data is None:
                self._mark_missing(row["hash"])
                raise PortError(
                    code="DataLoss",
                    message=f"blob row exists but bytea payload is missing: {row['hash']}",
                    provider="pg",
                    provider_code="E_STORAGE_BLOB_MISSING",
                )
        actual = sha256_hex(data)
        if actual != row["hash"]:
            self._mark_missing(row["hash"])
            raise PortError(
                code="DataLoss",
                message=f"sha256 mismatch for {bucket}/{key}: expected {row['hash']}, got {actual}",
                provider="layered",
                provider_code="E_STORAGE_HASH_MISMATCH",
                details={"expected": row["hash"], "actual": actual},
            )
        return data, self._object_meta(row, bucket, key)

    def head(self, bucket: str, key: str) -> dict[str, Any]:
        row = self._row(bucket, key)
        if row is None:
            raise PortError(
                code="NotFound",
                message=f"object not found: {bucket}/{key}",
                provider="layered",
                provider_code="E_OBJECT_NOT_FOUND",
            )
        return self._object_meta(row, bucket, key)

    def delete(self, bucket: str, key: str) -> None:
        owner_id = self._owner_id(bucket, key)
        with self._meta.tx() as tx:
            rows = tx.query(
                "SELECT hash FROM platform.blob_ref WHERE owner_type = %s AND owner_id = %s",
                (OWNER_TYPE, owner_id),
            )
            for row in rows:
                tx.execute(
                    "DELETE FROM platform.blob_ref WHERE hash = %s AND owner_type = %s AND owner_id = %s",
                    (row["hash"], OWNER_TYPE, owner_id),
                )
                tx.execute(
                    """
                    UPDATE platform.blob
                       SET refcount = GREATEST(refcount - 1, 0),
                           state = CASE WHEN refcount - 1 <= 0 THEN 'deleting' ELSE state END,
                           deleted_at = CASE WHEN refcount - 1 <= 0 THEN now() ELSE deleted_at END
                     WHERE hash = %s
                    """,
                    (row["hash"],),
                )

    def list(self, bucket: str, prefix: str = "", limit: int = 100) -> list[dict[str, Any]]:
        owner_prefix = self._owner_id(bucket, prefix)
        rows = self._meta.query(
            """
            SELECT b.hash, b.size, b.mime, b.tier, b.path, b.state, b.metadata, b.created_at,
                   r.owner_id
              FROM platform.blob_ref r
              JOIN platform.blob b ON b.hash = r.hash
             WHERE r.owner_type = %s AND r.owner_id LIKE %s
             ORDER BY r.owner_id
             LIMIT %s
            """,
            (OWNER_TYPE, f"{owner_prefix}%", limit),
        )
        result: list[dict[str, Any]] = []
        for row in rows:
            key = row["owner_id"][len(bucket) + 1 :]
            result.append(self._object_meta(row, bucket, key))
        return result

    def _mark_missing(self, hash_hex: str) -> None:
        self._meta.execute(
            "UPDATE platform.blob SET state = 'missing', verified_ok = false WHERE hash = %s",
            (hash_hex,),
        )

    # ---- explicit placeholders ------------------------------------------

    def copy(self, *_args: Any, **_kwargs: Any) -> Any:
        raise PortError(
            code="Unsupported",
            message="ObjectStore.copy is not implemented in S0",
            provider="layered",
            provider_code="E_PORT_NOT_IMPLEMENTED",
            details={"slice": "S2"},
        )

    def presign_get(self, *_args: Any, **_kwargs: Any) -> Any:
        raise PortError(
            code="Unsupported",
            message="presign is not supported (presign=false)",
            provider="layered",
            provider_code="E_PORT_NOT_IMPLEMENTED",
        )
