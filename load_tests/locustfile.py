"""
Load Testing with Locust
=========================

This module defines load test scenarios for the FastAPI application.

Test Scenarios:
    1. Smoke Test: Verify basic functionality under minimal load
    2. Load Test: Test normal expected load
    3. Stress Test: Push system beyond normal capacity
    4. Spike Test: Sudden burst of traffic
    5. Soak Test: Extended duration test for memory leaks

Usage:
    # Run with web UI
    locust -f load_tests/locustfile.py --host=http://localhost:8000

    # Run headless
    locust -f load_tests/locustfile.py --host=http://localhost:8000 \
           --headless -u 100 -r 10 -t 5m

    # Run specific scenario
    locust -f load_tests/locustfile.py --host=http://localhost:8000 \
           --tags smoke --headless -u 10 -r 2 -t 1m
"""

import json
import random
import string
from typing import Any

from locust import HttpUser, between, events, tag, task


def generate_random_string(length: int = 10) -> str:
    """Generate a random string for test data."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_item_data() -> dict[str, Any]:
    """Generate random item data for POST requests."""
    return {
        "name": f"Test Item {generate_random_string(5)}",
        "description": f"Load test item - {generate_random_string(20)}",
        "price": round(random.uniform(1.0, 1000.0), 2),
        "quantity": random.randint(0, 1000),
        "tags": [generate_random_string(5) for _ in range(random.randint(1, 5))],
    }


class FastAPIUser(HttpUser):
    """
    Simulates a typical user interacting with the FastAPI application.

    Behavior:
        - Checks health endpoints periodically
        - Creates, reads, updates, and deletes items
        - Weighted towards read operations (realistic traffic pattern)
    """

    # Wait time between tasks (simulates user think time)
    wait_time = between(1, 3)

    # Store created item IDs for later operations
    created_items: list[str] = []

    def on_start(self) -> None:
        """Called when a user starts - verify API is available."""
        response = self.client.get("/healthz")
        if response.status_code != 200:
            raise Exception("API health check failed")

    # -------------------------------------------------------------------------
    # Health Check Tasks
    # -------------------------------------------------------------------------

    @tag("smoke", "health")
    @task(1)
    def check_liveness(self) -> None:
        """Check the liveness probe endpoint."""
        with self.client.get("/healthz", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Liveness check failed: {response.status_code}")

    @tag("smoke", "health")
    @task(1)
    def check_readiness(self) -> None:
        """Check the readiness probe endpoint."""
        with self.client.get("/readyz", catch_response=True) as response:
            if response.status_code in [200, 503]:  # 503 is valid for degraded state
                response.success()
            else:
                response.failure(f"Readiness check failed: {response.status_code}")

    # -------------------------------------------------------------------------
    # Metrics Task
    # -------------------------------------------------------------------------

    @tag("smoke", "metrics")
    @task(1)
    def get_metrics(self) -> None:
        """Fetch Prometheus metrics."""
        self.client.get("/metrics")

    # -------------------------------------------------------------------------
    # Items CRUD Tasks
    # -------------------------------------------------------------------------

    @tag("load", "items", "create")
    @task(2)
    def create_item(self) -> None:
        """Create a new item."""
        item_data = generate_item_data()

        with self.client.post(
            "/api/v1/items",
            json=item_data,
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                item_id = response.json().get("id")
                if item_id:
                    # Store for later operations (limit to prevent memory issues)
                    if len(self.created_items) < 100:
                        self.created_items.append(item_id)
                response.success()
            else:
                response.failure(f"Create failed: {response.status_code}")

    @tag("load", "items", "read")
    @task(10)  # Higher weight - reads are more common
    def list_items(self) -> None:
        """List items with pagination."""
        page = random.randint(1, 5)
        page_size = random.choice([10, 20, 50])

        self.client.get(f"/api/v1/items?page={page}&page_size={page_size}")

    @tag("load", "items", "read")
    @task(5)
    def get_item(self) -> None:
        """Get a specific item by ID."""
        if self.created_items:
            item_id = random.choice(self.created_items)
            with self.client.get(
                f"/api/v1/items/{item_id}",
                catch_response=True,
            ) as response:
                if response.status_code in [200, 404]:  # 404 is valid if item was deleted
                    response.success()
                else:
                    response.failure(f"Get item failed: {response.status_code}")

    @tag("load", "items", "update")
    @task(2)
    def update_item(self) -> None:
        """Update an existing item."""
        if self.created_items:
            item_id = random.choice(self.created_items)
            update_data = {
                "name": f"Updated Item {generate_random_string(5)}",
                "price": round(random.uniform(1.0, 1000.0), 2),
            }

            with self.client.put(
                f"/api/v1/items/{item_id}",
                json=update_data,
                catch_response=True,
            ) as response:
                if response.status_code in [200, 404]:
                    response.success()
                else:
                    response.failure(f"Update failed: {response.status_code}")

    @tag("load", "items", "delete")
    @task(1)  # Lower weight - deletes are less common
    def delete_item(self) -> None:
        """Delete an existing item."""
        if self.created_items:
            item_id = self.created_items.pop(0)  # Remove from our list

            with self.client.delete(
                f"/api/v1/items/{item_id}",
                catch_response=True,
            ) as response:
                if response.status_code in [204, 404]:
                    response.success()
                else:
                    response.failure(f"Delete failed: {response.status_code}")


class StressTestUser(FastAPIUser):
    """
    Aggressive user for stress testing.

    Characteristics:
        - No wait time between requests
        - Heavy on write operations
        - Tests system limits
    """

    wait_time = between(0.1, 0.5)

    @tag("stress", "burst")
    @task(5)
    def burst_create(self) -> None:
        """Rapidly create items to stress the system."""
        for _ in range(5):
            self.create_item()

    @tag("stress", "burst")
    @task(3)
    def burst_read(self) -> None:
        """Rapid concurrent reads."""
        for _ in range(10):
            self.list_items()


class SpikeTestUser(FastAPIUser):
    """
    User for spike testing - sudden bursts of traffic.
    """

    wait_time = between(0.1, 0.3)

    @tag("spike")
    @task
    def spike_traffic(self) -> None:
        """Generate spike traffic pattern."""
        # Random burst of requests
        burst_size = random.randint(5, 20)
        for _ in range(burst_size):
            self.client.get("/healthz")
            self.list_items()


# =============================================================================
# Event Hooks for Custom Reporting
# =============================================================================


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("=" * 60)
    print("Load Test Starting")
    print(f"Target Host: {environment.host}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    print("=" * 60)
    print("Load Test Complete")
    print("=" * 60)

    # Print summary statistics
    stats = environment.stats
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Average Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min Response Time: {stats.total.min_response_time:.2f}ms")
    print(f"Max Response Time: {stats.total.max_response_time:.2f}ms")

    if stats.total.num_requests > 0:
        error_rate = (stats.total.num_failures / stats.total.num_requests) * 100
        print(f"Error Rate: {error_rate:.2f}%")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Called on each request - can be used for custom metrics."""
    # Could send to external monitoring here
    pass
