# Grafana Alloy Operations

## Overview

Grafana Alloy is the successor to Promtail for collecting container logs and forwarding them to Loki. It uses the River configuration language and provides a unified approach to log collection with metrics and trace support.

**Current Version:** 1.1.0

## Architecture

```
Docker Host
  ├─ Container 1 (logs) ──┐
  ├─ Container 2 (logs) ──┼─→ Alloy (River config) ──→ Loki (3100)
  └─ Container N (logs) ──┘
```

### Log Flow

1. **Alloy's Docker Source** (`loki.source.docker`)
   - Mounts `/var/run/docker.sock` to discover running containers
   - Scrapes stdout/stderr logs from all containers
   - Attaches metadata: container_name, container_id, compose_service, compose_project

2. **Pipeline Processing** (`loki.process`)
   - Parses Docker JSON log format
   - Extracts labels from container metadata
   - Enriches log entries with compose labels

3. **Loki Write** (`loki.write`)
   - Sends processed logs to Loki via HTTP push API
   - Configurable retry and batching behavior

## Deployment

### Start the Observability Stack

```bash
# Start with Alloy (included in 'core' profile)
docker compose up --profile core

# Verify Alloy is running
docker compose ps alloy

# Check Alloy logs
docker compose logs alloy --tail 50
```

### Verify Alloy Configuration

```bash
# Check Alloy metrics
curl -s http://localhost:12345/metrics | grep loki_source_docker

# Check Alloy status in Grafana
# 1. Open Grafana: http://localhost:3000
# 2. Go to Explore > Logs (Loki)
# 3. Query for {job="docker"} to see container logs
```

## Configuration

**Location:** `config/alloy/config.river`

### Key Components

#### 1. Logging (Server Telemetry)

```river
logging {
  level  = "info"
  format = "logfmt"
}

server {
  http {
    listen_address = "0.0.0.0"
    listen_port    = 12345
  }
}
```

#### 2. Docker Source

```river
loki.source.docker "containers" {
  host           = "unix:///var/run/docker.sock"
  positions_path = "/var/lib/alloy/positions.yaml"
  labels = {
    job = "docker"
  }
  forward_to = [loki.process.containers.receiver]
}
```

- **host**: Path to Docker daemon socket
- **positions_path**: Tracks log read positions across restarts
- **forward_to**: Chains to processing stage

#### 3. Log Processing (Docker + Labels)

```river
loki.process "containers" {
  stage.docker {}

  stage.labels {
    values = {
      stream          = "stream"
      container       = "container_name"
      container_id    = "container_id"
      compose_service = "container_label_com_docker_compose_service"
      compose_project = "container_label_com_docker_compose_project"
    }
  }

  forward_to = [loki.write.loki.receiver]
}
```

- **stage.docker**: Parses Docker JSON log entries
- **stage.labels**: Extracts metadata as Loki labels
- Enables filtering by: `{container_name="..."}`, `{compose_service="grafana"}`, etc.

#### 4. Loki Write

```river
loki.write "loki" {
  endpoint {
    url = "http://loki:3100/loki/api/v1/push"
    tls_config {
      insecure_skip_verify = true
    }
  }
}
```

## Monitoring & Health Checks

### Alloy Metrics

```bash
# View Alloy metrics endpoint
curl -s http://localhost:12345/metrics | head -20

# Filter for docker source metrics
curl -s http://localhost:12345/metrics | grep loki_source_docker

# Check for scrape activity
curl -s http://localhost:12345/metrics | grep "scrape.*bytes"
```

### Expected Metrics

- `loki_source_docker_target_*`: Target discovery metrics
- `loki_write_*`: Write API metrics
- `alloy_*`: Alloy runtime metrics

### Common Health Checks

```bash
# 1. Alloy HTTP port is open
curl -s http://localhost:12345/metrics > /dev/null && echo "✓ Alloy metrics OK"

# 2. Alloy can reach Docker socket
docker compose logs alloy | grep -i "connected\|docker" | head -10

# 3. Loki received logs from Alloy
curl -s "http://localhost:3100/loki/api/v1/query_range?query={job=\"docker\"}&start=now-5m&end=now" \
  | jq '.data.result | length'
```

## Troubleshooting

### Alloy Not Collecting Logs

**Symptom:** Loki has no logs with `{job="docker"}`

**Root Cause:**
1. Alloy metrics show no `loki_source_docker_targets_active`
2. Docker socket permission issue
3. Alloy → Loki network connectivity

**Solutions:**

1. **Check Docker Socket Access**
   ```bash
   docker exec alloy ls -la /var/run/docker.sock
   # Should show: srw-rw---- (writable by container)
   ```

2. **Check Alloy Logs**
   ```bash
   docker compose logs alloy --tail 50 | grep -i "error\|docker\|connection"
   ```

3. **Verify Loki Connectivity**
   ```bash
   docker exec alloy curl -v http://loki:3100/ready
   # Should return 200 OK
   ```

4. **Restart Alloy**
   ```bash
   docker compose restart alloy
   # Wait 30s for discovery to complete
   sleep 30
   
   docker compose logs alloy --tail 20
   ```

### Alloy High Memory Usage

**Root Cause:**
- Large number of containers generating high log volume
- Positions file growing unbounded

**Solution:**

1. **Reduce batch size** (config.river):
   ```river
   # Add to loki.process if using write cache
   forward_to = [loki.write.loki.receiver]
   ```

2. **Rotate positions file**:
   ```bash
   docker exec alloy rm /var/lib/alloy/positions.yaml
   docker compose restart alloy
   ```

### Missing Labels in Logs

**Symptom:** Logs appear but lack `compose_service` or `container` labels

**Cause:** Docker container doesn't have compose labels

**Solution:**

Check if container has compose labels:
```bash
docker inspect <container_name> | jq '.Config.Labels'

# If missing, ensure container is started via:
docker compose up -d <service>
```

## Performance Tuning

### Reduce Log Volume

In `config/alloy/config.river`, add filter stages:

```river
loki.process "containers" {
  stage.docker {}
  
  # Drop noisy services
  stage.drop {
    expression = "{{ .container_name | contains(\"debug\") }}"
  }

  stage.labels {
    values = {
      stream          = "stream"
      container       = "container_name"
      compose_service = "container_label_com_docker_compose_service"
      compose_project = "container_label_com_docker_compose_project"
    }
  }

  forward_to = [loki.write.loki.receiver]
}
```

### Adjust Resource Limits

In `compose.yaml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'      # Increase if high CPU usage
      memory: 1G       # Increase if OOM kills
    reservations:
      cpus: '0.25'
      memory: 256M
```

## Query Examples in Grafana

### All Docker Container Logs

```logql
{job="docker"}
```

### Specific Service

```logql
{compose_service="grafana"}
```

### Error Logs (stderr)

```logql
{job="docker", stream="stderr"}
```

### Combine with Metrics & Traces

In Grafana dashboards:
1. **Logs**: `{compose_service="my-service"}`
2. **Metrics**: `rate(container_cpu_usage_seconds[5m])`
3. **Traces**: Link via derived fields (configured in datasources.yaml)

## Migration from Promtail

**Key Differences:**

| Aspect | Promtail | Alloy |
|--------|----------|-------|
| Config Format | YAML | River (HCL-like) |
| Log Processing | Multiple job configs | Unified pipelines |
| Metrics | `/metrics` on 9080 | `/metrics` on 12345 |
| Docker Integration | Job with docker_sd | Native `loki.source.docker` |
| Position Tracking | `/tmp/positions.yaml` | `/var/lib/alloy/positions.yaml` |
| Community Support | Deprecated | Active development |

**Migration Checklist:**
- [x] Update compose.yaml (alloy replaces promtail)
- [x] Create config/alloy/config.river from promtail.yaml logic
- [x] Mount data/alloy for state persistence
- [x] Update tests to check alloy metrics (port 12345)
- [x] Update docs (this file)
- [x] Remove old promtail config and references

## References

- **Alloy Docs**: https://grafana.com/docs/alloy/latest/
- **River Config**: https://grafana.com/docs/alloy/latest/concepts/config-language/
- **Loki Integration**: https://grafana.com/docs/alloy/latest/reference/components/loki/
- **Docker Source**: https://grafana.com/docs/alloy/latest/reference/components/loki.source.docker/

## Support & Debugging

### Common River Config Errors

```bash
# Validate config syntax
docker exec alloy alloy eval config.river

# Check for runtime errors
docker compose logs alloy | grep -i "error\|failed\|invalid"
```

### Enable Debug Logging

In `compose.yaml`, update Alloy command:
```yaml
command:
  - "run"
  - "--config.file=/etc/alloy/config.river"
  - "--log.level=debug"   # Add this
```

### Report Issues

If Alloy is not collecting logs:
1. Check `docker compose logs alloy --tail 100`
2. Verify `http://localhost:12345/metrics` returns data
3. Confirm `{job="docker"}` query returns logs in Grafana Explore

## Next Steps

- Monitor Alloy metrics in the **Observability Stack Health** dashboard
- Configure log retention in Loki (default: 744h / 31 days)
- Set up alerting for high error rates in containers
- Use derived fields in Loki datasource to link to traces (see datasources.yaml)
