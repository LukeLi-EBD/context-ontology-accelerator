# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Serve sync-path boto3 clients carry the fail-fast config."""

from __future__ import annotations

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_sources_registry_dynamodb_uses_sync_config():
    from coa_serve.clients import sources_registry

    with patch.object(sources_registry.boto3, "resource") as mock_res:
        sources_registry.SourcesRegistry(table_name="t", region="us-east-1")
        _, kwargs = mock_res.call_args
        assert kwargs["config"].connect_timeout == 2
        assert kwargs["config"].read_timeout == 8


def test_session_metadata_dynamodb_uses_sync_config():
    from coa_serve import session_metadata

    with patch.object(session_metadata.boto3, "resource") as mock_res:
        session_metadata.SessionMetadataStore(table_name="t", region="us-east-1")
        _, kwargs = mock_res.call_args
        assert kwargs["config"].read_timeout == 8


def test_opensearch_proxy_lambda_uses_sync_config(monkeypatch):
    # The direct AOSS client (and its transient-fault retry) now lives in the
    # shared coa_common.opensearch.AossVectorClient. The only
    # boto3 client serve builds here is the optional proxy-invoke Lambda client,
    # which must carry the sync fail-fast config.
    monkeypatch.setenv("OPENSEARCH_PROXY_LAMBDA_ARN", "arn:aws:lambda:us-east-1:123456789012:function:proxy")

    from coa_serve.clients import opensearch as osmod

    with (
        patch.object(osmod.boto3, "client") as mock_client,
        patch.object(osmod, "AossVectorClient"),
    ):
        osmod.OpenSearchVectorClient(endpoint="example.aoss.amazonaws.com", region="us-east-1")
        _, kwargs = mock_client.call_args
        assert kwargs["config"].connect_timeout == 2
        assert kwargs["config"].read_timeout == 8
