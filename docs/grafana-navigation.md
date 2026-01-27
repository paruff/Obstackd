# Grafana Navigation: Where to Find Your Data

## TL;DR - Start Here in Grafana

**URL:** http://localhost:3000

**Quick Navigation Map:**

```
Grafana Home
├─ Dashboards (left sidebar)
│  ├─ 📊 Observability Stack Health  ← START HERE (shows all infrastructure)
│  ├─ 📊 OTel Collector             ← Collector performance
│  ├─ 📊 Prometheus                 ← Metrics database health
│  ├─ 📊 Application Performance    ← App metrics (when available)
│  └─ 📊 Infrastructure Overview    ← System-level metrics
│
├─ Explore (left sidebar)
│  ├─ Prometheus datasource → Query metrics
│  ├─ Loki datasource → Search logs
│  └─ Tempo datasource → Find traces
│
└─ Alerting (left sidebar)
   └─ Alert rules → See configured alerts
```

---

## 1. METRICS (Prometheus) ✅ LIVE

### What You Have Right Now

✅ **Infrastructure metrics are actively being collected:**
- Prometheus internal metrics
- OpenTelemetry Collector performance
- Alertmanager metrics
- Loki, Tempo, Grafana system metrics

### Best Dashboard for Metrics

**Go to:** `Dashboards` → `Observability Stack Health`

This shows:
- OTel Collector receiver/exporter status
- Queue depths and processing rates
- Memory usage
- Uptime and health checks

### Alternative: Query Raw Metrics

**Go to:** `Explore` (left sidebar)
1. Select **Prometheus** datasource (top dropdown)
2. Try queries:
   ```promql
   up                              # Show all targets
   up{job="otel-collector"}        # Collector health
   rate(otelcol_exporter_queue_size[5m])  # Processing rate
   ```

### Available Prometheus Scrape Jobs

```
✓ prometheus        - Prometheus self-monitoring
✓ otel-collector    - OTel Collector internal metrics
✓ otel-app-metrics  - App metrics exported by OTel
✓ alertmanager      - Alert management
```

---

## 2. LOGS (Loki) ✅ NOW ACTIVE

### What's New

**✅ FIXED:** Promtail upgraded to v3.0.0 - Docker logs now flowing!

### What Logs You Have

All container logs from both stacks:
- **Obstackd services:** prometheus, loki, tempo, grafana, otel-collector, alertmanager
- **Media-Refinery services:** media-refinery, beets, tdarr, radarr, sonarr, plex

### How to View Logs in Grafana

**Go to:** `Explore` (left sidebar)
1. Select **Loki** datasource (top dropdown)
2. Click **Log browser** (left panel)
3. Select label filters:
   - **compose_service** = "media-refinery" (to see app logs)
   - **compose_project** = "media-refinery_" or "observability-lab"
   - **stream** = "stdout" or "stderr"

### Log Query Examples

```
# All logs from media-refinery
{compose_service="media-refinery"}

# All error logs
{stream="stderr"}

# Specific container
{container="otel-collector"}

# By compose project
{compose_project="media-refinery_"}
```

### Available Log Labels

From the log browser, you can filter by:
- `compose_service` - Service name (media-refinery, prometheus, etc.)
- `compose_project` - Which docker-compose project
- `stream` - stdout or stderr
- `container` - Container name
- `job` - Always "docker" for container logs

---

## 3. TRACES (Tempo) ⚠️ Not Yet (Requires Code Changes)

### Current Status

Tempo is running but **has no traces** because:
- Media-Refinery code doesn't emit OpenTelemetry traces
- Environment variables alone don't generate traces
- Requires code instrumentation

### To View Traces (When Available)

**Go to:** `Explore` (left sidebar)
1. Select **Tempo** datasource
2. Click **Search** button
3. Will search for traces by service, operation, duration

### How to Enable Traces

See [Media-Refinery Integration Guide](../examples/media-refinery-integration.md#enabling-traces) for adding OpenTelemetry SDK to Go code.

---

## STEP-BY-STEP: View Media-Refinery Logs

### 1. Go to Grafana
```
http://localhost:3000
```

### 2. Click "Explore" in left sidebar
```
(you'll see a query interface)
```

### 3. Change datasource to "Loki"
```
Top-left dropdown where it shows "Prometheus"
```

### 4. Click "Log browser"
```
Left sidebar expands to show labels
```

### 5. Select filters:
```
compose_service = "media-refinery"
```

### 6. Click "Show logs"
```
You'll see media-refinery logs in the center panel
```

### 7. (Optional) Filter by time:
```
Top-right time picker → Last hour, Last day, etc.
```

---

## STEP-BY-STEP: Check Infrastructure Health

### 1. Go to Grafana
```
http://localhost:3000
```

### 2. Click "Dashboards" in left sidebar
```
Shows list of pre-made dashboards
```

### 3. Click "Observability Stack Health"
```
Opens dashboard showing all system metrics
```

### 4. Review metrics:
```
- OTel Collector: Status of receivers/exporters
- Queue depths: How much data is being processed
- Memory: RAM usage of each service
- Uptime: How long each service has been running
```

---

## STEP-BY-STEP: Query Prometheus Metrics

### 1. Go to Grafana
```
http://localhost:3000
```

### 2. Click "Explore" in left sidebar
```
```

### 3. Make sure "Prometheus" is selected (top dropdown)
```
```

### 4. In the query box, type a metric:
```promql
up
```
```

### 5. Click "Run query" button (or Ctrl+Shift+Enter)
```
Shows all targets and their status (0=down, 1=up)
```

### 6. Try other queries:
```promql
rate(otelcol_http_server_duration_count[5m])
otelcol_exporter_queue_size
up{job="otel-collector"}
```

---

## Troubleshooting

### "I don't see any logs in Loki"

**Solution:**
1. Check that logs are being shipped:
   ```bash
   curl 'http://localhost:3100/loki/api/v1/label/compose_service/values'
   ```
   Should show: ["alertmanager", "media-refinery", "prometheus", ...]

2. If empty, check promtail status:
   ```bash
   docker logs promtail --tail 20
   ```
   Should see: `msg="successfully sent entries to loki"`

3. If errors, restart:
   ```bash
   docker compose restart promtail
   ```

### "I don't see Media-Refinery logs specifically"

**Solution:**
1. Make sure Media-Refinery is running:
   ```bash
   docker ps | grep media-refinery
   ```

2. Check it's on observability-lab network:
   ```bash
   docker inspect media-refinery | grep observability-lab
   ```

3. In Grafana Explore, try this query:
   ```
   {job="docker"}
   ```
   This shows ALL logs. Look for media-refinery entries.

### "Prometheus shows no targets"

**Solution:**
1. Check targets are configured:
   ```bash
   curl 'http://localhost:9090/api/v1/targets'
   ```

2. Verify Prometheus config:
   ```bash
   cat config/prometheus/prometheus.yaml
   ```

3. Check scrape targets manually:
   ```bash
   docker logs prometheus --tail 20
   ```

---

## Data Storage Locations

| Data | Storage | View In |
|------|---------|---------|
| **Metrics** | `/data/prometheus` | Prometheus UI or Grafana |
| **Logs** | `/data/loki` | Loki API or Grafana |
| **Traces** | `/data/tempo` | Tempo API or Grafana |

---

## API Endpoints (For Advanced Users)

### Prometheus
- List all metrics: `curl http://localhost:9090/api/v1/labels`
- Query metric: `curl 'http://localhost:9090/api/v1/query?query=up'`
- List targets: `curl http://localhost:9090/api/v1/targets`

### Loki
- List labels: `curl http://localhost:3100/loki/api/v1/labels`
- Query logs: `curl 'http://localhost:3100/loki/api/v1/query?query=%7Bjob%3D%22docker%22%7D'`
- Check sources: `curl http://localhost:3100/loki/api/v1/label/compose_service/values`

### Tempo
- Search traces: `curl http://localhost:3200/api/search`
- Get trace: `curl http://localhost:3200/api/traces/{traceID}`

---

## What's Working vs. What Needs Setup

| Component | Status | Next Step |
|-----------|--------|-----------|
| ✅ Prometheus metrics | Active | View in Dashboards |
| ✅ Loki logs | Active (JUST FIXED) | Go to Explore → Loki |
| ⚠️ Tempo traces | Waiting for instrumentation | Add OTel SDK to code |
| ✅ Alertmanager | Active | View in Alerting |
| ✅ Grafana | Active | Use as UI |

---

## Next: Enable Traces

To see traces from Media-Refinery, follow: [Instrumentation Guide](../examples/media-refinery-integration.md#enabling-traces)

Key requirement: Media-Refinery code needs OpenTelemetry SDK added and initialized.

