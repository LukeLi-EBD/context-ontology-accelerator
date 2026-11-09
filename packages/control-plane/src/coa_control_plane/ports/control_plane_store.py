"""DynamoDB item semantics as a port (replaces DynamoDB in the Control Plane).

Why this port lives in ``control-plane`` rather than ``coa_ports``: its only
consumer is this package (plan §7.2), and its shape is dictated by the
existing ``coa_common.dao.DatastoreDAO`` surface the handlers already call.

Shape decisions, all deliberate:

* **Synchronous.** ``DatastoreDAO`` is synchronous and the 12 handlers call it
  from sync code. Making the port async would force an async rewrite that this
  phase does not need.
* **Method names match ``DatastoreDAO``** (``get`` / ``put`` / ``query`` /
  ``update`` / ``delete`` / ``atomic_increment`` / ``batch_get``), so a local
  implementation is a drop-in at the injection point.
* **Item maps are the documented transport envelope.** ``Item`` is a
  DynamoDB attribute map whose keys are the caller's attribute names; the port
  cannot know them. This is the one place plan §11.5 allows a mapping in a
  signature, and it is typed as ``Item`` / ``ItemKey`` rather than a bare dict.
* **Conditional writes and exclusive start keys stay first-class.** A local
  implementation that ignores them would silently lose optimistic locking and
  make phase 7 impossible to verify.

Error contract: implementations raise
:class:`coa_ports.errors.PortError`. A failed condition check is ``CONFLICT``;
a missing item is ``NOT_FOUND``; a backend that cannot honour a requested
semantic is ``UNSUPPORTED`` — never a silent downgrade.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

Item = Mapping[str, Any]
"""DynamoDB attribute map. Keys are caller-defined attribute names."""

ItemKey = Mapping[str, Any]
"""Primary key attribute map (partition key, plus sort key when the table has one)."""


@dataclass(frozen=True)
class Page:
    """One page of items plus the cursor that continues it.

    ``last_key`` is ``None`` on the final page. Callers must treat it as
    opaque: it is only meaningful to the provider that produced it.
    """

    items: tuple[Item, ...] = ()
    last_key: ItemKey | None = None


@runtime_checkable
class ControlPlaneStore(Protocol):
    """Item store for namespaces, roles, grants and their indexes."""

    def get(self, key: ItemKey) -> Item | None:
        """Return the item for ``key``, or ``None`` when absent."""
        ...

    def put(
        self,
        item: Item,
        *,
        condition: str | None = None,
        condition_values: Mapping[str, Any] | None = None,
        condition_names: Mapping[str, str] | None = None,
    ) -> None:
        """Create or overwrite ``item``.

        ``condition`` is a condition expression; failing it raises
        ``PortError(CONFLICT)``. ``None`` means unconditional overwrite.
        """
        ...

    def update(
        self,
        key: ItemKey,
        fields: Mapping[str, Any],
        *,
        remove_fields: Sequence[str] | None = None,
        condition: str | None = None,
        condition_values: Mapping[str, Any] | None = None,
        condition_names: Mapping[str, str] | None = None,
    ) -> bool:
        """Partially update one item.

        Returns ``True`` when the item exists and the condition held. A failed
        condition raises ``CONFLICT``; an absent item raises ``NOT_FOUND``.
        ``remove_fields`` lists attributes to delete in the same operation.
        """
        ...

    def delete(self, key: ItemKey, *, condition: str | None = None) -> None:
        """Delete one item; deleting an absent key is a no-op."""
        ...

    def query(
        self,
        *,
        key_condition: str,
        expression_values: Mapping[str, Any] | None = None,
        expression_names: Mapping[str, str] | None = None,
        index_name: str | None = None,
        limit: int | None = None,
        exclusive_start_key: ItemKey | None = None,
        scan_forward: bool = True,
        consistent_read: bool = False,
    ) -> Page:
        """Return one page of items matching ``key_condition``.

        Pagination is returned, never silently collapsed: a provider that
        cannot page raises ``UNSUPPORTED`` instead of ignoring ``limit``.
        """
        ...

    def atomic_increment(self, key: ItemKey, attribute: str, amount: int = 1) -> int:
        """Add ``amount`` to a numeric attribute and return the new value."""
        ...

    def batch_get(self, keys: Sequence[ItemKey]) -> tuple[Item, ...]:
        """Fetch several items by key; absent keys are omitted, order is not guaranteed."""
        ...

    def probe(self) -> Mapping[str, Any]:
        """Reachability snapshot for the health dashboard; never raises."""
        ...


__all__ = ["ControlPlaneStore", "Item", "ItemKey", "Page"]
