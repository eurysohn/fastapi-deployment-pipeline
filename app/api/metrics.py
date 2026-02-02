"""Prometheus metrics endpoint and application metrics.

Exposes application metrics in Prometheus format for:
- Request latency histograms
- Request counters by endpoint and status
- Active connections gauge
- Custom business metrics
"""

import logging
import time
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match

logger = logging.getLogger(__name__)

router = APIRouter()

# Define metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
)

# Custom business metrics
CACHE_HITS = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["operation"],
)

CACHE_MISSES = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["operation"],
)

ITEMS_CREATED = Counter(
    "items_created_total",
    "Total items created",
)

ITEMS_DELETED = Counter(
    "items_deleted_total",
    "Total items deleted",
)


def get_path_template(request: Request) -> str:
    """Get the path template for the request (e.g., /api/v1/items/{item_id})."""
    for route in request.app.routes:
        match, _ = route.matches(request.scope)
        if match == Match.FULL:
            return route.path
    return request.url.path


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect request metrics."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Any]
    ) -> Response:
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        path = get_path_template(request)

        # Track in-progress requests
        REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path).inc()

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            # Record metrics
            duration = time.perf_counter() - start_time

            REQUEST_COUNT.labels(
                method=method,
                endpoint=path,
                status_code=status_code,
            ).inc()

            REQUEST_LATENCY.labels(
                method=method,
                endpoint=path,
            ).observe(duration)

            REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path).dec()

        return response


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    description="Exposes application metrics in Prometheus format",
    response_class=Response,
    include_in_schema=False,
)
async def metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus exposition format for scraping.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# Helper functions for recording business metrics
def record_cache_hit(operation: str) -> None:
    """Record a cache hit."""
    CACHE_HITS.labels(operation=operation).inc()


def record_cache_miss(operation: str) -> None:
    """Record a cache miss."""
    CACHE_MISSES.labels(operation=operation).inc()


def record_item_created() -> None:
    """Record an item creation."""
    ITEMS_CREATED.inc()


def record_item_deleted() -> None:
    """Record an item deletion."""
    ITEMS_DELETED.inc()
