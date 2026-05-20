# uFawkesObs Health Runbook

This runbook covers self-monitoring alerts for the uFawkesObs platform.

## UFawkesObsServiceDown

### What to check
- `docker compose ps` for unhealthy or exited services
- `docker compose logs <service>` for recent errors
- `up{plane="obstackd"}` in Prometheus to confirm missing targets

### Remediation
- Restart the failed service: `docker compose restart <service>`
- If healthchecks keep failing, inspect mounted config and volume permissions under `./data/`
- Verify network connectivity on `observability-lab`

## UFawkesObsPrometheusStorageHigh

### What to check
- `prometheus_tsdb_storage_blocks_bytes` trend in Grafana
- Host free space for `./data/prometheus`
- Retention policy (`--storage.tsdb.retention.time=30d`)

### Remediation
- Free host disk space or move Prometheus data to a larger volume
- Reduce cardinality/noisy metrics
- Reduce retention window if required

## UFawkesObsLokiIngestionDropped

### What to check
- `loki_ingester_streams_created_total` and `loki_distributor_lines_received_total`
- Loki logs for rate-limit or backpressure errors
- Alloy logs for retry/drop messages

### Remediation
- Scale down noisy log sources
- Increase Loki resources and tune ingestion limits
- Verify Alloy can reach `http://loki:3100`

## UFawkesObsTempoStorageHigh

### What to check
- Host filesystem usage from `node_filesystem_*` metrics
- Disk usage under `./data/tempo`
- Tempo compaction behavior and block growth

### Remediation
- Free space on the host filesystem containing `./data/tempo`
- Move Tempo data path to a larger disk
- Tune retention/compaction settings for trace storage

## UFawkesObsOtelCollectorDropped

### What to check
- `otelcol_processor_dropped_spans` and `otelcol_exporter_send_failed_spans`
- OTel Collector logs for queue overflow or exporter failures
- Downstream endpoint health (`tempo`, `loki`, `prometheus`)

### Remediation
- Increase collector resources and queue capacity
- Reduce incoming telemetry burst volume
- Fix downstream failures before restarting collector

## UFawkesObsContainerRestarting

### What to check
- `changes(process_start_time_seconds[15m])` by job
- `docker compose ps --all` restart counts
- Service logs around restart timestamp

### Remediation
- Fix crash-loop cause from logs/config
- Verify mounted files and data permissions
- Restart only after fixing root cause to avoid repeated restarts
