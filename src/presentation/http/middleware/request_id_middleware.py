"""
Middleware that injects a unique request ID into each request's logging context.

This enables log correlation across distributed traces and simplifies debugging
by grouping all log entries generated during a single request under a common ID.

Usage:
    app.add_middleware(RequestIDMiddleware)

The middleware adds the `request_id` to the request state, logs it on every
request/response, and makes it available via `request.state.request_id`.
"""

import logging
import uuid
from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns a unique request ID to every incoming request."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        logger.info(
            "request_start | method=%s | path=%s | request_id=%s",
            request.method,
            request.url.path,
            request_id,
        )

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request_exception | method=%s | path=%s | request_id=%s",
                request.method,
                request.url.path,
                request_id,
            )
            raise

        logger.info(
            "request_end | method=%s | path=%s | status=%d | request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            request_id,
        )

        response.headers["X-Request-ID"] = request_id
        return response
