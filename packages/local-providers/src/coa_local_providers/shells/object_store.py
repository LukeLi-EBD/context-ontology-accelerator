"""``platform_core.adapters.object_layered.LayeredObjectStore`` -> ``coa_ports.ObjectStorePort``.

Signature differences (S8, measured in ``doc/coa-x/02-薄壳清点.md``):

- method names and parameters are identical, and both sides are synchronous;
- every return is a dict (or a list of dicts) where the port promises
  ``ObjectInfo`` / ``tuple[ObjectInfo, ...]``;
- the port adds ``probe``; the layered store has no health method, so the
  shell probes with one cheap read unless the inner object exposes
  ``probe``/``health``.

The dict->``ObjectInfo`` mapping reads the platform envelope
(``ref.bucket``/``ref.key``/``ref.size``/``ref.etag``, ``contentType``,
``metadata``). On ``put`` the platform only returns ``ref`` plus ``tier``, so
the content type and metadata come from the caller's arguments — those are
exactly the values the adapter stored, not a guess.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from coa_ports import ObjectInfo, PortError

from .errors import to_port_error

_REQUIRED_METHODS = ("put", "get", "head", "delete", "list")
_PROBE_BUCKET = "__coa_probe__"
_PROBE_PREFIX = "__coa_probe__"


class ObjectStoreShell:
    """Adapt a platform object store to the COA ``ObjectStorePort``.

    Args:
        inner: A platform store exposing ``put``/``get``/``head``/``delete``/
            ``list``. Typed ``object`` so importing this module does not drag
            in the adapter stack.
        provider: Provider name recorded on translated errors.
    """

    def __init__(self, inner: object, *, provider: str = "layered") -> None:
        missing = [
            name for name in _REQUIRED_METHODS if not callable(getattr(inner, name, None))
        ]
        if missing:
            raise TypeError(f"inner must expose callable {', '.join(missing)}")
        self._inner = inner
        self._provider = provider

    def put(
        self,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str = "application/octet-stream",
        metadata: Mapping[str, str] | None = None,
    ) -> ObjectInfo:
        """Store ``body`` and return its metadata."""
        result = self._call("put", bucket, key, body, content_type, metadata)
        ref = result.get("ref") if isinstance(result, Mapping) else None
        ref = ref if isinstance(ref, Mapping) else {}
        return ObjectInfo(
            bucket=bucket,
            key=key,
            size=int(ref.get("size", len(body))),
            content_type=content_type,
            metadata=dict(metadata or {}),
            etag=str(ref.get("etag", "")),
        )

    def get(self, bucket: str, key: str) -> tuple[bytes, ObjectInfo]:
        """Return ``(body, metadata)``; a missing key raises ``not_found``."""
        body, meta = self._call("get", bucket, key)
        return body, self._info(meta, bucket, key)

    def head(self, bucket: str, key: str) -> ObjectInfo:
        """Return metadata only; a missing key raises ``not_found``."""
        return self._info(self._call("head", bucket, key), bucket, key)

    def delete(self, bucket: str, key: str) -> None:
        """Delete one object; deleting an absent key is a no-op."""
        self._call("delete", bucket, key)

    def list(self, bucket: str, prefix: str = "", limit: int = 100) -> tuple[ObjectInfo, ...]:
        """List objects under ``prefix``."""
        rows = self._call("list", bucket, prefix, limit)
        return tuple(self._info(row, bucket, "") for row in rows)

    def probe(self) -> Mapping[str, Any]:
        """Reachability snapshot; never raises.

        Prefers a native ``probe``/``health`` on the inner object. Otherwise it
        performs one read through the normal ``list`` path, which reaches the
        metadata backend without writing anything.
        """
        snapshot: dict[str, Any] = {"status": "ok", "provider": self._provider}
        try:
            native = getattr(self._inner, "probe", None)
            health = getattr(self._inner, "health", None)
            if callable(native):
                extra = native()
                if isinstance(extra, Mapping):
                    snapshot.update(extra)
            elif callable(health):
                health()
            else:
                self._inner.list(_PROBE_BUCKET, _PROBE_PREFIX, 1)  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001 - probe must never raise
            return {
                "status": "unavailable",
                "provider": self._provider,
                "provider_code": str(
                    getattr(exc, "provider_code", "") or type(exc).__name__
                ),
            }
        return snapshot

    # ── internals ───────────────────────────────────────────────────────────

    def _call(self, method: str, *args: Any) -> Any:
        try:
            return getattr(self._inner, method)(*args)
        except PortError:
            raise
        except Exception as exc:  # noqa: BLE001 - platform error class is not importable here
            raise to_port_error(
                exc, provider=self._provider, message=f"object {method} failed"
            ) from exc

    @staticmethod
    def _info(meta: Any, bucket: str, key: str) -> ObjectInfo:
        envelope = meta if isinstance(meta, Mapping) else {}
        ref = envelope.get("ref")
        ref = ref if isinstance(ref, Mapping) else {}
        return ObjectInfo(
            bucket=str(ref.get("bucket", bucket)),
            key=str(ref.get("key", key)),
            size=int(ref.get("size", 0)),
            content_type=str(envelope.get("contentType", "application/octet-stream")),
            metadata=dict(envelope.get("metadata") or {}),
            etag=str(ref.get("etag", "")),
        )


__all__ = ["ObjectStoreShell"]
