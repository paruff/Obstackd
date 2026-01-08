# Obstackd

## What This Is

A **Docker Compose-based observability platform** that provides a complete monitoring stack with OpenTelemetry, Prometheus, and Grafana. This is a self-hosted, GitOps-first solution designed for long-term operability and reproducibility.

**Tech Stack:**
- **OpenTelemetry Collector** (v0.99.0) - Telemetry data collection and routing
- **Prometheus** (v2.50.1) - Metrics storage and querying
- **Grafana** (v10.4.2) - Visualization and dashboards
- **Docker Compose** - Service orchestration

**Primary Use Case:** Provides a production-ready observability platform that can be deployed from a single `docker compose up` command, with zero manual configuration steps required.

---

## Quick Start

### Prerequisites

- **Docker** 20.10+ installed
- **Docker Compose** v2.0+ installed
- At least 2GB of free RAM
- Ports 3000, 4317, 4318, 8888, and 9090 available

### Installation

1. **Clone and enter:**
   ```bash
   git clone https://github.com/<your-username>/Obstackd.git
   cd Obstackd
   ```

2. **Create data directories:**
   ```bash
   mkdir -p data/prometheus data/grafana
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
| **OpenTelemetry**    | 4317  | OTLP gRPC receiver           | localhost:4317                  |
| **OpenTelemetry**    | 4318  | OTLP HTTP receiver           | localhost:4318                  |
| **OpenTelemetry**    | 8888  | Collector metrics endpoint   | http://localhost:8888/metrics   |
| **Prometheus**       | 9090  | Metrics storage & query UI   | http://localhost:9090           |

---

## Access & Credentials

### Grafana Dashboard
- **URL:** http://localhost:3000
- **Username:** `admin`
- **Password:** `admin`

The Prometheus datasource is pre-configured and ready to use.

---

## Health Checks

Verify that all services are operational:

```bash
# Check Prometheus
curl -f http://localhost:9090/-/ready

# Check Grafana
curl -f http://localhost:3000/api/health

# Check OpenTelemetry Collector metrics
curl -f http://localhost:8888/metrics
```

---

## Profiles

The system uses Docker Compose profiles to control which services run:

| Profile | Services                                    | Purpose                  |
|---------|---------------------------------------------|--------------------------|
| `core`  | otel-collector, prometheus, grafana         | Base observability stack |

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
├── prometheus/
│   └── prometheus.yaml         # Prometheus scrape config
└── grafana/
    └── provisioning/
        └── datasources/
            └── datasources.yaml # Pre-configured Prometheus datasource
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
│ Collector           │──────┐
└──────────┬──────────┘      │
           │                 │
           │ metrics         │ logs/traces
           ▼                 │ (future)
   ┌──────────────┐          │
   │  Prometheus  │          │
   │   :9090      │          │
   └──────┬───────┘          │
          │                  │
          │ datasource       │
          ▼                  ▼
     ┌──────────────────────┐
     │      Grafana         │
     │       :3000          │
     └──────────────────────┘
```

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
rm -rf data/prometheus/* data/grafana/*

# Recreate
mkdir -p data/prometheus data/grafana
chmod -R 777 data/

# Start fresh
docker compose --profile core up -d
```

---

## Next Steps

- **Add instrumented applications** to send telemetry to the OTLP endpoints
- **Create custom Grafana dashboards** in `config/grafana/dashboards/`
- **Configure additional Prometheus scrape targets** in `config/prometheus/prometheus.yaml`
- **Extend the OpenTelemetry pipeline** for traces and logs in `config/otel/collector.yaml`

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
