# Prompt Library — Obstackd Compliance Reviews

> Tested prompt templates for recurring compliance tasks.
> Run these five reviews in order for each audit cycle.
> Fix all findings before merging. Flag documentation gaps as separate issues.

---

## Review 1 — Docker Compose Compliance

**Purpose:** Verify `compose.yaml` meets all Obstackd architecture rules.

**Checklist:**

| Rule | Check |
|------|-------|
| All image tags are pinned (no `latest`) | `grep -n "image: .*:latest" compose.yaml` must return nothing |
| Every service has `healthcheck:` | Each service block contains a `healthcheck:` key |
| Every service has labels `plane`, `component`, `managed-by` | Each service block contains all three labels |
| All services use the `observability` named network | Each service has `networks: [observability]` |
| No inline secrets or passwords | No plaintext credentials — env vars only via `${VAR}` |
| Named networks declared at the top level | `networks:` block exists with explicit `driver: bridge` |

**How to run:**

```bash
# Check for latest tags
grep -n "image: .*:latest" compose.yaml && echo "FAIL: latest tag found" || echo "PASS"

# Check docker compose config is valid
docker compose config -q && echo "PASS: compose valid" || echo "FAIL: invalid compose"

# Run supply-chain workflow locally
grep -R "image: .*:latest" compose.yaml && exit 1 || echo "PASS: no latest tags"
```

---

## Review 2 — OTEL Collector Config Compliance

**Purpose:** Verify `config/otel/collector.yaml` follows Obstackd conventions.

**Checklist:**

| Rule | Check |
|------|-------|
| Receivers are defined (at minimum `otlp`) | `receivers:` block with `otlp:` present |
| `memory_limiter` processor is listed first in every pipeline | `processors: [memory_limiter, ...]` ordering |
| `batch` processor is listed last in every pipeline | `processors: [..., batch]` ordering |
| Exporters reference Compose service names, never `localhost` | No `localhost` in exporter endpoints |
| All pipelines have at least one receiver and one exporter | Each pipeline under `service.pipelines` has both |
| Telemetry metrics address uses `0.0.0.0`, not `localhost` | `address: "0.0.0.0:8888"` |

**How to run:**

```bash
# Check for localhost in exporter endpoints
grep -n "localhost" config/otel/collector.yaml && echo "FAIL: localhost found in OTEL config" || echo "PASS"

# Validate config via Docker
docker run --rm \
  -v "$PWD/config/otel/collector.yaml:/etc/otel/config.yaml" \
  otel/opentelemetry-collector-contrib:0.103.1 \
  validate --config=/etc/otel/config.yaml
```

---

## Review 3 — Prometheus Config Compliance

**Purpose:** Verify `config/prometheus/prometheus.yaml` and `config/prometheus/alerts.yml` follow Obstackd conventions.

**Checklist:**

| Rule | Check |
|------|-------|
| Scrape targets use Compose service names (not `localhost`) | Targets like `otel-collector:8888`, `alertmanager:9093` |
| Self-monitoring uses `localhost:9090` (correct inside container) | `prometheus` job targets `localhost:9090` — this is intentional |
| Alert rules are in a separate file, not inline | `rule_files:` points to `/etc/prometheus/alerts.yml` |
| `global.scrape_interval` is set | Present in `global:` block |
| `alerting.alertmanagers` targets Compose service name | `alertmanager:9093` — not localhost |
| Recording rules have explanatory comments | Each recording rule group has a comment |

**How to run:**

```bash
# Check for unexpected localhost in scrape targets (self-monitoring localhost is expected)
grep -n "localhost" config/prometheus/prometheus.yaml

# Validate Prometheus config
docker run --rm \
  -v "$PWD/config/prometheus:/etc/prometheus" \
  --entrypoint promtool \
  prom/prometheus:v2.52.0 \
  check config /etc/prometheus/prometheus.yaml

# Validate alert rules
docker run --rm \
  -v "$PWD/config/prometheus:/etc/prometheus" \
  --entrypoint promtool \
  prom/prometheus:v2.52.0 \
  check rules /etc/prometheus/alerts.yml
```

---

## Review 4 — Grafana Datasource Compliance

**Purpose:** Verify Grafana provisioning files reference Compose service names and use env-var substitution for any credentials.

**Checklist:**

| Rule | Check |
|------|-------|
| Prometheus datasource URL uses service name | `url: http://prometheus:9090` |
| Tempo datasource URL uses service name | `url: http://tempo:3200` |
| Loki datasource URL uses service name | `url: http://loki:3100` |
| Alertmanager datasource URL uses service name | `url: http://alertmanager:9093` |
| No `localhost` in any datasource URL | `grep localhost config/grafana/provisioning/datasources/*.yaml` returns nothing |
| `grafana.ini` uses env-var substitution for credentials | `admin_user = ${GF_SECURITY_ADMIN_USER}`, `admin_password = ${GRAFANA_ADMIN_PASSWORD}` |
| Dashboard UIDs are stable (explicitly set) | Each dashboard JSON has a `uid` field |

**How to run:**

```bash
# Check for localhost in Grafana datasource config
grep -n "localhost" config/grafana/provisioning/datasources/datasources.yaml \
  && echo "FAIL: localhost found" || echo "PASS"

# Check grafana.ini for hardcoded credentials
grep -n "admin_user\|admin_password" config/grafana/grafana.ini

# Validate datasource YAML
yamllint config/grafana/provisioning/datasources/datasources.yaml
yamllint config/grafana/provisioning/dashboards/dashboards.yaml
```

---

## Review 5 — Shell Script Compliance

**Purpose:** Verify all shell scripts in `scripts/` and `tests/acceptance/` meet Obstackd standards.

**Checklist:**

| Rule | Check |
|------|-------|
| Every `.sh` file starts with `#!/bin/bash` | First line of each file |
| `set -euo pipefail` present near the top | Within first 10 lines |
| No `readonly VAR=$(command)` pattern (SC2155) | Declare and assign separately |
| No unused variables (SC2034) | All declared variables are actually used |
| No hardcoded container names | Names read from env or compose service names |
| Health check scripts exit non-zero on failure | Return codes checked |

**How to run:**

```bash
# Check set -euo pipefail in all scripts
find scripts/ tests/acceptance/ -name "*.sh" | \
  xargs grep -L "set -euo pipefail" | \
  { read -r missing && echo "FAIL: missing set -euo pipefail: $missing" || echo "PASS"; }

# Run shellcheck on all scripts
shellcheck scripts/**/*.sh tests/acceptance/**/*.sh tests/acceptance/*.sh
```

---

## Running All Five Reviews

```bash
#!/bin/bash
# Run all five compliance reviews
set -euo pipefail

echo "=== Review 1: Docker Compose Compliance ==="
grep -R "image: .*:latest" compose.yaml && { echo "FAIL: latest tag"; exit 1; } || echo "PASS"
docker compose config -q && echo "PASS: compose valid" || { echo "FAIL: invalid compose"; exit 1; }

echo "=== Review 2: OTEL Collector Config Compliance ==="
grep -n "localhost" config/otel/collector.yaml \
  | grep -v "^#" \
  && { echo "FAIL: localhost in OTEL exporters"; exit 1; } || echo "PASS"

echo "=== Review 3: Prometheus Config Compliance ==="
docker run --rm \
  -v "$PWD/config/prometheus:/etc/prometheus" \
  --entrypoint promtool \
  prom/prometheus:v2.52.0 \
  check config /etc/prometheus/prometheus.yaml

echo "=== Review 4: Grafana Datasource Compliance ==="
grep -n "localhost" config/grafana/provisioning/datasources/datasources.yaml \
  && { echo "FAIL: localhost in Grafana datasources"; exit 1; } || echo "PASS"
grep -n "admin_user\s*=\s*[^$]" config/grafana/grafana.ini \
  && { echo "FAIL: hardcoded admin_user"; exit 1; } || echo "PASS"

echo "=== Review 5: Shell Script Compliance ==="
shellcheck scripts/**/*.sh tests/acceptance/**/*.sh tests/acceptance/*.sh \
  && echo "PASS: shellcheck" || { echo "FAIL: shellcheck errors"; exit 1; }

echo ""
echo "✅ All five compliance reviews passed."
```
