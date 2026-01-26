# Test fixtures for configuration validation

This directory contains test fixtures used by the unit tests.

## Structure

```
fixtures/
├── otel/           # OpenTelemetry Collector fixtures
├── prometheus/     # Prometheus fixtures
├── grafana/        # Grafana fixtures
├── tempo/          # Tempo fixtures
└── loki/           # Loki fixtures
```

## Valid vs Invalid Fixtures

- `valid_*.yaml` - Valid configuration examples that should pass validation
- `invalid_*.yaml` - Invalid configuration examples that should fail validation

## Usage

Fixtures are used in negative testing to ensure validators correctly catch errors.

Example:
```python
def test_missing_receiver_fails():
    """Test that missing required receiver is caught."""
    with open(fixtures_dir / 'otel' / 'invalid_missing_receiver.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Should fail validation
    assert 'otlp' not in config.get('receivers', {})
```

## Adding Fixtures

1. Create a YAML file in the appropriate subdirectory
2. Name it descriptively (e.g., `invalid_missing_otlp_receiver.yaml`)
3. Add a comment at the top explaining what's wrong/right
4. Reference it in your test

## Example Fixtures

### Invalid Configuration Examples

These demonstrate common misconfigurations that should be caught:

#### OTel Collector
- Missing required OTLP receiver
- Invalid endpoint format
- Missing pipeline sections
- Undefined component references
- Wrong processor order

#### Prometheus
- Missing global section
- Invalid scrape_interval format
- Empty scrape_configs
- Missing job_name
- Invalid scheme

#### Grafana
- Missing apiVersion
- Duplicate datasource names
- Invalid URL format
- Missing required datasources

#### Tempo
- Invalid port numbers
- Missing required sections
- Invalid storage backend
- Missing endpoint

#### Loki
- Invalid auth_enabled type
- Missing schema_config
- Invalid store type
- Invalid retention format
