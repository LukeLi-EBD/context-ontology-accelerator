"""Real-call tests for the ``ObjectStorePort`` ACL shell.

No mocks: the shell wraps the real ``LayeredObjectStore``, which routes through
the real PostgreSQL metadata tables and a real filesystem CAS under ``tmp_path``.
Requires ``COA_TEST_PG_DSN`` pointing at a database where the platform schema is
migrated (``platform.blob`` exists); otherwise the tests skip.
"""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import pytest

from coa_local_providers.shells import ObjectStoreShell
from coa_ports import ObjectInfo, ObjectStorePort, PortError, PortErrorCode
from platform_core.adapters.metadata_pg import MetadataPg
from platform_core.adapters.object_fs import FsCasBackend
from platform_core.adapters.object_layered import LayeredObjectStore
from platform_core.adapters.object_pg import PgByteaBackend
from platform_core.config import StorageConfig

BUCKET = "__coa_shell_test__"


class _Minimal:
    """Shape stand-in for the isinstance/constructor checks only."""

    def put(self, bucket, key, body, content_type="", metadata=None):  # noqa: ANN001
        return {}

    def get(self, bucket, key):  # noqa: ANN001
        return b"", {}

    def head(self, bucket, key):  # noqa: ANN001
        return {}

    def delete(self, bucket, key):  # noqa: ANN001
        return None

    def list(self, bucket, prefix="", limit=100):  # noqa: ANN001
        return []


def test_shell_is_an_object_store_port() -> None:
    assert isinstance(ObjectStoreShell(_Minimal()), ObjectStorePort)


def test_constructor_rejects_an_object_missing_a_method() -> None:
    class NoList:
        def put(self, *a): ...
        def get(self, *a): ...
        def head(self, *a): ...
        def delete(self, *a): ...

    with pytest.raises(TypeError):
        ObjectStoreShell(NoList())


@pytest.fixture()
def live_shell(pg_dsn: str, tmp_path: Path):
    """Real LayeredObjectStore over live PG + a temp filesystem CAS."""
    store = MetadataPg(pg_dsn, pool_max=2)
    store.open(retry_seconds=5.0)
    try:
        registered = store.query("SELECT to_regclass('platform.blob') AS reg")[0]["reg"]
        if not registered:
            pytest.skip("platform schema 未迁移，无法跑真实对象存储")
        root = tmp_path / "storage"
        fs = FsCasBackend(root, tmp_path / "tmp")
        fs.ensure_dirs()
        layered = LayeredObjectStore(
            StorageConfig(
                root=str(root),
                tmp_dir=str(tmp_path / "tmp"),
                pg_blob_max_file_mb=1,
                min_free_pct=0,
            ),
            store,
            fs,
            PgByteaBackend(store),
        )
        yield ObjectStoreShell(layered), store
    finally:
        store.close()


def _purge(store: MetadataPg, key: str, digest: str) -> None:
    store.execute(
        "DELETE FROM platform.blob_ref WHERE owner_type = 'object' AND owner_id = %s",
        (f"{BUCKET}/{key}",),
    )
    store.execute("DELETE FROM platform.blob WHERE hash = %s", (digest,))


def test_put_get_head_list_delete_roundtrip(live_shell) -> None:
    shell, store = live_shell
    key = f"obj-{uuid.uuid4().hex}"
    body = b"coa shell object body"
    digest = hashlib.sha256(body).hexdigest()
    try:
        info = shell.put(
            BUCKET, key, body, content_type="text/plain", metadata={"origin": "coa-test"}
        )
        assert isinstance(info, ObjectInfo)
        assert (info.bucket, info.key, info.size) == (BUCKET, key, len(body))
        assert info.content_type == "text/plain"
        assert info.etag == digest
        assert info.metadata == {"origin": "coa-test"}

        data, fetched = shell.get(BUCKET, key)
        assert data == body
        assert isinstance(fetched, ObjectInfo)
        assert fetched.etag == digest

        head = shell.head(BUCKET, key)
        assert head.size == len(body)
        assert head.metadata == {"origin": "coa-test"}

        listed = shell.list(BUCKET, "obj-", 10)
        assert isinstance(listed, tuple)
        assert all(isinstance(item, ObjectInfo) for item in listed)
        assert any(item.key == key for item in listed)

        shell.delete(BUCKET, key)
        with pytest.raises(PortError) as excinfo:
            shell.get(BUCKET, key)
        assert excinfo.value.code is PortErrorCode.NOT_FOUND
        assert excinfo.value.provider_code == "E_OBJECT_NOT_FOUND"
        assert excinfo.value.provider == "layered"
    finally:
        _purge(store, key, digest)


def test_missing_object_maps_to_not_found(live_shell) -> None:
    shell, _ = live_shell
    with pytest.raises(PortError) as excinfo:
        shell.head(BUCKET, f"absent-{uuid.uuid4().hex}")
    assert excinfo.value.code is PortErrorCode.NOT_FOUND


def test_delete_of_an_absent_key_is_a_no_op(live_shell) -> None:
    shell, _ = live_shell
    shell.delete(BUCKET, f"absent-{uuid.uuid4().hex}")


def test_probe_reaches_the_metadata_backend(live_shell) -> None:
    shell, _ = live_shell
    snapshot = shell.probe()
    assert snapshot["status"] == "ok"
    assert snapshot["provider"] == "layered"
