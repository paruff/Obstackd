---
name: Observability Config Instructions
description: Applied automatically when working in config/
applyTo: "config/**/*.yaml,config/**/*.yml"
---

# Observability Config Instructions — Obstackd

## OpenTelemetry Collector (config/otel-collector/)

```yaml
# ✅ Correct: exporters reference Compose service names
exporters:
  prometheusremotewrite:
    endpoint: "http://prometheus:9090/api/v1/write"
  otlp:
    endpoint: "tempo:4317"
    tls:
      insecure: true

# ❌ Never use localhost — breaks in Docker networking
exporters:
  prometheusremotewrite:
    endpoint: "http://localhost:9090/api/v1/write"
```

### OTEL Collector Checklist
- Receivers define what comes IN (otlp, hostmetrics, etc.)
- Processors are applied in order (batch last, memory_limiter first)
- Exporters define where telemetry goes OUT
- Pipelines connect receivers → processors → exporters
- Every pipeline must have at least one receiver and one exporter

## Prometheus (config/prometheus/)

```yaml
# ✅ Scrape targets use Compose service names
scrape_configs:
  - job_name: 'otel-collector'
    static_configs:
      - targets: ['otel-collector:8889']

  - job_name: 'tempo'
    static_configs:
      - targets: ['tempo:3200']
```

### Prometheus Checklist
- `scrape_interval` set globally and per-job where needed
- Alert rules in separate `rules/` files, not inline
- Recording rules documented with a comment explaining the use case
- Retention and storage configured via environment variable, not hardcoded

## Tempo (config/tempo/)

```yaml
# ✅ Tempo receives traces and stores them
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: "0.0.0.0:4317"
        http:
          endpoint: "0.0.0.0:4318"

storage:
  trace:
    backend: local
    local:
      path: /var/tempo/traces
```

## Grafana (config/grafana/)

### Datasource Provisioning
```yaml
# config/grafana/provisioning/datasources/datasources.yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090    # ← Compose service name, not localhost
    isDefault: true

  - name: Tempo
    type: tempo
    url: http://tempo:3200         # ← Compose service name, not localhost
```

### Dashboard Provisioning
```yaml
# config/grafana/provisioning/dashboards/dashboards.yaml
apiVersion: 1
providers:
  - name: default
    folder: Obstackd
    type: file
    options:
      path: /var/lib/grafana/dashboards
```

- Dashboard JSON files go in `data/grafana/dashboards/`
- Never edit dashboard JSON by hand — export from Grafana UI, then commit
- Dashboard UIDs must be stable (set explicitly, not auto-generated)
