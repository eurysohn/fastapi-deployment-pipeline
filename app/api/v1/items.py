"""Items CRUD API with Redis caching.

Demonstrates production patterns:
- RESTful API design
- Input validation with Pydantic
- Cache-aside pattern with Redis
- Proper error handling
- Pagination support
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.metrics import (
    record_cache_hit,
    record_cache_miss,
    record_item_created,
    record_item_deleted,
)
from app.services.cache import get_cache_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Cache settings
CACHE_PREFIX = "item:"
CACHE_TTL = 3600  # 1 hour
ITEMS_LIST_KEY = "items:list"

# In-memory storage (would be a database in production)
_items_db: dict[str, dict[str, Any]] = {}


# Pydantic models
class ItemCreate(BaseModel):
    """Request model for creating an item."""

    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: str | None = Field(
        None, max_length=500, description="Item description"
    )
    price: float = Field(..., gt=0, description="Item price (must be positive)")
    quantity: int = Field(default=0, ge=0, description="Item quantity in stock")
    tags: list[str] = Field(default_factory=list, description="Item tags")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Widget",
                    "description": "A useful widget",
                    "price": 29.99,
                    "quantity": 100,
                    "tags": ["electronics", "gadgets"],
                }
            ]
        }
    }


class ItemUpdate(BaseModel):
    """Request model for updating an item."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    price: float | None = Field(None, gt=0)
    quantity: int | None = Field(None, ge=0)
    tags: list[str] | None = None


class ItemResponse(BaseModel):
    """Response model for an item."""

    id: str
    name: str
    description: str | None
    price: float
    quantity: int
    tags: list[str]
    created_at: datetime
    updated_at: datetime


class ItemListResponse(BaseModel):
    """Response model for paginated item list."""

    items: list[ItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


def _get_cache_key(item_id: str) -> str:
    """Generate cache key for an item."""
    return f"{CACHE_PREFIX}{item_id}"


async def _get_from_cache(item_id: str) -> dict[str, Any] | None:
    """Get item from cache."""
    cache = await get_cache_service()
    cached = await cache.get(_get_cache_key(item_id))
    if cached:
        record_cache_hit("get_item")
        return cached
    record_cache_miss("get_item")
    return None


async def _set_in_cache(item_id: str, item: dict[str, Any]) -> None:
    """Set item in cache."""
    cache = await get_cache_service()
    await cache.set(_get_cache_key(item_id), item, ttl=CACHE_TTL)


async def _delete_from_cache(item_id: str) -> None:
    """Delete item from cache."""
    cache = await get_cache_service()
    await cache.delete(_get_cache_key(item_id))
    await cache.delete(ITEMS_LIST_KEY)


@router.post(
    "/items",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new item",
)
async def create_item(item: ItemCreate) -> ItemResponse:
    """
    Create a new item.

    - **name**: Item name (required)
    - **description**: Optional description
    - **price**: Item price (must be positive)
    - **quantity**: Stock quantity (default: 0)
    - **tags**: List of tags
    """
    item_id = str(uuid.uuid4())
    now = datetime.utcnow()

    item_data = {
        "id": item_id,
        **item.model_dump(),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    # Store in database
    _items_db[item_id] = item_data

    # Cache the new item
    await _set_in_cache(item_id, item_data)

    # Invalidate list cache
    cache = await get_cache_service()
    await cache.delete(ITEMS_LIST_KEY)

    # Record metric
    record_item_created()

    logger.info(f"Created item: {item_id}", extra={"item_id": item_id})

    return ItemResponse(**item_data)


@router.get(
    "/items",
    response_model=ItemListResponse,
    summary="List all items",
)
async def list_items(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
) -> ItemListResponse:
    """
    List all items with pagination.

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 10, max: 100)
    """
    # Get all items
    all_items = list(_items_db.values())
    total = len(all_items)

    # Calculate pagination
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    start = (page - 1) * page_size
    end = start + page_size

    # Get page items
    page_items = all_items[start:end]

    return ItemListResponse(
        items=[ItemResponse(**item) for item in page_items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="Get an item by ID",
)
async def get_item(item_id: str) -> ItemResponse:
    """
    Get a specific item by ID.

    Uses cache-aside pattern:
    1. Check cache first
    2. If miss, fetch from database and cache
    """
    # Try cache first
    cached = await _get_from_cache(item_id)
    if cached:
        return ItemResponse(**cached)

    # Cache miss - get from database
    if item_id not in _items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )

    item_data = _items_db[item_id]

    # Cache for next time
    await _set_in_cache(item_id, item_data)

    return ItemResponse(**item_data)


@router.put(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="Update an item",
)
async def update_item(item_id: str, item: ItemUpdate) -> ItemResponse:
    """
    Update an existing item.

    Only provided fields will be updated (partial update).
    """
    if item_id not in _items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )

    # Update fields
    item_data = _items_db[item_id]
    update_data = item.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        item_data[field] = value

    item_data["updated_at"] = datetime.utcnow().isoformat()

    # Update database
    _items_db[item_id] = item_data

    # Update cache
    await _set_in_cache(item_id, item_data)

    # Invalidate list cache
    cache = await get_cache_service()
    await cache.delete(ITEMS_LIST_KEY)

    logger.info(f"Updated item: {item_id}", extra={"item_id": item_id})

    return ItemResponse(**item_data)


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an item",
)
async def delete_item(item_id: str) -> None:
    """
    Delete an item by ID.

    Removes from both database and cache.
    """
    if item_id not in _items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )

    # Delete from database
    del _items_db[item_id]

    # Delete from cache
    await _delete_from_cache(item_id)

    # Record metric
    record_item_deleted()

    logger.info(f"Deleted item: {item_id}", extra={"item_id": item_id})
