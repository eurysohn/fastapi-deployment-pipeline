"""Pytest configuration and fixtures.

Provides shared test fixtures for:
- FastAPI test client
- Mock Redis service
- Test data factories
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.cache import CacheService


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_cache_service() -> MagicMock:
    """Create a mock cache service."""
    mock = MagicMock(spec=CacheService)
    mock.health_check = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=False)
    return mock


@pytest.fixture
def client(mock_cache_service: MagicMock) -> Generator[TestClient, None, None]:
    """Create a test client with mocked dependencies."""
    with patch(
        "app.services.cache.get_cache_service",
        return_value=mock_cache_service,
    ):
        with patch("app.services.cache.init_cache", new_callable=AsyncMock):
            with patch("app.services.cache.close_cache", new_callable=AsyncMock):
                with TestClient(app) as test_client:
                    yield test_client


@pytest.fixture
async def async_client(
    mock_cache_service: MagicMock,
) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    with patch(
        "app.services.cache.get_cache_service",
        return_value=mock_cache_service,
    ):
        with patch("app.services.cache.init_cache", new_callable=AsyncMock):
            with patch("app.services.cache.close_cache", new_callable=AsyncMock):
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as ac:
                    yield ac


@pytest.fixture
def sample_item() -> dict[str, Any]:
    """Create a sample item for testing."""
    return {
        "name": "Test Item",
        "description": "A test item description",
        "price": 29.99,
        "quantity": 100,
        "tags": ["test", "sample"],
    }


@pytest.fixture
def sample_item_minimal() -> dict[str, Any]:
    """Create a minimal sample item (only required fields)."""
    return {
        "name": "Minimal Item",
        "price": 9.99,
    }
