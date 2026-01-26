# Alertmanager Service Operations Guide

## Overview

This document provides operational guidance for the Alertmanager service in the Obstackd observability stack. Alertmanager handles alerts sent by Prometheus and routes them to the appropriate notification channels.

## Service Access

| Endpoint | URL | Purpose |
|----------|-----|---------|
| **Web UI** | http://localhost:9093 | Alert management interface |
| **Metrics** | http://localhost:9093/metrics | Alertmanager self-monitoring metrics |
| **Health Check** | http://localhost:9093/-/healthy | Liveness probe |
| **Ready Check** | http://localhost:9093/-/ready | Readiness probe |
| **API** | http://localhost:9093/api/v2/* | Alert management API |

## Common Operations

### Starting the Service

```bash
# Start Alertmanager with the core profile
docker compose --profile core up -d alertmanager

# Verify it's running
docker compose ps alertmanager
```

### Checking Service Health

```bash
# Check if Alertmanager is healthy
curl -f http://localhost:9093/-/healthy

# Check if Alertmanager is ready to serve requests
curl -f http://localhost:9093/-/ready

# Check container health status
docker compose ps --format "table {{.Service}}\t{{.Status}}" alertmanager
```

### Reloading Configuration

Alertmanager supports hot-reload of configuration without restarting:

```bash
# Reload configuration
curl -X POST http://localhost:9093/-/reload

# Check if the reload was successful
docker compose logs alertmanager --tail=20
```

### Viewing Active Alerts

```bash
# Get all active alerts via API
curl -s http://localhost:9093/api/v2/alerts | jq .

# Get alerts filtered by state
curl -s "http://localhost:9093/api/v2/alerts?filter=state%3Dactive" | jq .

# Get silences
curl -s http://localhost:9093/api/v2/silences | jq .
```

### Creating a Silence

```bash
# Create a silence via API (example)
curl -X POST http://localhost:9093/api/v2/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      {
        "name": "alertname",
        "value": "ServiceDown",
        "isRegex": false
      }
    ],
    "startsAt": "2024-01-01T00:00:00Z",
    "endsAt": "2024-01-01T01:00:00Z",
    "createdBy": "operator",
    "comment": "Maintenance window"
  }'
```

### Viewing Logs

```bash
# View recent logs
docker compose logs alertmanager --tail=50

# Follow logs in real-time
docker compose logs -f alertmanager

# View logs with timestamps
docker compose logs alertmanager --timestamps
```

## Alert Runbooks

### ServiceDown

**Severity:** Critical  
**Category:** Availability

**Description:** A monitored service has been down for more than 2 minutes.

**Investigation Steps:**

1. Check which service is down:
   ```bash
   curl -s http://localhost:9093/api/v2/alerts | jq '.[] | select(.labels.alertname=="ServiceDown")'
   ```

2. Check the service status:
   ```bash
   docker compose ps
   ```

3. View service logs:
   ```bash
   docker compose logs <service-name> --tail=100
   ```

4. Check container health:
   ```bash
   docker inspect <container-name> | jq '.[0].State.Health'
   ```

**Resolution:**

- If the service crashed, restart it:
  ```bash
  docker compose restart <service-name>
  ```

- If there are configuration issues, fix the config and reload:
  ```bash
  # Fix config file
  docker compose restart <service-name>
  ```

### OTelCollectorDown

**Severity:** Critical  
**Category:** Observability

**Description:** The OpenTelemetry Collector has been down for more than 1 minute. This affects all telemetry data collection.

**Investigation Steps:**

1. Check OTel Collector status:
   ```bash
   docker compose ps otel-collector
   ```

2. View OTel Collector logs:
   ```bash
   docker compose logs otel-collector --tail=100
   ```

3. Verify configuration:
   ```bash
   docker compose exec otel-collector cat /etc/otel/collector.yaml
   ```

**Resolution:**

- Restart the OTel Collector:
  ```bash
  docker compose restart otel-collector
  ```

- If configuration is invalid, fix and restart:
  ```bash
  # Edit config/otel/collector.yaml
  docker compose restart otel-collector
  ```

### PrometheusScrapeFailure

**Severity:** Warning  
**Category:** Monitoring

**Description:** Prometheus has failed to scrape a target for more than 5 minutes.

**Investigation Steps:**

1. Check scrape targets in Prometheus UI:
   - Navigate to http://localhost:9090/targets

2. Verify network connectivity:
   ```bash
   docker compose exec prometheus wget -O- http://<target-service>:<port>/metrics
   ```

3. Check target service logs:
   ```bash
   docker compose logs <target-service>
   ```

**Resolution:**

- If the target service is down, restart it
- If the metrics endpoint is misconfigured, update the Prometheus configuration
- If it's a network issue, check Docker network connectivity

### OTelCollectorHighCPU

**Severity:** Warning  
**Category:** Resource

**Description:** OpenTelemetry Collector is using more than 80% of a CPU core for over 10 minutes.

**Investigation Steps:**

1. Check OTel Collector CPU usage:
   ```bash
   docker stats otel-collector --no-stream
   ```

2. Review OTel Collector metrics:
   ```bash
   curl -s http://localhost:8888/metrics | grep cpu
   ```

3. Check for backpressure or excessive load:
   ```bash
   curl -s http://localhost:8888/metrics | grep queue
   ```

**Resolution:**

- If it's a temporary spike, monitor and wait for it to stabilize
- If it's sustained, consider:
  - Reviewing and optimizing OTel Collector pipeline configuration
  - Reducing batch sizes to decrease processing load
  - Increasing resource limits in compose.yaml
  - Scaling horizontally (if applicable)

### OTelCollectorHighMemory

**Severity:** Warning  
**Category:** Resource

**Description:** OTel Collector is using more than 3GB of memory for over 5 minutes.

**Investigation Steps:**

1. Check current memory usage:
   ```bash
   docker stats otel-collector --no-stream
   ```

2. Review OTel Collector metrics:
   ```bash
   curl -s http://localhost:8888/metrics | grep memory
   ```

3. Check for backpressure or queuing:
   ```bash
   curl -s http://localhost:8888/metrics | grep queue
   ```

**Resolution:**

- Restart the OTel Collector to clear memory:
  ```bash
  docker compose restart otel-collector
  ```

- If the issue persists:
  - Review and optimize OTel Collector configuration
  - Increase memory limits in compose.yaml
  - Add batch processor settings to reduce memory usage

### PrometheusTSDBReloadsFailing

**Severity:** Warning  
**Category:** Storage

**Description:** Prometheus has had TSDB reload failures.

**Investigation Steps:**

1. Check Prometheus logs:
   ```bash
   docker compose logs prometheus --tail=100 | grep -i reload
   ```

2. Verify TSDB health:
   ```bash
   curl -s http://localhost:9090/api/v1/status/tsdb | jq .
   ```

**Resolution:**

- If disk space is low, free up space
- If TSDB is corrupted, consider:
  ```bash
  # Stop Prometheus
  docker compose stop prometheus
  
  # Backup data
  cp -r data/prometheus data/prometheus.backup
  
  # Restart Prometheus
  docker compose start prometheus
  ```

### PrometheusSlowQueries

**Severity:** Warning  
**Category:** Performance

**Description:** 99th percentile of Prometheus query duration is above 5 seconds.

**Investigation Steps:**

1. Identify slow queries in Prometheus UI:
   - Navigate to http://localhost:9090/graph
   - Use query: `topk(10, prometheus_engine_query_duration_seconds)`

2. Check for large result sets or complex queries

**Resolution:**

- Optimize queries by:
  - Using more specific label matchers
  - Reducing time ranges
  - Using recording rules for complex queries
- Consider increasing Prometheus resources

### PrometheusStorageAlmostFull

**Severity:** Warning  
**Category:** Storage

**Description:** Prometheus storage is over 80% full.

**Investigation Steps:**

1. Check current storage usage:
   ```bash
   du -sh data/prometheus
   ```

2. Review retention settings in compose.yaml

**Resolution:**

- Decrease retention time:
  ```yaml
  # In compose.yaml
  - "--storage.tsdb.retention.time=15d"  # Reduce from 30d
  ```

- Increase storage volume size
- Clean up old data if necessary

### AlertmanagerConfigReloadFailed

**Severity:** Warning  
**Category:** Alerting

**Description:** Alertmanager configuration reload has failed.

**Investigation Steps:**

1. Check Alertmanager logs:
   ```bash
   docker compose logs alertmanager --tail=50
   ```

2. Validate configuration:
   ```bash
   docker compose exec alertmanager amtool check-config /etc/alertmanager/alertmanager.yml
   ```

**Resolution:**

- Fix the configuration file at `config/alertmanager/alertmanager.yml`
- Reload the configuration:
  ```bash
  curl -X POST http://localhost:9093/-/reload
  ```

### AlertmanagerClusterDown

**Severity:** Critical  
**Category:** Alerting

**Description:** No Alertmanager instances are reachable. Alert notifications are not being sent.

**Investigation Steps:**

1. Check Alertmanager status:
   ```bash
   docker compose ps alertmanager
   ```

2. View Alertmanager logs:
   ```bash
   docker compose logs alertmanager
   ```

**Resolution:**

- Restart Alertmanager:
  ```bash
  docker compose restart alertmanager
  ```

- If the issue persists, check for:
  - Configuration errors
  - Resource constraints
  - Network issues

## Troubleshooting

### Alerts Not Firing

1. Verify Prometheus is evaluating rules:
   ```bash
   curl -s http://localhost:9090/api/v1/rules | jq .
   ```

2. Check if alert rules are loaded:
   ```bash
   curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | select(.type=="alerting")'
   ```

3. Verify Alertmanager is reachable from Prometheus:
   ```bash
   docker compose exec prometheus wget -O- http://alertmanager:9093/-/healthy
   ```

### Notifications Not Being Sent

1. Check Alertmanager logs for errors:
   ```bash
   docker compose logs alertmanager | grep -i error
   ```

2. Verify webhook endpoint is reachable (if using webhook):
   ```bash
   docker compose exec alertmanager wget -O- http://host.docker.internal:5001/webhook
   ```

3. Review notification configuration in `config/alertmanager/alertmanager.yml`

### Silences Not Working

1. Verify silence is active:
   ```bash
   curl -s http://localhost:9093/api/v2/silences | jq .
   ```

2. Check silence matchers match the alert labels:
   ```bash
   curl -s http://localhost:9093/api/v2/alerts | jq '.[0].labels'
   ```

## Performance Tuning

### Memory Optimization

- Adjust group interval to reduce notification frequency:
  ```yaml
  route:
    group_interval: 10m  # Increase from 5m
  ```

### Storage Optimization

- Configure retention in compose.yaml:
  ```yaml
  volumes:
    - ./data/alertmanager:/alertmanager
  # Data is automatically cleaned up after 120 hours by default
  ```

## Monitoring Alertmanager

Key metrics to monitor:

```promql
# Alert processing rate
rate(alertmanager_alerts_received_total[5m])

# Notification success rate
rate(alertmanager_notifications_total{integration="webhook"}[5m])

# Notification latency
histogram_quantile(0.99, rate(alertmanager_notification_duration_seconds_bucket[5m]))

# Active silences
alertmanager_silences
```

## Security Considerations

1. **Authentication:** Alertmanager does not have built-in authentication. Use a reverse proxy for production.

2. **Webhook Security:** Ensure webhook endpoints use HTTPS and authentication.

3. **API Access:** Restrict access to the Alertmanager API in production environments.

## Backup and Recovery

### Backup Alertmanager Data

```bash
# Backup Alertmanager data directory
tar -czf alertmanager-backup-$(date +%Y%m%d).tar.gz data/alertmanager/
```

### Restore from Backup

```bash
# Stop Alertmanager
docker compose stop alertmanager

# Restore data
tar -xzf alertmanager-backup-YYYYMMDD.tar.gz -C .

# Start Alertmanager
docker compose start alertmanager
```

## Additional Resources

- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Alert Routing](https://prometheus.io/docs/alerting/latest/configuration/#route)
- [Notification Templates](https://prometheus.io/docs/alerting/latest/notification_examples/)
- [API Documentation](https://github.com/prometheus/alertmanager/blob/main/api/v2/openapi.yaml)
