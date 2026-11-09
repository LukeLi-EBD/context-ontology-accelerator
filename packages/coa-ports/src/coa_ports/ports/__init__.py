"""Outbound port protocols, grouped by owning bounded context (plan §11.1)."""

from __future__ import annotations

from .answering import ContextManagerPort
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
    "GraphStorePort",
    "IdentityPort",
    "MetadataStorePort",
    "ObjectStorePort",
    "SchedulerPort",
    "SchemaProvider",
    "SecretProvider",
    "ServiceRegistryPort",
    "TaskQueuePort",
    "WorkflowPort",
]
