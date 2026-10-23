import asyncio
import io
import os
import subprocess
import sys
import threading

import httpx
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import ResponseValidationError
from pydantic import BaseModel, Field

from src.infrastructure.cache.byte_cache import ByteCache
from src.infrastructure.resources import CapacityGate, PDFRenderer
from src.presentation.http.large_json import LargeJSONService
from src.presentation.http.middleware.global_exception_handler import (
    register_global_exception_handlers,
)
from src.presentation.http.owned_stream import OwnedStreamResponse


class Item(BaseModel):
    id: int
    name: str = Field(default="Nordeste", serialization_alias="nome")


async def numbers():
    for i in range(3):
        yield {"id": str(i), "ignored": "not public"}


def test_byte_cache_limits_lru_expiry_and_oversized_entries():
    now = [0.0]
    cache = ByteCache(max_bytes=6, max_entry_bytes=4, max_keys=2, now_fn=lambda: now[0])
    cache.set("a", b"123", 60)
    cache.set("b", b"456", 60)
    assert cache.get("a") == b"123"
    cache.set("c", b"789", 1)
    assert cache.get("b") is None
    cache.set("large", b"12345", 60)
    assert cache.get("large") is None
    assert cache.bytes_used == 6
    now[0] = 2
    assert cache.get("c") is None
    assert cache.bytes_used == 3
    cache.clear()
    assert cache.bytes_used == 0


@pytest.mark.asyncio
async def test_complete_validated_json_and_oversized_response_not_cached():
    service = LargeJSONService(cache=ByteCache(max_entry_bytes=1))
    app = FastAPI()
    paths = []

    @app.get("/")
    async def endpoint():
        response = await service.response("key", numbers, Item, collection=False)
        paths.append(response.path)
        return response

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url="http://test"
        ) as client:
            result = await client.get("/")
        assert result.json() == [{"id": i, "nome": "Nordeste"} for i in range(3)]
        assert result.headers["content-type"] == "application/json"
        assert not os.path.exists(paths[0])
        assert service.cache.bytes_used == 0
        assert service.flights == {}
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_failure_before_headers_closes_generator_and_removes_file(
    monkeypatch, tmp_path
):
    import src.presentation.http.large_json as module

    monkeypatch.setattr(module.tempfile, "tempdir", str(tmp_path))
    closed = asyncio.Event()

    async def broken():
        try:
            yield {"id": 1}
            yield {"id": "invalid"}
        finally:
            closed.set()

    service = LargeJSONService()
    with pytest.raises(ResponseValidationError):
        await service.response("key", broken, Item)
    assert closed.is_set()
    assert list(tmp_path.iterdir()) == []
    assert service.flights == {}
    assert service.cache.bytes_used == 0


@pytest.mark.asyncio
async def test_duplicate_requests_share_large_file_until_last_reader():
    entered = asyncio.Event()
    resume = asyncio.Event()
    calls = 0

    async def source():
        nonlocal calls
        calls += 1
        entered.set()
        await resume.wait()
        yield {"id": 1}

    service = LargeJSONService(cache=ByteCache(max_entry_bytes=0))
    first = asyncio.create_task(service.response("key", source, Item))
    await entered.wait()
    second = asyncio.create_task(service.response("key", source, Item))
    await asyncio.sleep(0)
    resume.set()
    a, b = await asyncio.gather(first, second)
    assert calls == 1
    assert a.path == b.path
    a._release()
    assert os.path.exists(b.path)
    b._release()
    assert not os.path.exists(b.path)
    await service.close()


@pytest.mark.asyncio
async def test_cancel_one_waiter_does_not_cancel_shared_generation():
    entered = asyncio.Event()
    resume = asyncio.Event()

    async def source():
        entered.set()
        await resume.wait()
        yield {"id": 1}

    service = LargeJSONService()
    a = asyncio.create_task(service.response("key", source, Item))
    await entered.wait()
    b = asyncio.create_task(service.response("key", source, Item))
    await asyncio.sleep(0)
    a.cancel()
    with pytest.raises(asyncio.CancelledError):
        await a
    resume.set()
    response = await b
    response._release()
    assert not service.flights
    await service.close()


@pytest.mark.asyncio
async def test_last_cancelled_waiter_cleans_partial_file(monkeypatch, tmp_path):
    import src.presentation.http.large_json as module

    monkeypatch.setattr(module.tempfile, "tempdir", str(tmp_path))
    entered = asyncio.Event()
    closed = asyncio.Event()

    async def source():
        try:
            yield {"id": 1}
            entered.set()
            await asyncio.Event().wait()
        finally:
            closed.set()

    service = LargeJSONService()
    request = asyncio.create_task(service.response("key", source, Item))
    await entered.wait()
    request.cancel()
    with pytest.raises(asyncio.CancelledError):
        await request
    await asyncio.wait_for(closed.wait(), 1)
    assert list(tmp_path.iterdir()) == []
    await service.close()


@pytest.mark.asyncio
async def test_disconnect_during_send_releases_artifact():
    service = LargeJSONService()
    response = await service.response("key", numbers, Item)

    async def send(message):
        if message["type"] == "http.response.body":
            raise ConnectionError("client gone")

    with pytest.raises(ConnectionError):
        await response({"type": "http", "method": "GET", "headers": []}, None, send)
    assert not os.path.exists(response.path)
    assert not service.flights
    await service.close()


@pytest.mark.asyncio
async def test_gate_burst_queue_timeout_and_recovery():
    gate = CapacityGate(limit=1, max_waiters=1, timeout=0.02)
    async with gate.slot():

        async def wait():
            async with gate.slot():
                pass

        pending = asyncio.create_task(wait())
        while not gate.waiting:
            await asyncio.sleep(0)
        with pytest.raises(HTTPException) as rejected:
            async with gate.slot():
                pass
        assert rejected.value.status_code == 503
        assert rejected.value.headers["Retry-After"] == "10"
        with pytest.raises(HTTPException):
            await pending
        assert gate.waiting == 0
    async with gate.slot():
        assert gate.active == 1
    assert gate.active == 0


@pytest.mark.asyncio
async def test_pdf_thread_keeps_slot_until_cancelled_render_really_finishes():
    renderer = PDFRenderer()
    entered = threading.Event()
    resume = threading.Event()
    buffer = io.BytesIO(b"pdf")

    def render():
        entered.set()
        resume.wait(2)
        return buffer

    task = asyncio.create_task(renderer.run(render))
    try:
        while not entered.is_set():
            await asyncio.sleep(0.001)
        task.cancel()
        await asyncio.sleep(0.01)
        assert renderer.gate.active == 1
        assert not task.done()
        # A lightweight coroutine still runs while the PDF thread is blocked.
        assert (
            await asyncio.wait_for(asyncio.sleep(0, result="healthy"), 0.1) == "healthy"
        )
        resume.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert renderer.gate.active == 0
        assert buffer.closed
    finally:
        resume.set()
        renderer.close()


def test_startup_does_not_import_plotting_or_reportlab():
    environment = {
        **os.environ,
        "MONGO_URI": "mongodb://localhost:27017",
        "DATABASE_NAME": "odin_test",
    }
    result = subprocess.run(  # noqa: S603 - fixed local interpreter and constant source
        [
            sys.executable,
            "-c",
            "import src.main, sys; assert 'matplotlib.pyplot' not in sys.modules; assert 'reportlab' not in sys.modules",
        ],
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.asyncio
async def test_capacity_http_error_keeps_retry_after_header():
    app = FastAPI()
    register_global_exception_handlers(app)

    @app.get("/")
    async def endpoint():
        raise CapacityGate.unavailable()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        response = await client.get("/")
    assert response.status_code == 503
    assert response.headers["retry-after"] == "10"


@pytest.mark.asyncio
async def test_flight_registry_is_bounded_even_for_completed_slow_readers(monkeypatch):
    from src.infrastructure.database.config.app_config import config

    monkeypatch.setattr(config, "response_max_flights", 1)
    service = LargeJSONService(cache=ByteCache(max_entry_bytes=0))
    first = await service.response("a", numbers, Item)
    try:
        with pytest.raises(HTTPException):
            await service.response("b", numbers, Item)
        assert len(service.flights) == 1
    finally:
        first._release()
        await service.close()


@pytest.mark.asyncio
async def test_pdf_admission_happens_before_database_work():
    renderer = PDFRenderer()
    renderer.gate = CapacityGate(limit=1, max_waiters=0)
    called = False

    async def prepare():
        nonlocal called
        called = True
        return "data"

    try:
        async with renderer.gate.slot():
            with pytest.raises(HTTPException):
                await renderer.run(lambda data: data, prepare=prepare)
        assert not called
    finally:
        renderer.close()


@pytest.mark.asyncio
async def test_gzip_keeps_streamed_json_complete_and_removes_artifact():
    from starlette.middleware.gzip import GZipMiddleware

    service = LargeJSONService()
    app = FastAPI()
    app.add_middleware(GZipMiddleware, minimum_size=1, compresslevel=3)

    @app.get("/")
    async def endpoint():
        return await service.response("gzip", numbers, Item, collection=False)

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url="http://test"
        ) as client:
            response = await client.get("/", headers={"Accept-Encoding": "gzip"})
        assert response.headers["content-encoding"] == "gzip"
        assert response.json() == [{"id": i, "nome": "Nordeste"} for i in range(3)]
        assert not service.flights
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_pdf_response_closes_buffer_after_disconnect():
    stream = io.BytesIO(b"%PDF-" * 20000)
    response = OwnedStreamResponse(stream, media_type="application/pdf")

    async def receive():
        return {"type": "http.disconnect"}

    async def send(message):
        await asyncio.sleep(0)

    await response({"type": "http", "method": "GET"}, receive, send)
    assert stream.closed
