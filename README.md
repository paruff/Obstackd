# Obstackd

## What This Is

A **Docker Compose-based observability platform** that provides a complete monitoring stack with OpenTelemetry, Prometheus, and Grafana. This is a self-hosted, GitOps-first solution designed for long-term operability and reproducibility.

**Tech Stack:**
- **OpenTelemetry Collector** (v0.99.0) - Telemetry data collection and routing
- **Prometheus** (v2.50.1) - Metrics storage and querying
- **Tempo** (v2.3.1) - Distributed tracing backend
- **Loki** (v2.9.4) - Log aggregation and querying
- **Promtail** (v2.9.4) - Log collection agent
- **Grafana** (v10.4.2) - Visualization and dashboards
- **Docker Compose** - Service orchestration

**Primary Use Case:** Provides a production-ready observability platform that can be deployed from a single `docker compose up` command, with zero manual configuration steps required.

---

## Quick Start

### Prerequisites

- **Docker** 20.10+ installed
- **Docker Compose** v2.0+ installed
- At least 4GB of free RAM
- Ports 3000, 3100, 3200, 4317, 4318, 8888, 8889, 9080, 9090, 9095, 9096, 9411, 14250, 14268 available

### Installation

1. **Clone and enter:**
   ```bash
   git clone https://github.com/<your-username>/Obstackd.git
   cd Obstackd
   ```

2. **Create data directories:**
   ```bash
   mkdir -p data/prometheus data/grafana data/tempo data/loki
   chmod -R 777 data/
   ```
   
   > **Note:** `chmod 777` is used for maximum compatibility across different Docker setups. For production deployments, consider using more restrictive permissions based on your Docker user/group configuration.

3. **Start the observability stack:**
   ```bash
   docker compose --profile core up -d
   ```

4. **Wait for services to initialize:**
   ```bash
   sleep 30
   ```

5. **Verify services are running:**
   ```bash
   docker compose ps
   ```

---

## Ports

| Service              | Port  | Purpose                      | Access URL                      |
|----------------------|-------|------------------------------|---------------------------------|
| **Grafana**          | 3000  | Visualization UI             | http://localhost:3000           |
| **Loki**             | 3100  | Log aggregation HTTP API     | http://localhost:3100           |
| **Tempo**            | 3200  | Tempo HTTP API               | http://localhost:3200           |
| **OpenTelemetry**    | 4317  | OTLP gRPC receiver           | localhost:4317                  |
| **OpenTelemetry**    | 4318  | OTLP HTTP receiver           | localhost:4318                  |
| **OpenTelemetry**    | 8888  | Collector telemetry metrics  | http://localhost:8888/metrics   |
| **OpenTelemetry**    | 8889  | App metrics (Prometheus)     | http://localhost:8889/metrics   |
| **Promtail**         | 9080  | Log collection agent HTTP    | http://localhost:9080           |
| **Prometheus**       | 9090  | Metrics storage & query UI   | http://localhost:9090           |
| **Tempo**            | 9095  | Tempo gRPC                   | localhost:9095                  |
| **Loki**             | 9096  | Loki gRPC                    | localhost:9096                  |
| **Tempo**            | 9411  | Zipkin receiver              | http://localhost:9411           |
| **Tempo**            | 14250 | Jaeger gRPC receiver         | localhost:14250                 |
| **Tempo**            | 14268 | Jaeger HTTP receiver         | http://localhost:14268          |

---

## Access & Credentials

### Grafana Dashboard
- **URL:** http://localhost:3000
- **Username:** `admin`
- **Password:** `admin`

The Prometheus datasource is pre-configured and ready to use. Tempo and Loki datasources are also pre-configured for distributed tracing and log aggregation.

---

## Health Checks

Verify that all services are operational:

```bash
# Check Prometheus
curl -f http://localhost:9090/-/ready

# Check Tempo
curl -f http://localhost:3200/ready

# Check Grafana
curl -f http://localhost:3000/api/health

# Check OpenTelemetry Collector telemetry
curl -f http://localhost:8888/metrics

# Check OpenTelemetry Collector app metrics endpoint
curl -f http://localhost:8889/metrics

# Check Loki
curl -f http://localhost:3100/ready

# Check Promtail targets
curl -f http://localhost:9080/targets
```

---

## Profiles

The system uses Docker Compose profiles to control which services run:

| Profile | Services                                                  | Purpose                  |
|---------|-----------------------------------------------------------|--------------------------|
| `core`  | otel-collector, tempo, loki, promtail, prometheus, grafana| Base observability stack |

**To start with a specific profile:**
```bash
docker compose --profile core up -d
```

---

## Configuration

All configuration is file-based and located in the `config/` directory:

```
config/
├── otel/
│   └── collector.yaml          # OpenTelemetry Collector config
├── tempo/
│   └── tempo.yaml              # Tempo distributed tracing config
├── loki/
│   └── loki.yaml               # Loki log aggregation config
├── promtail/
│   └── promtail.yaml           # Promtail log collection config
├── prometheus/
│   └── prometheus.yaml         # Prometheus scrape config
└── grafana/
    └── provisioning/
        └── datasources/
            └── datasources.yaml # Pre-configured datasources
```

All runtime data is stored in `./data/` and is excluded from version control.

---

## Stopping the Stack

```bash
# Stop all services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v
```

---

## Architecture

```
┌─────────────────┐
│  Applications   │
│  (Send OTLP)    │
└────────┬────────┘
         │ :4317/:4318
         ▼
┌─────────────────────┐
│ OpenTelemetry       │
│ Collector           │──────┬──────┬──────┐
└──────────┬──────────┘      │      │      │
           │                 │      │      │
           │ metrics         │      │      │ logs
           ▼                 │      │      ▼
   ┌──────────────┐          │      │  ┌──────────────┐
   │  Prometheus  │          │      │  │     Loki     │◄─────┐
   │   :9090      │          │      │  │    :3100     │      │
   └──────┬───────┘          │      │  └──────┬───────┘      │
          │                  │      │         │               │
          │ datasource       │      │         │ datasource    │
          ▼                  ▼      ▼         ▼               │
     ┌──────────────────────────────────┐                     │
     │          Grafana                 │                     │
     │           :3000                  │                     │
     └──────────────────────────────────┘                     │
                                                              │
┌─────────────────┐                                           │
│ Docker Engine   │                                           │
│ Container Logs  │────────────────────────────────────────┐  │
└─────────────────┘                                        │  │
                                                           ▼  │
                                                    ┌──────────────┐
                                                    │  Promtail    │
                                                    │   :9080      │
                                                    └──────────────┘
```

---

---

## Troubleshooting

### Ports Already in Use
If you see port binding errors:
```bash
# Check what's using the ports
lsof -i :3000
lsof -i :9090

# Either stop the conflicting service or modify compose.yaml port mappings
```

### Permission Denied on Data Directories
```bash
chmod -R 777 data/
```

> **Security Note:** The `chmod 777` command is used in this project's smoke tests for maximum compatibility. For production use, consider using more restrictive permissions (e.g., `chmod 755`) and proper Docker user/group configuration.

### Containers Won't Start
```bash
# Check logs
docker compose logs

# Check specific service
docker compose logs grafana
```

### Reset Everything
```bash
# Stop and remove everything
docker compose down -v

# Clean data directories
rm -rf data/prometheus/* data/grafana/* data/tempo/* data/loki/*

# Recreate
mkdir -p data/prometheus data/grafana data/tempo data/loki
chmod -R 777 data/

# Start fresh
docker compose --profile core up -d
```

---

## Observability Acceptance Test

### Purpose
This automated test validates that the complete observability pipeline is functioning correctly:
1. **OpenTelemetry Collector** → Exports self-telemetry metrics
2. **Prometheus** → Scrapes and stores OTel Collector metrics
3. **Grafana** → Queries and visualizes metrics

### Quick Start
```bash
# Ensure services are running
docker compose --profile core up -d
sleep 30

# Run the complete acceptance test
./tests/acceptance/observability-pipeline/test-otel-pipeline.sh
```

### Expected Output
```
✅ OTel Collector healthy (0s)
✅ Prometheus scraping OTel metrics (1s, 1 metrics)
✅ Grafana datasource configured (0s)
✅ SUCCESS: OTel metrics visible in Grafana
  Data points: 15
  Sample value: 123.456
========================================
✅ ACCEPTANCE TEST PASSED
========================================
```

### Manual Verification

If you prefer to verify manually:

1. **Open Grafana**: http://localhost:3000 (admin/admin)
2. **Navigate to**: Explore → Prometheus datasource
3. **Run Query**: `otelcol_process_uptime`
4. **Expected**: Graph showing uptime increasing over time

### Using the E2E Runner

The E2E runner provides additional control over test execution:

```bash
# Run with automatic service detection
./tests/acceptance/e2e-runner.sh

# Force start services before testing
./tests/acceptance/e2e-runner.sh --start-services

# Run test and clean up after
./tests/acceptance/e2e-runner.sh --cleanup

# Quick health check only
./tests/acceptance/e2e-runner.sh --scenario quick-check
```

### Test Results

Test results are saved in `tests/acceptance/observability-pipeline/reports/` with timestamped directories containing:
- `summary.md` - Human-readable test report
- `report.json` - Machine-readable results for CI/CD
- `e2e-test-evidence.md` - Detailed test evidence
- `grafana-query-response.json` - Raw Grafana API response
- `test-execution.log` - Complete execution log

### Troubleshooting

If tests fail, check:

1. **Services Running**: `docker compose ps`
2. **OTel Metrics**: `curl http://localhost:8888/metrics | grep otelcol`
3. **Prometheus Target**: http://localhost:9090/targets
4. **Grafana Health**: `curl http://localhost:3000/api/health`

### Integration with CI/CD

```yaml
# GitHub Actions example
jobs:
  observability-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run acceptance test
        run: |
          mkdir -p data/prometheus data/grafana
          chmod -R 777 data/
          docker compose --profile core up -d
          sleep 30
          ./tests/acceptance/observability-pipeline/test-otel-pipeline.sh
      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: acceptance-test-report
          path: tests/acceptance/observability-pipeline/reports/**/summary.md
```

---

## Next Steps

- **Add instrumented applications** to send telemetry (metrics, traces, and logs) to the OTLP endpoints
- **Create custom Grafana dashboards** in `config/grafana/dashboards/`
- **Configure additional Prometheus scrape targets** in `config/prometheus/prometheus.yaml`
- **Query traces in Grafana** using the Tempo datasource to visualize distributed traces
- **Query logs in Grafana** using the Loki datasource with LogQL to search and analyze logs
- **Explore log-trace correlation** to debug issues across the full observability stack

---

## Development Philosophy

This project follows these principles:
- ✅ **GitOps-first:** Everything is defined in version-controlled files
- ✅ **Reproducible:** Can be rebuilt from zero with `git clone` + `docker compose up`
- ✅ **No manual steps:** Zero UI clicks or CLI wizardry required
- ✅ **Declarative:** All configuration is explicit and file-based
- ✅ **Boring technology:** Reliable, well-documented, production-ready tools

---

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
