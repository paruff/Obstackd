# Known Limitations — Obstackd

> Check this before reporting a bug. These are known issues that are not bugs in Obstackd itself.
> Update this file when a new limitation is confirmed or a workaround is found.

---

## Security & Authentication

### No TLS Between Internal Services

**Limitation:** All communication between services (OTEL Collector → Tempo, Alloy → Loki, etc.)
uses plaintext HTTP/gRPC with `insecure: true`. This is intentional for a local development setup.

**Impact:** Not suitable for production without adding mutual TLS.

**Workaround:** For production, add TLS certificates and update all exporter/endpoint configs
in `config/otel/collector.yaml`, `config/alloy/config.river`, and Grafana datasource URLs.

---

### No Authentication on Loki, Tempo, Prometheus

**Limitation:** All backend services accept unauthenticated requests on their exposed ports.

**Impact:** Anyone with network access can read or write telemetry data.

**Workaround:** Restrict access at the network/firewall level. Enable `auth_enabled: true` in
`config/loki/loki.yaml` for multi-tenant setups.

---

## Data Storage

### Local Filesystem Storage Only

**Limitation:** All persistent data (metrics, traces, logs) is stored on the local filesystem
under `./data/`. There is no object storage backend configured.

**Impact:**
- Data is lost if the host disk fails
- No horizontal scaling
- Tempo local storage is limited by disk capacity

**Workaround:** For production, configure object storage (S3, GCS) in each service's config.

---

### Tempo Storage Quota

**Limitation:** Tempo is configured with local storage. There is no automatic size limit on
trace storage beyond the host disk capacity.

**Impact:** Long-running deployments may fill the disk.

**Workaround:** Monitor `./data/tempo` disk usage. Set `max_block_bytes` in
`config/tempo/tempo.yaml` to limit storage.

---

## Operational

### `chmod 777 data/` Required for Startup

**Limitation:** The `data/` directories must be world-writable for Docker containers to write
persistent data. This is because container processes run as non-root UIDs that differ from
the host user.

**Impact:** Overly permissive permissions on the host filesystem.

**Workaround:** The smoke tests apply `chmod 777 data/` automatically. For production, configure
proper UID/GID mappings using Docker `user:` and `group_add:` settings.

---

### Single-Node Deployment Only

**Limitation:** `compose.yaml` deploys all services on a single Docker host. There is no
built-in support for distributing services across multiple nodes.

**Impact:** No high-availability for any individual service.

**Workaround:** For HA, migrate to Kubernetes or use managed cloud observability services.

---

## Alloy (Log Collection)

### Docker Socket Access Required

**Limitation:** Alloy requires read access to `/var/run/docker.sock` to discover and collect
container logs. On some Docker Desktop configurations, the socket path may differ.

**Impact:** Alloy may fail to start or collect no logs if the socket is not accessible.

**Workaround:** Verify that `/var/run/docker.sock` exists on the host. On macOS with Docker
Desktop, the socket may be at `/var/run/docker.sock` via a symlink. Check
`docker compose logs alloy` for permission errors.

---

### Alloy Positions File

**Limitation:** Alloy tracks log read positions in `/var/lib/alloy/positions.yaml` (persisted
in `./data/alloy`). If the positions file is deleted or corrupted, Alloy will re-read all
container logs from the beginning.

**Impact:** Duplicate log entries in Loki after an Alloy data directory reset.

**Workaround:** This resolves itself after the log retention period. To prevent: do not
delete `./data/alloy` while containers are running.

---

## Grafana

### Default Credentials

**Limitation:** The default Grafana admin credentials are `admin`/`admin` (configurable via
`.env`). If `.env` is not present, these weak defaults apply.

**Impact:** Anyone with access to port 3000 can log in as admin.

**Workaround:** Always set `GRAFANA_ADMIN_PASSWORD` in `.env` before first run. The `.env`
file is gitignored and will not be committed.

---

### Dashboard UIDs Must Be Stable

**Limitation:** Cross-dashboard links use UIDs. If a dashboard is re-imported with a
different UID, those links will break.

**Impact:** Broken "Open in" links between dashboards.

**Workaround:** Always export dashboards from Grafana UI and keep the `uid` field set to a
stable value in the JSON. Never let Grafana auto-generate UIDs.

---

## Prometheus

### 30-Day Retention Only

**Limitation:** Prometheus is configured with `--storage.tsdb.retention.time=30d`. Metrics
older than 30 days are automatically deleted.

**Impact:** No long-term metrics history beyond 30 days.

**Workaround:** Enable remote-write to a long-term storage backend (Thanos, Cortex, Mimir),
or increase `--storage.tsdb.retention.time` (requires more disk).

---

## Alertmanager

### Webhook Receiver Only (No Email/Slack by Default)

**Limitation:** The default `config/alertmanager/alertmanager.yml` uses a webhook receiver
for testing. No email, Slack, or PagerDuty integration is configured out of the box.

**Impact:** Alerts are not sent to any notification channel by default.

**Workaround:** Edit `config/alertmanager/alertmanager.yml` to add your notification
receivers. See [Alertmanager docs](https://prometheus.io/docs/alerting/latest/configuration/).

---

## Telemetry Generator (`apps` profile)

### Demo Application Only

**Limitation:** The `telemetry-generator` service (`apps` profile) is a demo application
for testing the telemetry pipeline. It is not intended for production use.

**Impact:** Do not rely on it for production telemetry.

**Workaround:** Replace with your own instrumented application. See
`apps/telemetry-generator/README.md` for the telemetry patterns it uses.
