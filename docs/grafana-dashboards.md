# Grafana Dashboards Documentation

This document describes the pre-built Grafana dashboards included in the Obstackd observability platform.

## Overview

Obstackd includes 4 pre-built dashboards that provide comprehensive monitoring across the entire observability stack:

1. **Observability Stack Health** - Monitor the health of core observability components
2. **IoT Devices & MQTT** - Monitor IoT device connectivity and MQTT broker
3. **Application Performance** - Monitor application RED metrics and traces
4. **Infrastructure Overview** - Monitor container and host resources

All dashboards are:
- ✅ Auto-provisioned on startup
- ✅ Stored in version control
- ✅ Pre-configured with variables for filtering
- ✅ Set to auto-refresh every 30 seconds
- ✅ Configured with 1-hour default time range

## Dashboard Details

### 1. Observability Stack Health

**UID:** `observability-stack-health`  
**Tags:** observability, monitoring, health

**Purpose:** Monitor the health and performance of the core observability stack components.

**Key Panels:**

**Stack Health Overview**
- **Service Status Panels** - Shows up/down status for:
  - Prometheus
  - OTel Collector
  - Loki
  - Tempo
  - Grafana
  - Alertmanager

**Prometheus Metrics**
- **Prometheus Scrape Targets** - Number of active scrape targets
- **Prometheus Query Rate** - Rate of queries executed
- **Prometheus Storage Size** - TSDB storage size over time
- **Prometheus Time Series Count** - Number of time series in Prometheus

**OpenTelemetry Collector Metrics**
- **OTel Collector - Metrics Received** - Rate of metrics received by receiver
- **OTel Collector - Spans Received** - Rate of spans received for tracing
- **OTel Collector - Logs Received** - Rate of log records received
- **OTel Collector - Metrics Exported** - Rate of metrics exported to backends

**Tempo & Loki Metrics**
- **Tempo - Trace Ingestion Rate** - Rate of spans ingested by Tempo
- **Loki - Log Ingestion Rate** - Rate of log entries ingested by Loki
- **Loki - Query Performance** - Query duration percentiles (p50, p95, p99)
- **Tempo - Storage Size** - Tempo storage size over time

**Queries Used:**
```promql
# Prometheus status
up{job="prometheus"}

# OTel Collector metrics received
rate(otelcol_receiver_accepted_metric_points{job="otel-collector"}[5m])

# Tempo trace ingestion
rate(tempo_distributor_spans_received_total{job="tempo"}[5m])

# Loki log ingestion
rate(loki_distributor_lines_received_total{job="loki"}[5m])
```

---

### 2. IoT Devices & MQTT

**UID:** `iot-devices-mqtt`  
**Tags:** iot, mqtt, devices

**Purpose:** Monitor IoT device connectivity and MQTT broker performance.

**Key Panels:**

**MQTT Broker Overview**
- **Active Connections** - Number of active MQTT client connections
- **Active Topics** - Number of active MQTT topics
- **Message Queue Depth** - Number of queued messages
- **Broker Status** - Up/down status indicator

**Message Traffic**
- **Message Rate by Topic** - Messages per second by topic
- **Message Bandwidth** - Bytes sent/received per second
- **Top Topics by Message Count** - Pie chart of most active topics
- **Retained Messages** - Count of retained messages over time

**Device Status**
- **Device Online Status** - Count of online vs offline devices
- **Devices by Type** - Pie chart showing device type distribution
- **Device Last Seen** - Time since each device was last seen (in minutes)

**Broker Performance**
- **Publish Latency** - MQTT publish latency percentiles (p50, p95, p99)
- **Broker Resource Usage** - CPU and memory usage of broker

**Variables:**
- `topic` - Filter by MQTT topic (multi-select)

**Queries Used:**
```promql
# Active connections
mqtt_broker_connections_active

# Message rate by topic
rate(mqtt_topic_messages_total[5m])

# Device online count
count(iot_device_online{status="online"})

# Publish latency
histogram_quantile(0.99, rate(mqtt_publish_duration_milliseconds_bucket[5m]))
```

---

### 3. Application Performance

**UID:** `application-performance`  
**Tags:** application, performance, red-metrics, traces

**Purpose:** Monitor application performance using RED (Rate, Errors, Duration) metrics and distributed tracing.

**Key Panels:**

**RED Metrics Overview**
- **Total Request Rate** - Requests per second across all services
- **Error Rate** - Percentage of failed requests (5xx errors)
- **p95 Latency** - 95th percentile request duration

**Request Rate (R)**
- **Request Rate by Service** - Requests per second per service
- **Request Rate by Endpoint** - Requests per second per endpoint

**Errors (E)**
- **Error Rate by Service** - Error percentage per service
- **Errors by Status Code** - Count of errors by HTTP status code (4xx, 5xx)

**Duration (D)**
- **Request Duration Percentiles** - p50, p95, p99 latency by service
- **Average Duration by Endpoint** - Average request duration per endpoint

**Tracing Metrics**
- **Trace Sampling Rate** - Percentage of traces sampled
- **Span Count per Trace** - Average number of spans per trace
- **Error Traces (Recent)** - Recent traces with errors (clickable to investigate)

**Variables:**
- `service` - Filter by service name (multi-select)

**Queries Used:**
```promql
# Request rate
sum(rate(http_requests_total[5m]))

# Error rate
(sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) * 100

# p95 latency
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# Trace sampling rate
(sum(rate(traces_sampled_total[5m])) / sum(rate(traces_total[5m]))) * 100
```

**TraceQL Query for Error Traces:**
```traceql
{status=error}
```

---

### 4. Infrastructure Overview

**UID:** `infrastructure-overview`  
**Tags:** infrastructure, containers, docker, resources

**Purpose:** Monitor Docker container resources, host metrics, and system health.

**Key Panels:**

**Infrastructure Overview**
- **Running Containers** - Total number of running containers
- **Total CPU Usage** - CPU usage percentage across all containers
- **Total Memory Usage** - Memory usage in bytes across all containers
- **Total Network I/O** - Network bandwidth (RX + TX)

**Container Resources**
- **Container CPU Usage** - CPU percentage per container
- **Container Memory Usage** - Memory usage per container
- **Container Network RX** - Network receive rate per container
- **Container Network TX** - Network transmit rate per container

**Host Metrics**
- **Host CPU Usage** - Host CPU utilization percentage
- **Host Memory Usage** - Host memory used vs available
- **Host Disk Usage** - Disk utilization percentage for root filesystem
- **Host Network I/O** - Host network RX/TX rates

**Container Status & Uptime**
- **Container Uptime** - Time since each container started
- **Docker Images in Use** - Pie chart of Docker images
- **Container Restart Count** - Number of restarts per container

**Variables:**
- `container` - Filter by container name (multi-select)

**Queries Used:**
```promql
# Running containers
count(container_last_seen)

# Container CPU usage
rate(container_cpu_usage_seconds_total{name=~"$container"}[5m]) * 100

# Host CPU usage
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Container uptime
time() - container_start_time_seconds{name=~"$container"}
```

---

## Using the Dashboards

### Accessing Dashboards

1. Open Grafana at http://localhost:3000
2. Login with credentials: `admin` / `admin`
3. Click on **Dashboards** in the left menu
4. All 5 dashboards will be available in the list

### Using Dashboard Variables

Most dashboards include variables for filtering data:

- **Time Range Variables** - Select preset time ranges (15m, 1h, 6h, etc.)
- **Service/Container Variables** - Filter by specific service or container
- **Topic Variables** - Filter MQTT topics in IoT dashboard

Variables appear at the top of each dashboard and update all panels when changed.

### Auto-Refresh

All dashboards are configured to auto-refresh every 30 seconds to show near real-time data.

To change the refresh interval:
1. Click the refresh icon in the top-right
2. Select a different interval or turn off auto-refresh

### Time Range Selection

Default time range is **1 hour** (`now-1h` to `now`).

To change the time range:
1. Click the time range selector in the top-right
2. Select a preset range or enter a custom range

---

## Dashboard Provisioning

Dashboards are automatically provisioned on Grafana startup via the provisioning configuration.

**Provisioning Config:** `config/grafana/provisioning/dashboards/dashboards.yaml`

```yaml
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: false
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: true
```

**Key Settings:**
- `disableDeletion: false` - Dashboards can be deleted from UI (but will be re-provisioned on restart)
- `allowUiUpdates: false` - UI changes are not persisted (GitOps-first approach)
- `updateIntervalSeconds: 10` - Check for dashboard updates every 10 seconds

---

## Troubleshooting

### Dashboards Not Appearing

1. **Check Grafana logs:**
   ```bash
   docker compose logs grafana | grep -i dashboard
   ```

2. **Verify dashboard files exist:**
   ```bash
   ls -la config/grafana/dashboards/
   ```

3. **Check provisioning config:**
   ```bash
   cat config/grafana/provisioning/dashboards/dashboards.yaml
   ```

### No Data in Panels

1. **Check datasource connection:**
   - Go to Configuration → Data Sources
   - Verify Prometheus, Tempo, and Loki are connected

2. **Check metrics are being scraped:**
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```

3. **Verify time range:**
   - Ensure the selected time range has data
   - Try expanding to "Last 24 hours"

### Panels Show "No Data"

This can happen when:
- Metrics don't exist yet (e.g., no MQTT traffic)
- Metric names have changed
- Service is not running or not being scraped

**Solutions:**
1. Start the missing service
2. Wait for at least one scrape cycle (30 seconds)
3. Check Prometheus targets are up: http://localhost:9090/targets

---

## Testing Dashboards

Run the integration tests to validate all dashboards:

```bash
# Start the stack
docker compose --profile core up -d

# Wait for services to be ready
sleep 30

# Run dashboard tests
pytest tests/integration/test_dashboards.py -v
```

**Expected Output:**
```
✅ Grafana is ready after 3 attempts
✅ All 4 dashboards are provisioned
✅ Observability Stack Health dashboard validated
✅ IoT Devices & MQTT dashboard validated
✅ Application Performance dashboard validated
✅ Infrastructure Overview dashboard validated
✅ All dashboards have auto-refresh configured
✅ All dashboards have time range configured
✅ Prometheus datasource is configured correctly
✅ Tempo datasource is configured correctly
✅ Loki datasource is configured correctly
```

---

## Customizing Dashboards

While the dashboards are pre-built and version-controlled, you can:

1. **Make temporary changes in Grafana UI:**
   - Changes are not persisted (due to `allowUiUpdates: false`)
   - Useful for testing new panels or queries

2. **Create custom dashboards:**
   - Create new dashboards in Grafana UI
   - These won't be version controlled
   - Store in a different folder to avoid conflicts

3. **Modify dashboard JSON files:**
   - Edit files in `config/grafana/dashboards/`
   - Restart Grafana to apply changes
   - Commit to version control

**Recommended Workflow:**
1. Test changes in Grafana UI
2. Export dashboard JSON
3. Update the file in `config/grafana/dashboards/`
4. Commit to git
5. Restart Grafana to verify

---

## Next Steps

- **Add custom panels** for your specific use case
- **Create alerts** based on dashboard metrics
- **Export dashboards** to share with team
- **Link dashboards** together for easy navigation
- **Add annotations** to mark deployments or incidents

---

## Related Documentation

- [Prometheus Operations](prometheus-operations.md)
- [Tempo Operations](tempo-operations.md)
- [Loki Operations](loki-operations.md)
- [Alertmanager Operations](alertmanager-operations.md)
