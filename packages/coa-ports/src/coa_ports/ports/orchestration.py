"""Orchestration ports (replace SQS / StepFunctions / EventBridge / ECS / Cloud Map).

Six independent capabilities, six independent configuration keys. They are
infrastructure ports: no aggregate, no domain event, no repository.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from ..dto import (
    ComputeResult,
    QueueMessage,
    ScheduleHandle,
    ServiceEndpoint,
    WorkflowRun,
)
from ..language import EventId, ScheduleId, TaskId, WorkflowRunId


@runtime_checkable
class TaskQueuePort(Protocol):
    """Work queue (replaces SQS)."""

    async def enqueue(
        self,
        queue: str,
        payload: Mapping[str, Any],
        *,
        delay_seconds: int = 0,
    ) -> TaskId:
        """Put one message on ``queue`` and return its task identity."""
        ...

    async def receive(
        self,
        queue: str,
        *,
        max_messages: int = 1,
        wait_seconds: int = 0,
    ) -> tuple[QueueMessage, ...]:
        """Take up to ``max_messages`` messages; the empty tuple means nothing arrived."""
        ...

    async def ack(self, message: QueueMessage) -> None:
        """Acknowledge one message of ``message.receipt``; repeated acks are not an error."""
        ...

    async def health_check(self) -> Mapping[str, Any]:
        """Probe reachability; never raises."""
        ...


@runtime_checkable
class WorkflowPort(Protocol):
    """State machine execution (replaces StepFunctions)."""

    async def start(self, workflow: str, payload: Mapping[str, Any]) -> WorkflowRun:
        """Start ``workflow`` and return its initial run state."""
        ...

    async def describe(self, run_id: WorkflowRunId) -> WorkflowRun:
        """Read the current state; a missing run raises ``not_found``."""
        ...

    async def cancel(self, run_id: WorkflowRunId) -> None:
        """Request cancellation; cancelling a terminal run is a no-op."""
        ...


@runtime_checkable
class EventBusPort(Protocol):
    """Fact publication (replaces EventBridge)."""

    async def publish(
        self,
        source: str,
        detail_type: str,
        detail: Mapping[str, Any],
    ) -> EventId:
        """Publish one event and return its identity."""
        ...


@runtime_checkable
class SchedulerPort(Protocol):
    """Deferred execution (replaces EventBridge Scheduler)."""

    async def schedule(
        self,
        name: str,
        run_at: str,
        payload: Mapping[str, Any],
        *,
        group: str = "default",
    ) -> ScheduleHandle:
        """Schedule one job at ``run_at`` (ISO-8601, UTC) and return its handle."""
        ...

    async def cancel(self, schedule_id: ScheduleId) -> None:
        """Cancel one schedule; cancelling a fired schedule is a no-op."""
        ...

    async def list_schedules(self, *, group: str | None = None) -> tuple[ScheduleHandle, ...]:
        """List pending schedules, optionally filtered by group."""
        ...


@runtime_checkable
class ComputePort(Protocol):
    """Task execution (replaces ECS run-task)."""

    async def run(self, task: str, payload: Mapping[str, Any]) -> ComputeResult:
        """Run ``task`` to completion and return its outcome."""
        ...

    async def health_check(self) -> Mapping[str, Any]:
        """Probe reachability; never raises."""
        ...


@runtime_checkable
class ServiceRegistryPort(Protocol):
    """Service discovery (replaces Cloud Map)."""

    async def resolve(self, name: str) -> ServiceEndpoint:
        """Resolve ``name``; an unknown name raises ``not_found``."""
        ...

    async def register(
        self,
        name: str,
        url: str,
        *,
        ttl_seconds: int = 0,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Register or refresh one endpoint."""
        ...

    async def deregister(self, name: str) -> None:
        """Remove one endpoint; removing an unknown name is a no-op."""
        ...
