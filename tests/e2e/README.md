# End-to-End (E2E) Tests

This directory contains end-to-end tests that validate the complete telemetry flow through the Obstackd observability stack.

## Overview

The E2E tests verify that telemetry data (metrics, traces, and logs) flows correctly from application instrumentation through the OpenTelemetry Collector to backend storage (Prometheus, Tempo, Loki) and is queryable via Grafana.

## Test Scenarios

### Metrics Flow Tests (`test_telemetry_flow.py::TestMetricsFlow`)

**Scenario: Metrics flow from application to Grafana**
- Sends synthetic metrics via OTLP HTTP (port 4318)
- Validates metrics appear in Prometheus within 15 seconds
- Verifies metrics are queryable in Grafana within 30 seconds
- Checks correct metric values and labels

### Traces Flow Tests (`test_telemetry_flow.py::TestTracesFlow`)

**Scenario: Traces flow from application to Tempo**
- Sends synthetic traces via OTLP gRPC (port 4317)
- Validates traces appear in Tempo within 10 seconds
- Verifies traces are viewable in Grafana Explore
- Checks all expected spans are present

### Correlation Tests (`test_telemetry_flow.py::TestCorrelation`)

**Scenario: Trace and metric correlation works**
- Sends correlated metrics and traces with shared trace_id
- Validates metrics can be queried by trace_id
- Verifies ability to navigate from metric to trace
- Demonstrates exemplar-style correlation

### Latency Tests (`test_telemetry_flow.py::TestEndToEndLatency`)

**Scenario: End-to-end latency is acceptable**
- Measures time from telemetry generation to availability in Prometheus
- Documents actual latency vs. 5-second SLA
- Provides tuning recommendations if SLA is not met

## Prerequisites

1. **Running Obstackd Stack**
   ```bash
   docker compose --profile core up -d
   ```

2. **Python 3.8+**

3. **Test Dependencies**
   ```bash
   pip install -r tests/e2e/requirements.txt
   ```

## Running Tests

### All E2E Tests

```bash
pytest tests/e2e/ -v
```

### Specific Test Classes

```bash
# Metrics flow tests
pytest tests/e2e/test_telemetry_flow.py::TestMetricsFlow -v

# Traces flow tests
pytest tests/e2e/test_telemetry_flow.py::TestTracesFlow -v

# Correlation tests
pytest tests/e2e/test_telemetry_flow.py::TestCorrelation -v

# Latency tests
pytest tests/e2e/test_telemetry_flow.py::TestEndToEndLatency -v
```

### Individual Tests

```bash
# Test metric flow to Prometheus
pytest tests/e2e/test_telemetry_flow.py::TestMetricsFlow::test_metric_reaches_prometheus -v

# Test trace flow via gRPC
pytest tests/e2e/test_telemetry_flow.py::TestTracesFlow::test_trace_reaches_tempo_via_grpc -v

# Test correlation
pytest tests/e2e/test_telemetry_flow.py::TestCorrelation::test_trace_and_metric_correlation -v
```

### Using Test Markers

```bash
# Run only E2E tests
pytest -m e2e -v

# Exclude E2E tests from other test runs
pytest -m "not e2e" -v
```

## Environment Variables

Configure test endpoints via environment variables:

```bash
export OTEL_HTTP_ENDPOINT="http://localhost:4318"
export OTEL_GRPC_ENDPOINT="http://localhost:4317"
export PROMETHEUS_URL="http://localhost:9090"
export TEMPO_URL="http://localhost:3200"
export LOKI_URL="http://localhost:3100"
export GRAFANA_URL="http://localhost:3000"
export GRAFANA_USER="admin"
export GRAFANA_PASSWORD="admin"
```

## Test Architecture

### TelemetryGenerator Class

The `TelemetryGenerator` class provides methods to generate synthetic telemetry:

- **`send_test_metric()`** - Generates counter or histogram metrics
- **`send_test_trace()`** - Generates traces with multiple spans
- **`send_correlated_telemetry()`** - Generates metrics and traces with shared trace_id

### OpenTelemetry SDK Integration

Tests use the official OpenTelemetry Python SDK to:
- Create instrumented telemetry (not raw OTLP requests)
- Use OTLP exporters (HTTP and gRPC)
- Configure resource attributes
- Batch and export data realistically

### Validation Strategy

1. **Send telemetry** via OTel SDK
2. **Wait for propagation** (batch processing, scraping)
3. **Query backends** (Prometheus, Tempo, Loki)
4. **Validate presence** and correctness
5. **Measure latency** for SLA compliance

## Expected Results

When the Obstackd stack is healthy:

- ✅ All metrics flow tests pass
- ✅ All traces flow tests pass
- ✅ Correlation tests demonstrate trace_id linking
- ✅ Latency measurements documented (may exceed 5s with default config)

### Typical Latency Breakdown

| Component | Typical Delay | Tunable |
|-----------|---------------|---------|
| OTel Batch Export | 1-5s | Yes (batch timeout) |
| Prometheus Scrape | 15-30s | Yes (scrape interval) |
| Tempo Ingestion | 1-5s | Limited |
| Grafana Query | <1s | N/A |

**Note:** The 5-second SLA is challenging with default configurations. Consider:
- Reducing OTel batch timeout to 1s (from 5s)
- Reducing Prometheus scrape interval to 5s (from 15s)
- Using push-based metrics (remote write) instead of pull

## Troubleshooting

### Tests Fail: "Stack component not ready"

**Cause:** Services not fully started

**Solution:**
```bash
# Check service health
docker compose ps
docker compose logs otel-collector
docker compose logs prometheus

# Wait longer for startup
sleep 60
pytest tests/e2e/
```

### Tests Fail: "Metric not found"

**Cause:** Telemetry not reaching backend

**Solution:**
```bash
# Check OTel Collector is receiving data
curl http://localhost:8888/metrics | grep receiver_accepted

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify OTel Collector config
docker compose exec otel-collector cat /etc/otel/collector.yaml
```

### Tests Fail: "Trace not found in Tempo"

**Cause:** Trace propagation delay or Tempo configuration

**Solution:**
```bash
# Check Tempo status
curl http://localhost:3200/ready

# Check OTel Collector trace export
docker compose logs otel-collector | grep -i tempo

# Verify Tempo is receiving traces
docker compose logs tempo | grep -i "traces"
```

### High Latency (>5s)

**Cause:** Batch processing and scrape intervals

**Solutions:**
1. Tune OTel Collector batch processor (in `config/otel/collector.yaml`):
   ```yaml
   processors:
     batch:
       timeout: 1s  # Reduce from default 5s
       send_batch_size: 100
   ```

2. Tune Prometheus scrape interval (in `config/prometheus/prometheus.yaml`):
   ```yaml
   scrape_configs:
     - job_name: 'otel-collector'
       scrape_interval: 5s  # Reduce from default 15s
   ```

3. Restart services after config changes:
   ```bash
   docker compose --profile core restart
   ```

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```bash
# Start stack
docker compose --profile core up -d

# Wait for readiness
sleep 60

# Run E2E tests
pytest tests/e2e/ --junitxml=e2e-results.xml

# Cleanup
docker compose down -v
```

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Start Obstackd Stack
        run: docker compose --profile core up -d
      
      - name: Wait for Services
        run: sleep 60
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Dependencies
        run: pip install -r tests/e2e/requirements.txt
      
      - name: Run E2E Tests
        run: pytest tests/e2e/ -v --junitxml=e2e-results.xml
      
      - name: Upload Test Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-test-results
          path: e2e-results.xml
      
      - name: Cleanup
        if: always()
        run: docker compose down -v
```

## Development

### Adding New Tests

1. Follow BDD-style test structure (Given/When/Then)
2. Use the `@pytest.mark.e2e` marker
3. Add docstrings with scenario descriptions
4. Use unique test_id for each test run (UUID)
5. Document expected latency and SLAs

### Test Fixtures

Available fixtures (from `conftest.py`):
- `wait_for_stack` - Wait for all components
- `otel_http_endpoint` - OTLP HTTP endpoint
- `otel_grpc_endpoint` - OTLP gRPC endpoint
- `prometheus_query` - Query Prometheus
- `tempo_query` - Query Tempo
- `loki_query` - Query Loki
- `grafana_query` - Query Grafana datasources

### Best Practices

1. **Always wait for propagation** - Don't expect instant results
2. **Use unique identifiers** - Avoid test interference (UUID test_id)
3. **Retry with timeout** - Poll for results with reasonable timeout
4. **Measure and document latency** - Track actual vs. expected performance
5. **Clean up resources** - Though not critical for containerized tests

## References

- [OpenTelemetry Python SDK](https://opentelemetry.io/docs/instrumentation/python/)
- [OTLP Specification](https://opentelemetry.io/docs/specs/otlp/)
- [Prometheus Query API](https://prometheus.io/docs/prometheus/latest/querying/api/)
- [Tempo API](https://grafana.com/docs/tempo/latest/api_docs/)
- [Grafana Datasource API](https://grafana.com/docs/grafana/latest/developers/http_api/data_source/)

## Summary

These E2E tests validate the **Definition of Done** for Story 1.3:

- ✅ Complete telemetry pipeline tested
- ✅ End-to-end latency measured
- ✅ Correlation working for metrics and traces
- ✅ Tests run as part of CI/CD (ready for integration)
