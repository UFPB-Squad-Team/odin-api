"""Validate complete JSON on disk before headers; share bounded in-flight work.

Temporary files are owned by a flight until its last response (or cancelled
waiter) releases it. Each FileResponse opens a separate reader.
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from typing import Any

from fastapi.exceptions import ResponseValidationError
from pydantic import TypeAdapter, ValidationError
from starlette.responses import FileResponse, Response
from starlette.types import Receive, Scope, Send

from src.infrastructure.cache.byte_cache import ByteCache
from src.infrastructure.database.config.app_config import config
from src.infrastructure.database.repository.cursor import CursorMetrics, cursor_metrics
from src.infrastructure.resources import CapacityGate

logger = logging.getLogger(__name__)


@dataclass
class Artifact:
    path: str
    size: int


@dataclass
class Flight:
    task: asyncio.Task[Artifact]
    users: int = 0


class ArtifactResponse(FileResponse):
    def __init__(self, artifact: Artifact, release: Callable[[], None]) -> None:
        super().__init__(artifact.path, media_type="application/json")
        self._release = release

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await super().__call__(scope, receive, send)
        finally:
            self._release()


class LargeJSONService:
    def __init__(
        self, cache: ByteCache | None = None, gate: CapacityGate | None = None
    ) -> None:
        self.cache = (
            cache
            if cache is not None
            else ByteCache(
                max_bytes=config.response_cache_max_bytes,
                max_entry_bytes=config.response_cache_max_entry_bytes,
                max_keys=config.aggregation_cache_max_keys,
            )
        )
        self.gate = gate or CapacityGate(limit=config.geo_concurrency)
        self.flights: dict[str, Flight] = {}

    async def response(
        self,
        key: str,
        items: Callable[[], AsyncGenerator[Any, None]],
        schema: Any,
        *,
        collection: bool = True,
        ttl: float = 300,
    ) -> Response:
        cached = self.cache.get(key)
        if cached is not None:
            logger.info("large_json cache=hit bytes=%s", len(cached))
            return Response(cached, media_type="application/json")
        flight = self.flights.get(key)
        if flight is None:
            if len(self.flights) >= config.response_max_flights:
                raise self.gate.unavailable()
            flight = Flight(
                asyncio.create_task(self._build(key, items, schema, collection, ttl))
            )
            self.flights[key] = flight
        flight.users += 1
        try:
            artifact = await asyncio.shield(flight.task)
        except BaseException:
            self._release(key, flight)
            raise
        return ArtifactResponse(artifact, lambda: self._release(key, flight))

    def _release(self, key: str, flight: Flight) -> None:
        flight.users -= 1
        if flight.users:
            return
        if self.flights.get(key) is flight:
            self.flights.pop(key, None)
        if not flight.task.done():
            flight.task.cancel()
            flight.task.add_done_callback(self._discard)
        else:
            self._discard(flight.task)

    @staticmethod
    def _discard(task: asyncio.Task[Artifact]) -> None:
        if not task.cancelled() and task.exception() is None:
            try:
                os.unlink(task.result().path)
            except FileNotFoundError:
                pass  # Already discarded during graceful shutdown.

    async def _build(
        self,
        key: str,
        items: Callable[[], AsyncGenerator[Any, None]],
        schema: Any,
        collection: bool,
        ttl: float,
    ) -> Artifact:
        async with self.gate.slot():
            started = time.monotonic()
            totals = CursorMetrics()
            token = cursor_metrics.set(totals)
            serialization_seconds = 0.0
            adapter: TypeAdapter[Any] = TypeAdapter(schema)
            path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w+b", prefix="odin-json-", delete=False
                ) as output:
                    path = output.name
                    output.write(
                        b'{"type":"FeatureCollection","features":['
                        if collection
                        else b"["
                    )
                    first = True
                    iterator = items()
                    try:
                        async for item in iterator:
                            serialization_started = time.monotonic()
                            try:
                                value = adapter.validate_python(
                                    item, from_attributes=True
                                )
                            except ValidationError as exc:
                                raise ResponseValidationError(exc.errors()) from exc
                            payload = json.dumps(
                                adapter.dump_python(value, mode="json", by_alias=True),
                                ensure_ascii=False,
                                allow_nan=False,
                                separators=(",", ":"),
                            ).encode("utf-8")
                            if not first:
                                output.write(b",")
                            output.write(payload)
                            first = False
                            serialization_seconds += (
                                time.monotonic() - serialization_started
                            )
                            # Bound CPU/disk work per event-loop turn as well as RAM.
                            await asyncio.sleep(0)
                    finally:
                        await iterator.aclose()
                    output.write(b"]}" if collection else b"]")
                    size = output.tell()
                    if size <= min(self.cache.max_entry_bytes, self.cache.max_bytes):
                        output.seek(0)
                        self.cache.set(key, output.read(), ttl)
                elapsed = time.monotonic() - started
                logger.info(
                    "large_json kind=%s cache=miss bytes=%s documents=%s query_ms=%.1f transform_ms=%.1f serialize_ms=%.1f generation_ms=%.1f active=%s waiting=%s",
                    key.partition(":")[0],
                    size,
                    totals.documents,
                    totals.seconds * 1000,
                    max(0, elapsed - totals.seconds - serialization_seconds) * 1000,
                    serialization_seconds * 1000,
                    elapsed * 1000,
                    self.gate.active,
                    self.gate.waiting,
                )
                return Artifact(path, size)
            except BaseException:
                if path is not None:
                    os.unlink(path)
                raise
            finally:
                cursor_metrics.reset(token)

    async def close(self) -> None:
        flights = list(self.flights.values())
        for flight in flights:
            if not flight.task.done():
                flight.task.cancel()
        await asyncio.gather(
            *(flight.task for flight in flights), return_exceptions=True
        )
        for flight in flights:
            self._discard(flight.task)
        self.flights.clear()
        self.cache.clear()


def response_key(namespace: str, **parameters: Any) -> str:
    return namespace + ":" + json.dumps(parameters, sort_keys=True, ensure_ascii=True)


large_json = LargeJSONService()


async def iter_use_case(
    use_case: Any, *, collection: bool = True, **kwargs: Any
) -> AsyncGenerator[Any, None]:
    if hasattr(use_case, "iter_items"):
        iterator = use_case.iter_items(**kwargs)
        try:
            async for item in iterator:
                yield item
        finally:
            await iterator.aclose()
    else:
        result = await use_case.execute(**kwargs)
        for item in result["features"] if collection else result:
            yield item
