"""FastAPI application entry point.

Production-ready FastAPI application with:
- Lifespan management for startup/shutdown
- Middleware for request tracking
- Health and metrics endpoints
- CORS and security headers
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app import __version__
from app.api import health, metrics
from app.api.metrics import MetricsMiddleware
from app.api.v1 import items
from app.core.config import settings
from app.core.logging import setup_logging
from app.middleware.request_id import RequestIDMiddleware
from app.services.cache import close_cache, init_cache

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events."""
    # Startup
    setup_logging()
    logger.info(
        f"Starting {settings.app_name} v{__version__}",
        extra={"environment": settings.environment},
    )

    # Initialize services
    try:
        await init_cache()
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.warning(f"Cache initialization failed (continuing without cache): {e}")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_cache()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Production-ready FastAPI deployment pipeline demonstrating DevOps best practices",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Add middleware (order matters - first added is outermost)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(MetricsMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(metrics.router, tags=["Metrics"])
    app.include_router(items.router, prefix="/api/v1", tags=["Items"])

    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {
            "service": settings.app_name,
            "version": __version__,
            "environment": settings.environment,
            "docs": "/docs" if settings.is_development else "disabled",
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        workers=settings.workers if not settings.is_development else 1,
        log_level=settings.log_level.lower(),
    )
