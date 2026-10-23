"""ASGI request metrics measured through the final response body."""

import logging
import time
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


def container_memory_bytes():
    # cgroup v2 / v1 account for master, worker and filesystem page cache.
    for path in (
        "/sys/fs/cgroup/memory.current",
        "/sys/fs/cgroup/memory/memory.usage_in_bytes",
    ):
        try:
            return int(Path(path).read_text().strip())
        except (OSError, ValueError):
            continue
    return None


class RequestIDMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request_id = str(uuid.uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        started = time.monotonic()
        status = 500
        size = 0
        headers_at = None

        async def measured_send(message):
            nonlocal status, size, headers_at
            if message["type"] == "http.response.start":
                status = message["status"]
                headers_at = time.monotonic()
                message = {
                    **message,
                    "headers": [
                        *message.get("headers", []),
                        (b"x-request-id", request_id.encode("ascii")),
                    ],
                }
            elif message["type"] == "http.response.body":
                size += len(message.get("body", b""))
            await send(message)

        try:
            await self.app(scope, receive, measured_send)
        except Exception:
            logger.exception("request_exception request_id=%s", request_id)
            raise
        finally:
            route = scope.get("route")
            logger.info(
                "request_end method=%s route=%s status=%s bytes=%s duration_ms=%.1f headers_ms=%s memory_bytes=%s request_id=%s",
                scope["method"],
                getattr(route, "path", scope["path"]),
                status,
                size,
                (time.monotonic() - started) * 1000,
                round((headers_at - started) * 1000, 1) if headers_at else None,
                container_memory_bytes(),
                request_id,
            )
