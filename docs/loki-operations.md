# Loki Log Aggregation - Operations Guide

## Overview

Grafana Loki provides centralized log aggregation and query capabilities for the observability stack. It ingests logs from containers via Promtail and from applications via the OpenTelemetry Collector, storing them efficiently for querying through Grafana using LogQL.

**Architecture Note:** Logs are collected through two primary paths:
1. **Container logs**: Promtail scrapes Docker container logs and forwards them to Loki
2. **Application logs**: Applications send structured logs via OTLP to the OpenTelemetry Collector, which forwards them to Loki

## Access Points

- **Loki HTTP API**: http://localhost:3100
- **Loki Ready Endpoint**: http://localhost:3100/ready
- **Loki Metrics**: http://localhost:3100/metrics
- **Loki gRPC**: localhost:9096
- **Promtail HTTP**: http://localhost:9080
- **OTLP** (for app logs, via OTel Collector): localhost:4317 (gRPC), localhost:4318 (HTTP)

## Quick Start

### Deploy Loki and Promtail

```bash
# Start the full observability stack (includes Loki and Promtail)
docker compose --profile core up -d

# Check Loki status
docker compose ps loki promtail

# Verify Loki is ready
curl http://localhost:3100/ready

# Check Promtail targets
curl -s http://localhost:9080/targets | jq '.activeTargets'
```

### Query Logs

```bash
# Query all logs from last hour
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="docker"}' \
  --data-urlencode "start=$(date -u -d '1 hour ago' +%s)000000000" \
  --data-urlencode "end=$(date -u +%s)000000000" | jq '.'

# Query specific container logs
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={container="grafana"}' \
  --data-urlencode "start=$(date -u -d '1 hour ago' +%s)000000000" \
  --data-urlencode "end=$(date -u +%s)000000000" | jq '.data.result'
```

## Configuration

### Main Configuration

Location: `config/loki/loki.yaml`

**Key Settings:**
- **Retention Period**: 7 days (168h)
- **Storage**: Local filesystem (`./data/loki`)
- **Ingestion Rate Limit**: 10MB/s with 20MB burst
- **Schema**: TSDB v13 (latest, optimized)

### Promtail Configuration

Location: `config/promtail/promtail.yaml`

**Key Settings:**
- **Docker Service Discovery**: Automatically discovers running containers
- **Labels**: Extracts container name, ID, compose service, compose project
- **Log Path**: `/var/lib/docker/containers/*/*.log`

### Data Storage

```
data/loki/
├── chunks/       # Log chunks
├── tsdb-index/   # TSDB index
├── tsdb-cache/   # Index cache
├── compactor/    # Compactor working directory
└── rules/        # Alert rules (if configured)
```

## LogQL Query Examples

### Basic Queries

```bash
# All logs
{job="docker"}

# Specific container
{container="prometheus"}

# Multiple containers
{container=~"prometheus|grafana"}

# Exclude containers
{job="docker"} != "loki"

# By compose service
{compose_service="tempo"}
```

### Filtering and Searching

```bash
# Contains "error"
{container="grafana"} |= "error"

# Contains "error" but not "context"
{container="grafana"} |= "error" != "context"

# Case-insensitive search
{container="grafana"} |~ "(?i)error"

# Regex pattern
{container="prometheus"} |~ "level=(error|warn)"

# JSON field extraction
{container="otel-collector"} | json | level="error"
```

### Aggregations and Metrics

```bash
# Count logs per container (last 5m)
sum by (container) (count_over_time({job="docker"}[5m]))

# Rate of errors per second
sum(rate({container="grafana"} |= "error" [5m]))

# Bytes processed per container
sum by (container) (bytes_over_time({job="docker"}[1h]))

# Top 5 containers by log volume
topk(5, sum by (container) (count_over_time({job="docker"}[1h])))
```

### Trace Correlation

```bash
# Find logs for a specific trace
{job="docker"} |~ "traceID=abc123def456"

# Extract trace ID and filter
{job="docker"} | json | trace_id="abc123def456"

# Logs around a specific trace (±5 minutes)
{job="docker"} |~ "traceID=abc123def456" [10m]
```

## Grafana Integration

### Querying Logs in Grafana

1. **Navigate to Explore**: http://localhost:3000/explore
2. **Select Loki datasource** from the dropdown
3. **Enter LogQL query** in the query builder
4. **Select time range** from the time picker
5. **View logs** in the results panel

### Log-Trace Correlation

The Loki datasource is configured with trace correlation:
- Grafana automatically detects `traceID=<value>` patterns in logs
- Click on a trace ID to jump to Tempo
- In Tempo, click "Logs for this span" to return to related logs

### Example Grafana Queries

**Log Volume Dashboard:**
```
sum by (container) (count_over_time({job="docker"}[1m]))
```

**Error Rate Panel:**
```
sum(rate({job="docker"} |= "error" [5m])) by (container)
```

**Log Table:**
```
{job="docker"} | json
```

## Health Checks

### Loki Health

```bash
# Ready check
curl -f http://localhost:3100/ready

# Metrics endpoint
curl -s http://localhost:3100/metrics | grep loki_

# Ring status (for distributed mode)
curl -s http://localhost:3100/ring

# Build info
curl -s http://localhost:3100/loki/api/v1/status/buildinfo | jq '.'
```

### Promtail Health

```bash
# Targets (discovered containers)
curl -s http://localhost:9080/targets | jq '.activeTargets | length'

# Metrics
curl -s http://localhost:9080/metrics | grep promtail_

# Service discovery status
curl -s http://localhost:9080/service-discovery | jq '.'
```

## Operational Tasks

### Verify Log Ingestion

```bash
# Check if logs are flowing to Loki
curl -G -s "http://localhost:3100/loki/api/v1/query" \
  --data-urlencode 'query=count_over_time({job="docker"}[1m])' | jq '.data.result'

# List all unique labels
curl -s "http://localhost:3100/loki/api/v1/labels" | jq '.data'

# List values for a specific label
curl -s "http://localhost:3100/loki/api/v1/label/container/values" | jq '.data'
```

### Monitor Retention

```bash
# Check oldest logs
curl -G -s "http://localhost:3100/loki/api/v1/query" \
  --data-urlencode 'query={job="docker"}' \
  --data-urlencode 'limit=1' \
  --data-urlencode 'direction=backward' | jq '.data.result[0].values[0][0]'

# Expected: Timestamps should be within the last 7 days (168 hours)
```

### Troubleshooting

**No logs appearing:**
```bash
# 1. Check Promtail is running and discovering containers
docker compose logs promtail | tail -50
curl -s http://localhost:9080/targets | jq '.activeTargets | length'

# 2. Check Loki ingestion
docker compose logs loki | tail -50
curl -s http://localhost:3100/metrics | grep loki_ingester_

# 3. Verify container logs exist
docker compose logs grafana | head -10

# 4. Test direct push to Loki
curl -i -X POST "http://localhost:3100/loki/api/v1/push" \
  -H "Content-Type: application/json" \
  -d '{"streams":[{"stream":{"job":"test"},"values":[["'$(date +%s)000000000'","test log message"]]}]}'
```

**High memory usage:**
```bash
# Check ingestion rate
curl -s http://localhost:3100/metrics | grep loki_distributor_bytes_received_total

# Check cache size
curl -s http://localhost:3100/metrics | grep loki_cache_

# Adjust limits in config/loki/loki.yaml:
# - ingestion_rate_mb
# - per_stream_rate_limit
```

**Slow queries:**
```bash
# Enable query logging (already enabled in config)
# Check query metrics
curl -s http://localhost:3100/metrics | grep loki_query_

# Optimize queries:
# - Narrow time range
# - Use specific label matchers
# - Avoid unbounded queries
```

## Log Shipping from Applications

### OpenTelemetry SDK (Recommended)

Applications should use OpenTelemetry SDK to send structured logs via OTLP to the collector:

**Python Example:**
```python
from opentelemetry import logs
from opentelemetry.sdk.logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk.logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc.logs_exporter import OTLPLogExporter

# Configure OTLP exporter
exporter = OTLPLogExporter(endpoint="localhost:4317", insecure=True)

# Set up logger provider
provider = LoggerProvider()
provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
logs.set_logger_provider(provider)

# Use with standard logging
import logging
handler = LoggingHandler(logger_provider=provider)
logging.basicConfig(level=logging.INFO, handlers=[handler])

# Add trace correlation
logging.info("Operation completed", extra={"traceID": "abc123"})
```

**Go Example:**
```go
import (
    "go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc"
    "go.opentelemetry.io/otel/sdk/log"
)

exporter, _ := otlploggrpc.New(context.Background(),
    otlploggrpc.WithEndpoint("localhost:4317"),
    otlploggrpc.WithInsecure(),
)

provider := log.NewLoggerProvider(
    log.WithProcessor(log.NewBatchProcessor(exporter)),
)
```

### Log Format Best Practices

**Structured JSON:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "error",
  "message": "Database connection failed",
  "service": "api-server",
  "traceID": "abc123def456",
  "spanID": "def456",
  "error": "connection timeout",
  "database": "postgres-primary"
}
```

**Include Trace Context:**
- Always include `traceID` for correlation
- Include `spanID` when available
- Use consistent field names

## Backup and Recovery

### Backup Loki Data

```bash
# Stop Loki
docker compose stop loki

# Backup data directory
tar -czf loki-backup-$(date +%Y%m%d).tar.gz -C data/loki .

# Restart Loki
docker compose start loki
```

### Restore from Backup

```bash
# Stop Loki
docker compose stop loki

# Clear existing data
rm -rf data/loki/*

# Restore
tar -xzf loki-backup-20240115.tar.gz -C data/loki/

# Restart Loki
docker compose start loki
```

## Performance Tuning

### Ingestion Performance

**In `config/loki/loki.yaml`:**
```yaml
limits_config:
  ingestion_rate_mb: 20           # Increase if dropping logs
  ingestion_burst_size_mb: 40     # 2x ingestion_rate_mb
  per_stream_rate_limit: 10MB     # Per-stream limit
```

### Query Performance

**Enable caching:**
```yaml
query_range:
  cache_results: true
  max_retries: 5
  parallelise_shardable_queries: true
```

**Index optimization:**
```yaml
schema_config:
  configs:
    - index:
        period: 24h   # Smaller = more indexes, better queries
```

## Security Considerations

### Authentication (Not Enabled)

This setup runs without authentication for local development. For production:

1. Enable `auth_enabled: true` in `loki.yaml`
2. Configure tenants
3. Add authentication to Promtail and OTel Collector

### Network Security

- Loki and Promtail run on the internal Docker network
- Only essential ports are exposed to localhost
- No external access by default

### Sensitive Data

**Avoid logging:**
- Passwords and API keys
- Personal Identifiable Information (PII)
- Credit card numbers
- Session tokens

**Use log scrubbing:**
```yaml
# In promtail.yaml pipeline_stages:
- replace:
    expression: 'password=\S+'
    replace: 'password=***'
```

## Maintenance

### Regular Tasks

**Daily:**
- Monitor ingestion rate and storage growth
- Check for error logs in Loki and Promtail

**Weekly:**
- Review retention and compaction metrics
- Verify backups if enabled

**Monthly:**
- Review and optimize query patterns
- Check for Loki/Promtail updates

### Compaction

Compaction runs automatically (configured interval: 10 minutes):

```bash
# Check compaction status
curl -s http://localhost:3100/metrics | grep loki_compactor_

# Compactor metrics to watch:
# - loki_compactor_running: Should be 1
# - loki_compactor_blocks_marked_for_deletion_total
# - loki_compactor_blocks_cleaned_total
```

### Retention Enforcement

Retention is automatically enforced:

```bash
# Verify retention settings
curl -s http://localhost:3100/config | jq '.limits_config.retention_period'

# Check deleted chunks
curl -s http://localhost:3100/metrics | grep loki_compactor_deleted_
```

## Integration Examples

### Kubernetes Logs (if deployed to K8s)

```yaml
# Add to promtail.yaml
scrape_configs:
  - job_name: kubernetes-pods
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
```

## References

- **Loki Documentation**: https://grafana.com/docs/loki/v2.9.x/
- **LogQL Guide**: https://grafana.com/docs/loki/v2.9.x/query/
- **Promtail Configuration**: https://grafana.com/docs/loki/v2.9.x/send-data/promtail/configuration/
- **Best Practices**: https://grafana.com/docs/loki/v2.9.x/operations/best-practices/

## Support

For issues:
1. Check Docker logs: `docker compose logs loki promtail`
2. Verify configuration syntax: `docker compose config`
3. Review this guide's troubleshooting section
4. Check Grafana Loki GitHub issues
