"""``platform_core.adapters.metadata_pg.MetadataPg`` -> ``coa_ports.MetadataStorePort``.

Signature differences (S9, measured in ``doc/coa-x/02-薄壳清点.md``):

- the port adds ``probe``; the platform adapter has ``health`` and no probe;
- ``query`` returns ``list[dict]``, the port promises ``tuple[Mapping, ...]``;
- ``execute`` already returns the affected row count; it is forwarded as is;
- both are synchronous, and ``params`` already accepts tuple or list.

Nothing else changes: no SQL is rewritten, no statement is retried, no rule is
added. A platform error becomes a ``coa_ports.PortError`` with one of the
seven closed codes; a driver error (which carries no platform code) becomes
``internal`` rather than being guessed into ``invalid_argument``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from coa_ports import PortError

from .errors import to_port_error

_REQUIRED_METHODS = ("query", "execute")


class MetadataStoreShell:
    """Adapt a platform metadata store to the COA ``MetadataStorePort``.

    Args:
        inner: A platform store exposing ``query``/``execute`` and either
            ``probe`` or ``health``. Typed ``object`` so importing this
            module does not drag in the psycopg adapter stack.
        provider: Provider name recorded on translated errors.
    """

    def __init__(self, inner: object, *, provider: str = "postgres") -> None:
        missing = [
            name for name in _REQUIRED_METHODS if not callable(getattr(inner, name, None))
        ]
        if missing:
            raise TypeError(f"inner must expose callable {', '.join(missing)}")
        self._inner = inner
        self._provider = provider

    def query(
        self, sql: str, params: tuple[Any, ...] | list[Any] = ()
    ) -> tuple[Mapping[str, Any], ...]:
        """Run a read statement; the list of dict rows becomes a tuple."""
        try:
            rows = self._inner.query(sql, params)  # type: ignore[attr-defined]
        except PortError:
            raise
        except Exception as exc:  # noqa: BLE001 - platform error class is not importable here
            raise to_port_error(
                exc, provider=self._provider, message="metadata query failed"
            ) from exc
        return tuple(rows)

    def execute(self, sql: str, params: tuple[Any, ...] | list[Any] = ()) -> int:
        """Run a write statement and return the affected row count."""
        try:
            affected = self._inner.execute(sql, params)  # type: ignore[attr-defined]
        except PortError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_port_error(
                exc, provider=self._provider, message="metadata execute failed"
            ) from exc
        return int(affected)

    def probe(self) -> Mapping[str, Any]:
        """Reachability snapshot; never raises.

        Prefers a native ``probe``, then ``health``, then a bare ``SELECT 1``.
        The fallback is a reachability check, not a business call.
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
                self._inner.query("SELECT 1 AS ok")  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001 - probe must never raise
            return {
                "status": "unavailable",
                "provider": self._provider,
                "provider_code": str(
                    getattr(exc, "provider_code", "") or type(exc).__name__
                ),
            }
        return snapshot


__all__ = ["MetadataStoreShell"]
