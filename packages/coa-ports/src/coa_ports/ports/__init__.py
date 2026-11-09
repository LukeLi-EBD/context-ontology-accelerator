"""Outbound port protocols, grouped by owning bounded context (plan §11.1)."""

from __future__ import annotations

from .admin import GraphAdminPort, WarehouseAdminPort
from .answering import ContextManagerPort, MetricIndexPort
from .change import ChangeFeedPort
from .config import ConfigProvider
from .identity import IdentityPort
from .ontology import SchemaProvider
from .orchestration import (
    ComputePort,
    EventBusPort,
    SchedulerPort,
    ServiceRegistryPort,
    TaskQueuePort,
    WorkflowPort,
)
from .storage import GraphStorePort, MetadataStorePort, ObjectStorePort, SecretProvider

__all__ = [
    "ChangeFeedPort",
    "ComputePort",
    "ConfigProvider",
    "ContextManagerPort",
    "EventBusPort",
    "GraphAdminPort",
    "GraphStorePort",
    "IdentityPort",
    "MetadataStorePort",
    "MetricIndexPort",
    "ObjectStorePort",
    "SchedulerPort",
    "SchemaProvider",
    "SecretProvider",
    "ServiceRegistryPort",
    "TaskQueuePort",
    "WarehouseAdminPort",
    "WorkflowPort",
]
