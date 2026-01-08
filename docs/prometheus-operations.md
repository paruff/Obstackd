# Prometheus Service Operations Guide

## Overview

This document provides operational guidance for the Prometheus service in the Obstackd observability stack. Prometheus is configured for production-grade reliability with health checks, resource limits, and structured logging.

## Service Access

| Endpoint | URL | Purpose |
|----------|-----|---------|
| **Web UI** | http://localhost:9090 | Query interface and service status |
| **Metrics** | http://localhost:9090/metrics | Prometheus self-monitoring metrics |
| **Health Check** | http://localhost:9090/-/healthy | Liveness probe |
| **Ready Check** | http://localhost:9090/-/ready | Readiness probe |
| **API** | http://localhost:9090/api/v1/* | Query API |
| **Targets** | http://localhost:9090/targets | Scrape target status |

## Common Operations

### Starting the Service

```bash
# Start Prometheus with the core profile
docker compose --profile core up -d prometheus

# Verify it's running
docker compose ps prometheus
```

### Checking Service Health

```bash
# Check if Prometheus is healthy
curl -f http://localhost:9090/-/healthy

# Check if Prometheus is ready to serve requests
curl -f http://localhost:9090/-/ready

# Check container health status
docker compose ps --format "table {{.Service}}\t{{.Status}}"
```

### Reloading Configuration

Prometheus supports hot-reload of configuration without restarting:

```bash
# Reload configuration (requires --web.enable-lifecycle flag)
curl -X POST http://localhost:9090/-/reload

# Verify the configuration was reloaded successfully
curl -s http://localhost:9090/api/v1/status/config | jq '.data.yaml' | head -20

# Check for reload errors in logs
docker compose logs --tail=50 prometheus | grep -i reload
```

### Viewing Logs

```bash
# View recent logs
docker compose logs --tail=100 prometheus

# Follow logs in real-time
docker compose logs -f prometheus

# View logs with timestamps
docker compose logs -t prometheus

# Search for errors
docker compose logs prometheus | grep -i error
```

### Querying Metrics

```bash
# Get all Prometheus metrics
curl -s http://localhost:9090/metrics

# Query via API (example: up metric)
curl -s 'http://localhost:9090/api/v1/query?query=up' | jq

# Query with time range
curl -s 'http://localhost:9090/api/v1/query_range?query=up&start=2024-01-01T00:00:00Z&end=2024-01-01T01:00:00Z&step=15s' | jq
```

### Checking Scrape Targets

```bash
# View all configured targets
curl -s http://localhost:9090/api/v1/targets | jq

# View targets in UI
open http://localhost:9090/targets
```

### Stopping the Service

```bash
# Stop Prometheus (graceful shutdown)
docker compose stop prometheus

# Stop and remove container (preserves data)
docker compose down prometheus

# Stop and remove all data (clean slate)
docker compose down -v prometheus
```

## Data Management

### Data Location

- **Configuration**: `./config/prometheus/prometheus.yaml` (read-only mount)
- **Time-series data**: `./data/prometheus/` (persistent volume)
- **Logs**: Captured by Docker (use `docker compose logs`)

### Checking Storage Usage

```bash
# Check disk usage of Prometheus data
docker exec prometheus du -sh /prometheus

# Check detailed breakdown
docker exec prometheus du -h /prometheus | sort -h
```

### Data Retention

Prometheus is configured with a 30-day retention period:

```yaml
--storage.tsdb.retention.time=30d
```

Older data is automatically deleted. To modify retention:

1. Edit `compose.yaml` and change the `--storage.tsdb.retention.time` flag
2. Restart Prometheus: `docker compose restart prometheus`

### Backing Up Data

```bash
# Create a backup of time-series data
tar -czf prometheus-backup-$(date +%Y%m%d-%H%M%S).tar.gz ./data/prometheus/

# Restore from backup
docker compose down prometheus
rm -rf ./data/prometheus/*
tar -xzf prometheus-backup-YYYYMMDD-HHMMSS.tar.gz
docker compose up -d prometheus
```

## Resource Management

### Current Resource Limits

The service is configured with the following limits:

| Resource | Reservation | Limit |
|----------|-------------|-------|
| CPU | 0.5 cores | 1.0 core |
| Memory | 512 MB | 2 GB |

### Monitoring Resource Usage

```bash
# View real-time resource stats
docker stats prometheus --no-stream

# Continuous monitoring
docker stats prometheus
```

### Adjusting Resource Limits

If you need to modify resource limits, edit `compose.yaml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'      # Increase CPU limit
      memory: 4G       # Increase memory limit
    reservations:
      cpus: '1.0'
      memory: 1G
```

Then restart: `docker compose up -d prometheus`

## Troubleshooting

### Service Won't Start

1. **Check logs for errors**:
   ```bash
   docker compose logs prometheus
   ```

2. **Validate configuration**:
   ```bash
   ./scripts/prometheus/config-validator.sh
   ```

3. **Check port availability**:
   ```bash
   lsof -i :9090
   ```

4. **Verify data directory permissions**:
   ```bash
   ls -la ./data/prometheus/
   chmod 755 ./data/prometheus
   ```

### Configuration Errors

If Prometheus fails to start due to configuration errors:

1. **Validate the configuration file**:
   ```bash
   docker run --rm -v $(pwd)/config/prometheus:/etc/prometheus \
     prom/prometheus:v2.50.1 \
     promtool check config /etc/prometheus/prometheus.yaml
   ```

2. **Check for syntax errors in YAML**:
   ```bash
   yamllint config/prometheus/prometheus.yaml
   ```

3. **View detailed error messages**:
   ```bash
   docker compose logs --tail=100 prometheus | grep -i error
   ```

### Health Check Failing

If the health check reports unhealthy:

1. **Check if the service is responding**:
   ```bash
   curl -v http://localhost:9090/-/healthy
   ```

2. **Inspect the health check configuration**:
   ```bash
   docker inspect prometheus | jq '.[0].State.Health'
   ```

3. **View health check logs**:
   ```bash
   docker inspect prometheus | jq '.[0].State.Health.Log'
   ```

### High Memory Usage

If Prometheus approaches memory limits:

1. **Check current memory usage**:
   ```bash
   docker stats prometheus --no-stream
   ```

2. **Review scrape configuration** (reduce scrape_interval or targets)

3. **Reduce retention time** to free up space

4. **Increase memory limit** in `compose.yaml`

### Data Corruption

If you suspect data corruption:

1. **Check TSDB status**:
   ```bash
   docker exec prometheus promtool tsdb analyze /prometheus
   ```

2. **Restore from backup**:
   ```bash
   docker compose down prometheus
   rm -rf ./data/prometheus/*
   tar -xzf prometheus-backup-YYYYMMDD.tar.gz
   docker compose up -d prometheus
   ```

3. **Start fresh** (last resort):
   ```bash
   docker compose down prometheus
   rm -rf ./data/prometheus/*
   mkdir -p ./data/prometheus
   docker compose up -d prometheus
   ```

## Security Considerations

### Admin API

The admin API is **enabled** in this configuration with `--web.enable-admin-api`. This allows:

- Remote configuration reload
- Snapshot creation
- Time series deletion

**For production deployments**, consider:
- Disabling the admin API
- Placing Prometheus behind authentication proxy
- Using network segmentation to restrict access

### Network Exposure

Prometheus is exposed on `localhost:9090`. To restrict access:

1. Use Docker networks to isolate services
2. Implement authentication (via reverse proxy)
3. Use firewall rules to limit access

## Performance Tuning

### Query Performance

- Use recording rules for frequently-used queries
- Limit query time ranges
- Use appropriate step intervals
- Monitor query execution time in logs

### Scrape Performance

- Adjust `scrape_interval` based on needs (current: 15s)
- Use service discovery instead of static configs when possible
- Monitor scrape duration via `scrape_duration_seconds` metric

### Storage Performance

- Ensure adequate disk I/O for TSDB
- Use SSDs for better performance
- Monitor disk usage and retention policies

## Monitoring the Monitor

Prometheus monitors itself. Key metrics to watch:

```promql
# Prometheus up/down status
up{job="prometheus"}

# Scrape success rate
rate(prometheus_tsdb_head_samples_appended_total[5m])

# Memory usage
process_resident_memory_bytes{job="prometheus"}

# Storage usage
prometheus_tsdb_storage_blocks_bytes
```

## Integration with Grafana

Prometheus is pre-configured as a datasource in Grafana:

1. Access Grafana: http://localhost:3000
2. Navigate to Configuration > Data Sources
3. Prometheus datasource should be pre-configured
4. Test the connection

## Configuration Reference

Current Prometheus command-line flags:

```bash
--config.file=/etc/prometheus/prometheus.yaml      # Configuration file location
--storage.tsdb.path=/prometheus                     # Data directory
--storage.tsdb.retention.time=30d                   # Retention period
--web.console.templates=/etc/prometheus/consoles    # Console templates
--web.console.libraries=/etc/prometheus/console_libraries  # Console libraries
--web.enable-lifecycle                              # Enable config reload via API
--web.enable-admin-api                              # Enable admin API endpoints
--web.external-url=http://localhost:9090            # External URL for links
--log.level=info                                    # Log level (debug|info|warn|error)
--log.format=json                                   # Structured JSON logging
```

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Prometheus Configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
- [Prometheus Query Language (PromQL)](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Prometheus Storage](https://prometheus.io/docs/prometheus/latest/storage/)

## Support

For issues with the Obstackd observability stack:
1. Check this operations guide
2. Review logs and health checks
3. Validate configuration with provided scripts
4. Refer to the main README for architecture details
