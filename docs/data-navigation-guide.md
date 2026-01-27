# Observability Data Navigation Guide

## Quick Summary: Where Your Data Is

| Data Type | Storage | Status | View In Grafana |
|-----------|---------|--------|-----------------|
| **Metrics** | Prometheus | ✅ **Active** | Explore → Prometheus |
| **Logs** | Loki | ⚠️ **Limited** | Explore → Loki |
| **Traces** | Tempo | ⚠️ **Not Yet** | Explore → Tempo |
| **Alerts** | Alertmanager | ✅ **Active** | Alerting → Alert Rules |

---

## 1. METRICS (Prometheus) ✅

### What's Being Collected

Your observability stack is actively collecting **internal infrastructure metrics**:

```
Obstackd Stack Metrics:
├─ Prometheus (self-monitoring)
│  ├─ prometheus_tsdb_symbol_table_size_bytes
│  ├─ prometheus_tsdb_data_compaction_duration_seconds
│  └─ prometheus_sd_discovered_targets
├─ OpenTelemetry Collector
│  ├─ otelcol_exporter_queue_size
│  ├─ otelcol_http_server_duration
│  └─ otelcol_receiver_accepted_spans
├─ Alertmanager
│  ├─ alertmanager_alerts
│  ├─ alertmanager_notifications_total
│  └─ alertmanager_config_last_reload_successful
└─ Loki/Tempo/Grafana (system metrics)
```

### How to View Metrics in Grafana

**Method 1: Pre-made Dashboards**

1. Open http://localhost:3000
2. Left sidebar → **Dashboards**
3. Select one of:
   - **"Observability Stack Health"** ← START HERE (shows collector & infrastructure)
   - **"Prometheus"** (Prometheus internal metrics)
   - **"OTel Collector"** (collector performance)
   - **"Infrastructure Overview"** (system-level metrics)

**Method 2: Ad-hoc Exploration**

1. Open http://localhost:3000
2. Left sidebar → **Explore**
3. Top left dropdown → Select **"Prometheus"**
4. In query box, try:
   ```
   up{job="prometheus"}
   ```
5. Or search available metrics:
   ```
   up
   ```
   This shows which targets are running.

**Available Prometheus Queries**

```promql
# Infrastructure health
up{job="prometheus"}                          # Prometheus itself
up{job="otel-collector"}                      # OTel Collector
up{job="alertmanager"}                        # Alertmanager
up{job="otel-app-metrics"}                    # App metrics via OTel

# OTel Collector internals
rate(otelcol_exporter_queue_size[5m])         # Queue depth over time
otelcol_http_server_duration_count            # HTTP request count
increase(otelcol_exporter_sent_spans[5m])     # Spans sent to exporters

# Prometheus internals
prometheus_tsdb_symbol_table_size_bytes       # Database size
prometheus_sd_discovered_targets              # Service discovery targets
```

---

## 2. LOGS (Loki) ⚠️ Limited

### Current Status: Empty

Loki exists but has **no log data yet** because:

- **Obstackd containers** don't send structured logs to Loki (they log to stdout/stderr)
- **Media-Refinery** logs to stdout via Docker, not to Loki
- **Promtail** (log collector) is running but not configured to ship container logs

### How to Enable Log Collection

**Option A: Quick Fix - Ship Docker Logs (Recommended)**

Edit `config/promtail/promtail.yaml` to scrape Docker logs:

```yaml
scrape_configs:
  - job_name: docker-logs
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        target_label: 'container_name'
      - source_labels: ['__meta_docker_container_labels_com_docker_compose_service']
        target_label: 'service'
```

Then:
```bash
docker compose restart promtail
```

**Option B: Recommended - Configure OTel to Send Logs**

Update `config/otel/collector.yaml` to enable log reception:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

pipelines:
  logs:
    receivers: [otlp]
    processors: [memory_limiter, batch]
    exporters: [loki, debug]
```

### Viewing Logs in Grafana

1. http://localhost:3000
2. Left sidebar → **Explore**
3. Top left dropdown → **"Loki"**
4. Try queries like:
   ```
   {job="promtail"}                    # All promtail logs
   {container_name="media-refinery"}   # Specific container
   {service="media-processing"}        # By service label
   ```

---

## 3. TRACES (Tempo) ⚠️ Not Yet Implemented

### Current Status: Empty

Tempo is running but has **no traces** because:

- **Media-Refinery** does NOT have OpenTelemetry SDK in its code
- Environment variables alone don't generate traces
- You need code instrumentation to emit traces

### Trace Requirements

To send traces, Media-Refinery would need:

1. **OpenTelemetry SDK for Go** installed
2. **Instrumentation code** like:
   ```go
   import "go.opentelemetry.io/otel"
   import "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
   
   // Initialize exporter
   exporter, _ := otlptracehttp.New(ctx)
   tracer := otel.Tracer("media-refinery")
   
   // In your code:
   ctx, span := tracer.Start(ctx, "process_file")
   defer span.End()
   ```

3. **Rebuild Media-Refinery** with this instrumentation

### How to View Traces (When Available)

1. http://localhost:3000
2. Left sidebar → **Explore**
3. Top left dropdown → **"Tempo"**
4. Click "Search" button (top right)
5. Will show traces by:
   - Service name (media-refinery)
   - Operation name
   - Duration
   - Status

---

## 4. ALERTS (Alertmanager) ✅

### Current Status: Active

Pre-configured alert rules are in place.

### Viewing Alerts in Grafana

1. http://localhost:3000
2. Left sidebar → **Alerting** → **Alert rules**
3. Shows current alert status
4. Check `config/prometheus/alerts.yml` for rule definitions

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   OBSTACKD STACK                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐         ┌──────────────────┐        │
│  │   Prometheus │◄────────┤  OTel Collector  │        │
│  │  (Metrics)   │         │  (Telemetry)     │        │
│  └──────────────┘         └──────────────────┘        │
│         ▲                           ▲                  │
│         │                           │                  │
│         └───────────┬───────────────┘                  │
│                     │                                  │
│              Scrapes every 15s                         │
│                                                         │
│  ┌──────────────┐    ┌──────────┐    ┌──────────┐    │
│  │    Loki      │    │  Tempo   │    │ Grafana  │    │
│  │   (Logs)     │    │ (Traces) │    │  (UI)    │    │
│  └──────────────┘    └──────────┘    └──────────┘    │
│         ▲                 ▲                            │
│         │                 │                            │
│         └────────┬────────┘                            │
│                  │                                     │
│           Receives via OTLP                            │
│           (from OTel Collector)                        │
│                                                        │
└─────────────────────────────────────────────────────────┘
                      ▲
                      │ observability-lab network
                      │
         ┌────────────┴────────────┐
         │                         │
    ┌────▼──────┐          ┌──────▼────┐
    │   MEDIA   │          │   OTHER   │
    │ REFINERY  │          │   APPS    │
    │  STACK    │          │   STACK   │
    └───────────┘          └───────────┘
```

---

## What to Look At First

### 1. **Observability Stack Health Dashboard** (START HERE)

This shows the health of Obstackd itself:

```
✓ Click: Dashboards → Observability Stack Health
Shows:
- OTel Collector status
- Receiver metrics
- Exporter metrics
- Memory usage
- Uptime
```

### 2. **Prometheus Targets**

Verify what's being scraped:

```
In Grafana:
✓ Menu → Configuration → Data sources → Prometheus
✓ Click "Explore"
✓ Query: up
Should show 4 targets UP:
- prometheus (self)
- otel-collector (metrics)
- alertmanager
- otel-app-metrics
```

### 3. **Metric Explorer**

Try these to understand available data:

```promql
# Show all metric names
{__name__=~".+"}

# OTel Collector workload
rate(otelcol_exporter_queue_size[5m])
otelcol_http_server_duration_count

# System health
up{job=~"prometheus|alertmanager|otel-collector"}

# Container info
count(up) by (job)
```

---

## Troubleshooting: "Why don't I see X?"

### "No Logs in Loki"
- **Root cause**: Promtail not configured to scrape Docker logs
- **Fix**: See "Option A" under LOGS section above
- **Verification**: 
  ```bash
  curl http://localhost:3100/loki/api/v1/label/job/values
  # Should return something other than empty
  ```

### "No Traces in Tempo"
- **Root cause**: Media-Refinery code doesn't have OTel SDK
- **Fix**: Add OpenTelemetry instrumentation to Media-Refinery Go code
- **Verification**:
  ```bash
  curl http://localhost:3200/api/traces
  # Should return some traces (if instrumented)
  ```

### "Metrics Missing from Prometheus"
- **Root cause**: Target not in scrape config
- **Fix**: Add to `config/prometheus/prometheus.yaml`
- **Verification**:
  ```bash
  curl 'http://localhost:9090/api/v1/targets' | jq '.data.activeTargets'
  ```

### "Grafana Shows Empty Dashboards"
- **Root cause**: Dashboard queries don't match available metrics
- **Fix**: 
  1. Go to Explore
  2. Try a simple query like `up`
  3. Edit dashboard panels to use correct metric names
- **Verification**:
  ```bash
  curl 'http://localhost:9090/api/v1/labels' | jq '.data | length'
  # Should show > 40
  ```

---

## Next Steps

### Phase 1: Enable Full Data Collection (This Week)

- [ ] Configure Promtail to collect Docker logs
- [ ] Verify logs appear in Loki
- [ ] Create dashboard for Media-Refinery logs

### Phase 2: Add Instrumentation (Next Week)

- [ ] Add OpenTelemetry SDK to Media-Refinery
- [ ] Emit traces for file processing operations
- [ ] Create trace visualization dashboard

### Phase 3: Custom Metrics (Optional)

- [ ] Add Prometheus metrics to Media-Refinery
- [ ] Track processing times, file counts, success rates
- [ ] Create custom Grafana dashboards

---

## Quick API Tests

### Test Prometheus
```bash
curl 'http://localhost:9090/api/v1/targets'
curl 'http://localhost:9090/api/v1/labels'
curl 'http://localhost:9090/api/v1/query?query=up'
```

### Test Loki
```bash
curl 'http://localhost:3100/loki/api/v1/labels'
curl 'http://localhost:3100/loki/api/v1/label/job/values'
```

### Test Tempo
```bash
curl 'http://localhost:3200/api/traces'
curl 'http://localhost:3200/api/search'
```

### Test OTel Collector Metrics
```bash
curl 'http://localhost:8888/metrics' | grep -i otelcol
curl 'http://localhost:8889/metrics' | head -20
```

---

## Summary Table

| Component | URL | Data | Action |
|-----------|-----|------|--------|
| Prometheus | `http://localhost:9090` | Infrastructure metrics | ✅ Viewing now |
| Grafana | `http://localhost:3000` | Dashboards | ✅ Use this |
| Loki | `http://localhost:3100` | Logs | ⚠️ Configure Promtail |
| Tempo | `http://localhost:3200` | Traces | ⚠️ Instrument code |
| OTel Collector | `http://localhost:4317/4318` | OTLP receiver | ✅ Ready for data |
| Alertmanager | `http://localhost:9093` | Alerts | ✅ Configured |

