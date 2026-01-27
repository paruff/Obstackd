# Media-Refinery Integration Example

## Required Changes to Media-Refinery

To connect Media-Refinery to Obstackd, make these changes to `Media-Refinery/docker-compose.yml`:

### 1. Update Networks Section

**Replace:**
```yaml
networks:
  media-refinery-network:
    driver: bridge
```

**With:**
```yaml
networks:
  media-refinery-network:
    driver: bridge
  observability-lab:
    external: true
    name: observability-lab
```

### 2. Update media-refinery Service

**Add to the `media-refinery` service:**

```yaml
services:
  media-refinery:
    # ... existing config ...
    networks:
      - media-refinery-network
      - observability-lab    # Add this line
    environment:
      # ... existing environment vars ...
      # Update these OTel variables:
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
      - OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
      - OTEL_SERVICE_NAME=media-refinery
      - OTEL_RESOURCE_ATTRIBUTES=service.namespace=media-processing,service.version=1.0.0
      - OTEL_TRACES_EXPORTER=otlp
      - OTEL_METRICS_EXPORTER=otlp
      - OTEL_LOGS_EXPORTER=otlp
      # Update Loki URL:
      - LOKI_URL=http://loki:3100/loki/api/v1/push
    # Remove this section (no longer needed):
    # extra_hosts:
    #   - "host.docker.internal:host-gateway"
```

### 3. Update Other Services (Optional)

For beets, tdarr, radarr, sonarr, plex - if you want their logs in Obstackd:

```yaml
services:
  beets:
    # ... existing config ...
    networks:
      - media-refinery-network
      - observability-lab    # Add this

  tdarr:
    # ... existing config ...
    networks:
      - media-refinery-network
      - observability-lab    # Add this

  # ... same for radarr, sonarr, plex ...
```

## Complete Patch

Apply these changes to `/path/to/Media-Refinery/docker-compose.yml`:

```diff
--- docker-compose.yml.old
+++ docker-compose.yml
@@ -19,6 +19,7 @@
       - TZ=America/New_York
       # OpenTelemetry Configuration
-      - OTEL_EXPORTER_OTLP_ENDPOINT=http://host.docker.internal:4318
+      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
       - OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
       - OTEL_SERVICE_NAME=media-refinery
@@ -28,7 +29,7 @@
       - OTEL_LOGS_EXPORTER=otlp
       # Loki logging
-      - LOKI_URL=http://host.docker.internal:3100/loki/api/v1/push
+      - LOKI_URL=http://loki:3100/loki/api/v1/push
     logging:
       driver: "json-file"
@@ -50,8 +51,8 @@
     restart: unless-stopped
     networks:
       - media-refinery-network
-    extra_hosts:
-      - "host.docker.internal:host-gateway"
+      - observability-lab
     deploy:
       resources:
@@ -300,6 +301,9 @@
 networks:
   media-refinery-network:
     driver: bridge
+  observability-lab:
+    external: true
+    name: observability-lab
 
 volumes:
   input:
```

## Deployment Steps

### 1. Ensure Obstackd is Running

```bash
cd /path/to/Obstackd
docker compose --profile core up -d
docker network ls | grep observability-lab  # Verify network exists
```

### 2. Apply Changes to Media-Refinery

```bash
cd /path/to/Media-Refinery
# Edit docker-compose.yml with the changes above
docker compose down
docker compose up -d
```

### 3. Verify Connectivity

```bash
# Test from Media-Refinery container
docker exec media-refinery curl -v http://otel-collector:4318/
docker exec media-refinery curl -v http://loki:3100/ready
docker exec media-refinery curl -v http://prometheus:9090/-/healthy
```

### 4. Add Prometheus Scrape Job (Optional)

If Media-Refinery exposes Prometheus metrics, edit `Obstackd/config/prometheus/prometheus.yaml`:

```yaml
scrape_configs:
  # ... existing jobs ...

  # Media-Refinery metrics
  - job_name: 'media-refinery'
    static_configs:
      - targets: ['media-refinery:9090']  # Adjust port if different
        labels:
          component: 'media-refinery'
          service: 'media-processing'
    scrape_interval: 15s
    metrics_path: '/metrics'
    scheme: 'http'
```

Then restart Prometheus:

```bash
cd /path/to/Obstackd
docker compose restart prometheus
```

### 5. Verify Telemetry Flow

#### Check OTel Collector
```bash
# Check collector metrics
curl http://localhost:8888/metrics | grep -i "receiver.*media"

# Check collector logs
docker logs otel-collector --tail 50
```

#### Check Prometheus
```bash
# Check targets
curl 'http://localhost:9090/api/v1/targets' | jq '.data.activeTargets[] | select(.labels.component=="media-refinery")'

# Query for media-refinery metrics
curl 'http://localhost:9090/api/v1/query?query=up{component="media-refinery"}' | jq
```

#### Check Grafana
1. Open http://localhost:3000
2. Go to Explore
3. Select "Loki" datasource
4. Query: `{container_name="media-refinery"}`
5. Should see Media-Refinery logs

## Troubleshooting

### Issue: Container can't resolve 'otel-collector'

**Cause:** Container not on observability-lab network

**Solution:**
```bash
# Inspect container
docker inspect media-refinery | grep -A 20 Networks

# Should show both networks:
# - media-refinery-network
# - observability-lab

# If missing, recreate container
docker compose up -d --force-recreate media-refinery
```

### Issue: No logs in Grafana

**Cause:** Media-Refinery doesn't have OpenTelemetry SDK for logs

**Solution:** Use Docker log shipping with Promtail

Edit `Obstackd/config/promtail/promtail.yaml`:

```yaml
scrape_configs:
  # ... existing configs ...

  - job_name: media-refinery-logs
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        filters:
          - name: name
            values: ["media-refinery"]
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        target_label: 'container_name'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'stream'
```

Then mount Docker socket in Promtail service (already configured).

### Issue: Telemetry works but no traces

**Cause:** Media-Refinery Go code doesn't have OpenTelemetry SDK instrumentation

**Solution:** This requires code changes to Media-Refinery. The environment variables alone won't generate traces without SDK instrumentation in the code.

See: [Adding OpenTelemetry to Go Applications](https://opentelemetry.io/docs/languages/go/getting-started/)

## Expected Results

After successful integration:

✅ Media-Refinery logs visible in Grafana (Loki datasource)
✅ Container metrics visible (if Prometheus scrape configured)
✅ Network connectivity between stacks
✅ Traces visible (only if Media-Refinery has OTel SDK)
✅ All Media-Refinery services accessible via DNS

## Next Steps

1. **Add OpenTelemetry SDK to Media-Refinery Go code** for full observability
2. **Create custom Grafana dashboards** for Media-Refinery metrics
3. **Configure alerts** in Prometheus for Media-Refinery failures
4. **Add other application stacks** using the same pattern
