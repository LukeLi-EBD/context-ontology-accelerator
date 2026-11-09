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

    def test_creates_workgroup_with_correct_name(self, monkeypatch):
        from coa_control_plane.namespace import service

        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {"Parameter": {"Value": f"{RESOURCE_PREFIX}-dev-athena-results-123"}}
        monkeypatch.setattr(service.boto3, "client", lambda *a, **kw: mock_ssm)
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
        output_location = admin.create_workgroup.call_args.kwargs["output_location"]
        assert name.startswith(f"{RESOURCE_PREFIX}-dev-")
        assert output_location.startswith(f"s3://{RESOURCE_PREFIX}-dev-athena-results-123/")
        assert output_location.endswith(f"/{name.removeprefix(f'{RESOURCE_PREFIX}-dev-')}/")

    def test_workgroup_stored_in_ddb_record(self, monkeypatch):
        from coa_control_plane.namespace import service

        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {"Parameter": {"Value": f"{RESOURCE_PREFIX}-dev-athena-results-123"}}
        monkeypatch.setattr(service.boto3, "client", lambda *a, **kw: mock_ssm)
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

    def test_provider_failure_does_not_persist_workgroup_name(self, monkeypatch):
        """Unconfirmed workgroups must not be recorded in the namespace item."""
        from coa_control_plane.namespace import service

        mock_ssm = MagicMock()
        mock_ssm.get_parameter.return_value = {"Parameter": {"Value": f"{RESOURCE_PREFIX}-dev-athena-results-123"}}
        monkeypatch.setattr(service.boto3, "client", lambda *a, **kw: mock_ssm)
        admin = MagicMock()
        admin.create_workgroup.side_effect = RuntimeError("provider unavailable")
        monkeypatch.setattr(service, "_warehouse_admin", lambda: admin)

        svc = self._make_service()
        from coa_control_plane_server.models.create_namespace_request_content import (
            CreateNamespaceRequestContent,
        )

        req = CreateNamespaceRequestContent(name="sales", owner="alice@co.com")
        # Should not raise
        svc.create(req)

        ns_puts = [c for c in svc._ns_dao.put.call_args_list if c.args[0].get("athenaWorkgroupName")]
        assert ns_puts == []

    def test_missing_ssm_param_skips_workgroup_creation(self, monkeypatch):
        from botocore.exceptions import ClientError
        from coa_control_plane.namespace import service

        mock_ssm = MagicMock()

        # Mock SSM to return role ARN but fail on Athena bucket lookup
        def get_parameter_side_effect(Name):
            if "dz-project-access-role-arn" in Name:
                return {"Parameter": {"Value": "arn:aws:iam::123:role/project-access"}}
            # Athena results bucket SSM param is missing
            raise ClientError({"Error": {"Code": "ParameterNotFound", "Message": "not found"}}, "GetParameter")

        mock_ssm.get_parameter.side_effect = get_parameter_side_effect
        monkeypatch.setattr(service.boto3, "client", lambda *a, **kw: mock_ssm)
        admin = MagicMock()
        monkeypatch.setattr(service, "_warehouse_admin", lambda: admin)

        svc = self._make_service()
        from coa_control_plane_server.models.create_namespace_request_content import (
            CreateNamespaceRequestContent,
        )

        req = CreateNamespaceRequestContent(name="sales", owner="alice@co.com")
        svc.create(req)
        # Warehouse admin should NOT be called (SSM param missing)
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
