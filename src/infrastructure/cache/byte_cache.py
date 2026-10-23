"""A byte-budgeted TTL/LRU cache; no domain object graphs are retained."""

import time
from collections import OrderedDict
from collections.abc import Callable


class ByteCache:
    def __init__(
        self,
        max_bytes: int = 16 * 1024 * 1024,
        max_entry_bytes: int = 1024 * 1024,
        max_keys: int = 512,
        now_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_bytes = max_bytes
        self.max_entry_bytes = max_entry_bytes
        self.max_keys = max_keys
        self.now = now_fn
        self.data: OrderedDict[str, tuple[float, bytes]] = OrderedDict()
        self.bytes_used = 0

    def _remove(self, key: str) -> None:
        entry = self.data.pop(key, None)
        if entry is not None:
            self.bytes_used -= len(entry[1])

    def get(self, key: str) -> bytes | None:
        entry = self.data.get(key)
        if entry is None:
            return None
        if self.now() >= entry[0]:
            self._remove(key)
            return None
        self.data.move_to_end(key)
        return entry[1]

    def set(self, key: str, value: bytes, ttl: float) -> None:
        self._remove(key)
        for expired in [
            k for k, (deadline, _) in self.data.items() if self.now() >= deadline
        ]:
            self._remove(expired)
        if len(value) > min(self.max_entry_bytes, self.max_bytes) or self.max_keys <= 0:
            return
        while self.data and (
            self.bytes_used + len(value) > self.max_bytes
            or len(self.data) >= self.max_keys
        ):
            self._remove(next(iter(self.data)))
        self.data[key] = (self.now() + ttl, value)
        self.bytes_used += len(value)

    def clear(self) -> None:
        self.data.clear()
        self.bytes_used = 0
