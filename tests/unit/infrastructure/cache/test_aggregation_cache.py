import asyncio

import pytest

from src.infrastructure.cache.aggregation_cache import AggregationCache, uf_cache_key


class FakeClock:
    def __init__(self, start: float = 1000.0):
        self.now = start

    def __call__(self) -> float:
        return self.now


@pytest.mark.asyncio
async def test_cache_miss_returns_none_then_hit_returns_stored_value():
    cache = AggregationCache(ttl_seconds=300)

    assert await cache.get("key") is None

    await cache.set("key", {"result": 1})

    assert await cache.get("key") == {"result": 1}


@pytest.mark.asyncio
async def test_cache_entry_expires_after_ttl():
    clock = FakeClock()
    cache = AggregationCache(ttl_seconds=300, now_fn=clock)

    await cache.set("key", "value")
    assert await cache.get("key") == "value"

    # Just before the TTL boundary the entry is still valid.
    clock.now += 299.9
    assert await cache.get("key") == "value"

    # Past the boundary the entry is expired.
    clock.now += 0.2
    assert await cache.get("key") is None


@pytest.mark.asyncio
async def test_cache_evicts_oldest_when_overflowing():
    cache = AggregationCache(ttl_seconds=300, max_keys=2)

    await cache.set("a", 1)
    await cache.set("b", 2)
    await cache.set("c", 3)

    assert await cache.get("a") is None  # oldest evicted
    assert await cache.get("b") == 2
    assert await cache.get("c") == 3
    assert cache.size == 2


@pytest.mark.asyncio
async def test_cache_overwrites_existing_key_without_growing():
    cache = AggregationCache(ttl_seconds=300, max_keys=2)

    await cache.set("key", 1)
    await cache.set("key", 2)

    assert await cache.get("key") == 2
    assert cache.size == 1


@pytest.mark.asyncio
async def test_cache_clear_drops_all_entries():
    cache = AggregationCache(ttl_seconds=300)

    await cache.set("a", 1)
    await cache.set("b", 2)
    await cache.clear()

    assert cache.size == 0
    assert await cache.get("a") is None
    assert await cache.get("b") is None


@pytest.mark.asyncio
async def test_cache_supports_concurrent_reads_and_writes():
    cache = AggregationCache(ttl_seconds=300, max_keys=4)

    async def writer(i: int) -> None:
        await cache.set(f"key-{i}", i)
        await cache.get(f"key-{i}")

    await asyncio.gather(*(writer(i) for i in range(20)))

    assert 0 < cache.size <= 10
    # The most recent keys must have survived eviction.
    assert await cache.get("key-19") == 19


def test_uf_cache_key_normalizes_and_is_order_insensitive():
    assert uf_cache_key(" pb ") == ("PB",)
    assert uf_cache_key(["pb", " PE ", "pb"]) == ("PB", "PE")
    assert uf_cache_key(["PE", "PB"]) == ("PB", "PE")  # same tuple as above
    assert uf_cache_key(None) is None
    assert uf_cache_key([]) is None
    assert uf_cache_key(["", " "]) is None
