"""Health check endpoints for Kubernetes probes.

Implements standard Kubernetes health check patterns:
- /healthz (liveness): Is the application running?
- /readyz (readiness): Is the application ready to receive traffic?

These endpoints are critical for:
- Container orchestration (K8s liveness/readiness probes)
- Load balancer health checks
- Service mesh health monitoring
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict

from fastapi import APIRouter, Response, status

from app.services.cache import get_cache_service

router = APIRouter()
logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


@router.get(
    "/healthz",
    summary="Liveness probe",
    description="Returns 200 if the application is running. Used by Kubernetes liveness probe.",
    response_model=Dict[str, str],
    responses={
        200: {"description": "Application is alive"},
        503: {"description": "Application is not responding"},
    },
)
async def liveness() -> Dict[str, str]:
    """
    Liveness probe endpoint.

    This endpoint should return quickly and only fail if the application
    is in an unrecoverable state (e.g., deadlock, memory corruption).

    Kubernetes will restart the container if this probe fails.
    """
    return {"status": HealthStatus.HEALTHY}


@router.get(
    "/readyz",
    summary="Readiness probe",
    description="Returns 200 if the application is ready to receive traffic.",
    responses={
        200: {"description": "Application is ready to receive traffic"},
        503: {"description": "Application is not ready"},
    },
)
async def readiness(response: Response) -> Dict[str, Any]:
    """
    Readiness probe endpoint.

    Checks all dependencies (Redis, databases, etc.) to determine
    if the application can handle requests.

    Kubernetes will stop routing traffic if this probe fails.
    """
    checks: Dict[str, Dict[str, Any]] = {}
    overall_healthy = True

    # Check Redis
    try:
        cache = await get_cache_service()
        redis_healthy = await cache.health_check()
        checks["redis"] = {
            "status": HealthStatus.HEALTHY if redis_healthy else HealthStatus.UNHEALTHY,
            "required": False,  # App can function without cache
        }
        if not redis_healthy:
            logger.warning("Redis health check failed")
    except Exception as e:
        checks["redis"] = {
            "status": HealthStatus.UNHEALTHY,
            "error": str(e),
            "required": False,
        }
        logger.warning(f"Redis health check error: {e}")

    # Determine overall status
    # Only fail readiness for required dependencies
    required_unhealthy = any(
        check.get("required", False) and check["status"] == HealthStatus.UNHEALTHY
        for check in checks.values()
    )

    if required_unhealthy:
        overall_healthy = False
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    # Check if any non-required services are unhealthy (degraded state)
    any_unhealthy = any(
        check["status"] == HealthStatus.UNHEALTHY for check in checks.values()
    )

    return {
        "status": (
            HealthStatus.UNHEALTHY
            if not overall_healthy
            else HealthStatus.DEGRADED
            if any_unhealthy
            else HealthStatus.HEALTHY
        ),
        "checks": checks,
    }


@router.get(
    "/health",
    summary="Detailed health check",
    description="Returns detailed health information about all components.",
    responses={
        200: {"description": "Health check completed"},
    },
)
async def health_detailed(response: Response) -> Dict[str, Any]:
    """
    Detailed health check with component information.

    Useful for debugging and monitoring dashboards.
    """
    from app import __version__
    from app.core.config import settings

    readiness_result = await readiness(response)

    return {
        "service": settings.app_name,
        "version": __version__,
        "environment": settings.environment,
        **readiness_result,
    }
