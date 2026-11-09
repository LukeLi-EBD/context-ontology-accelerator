"""Contract tests for the local graph and warehouse admin ports."""

from __future__ import annotations

import pytest
from coa_local_providers.graph_admin import OxigraphGraphAdmin
from coa_local_providers.warehouse_admin import PgWarehouseAdmin
from coa_ports import GraphAdminPort, PortError, PortErrorCode, WarehouseAdminPort


class _FakeStore:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.asked: list[str] = []
        self.closed = False

    def ask(self, sparql: str) -> bool:
        self.asked.append(sparql)
        if self.fail:
            raise RuntimeError("down")
        return True

    def close(self) -> None:
        self.closed = True


class _FakeMeta:
    def __init__(self) -> None:
        self.last: tuple[str, tuple[object, ...]] | None = None
        self.closed = False

    def query(self, sql: str, params: tuple[object, ...] = ()) -> list[dict[str, object]]:
        self.last = (sql, params)
        return [{"a": 1, "b": None}]

    def close(self) -> None:
        self.closed = True


def _warehouse() -> tuple[PgWarehouseAdmin, _FakeMeta]:
    admin = PgWarehouseAdmin.__new__(PgWarehouseAdmin)
    meta = _FakeMeta()
    admin._meta = meta
    return admin, meta


def test_both_local_admins_implement_their_ports() -> None:
    assert isinstance(OxigraphGraphAdmin("http://graph:7878", store=_FakeStore()), GraphAdminPort)
    assert isinstance(_warehouse()[0], WarehouseAdminPort)


def test_probe_engine_refuses_another_endpoint() -> None:
    admin = OxigraphGraphAdmin("http://graph:7878", store=_FakeStore())

    with pytest.raises(PortError) as excinfo:
        admin.probe_engine("http://other:7878")

    assert excinfo.value.code is PortErrorCode.INVALID_ARGUMENT
    assert excinfo.value.provider_code == "E_GRAPH_ADMIN_ENDPOINT_MISMATCH"


def test_probe_engine_reports_an_unreachable_endpoint() -> None:
    admin = OxigraphGraphAdmin("http://graph:7878", store=_FakeStore(fail=True))

    with pytest.raises(PortError) as excinfo:
        admin.probe_engine("http://graph:7878")

    assert excinfo.value.code is PortErrorCode.UNAVAILABLE
    assert excinfo.value.provider_code == "E_GRAPH_ADMIN_PROBE"


def test_probe_engine_asks_the_configured_endpoint() -> None:
    store = _FakeStore()
    OxigraphGraphAdmin("http://graph:7878/", store=store).probe_engine("http://graph:7878/")

    assert store.asked == ["ASK {}"]


def test_the_local_cluster_is_the_configured_endpoint() -> None:
    admin = OxigraphGraphAdmin("http://graph:7878/", store=_FakeStore())

    clusters = admin.list_clusters()
    assert [cluster.identifier for cluster in clusters] == ["http://graph:7878"]
    assert clusters[0].engine == "oxigraph"
    assert clusters[0].iam_auth_enabled is False
    assert admin.list_tags("arn:whatever") == {}
    assert admin.list_clusters(cluster_id="http://elsewhere") == ()


def test_warehouse_rejects_anything_that_is_not_read_only() -> None:
    admin, meta = _warehouse()

    with pytest.raises(PortError) as excinfo:
        admin.run_query("DELETE FROM platform.metric_definition")

    assert excinfo.value.code is PortErrorCode.INVALID_ARGUMENT
    assert excinfo.value.provider_code == "E_WAREHOUSE_READ_ONLY"
    assert meta.last is None


def test_warehouse_wraps_the_query_and_caps_rows() -> None:
    admin, meta = _warehouse()

    rows = admin.run_query("SELECT 1 AS a, NULL AS b;", max_rows=7)

    assert rows == (("1", ""),)
    assert meta.last is not None
    assert meta.last[0].startswith("SELECT * FROM (SELECT 1 AS a, NULL AS b) AS coa_admin_query LIMIT %s")
    assert meta.last[1] == (7,)


def test_workgroup_and_catalog_calls_are_documented_no_ops() -> None:
    admin, _ = _warehouse()

    assert admin.create_workgroup("wg", output_location="s3://x") == "wg"
    # The full Athena policy is part of the contract; local must accept it as a no-op.
    assert (
        admin.create_workgroup(
            "wg",
            output_location="s3://x/ns/",
            encryption="SSE_S3",
            engine_version="Athena engine version 3",
            enforce_configuration=True,
            publish_metrics=True,
            tags={"coa:namespace": "ns", "coa:managed": "true"},
        )
        == "wg"
    )
    admin.delete_workgroup("wg")
    admin.register_catalog("cat", parameters={"a": "b"})
    admin.delete_catalog("cat")

    with pytest.raises(PortError):
        admin.create_workgroup("")
    with pytest.raises(PortError):
        admin.register_catalog("")


def test_probes_never_raise() -> None:
    graph = OxigraphGraphAdmin("http://graph:7878", store=_FakeStore(fail=True))
    assert graph.probe()["ok"] is False
    assert _warehouse()[0].probe()["ok"] is True
