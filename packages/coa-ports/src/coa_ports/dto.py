"""Transport-neutral DTOs for the outbound ports.

Every field name here is the authority from plan §11.2. ``dict[str, Any]`` is
allowed only in the two documented transport envelopes (``ContextRequest`` /
``ContextResponse``) whose keys are fixed by the COA contract, never in a
domain-facing port.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .language import (
    ChunkId,
    DataSourceId,
    DocumentId,
    Iri,
    MetricName,
    NamespaceId,
    OntologyVersion,
    PrincipalId,
    ReceiptHandle,
    ScheduleId,
    TaskId,
    WorkflowRunId,
)


# ── Control Plane ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Principal:
    """Projection of the Control Plane's Principal for use inside one call."""

    principal_id: PrincipalId
    email: str = ""
    groups: tuple[str, ...] = ()
    global_roles: tuple[str, ...] = ()


@dataclass(frozen=True)
class AuthorizationDecision:
    """Result of one authorization check. ``reason`` is diagnostic, never client text."""

    allowed: bool
    reason: str = ""


# ── Answering & Retrieval ────────────────────────────────────────────────────


class ContextAction(StrEnum):
    """The four COA contract actions plus the extension answer call."""

    QUERY = "query"
    TRANSLATE = "translate"
    KB_SEARCH = "kbSearch"
    GRAPH_TRAVERSE = "graphTraverse"
    ANSWER = "answer"


@dataclass(frozen=True)
class GraphCluster:
    """One graph cluster as the admin plane reports it.

    ``identifier`` is the cluster's stable name (a Neptune cluster id locally, a
    local endpoint URL for the single-node provider). ``endpoints`` holds the
    writer, reader and custom endpoints that must be treated as the same cluster.
    """

    identifier: str
    engine: str
    endpoints: tuple[str, ...]
    iam_auth_enabled: bool = True


@dataclass(frozen=True)
class MetricRecord:
    """One metric to make findable by description.

    ``text`` is the provider's searchable projection of the metric (name,
    definition, formula); it is built by the caller, not by the port, so a
    provider never has to know the metric model.
    """

    namespace: NamespaceId
    name: MetricName
    text: str


@dataclass(frozen=True)
class MetricHit:
    """One metric search result. ``score`` is provider-relative, not a probability."""

    namespace: NamespaceId
    name: MetricName
    text: str
    score: float


@dataclass(frozen=True)
class ContextRequest:
    """One request to the Answering & Retrieval context.

    ``options`` is the documented transport envelope: its keys are the COA
    contract's option names, not free-form domain data.
    """

    action: ContextAction
    namespace_id: NamespaceId
    query: str
    principal: Principal
    auth_token: str = ""
    options: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContextResponse:
    """One response from the Answering & Retrieval context.

    ``body`` is the contract payload already shaped by the remote context.
    ``request_id`` / ``session_id`` stay first-class because every caller
    needs them for tracing.
    """

    body: Mapping[str, Any]
    request_id: str | None = None
    session_id: str | None = None


# ── Ontology ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SchemaClass:
    """One class in a schema snapshot."""

    iri: Iri
    label: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SchemaSnapshot:
    """Queryable schema for one namespace.

    ``ontology_version`` is ``None`` when no immutable version exists yet;
    callers must not substitute a record timestamp.
    """

    classes: tuple[SchemaClass, ...] = ()
    ontology_version: OntologyVersion | None = None


# ── Orchestration ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class QueueMessage:
    """One received queue message. ``payload`` is the producer's document."""

    task_id: TaskId
    queue: str
    payload: Mapping[str, Any]
    receipt: ReceiptHandle


class WorkflowStatus(StrEnum):
    """Lifecycle of one workflow run, normalised across local and AWS providers."""

    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class WorkflowRun:
    """Observed state of one workflow run."""

    run_id: WorkflowRunId
    status: WorkflowStatus
    output: Mapping[str, Any] | None = None
    error: str = ""


@dataclass(frozen=True)
class ServiceEndpoint:
    """A resolved service instance."""

    name: str
    url: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComputeResult:
    """Outcome of one compute task."""

    task: str
    status: WorkflowStatus
    output: Mapping[str, Any] | None = None
    exit_code: int | None = None
    error: str = ""


@dataclass(frozen=True)
class ScheduleHandle:
    """Identity of one scheduled job."""

    schedule_id: ScheduleId
    name: str


# ── Change feed ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ChangeBatch:
    """A page of change records plus the cursor that continues it."""

    records: tuple[Mapping[str, Any], ...] = ()
    next_cursor: str | None = None
    truncated: bool = False


# ── Storage and graph (reused interfaces) ────────────────────────────────────


@dataclass(frozen=True)
class ObjectInfo:
    """Metadata for one stored object. ``etag`` is opaque."""

    bucket: str
    key: str
    size: int
    content_type: str = "application/octet-stream"
    metadata: Mapping[str, str] = field(default_factory=dict)
    etag: str = ""


@dataclass(frozen=True)
class GraphQueryResult:
    """Term-neutral result of a SPARQL query.

    ``kind`` is ``select`` or ``ask``. ``rows`` carries flat bindings
    (``{variable: value}``), never platform term dictionaries.
    """

    kind: str
    rows: tuple[Mapping[str, Any], ...] = ()
    boolean: bool | None = None


@dataclass(frozen=True)
class DocumentVersionRef:
    """What downstream contexts may know about a document version."""

    document_id: DocumentId
    version: str = ""


@dataclass(frozen=True)
class ChunkRef:
    """What downstream contexts may know about a retrievable chunk."""

    chunk_id: ChunkId
    document_id: DocumentId
    text: str = ""
    score: float = 0.0
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MetricObservation:
    """One persisted metric observation (plan §11.2)."""

    namespace_id: NamespaceId
    metric_name: MetricName
    period_start: str
    period_end: str
    value: float
    unit: str = ""
    dimensions: Mapping[str, str] = field(default_factory=dict)
    data_source_id: DataSourceId | None = None
    synthetic: bool = False


@dataclass(frozen=True)
class MetricComputation:
    """One read-only metric computation. Never persisted by this operation."""

    namespace_id: NamespaceId
    metric_name: MetricName
    value: float
    period_start: str
    period_end: str
    unit: str = ""
    data_source_id: DataSourceId | None = None
    truncated: bool = False


__all__ = [
    "AuthorizationDecision",
    "ChangeBatch",
    "ChunkRef",
    "ComputeResult",
    "ContextAction",
    "ContextRequest",
    "ContextResponse",
    "DocumentVersionRef",
    "GraphQueryResult",
    "MetricComputation",
    "MetricObservation",
    "ObjectInfo",
    "Principal",
    "QueueMessage",
    "ScheduleHandle",
    "SchemaClass",
    "SchemaSnapshot",
    "ServiceEndpoint",
    "WorkflowRun",
    "WorkflowStatus",
]
