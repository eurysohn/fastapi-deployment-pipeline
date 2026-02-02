# Operations Runbook

This runbook provides guidance for operating the FastAPI Deployment Pipeline in production.

## Table of Contents

- [Service Overview](#service-overview)
- [Health Monitoring](#health-monitoring)
- [Common Operations](#common-operations)
- [Incident Response](#incident-response)
- [Troubleshooting](#troubleshooting)
- [Scaling](#scaling)
- [Backup & Recovery](#backup--recovery)

---

## Service Overview

### Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  FastAPI    │────▶│    Redis    │
│             │     │   (API)     │     │   (Cache)   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              ┌──────────┐  ┌──────────┐
              │Prometheus│  │  Grafana │
              │(Metrics) │  │(Dashboard│
              └──────────┘  └──────────┘
```

### Service Endpoints

| Service | Port | URL |
|---------|------|-----|
| API | 8000 | http://localhost:8000 |
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3000 | http://localhost:3000 |
| Redis | 6379 | redis://localhost:6379 |

### Key Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `http_requests_total` | Total requests | N/A |
| `http_request_duration_seconds` | Request latency | P95 > 1s |
| `http_requests_in_progress` | Active requests | > 100 |
| Error rate | 5xx responses | > 1% |

---

## Health Monitoring

### Health Check Endpoints

```bash
# Liveness probe - Is the app running?
curl http://localhost:8000/healthz
# Expected: {"status": "healthy"}

# Readiness probe - Can it handle traffic?
curl http://localhost:8000/readyz
# Expected: {"status": "healthy", "checks": {...}}

# Detailed health - Full system status
curl http://localhost:8000/health
```

### Health Check Responses

| Status | HTTP Code | Meaning |
|--------|-----------|---------|
| healthy | 200 | All systems operational |
| degraded | 200 | Optional services down |
| unhealthy | 503 | Required services down |

### Monitoring Commands

```bash
# Check all containers
docker-compose ps

# Check API logs
docker-compose logs -f api

# Check container resources
docker stats

# Check Redis connection
docker-compose exec redis redis-cli ping
```

---

## Common Operations

### Starting Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d api

# Rebuild and start
docker-compose up -d --build
```

### Stopping Services

```bash
# Stop all services (keep data)
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop specific service
docker-compose stop api
```

### Restarting Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart api

# Rolling restart (zero downtime)
docker-compose up -d --no-deps --build api
```

### Viewing Logs

```bash
# All logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api

# Filter by time
docker-compose logs --since 1h api
```

### Scaling

```bash
# Scale API instances
docker-compose up -d --scale api=3

# Note: Requires load balancer configuration
```

---

## Incident Response

### Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| P1 | Service down | 15 minutes | API unresponsive |
| P2 | Degraded | 1 hour | High latency |
| P3 | Minor | 4 hours | Monitoring gap |
| P4 | Low | Next sprint | UI bug |

### P1: Service Down

1. **Assess**
   ```bash
   # Check container status
   docker-compose ps

   # Check API health
   curl http://localhost:8000/healthz

   # Check logs
   docker-compose logs --tail=50 api
   ```

2. **Mitigate**
   ```bash
   # Restart the service
   docker-compose restart api

   # If restart fails, rebuild
   docker-compose up -d --build api
   ```

3. **Escalate** if not resolved in 15 minutes

4. **Communicate** via status page/Slack

5. **Post-incident** - Create incident report

### P2: High Latency

1. **Identify** slow endpoints
   ```bash
   # Check Prometheus
   # Query: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
   ```

2. **Check** dependencies
   ```bash
   # Redis latency
   docker-compose exec redis redis-cli --latency

   # Container resources
   docker stats
   ```

3. **Scale** if needed
   ```bash
   docker-compose up -d --scale api=3
   ```

---

## Troubleshooting

### API Won't Start

**Symptoms**: Container exits immediately or restarts repeatedly

**Steps**:
```bash
# Check exit code
docker-compose ps

# Check logs
docker-compose logs api

# Common issues:
# - Port already in use
# - Missing environment variables
# - Redis not ready
```

**Solutions**:
```bash
# Port conflict
lsof -i :8000  # Find process
kill -9 <PID>  # Kill if safe

# Missing env vars
cp .env.example .env
# Edit .env with correct values

# Redis not ready (check depends_on)
docker-compose restart api
```

### High Memory Usage

**Symptoms**: Memory usage grows over time

**Steps**:
```bash
# Check memory
docker stats

# Profile memory
# Add to code: import tracemalloc; tracemalloc.start()
```

**Solutions**:
- Check for memory leaks in code
- Reduce connection pool sizes
- Add memory limits to containers

### Redis Connection Issues

**Symptoms**: "Could not connect to Redis"

**Steps**:
```bash
# Check Redis status
docker-compose ps redis
docker-compose logs redis

# Test connection
docker-compose exec redis redis-cli ping
```

**Solutions**:
```bash
# Restart Redis
docker-compose restart redis

# Check network
docker network inspect fastapi-deployment-pipeline_app-network

# Verify Redis URL
echo $REDIS_URL
```

### High Error Rate

**Symptoms**: Error rate > 1%

**Steps**:
```bash
# Check error logs
docker-compose logs api | grep -i error

# Check Prometheus
# Query: rate(http_requests_total{status_code=~"5.."}[5m])
```

**Solutions**:
- Review error logs for patterns
- Check dependency health
- Review recent deployments
- Scale if overwhelmed

---

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.override.yml
services:
  api:
    deploy:
      replicas: 3
```

### Vertical Scaling

```yaml
# docker-compose.override.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Auto-scaling (Kubernetes)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Backup & Recovery

### Redis Backup

```bash
# Create snapshot
docker-compose exec redis redis-cli BGSAVE

# Copy dump file
docker cp fastapi-redis:/data/dump.rdb ./backups/

# Restore
docker cp ./backups/dump.rdb fastapi-redis:/data/
docker-compose restart redis
```

### Configuration Backup

```bash
# Backup configs
tar -czf config-backup.tar.gz \
  .env \
  docker-compose.yml \
  monitoring/
```

### Disaster Recovery

1. **Stop services**
   ```bash
   docker-compose down
   ```

2. **Restore data**
   ```bash
   # Restore Redis
   docker cp backup/dump.rdb fastapi-redis:/data/
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Verify**
   ```bash
   curl http://localhost:8000/health
   ```

---

## Contacts

| Role | Contact |
|------|---------|
| On-call | oncall@example.com |
| Team Lead | lead@example.com |
| Security | security@example.com |

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2024-01-15 | 1.0 | Initial version |
