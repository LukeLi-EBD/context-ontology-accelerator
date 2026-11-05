"""Object bytes backend: filesystem CAS (07 section 2 and 4)."""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

from ..errors import PortError

log = logging.getLogger(__name__)


class FsCasBackend:
    provider = "fs"

    def __init__(self, root: str | Path, tmp_dir: str | Path) -> None:
        self._root = Path(root)
        self.blobs_dir = self._root / "blobs"
        self.tmp_dir = Path(tmp_dir)

    def ensure_dirs(self) -> None:
        self.blobs_dir.mkdir(parents=True, exist_ok=True)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, hash_hex: str) -> Path:
        return self.blobs_dir / hash_hex[:2] / hash_hex

    def relative_path(self, hash_hex: str) -> str:
        return f"blobs/{hash_hex[:2]}/{hash_hex}"

    def exists(self, hash_hex: str) -> bool:
        return self.path_for(hash_hex).is_file()

    def write(self, hash_hex: str, data: bytes) -> str:
        """Byte-first write: tmp -> fsync -> rename -> fsync(dir)."""
        self.ensure_dirs()
        tmp_path = self.tmp_dir / f"{uuid.uuid4().hex}.part"
        try:
            with open(tmp_path, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise PortError(
                code="PermissionDenied",
                message=f"cannot write temp object: {exc}",
                provider="fs",
                provider_code="E_STORAGE_WRITE",
            ) from exc

        return self._commit_temp(hash_hex, tmp_path, remove_source=True)

    def commit_from_path(self, hash_hex: str, source: Path) -> str:
        """Move an already-written temp file into the CAS (same volume).

        The caller is responsible for fsync-ing the source file. If the content
        already exists, the temp file is removed and the existing blob is reused.
        """
        if self.exists(hash_hex):
            try:
                source.unlink(missing_ok=True)
            except OSError:
                log.warning(
                    "could not remove duplicate temp object",
                    extra={"event": {"event": "cas_dedup_unlink_failed", "path": str(source)}},
                )
            return self.relative_path(hash_hex)
        return self._commit_temp(hash_hex, source, remove_source=True)

    def _commit_temp(self, hash_hex: str, tmp_path: Path, remove_source: bool) -> str:
        destination = self.path_for(hash_hex)
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(tmp_path, destination)
        except OSError as exc:
            if remove_source:
                try:
                    tmp_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise PortError(
                code="PermissionDenied",
                message=f"cannot commit object to CAS: {exc}",
                provider="fs",
                provider_code="E_STORAGE_RENAME",
            ) from exc

        self._fsync_dir(destination.parent)
        return self.relative_path(hash_hex)

    def read(self, hash_hex: str) -> bytes:
        path = self.path_for(hash_hex)
        try:
            return path.read_bytes()
        except FileNotFoundError as exc:
            raise PortError(
                code="DataLoss",
                message=f"blob row exists but file is missing: {path}",
                provider="fs",
                provider_code="E_STORAGE_BLOB_MISSING",
            ) from exc
        except OSError as exc:
            raise PortError(
                code="Unavailable",
                message=f"cannot read blob: {exc}",
                provider="fs",
                provider_code="E_STORAGE_READ",
                retryable=True,
            ) from exc

    def read_range(self, hash_hex: str, start: int, length: int) -> bytes:
        """True byte range: seek into the blob instead of materializing it."""
        path = self.path_for(hash_hex)
        try:
            with open(path, "rb") as handle:
                handle.seek(start)
                return handle.read(length)
        except FileNotFoundError as exc:
            raise PortError(
                code="DataLoss",
                message=f"blob row exists but file is missing: {path}",
                provider="fs",
                provider_code="E_STORAGE_BLOB_MISSING",
            ) from exc
        except OSError as exc:
            raise PortError(
                code="Unavailable",
                message=f"cannot read blob range: {exc}",
                provider="fs",
                provider_code="E_STORAGE_READ",
                retryable=True,
            ) from exc

    def _fsync_dir(self, directory: Path) -> None:
        """fsync a directory where the OS supports it; Windows does not."""
        try:
            fd = os.open(directory, os.O_RDONLY)
        except OSError:
            log.debug(
                "directory fsync unsupported",
                extra={"event": {"event": "fsync_dir", "supported": False, "dir": str(directory)}},
            )
            return
        try:
            os.fsync(fd)
        except OSError:
            pass
        finally:
            os.close(fd)
