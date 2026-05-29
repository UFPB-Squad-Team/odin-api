"""
Health check endpoints for load balancers and container orchestration.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.infrastructure.database.config.connect_db import mongodb

router = APIRouter(tags=["health"])


@router.get("/health", include_in_schema=False)
async def health_check() -> JSONResponse:
    """
    Liveness probe — indicates the process is running.
    Used by Docker HEALTHCHECK and load balancers.
    """
    return JSONResponse(
        status_code=200,
        content={"status": "healthy"},
    )


@router.get("/health/ready")
async def readiness_check() -> JSONResponse:
    """
    Readiness probe — indicates the service can handle traffic.
    Checks database connectivity.
    """
    checks = {
        "database": mongodb.is_connected,
    }

    all_healthy = all(checks.values())

    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "checks": {k: "ok" if v else "failing" for k, v in checks.items()},
        },
    )
