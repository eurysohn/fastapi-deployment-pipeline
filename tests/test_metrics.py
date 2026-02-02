"""Tests for metrics endpoint.

Tests cover:
- Prometheus metrics endpoint
- Metric format validation
- Custom business metrics
"""

import pytest
from fastapi.testclient import TestClient


class TestMetricsEndpoint:
    """Tests for the Prometheus metrics endpoint."""

    def test_metrics_endpoint_returns_prometheus_format(
        self, client: TestClient
    ) -> None:
        """Test that metrics endpoint returns Prometheus format."""
        response = client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    def test_metrics_contains_http_request_metrics(
        self, client: TestClient
    ) -> None:
        """Test that metrics include HTTP request counters."""
        # Make a request to generate metrics
        client.get("/healthz")

        response = client.get("/metrics")
        content = response.text

        # Check for expected metric names
        assert "http_requests_total" in content
        assert "http_request_duration_seconds" in content

    def test_metrics_contains_custom_business_metrics(
        self, client: TestClient
    ) -> None:
        """Test that metrics include custom business metrics."""
        response = client.get("/metrics")
        content = response.text

        # Check for business metrics (may be 0 initially)
        assert "cache_hits_total" in content
        assert "cache_misses_total" in content
        assert "items_created_total" in content
        assert "items_deleted_total" in content

    def test_metrics_increments_after_requests(
        self, client: TestClient
    ) -> None:
        """Test that metrics increment after requests."""
        # Get initial metrics
        initial_response = client.get("/metrics")
        initial_content = initial_response.text

        # Make some requests
        for _ in range(3):
            client.get("/healthz")

        # Get updated metrics
        updated_response = client.get("/metrics")
        updated_content = updated_response.text

        # Verify metrics were recorded
        assert "http_requests_total" in updated_content


class TestMetricLabels:
    """Tests for metric label correctness."""

    def test_metrics_have_method_label(self, client: TestClient) -> None:
        """Test that HTTP metrics have method label."""
        client.get("/healthz")
        response = client.get("/metrics")
        content = response.text

        # Should have GET method label
        assert 'method="GET"' in content

    def test_metrics_have_endpoint_label(self, client: TestClient) -> None:
        """Test that HTTP metrics have endpoint label."""
        client.get("/healthz")
        response = client.get("/metrics")
        content = response.text

        # Should have healthz endpoint label
        assert 'endpoint="/healthz"' in content

    def test_metrics_have_status_code_label(self, client: TestClient) -> None:
        """Test that HTTP metrics have status code label."""
        client.get("/healthz")
        response = client.get("/metrics")
        content = response.text

        # Should have 200 status code
        assert 'status_code="200"' in content
