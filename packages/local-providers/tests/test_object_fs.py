"""Real-call tests for the filesystem ``ObjectStorePort`` provider.

No mocks: every call reads and writes a real temporary directory.
"""

from __future__ import annotations

import hashlib

import pytest

from coa_local_providers.object_fs import FsObjectStore
from coa_ports import ObjectInfo, ObjectStorePort, PortError, PortErrorCode


def test_provider_is_an_object_store_port(tmp_path) -> None:
    assert isinstance(FsObjectStore(tmp_path), ObjectStorePort)


def test_put_get_head_list_delete_roundtrip(tmp_path) -> None:
    store = FsObjectStore(tmp_path)
    body = b"coa fs object body"
    digest = hashlib.sha256(body).hexdigest()

    info = store.put("bucket-a", "docs/readme.txt", body, content_type="text/plain", metadata={"origin": "coa"})
    assert isinstance(info, ObjectInfo)
    assert (info.bucket, info.key, info.size) == ("bucket-a", "docs/readme.txt", len(body))
    assert info.content_type == "text/plain"
    assert info.etag == digest

    data, fetched = store.get("bucket-a", "docs/readme.txt")
    assert data == body
    assert fetched.etag == digest
    assert fetched.metadata == {"origin": "coa"}

    head = store.head("bucket-a", "docs/readme.txt")
    assert head.size == len(body)

    listed = store.list("bucket-a", "docs/", 10)
    assert isinstance(listed, tuple)
    assert [item.key for item in listed] == ["docs/readme.txt"]

    store.delete("bucket-a", "docs/readme.txt")
    with pytest.raises(PortError) as excinfo:
        store.get("bucket-a", "docs/readme.txt")
    assert excinfo.value.code is PortErrorCode.NOT_FOUND
    assert excinfo.value.provider_code == "E_OBJECT_NOT_FOUND"


def test_delete_of_an_absent_key_is_a_no_op(tmp_path) -> None:
    FsObjectStore(tmp_path).delete("bucket-a", "absent.txt")


def test_list_respects_prefix_and_limit(tmp_path) -> None:
    store = FsObjectStore(tmp_path)
    for key in ("a/1.txt", "a/2.txt", "b/3.txt"):
        store.put("bucket-a", key, key.encode())
    assert [i.key for i in store.list("bucket-a", "a/", 10)] == ["a/1.txt", "a/2.txt"]
    assert [i.key for i in store.list("bucket-a", "a/", 1)] == ["a/1.txt"]
    assert store.list("bucket-a", "a/", 0) == ()


@pytest.mark.parametrize("key", ["../escape.txt", "/abs.txt", "a/../../b.txt", ""])
def test_path_traversal_is_rejected(tmp_path, key: str) -> None:
    with pytest.raises(PortError) as excinfo:
        FsObjectStore(tmp_path).put("bucket-a", key, b"x")
    assert excinfo.value.code is PortErrorCode.INVALID_ARGUMENT


def test_probe_never_raises(tmp_path) -> None:
    snapshot = FsObjectStore(tmp_path).probe()
    assert snapshot["status"] == "ok"
    assert snapshot["provider"] == "fs"
