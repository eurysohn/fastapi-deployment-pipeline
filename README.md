# FastAPI Deployment Pipeline

[![CI Pipeline](https://github.com/username/fastapi-deployment-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/username/fastapi-deployment-pipeline/actions/workflows/ci.yml)
[![Security Scan](https://github.com/username/fastapi-deployment-pipeline/actions/workflows/security.yml/badge.svg)](https://github.com/username/fastapi-deployment-pipeline/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/username/fastapi-deployment-pipeline/branch/main/graph/badge.svg)](https://codecov.io/gh/username/fastapi-deployment-pipeline)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Production-ready FastAPI deployment pipeline demonstrating DevOps best practices.**

This repository serves as a reference implementation for building, testing, and deploying FastAPI applications with enterprise-grade CI/CD pipelines, observability, and security practices.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CI/CD Pipeline                           │
├─────────────────────────────────────────────────────────────────┤
│  PR → Lint → Security → Test → Build → Push → Deploy (Mock)    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Application Stack                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   FastAPI    │───▶│    Redis     │    │  Prometheus  │      │
│  │   (API)      │    │   (Cache)    │    │  (Metrics)   │      │
│  └──────────────┘    └──────────────┘    └──────┬───────┘      │
│         │                                        │              │
│         └────────────────────────────────────────┘              │
│                              │                                  │
│                              ▼                                  │
│                     ┌──────────────┐                           │
│                     │   Grafana    │                           │
│                     │ (Dashboard)  │                           │
│                     └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### Application
- **FastAPI** with async support and automatic OpenAPI documentation
- **Health endpoints** (`/healthz`, `/readyz`) for Kubernetes probes
- **Prometheus metrics** (`/metrics`) for monitoring
- **Redis caching** with connection pooling
- **Structured JSON logging** for ELK/CloudWatch integration
- **Request ID tracking** for distributed tracing

### CI/CD
- **GitHub Actions** with parallel jobs for fast feedback
- **Multi-stage builds** for optimized Docker images
- **Security scanning** (SAST, dependency audit, container scan)
- **Automated releases** with changelog generation
- **Dependabot** for automated dependency updates

### Observability
- **Prometheus** metrics collection
- **Grafana** dashboards with pre-configured panels
- **Structured logging** with correlation IDs
- **Health checks** for all components

### Security
- **Non-root containers** for defense in depth
- **Secret detection** with Gitleaks
- **SAST** with Bandit
- **Dependency scanning** with Safety
- **Container scanning** with Trivy
- **CodeQL** analysis

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+
- Make (optional, but recommended)

### Local Development

```bash
# Clone the repository
git clone https://github.com/username/fastapi-deployment-pipeline.git
cd fastapi-deployment-pipeline

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
make dev  # or: pip install -r requirements-dev.txt

# Run locally
make run  # or: uvicorn app.main:app --reload
```

### Docker Compose (Full Stack)

```bash
# Start all services
make docker-up  # or: docker-compose up -d

# Access services:
# - API:        http://localhost:8000
# - API Docs:   http://localhost:8000/docs
# - Prometheus: http://localhost:9090
# - Grafana:    http://localhost:3000 (admin/admin)

# View logs
make docker-logs

# Stop services
make docker-down
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service info |
| `/healthz` | GET | Liveness probe |
| `/readyz` | GET | Readiness probe |
| `/health` | GET | Detailed health check |
| `/metrics` | GET | Prometheus metrics |
| `/api/v1/items` | GET | List items |
| `/api/v1/items` | POST | Create item |
| `/api/v1/items/{id}` | GET | Get item |
| `/api/v1/items/{id}` | PUT | Update item |
| `/api/v1/items/{id}` | DELETE | Delete item |
| `/docs` | GET | OpenAPI documentation |

## Project Structure

```
fastapi-deployment-pipeline/
├── app/                      # Application code
│   ├── api/                  # API endpoints
│   │   ├── health.py         # Health checks
│   │   ├── metrics.py        # Prometheus metrics
│   │   └── v1/               # API v1 endpoints
│   ├── core/                 # Core configuration
│   │   ├── config.py         # Settings management
│   │   └── logging.py        # Logging setup
│   ├── middleware/           # Custom middleware
│   ├── services/             # Business logic
│   └── main.py               # Application entry
├── tests/                    # Test suite
├── monitoring/               # Observability config
│   ├── prometheus/           # Prometheus config
│   └── grafana/              # Grafana dashboards
├── load_tests/               # Load testing (Locust)
├── scripts/                  # Utility scripts
├── docs/                     # Documentation
│   ├── architecture/         # ADRs
│   └── runbook.md            # Operations guide
├── .github/                  # GitHub configuration
│   ├── workflows/            # CI/CD pipelines
│   └── ISSUE_TEMPLATE/       # Issue templates
├── Dockerfile                # Container build
├── docker-compose.yml        # Local development
├── Makefile                  # Developer commands
└── pyproject.toml            # Python configuration
```

## Development

### Available Commands

```bash
make help          # Show all commands
make dev           # Install dev dependencies
make test          # Run tests with coverage
make lint          # Run linters
make format        # Format code
make security      # Run security checks
make build         # Build Docker image
make docker-up     # Start all services
make load-test     # Run load tests
make ci            # Run full CI pipeline locally
```

### Running Tests

```bash
# All tests with coverage
make test

# Fast tests (no coverage)
make test-fast

# Specific test file
pytest tests/test_health.py -v
```

### Code Quality

```bash
# Format code
make format

# Check linting
make lint

# Run security checks
make security

# Pre-commit hooks (auto-runs on commit)
pre-commit run --all-files
```

## CI/CD Pipeline

### Pull Request Pipeline

1. **Lint & Format** - Ruff, Black, MyPy
2. **Security Scan** - Bandit, Safety
3. **Test** - Pytest with 70% coverage threshold
4. **Build** - Docker image build
5. **Push** - Push to GitHub Container Registry
6. **Deploy** - Mock deployment

### Release Pipeline

Triggered on version tags (`v*.*.*`):
1. Generate changelog
2. Create GitHub release
3. Build and push versioned Docker image
4. Generate SBOM

### Security Pipeline

Weekly scheduled scan + on dependency changes:
- Dependency vulnerability scanning
- Container image scanning
- Secret detection
- CodeQL analysis

## Monitoring

### Grafana Dashboard

Pre-configured panels:
- Request rate (req/s)
- P95 latency
- Error rate (%)
- Request distribution by endpoint
- Response time distribution
- Cache hit/miss ratio

Access: http://localhost:3000 (admin/admin)

### Key Metrics

| Metric | Description |
|--------|-------------|
| `http_requests_total` | Total HTTP requests |
| `http_request_duration_seconds` | Request latency histogram |
| `http_requests_in_progress` | Active requests |
| `cache_hits_total` | Cache hit counter |
| `cache_misses_total` | Cache miss counter |

## Load Testing

```bash
# Start API first
make docker-up

# Run load test with web UI
make load-test

# Headless load test
make load-test-headless
```

See [load_tests/README.md](load_tests/README.md) for detailed scenarios.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | development/staging/production | development |
| `LOG_LEVEL` | DEBUG/INFO/WARNING/ERROR | INFO |
| `LOG_FORMAT` | json/console | json |
| `REDIS_URL` | Redis connection URL | redis://localhost:6379/0 |
| `METRICS_ENABLED` | Enable Prometheus metrics | true |

See [.env.example](.env.example) for full list.

## Documentation

- [Architecture Decision Records](docs/architecture/)
- [Operations Runbook](docs/runbook.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [Prometheus](https://prometheus.io/)
- [Grafana](https://grafana.com/)
- [Docker](https://www.docker.com/)
