"""Ubiquitous-language value objects (doc/coa-x/00-总计划.md §11.2).

These are transport-neutral aliases, not domain aggregates. They exist so a
port signature cannot silently swap a namespace id for a graph uri, or a
document id for a data source id. ``NewType`` is a static-typing device only;
at runtime every alias is still ``str`` and is not validated here.
"""

from __future__ import annotations

from typing import NewType

NamespaceId = NewType("NamespaceId", str)
"""Tenant / isolation boundary. UUID v4, owned by the Control Plane context."""

Iri = NewType("Iri", str)
"""RDF subject / predicate / object IRI. Owned by the Knowledge Graph context."""

GraphUri = NewType("GraphUri", str)
"""Named graph identifier. Never call this a namespace."""

EntityRef = NewType("EntityRef", tuple[NamespaceId, Iri])
"""A graph subject addressed inside one namespace."""

DocumentId = NewType("DocumentId", str)
"""Document identity. Owned by the Document Ingestion context."""

ChunkId = NewType("ChunkId", str)
"""Stable identifier of a retrievable chunk. Owned by the Document Ingestion context."""

MetricName = NewType("MetricName", str)
"""Metric definition name, unique per namespace. Owned by the Metrics context."""

DataSourceId = NewType("DataSourceId", str)
"""Database connection identity. Owned by the Data Source Onboarding context."""

OntologyId = NewType("OntologyId", str)
"""Ontology identity inside a namespace. Owned by the Ontology context."""

OntologyVersion = NewType("OntologyVersion", str)
"""Immutable ontology release identifier (content hash + publishedAt + graph uri)."""

PrincipalId = NewType("PrincipalId", str)
"""Caller identity. Owned by the Control Plane context."""

TaskId = NewType("TaskId", str)
"""Queued task identity."""

ReceiptHandle = NewType("ReceiptHandle", str)
"""Opaque acknowledgement handle for a received queued message."""

WorkflowRunId = NewType("WorkflowRunId", str)
"""One workflow execution identity."""

EventId = NewType("EventId", str)
"""One published event identity."""

ScheduleId = NewType("ScheduleId", str)
"""One scheduled job identity."""

Cursor = NewType("Cursor", str)
"""Opaque change-feed cursor. Never parse or synthesise it outside the provider."""

__all__ = [
    "ChunkId",
    "Cursor",
    "DataSourceId",
    "DocumentId",
    "EntityRef",
    "EventId",
    "GraphUri",
    "Iri",
    "MetricName",
    "NamespaceId",
    "OntologyId",
    "OntologyVersion",
    "PrincipalId",
    "ReceiptHandle",
    "ScheduleId",
    "TaskId",
    "WorkflowRunId",
]
