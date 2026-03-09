# Observability Data Now Available

## ✅ What's Live Right Now

### Metrics (Prometheus)
- **Status:** ✅ ACTIVE
- **Data:** Infrastructure metrics from 4 targets
- **View:** http://localhost:3000 → Dashboards → "Observability Stack Health"

### Logs (Loki)
- **Status:** ✅ ACTIVE (via Grafana Alloy v1.12.2)
- **Data:** All container logs from Obstackd core stack
- **View:** http://localhost:3000 → Explore → Loki

### Traces (Tempo)
- **Status:** ⚠️ Ready but empty
- **Requires:** OpenTelemetry SDK instrumentation in code
- **View:** http://localhost:3000 → Explore → Tempo

### Alerts (Alertmanager)
- **Status:** ✅ ACTIVE
- **Data:** Pre-configured alert rules
- **View:** http://localhost:3000 → Alerting → Alert rules

---

## Where to Look in Grafana

### Quick Links
- **Home:** http://localhost:3000
- **Prometheus UI:** http://localhost:9090
- **Loki UI:** http://localhost:3100
- **Alertmanager UI:** http://localhost:9093

### Navigation Paths

**For Metrics:**
```
Grafana → Dashboards → Observability Stack Health
OR
Grafana → Explore → Prometheus → Query: up
```

**For Logs:**
```
Grafana → Explore → Loki → Log Browser
Filter: compose_service = "media-refinery"
```

**For Alerts:**
```
Grafana → Alerting → Alert rules
```

---

## Data Flowing

### Prometheus Targets (4 active)
- `prometheus` (self-monitoring)
- `otel-collector` (collector internal metrics)
- `otel-app-metrics` (from collector)
- `alertmanager` (alert metrics)

### Loki Labels (All containers logged)
- Obstackd: prometheus, loki, tempo, grafana, otel-collector, alertmanager, alloy

Available filters:
- `compose_service` - Service name
- `compose_project` - Project name
- `stream` - stdout/stderr
- `container` - Container name

---

## Log Collection via Alloy

**Log shipper:** Grafana Alloy (v1.12.2) replaced Promtail as the container log collector.
Alloy uses the River configuration language and natively discovers Docker containers.

**Config:** `config/alloy/config.river`

**Result:** Docker container logs flow automatically to Loki ✅

---

## Documentation Files

- [Grafana Navigation Guide](grafana-navigation.md) - Detailed guide for viewing all data
- [Data Navigation Guide](data-navigation-guide.md) - Where data is stored
- [Multi-Stack Integration](multi-stack-integration.md) - How to add more apps

