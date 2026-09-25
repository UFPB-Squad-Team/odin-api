"""In-memory TTL cache for expensive aggregation use cases (ODIN-B09).

The cache is per-process (each Gunicorn worker keeps its own instance). The
hot set is small (a few states x a handful of municipalities), so a plain
``dict`` guarded by an ``asyncio.Lock`` is enough — no external dependency
(Redis was explicitly rejected for this scale in ADR-002).
"""

import asyncio
import time
from typing import Any, Callable


class AggregationCache:
    """Bounded TTL cache safe for concurrent async use.

    Entries expire lazily on read and are purged on write. When the cache
    exceeds ``max_keys``, expired entries are removed first and then the
    oldest remaining entries (insertion order) are evicted.
    """

    def __init__(
        self,
        *,
        ttl_seconds: float = 300.0,
        max_keys: int = 512,
        now_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl_seconds = ttl_seconds
        self._max_keys = max_keys
        self._now = now_fn
        self._data: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        """Return the cached value or ``None`` when missing/expired."""
        async with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if self._now() >= expires_at:
                self._data.pop(key, None)
                return None
            return value

    async def set(self, key: str, value: Any) -> None:
        """Store ``value`` under ``key`` with a fresh TTL."""
        async with self._lock:
            self._data[key] = (self._now() + self._ttl_seconds, value)
            self._evict_locked()

    async def clear(self) -> None:
        """Drop every cached entry (e.g. after a data reload)."""
        async with self._lock:
            self._data.clear()

    @property
    def size(self) -> int:
        return len(self._data)

    def _evict_locked(self) -> None:
        now = self._now()
        expired = [k for k, (expires_at, _) in self._data.items() if now >= expires_at]
        for key in expired:
            self._data.pop(key, None)

        overflow = len(self._data) - self._max_keys
        if overflow > 0:
            for key in list(self._data):
                if overflow <= 0:
                    break
                self._data.pop(key, None)
                overflow -= 1


def uf_cache_key(sg_uf: str | list[str] | None) -> tuple[str, ...] | None:
    """Normalize a UF filter into a deterministic, order-insensitive tuple.

    ``["PB", "PE"]`` and ``["PE", "PB"]`` produce the same tuple so both
    requests hit the same cache entry.
    """
    if isinstance(sg_uf, str):
        uf = sg_uf.strip().upper()
        return (uf,) if uf else None
    if not sg_uf:
        return None
    normalized = {uf.strip().upper() for uf in sg_uf if uf.strip()}
    return tuple(sorted(normalized)) or None
