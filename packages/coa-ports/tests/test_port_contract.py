"""Structural contract tests for the outbound ports.

These do not test any implementation. They enforce the design rules that
would otherwise drift silently: the error code set is closed, every port is
runtime-checkable, and no port signature leaks a bare ``dict`` (the only
allowed mapping is a documented transport envelope inside the DTOs).
"""

from __future__ import annotations

import inspect

import pytest

from coa_ports import ports
from coa_ports.errors import PortErrorCode

ALL_PORTS = [
    ports.ChangeFeedPort,
    ports.ComputePort,
    ports.ConfigProvider,
    ports.ContextManagerPort,
    ports.EventBusPort,
    ports.GraphStorePort,
    ports.IdentityPort,
    ports.MetadataStorePort,
    ports.ObjectStorePort,
    ports.SchedulerPort,
    ports.SchemaProvider,
    ports.SecretProvider,
    ports.ServiceRegistryPort,
    ports.TaskQueuePort,
    ports.WorkflowPort,
]


def test_error_code_set_is_closed() -> None:
    assert {str(code) for code in PortErrorCode} == {
        "not_found",
        "unavailable",
        "timeout",
        "invalid_argument",
        "conflict",
        "unsupported",
        "internal",
    }


@pytest.mark.parametrize("port", ALL_PORTS, ids=lambda p: p.__name__)
def test_every_port_is_runtime_checkable(port: type) -> None:
    assert getattr(port, "_is_runtime_protocol", False), f"{port.__name__} must be @runtime_checkable"


@pytest.mark.parametrize("port", ALL_PORTS, ids=lambda p: p.__name__)
def test_no_bare_dict_in_port_signatures(port: type) -> None:
    offenders: list[str] = []
    for name, member in inspect.getmembers(port, predicate=inspect.isfunction):
        if name.startswith("_"):
            continue
        for annotation in inspect.getfullargspec(member).annotations.values():
            text = str(annotation)
            if text == "dict" or text.startswith("dict["):
                offenders.append(f"{port.__name__}.{name}: {text}")
    assert not offenders, "port signatures must use typed aliases or Mapping, not bare dict: " + "; ".join(
        offenders
    )


@pytest.mark.parametrize("port", ALL_PORTS, ids=lambda p: p.__name__)
def test_every_port_declares_at_least_one_method(port: type) -> None:
    methods = [
        name
        for name, member in inspect.getmembers(port, predicate=inspect.isfunction)
        if not name.startswith("_")
    ]
    assert methods, f"{port.__name__} has no methods"
