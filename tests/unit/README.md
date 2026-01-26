# Configuration Validation Tests

This directory contains unit tests for validating observability platform configuration files.

## Overview

The unit tests validate configuration files for all components in the observability stack:
- OpenTelemetry Collector
- Prometheus
- Grafana
- Tempo
- Loki

These tests catch configuration errors early in the development cycle, before deployment.

## Test Files

### `test_otel_config_validation.py`
Validates OpenTelemetry Collector configuration (`config/otel/collector.yaml`).

**Validates:**
- YAML syntax
- Required receivers (OTLP)
- Processor configuration (memory_limiter, batch)
- Exporter endpoints (Prometheus, Tempo, Loki)
- Service pipeline definitions
- Pipeline processor order
- Component references

**Test Classes:**
- `TestOTelConfigStructure` - Basic structure validation
- `TestOTelReceivers` - Receiver configuration
- `TestOTelProcessors` - Processor configuration
- `TestOTelExporters` - Exporter endpoints
- `TestOTelServicePipelines` - Pipeline configuration

### `test_prometheus_config_validation.py`
Validates Prometheus configuration (`config/prometheus/prometheus.yaml`).

**Validates:**
- YAML syntax
- Global configuration (scrape_interval, evaluation_interval)
- Alertmanager configuration
- Rule files
- Scrape configurations
- Job configurations
- Required observability stack jobs

**Test Classes:**
- `TestPrometheusConfigStructure` - Basic structure
- `TestPrometheusGlobalConfig` - Global settings
- `TestPrometheusAlertingConfig` - Alerting configuration
- `TestPrometheusRuleFiles` - Rule file references
- `TestPrometheusScrapeConfigs` - Scrape job configurations
- `TestPrometheusJobsForObservabilityStack` - Required jobs

### `test_grafana_config_validation.py`
Validates Grafana datasources configuration (`config/grafana/provisioning/datasources/datasources.yaml`).

**Validates:**
- YAML syntax
- API version
- Datasource definitions
- Datasource types and URLs
- Access modes
- Required datasources (Prometheus, Tempo, Loki)
- jsonData configuration

**Test Classes:**
- `TestGrafanaConfigStructure` - Basic structure
- `TestGrafanaDatasourceBasics` - Datasource basics
- `TestGrafanaRequiredDatasources` - Required datasources
- `TestGrafanaPrometheusDatasource` - Prometheus datasource
- `TestGrafanaTempoDatasource` - Tempo datasource
- `TestGrafanaLokiDatasource` - Loki datasource
- `TestGrafanaJsonDataConfiguration` - jsonData validation

### `test_tempo_config_validation.py`
Validates Tempo configuration (`config/tempo/tempo.yaml`).

**Validates:**
- YAML syntax
- Server configuration (ports, log level)
- Distributor receivers (OTLP)
- Ingester settings
- Storage backend configuration
- Compactor settings
- Query configuration

**Test Classes:**
- `TestTempoConfigStructure` - Basic structure
- `TestTempoServerConfig` - Server settings
- `TestTempoDistributorConfig` - Distributor and receivers
- `TestTempoIngesterConfig` - Ingester settings
- `TestTempoStorageConfig` - Storage configuration
- `TestTempoCompactorConfig` - Compactor settings
- `TestTempoMetricsGeneratorConfig` - Metrics generator
- `TestTempoQueryConfig` - Query settings

### `test_loki_config_validation.py`
Validates Loki configuration (`config/loki/loki.yaml`).

**Validates:**
- YAML syntax
- Server configuration (ports, log level)
- Authentication settings
- Schema configuration
- Storage configuration
- Common configuration
- Limits and retention
- Compactor settings
- Query configuration

**Test Classes:**
- `TestLokiConfigStructure` - Basic structure
- `TestLokiServerConfig` - Server settings
- `TestLokiAuthConfig` - Authentication
- `TestLokiSchemaConfig` - Schema definitions
- `TestLokiStorageConfig` - Storage settings
- `TestLokiCommonConfig` - Common configuration
- `TestLokiLimitsConfig` - Limits and retention
- `TestLokiCompactorConfig` - Compactor settings
- `TestLokiQueryConfig` - Query settings

## Running Tests

### Install Dependencies

```bash
pip install -r tests/unit/requirements.txt
```

### Run All Unit Tests

```bash
pytest tests/unit/
```

### Run Tests for Specific Component

```bash
# OpenTelemetry Collector
pytest tests/unit/test_otel_config_validation.py

# Prometheus
pytest tests/unit/test_prometheus_config_validation.py

# Grafana
pytest tests/unit/test_grafana_config_validation.py

# Tempo
pytest tests/unit/test_tempo_config_validation.py

# Loki
pytest tests/unit/test_loki_config_validation.py
```

### Run with Verbose Output

```bash
pytest tests/unit/ -v
```

### Run Specific Test Class

```bash
pytest tests/unit/test_otel_config_validation.py::TestOTelReceivers -v
```

### Run Specific Test

```bash
pytest tests/unit/test_otel_config_validation.py::TestOTelReceivers::test_otlp_receiver_exists -v
```

### Use Markers

```bash
# Run only OTel tests
pytest -m otel

# Run only config validation tests
pytest -m config_validation
```

## Test Coverage

Current test coverage:
- **OpenTelemetry Collector**: 74 tests
- **Prometheus**: 21 tests
- **Grafana**: 22 tests
- **Tempo**: 28 tests
- **Loki**: 28 tests

**Total**: 118 tests

## Validation Rules

### Common Validations

All configuration files are validated for:
1. Valid YAML syntax
2. Required sections present
3. No empty required fields
4. Valid data types for fields
5. Valid port numbers (1-65535)
6. Valid URL formats
7. Valid time duration formats (e.g., "15s", "1m", "1h")

### Component-Specific Validations

#### OpenTelemetry Collector
- OTLP receiver must be configured
- memory_limiter processor recommended
- batch processor recommended
- Processor order: memory_limiter before batch
- All pipeline references must be valid
- Exporter endpoints must be valid

#### Prometheus
- Global scrape_interval required
- At least one scrape config required
- All scrape configs must have job_name
- Alertmanager targets must be valid
- Self-monitoring job recommended
- OTel Collector scrape job recommended

#### Grafana
- apiVersion must be 1
- At least one datasource required
- Prometheus, Tempo, and Loki datasources required
- At least one default datasource
- No duplicate datasource names
- All datasource URLs must be valid

#### Tempo
- Server HTTP port required
- OTLP receiver required
- Storage backend must be valid (local, s3, gcs, azure)
- Local storage requires path
- Ports must be in valid range

#### Loki
- auth_enabled must be boolean
- Server HTTP port required
- Schema config required with at least one entry
- Schema store must be valid (boltdb, boltdb-shipper, tsdb)
- Object store must be valid (filesystem, s3, gcs, azure, swift)
- Filesystem storage requires directory configuration
- Retention periods must have valid format

## CI Integration

These tests can be integrated into CI pipelines to prevent invalid configurations from being merged.

### GitHub Actions Example

```yaml
name: Config Validation

on:
  pull_request:
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: pip install -r tests/unit/requirements.txt
      
      - name: Run config validation tests
        run: pytest tests/unit/ -v
```

## Pre-commit Hook

To validate configurations before committing:

### `.pre-commit-config.yaml`

```yaml
- repo: local
  hooks:
    - id: config-validation
      name: Validate Configs
      entry: pytest tests/unit/
      language: system
      pass_filenames: false
      always_run: false
      files: ^config/.*\.(yaml|yml)$
```

## Extending Tests

### Adding New Validation Tests

1. Identify the configuration file to validate
2. Add fixture in `conftest.py` if needed
3. Create test class following existing patterns
4. Add validation logic with clear error messages
5. Run tests to ensure they pass
6. Update this README with new test information

### Example Test Template

```python
def test_new_validation_rule(self, config_path):
    """Test that <specific rule> is validated."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Your validation logic
    assert 'required_field' in config, \
        "Missing required field: required_field"
```

## Troubleshooting

### Test Failures

If tests fail, check:
1. YAML syntax is valid
2. Required sections are present
3. All referenced components are defined
4. Port numbers are in valid range (1-65535)
5. URLs have correct format
6. Time durations have units (s, m, h, d)

### Common Issues

**YAML syntax error**: Use a YAML linter to identify the issue
```bash
yamllint config/otel/collector.yaml
```

**Missing section**: Add required section to config file

**Invalid reference**: Ensure all pipeline/component references exist in their respective sections

**Invalid port**: Use a port number between 1 and 65535

**Invalid URL**: Ensure URLs start with http:// or https://

## Best Practices

1. **Run tests before committing**: Catch errors early
2. **Keep tests focused**: One test per validation rule
3. **Use descriptive test names**: Make failures easy to understand
4. **Add helpful error messages**: Include context in assertions
5. **Test both positive and negative cases**: Validate both valid and invalid configs
6. **Keep fixtures up-to-date**: Ensure test fixtures match actual configurations

## Future Enhancements

Potential improvements:
- [ ] Add negative test fixtures (invalid configurations)
- [ ] Add JSON schema validation
- [ ] Add custom validators for complex rules
- [ ] Generate validation reports
- [ ] Add performance benchmarks
- [ ] Validate cross-component relationships
- [ ] Add mutation testing for test coverage
