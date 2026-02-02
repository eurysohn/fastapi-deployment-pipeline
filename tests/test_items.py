"""Tests for items CRUD API.

Tests cover:
- Create, Read, Update, Delete operations
- Input validation
- Error handling
- Pagination
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient


class TestCreateItem:
    """Tests for item creation."""

    def test_create_item_success(
        self, client: TestClient, sample_item: dict[str, Any]
    ) -> None:
        """Test successful item creation."""
        response = client.post("/api/v1/items", json=sample_item)

        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["name"] == sample_item["name"]
        assert data["description"] == sample_item["description"]
        assert data["price"] == sample_item["price"]
        assert data["quantity"] == sample_item["quantity"]
        assert data["tags"] == sample_item["tags"]
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_item_minimal(
        self, client: TestClient, sample_item_minimal: dict[str, Any]
    ) -> None:
        """Test item creation with minimal required fields."""
        response = client.post("/api/v1/items", json=sample_item_minimal)

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == sample_item_minimal["name"]
        assert data["price"] == sample_item_minimal["price"]
        assert data["description"] is None
        assert data["quantity"] == 0
        assert data["tags"] == []

    def test_create_item_invalid_price(self, client: TestClient) -> None:
        """Test item creation with invalid price."""
        response = client.post(
            "/api/v1/items",
            json={"name": "Invalid", "price": -10},
        )

        assert response.status_code == 422
        assert "price" in response.text.lower()

    def test_create_item_missing_required_field(self, client: TestClient) -> None:
        """Test item creation with missing required field."""
        response = client.post(
            "/api/v1/items",
            json={"description": "Missing name and price"},
        )

        assert response.status_code == 422

    def test_create_item_name_too_long(self, client: TestClient) -> None:
        """Test item creation with name exceeding max length."""
        response = client.post(
            "/api/v1/items",
            json={"name": "x" * 101, "price": 10},
        )

        assert response.status_code == 422


class TestGetItem:
    """Tests for getting items."""

    def test_get_item_success(
        self, client: TestClient, sample_item: dict[str, Any]
    ) -> None:
        """Test getting an existing item."""
        # Create item first
        create_response = client.post("/api/v1/items", json=sample_item)
        item_id = create_response.json()["id"]

        # Get the item
        response = client.get(f"/api/v1/items/{item_id}")

        assert response.status_code == 200
        assert response.json()["id"] == item_id

    def test_get_item_not_found(self, client: TestClient) -> None:
        """Test getting a non-existent item."""
        response = client.get("/api/v1/items/nonexistent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestListItems:
    """Tests for listing items."""

    def test_list_items_empty(self, client: TestClient) -> None:
        """Test listing items when none exist."""
        response = client.get("/api/v1/items")

        assert response.status_code == 200
        data = response.json()

        assert data["items"] == [] or isinstance(data["items"], list)
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

    def test_list_items_pagination(
        self, client: TestClient, sample_item: dict[str, Any]
    ) -> None:
        """Test item list pagination."""
        # Create multiple items
        for i in range(5):
            item = {**sample_item, "name": f"Item {i}"}
            client.post("/api/v1/items", json=item)

        # Test first page
        response = client.get("/api/v1/items?page=1&page_size=2")
        data = response.json()

        assert response.status_code == 200
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    def test_list_items_invalid_page(self, client: TestClient) -> None:
        """Test invalid page number."""
        response = client.get("/api/v1/items?page=0")

        assert response.status_code == 422

    def test_list_items_page_size_limit(self, client: TestClient) -> None:
        """Test page size limit enforcement."""
        response = client.get("/api/v1/items?page_size=101")

        assert response.status_code == 422


class TestUpdateItem:
    """Tests for updating items."""

    def test_update_item_success(
        self, client: TestClient, sample_item: dict[str, Any]
    ) -> None:
        """Test successful item update."""
        # Create item
        create_response = client.post("/api/v1/items", json=sample_item)
        item_id = create_response.json()["id"]

        # Update item
        update_data = {"name": "Updated Name", "price": 99.99}
        response = client.put(f"/api/v1/items/{item_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Updated Name"
        assert data["price"] == 99.99
        # Original fields should remain
        assert data["description"] == sample_item["description"]

    def test_update_item_partial(
        self, client: TestClient, sample_item: dict[str, Any]
    ) -> None:
        """Test partial update (only some fields)."""
        # Create item
        create_response = client.post("/api/v1/items", json=sample_item)
        item_id = create_response.json()["id"]
        original_price = create_response.json()["price"]

        # Update only name
        response = client.put(
            f"/api/v1/items/{item_id}",
            json={"name": "Only Name Updated"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Only Name Updated"
        assert data["price"] == original_price

    def test_update_item_not_found(self, client: TestClient) -> None:
        """Test updating a non-existent item."""
        response = client.put(
            "/api/v1/items/nonexistent-id",
            json={"name": "Update"},
        )

        assert response.status_code == 404


class TestDeleteItem:
    """Tests for deleting items."""

    def test_delete_item_success(
        self, client: TestClient, sample_item: dict[str, Any]
    ) -> None:
        """Test successful item deletion."""
        # Create item
        create_response = client.post("/api/v1/items", json=sample_item)
        item_id = create_response.json()["id"]

        # Delete item
        response = client.delete(f"/api/v1/items/{item_id}")

        assert response.status_code == 204

        # Verify item is gone
        get_response = client.get(f"/api/v1/items/{item_id}")
        assert get_response.status_code == 404

    def test_delete_item_not_found(self, client: TestClient) -> None:
        """Test deleting a non-existent item."""
        response = client.delete("/api/v1/items/nonexistent-id")

        assert response.status_code == 404

    def test_delete_item_idempotent(
        self, client: TestClient, sample_item: dict[str, Any]
    ) -> None:
        """Test that deleting twice returns 404 on second attempt."""
        # Create and delete item
        create_response = client.post("/api/v1/items", json=sample_item)
        item_id = create_response.json()["id"]
        client.delete(f"/api/v1/items/{item_id}")

        # Try to delete again
        response = client.delete(f"/api/v1/items/{item_id}")

        assert response.status_code == 404
