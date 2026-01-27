# Integration Tests

This directory contains comprehensive integration tests for the Obstackd observability platform, validating end-to-end telemetry flows and component health.

## Test Suites

### Observability Stack Core Tests

#### Prometheus Scraping (`test_prometheus_scraping.py`)
Tests Prometheus metric scraping functionality across all configured targets.

**Test Scenarios:**
- ✅ OTel Collector target is up and scraped successfully
- ✅ Scrape duration is within SLA (<1s)
- ✅ All configured targets are healthy
- ✅ No scrape errors
- ✅ Metrics have correct labels
- ✅ Metric cardinality is reasonable
- ✅ Target details and health monitoring

#### OpenTelemetry Collector (`test_otel_collector.py`)
Tests OTel Collector operations and telemetry pipeline.

**Test Scenarios:**
- ✅ Collector is running and serving metrics
- ✅ OTLP receivers (gRPC and HTTP) are operational
- ✅ Exporters are sending data successfully
- ✅ Processors (batch) are working
- ✅ Queue metrics are healthy
- ✅ No data is being refused or dropped

#### Grafana Integration (`test_grafana_integration.py`)
Tests Grafana functionality and datasource connectivity.

**Test Scenarios:**
- ✅ Grafana is healthy and accessible
- ✅ All datasources (Prometheus, Tempo, Loki) are provisioned
- ✅ Datasource connectivity is working
- ✅ Dashboards can query data
- ✅ Required plugins are installed
- ✅ Authentication is configured

#### Tempo Tracing (`test_tempo_integration.py`)
Tests Tempo distributed tracing backend.

**Test Scenarios:**
- ✅ Tempo is ready and healthy
- ✅ All receiver ports are accessible (OTLP, Jaeger, Zipkin)
- ✅ Tempo API endpoints are working
- ✅ Search functionality is operational
- ✅ Metrics are exposed

#### Loki Logs (`test_loki_integration.py`)
Tests Loki log aggregation system.

**Test Scenarios:**
- ✅ Loki is ready and healthy
- ✅ Log ingestion ports are accessible
- ✅ Loki API endpoints are working
- ✅ Label queries are functional
- ✅ Promtail integration is working
- ✅ Metrics are exposed

### Application Integration Tests

## Prerequisites

- Docker and Docker Compose installed
- Python 3.8+ installed
- Services running via `docker compose --profile core up -d`

## Installation

1. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r tests/integration/requirements.txt
   ```

## Running Tests

### Prerequisites

- Docker and Docker Compose installed
- Python 3.8+ installed
- Services running via `docker compose --profile core up -d`

### Installation

1. Create a virtual environment (optional):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r tests/integration/requirements.txt
   ```

### Run All Integration Tests

```bash
pytest tests/integration/
```

### Run Specific Test Files

```bash
# Prometheus scraping tests
pytest tests/integration/test_prometheus_scraping.py -v

# OTel Collector tests
pytest tests/integration/test_otel_collector.py -v

# Grafana tests
pytest tests/integration/test_grafana_integration.py -v

# Tempo tests
pytest tests/integration/test_tempo_integration.py -v

# Loki tests
pytest tests/integration/test_loki_integration.py -v

# Dashboard tests
pytest tests/integration/test_dashboards.py -v
```

### Run Using e2e-runner

```bash
# Start services and run integration tests
./tests/acceptance/e2e-runner.sh --scenario integration-tests

# With cleanup
./tests/acceptance/e2e-runner.sh --scenario integration-tests --cleanup
```

### Run with Verbose Output

```bash
pytest tests/integration/ -v
```

### Run Excluding Slow Tests

```bash
pytest tests/integration/ -m "not slow"
```

## Test Markers

Tests are marked with the following markers for easy filtering:

- `@pytest.mark.prometheus` - Prometheus-related tests
- `@pytest.mark.otel` - OpenTelemetry Collector tests
- `@pytest.mark.grafana` - Grafana tests
- `@pytest.mark.tempo` - Tempo tests
- `@pytest.mark.loki` - Loki tests
- `@pytest.mark.metrics` - Metrics collection tests
- `@pytest.mark.slow` - Tests that take >30 seconds (require scrape cycles)
- `@pytest.mark.integration` - All integration tests

### Run Tests by Marker

```bash
# Run only Prometheus tests
pytest tests/integration/ -v -m prometheus

# Run only Grafana tests
pytest tests/integration/ -v -m grafana

# Exclude slow tests
pytest tests/integration/ -m "not slow"
```

## Environment Variables

Tests can be configured with the following environment variables:

**Core Services:**
- `PROMETHEUS_URL` - Prometheus base URL (default: `http://localhost:9090`)
- `OTEL_METRICS_URL` - OTel Collector metrics URL (default: `http://localhost:8888`)
- `GRAFANA_URL` - Grafana base URL (default: `http://localhost:3000`)
- `GRAFANA_USER` - Grafana username (default: `admin`)
- `GRAFANA_PASSWORD` - Grafana password (default: `admin`)
- `TEMPO_URL` - Tempo base URL (default: `http://localhost:3200`)
- `LOKI_URL` - Loki base URL (default: `http://localhost:3100`)

**Applications:**
Example:
```bash
GRAFANA_URL=http://grafana:3000 pytest tests/integration/test_grafana_integration.py
```

## Test Coverage Summary

| Component | Tests | Coverage |
|-----------|-------|----------|
| Prometheus | 13 | Scraping, targets, labels, cardinality |
| OTel Collector | 14 | Health, receivers, exporters, processors |
| Grafana | 14 | Health, datasources, dashboards, plugins |
| Tempo | 15 | Health, ports, API, metrics |
| Loki | 15 | Health, ports, API, Promtail |
| **Core Total** | **71** | **All core functionality** |
| Dashboards | 14 | Provisioning, structure, datasources |
| **Grand Total** | **85+** | **Complete observability stack** |

### Expected Test Results

When running with `--profile core`:
- **71 core tests** pass
- **0 failures**
- **Duration**: ~20 seconds

When running with `--profile core`:
- **Duration**: ~40-60 seconds

## Troubleshooting

### Slow Tests Timing Out

Slow tests wait for Prometheus scrape cycles (35 seconds by default). If tests timeout:

- Increase test timeout in pytest.ini
- Check that services are actually healthy
- Ensure sufficient resources for containers

## Development

### Adding New Tests

1. Follow BDD style with clear Given/When/Then structure
2. Use appropriate test markers
3. Add docstrings explaining test purpose
4. Update this README with new test scenarios

### Test Fixtures

Common fixtures are defined in `conftest.py`:

- `prometheus_base_url` - Prometheus base URL
- `wait_for_prometheus` - Wait for Prometheus readiness
- `wait_for_scrape_cycle` - Wait for Prometheus scrape
- `prometheus_query` - Helper to query Prometheus
- `parse_metrics` - Helper to parse Prometheus text format

## CI/CD Integration

Integration tests run automatically in GitHub Actions:

**Workflow:** `.github/workflows/integration-tests.yml`

**Trigger:** Pull requests and pushes to main

**Steps:**
1. Start observability stack with `docker compose --profile core up -d`
2. Wait for services to be ready (~60 seconds)
3. Run all integration tests
4. Collect logs on failure
5. Clean up services

**Expected Results:**
- **71 tests** should pass for core stack
- **Additional tests** for applications when `--profile apps` is used
- **Test duration**: ~5-10 minutes in CI

Manual CI-style run:
```bash
# Exactly as CI does it
docker compose --profile core up -d
sleep 60
pytest tests/integration/ --junitxml=test-results.xml
docker compose down -v
```

## References

- [Prometheus Query API](https://prometheus.io/docs/prometheus/latest/querying/api/)
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-bdd Documentation](https://pytest-bdd.readthedocs.io/)
