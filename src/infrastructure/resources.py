"""Admission control and a cancellation-safe, single-thread PDF renderer."""

import asyncio
import functools
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Any

from fastapi import HTTPException

logger = logging.getLogger(__name__)


class CapacityGate:
    def __init__(
        self, limit: int = 2, max_waiters: int = 5, timeout: float = 10.0
    ) -> None:
        self.limit = limit
        self.max_waiters = max_waiters
        self.timeout = timeout
        self.active = 0
        self.waiting = 0
        self._semaphore = asyncio.Semaphore(limit)

    @staticmethod
    def unavailable() -> HTTPException:
        return HTTPException(
            503, "Service temporarily at capacity", headers={"Retry-After": "10"}
        )

    @asynccontextmanager
    async def slot(self) -> AsyncIterator[None]:
        if not self._semaphore.locked():
            await self._semaphore.acquire()
        else:
            if self.waiting >= self.max_waiters:
                raise self.unavailable()
            self.waiting += 1
            try:
                try:
                    await asyncio.wait_for(self._semaphore.acquire(), self.timeout)
                except TimeoutError as exc:
                    raise self.unavailable() from exc
            finally:
                self.waiting -= 1
        self.active += 1
        logger.info(
            "capacity active=%s waiting=%s limit=%s",
            self.active,
            self.waiting,
            self.limit,
        )
        try:
            yield
        finally:
            self.active -= 1
            self._semaphore.release()


class PDFRenderer:
    def __init__(self) -> None:
        self.gate = CapacityGate(limit=1)
        self._executor: ThreadPoolExecutor | None = None

    async def run(
        self,
        operation: Callable[..., Any],
        *args: Any,
        prepare: Callable[[], Awaitable[Any]] | None = None,
    ) -> Any:
        async with self.gate.slot():
            if prepare is not None:
                data = await prepare()
                if data is None:
                    return None
                args = (data,)
            if self._executor is None:
                self._executor = ThreadPoolExecutor(
                    max_workers=1, thread_name_prefix="odin-pdf"
                )
            future = asyncio.get_running_loop().run_in_executor(
                self._executor, functools.partial(self._render, operation, args)
            )
            try:
                return await asyncio.shield(future)
            except asyncio.CancelledError:
                # A running Python thread cannot be cancelled. Keep admission occupied
                # until it exits, and close its orphaned output before propagating.
                while not future.done():
                    try:
                        await asyncio.shield(future)
                    except asyncio.CancelledError:
                        continue
                    except Exception:
                        break
                if not future.cancelled() and future.exception() is None:
                    result = future.result()
                    if hasattr(result, "close"):
                        result.close()
                raise

    @staticmethod
    def _render(operation: Callable[..., Any], args: tuple[Any, ...]) -> Any:
        try:
            return operation(*args)
        finally:
            # Imported only on the rendering thread, never during application boot.
            import sys

            if "matplotlib.pyplot" in sys.modules:
                sys.modules["matplotlib.pyplot"].close("all")

    def close(self) -> None:
        if self._executor is not None:
            self._executor.shutdown(wait=True)
            self._executor = None


pdf_renderer = PDFRenderer()
