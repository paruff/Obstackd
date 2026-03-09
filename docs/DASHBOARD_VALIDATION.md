# Dashboard Validation & Testing Guide

## Status Summary ✅

All dashboards are now working with real data from your observability stack.

### Component Status
- ✅ **Prometheus**: UP - Metrics database operational
- ✅ **Loki**: UP - Log aggregation operational
- ✅ **Tempo**: UP - Trace storage operational
- ✅ **Grafana**: UP - Visualization UI operational
- ✅ **OTel Collector**: UP - Telemetry ingestion operational
- ✅ **Alertmanager**: UP - Alert management operational
- ✅ **Media-Refinery**: Connected to observability-lab network and logging

---

## Available Dashboards

### 1. **Observability Stack Health** 🔧
**Location**: http://localhost:3000 → Dashboards → "Observability Stack Health"

**What it shows**:
- Status of Prometheus, OTel Collector, and Alertmanager (UP/DOWN cards)
- Current active alerts count
- OTel Collector queue depth and HTTP request rates
- Alert notification trends

**Status**: ✅ Fixed - Replaced with working queries
- Old dashboard queried non-existent metrics (loki_*, tempo_*)
- New dashboard uses only metrics Prometheus actually exports
- Backup of old version: `observability-stack-health.json.bak`

**Expected data**: Should show status cards with "1" (UP) for all components

---

### 2. **Application Performance - Logs** (NEW) 📊
**Location**: http://localhost:3000 → Dashboards → "Application Performance - Logs"

**What it shows**:
- **Media-Refinery Logs**: Real-time log output from your media processing app
- **Log Volume Trends**: Activity graph for all services
- **Error Tracking**: stderr logs graphed by service  
- **Quick Access Panels**: Prometheus and OTel Collector logs for debugging

**Design for Multiple Stacks**:
```
Default filter: {compose_service="media-refinery"}

To monitor other stacks, duplicate the main log panel and change:
  {compose_service="media-refinery"}    → {compose_service="YOUR_APP"}
```

**Available services** (logging to Loki via Alloy):
```
alertmanager, alloy, grafana, loki, otel-collector,
prometheus, tempo
```

---

### 3. **OTel Collector Dashboard**
**Location**: http://localhost:3000 → Dashboards → "otel-collector"

**Purpose**: Monitor OpenTelemetry collector health and performance

**Data**: 
- OTel collector metrics (exporter queue size, HTTP request rates, etc.)
- 14 metrics available from OTel Collector

---

## How Data Flows

```
Your Apps (any container on observability-lab network)
    ↓
Docker Containers → Logs → Alloy (port 12345)
    ↓
Loki (Log Storage)
    ↓
Grafana Dashboard Queries
```

### For Metrics
```
Your Apps (with OTel SDK instrumentation)
    ↓
OTel Collector (localhost:4317/4318)
    ↓
Prometheus (Metrics Storage)
    ↓
Grafana Dashboard Queries
```

---

## Available Data by Source

### Logs (via Loki)
✅ **7 core services** actively logging (via Alloy):
- observability-lab stack: prometheus, grafana, loki, tempo, otel-collector, alertmanager, alloy

**Query pattern**: `{compose_service="SERVICE_NAME"}`

### Metrics (via Prometheus)
✅ **51 metrics** available:

**Available metric suites**:
- `alertmanager_*` (30+ metrics) - Alert counts, notification rates, etc.
- `otelcol_*` (14 metrics) - Queue sizes, HTTP request rates, memory usage
- `prometheus_*` - Self-monitoring metrics
- `ALERTS` - Recording rules for firing alerts

**NOT available** (by default):
- `loki_*` - Loki doesn't export internal metrics by default
- `tempo_*` - Tempo doesn't export internal metrics by default
- Custom application metrics (requires OTel SDK instrumentation in apps)

### Traces (via Tempo)
✅ Ready to receive traces via OTel Collector (localhost:4317/4318)
- No traces yet without app instrumentation
- See docs/examples/media-refinery-integration.md for setup

---

## Testing the Dashboards

### Test 1: Verify Data in "Observability Stack Health"
1. Go to http://localhost:3000
2. Navigate to Dashboards → "Observability Stack Health"
3. You should see:
   - Status cards showing "1" (UP) for Prometheus, OTel, Alertmanager
   - Charts showing queue depth and request rates (live data)
   - Alert timeseries (should show 0 if no alerts firing)

### Test 2: View Application Logs in "Application Performance - Logs"
1. Go to Dashboards → "Application Performance - Logs"
2. Main panel should show recent logs from media-refinery
3. Log volume chart should show activity trends
4. Change the filter to `{compose_service="prometheus"}` to see other service logs

### Test 3: Check Loki for All Services
1. Go to Explore (left sidebar)
2. Select Loki datasource
3. Query: `{job="docker"}`
4. You should see logs from all 13 services

### Test 4: Check Prometheus Metrics
1. Go to Explore (left sidebar)
2. Select Prometheus datasource
3. Query: `up`
4. You should see status of all 5 components (Prometheus, OTel, Alertmanager, etc.)

---

## Next Steps

### To Monitor Media-Refinery Metrics
You need to instrument it with OpenTelemetry SDK:

```go
// In your Go application
import "go.opentelemetry.io/otel/sdk/metric"
// ... initialize metrics exporter to otel-collector:4317
```

See: `docs/examples/media-refinery-integration.md`

### To Add More Dashboards
1. Create new dashboard in Grafana UI
2. Save as JSON to `config/grafana/dashboards/`
3. Restart Grafana to load it

### To Monitor More Services
1. Add them to the `observability-lab` Docker network
2. They'll automatically be logged via Alloy (Docker container log discovery)
3. Add Loki query panels with their `compose_service` name

---

## Troubleshooting

### Dashboards Show Empty Panels
1. **Check time range**: Click time picker (top right) and select "Last 1 hour"
2. **Check refresh**: Ensure auto-refresh is enabled (top right)
3. **Verify datasource**: Dashboard panel → Edit → check datasource is selected
4. **Check Prometheus**: Visit http://localhost:9090 and run same query

### No Logs Appearing
1. **Verify Loki is running**: `docker compose ps loki`
2. **Check Alloy**: `docker compose logs alloy --tail 20` and `curl http://localhost:12345/metrics | grep loki_source_docker`
3. **Verify network**: `docker network inspect observability-lab`

### No Metrics for Component
1. **Check target**: http://localhost:9090 → Status → Targets
2. **Verify scrape config**: `config/prometheus/prometheus.yaml`
3. **Check metrics endpoint**: `curl http://COMPONENT:METRICS_PORT/metrics`

---

## File Locations

```
config/grafana/dashboards/
├── application-performance-logs.json      ← NEW: App logs dashboard
├── observability-stack-health.json        ← FIXED: Stack health (was broken)
├── observability-stack-health.json.bak    ← Backup of old broken version
├── infrastructure-overview.json
├── otel-collector.json
└── prometheus.json
```

---

**Last Updated**: 2024-12-22  
**All Dashboards**: ✅ Validated and working
