# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for Athena workgroup lifecycle in namespace create/delete."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from coa_common.constants import RESOURCE_PREFIX

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def env_vars(monkeypatch):
    monkeypatch.setenv("NAMESPACES_TABLE", "test-namespaces")
    monkeypatch.setenv("ROLES_TABLE", "test-roles")
    monkeypatch.setenv("RESOURCE_ROLE_MAPPINGS_TABLE", "test-mappings")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("ALLOWED_ORIGIN", "*")
    monkeypatch.setenv("RESOURCE_PREFIX", f"{RESOURCE_PREFIX}-dev-")
    monkeypatch.setenv("ATHENA_RESULTS_BUCKET_SSM", "/coa/query/athena-results-bucket")
    monkeypatch.setenv("TAG_PREFIX", "scl")
    monkeypatch.setenv("PROJECT_ACCESS_ROLE_ARN_SSM", "/coa/smus/dz-project-access-role-arn")


# ═══════════════════════════════════════════════════════════════════
# Workgroup Creation (namespace service)
# ═══════════════════════════════════════════════════════════════════


def test_warehouse_admin_resolves_a_catalog_interface(monkeypatch):
    """The lazy resolver must use the catalog's interface name, not a nickname."""
    from coa_control_plane.namespace import cleanup, service
    from coa_runtime.registry import default_registry

    seen: list[str] = []

    def _resolve(name: str):
        seen.append(name)
        return MagicMock()

    monkeypatch.setattr("coa_runtime.registry.resolve", _resolve)
    service._warehouse_admin()
    cleanup._warehouse_admin()

    assert seen == ["WarehouseAdminPort", "WarehouseAdminPort"]
    assert set(seen) <= set(default_registry().interfaces)


class TestAthenaWorkgroupCreation:
    def _make_service(self):
        from coa_common.dao import PaginatedResult
        from coa_common.metadata_store.base import ProjectResult
        from coa_control_plane.namespace.service import NamespaceService

        mock_metadata = MagicMock()
        mock_metadata.create_project.return_value = ProjectResult(project_id="proj-abc", name="test-ns")

        ns_dao = MagicMock()
        ns_dao._table_name = "test-namespaces"
        ns_dao.query.return_value = PaginatedResult(items=[])

        roles_dao = MagicMock()
        roles_dao._table_name = "test-roles"
        roles_dao.query.return_value = PaginatedResult(
            items=[
                {"PK": "NAMESPACE_TEMPLATE", "SK": "ROLE#namespace-owner", "name": "Owner", "scope": "NAMESPACE"},
            ]
        )

        mappings_dao = MagicMock()
        mappings_dao._table_name = "test-role-mappings"

        return NamespaceService(
            namespaces_dao=ns_dao,
            roles_dao=roles_dao,
            mappings_dao=mappings_dao,
            metadata_store=mock_metadata,
        )

    def _stub_role_ssm(self, monkeypatch):
        """The DataZone project-access role lookup is out of scope here."""
        from coa_control_plane.namespace import service

        ssm = MagicMock()
        ssm.get_parameter.return_value = {"Parameter": {"Value": "arn:aws:iam::123:role/project-access"}}
        monkeypatch.setattr(service.boto3, "client", lambda *a, **kw: ssm)

    def test_creates_workgroup_with_full_policy(self, monkeypatch):
        from coa_control_plane.namespace import service

        self._stub_role_ssm(monkeypatch)
        provider = MagicMock()
        provider.get.return_value = f"{RESOURCE_PREFIX}-dev-athena-results-123"
        monkeypatch.setattr(service, "_config_provider", lambda: provider)
        admin = MagicMock()
        monkeypatch.setattr(service, "_warehouse_admin", lambda: admin)

        svc = self._make_service()
        from coa_control_plane_server.models.create_namespace_request_content import (
            CreateNamespaceRequestContent,
        )

        req = CreateNamespaceRequestContent(name="sales", owner="alice@co.com")
        svc.create(req)

        # Workgroup name is prefix + namespace UUID; results go to the bucket/namespace prefix.
        admin.create_workgroup.assert_called_once()
        name = admin.create_workgroup.call_args.args[0]
        kwargs = admin.create_workgroup.call_args.kwargs
        namespace_id = name.removeprefix(f"{RESOURCE_PREFIX}-dev-")
        assert name.startswith(f"{RESOURCE_PREFIX}-dev-")
        assert kwargs["output_location"] == f"s3://{RESOURCE_PREFIX}-dev-athena-results-123/{namespace_id}/"
        # The six policy fields dropped by the first pass must reach the provider.
        assert kwargs["encryption"] == "SSE_S3"
        assert kwargs["engine_version"] == "Athena engine version 3"
        assert kwargs["enforce_configuration"] is True
        assert kwargs["publish_metrics"] is True
        assert kwargs["tags"] == {
            "scl:namespace": namespace_id,
            "scl:managed": "true",
        }

    def test_workgroup_stored_in_ddb_record(self, monkeypatch):
        from coa_control_plane.namespace import service

        self._stub_role_ssm(monkeypatch)
        provider = MagicMock()
        provider.get.return_value = f"{RESOURCE_PREFIX}-dev-athena-results-123"
        monkeypatch.setattr(service, "_config_provider", lambda: provider)
        admin = MagicMock()
        monkeypatch.setattr(service, "_warehouse_admin", lambda: admin)

        svc = self._make_service()
        from coa_control_plane_server.models.create_namespace_request_content import (
            CreateNamespaceRequestContent,
        )

        req = CreateNamespaceRequestContent(name="sales", owner="alice@co.com")
        svc.create(req)

        # Check the namespace DDB put includes athenaWorkgroupName
        ns_put_calls = [c for c in svc._ns_dao.put.call_args_list if "athenaWorkgroupName" in c.args[0]]
        assert len(ns_put_calls) == 1
        assert ns_put_calls[0].args[0]["athenaWorkgroupName"].startswith(f"{RESOURCE_PREFIX}-dev-")

    def test_provider_failure_propagates(self, monkeypatch):
        """A failed create must not be disguised as "no workgroup configured"."""
        from coa_control_plane.namespace import service

        self._stub_role_ssm(monkeypatch)
        provider = MagicMock()
        provider.get.return_value = f"{RESOURCE_PREFIX}-dev-athena-results-123"
        monkeypatch.setattr(service, "_config_provider", lambda: provider)
        admin = MagicMock()
        admin.create_workgroup.side_effect = RuntimeError("provider unavailable")
        monkeypatch.setattr(service, "_warehouse_admin", lambda: admin)

        svc = self._make_service()
        from coa_control_plane_server.models.create_namespace_request_content import (
            CreateNamespaceRequestContent,
        )

        req = CreateNamespaceRequestContent(name="sales", owner="alice@co.com")
        with pytest.raises(RuntimeError, match="provider unavailable"):
            svc.create(req)

        ns_puts = [c for c in svc._ns_dao.put.call_args_list if c.args[0].get("athenaWorkgroupName")]
        assert ns_puts == []

    def test_bucket_read_failure_propagates(self, monkeypatch):
        from coa_ports import PortError, PortErrorCode
        from coa_control_plane.namespace import service

        self._stub_role_ssm(monkeypatch)
        provider = MagicMock()
        provider.get.side_effect = PortError(PortErrorCode.UNAVAILABLE, "ssm down", provider="ssm")
        monkeypatch.setattr(service, "_config_provider", lambda: provider)
        admin = MagicMock()
        monkeypatch.setattr(service, "_warehouse_admin", lambda: admin)

        svc = self._make_service()
        from coa_control_plane_server.models.create_namespace_request_content import (
            CreateNamespaceRequestContent,
        )

        req = CreateNamespaceRequestContent(name="sales", owner="alice@co.com")
        with pytest.raises(PortError):
            svc.create(req)
        admin.create_workgroup.assert_not_called()

    def test_missing_bucket_skips_workgroup_creation(self, monkeypatch):
        from coa_control_plane.namespace import service

        self._stub_role_ssm(monkeypatch)
        provider = MagicMock()
        provider.get.return_value = None
        monkeypatch.setattr(service, "_config_provider", lambda: provider)
        admin = MagicMock()
        monkeypatch.setattr(service, "_warehouse_admin", lambda: admin)

        svc = self._make_service()
        from coa_control_plane_server.models.create_namespace_request_content import (
            CreateNamespaceRequestContent,
        )

        req = CreateNamespaceRequestContent(name="sales", owner="alice@co.com")
        svc.create(req)
        # No result bucket configured is "workgroup feature not provisioned", not an error.
        admin.create_workgroup.assert_not_called()
        ns_puts = [c for c in svc._ns_dao.put.call_args_list if c.args[0].get("athenaWorkgroupName")]
        assert ns_puts == []

    def test_unconfigured_config_provider_skips_workgroup_creation(self, monkeypatch):
        from coa_runtime.errors import MissingConfigurationError
        from coa_control_plane.namespace import service

        def _raise():
            raise MissingConfigurationError(
                "ConfigProvider has no provider configured",
                interface="ConfigProvider",
                key="COA_PROVIDER_CONFIG",
            )

        self._stub_role_ssm(monkeypatch)
        monkeypatch.setattr(service, "_config_provider", _raise)
        admin = MagicMock()
        monkeypatch.setattr(service, "_warehouse_admin", lambda: admin)

        svc = self._make_service()
        from coa_control_plane_server.models.create_namespace_request_content import (
            CreateNamespaceRequestContent,
        )

        req = CreateNamespaceRequestContent(name="sales", owner="alice@co.com")
        svc.create(req)
        admin.create_workgroup.assert_not_called()


# ═══════════════════════════════════════════════════════════════════
# Workgroup Deletion (cleanup.py — invoked by the deletion pipeline's
# delete_platform step, see test_namespace_deletion_pipeline.py for the
# step-level test and test_namespace_cleanup.py for the skip/no-op case).
# "Not found" is the provider's contract now, not cleanup's.
# ═══════════════════════════════════════════════════════════════════


class TestAthenaWorkgroupDeletion:
    def test_delete_delegates_to_warehouse_admin(self, monkeypatch):
        from coa_control_plane.namespace import cleanup

        admin = MagicMock()
        monkeypatch.setattr(cleanup, "_warehouse_admin", lambda: admin)

        cleanup.delete_athena_workgroup(f"{RESOURCE_PREFIX}-dev-ns-123")

        admin.delete_workgroup.assert_called_once_with(f"{RESOURCE_PREFIX}-dev-ns-123")

    def test_delete_propagates_provider_failure(self, monkeypatch):
        from coa_control_plane.namespace import cleanup

        admin = MagicMock()
        admin.delete_workgroup.side_effect = RuntimeError("warehouse unreachable")
        monkeypatch.setattr(cleanup, "_warehouse_admin", lambda: admin)

        with pytest.raises(RuntimeError):
            cleanup.delete_athena_workgroup(f"{RESOURCE_PREFIX}-dev-ns-123")
