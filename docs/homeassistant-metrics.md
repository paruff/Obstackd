# Home Assistant Metrics Documentation

This document describes the expected metrics from Home Assistant when integrated with the Obstackd observability platform.

## Metrics Endpoint

**URL:** `http://homeassistant:8123/api/prometheus`  
**Format:** Prometheus text format  
**Authentication:** None required (configured in http component)

## Metric Categories

### 1. Entity Metrics

Home Assistant exposes metrics for entities across different domains (sensor, switch, light, etc.):

#### `homeassistant_entity_available`

**Type:** Gauge  
**Description:** Entity availability status  
**Labels:**
- `domain` - Entity domain (sensor, switch, light, etc.)
- `entity` - Full entity ID
- `friendly_name` - Human-readable entity name

**Values:**
- `1` - Entity is available
- `0` - Entity is unavailable

**Example:**
```prometheus
homeassistant_entity_available{domain="sensor",entity="sensor.test_sensor_1",friendly_name="Test Sensor 1"} 1
```

### 2. Sensor Metrics

For each numeric sensor, Home Assistant exports the current state value:

#### `homeassistant_sensor_<unit>_<name>`

**Type:** Gauge  
**Description:** Current sensor value  
**Labels:**
- `entity` - Full entity ID
- `friendly_name` - Human-readable entity name
- Additional domain-specific labels

**Example:**
```prometheus
homeassistant_sensor_units_test_sensor_1{entity="sensor.test_sensor_1",friendly_name="Test Sensor 1"} 42
```

### 3. Automation Metrics

Metrics related to automation execution:

#### Automation Trigger Counts

**Description:** Number of times automations have been triggered  
**Labels:**
- `automation_id` - Automation identifier
- `friendly_name` - Automation name

### 4. System Metrics

#### API Metrics

Metrics about API calls and performance (if enabled):

- Request counts
- Response times
- Error rates

### 5. Integration Metrics

Status and health of various Home Assistant integrations:

- Integration load status
- Error counts per integration
- Component states

## Baseline Metrics for Testing

The following metrics are guaranteed to be present in the test configuration:

### Minimum Test Configuration

**Configuration File:** `config/homeassistant/configuration.yaml`

**Test Entities:**
- 2 template sensors (`sensor.test_sensor_1`, `sensor.test_sensor_2`)
- 2 time/date sensors
- 2 automations (`Test Automation 1`, `Test Automation 2`)

**Expected Minimum Metrics:**

1. Entity availability metrics (at least 4 entities)
2. Sensor value metrics (at least 2 numeric sensors)
3. System health indicators

## Prometheus Integration Configuration

Home Assistant's Prometheus integration is configured in `configuration.yaml`:

```yaml
prometheus:
  namespace: homeassistant
```

This adds the `homeassistant_` prefix to all exported metrics.

## Scrape Configuration

Prometheus is configured to scrape Home Assistant in `config/prometheus/prometheus.yaml`:

```yaml
scrape_configs:
  - job_name: 'homeassistant'
    static_configs:
      - targets: ['homeassistant:8123']
        labels:
          component: 'homeassistant'
          service: 'home-automation'
    scrape_interval: 30s
    metrics_path: '/api/prometheus'
```

## Common Metric Labels

All Home Assistant metrics scraped by Prometheus will include:

### Prometheus-Added Labels

- `job="homeassistant"` - Scrape job name
- `instance="homeassistant:8123"` - Target instance
- `component="homeassistant"` - Component label (custom)
- `service="home-automation"` - Service label (custom)

### Home Assistant-Added Labels

- `entity` - Entity ID (for entity-specific metrics)
- `friendly_name` - Human-readable name
- `domain` - Entity domain (sensor, switch, etc.)

## Metric Name Conventions

Home Assistant follows these naming conventions:

1. **Prefix:** All metrics start with `homeassistant_`
2. **Category:** Next component indicates metric category (entity, sensor, etc.)
3. **Type/Name:** Specific metric type or measurement
4. **Suffix:** Unit or qualifier (if applicable)

**Examples:**
- `homeassistant_entity_available` - Entity availability
- `homeassistant_sensor_units_temperature` - Temperature sensor value
- `homeassistant_switch_state` - Switch state (on/off)

## Validation Checklist

When validating Home Assistant metrics integration:

- [ ] Metrics endpoint (`/api/prometheus`) is accessible
- [ ] Metrics are in valid Prometheus text format
- [ ] HELP and TYPE comments are present (optional but recommended)
- [ ] At least one `homeassistant_entity_available` metric exists
- [ ] Sensor value metrics are present for configured sensors
- [ ] Prometheus scrapes successfully (`up{job="homeassistant"}=1`)
- [ ] Metrics appear in Prometheus with correct labels
- [ ] Metric values are reasonable (no NaN, no extremely large values)

## Troubleshooting

### No Metrics Exported

**Symptoms:** Empty response from `/api/prometheus`

**Possible Causes:**
1. Prometheus integration not configured
2. Home Assistant not fully started
3. Configuration error in `configuration.yaml`

**Resolution:**
1. Check `configuration.yaml` has `prometheus:` section
2. Wait for HA to complete startup (check logs)
3. Validate configuration with `hass --script check_config`

### Metrics Not in Prometheus

**Symptoms:** Metrics visible at HA endpoint but not in Prometheus

**Possible Causes:**
1. Prometheus not configured to scrape HA
2. Network connectivity issues
3. Scrape timeout

**Resolution:**
1. Check Prometheus targets: `http://localhost:9090/targets`
2. Verify target is "up" and health is green
3. Check Prometheus logs for scrape errors
4. Increase scrape_timeout if needed

### Missing Entity Metrics

**Symptoms:** Some entities don't have metrics

**Possible Causes:**
1. Entities not fully initialized
2. Domain not supported by Prometheus integration
3. Entity unavailable

**Resolution:**
1. Wait for all entities to become available
2. Check entity state in Home Assistant UI
3. Verify entity domain is supported

## References

- [Home Assistant Prometheus Integration Docs](https://www.home-assistant.io/integrations/prometheus/)
- [Prometheus Metric Types](https://prometheus.io/docs/concepts/metric_types/)
- [Prometheus Text Format](https://prometheus.io/docs/instrumenting/exposition_formats/)

## Version Information

- **Home Assistant Version:** 2024.1.5
- **Prometheus Integration:** Built-in (included in default_config)
- **Last Updated:** 2026-01-26
