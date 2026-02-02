# Contributing Guide

Thank you for your interest in contributing to the FastAPI Deployment Pipeline! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to:

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Git
- Make (recommended)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/fastapi-deployment-pipeline.git
   cd fastapi-deployment-pipeline
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/username/fastapi-deployment-pipeline.git
   ```

## Development Setup

### 1. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
make dev
# or manually:
pip install -r requirements-dev.txt
pre-commit install
```

### 3. Start Services

```bash
make docker-up
```

### 4. Verify Setup

```bash
# Run tests
make test

# Check linting
make lint

# Run the application
make run
```

## Making Changes

### Branch Naming Convention

Use descriptive branch names with prefixes:

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/changes
- `chore/` - Maintenance tasks

Examples:
```bash
git checkout -b feature/add-authentication
git checkout -b fix/redis-connection-leak
git checkout -b docs/update-api-examples
```

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(api): add user authentication endpoint

- Implement JWT token authentication
- Add login/logout endpoints
- Include rate limiting

Closes #123
```

```
fix(cache): resolve Redis connection pool exhaustion

The connection pool was not properly releasing connections
after timeouts, causing pool exhaustion under load.
```

### Before Submitting

1. **Update your branch:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run the full test suite:**
   ```bash
   make ci
   ```

3. **Check for linting issues:**
   ```bash
   make lint
   make format
   ```

4. **Update documentation** if needed

## Pull Request Process

### 1. Create the PR

- Use the PR template
- Provide a clear description of changes
- Link related issues
- Add appropriate labels

### 2. PR Checklist

- [ ] Tests pass locally
- [ ] Code follows project style guidelines
- [ ] Documentation is updated
- [ ] Changelog entry added (if applicable)
- [ ] No secrets or sensitive data included
- [ ] Branch is up to date with main

### 3. Review Process

- At least one approval required
- All CI checks must pass
- Address review feedback promptly
- Keep discussions professional and constructive

### 4. After Merge

- Delete your feature branch
- Update your local main:
  ```bash
  git checkout main
  git pull upstream main
  ```

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints (PEP 484)
- Maximum line length: 88 characters (Black default)
- Use docstrings for public functions/classes

### Code Quality Tools

The project uses:
- **Black** - Code formatting
- **Ruff** - Linting
- **MyPy** - Type checking
- **Bandit** - Security scanning

Run all checks:
```bash
make lint
```

Auto-format code:
```bash
make format
```

### Example Code Style

```python
"""Module docstring describing the purpose."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    """Request model for creating an item."""

    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)


async def create_item(item: ItemCreate) -> dict[str, Any]:
    """
    Create a new item.

    Args:
        item: The item data to create.

    Returns:
        The created item with generated ID.

    Raises:
        HTTPException: If creation fails.
    """
    # Implementation here
    pass
```

## Testing Guidelines

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── test_health.py       # Health endpoint tests
├── test_metrics.py      # Metrics tests
├── test_items.py        # Items API tests
└── integration/         # Integration tests
    └── test_redis.py
```

### Writing Tests

- Use descriptive test names
- Follow Arrange-Act-Assert pattern
- Use fixtures for common setup
- Aim for >70% code coverage

Example:
```python
class TestCreateItem:
    """Tests for item creation endpoint."""

    def test_create_item_success(
        self, client: TestClient, sample_item: dict
    ) -> None:
        """Test successful item creation with valid data."""
        # Arrange
        # (using fixtures)

        # Act
        response = client.post("/api/v1/items", json=sample_item)

        # Assert
        assert response.status_code == 201
        assert response.json()["name"] == sample_item["name"]

    def test_create_item_invalid_price(self, client: TestClient) -> None:
        """Test item creation fails with negative price."""
        response = client.post(
            "/api/v1/items",
            json={"name": "Test", "price": -10},
        )
        assert response.status_code == 422
```

### Running Tests

```bash
# All tests with coverage
make test

# Specific test file
pytest tests/test_health.py -v

# Specific test class/function
pytest tests/test_items.py::TestCreateItem::test_create_item_success -v

# With print output
pytest -v -s
```

## Documentation

### When to Update Docs

- Adding new features
- Changing API endpoints
- Modifying configuration options
- Updating dependencies
- Adding new scripts/commands

### Documentation Locations

- **README.md** - Project overview
- **docs/** - Detailed documentation
- **Code docstrings** - Inline documentation
- **CHANGELOG.md** - Version history

### ADR (Architecture Decision Records)

For significant technical decisions, create an ADR:

```bash
# Create new ADR
touch docs/architecture/XXX-decision-title.md
```

Follow the template in `docs/architecture/001-fastapi-choice.md`.

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for general questions
- Check existing issues/discussions first

Thank you for contributing!
