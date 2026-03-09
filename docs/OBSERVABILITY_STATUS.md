# Complete Observability Data Guide

## TL;DR - Go Here Now

| What You Want | URL |
|---|---|
| **Infrastructure Metrics** | http://localhost:3000 → Dashboards → "Observability Stack Health" |
| **Container Logs** | http://localhost:3000 → Explore → Loki → Log Browser |
| **System Health** | http://localhost:9090 (Prometheus) |
| **Alerts** | http://localhost:3000 → Alerting → Alert rules |

---

## What's Running (All 7 Core Services)

✅ **Prometheus** (v2.52.0) - Metrics database
✅ **Loki** (v2.9.10) - Log storage
✅ **Tempo** (v2.5.0) - Trace storage
✅ **Grafana** (v10.4.5) - Visualization
✅ **OTel Collector** (v0.103.1) - Telemetry ingestion
✅ **Alertmanager** (v0.27.0) - Alert routing
✅ **Alloy** (v1.12.2) - Log shipper (Docker container logs → Loki)

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

### 2. LOGS ✅
**Source:** Docker containers via Grafana Alloy (v1.12.2)
**What:** Stdout/stderr from all running containers

**Containers Being Logged:**
```
Obstackd Stack:
  - prometheus
  - loki
  - tempo
  - grafana
  - otel-collector
  - alertmanager
  - alloy
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

### Promtail → Alloy Migration

Promtail has been replaced by Grafana Alloy as the log collection agent. Alloy uses the
River configuration language and provides native Docker container log discovery.

**Key change:** Log collection now runs on port 12345 (Alloy) instead of 9080 (Promtail).
Config is at `config/alloy/config.river` instead of `config/promtail/promtail.yaml`.

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
│  └─ Alloy (log shipper)                      │
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
| Alloy | 12345 | Metrics/health check |

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

