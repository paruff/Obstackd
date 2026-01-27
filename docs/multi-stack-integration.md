# Multi-Stack Integration Guide

## Overview

Obstackd is designed as a **centralized observability platform** for multiple Docker Compose applications. Each application stack remains independent but can send telemetry to Obstackd.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Obstackd Stack                       │
│  ┌──────────────┐  ┌──────────┐  ┌──────────────┐     │
│  │ OTel         │  │Prometheus│  │   Grafana    │     │
│  │ Collector    │  │          │  │              │     │
│  └──────────────┘  └──────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────┐                        │
│  │    Tempo     │  │   Loki   │                        │
│  └──────────────┘  └──────────┘                        │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │ observability-lab network
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
   │  App    │      │  App    │      │  App    │
   │ Stack 1 │      │ Stack 2 │      │ Stack 3 │
   └─────────┘      └─────────┘      └─────────┘
```

## Integration Pattern

### Step 1: Start Obstackd

```bash
cd /path/to/Obstackd
docker compose --profile core up -d
```

This creates the `observability-lab` network.

### Step 2: Connect Your Application Stack

In your application's `docker-compose.yml`, add:

```yaml
services:
  your-app:
    # ... your app configuration ...
    networks:
      - default              # Your app's internal network
      - observability-lab    # Obstackd's network
    environment:
      # OpenTelemetry (send to Obstackd)
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
      - OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
      - OTEL_SERVICE_NAME=your-app-name
      - OTEL_TRACES_EXPORTER=otlp
      - OTEL_METRICS_EXPORTER=otlp
      - OTEL_LOGS_EXPORTER=otlp

networks:
  default:
    driver: bridge
  observability-lab:
    external: true
    name: observability-lab
```

### Step 3: Add Prometheus Scrape Job (Optional)

If your app exposes Prometheus metrics, add to Obstackd's [`config/prometheus/prometheus.yaml`](../config/prometheus/prometheus.yaml):

```yaml
scrape_configs:
  - job_name: 'your-app'
    static_configs:
      - targets: ['your-app-container-name:9090']
        labels:
          component: 'your-app'
          service: 'your-service-category'
    scrape_interval: 15s
```

Then restart Prometheus:

```bash
docker compose restart prometheus
```

## Service Endpoints

From your application containers, use these DNS names:

| Service | Endpoint | Protocol | Purpose |
|---------|----------|----------|---------|
| OTel Collector | `otel-collector:4317` | gRPC | OTLP traces/metrics/logs |
| OTel Collector | `otel-collector:4318` | HTTP | OTLP traces/metrics/logs |
| Loki | `loki:3100` | HTTP | Direct log pushing |
| Tempo | `tempo:4317` | gRPC | Direct trace pushing |
| Prometheus | `prometheus:9090` | HTTP | Query metrics |
| Grafana | `grafana:3000` | HTTP | Visualization (if needed) |

## Instrumentation Requirements

### For Applications WITH OpenTelemetry SDK

Set environment variables as shown in Step 2. Your app must use an OpenTelemetry SDK (available for most languages: Go, Python, Java, Node.js, .NET, etc.).

Example for Go:
```go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
)
```

### For Applications WITHOUT OpenTelemetry SDK

Use **log shipping** with Promtail or Docker logging drivers:

```yaml
services:
  your-app:
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
        labels: "app.name,app.environment"
        tag: "{{.Name}}"
```

Then configure Promtail to scrape Docker logs and send to Loki.

## Example: Media-Refinery Integration

```yaml
# Media-Refinery's docker-compose.yml
services:
  media-refinery:
    # ... existing config ...
    networks:
      - media-refinery-network
      - observability-lab
    environment:
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
      - OTEL_SERVICE_NAME=media-refinery

networks:
  media-refinery-network:
    driver: bridge
  observability-lab:
    external: true
    name: observability-lab
```

## Validation

### Test Network Connectivity

From your application container:

```bash
# Test OTel Collector
docker exec your-app-container curl http://otel-collector:4318/

# Test Loki
docker exec your-app-container curl http://loki:3100/ready

# Test Prometheus
docker exec your-app-container curl http://prometheus:9090/-/healthy
```

### Verify Telemetry Flow

1. **Check OTel Collector is receiving data:**
   ```bash
   curl http://localhost:8888/metrics | grep receiver
   ```

2. **Check Prometheus targets:**
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```

3. **Check Grafana dashboards:**
   - Open http://localhost:3000
   - Navigate to Infrastructure Overview dashboard

## Troubleshooting

### Application can't reach Obstackd services

**Problem:** DNS resolution fails or connection refused

**Solution:**
1. Verify network exists: `docker network ls | grep observability-lab`
2. Verify your container joined the network: `docker inspect your-container | grep observability-lab`
3. Restart your application: `docker compose restart`

### No telemetry data appearing

**Problem:** OTel Collector not receiving data

**Checklist:**
- [ ] Application has OpenTelemetry SDK installed and initialized
- [ ] OTEL_* environment variables are set correctly
- [ ] Application is on `observability-lab` network
- [ ] OTel Collector is running: `docker ps | grep otel-collector`
- [ ] Check OTel Collector logs: `docker logs otel-collector`

### Logs not appearing in Loki

**Problem:** Logs aren't showing in Grafana

**Solutions:**
- Use Promtail to ship logs from your app
- Or configure your app to push logs directly to `loki:3100/loki/api/v1/push`
- Or use Docker logging driver with Promtail scraping

## Best Practices

1. **Use OpenTelemetry SDK** - Preferred method for traces, metrics, and logs
2. **Keep stacks separate** - Don't merge compose files unless necessary
3. **Use DNS names** - Never use IP addresses or `host.docker.internal`
4. **Label everything** - Use consistent labels for service, environment, etc.
5. **Test in isolation** - Start Obstackd first, then your app
6. **Monitor the monitor** - Check Obstackd's own telemetry regularly

## Security Considerations

- The `observability-lab` network is **unauthenticated** by default
- Only add trusted applications to this network
- Consider using Docker secrets for sensitive configuration
- For production, add authentication to Grafana, Prometheus, etc.

## Removing an Application

To disconnect an application:

1. Remove `observability-lab` from its networks section
2. Remove OTEL_* environment variables
3. Remove Prometheus scrape job (if added)
4. Restart: `docker compose up -d`

The application will continue running but stop sending telemetry.

## Adding More Obstackd Components

To add new observability services (e.g., Jaeger, Zipkin):

1. Add service to `compose.yaml`
2. Connect to `observability-lab` network (automatic via default)
3. Update OTel Collector config if needed
4. Restart: `docker compose up -d`

All connected applications automatically gain access to the new service.
