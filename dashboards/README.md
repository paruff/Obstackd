# Grafana Dashboard Template Suite

## Overview

This directory contains a production-grade, versioned, reusable Grafana dashboard template suite for comprehensive observability. The dashboards are designed to be:

- ✅ **Provisionable** - Automatically loaded via Grafana provisioning
- ✅ **Parameterized** - Use template variables for flexibility
- ✅ **Git-managed** - Version controlled and reproducible
- ✅ **Reusable** - Work across clusters, environments, and services

## Directory Structure

```
dashboards/
├── platform/           # Observability platform monitoring
│   ├── global-health.json              # Overall platform health
│   ├── prometheus-overview.json        # Prometheus metrics
│   ├── loki-overview.json              # Loki log aggregation
│   ├── tempo-overview.json             # Tempo distributed tracing
│   ├── alloy-overview.json             # Alloy/OTel Collector
│   ├── alertmanager-overview.json      # Alertmanager
│   ├── storage-capacity.json           # Storage planning
│   └── ingestion-health.json           # Cross-component ingestion
├── services/           # Application monitoring (Golden Signals)
│   ├── service-overview.json           # Golden Signals summary
│   ├── service-latency.json            # Latency analysis
│   ├── service-errors.json             # Error tracking
│   ├── service-saturation.json         # Resource saturation
│   ├── service-debug.json              # Debugging tools
│   ├── service-slo.json                # SLO tracking
│   └── service-capacity.json           # Capacity planning
├── provisioning/
│   └── dashboards.yaml                 # Provisioning config
└── README.md                           # This file
```

## Quick Start

### Option 1: Provision Dashboards (Recommended)

1. **Update your Grafana volume mounts** in `compose.yaml`:

```yaml
grafana:
  volumes:
    - ./dashboards/platform:/etc/grafana/dashboards/platform:ro
    - ./dashboards/services:/etc/grafana/dashboards/services:ro
    - ./provisioning/dashboards.yaml:/etc/grafana/provisioning/dashboards/new-dashboards.yaml:ro
```

2. **Restart Grafana**:

```bash
docker compose restart grafana
```

3. **Verify** dashboards appear in:
   - `Platform` folder (8 dashboards)
   - `Services` folder (7 dashboards)

### Option 2: Manual Import

1. Open Grafana UI: http://localhost:3000
2. Navigate to **Dashboards** → **Import**
3. Upload JSON files from `dashboards/platform/` or `dashboards/services/`
4. Select appropriate folder

## Dashboard Categories

### Platform Dashboards (8)

Monitor the health and performance of your observability infrastructure:

| Dashboard | Purpose | Key Metrics |
|-----------|---------|-------------|
| **Global Health** | Overall platform status | Active alerts, ingestion rates, component health |
| **Prometheus** | Metrics storage | Scrape duration, TSDB size, WAL latency, series count |
| **Loki** | Log aggregation | Ingest rate, query latency, chunk flush, compactor |
| **Tempo** | Distributed tracing | Spans/sec, query latency, distributor health |
| **Alloy** | OTel Collector | Pipeline throughput, drops, queue depth, resources |
| **Alertmanager** | Alert routing | Alert handling, notification success/failure |
| **Storage Capacity** | Capacity planning | Growth trends, retention, projections |
| **Ingestion Health** | Cross-component | Ingestion metrics, bottlenecks, drop rates |

### Service Dashboards (7)

Monitor application performance using the Golden Signals methodology:

| Dashboard | Purpose | Answers |
|-----------|---------|---------|
| **Service Overview** | Golden Signals at a glance | Is my service healthy? |
| **Service Latency** | Latency deep-dive | Which endpoints are slow? |
| **Service Errors** | Error analysis | What's failing and why? |
| **Service Saturation** | Resource utilization | Am I running out of resources? |
| **Service Debug** | Troubleshooting | Logs, traces, exemplars |
| **Service SLO** | SLO tracking | Am I meeting my SLOs? |
| **Service Capacity** | Growth planning | When do I need to scale? |

## Template Variables

All dashboards use consistent template variables:

| Variable | Source | Purpose |
|----------|--------|---------|
| `datasource` | Datasource query | Select Prometheus instance |
| `cluster` | `label_values(up, cluster)` | Filter by cluster |
| `namespace` | `label_values(up, namespace)` | Filter by namespace |
| `environment` | Custom | Filter by environment (prod/staging/dev) |
| `service` | `label_values(up, job)` | Filter by service (service dashboards only) |
| `instance` | `label_values(up, instance)` | Filter by instance (service dashboards only) |

## Required Metrics and Labels

### For Platform Dashboards

Standard Prometheus, Loki, Tempo, and OTel Collector metrics are used. No special configuration required if you're using the standard exporters.

### For Service Dashboards

Your applications must expose metrics following these conventions:

#### Required Labels

All metrics should include:

```promql
job="your-service-name"       # Service identifier
namespace="production"         # Deployment namespace
cluster="us-west-1"           # Cluster identifier (optional)
instance="pod-123"            # Instance identifier
```

#### Required Metrics

**HTTP Traffic:**
```promql
http_requests_total{job, method, status, endpoint}
http_request_duration_seconds{job, method, endpoint}  # Histogram
```

**Errors:**
```promql
http_requests_total{status=~"5.."}  # 5xx errors
http_requests_total{status=~"4.."}  # 4xx errors
```

**Saturation:**
```promql
process_cpu_seconds_total{job}
process_resident_memory_bytes{job}
go_goroutines{job}  # For Go applications
```

**Logs (Loki):**
```logql
{job="your-service", level="error"}  # Structured logs with level
```

**Traces (Tempo):**
```promql
traces_spanmetrics_calls_total{service_name="your-service"}
traces_spanmetrics_latency_bucket{service_name="your-service"}
```

### Using OpenTelemetry

If using OpenTelemetry SDKs, configure your service:

```yaml
# OTEL environment variables
OTEL_SERVICE_NAME=your-service-name
OTEL_RESOURCE_ATTRIBUTES=namespace=production,cluster=us-west-1
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

The OTel Collector will automatically generate the required metrics for service dashboards.

## Service Onboarding Guide

### Step 1: Instrument Your Application

**Option A: OpenTelemetry SDK (Recommended)**

1. Add OpenTelemetry SDK to your application
2. Configure resource attributes (service name, namespace, cluster)
3. Export to `http://otel-collector:4317` (gRPC) or `:4318` (HTTP)

Example (Go):
```go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    "go.opentelemetry.io/otel/sdk/resource"
    semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
)

resource := resource.NewWithAttributes(
    semconv.SchemaURL,
    semconv.ServiceName("my-service"),
    semconv.ServiceNamespace("production"),
    attribute.String("cluster", "us-west-1"),
)
```

**Option B: Prometheus Client Library**

1. Add Prometheus client library
2. Expose metrics endpoint at `/metrics`
3. Add Prometheus scrape config

### Step 2: Configure Prometheus Scraping

Add to `config/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'my-service'
    static_configs:
      - targets: ['my-service:8080']
        labels:
          cluster: 'us-west-1'
          namespace: 'production'
          environment: 'production'
```

### Step 3: Configure Logging

Send logs to Loki with proper labels:

```yaml
# Using Promtail or Alloy
scrape_configs:
  - job_name: my-service
    static_configs:
      - targets:
          - localhost
        labels:
          job: my-service
          namespace: production
          cluster: us-west-1
```

### Step 4: Access Your Dashboards

1. Open Grafana: http://localhost:3000
2. Go to **Services** folder
3. Open **Service Overview** dashboard
4. Select your service from the `service` dropdown
5. All panels will automatically populate with your service's data

## Dashboard Design Philosophy

### Decision-Oriented

Each dashboard answers **one main question**:

- Global Health: *Is my platform healthy?*
- Service Overview: *Is my service healthy?*
- Service Latency: *Where is latency coming from?*
- Service Errors: *What's failing?*

### User Impact → Root Cause → Internals

Dashboards are laid out from:
1. **Top** - User-facing impact (errors, latency)
2. **Middle** - Application metrics (endpoints, methods)
3. **Bottom** - Internal details (resources, queues)

### Golden Signals (Service Dashboards)

All service dashboards follow the [Golden Signals](https://sre.google/sre-book/monitoring-distributed-systems/#xref_monitoring_golden-signals):

1. **Traffic** - How much demand is on your system?
2. **Latency** - How long does it take to service requests?
3. **Errors** - What is the rate of failed requests?
4. **Saturation** - How "full" is your service?

## Customization Guide

### Modify Queries

All queries are PromQL-based. To customize:

1. Open dashboard JSON in your editor
2. Find the panel's `targets` array
3. Modify the `expr` field with your PromQL query
4. Save and re-provision or re-import

Example:
```json
{
  "targets": [
    {
      "expr": "rate(http_requests_total{job=~\"$service\"}[5m])",
      "legendFormat": "{{method}}"
    }
  ]
}
```

### Add New Panels

1. Use Grafana UI to create the panel
2. Export the dashboard JSON
3. Copy the panel JSON into your dashboard file
4. Update IDs to avoid conflicts

### Adjust Thresholds

Find the `thresholds` section in field config:

```json
{
  "thresholds": {
    "mode": "absolute",
    "steps": [
      {"color": "green", "value": null},
      {"color": "yellow", "value": 80},
      {"color": "red", "value": 95}
    ]
  }
}
```

## Troubleshooting

### Dashboards Not Appearing

1. **Check volume mounts** in `compose.yaml`
2. **Check Grafana logs**: `docker logs grafana`
3. **Verify provisioning config**: Look for errors in logs
4. **Check file permissions**: Files should be readable by Grafana container

### No Data in Panels

1. **Verify datasource** is configured (Prometheus, Loki, Tempo)
2. **Check template variables** - Are they populated?
3. **Verify metric names** match your actual metrics
4. **Check time range** - Adjust to ensure data exists

### Template Variables Empty

1. **Check Prometheus** is scraping your targets
2. **Verify labels exist** on your metrics (cluster, namespace, job)
3. **Check label consistency** - Ensure metric labels match dashboard queries

### Queries Timing Out

1. **Reduce time range** (use 1h instead of 24h)
2. **Optimize queries** - Add more specific label filters
3. **Check cardinality** - High cardinality can slow queries
4. **Increase Prometheus resources** if needed

## Maintenance

### Updating Dashboards

1. Make changes to JSON files in this directory
2. Commit to Git
3. Restart Grafana or wait for auto-reload (10 seconds)

```bash
git add dashboards/
git commit -m "Update service latency dashboard thresholds"
git push
docker compose restart grafana
```

### Versioning

Dashboard files include a `version` field that auto-increments with each save. For manual versioning:

1. Update the `version` field in the JSON
2. Document changes in Git commit message
3. Consider using Git tags for major releases

### Backup

Dashboards are backed up via Git. To export current state from Grafana:

```bash
# Export all dashboards
curl -u admin:admin http://localhost:3000/api/search?query=& | \
  jq -r '.[].uri' | \
  xargs -I {} curl -u admin:admin http://localhost:3000/api/dashboards/{} | \
  jq -r '.dashboard'
```

## Best Practices

### Do's ✅

- ✅ Use template variables for all filters
- ✅ Add descriptions to panels
- ✅ Set appropriate thresholds for alerts
- ✅ Use consistent metric naming
- ✅ Add links to related dashboards
- ✅ Keep queries performant (use recording rules if needed)
- ✅ Version control all changes
- ✅ Test dashboards with real data before deploying

### Don'ts ❌

- ❌ Don't hardcode service names in queries
- ❌ Don't use pie charts (hard to read)
- ❌ Don't create unbounded high-cardinality queries
- ❌ Don't mix multiple concerns in one dashboard
- ❌ Don't use unstable metrics or features
- ❌ Don't bypass provisioning (manual changes are lost)

## Integration with Alerting

While these dashboards focus on visualization, consider creating recording rules for complex queries:

```yaml
# prometheus.rules.yml
groups:
  - name: service_slos
    interval: 30s
    rules:
      - record: service:request_latency:p99
        expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

Then reference in dashboards:
```promql
service:request_latency:p99{job="$service"}
```

## Support and Contribution

### Getting Help

- Check this README
- Review dashboard descriptions
- Check Grafana logs: `docker logs grafana`
- Review Prometheus queries: http://localhost:9090

### Contributing

To improve these dashboards:

1. Test changes locally
2. Ensure JSON is valid
3. Follow existing patterns
4. Update this README if needed
5. Submit changes via Git

## License

These dashboards are part of the Obstackd observability platform and follow the same license as the main repository.

---

## Quick Reference

### Metric Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Counter | `*_total` | `http_requests_total` |
| Gauge | `*` | `process_resident_memory_bytes` |
| Histogram | `*_bucket`, `*_sum`, `*_count` | `http_request_duration_seconds_bucket` |
| Summary | `*{quantile="..."}` | `http_request_duration_seconds{quantile="0.99"}` |

### Common PromQL Patterns

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Success rate
sum(rate(http_requests_total{status!~"5.."}[5m])) / sum(rate(http_requests_total[5m]))

# P99 latency
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# CPU usage
rate(process_cpu_seconds_total[5m])

# Memory usage
process_resident_memory_bytes

# Aggregation by label
sum by (method, status) (rate(http_requests_total[5m]))
```

### Useful Links

- [Prometheus Query Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Golden Signals (Google SRE)](https://sre.google/sre-book/monitoring-distributed-systems/)
