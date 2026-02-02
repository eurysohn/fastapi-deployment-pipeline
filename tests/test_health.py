"""Tests for health check endpoints.

Tests cover:
- Liveness probe (/healthz)
- Readiness probe (/readyz)
- Detailed health check (/health)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestLivenessProbe:
    """Tests for the liveness probe endpoint."""

    def test_liveness_returns_healthy(self, client: TestClient) -> None:
        """Test that liveness probe returns healthy status."""
        response = client.get("/healthz")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_liveness_response_time(self, client: TestClient) -> None:
        """Test that liveness probe responds quickly."""
        import time

        start = time.perf_counter()
        response = client.get("/healthz")
        duration = time.perf_counter() - start

        assert response.status_code == 200
        assert duration < 0.1  # Should respond in under 100ms


class TestReadinessProbe:
    """Tests for the readiness probe endpoint."""

    def test_readiness_healthy_when_redis_available(
        self, client: TestClient, mock_cache_service: MagicMock
    ) -> None:
        """Test readiness returns healthy when all dependencies are up."""
        mock_cache_service.health_check = AsyncMock(return_value=True)

        with patch(
            "app.api.health.get_cache_service",
            return_value=mock_cache_service,
        ):
            response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "checks" in data
        assert data["checks"]["redis"]["status"] == "healthy"

    def test_readiness_degraded_when_redis_unavailable(
        self, client: TestClient, mock_cache_service: MagicMock
    ) -> None:
        """Test readiness returns degraded when optional dependencies are down."""
        mock_cache_service.health_check = AsyncMock(return_value=False)

        with patch(
            "app.api.health.get_cache_service",
            return_value=mock_cache_service,
        ):
            response = client.get("/readyz")

        # Should still return 200 since Redis is optional
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["checks"]["redis"]["status"] == "unhealthy"

    def test_readiness_handles_redis_exception(
        self, client: TestClient, mock_cache_service: MagicMock
    ) -> None:
        """Test readiness handles exceptions gracefully."""
        mock_cache_service.health_check = AsyncMock(
            side_effect=Exception("Connection refused")
        )

        with patch(
            "app.api.health.get_cache_service",
            return_value=mock_cache_service,
        ):
            response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()
        assert "error" in data["checks"]["redis"]


class TestDetailedHealthCheck:
    """Tests for the detailed health check endpoint."""

    def test_health_returns_service_info(
        self, client: TestClient, mock_cache_service: MagicMock
    ) -> None:
        """Test that detailed health check includes service information."""
        mock_cache_service.health_check = AsyncMock(return_value=True)

        with patch(
            "app.api.health.get_cache_service",
            return_value=mock_cache_service,
        ):
            response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Check service info
        assert "service" in data
        assert "version" in data
        assert "environment" in data

        # Check health status
        assert "status" in data
        assert "checks" in data

    def test_health_version_matches_app_version(
        self, client: TestClient, mock_cache_service: MagicMock
    ) -> None:
        """Test that health check version matches app version."""
        from app import __version__

        mock_cache_service.health_check = AsyncMock(return_value=True)

        with patch(
            "app.api.health.get_cache_service",
            return_value=mock_cache_service,
        ):
            response = client.get("/health")

        assert response.json()["version"] == __version__
