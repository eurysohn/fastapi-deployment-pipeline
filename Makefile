# =============================================================================
# Makefile - Developer Experience Commands
# =============================================================================
# Run `make help` to see all available commands
# =============================================================================

.PHONY: help install dev test lint format security build run clean docker-up docker-down docker-logs load-test

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip
DOCKER_COMPOSE := docker-compose
APP_NAME := fastapi-deployment-pipeline

# Colors for pretty output
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo ""
	@echo "$(BLUE)$(APP_NAME)$(NC) - Available Commands"
	@echo ""
	@echo "$(YELLOW)Usage:$(NC) make [target]"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""

# =============================================================================
# Development Setup
# =============================================================================

install: ## Install production dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

dev: ## Install development dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	pre-commit install

venv: ## Create virtual environment
	$(PYTHON) -m venv .venv
	@echo "$(GREEN)Virtual environment created. Activate with: source .venv/bin/activate$(NC)"

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linters (ruff, mypy)
	@echo "$(BLUE)Running Ruff linter...$(NC)"
	ruff check app/ tests/
	@echo "$(BLUE)Running MyPy type checker...$(NC)"
	mypy app/ --ignore-missing-imports

format: ## Format code (black, ruff)
	@echo "$(BLUE)Formatting code with Black...$(NC)"
	black app/ tests/
	@echo "$(BLUE)Formatting code with Ruff...$(NC)"
	ruff format app/ tests/
	@echo "$(GREEN)Code formatted!$(NC)"

format-check: ## Check code formatting without changes
	black --check app/ tests/
	ruff format --check app/ tests/

# =============================================================================
# Testing
# =============================================================================

test: ## Run tests with coverage
	pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

test-fast: ## Run tests without coverage (faster)
	pytest tests/ -v

test-watch: ## Run tests in watch mode
	ptw -- -v

# =============================================================================
# Security
# =============================================================================

security: ## Run security checks
	@echo "$(BLUE)Running Bandit (SAST)...$(NC)"
	bandit -r app/ -ll || true
	@echo "$(BLUE)Running Safety (dependency check)...$(NC)"
	safety check -r requirements.txt || true

# =============================================================================
# Local Development
# =============================================================================

run: ## Run application locally
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run application in production mode
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# =============================================================================
# Docker
# =============================================================================

build: ## Build Docker image
	docker build -t $(APP_NAME):latest .

docker-up: ## Start all services with Docker Compose
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "  API:        http://localhost:8000"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana:    http://localhost:3000"

docker-down: ## Stop all services
	$(DOCKER_COMPOSE) down

docker-down-v: ## Stop all services and remove volumes
	$(DOCKER_COMPOSE) down -v

docker-logs: ## Follow Docker Compose logs
	$(DOCKER_COMPOSE) logs -f

docker-logs-api: ## Follow API service logs
	$(DOCKER_COMPOSE) logs -f api

docker-build: ## Build and start services
	$(DOCKER_COMPOSE) up -d --build

docker-restart: ## Restart all services
	$(DOCKER_COMPOSE) restart

docker-ps: ## Show running containers
	$(DOCKER_COMPOSE) ps

# =============================================================================
# Load Testing
# =============================================================================

load-test: ## Run load test (requires running API)
	locust -f load_tests/locustfile.py --host=http://localhost:8000

load-test-headless: ## Run headless load test
	locust -f load_tests/locustfile.py \
		--host=http://localhost:8000 \
		--headless \
		--users 50 \
		--spawn-rate 5 \
		--run-time 2m

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Clean up generated files
	@echo "$(BLUE)Cleaning up...$(NC)"
	rm -rf __pycache__ .pytest_cache .coverage htmlcov .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

clean-docker: ## Remove Docker images and volumes
	docker-compose down -v --rmi local
	docker image prune -f

# =============================================================================
# Release
# =============================================================================

version: ## Show current version
	@cat VERSION

bump-patch: ## Bump patch version
	./scripts/bump-version.sh patch

bump-minor: ## Bump minor version
	./scripts/bump-version.sh minor

bump-major: ## Bump major version
	./scripts/bump-version.sh major

# =============================================================================
# Utilities
# =============================================================================

shell: ## Open Python shell with app context
	$(PYTHON) -c "from app.main import app; import code; code.interact(local=locals())"

redis-cli: ## Connect to Redis CLI
	docker-compose exec redis redis-cli

health: ## Check API health
	@curl -s http://localhost:8000/healthz | python -m json.tool

metrics: ## Fetch Prometheus metrics
	@curl -s http://localhost:8000/metrics | head -50

# =============================================================================
# CI/CD Simulation
# =============================================================================

ci: lint test security build ## Run full CI pipeline locally
	@echo "$(GREEN)CI pipeline completed successfully!$(NC)"
