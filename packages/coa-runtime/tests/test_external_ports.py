"""The two ports that live outside ``coa_ports`` must match the catalog.

``ControlPlaneStore`` sits in ``control-plane`` and ``OcrPort`` in
``context-manager`` (plan §7.2). The catalog records where each Protocol lives
and which methods it must expose; this test makes a drift between the two
fail here instead of at a call site.
"""

from __future__ import annotations

import importlib
import inspect

import pytest

from coa_runtime.catalog import catalog


def _spec(name: str):
    return catalog()[name]


@pytest.mark.parametrize("name", ["ControlPlaneStore", "OcrPort"])
def test_catalog_records_an_external_port_location(name: str) -> None:
    assert _spec(name).port_location, f"{name} must declare port_location"


@pytest.mark.parametrize("name", ["ControlPlaneStore", "OcrPort"])
def test_declared_module_exposes_a_runtime_checkable_protocol(name: str) -> None:
    module = importlib.import_module(_spec(name).port_location)
    protocol = getattr(module, name)
    assert getattr(protocol, "_is_runtime_protocol", False), f"{name} must be @runtime_checkable"


@pytest.mark.parametrize("name", ["ControlPlaneStore", "OcrPort"])
def test_required_methods_exist_on_the_protocol(name: str) -> None:
    spec = _spec(name)
    module = importlib.import_module(spec.port_location)
    protocol = getattr(module, name)
    declared = {method for method, _ in inspect.getmembers(protocol, predicate=inspect.isfunction)}
    assert set(spec.required_methods) <= declared


def test_control_plane_store_is_sync_by_design() -> None:
    module = importlib.import_module("coa_control_plane.ports")
    store = module.ControlPlaneStore
    for method in ("get", "put", "query", "update", "delete", "atomic_increment"):
        assert not inspect.iscoroutinefunction(getattr(store, method)), f"{method} must stay sync"


def test_ocr_port_is_async_by_design() -> None:
    module = importlib.import_module("coa_serve.ports")
    port = module.OcrPort
    assert inspect.iscoroutinefunction(port.extract)
    assert inspect.iscoroutinefunction(port.health_check)


def test_both_ports_have_one_config_key_each() -> None:
    keys = {
        "ControlPlaneStore": "COA_PROVIDER_CONTROL_PLANE_STORE",
        "OcrPort": "COA_PROVIDER_OCR",
    }
    for name, key in keys.items():
        assert _spec(name).key == key
