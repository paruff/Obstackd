# Telemetry Generator

Simple Flask application that generates OpenTelemetry metrics, logs, and traces for testing the observability stack.

## Endpoints

- `GET /` - Health check and service info
- `GET /generate` - Generate telemetry (trace, logs, metrics)
- `GET /error` - Generate error trace/log for testing
- `GET /slow` - Generate slow request (1-3s) for latency testing

## Telemetry Generated

### Traces
- Automatic HTTP spans via Flask instrumentation
- Custom spans for operations
- Span attributes: operation.id, operation.type, duration, error

### Logs
- Structured logs with trace correlation
- INFO: Normal operations
- WARNING: Slow requests
- ERROR: Intentional errors

### Metrics
- `requests_total` (counter): Total requests by endpoint and status
- `processing_duration_seconds` (histogram): Request processing time

## Usage

Start the stack:
```bash
docker compose --profile apps up -d
```

Generate telemetry:
```bash
# Normal request
curl http://localhost:5000/generate

# Generate errors
curl http://localhost:5000/error

# Generate slow traces
curl http://localhost:5000/slow

# Generate load
for i in {1..10}; do curl http://localhost:5000/generate; done
```

## Verification

View in Grafana:
- Traces: http://localhost:3000/explore → Tempo
- Logs: http://localhost:3000/explore → Loki → {compose_service="telemetry-generator"}
- Metrics: http://localhost:3000/explore → Prometheus → requests_total
