"""Unit tests for the AWS adapters behind the COA ports.

These use botocore's ``Stubber``: the request shape is validated against the
real S3/Secrets Manager/SSM service models, but no network call is made. They
prove construction, request parity and error mapping — not end-to-end
behaviour against AWS.
"""

from __future__ import annotations

import base64

import boto3
import pytest
from botocore.stub import Stubber
from coa_ports import (
    ConfigProvider,
    ObjectInfo,
    ObjectStorePort,
    PortError,
    PortErrorCode,
    SecretProvider,
)

from coa_local_providers.aws import S3ObjectStore, SecretsManagerSecret, SsmConfig


def _client(service: str):
    return boto3.client(
        service,
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


# ── ObjectStorePort / S3 ────────────────────────────────────────────────────


def test_s3_shell_is_an_object_store_port() -> None:
    assert isinstance(S3ObjectStore(_client("s3")), ObjectStorePort)


def test_s3_put_get_head_list_delete_roundtrip() -> None:
    client = _client("s3")
    store = S3ObjectStore(client)
    with Stubber(client) as stub:
        stub.add_response(
            "put_object",
            {"ETag": '"abc123"'},
            {
                "Bucket": "b",
                "Key": "k",
                "Body": b"hello",
                "ContentType": "text/plain",
                "Metadata": {"origin": "test"},
            },
        )
        stub.add_response(
            "get_object",
            {
                "Body": _Body(b"hello"),
                "ContentLength": 5,
                "ETag": '"abc123"',
                "ContentType": "text/plain",
                "Metadata": {"origin": "test"},
            },
            {"Bucket": "b", "Key": "k"},
        )
        stub.add_response(
            "head_object",
            {"ContentLength": 5, "ETag": '"abc123"', "Metadata": {"origin": "test"}},
            {"Bucket": "b", "Key": "k"},
        )
        stub.add_response(
            "list_objects_v2",
            {"Contents": [{"Key": "k", "Size": 5, "ETag": '"abc123"'}]},
            {"Bucket": "b", "Prefix": "", "MaxKeys": 100},
        )
        stub.add_response("delete_object", {}, {"Bucket": "b", "Key": "k"})

        info = store.put("b", "k", b"hello", "text/plain", {"origin": "test"})
        assert isinstance(info, ObjectInfo)
        assert (info.bucket, info.key, info.size) == ("b", "k", 5)
        assert info.etag == "abc123"
        assert info.metadata == {"origin": "test"}

        body, fetched = store.get("b", "k")
        assert body == b"hello"
        assert fetched.content_type == "text/plain"

        assert store.head("b", "k").size == 5
        listed = store.list("b")
        assert tuple(item.key for item in listed) == ("k",)
        store.delete("b", "k")
        stub.assert_no_pending_responses()


def test_s3_missing_key_maps_to_not_found() -> None:
    client = _client("s3")
    store = S3ObjectStore(client)
    with Stubber(client) as stub:
        stub.add_client_error("get_object", service_error_code="NoSuchKey", http_status_code=404)
        with pytest.raises(PortError) as excinfo:
            store.get("b", "missing")
    assert excinfo.value.code is PortErrorCode.NOT_FOUND
    assert excinfo.value.provider_code == "NoSuchKey"


def test_s3_access_denied_is_internal_not_unavailable() -> None:
    client = _client("s3")
    store = S3ObjectStore(client)
    with Stubber(client) as stub:
        stub.add_client_error("head_object", service_error_code="AccessDenied", http_status_code=403)
        with pytest.raises(PortError) as excinfo:
            store.head("b", "k")
    assert excinfo.value.code is PortErrorCode.INTERNAL
    assert excinfo.value.provider_code == "AccessDenied"


def test_s3_probe_without_a_bucket_is_honestly_unknown() -> None:
    snapshot = S3ObjectStore(_client("s3")).probe()
    assert snapshot["status"] == "unknown"


def test_s3_probe_checks_the_configured_bucket() -> None:
    client = _client("s3")
    store = S3ObjectStore(client, probe_bucket="b")
    with Stubber(client) as stub:
        stub.add_response("head_bucket", {}, {"Bucket": "b"})
        assert store.probe()["status"] == "ok"


# ── SecretProvider / Secrets Manager ────────────────────────────────────────


def test_secret_shell_is_a_secret_provider() -> None:
    assert isinstance(SecretsManagerSecret(_client("secretsmanager")), SecretProvider)


def test_secret_returns_the_string_payload() -> None:
    client = _client("secretsmanager")
    provider = SecretsManagerSecret(client)
    with Stubber(client) as stub:
        stub.add_response(
            "get_secret_value",
            {"SecretString": '{"username":"u"}'},
            {"SecretId": "coa/db"},
        )
        assert provider.get("coa/db") == '{"username":"u"}'


def test_secret_supports_binary_payloads() -> None:
    client = _client("secretsmanager")
    provider = SecretsManagerSecret(client)
    with Stubber(client) as stub:
        stub.add_response(
            "get_secret_value",
            {"SecretBinary": base64.b64encode(b"s3cr3t")},
            {"SecretId": "coa/bin"},
        )
        assert provider.get("coa/bin") == "s3cr3t"


def test_missing_secret_maps_to_not_found_without_echoing_the_value() -> None:
    client = _client("secretsmanager")
    provider = SecretsManagerSecret(client)
    with Stubber(client) as stub:
        stub.add_client_error(
            "get_secret_value",
            service_error_code="ResourceNotFoundException",
            http_status_code=400,
        )
        with pytest.raises(PortError) as excinfo:
            provider.get("coa/missing")
    assert excinfo.value.code is PortErrorCode.NOT_FOUND
    assert "s3cr3t" not in str(excinfo.value)


# ── ConfigProvider / SSM ────────────────────────────────────────────────────


def test_ssm_shell_is_a_config_provider() -> None:
    assert isinstance(SsmConfig(_client("ssm")), ConfigProvider)


def test_ssm_get_and_require() -> None:
    client = _client("ssm")
    provider = SsmConfig(client)
    with Stubber(client) as stub:
        for _ in range(2):
            stub.add_response(
                "get_parameter",
                {"Parameter": {"Name": "/coa/domain", "Value": "d-123"}},
                {"Name": "/coa/domain"},
            )
        assert provider.get("/coa/domain") == "d-123"
        assert provider.require("/coa/domain") == "d-123"
    assert provider.as_mapping() == {"/coa/domain": "d-123"}


def test_ssm_missing_parameter_is_none_or_not_found() -> None:
    client = _client("ssm")
    provider = SsmConfig(client)
    with Stubber(client) as stub:
        stub.add_client_error(
            "get_parameter", service_error_code="ParameterNotFound", http_status_code=400
        )
        assert provider.get("/coa/missing") is None
    with Stubber(client) as stub:
        stub.add_client_error(
            "get_parameter", service_error_code="ParameterNotFound", http_status_code=400
        )
        with pytest.raises(PortError) as excinfo:
            provider.require("/coa/missing")
    assert excinfo.value.code is PortErrorCode.NOT_FOUND
    assert excinfo.value.details == {"name": "/coa/missing"}


def test_ssm_other_errors_are_not_swallowed() -> None:
    client = _client("ssm")
    provider = SsmConfig(client)
    with Stubber(client) as stub:
        stub.add_client_error("get_parameter", service_error_code="AccessDeniedException")
        with pytest.raises(PortError) as excinfo:
            provider.get("/coa/x")
    assert excinfo.value.code is PortErrorCode.INTERNAL


class _Body:
    """Minimal ``StreamingBody`` substitute for a stubbed get_object."""

    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data
