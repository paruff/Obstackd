# Tempo Distributed Tracing - Operations Guide

## Overview

Grafana Tempo provides distributed tracing storage and query capabilities for the observability stack. It ingests traces in multiple formats (OTLP, Jaeger, Zipkin) and stores them efficiently for querying through Grafana.

**Architecture Note:** All OTLP traffic (from applications) should go through the OpenTelemetry Collector, which then forwards traces to Tempo on the internal Docker network. Direct protocol ingestion (Jaeger, Zipkin) is supported for backward compatibility but not recommended.

## Access Points

- **Tempo HTTP API**: http://localhost:3200
- **Tempo Ready Endpoint**: http://localhost:3200/ready
- **Tempo Metrics**: http://localhost:3200/metrics
- **OTLP** (recommended, via OTel Collector): localhost:4317 (gRPC), localhost:4318 (HTTP)
- **Jaeger gRPC** (legacy, direct to Tempo): localhost:14250
- **Jaeger HTTP** (legacy, direct to Tempo): http://localhost:14268
- **Zipkin** (legacy, direct to Tempo): http://localhost:9411

## Quick Start

### Deploy Tempo

```bash
# Start the full observability stack (includes Tempo)
docker compose --profile core up -d

# Check Tempo status
docker compose ps tempo

# Verify Tempo is ready
curl http://localhost:3200/ready
```

### Send Test Trace

```bash
# Create test trace
cat > /tmp/test-trace.json << 'EOF'
{
  "resourceSpans": [{
    "resource": {
      "attributes": [{
        "key": "service.name",
        "value": { "stringValue": "my-service" }
      }]
    },
    "scopeSpans": [{
      "scope": { "name": "manual-instrumentation" },
      "spans": [{
        "traceId": "0123456789abcdef0123456789abcdef",
        "spanId": "abcdef0123456789",
        "name": "my-operation",
        "kind": 1,
        "startTimeUnixNano": "1704710400000000000",
        "endTimeUnixNano": "1704710401000000000",
        "attributes": [{
          "key": "http.method",
          "value": { "stringValue": "GET" }
        }]
      }]
    }]
  }]
}
EOF

# Send trace via OTel Collector
curl -X POST \
  -H "Content-Type: application/json" \
  -d @/tmp/test-trace.json \
  http://localhost:4318/v1/traces

# Query trace
sleep 5
curl "http://localhost:3200/api/search?tags=service.name%3Dmy-service" | jq '.'
```

## Configuration

### Main Configuration

- **Location**: `config/tempo/tempo.yaml`
- **Mount**: Read-only in container at `/etc/tempo/tempo.yaml`

### Storage

- **Location**: `data/tempo/`
- **Backend**: Local filesystem
- **Retention**: 24 hours (configurable in `tempo.yaml`)

### Key Settings

```yaml
# Trace retention
compactor:
  compaction:
    block_retention: 24h

# Ingestion limits
overrides:
  ingestion_rate_limit_bytes: 10000000  # 10MB/s
  max_traces_per_user: 10000000
  max_bytes_per_trace: 50000  # 50KB
```

## Monitoring

### Health Check

```bash
# Ready endpoint (used by Docker healthcheck)
curl http://localhost:3200/ready

# Should return: "ready"
```

### Metrics

Tempo exports Prometheus metrics:

```bash
# View all Tempo metrics
curl http://localhost:3200/metrics | grep tempo_

# Key metrics:
# - tempo_ingester_bytes_received_total
# - tempo_distributor_spans_received_total
# - tempo_request_duration_seconds
```

### Logs

```bash
# View Tempo logs
docker compose logs tempo

# Follow logs
docker compose logs -f tempo

# Filter for errors
docker compose logs tempo | grep -i error
```

## Grafana Integration

### Pre-configured Datasource

The Tempo datasource is automatically provisioned in Grafana:

1. **Open Grafana**: http://localhost:3000 (admin/admin)
2. **Navigate to**: Explore
3. **Select**: Tempo datasource
4. **Query traces** by:
   - Trace ID
   - Service name
   - Tags/attributes

### Querying Traces

**By Trace ID:**
```
# In Grafana Explore, paste trace ID in the search box
0123456789abcdef0123456789abcdef
```

**By Service Name:**
```
# Use the search builder in Grafana
service.name = "my-service"
```

**Via API:**
```bash
# Search for traces
curl "http://localhost:3200/api/search?tags=service.name%3Dmy-service" | jq '.'

# Get specific trace
curl "http://localhost:3200/api/traces/0123456789abcdef0123456789abcdef" | jq '.'
```

## Application Integration

### OpenTelemetry SDK (Recommended)

Send traces through the OTel Collector:

**Python Example:**
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure OTLP exporter
otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:4318/v1/traces"
)

# Set up tracer
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(otlp_exporter)
)

# Create spans
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("my-operation"):
    # Your code here
    pass
```

**Node.js Example:**
```javascript
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');
const { BatchSpanProcessor } = require('@opentelemetry/sdk-trace-base');

const provider = new NodeTracerProvider();
const exporter = new OTLPTraceExporter({
  url: 'http://localhost:4318/v1/traces'
});

provider.addSpanProcessor(new BatchSpanProcessor(exporter));
provider.register();
```

### Jaeger Client

Direct integration (bypasses OTel Collector):

```bash
# Set environment variable
export JAEGER_ENDPOINT=http://localhost:14268/api/traces
```

### Zipkin Client

Direct integration (bypasses OTel Collector):

```bash
# Set environment variable
export ZIPKIN_ENDPOINT=http://localhost:9411
```

## Troubleshooting

### Tempo Not Ready

**Symptom**: Health check fails, Tempo restarts repeatedly

**Check logs:**
```bash
docker compose logs tempo | tail -50
```

**Common causes:**
1. **Configuration error**: Validate `config/tempo/tempo.yaml` syntax
2. **Storage permission**: Ensure `data/tempo/` is writable
3. **Port conflict**: Check if ports 3200, 9095, 9411, 14250, 14268 are available

**Solution:**
```bash
# Fix permissions
chmod -R 777 data/tempo/

# Validate configuration
docker compose config tempo

# Check port usage
lsof -i :3200
```

### Traces Not Appearing

**Symptom**: Traces sent but not visible in Grafana/queries

**Verify trace ingestion:**
```bash
# Check OTel Collector is forwarding
docker compose logs otel-collector | grep -i trace

# Check Tempo received spans
curl http://localhost:3200/metrics | grep tempo_distributor_spans_received_total
```

**Verify trace format:**
```bash
# Traces must be valid OTLP format
# Check timestamp is in nanoseconds (Unix epoch * 1e9)
# Verify traceId is 32 hex characters
# Verify spanId is 16 hex characters
```

### High Memory Usage

**Symptom**: Tempo container using excessive memory

**Check configuration:**
```yaml
# In compose.yaml
deploy:
  resources:
    limits:
      memory: 4G  # Adjust as needed
```

**Tune Tempo settings:**
```yaml
# In config/tempo/tempo.yaml
ingester:
  max_block_bytes: 500000000  # Reduce if needed
  max_block_duration: 5m      # Increase to flush less often
```

### Storage Growing Too Fast

**Symptom**: `data/tempo/` directory size increasing rapidly

**Check retention:**
```yaml
# In config/tempo/tempo.yaml
compactor:
  compaction:
    block_retention: 24h  # Reduce retention period
```

**Manual cleanup:**
```bash
# Stop Tempo
docker compose stop tempo

# Clean old blocks (data loss warning!)
rm -rf data/tempo/blocks/*

# Restart Tempo
docker compose start tempo
```

## Backup and Recovery

### Backup Traces

```bash
# Create backup directory
mkdir -p /tmp/tempo-backup

# Backup trace data
tar -czf /tmp/tempo-backup/tempo-$(date +%Y%m%d).tar.gz \
  data/tempo/

# Backup configuration
cp config/tempo/tempo.yaml /tmp/tempo-backup/
```

### Restore from Backup

```bash
# Stop Tempo
docker compose stop tempo

# Restore data
tar -xzf /tmp/tempo-backup/tempo-20240108.tar.gz

# Restore configuration
cp /tmp/tempo-backup/tempo.yaml config/tempo/

# Restart Tempo
docker compose start tempo
```

## Performance Tuning

### For High Throughput

```yaml
# In config/tempo/tempo.yaml
overrides:
  ingestion_rate_limit_bytes: 50000000  # 50MB/s
  ingestion_burst_size_bytes: 100000000 # 100MB

storage:
  trace:
    pool:
      max_workers: 200
      queue_depth: 20000
```

### For Low Latency

```yaml
# In config/tempo/tempo.yaml
ingester:
  max_block_duration: 1m     # Flush more frequently
  flush_check_period: 5s     # Check more often

querier:
  search:
    query_timeout: 10s       # Faster timeout
```

## Security

### Production Considerations

1. **Authentication**: Enable multi-tenancy in production
2. **Network**: Use TLS for all endpoints
3. **Access Control**: Restrict access to Tempo API
4. **Data Privacy**: Consider trace sampling for sensitive data

### Enable Basic Security

```yaml
# In config/tempo/tempo.yaml (example - not enabled by default)
auth_enabled: true
multitenancy_enabled: true

server:
  http_tls_config:
    cert_file: /path/to/cert.pem
    key_file: /path/to/key.pem
```

## Additional Resources

- **Tempo Documentation**: https://grafana.com/docs/tempo/latest/
- **OpenTelemetry**: https://opentelemetry.io/docs/
- **Jaeger Client**: https://www.jaegertracing.io/docs/
- **Zipkin**: https://zipkin.io/

## Support

For issues specific to this deployment:
1. Check logs: `docker compose logs tempo`
2. Validate configuration: `docker compose config tempo`
3. Review this operations guide
4. Check the main README.md for general troubleshooting
