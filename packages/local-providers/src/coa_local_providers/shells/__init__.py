"""Anti-corruption shells between ``platform_core`` adapters and COA ports.

Each module here adapts one platform adapter to one port defined in
``coa_ports`` (or in a COA service package). A shell may only:

* translate call style (sync/async),
* reshape arguments and return values,
* map error codes.

It must not contain business rules. Shells are imported by the composition
root (``coa_runtime``) and by nobody else.
"""

from __future__ import annotations

from .graph_store import GraphStoreShell
from .metadata_store import MetadataStoreShell
from .object_store import ObjectStoreShell
from .secret_env import EnvSecretShell

__all__ = ["EnvSecretShell", "GraphStoreShell", "MetadataStoreShell", "ObjectStoreShell"]
