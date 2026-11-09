"""Port to the Ontology context (replaces Glue / DescribeSchema Lambda).

``SchemaProvider`` returns a schema snapshot for one namespace. It does not
return graph instances; those belong to the Knowledge Graph context.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from ..dto import SchemaSnapshot
from ..language import NamespaceId


@runtime_checkable
class SchemaProvider(Protocol):
    """Async schema lookup for a namespace."""

    async def describe_schema(
        self,
        namespace_id: NamespaceId,
        *,
        include_properties: bool = False,
        max_results: int = 1000,
        auth_token: str = "",
    ) -> SchemaSnapshot:
        """Return the queryable schema.

        ``ontology_version`` is ``None`` when no immutable release exists; a
        provider must never substitute ``updatedAt`` or any other timestamp.
        """
        ...

    async def health_check(self) -> Mapping[str, Any]:
        """Probe reachability; never raises."""
        ...
