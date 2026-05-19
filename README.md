# uFawkesObs

## What This Is

uFawkesObs is for small-to-medium engineering teams (3–15 people) running Docker Compose workloads who want production-grade metrics, logs, and traces without a SaaS observability bill.

It is a Docker Compose-based observability platform that provides the OpenTelemetry, Prometheus, Loki, Tempo, Alertmanager, and Grafana infrastructure needed to collect, store, and query telemetry in one place.

uFawkesObs provides the observability substrate required for DORA measurement — DORA dashboard integration is on the roadmap (see M4).

**Tech Stack:**
- **OpenTelemetry Collector** (v0.103.1) - Telemetry data collection and routing
- **Prometheus** (v2.52.0) - Metrics storage and querying
- **Alertmanager** (v0.27.0) - Alert management and routing
- **Tempo** (v2.5.0) - Distributed tracing backend
- **Loki** (v2.9.10) - Log aggregation and querying
- **Alloy** (v1.12.2) - Log and telemetry collection agent
- **Grafana** (v10.4.5) - Visualization and dashboards
- **Docker Compose** - Service orchestration

**Primary Use Case:** Provides a self-hosted observability foundation deployable with `make up`. Configure secure Grafana credentials in `.env` first. Startup validation blocks insecure deployments.

**Multi-Stack Support:** Designed to serve as a centralized observability platform for multiple Docker Compose applications. See [Multi-Stack Integration Guide](docs/multi-stack-integration.md) for connecting other applications.

---

## What This Is Not

- Not a DORA metrics generator — it is the instrumentation substrate that makes DORA measurement possible.
- Not a replacement for Grafana Cloud or Datadog for teams with >50 engineers or multi-region deployments.
- Not horizontally scalable in this release — single-instance only.
- Not multi-tenant — all telemetry shares one Prometheus, Loki, and Tempo instance.

---

## Part of the Fawkes IDP

uFawkesObs is the observability plane in the [Fawkes IDP](https://github.com/paruff/fawkes) family.

- **uFawkesObs**: observability plane (metrics, logs, traces, dashboards)
- **deliveryd** (also referred to as **uFawkesPipe**): CI/CD plane for pipeline orchestration and deployment event flow
- **developerd** (also referred to as **uFawkesDevX**): developer plane for local development workflows and tooling

In this architecture, uFawkesObs provides the telemetry substrate; higher-level delivery and developer planes provide the event context needed for end-to-end DORA measurement.

---

## Quick Start

### Prerequisites

- **Docker** 20.10+ installed
- **Docker Compose** v2.0+ installed
- At least 4GB of free RAM
- Ports 3000, 3100, 3200, 4317, 4318, 8888, 8889, 9090, 9093, 9095, 9096, 9411, 12345, 14250, 14268 available

### Installation

1. **Clone and enter:**
   ```bash
   git clone https://github.com/paruff/uFawkesObs.git
   cd uFawkesObs
   ```

2. **Create and configure environment variables:**
   ```bash
   cp .env.example .env
   $EDITOR .env
   ```
   Set both `GRAFANA_ADMIN_USER` and `GRAFANA_ADMIN_PASSWORD` in `.env`.

3. **Create data directories:**
   ```bash
   mkdir -p data/prometheus data/grafana data/tempo data/loki data/alertmanager data/alloy
   chmod -R 777 data/
   ```
   
   > **Note:** `chmod 777` is used for maximum compatibility across different Docker setups. For production deployments, consider using more restrictive permissions based on your Docker user/group configuration.

4. **Start the observability stack:**
   ```bash
   make up
   ```

5. **Wait for services to initialize:**
   ```bash
   sleep 30
   ```

6. **Verify services are running:**
   ```bash
   docker compose ps
   ```

---

## Ports

| Service                   | Port  | Purpose                      | Access URL                      |
|---------------------------|-------|------------------------------|---------------------------------|
| **Grafana**               | 3000  | Visualization UI             | http://localhost:3000           |
| **Loki**                  | 3100  | Log aggregation HTTP API     | http://localhost:3100           |
| **Tempo**                 | 3200  | Tempo HTTP API               | http://localhost:3200           |
| **OpenTelemetry**         | 4317  | OTLP gRPC receiver           | localhost:4317                  |
| **OpenTelemetry**         | 4318  | OTLP HTTP receiver           | localhost:4318                  |
| **OpenTelemetry**         | 8888  | Collector telemetry metrics  | http://localhost:8888/metrics   |
| **OpenTelemetry**         | 8889  | App metrics (Prometheus)     | http://localhost:8889/metrics   |
| **Prometheus**            | 9090  | Metrics storage & query UI   | http://localhost:9090           |
| **Alertmanager**          | 9093  | Alert management UI          | http://localhost:9093           |
| **Tempo**                 | 9095  | Tempo gRPC                   | localhost:9095                  |
| **Loki**                  | 9096  | Loki gRPC                    | localhost:9096                  |
| **Tempo**                 | 9411  | Zipkin receiver              | http://localhost:9411           |
| **Alloy**                 | 12345 | Alloy HTTP/metrics           | http://localhost:12345          |
| **Tempo**                 | 14250 | Jaeger gRPC receiver         | localhost:14250                 |
| **Tempo**                 | 14268 | Jaeger HTTP receiver         | http://localhost:14268          |
| **Telemetry Generator**   | 5001  | Demo app (apps profile)      | http://localhost:5001           |

---

## Access & Credentials

### Grafana Dashboard
- **URL:** http://localhost:3000
- **Username:** `GRAFANA_ADMIN_USER` from `.env` (default in `.env.example`: `admin`)
- **Password:** `GRAFANA_ADMIN_PASSWORD` from `.env` (validated by `make check-env`)

The Prometheus, Tempo, Loki, and Alertmanager datasources are pre-configured and ready to use.

### Alertmanager
- **URL:** http://localhost:9093
- Pre-configured with webhook receivers for testing
- Alert rules automatically loaded from Prometheus

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

# Check Alloy
curl -f http://localhost:12345/-/ready

# Check Alertmanager
curl -f http://localhost:9093/-/healthy

# View active alerts
curl -s http://localhost:9093/api/v2/alerts | jq .
```

---

## Profiles

The system uses Docker Compose profiles to control which services run:

| Profile | Services                                                              | Purpose                  |
|---------|-----------------------------------------------------------------------|--------------------------|
| `core`  | otel-collector, tempo, loki, alloy, alertmanager, prometheus, grafana | Base observability stack |
| `apps`  | telemetry-generator                                                   | Demo telemetry generator |

**To start with a specific profile:**
```bash
make up

# To also run the demo telemetry generator:
make up-apps
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
├── alloy/
│   └── config.river            # Alloy log collection config (River format)
├── alertmanager/
│   └── alertmanager.yml        # Alertmanager routing config
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
   │   :9090      │◄────────►│      │  │    :3100     │      │
   └──────┬───────┘  alerts  │      │  └──────┬───────┘      │
          │                  │      │         │               │
          │ datasource       │traces│         │ datasource    │
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
                                                    │    Alloy     │
                                                    │   :12345     │
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
rm -rf data/prometheus/* data/grafana/* data/tempo/* data/loki/* data/alertmanager/* data/alloy/*

# Recreate
mkdir -p data/prometheus data/grafana data/tempo data/loki data/alertmanager data/alloy
chmod -R 777 data/

# Start fresh
make up
```

---

## Testing

### Unit Tests for Configuration Validation

The repository includes comprehensive unit tests that validate configuration files for all observability components. These tests catch configuration errors early in the development cycle, before deployment.

**Validated components:**
- OpenTelemetry Collector
- Prometheus
- Grafana
- Tempo
- Loki

**Running unit tests:**

```bash
# Install dependencies
pip install -r tests/unit/requirements.txt

# Run all unit tests
pytest tests/unit/

# Run tests for a specific component
pytest tests/unit/test_otel_config_validation.py
pytest tests/unit/test_prometheus_config_validation.py
pytest tests/unit/test_grafana_config_validation.py
pytest tests/unit/test_tempo_config_validation.py
pytest tests/unit/test_loki_config_validation.py
```

**What is validated:**
- Valid YAML syntax
- Required sections and fields
- Port numbers in valid range
- URL formats
- Time duration formats
- Component references
- Pipeline configurations
- Common misconfigurations

**Test coverage:** 118 tests covering all configuration aspects

For detailed documentation, see [tests/unit/README.md](tests/unit/README.md)

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
make up
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

1. **Open Grafana**: http://localhost:3000 (credentials from `.env`)
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

> **Note:** Add a repository secret named `GRAFANA_ADMIN_PASSWORD` in **GitHub → Settings → Secrets and variables → Actions** before running this workflow. Use a secure non-default value (not `admin`, `changeme`, or `REPLACE_ME_set_a_real_password_here`).

```yaml
# GitHub Actions example
jobs:
  observability-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run acceptance test
        env:
          GRAFANA_ADMIN_PASSWORD: ${{ secrets.GRAFANA_ADMIN_PASSWORD }}
        run: |
          mkdir -p data/prometheus data/grafana
          chmod -R 777 data/
          make up
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

- **DORA data integration (M4):** wire deployment and commit event sources from uFawkesPipe so DORA metrics can be computed from reliable data.
- **Production hardening:** add stronger authentication/TLS posture, storage backends, and operational safeguards for longer-lived deployments.
- **Kubernetes deployment option (M5):** provide a Helm + ArgoCD track for pull-based reconciliation and multi-node operations.

---

## Development Philosophy

This project follows these principles:
- ✅ **GitOps at the configuration layer:** all desired state is in version control and applied declaratively. In this release, deployment reconciliation is push-triggered (via `make up` or CI). Pull-based reconciliation (continuous sync from git to runtime state) requires the Helm + ArgoCD track (see M5).
- ✅ **Reproducible:** Can be rebuilt from zero with `git clone` + `make up`
- ✅ **No manual steps:** Zero UI clicks or CLI wizardry required
- ✅ **Declarative:** All configuration is explicit and file-based
- ✅ **Boring technology:** Reliable, well-documented, production-ready tools

---

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
