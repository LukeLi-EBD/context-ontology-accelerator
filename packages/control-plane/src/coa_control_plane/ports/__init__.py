"""Outbound ports owned by the Control Plane context (plan §7.2).

Only ports whose only consumer is this package live here. Cross-service
ports stay in ``coa_ports``.
"""

from __future__ import annotations

from .control_plane_store import ControlPlaneStore, Item, ItemKey, Page

__all__ = ["ControlPlaneStore", "Item", "ItemKey", "Page"]
