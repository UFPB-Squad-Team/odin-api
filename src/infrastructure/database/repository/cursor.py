"""Bounded cursor traversal, including deterministic cursor cleanup."""

import logging
import time
from collections.abc import AsyncGenerator
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CursorMetrics:
    seconds: float = 0.0
    documents: int = 0


cursor_metrics: ContextVar[CursorMetrics | None] = ContextVar(
    "cursor_metrics", default=None
)


async def iter_documents(cursor: Any) -> AsyncGenerator[dict, None]:
    if hasattr(cursor, "batch_size"):
        cursor = cursor.batch_size(100)
    iterator = aiter(cursor)
    query_seconds = 0.0
    count = 0
    try:
        while True:
            started = time.monotonic()
            try:
                document = await anext(iterator)
            except StopAsyncIteration:
                query_seconds += time.monotonic() - started
                break
            query_seconds += time.monotonic() - started
            count += 1
            yield document
    finally:
        totals = cursor_metrics.get()
        if totals is not None:
            totals.seconds += query_seconds
            totals.documents += count
        logger.info(
            "mongo_cursor documents=%s query_ms=%.1f", count, query_seconds * 1000
        )
        if hasattr(cursor, "close"):
            await cursor.close()
