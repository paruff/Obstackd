# Integration Tests

This directory contains integration tests for the Obstackd observability platform, focusing on validating end-to-end telemetry flows.

## Test Suites

### Home Assistant Metrics Integration (`test_homeassistant_metrics.py`)

Tests the complete flow of Home Assistant metrics from source to Prometheus.

**Test Scenarios:**

1. **Home Assistant Prometheus Endpoint**
   - Validates HA exposes metrics at `/api/prometheus`
   - Verifies metrics are in valid Prometheus format
   - Checks for key metrics (entity count, automation count)

2. **Prometheus Scraping**
   - Validates Prometheus discovers and scrapes HA target
   - Verifies `up{job="homeassistant"}=1` metric
   - Ensures HA metrics appear in Prometheus

3. **Metric Labels and Quality**
   - Validates required labels (job, instance)
   - Checks metric values are reasonable
   - Documents available metrics

## Prerequisites

- Docker and Docker Compose installed
- Python 3.8+ installed
- Services running via `docker compose --profile core --profile apps up -d`

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

### Run All Integration Tests

```bash
pytest tests/integration/
```

### Run Only Home Assistant Tests

```bash
pytest tests/integration/test_homeassistant_metrics.py
```

### Run with Verbose Output

```bash
pytest tests/integration/ -v
```

### Run Excluding Slow Tests

```bash
pytest tests/integration/ -m "not slow"
```

### Run Specific Test

```bash
pytest tests/integration/test_homeassistant_metrics.py::TestHomeAssistantPrometheusEndpoint::test_homeassistant_is_running
```

## Test Markers

Tests are marked with the following markers:

- `@pytest.mark.homeassistant` - Home Assistant related tests
- `@pytest.mark.metrics` - Metrics collection tests
- `@pytest.mark.prometheus` - Prometheus integration tests
- `@pytest.mark.otel` - OpenTelemetry Collector tests
- `@pytest.mark.slow` - Tests that take >30 seconds (require scrape cycles)
- `@pytest.mark.integration` - All integration tests

## Environment Variables

Tests can be configured with the following environment variables:

- `HOMEASSISTANT_URL` - Home Assistant base URL (default: `http://localhost:8123`)
- `PROMETHEUS_URL` - Prometheus base URL (default: `http://localhost:9090`)
- `OTEL_COLLECTOR_URL` - OTel Collector base URL (default: `http://localhost:8888`)

Example:
```bash
HOMEASSISTANT_URL=http://ha:8123 pytest tests/integration/
```

## Expected Metrics

### Home Assistant Core Metrics

Based on Home Assistant's Prometheus integration, the following metric categories are expected:

1. **Entity Metrics**
   - `homeassistant_entity_available` - Entity availability by domain
   - Entity state values (depends on configuration)

2. **Automation Metrics**
   - Automation trigger counts
   - Automation execution states

3. **System Metrics**
   - API call counts
   - Integration health
   - Component states

For a complete list of available metrics, run:
```bash
pytest tests/integration/test_homeassistant_metrics.py::TestHomeAssistantMetricsDocumentation::test_document_available_metrics -v -s
```

## Troubleshooting

### Home Assistant Not Ready

If tests fail with "Home Assistant did not become ready in time":

1. Check if Home Assistant container is running:
   ```bash
   docker compose ps homeassistant
   ```

2. Check Home Assistant logs:
   ```bash
   docker compose logs homeassistant
   ```

3. Verify configuration is valid:
   ```bash
   docker compose exec homeassistant hass --script check_config
   ```

### No Metrics in Prometheus

If Home Assistant metrics don't appear in Prometheus:

1. Check Prometheus targets:
   ```bash
   curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="homeassistant")'
   ```

2. Verify Prometheus is scraping:
   ```bash
   docker compose logs prometheus | grep homeassistant
   ```

3. Test HA metrics endpoint directly:
   ```bash
   curl http://localhost:8123/api/prometheus
   ```

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

- `homeassistant_base_url` - HA base URL
- `prometheus_base_url` - Prometheus base URL
- `wait_for_homeassistant` - Wait for HA readiness
- `wait_for_prometheus` - Wait for Prometheus readiness
- `wait_for_scrape_cycle` - Wait for Prometheus scrape
- `prometheus_query` - Helper to query Prometheus
- `parse_metrics` - Helper to parse Prometheus text format

## CI/CD Integration

These tests are designed to run in CI/CD pipelines:

```yaml
- name: Run Integration Tests
  run: |
    docker compose --profile core --profile apps up -d
    sleep 60  # Wait for services
    pip install -r tests/integration/requirements.txt
    pytest tests/integration/ --junitxml=test-results.xml
```

## References

- [Home Assistant Prometheus Integration](https://www.home-assistant.io/integrations/prometheus/)
- [Prometheus Query API](https://prometheus.io/docs/prometheus/latest/querying/api/)
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-bdd Documentation](https://pytest-bdd.readthedocs.io/)
