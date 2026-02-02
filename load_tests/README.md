# Load Testing

This directory contains load testing configurations using [Locust](https://locust.io/).

## Quick Start

### Prerequisites

```bash
pip install locust
```

### Running Tests

#### With Web UI

```bash
# Start Locust with web interface
locust -f load_tests/locustfile.py --host=http://localhost:8000

# Open browser to http://localhost:8089
```

#### Headless Mode (CI/CD)

```bash
# Run smoke test
locust -f load_tests/locustfile.py \
    --host=http://localhost:8000 \
    --headless \
    --users 10 \
    --spawn-rate 2 \
    --run-time 1m \
    --tags smoke

# Run full load test
locust -f load_tests/locustfile.py \
    --host=http://localhost:8000 \
    --headless \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --tags load
```

## Test Scenarios

### 1. Smoke Test

Verifies basic functionality under minimal load.

```bash
locust -f load_tests/locustfile.py --host=http://localhost:8000 \
    --headless -u 5 -r 1 -t 1m --tags smoke
```

**Parameters:**
- Users: 5
- Spawn rate: 1/second
- Duration: 1 minute

**Success Criteria:**
- 0% error rate
- All health checks pass
- Response time < 500ms

### 2. Load Test

Tests normal expected production load.

```bash
locust -f load_tests/locustfile.py --host=http://localhost:8000 \
    --headless -u 100 -r 10 -t 10m --tags load
```

**Parameters:**
- Users: 100
- Spawn rate: 10/second
- Duration: 10 minutes

**Success Criteria:**
- Error rate < 1%
- P95 response time < 1000ms
- No memory leaks

### 3. Stress Test

Pushes system beyond normal capacity to find breaking points.

```bash
locust -f load_tests/locustfile.py --host=http://localhost:8000 \
    --headless -u 500 -r 50 -t 5m --tags stress \
    --class-picker StressTestUser
```

**Parameters:**
- Users: 500
- Spawn rate: 50/second
- Duration: 5 minutes

**Goals:**
- Identify breaking point
- Monitor resource exhaustion
- Verify graceful degradation

### 4. Spike Test

Tests sudden traffic bursts.

```bash
locust -f load_tests/locustfile.py --host=http://localhost:8000 \
    --headless -u 200 -r 200 -t 2m --tags spike \
    --class-picker SpikeTestUser
```

**Parameters:**
- Users: 200 (all at once)
- Spawn rate: 200/second
- Duration: 2 minutes

**Goals:**
- Verify system handles sudden load
- Test auto-scaling triggers
- Monitor recovery time

### 5. Soak Test

Extended duration test for memory leaks.

```bash
locust -f load_tests/locustfile.py --host=http://localhost:8000 \
    --headless -u 50 -r 5 -t 2h --tags load
```

**Parameters:**
- Users: 50
- Spawn rate: 5/second
- Duration: 2 hours

**Goals:**
- Detect memory leaks
- Verify long-term stability
- Monitor resource trends

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOCUST_HOST` | Target host URL | - |
| `LOCUST_USERS` | Number of users | 10 |
| `LOCUST_SPAWN_RATE` | Users per second | 1 |
| `LOCUST_RUN_TIME` | Test duration | 1m |

### Custom Configuration

Create a `locust.conf` file:

```ini
[runtime settings]
host = http://localhost:8000
users = 100
spawn-rate = 10
run-time = 5m
headless = true

[web ui]
web-host = 0.0.0.0
web-port = 8089
```

## Output & Reports

### CSV Reports

```bash
locust -f load_tests/locustfile.py --host=http://localhost:8000 \
    --headless -u 100 -r 10 -t 5m \
    --csv=results/load_test
```

Generates:
- `load_test_stats.csv` - Request statistics
- `load_test_stats_history.csv` - Time series data
- `load_test_failures.csv` - Failure details

### HTML Report

```bash
locust -f load_tests/locustfile.py --host=http://localhost:8000 \
    --headless -u 100 -r 10 -t 5m \
    --html=results/report.html
```

## Integrating with CI/CD

### GitHub Actions Example

```yaml
- name: Run Load Test
  run: |
    pip install locust
    locust -f load_tests/locustfile.py \
        --host=${{ env.API_URL }} \
        --headless \
        --users 50 \
        --spawn-rate 5 \
        --run-time 2m \
        --csv=results/load_test \
        --exit-code-on-error 1
```

### Failure Criteria

```bash
# Exit with error if:
# - Error rate > 5%
# - P95 > 2000ms
locust -f load_tests/locustfile.py \
    --host=http://localhost:8000 \
    --headless -u 100 -r 10 -t 5m \
    --check-fail-ratio 0.05 \
    --check-avg-response-time 2000
```

## Monitoring During Tests

While running load tests, monitor:

1. **Application Metrics**: http://localhost:3000 (Grafana)
2. **Prometheus**: http://localhost:9090
3. **Container Stats**: `docker stats`
4. **Application Logs**: `docker-compose logs -f api`

## Interpreting Results

### Key Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| RPS | Requests per second | Depends on scale |
| P50 | Median response time | < 100ms |
| P95 | 95th percentile | < 500ms |
| P99 | 99th percentile | < 1000ms |
| Error Rate | Percentage of failures | < 1% |

### Common Issues

| Symptom | Possible Cause | Solution |
|---------|---------------|----------|
| High error rate | Connection limits | Increase worker connections |
| Increasing latency | Resource exhaustion | Scale horizontally |
| Timeouts | Slow database | Add caching, optimize queries |
| Memory growth | Memory leak | Profile and fix |
