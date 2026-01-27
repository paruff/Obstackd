# Complete Observability Data Guide

## TL;DR - Go Here Now

| What You Want | URL |
|---|---|
| **Infrastructure Metrics** | http://localhost:3000 → Dashboards → "Observability Stack Health" |
| **Container Logs** | http://localhost:3000 → Explore → Loki → Log Browser |
| **System Health** | http://localhost:9090 (Prometheus) |
| **Alerts** | http://localhost:3000 → Alerting → Alert rules |

---

## What's Running (All 8 Services UP)

✅ **Prometheus** (v2.50.1) - Metrics database - 22 hours uptime
✅ **Loki** (v2.9.4) - Log storage - 22 hours uptime
✅ **Tempo** (v2.3.1) - Trace storage - 22 hours uptime
✅ **Grafana** (v10.4.2) - Visualization - 22 hours uptime
✅ **OTel Collector** (v0.99.0) - Telemetry ingestion - 22 hours uptime
✅ **Alertmanager** (v0.27.0) - Alert routing - 22 hours uptime
✅ **Promtail** (v3.0.0) - Log shipper - 2 minutes (JUST RESTARTED & FIXED)
✅ **Media-Refinery** - Application under observation - 9 minutes

---

## Data Now Available

### 1. METRICS ✅
**Source:** Prometheus
**What:** Infrastructure metrics from observability stack
**Targets (4 active):**
- prometheus (self-monitoring)
- otel-collector (collector internals)
- otel-app-metrics (exported by collector)
- alertmanager (alert system)

**How to View:**
```
Method 1: Dashboards
  Grafana → Dashboards → "Observability Stack Health"
  Shows: OTel receiver/exporter status, queue depth, memory usage

Method 2: Query Directly
  Grafana → Explore → Prometheus
  Try: up, otelcol_exporter_queue_size, otelcol_http_server_duration_count
```

### 2. LOGS ✅ (NEWLY FIXED)
**Source:** Docker containers via Promtail v3.0.0
**What:** Stdout/stderr from all 13 running containers

**Containers Being Logged:**
```
Obstackd Stack:
  - prometheus
  - loki
  - tempo
  - grafana
  - otel-collector
  - alertmanager
  - promtail

Media-Refinery Stack:
  - media-refinery (your app)
  - beets
  - tdarr
  - radarr
  - sonarr
  - plex
```

**How to View:**
```
Grafana → Explore → Loki

Quick Filters:
  {compose_service="media-refinery"}     → App logs
  {compose_service="prometheus"}         → Prometheus logs
  {stream="stderr"}                      → Error logs only
  {compose_project="observability-lab"} → Obstackd stack
```

### 3. TRACES ⚠️
**Source:** Tempo (waiting for instrumentation)
**Status:** Ready but empty
**Requirement:** Code must emit OpenTelemetry spans

**To Enable:**
1. Add OpenTelemetry SDK to Media-Refinery Go code
2. Initialize in main()
3. Wrap operations with `tracer.Start()`
4. Rebuild and redeploy

See: [Instrumentation Guide](examples/media-refinery-integration.md)

### 4. ALERTS ✅
**Source:** Alertmanager
**What:** Pre-configured alert rules
**Rules Defined:** See `config/prometheus/alerts.yml`

**How to View:**
```
Grafana → Alerting → Alert rules
OR
Alertmanager Web UI → http://localhost:9093
```

---

## Fix Applied Today

### Problem
Promtail couldn't read Docker logs:
```
Error: client version 1.42 is too old. 
Minimum supported API version is 1.44
```

### Solution
Upgraded Promtail: v2.9.4 → v3.0.0

### Result
✅ All 13 containers now being logged
✅ Logs flowing to Loki
✅ Queryable in Grafana

---

## Network Topology

```
┌─────────────────────────────────────────────┐
│  observability-lab (Docker network)         │
├─────────────────────────────────────────────┤
│                                             │
│  Obstackd Stack:                            │
│  ├─ Prometheus (metrics)                    │
│  ├─ Loki (logs)                             │
│  ├─ Tempo (traces)                          │
│  ├─ Grafana (UI)                            │
│  ├─ OTel Collector (ingestion)              │
│  ├─ Alertmanager                            │
│  └─ Promtail (log shipper)                  │
│                                             │
│  Media-Refinery Stack:                      │
│  └─ media-refinery + integrations           │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Port Reference

| Service | Port | Purpose |
|---------|------|---------|
| Grafana | 3000 | Visualization UI |
| Prometheus | 9090 | Query & scrape UI |
| Loki | 3100 | Log API |
| Tempo | 3200 | Trace API |
| Alertmanager | 9093 | Alert UI |
| OTel Collector | 4317/4318 | OTLP gRPC/HTTP |
| Promtail | 9080 | Health check |

---

## Verification

### Check Prometheus Scraping
```bash
curl http://localhost:9090/api/v1/targets
# Should show 4 targets with health="up"
```

### Check Loki Receiving Logs
```bash
curl http://localhost:3100/loki/api/v1/label/compose_service/values
# Should show all 13 service names
```

### Check OTel Collector
```bash
curl http://localhost:8888/metrics
# Should show collector metrics
```

---

## Common Queries

### Prometheus Queries
```promql
# All targets
up

# OTel Collector processing
rate(otelcol_exporter_queue_size[5m])

# Collector uptime
rate(otelcol_http_server_duration_count[5m])

# Alertmanager alerts
alertmanager_alerts
```

### Loki Queries (LogQL)
```
# All logs from media-refinery
{compose_service="media-refinery"}

# Error logs only
{stream="stderr"}

# Prometheus logs
{compose_service="prometheus"}

# Recent logs (pattern matching)
{compose_service="media-refinery"} | grep "ERROR"
```

---

## What's Working vs What Needs Setup

| Feature | Status | Action |
|---------|--------|--------|
| Metrics collection | ✅ Active | View in Grafana dashboards |
| Log shipping | ✅ Active (FIXED) | Query in Loki explorer |
| Trace collection | ⚠️ Ready/Empty | Add OTel SDK to code |
| Alert rules | ✅ Configured | Check in Alerting section |
| Multi-app support | ✅ Ready | Connect more stacks to observability-lab network |

---

## Documentation

- [Grafana Navigation Guide](grafana-navigation.md) - Detailed Grafana walkthrough
- [Data Navigation Guide](data-navigation-guide.md) - Where data is stored
- [Multi-Stack Integration](multi-stack-integration.md) - Connect other apps
- [Media-Refinery Integration](examples/media-refinery-integration.md) - Specific setup

---

## Quick Troubleshooting

**"I don't see logs"**
→ Check: `curl http://localhost:3100/loki/api/v1/label/compose_service/values`
→ Should list all services including "media-refinery"

**"Prometheus shows no targets"**
→ Check: `curl http://localhost:9090/api/v1/targets | grep health`
→ Should show targets with `"health":"up"`

**"Grafana dashboards are empty"**
→ Go to: Grafana → Explore → Prometheus → Query: `up`
→ Should return metrics

---

## Next Steps

### Now
1. ✅ Open Grafana: http://localhost:3000
2. ✅ View Dashboards → "Observability Stack Health"
3. ✅ Explore Logs → Loki datasource
4. ✅ Check alerts in Alerting menu

### This Week
1. ⚠️ (Optional) Add OpenTelemetry SDK to Media-Refinery for traces
2. ⚠️ (Optional) Create custom dashboards for app-specific metrics
3. ⚠️ (Optional) Configure alert notifications via webhooks

### This Month
1. ⚠️ (Optional) Add more applications to observability-lab network
2. ⚠️ (Optional) Set up alerting to email/Slack/PagerDuty
3. ⚠️ (Optional) Create runbooks for common alerts

