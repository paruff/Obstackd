# Known Limitations — Obstackd

> Read this before making any changes to ensure you don't make existing issues worse.
> Update this file whenever a new limitation or version-specific bug is discovered.
> Reference: `AGENTS.md` section 3, priority 4 context file.

---

## 1. Missing `healthcheck:` on `otel-collector`

**Severity:** Medium  
**Service:** `otel-collector`  
**Rule violated:** "All services must have `healthcheck:` defined" (AGENTS.md §4)

The `otel-collector` service in `compose.yaml` has no `healthcheck:` block, which means:
- Docker cannot report a meaningful health status for it
- Downstream services cannot express `depends_on: otel-collector: condition: service_healthy`
- CI and acceptance tests cannot reliably wait for the collector to be ready

**Workaround:** Use a `start_period` sleep in scripts or `depends_on` without health condition.

**Fix required:** Two steps are needed (both require human approval per PM–Agent contract):
1. Add the `health_check` extension to `config/otel/collector.yaml` (default port 13133, path `/`).
2. Add a `healthcheck:` to the `otel-collector` service in `compose.yaml` targeting
   `http://localhost:13133/`.

Until the extension is configured, an alternative is to probe the collector's internal
metrics endpoint: `http://localhost:8888/metrics`.

---

## 2. Missing `healthcheck:` on `alloy`

**Severity:** Medium  
**Service:** `alloy`  
**Rule violated:** "All services must have `healthcheck:` defined" (AGENTS.md §4)

The `alloy` service in `compose.yaml` has no `healthcheck:` block. Alloy exposes a
`/-/ready` endpoint on port `12345`.

**Workaround:** Acceptance tests use a fixed sleep before checking Alloy metrics.

**Fix required:** Add a `healthcheck:` targeting `http://localhost:12345/-/ready`. Requires
human approval per PM–Agent contract because it modifies `compose.yaml`.

---

## 3. Missing `restart: unless-stopped` on `otel-collector`

**Severity:** Low  
**Service:** `otel-collector`

All other core services have `restart: unless-stopped`, but `otel-collector` does not.
If the collector process crashes, it will not be automatically restarted.

**Fix required:** Add `restart: unless-stopped` to the `otel-collector` service definition.
Requires human approval per PM–Agent contract.

---

## 4. `otel-collector` missing resource limits (`deploy.resources`)

**Severity:** Low  
**Service:** `otel-collector`

All other core services define `deploy.resources` with CPU and memory limits and
reservations. The `otel-collector` service has no resource constraints, which can allow
it to consume unbounded host resources under high telemetry load.

**Fix required:** Add a `deploy.resources` block to `otel-collector`. Requires human
approval per PM–Agent contract.

---

## 5. Traces are empty until an application is instrumented

**Severity:** Informational  
**Service:** `tempo`

Tempo is running and healthy, but the traces view in Grafana will be empty until at
least one application sends spans to the OTEL Collector (ports 4317 gRPC / 4318 HTTP).

**Workaround:** Use the `telemetry-generator` application (defined in `compose.yaml` under
the `apps` profile) to produce synthetic traces for testing:

```bash
docker compose --profile core --profile apps up -d
```

This starts the `telemetry-generator` container which emits OTLP spans to the collector.

---

## 6. Alloy log discovery delay after startup

**Severity:** Low  
**Service:** `alloy`

After the stack starts, Alloy may take 30–60 seconds to discover running containers via
the Docker socket. Log queries against Loki will return no results during this window.

**Workaround:** Wait at least 60 seconds after `docker compose up` before querying logs.
Acceptance tests should account for this delay.

---

## 7. Alloy may duplicate logs on first start

**Severity:** Low  
**Service:** `alloy`

On the very first startup (before `data/alloy/positions.yaml` is created), Alloy has no
record of previously shipped log positions. If containers were already running before
Alloy started, some log lines may be shipped twice.

**Workaround:** Expected on first run; automatic on subsequent restarts once
`positions.yaml` exists.

---

## Recently Resolved

### AGENTS.md stack version table was out of date

**File:** `AGENTS.md`  
**Status:** ✅ Resolved

The stack version table in `AGENTS.md` section 1 listed versions that did not match
the pinned image tags in `compose.yaml`. Also missing: Loki, Alloy, and Alertmanager.
The table has been corrected and now reflects the actual images in `compose.yaml`.

---

## Version Reference (as of last audit)

| Service | Image in `compose.yaml` | Notes |
|---|---|---|
| OpenTelemetry Collector | `otel/opentelemetry-collector-contrib:0.103.1` | |
| Prometheus | `prom/prometheus:v2.52.0` | |
| Tempo | `grafana/tempo:2.5.0` | |
| Loki | `grafana/loki:2.9.10` | |
| Grafana | `grafana/grafana:10.4.5` | |
| Alloy | `grafana/alloy:v1.12.2` | Replaced Promtail |
| Alertmanager | `prom/alertmanager:v0.27.0` | |

> Always cross-check against `compose.yaml` — this table may lag behind image bumps.
