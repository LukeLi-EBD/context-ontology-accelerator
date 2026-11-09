"""Run a synchronous platform adapter from COA's async surface.

One bounded pool per shell instance, not one per call: a slow backend then
cannot grow threads without limit, and two independent ports never compete for
the same workers.

Timeouts and cancellation are explicit:

* a timeout raises ``PortError(TIMEOUT)`` and cancels the queued work item;
* a cancelled caller cancels the queued work item and re-raises ``CancelledError``.

A running Python thread cannot be interrupted, so an in-flight call finishes on
its own and returns its slot afterwards. That is why the pool is bounded and why
the timeout is documented as "stop waiting", not "stop the backend".
"""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any, TypeVar

from coa_ports import PortError, PortErrorCode

T = TypeVar("T")


class SyncToAsyncShell:
    """Await a blocking callable on a bounded thread pool."""

    def __init__(
        self,
        *,
        provider: str,
        max_workers: int = 8,
        timeout_s: float = 60.0,
        thread_name_prefix: str = "coa-sync",
    ) -> None:
        if max_workers <= 0:
            raise ValueError("max_workers must be positive")
        if timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        self.provider = provider
        self.timeout_s = timeout_s
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=thread_name_prefix)

    async def call(
        self,
        fn: Callable[..., T],
        *args: Any,
        timeout_s: float | None = None,
        **kwargs: Any,
    ) -> T:
        """Run ``fn(*args, **kwargs)`` in the pool and await its result."""
        timeout = self.timeout_s if timeout_s is None else timeout_s
        future = asyncio.get_running_loop().run_in_executor(self._pool, functools.partial(fn, *args, **kwargs))
        try:
            return await asyncio.wait_for(asyncio.shield(future), timeout)
        except asyncio.TimeoutError as exc:
            # Best effort: a queued item is dropped, a running one keeps its slot
            # until the backend returns. The caller is released either way.
            future.cancel()
            raise PortError(
                PortErrorCode.TIMEOUT,
                f"synchronous call did not finish within {timeout:g}s",
                provider=self.provider,
                provider_code="E_SYNC_TIMEOUT",
                details={"timeout_s": timeout, "callable": getattr(fn, "__name__", type(fn).__name__)},
            ) from exc
        except asyncio.CancelledError:
            future.cancel()
            raise

    def close(self) -> None:
        """Drop queued work; running calls finish on their own."""
        self._pool.shutdown(wait=False, cancel_futures=True)


__all__ = ["SyncToAsyncShell"]
