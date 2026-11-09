"""Shape guard for the Control Plane item-store port.

No implementation exists yet (phase 7). These tests pin the contract that a
later DynamoDB or Postgres implementation must satisfy, so the port cannot
drift into async or lose pagination/conditional writes unnoticed.
"""

from __future__ import annotations

import inspect

import pytest

from coa_control_plane.ports import ControlPlaneStore, Page


def test_port_is_a_runtime_checkable_protocol() -> None:
    assert getattr(ControlPlaneStore, "_is_runtime_protocol", False)


def test_structural_match_accepts_a_minimal_store() -> None:
    class Stub:
        def get(self, key):
            return None

        def put(self, item, *, condition=None, condition_values=None, condition_names=None):
            return None

        def update(self, key, fields, *, remove_fields=None, condition=None, condition_values=None, condition_names=None):
            return True

        def delete(self, key, *, condition=None):
            return None

        def query(self, *, key_condition, expression_values=None, expression_names=None, index_name=None,
                  limit=None, exclusive_start_key=None, scan_forward=True, consistent_read=False):
            return Page()

        def atomic_increment(self, key, attribute, amount=1):
            return amount

        def batch_get(self, keys):
            return ()

        def probe(self):
            return {"status": "ok"}

    assert isinstance(Stub(), ControlPlaneStore)


def test_conditional_write_arguments_are_part_of_the_contract() -> None:
    signature = inspect.signature(ControlPlaneStore.put)
    assert "condition" in signature.parameters
    assert "condition_values" in signature.parameters


def test_pagination_is_part_of_the_contract() -> None:
    signature = inspect.signature(ControlPlaneStore.query)
    assert "exclusive_start_key" in signature.parameters
    assert "limit" in signature.parameters
    assert "index_name" in signature.parameters


def test_page_default_is_empty_and_terminal() -> None:
    page = Page()
    assert page.items == ()
    assert page.last_key is None


@pytest.mark.parametrize("method", ["get", "put", "query", "update", "delete", "atomic_increment", "batch_get"])
def test_every_method_stays_synchronous(method: str) -> None:
    assert not inspect.iscoroutinefunction(getattr(ControlPlaneStore, method))
