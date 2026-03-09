# Change Impact Map — Obstackd

> Check this before touching any service. Observability stacks have tight coupling:
> a Prometheus config change can silence all alerts; an OTEL route change can drop traces.
> Update this file whenever a new cross-service dependency is discovered.

---

## compose.yaml Changes

| If you change... | You must also check / update... |
|---|---|
| Any image version | `docs/KNOWN_LIMITATIONS.md` for version-specific bugs; acceptance tests; PR description |
| Prometheus port (default 9090) | `config/grafana/provisioning/datasources/`, OTEL collector exporters, `docs/` port reference |
| Tempo port (default 3200 / 4317 / 4318) | OTEL collector `otlp` exporter endpoint, Grafana Tempo datasource URL |
| Loki port (default 3100 / 9096) | OTEL collector `loki` exporter endpoint, Alloy `loki.write` endpoint, Grafana Loki datasource URL |
| Alloy port (default 12345) | Prometheus scrape config, `docs/` port reference, acceptance tests |
| Alertmanager port (default 9093) | Prometheus `alerting.alertmanagers` config, Grafana Alertmanager datasource URL, `docs/` port reference |
| Grafana port (default 3000) | `scripts/` health checks, acceptance tests, `README.md` |
| OTEL Collector ports (4317 gRPC / 4318 HTTP / 8889 metrics) | Any upstream services sending telemetry, Prometheus scrape config |
| Volume mount paths | `config/` file paths that reference them, `docs/RUNBOOKS.md` backup procedures |
| Network name | All services that reference it, `scripts/` that use `docker network inspect` |
| Environment variable names | `.env.example`, `docs/`, CI workflows that set them |
| Adding a new service | Add healthcheck, add to acceptance tests, add Grafana datasource if applicable, update `docs/ARCHITECTURE.md` |
| Removing a service | Check all `depends_on:` references, remove from acceptance tests, update `docs/` |
| Telemetry generator (apps profile) | Update acceptance tests that rely on it, update `README.md` |

---

## config/ Changes

| If you change... | You must also check / update... |
|---|---|
| OTEL collector receiver endpoints | Upstream services sending to those endpoints |
| OTEL collector exporter endpoints | Must match Compose service names and ports |
| OTEL pipeline definitions | All three: receivers, processors, exporters must be consistent |
| Prometheus scrape targets | Verify target service names match Compose service names exactly |
| Prometheus alert rules | `docs/RUNBOOKS.md` — does the runbook cover this alert? |
| Prometheus recording rules | Any Grafana panels using the recording rule metric name |
| Grafana datasource URLs | Must use Compose service name, not `localhost` |
| Grafana dashboard UIDs | Any cross-dashboard links that reference the UID |
| Tempo storage path | Must match volume mount in `compose.yaml` |
| Alloy config (`config/alloy/config.river`) | `loki.write` endpoint URL, Docker socket mount, data volume path |
| Loki config (`config/loki/loki.yaml`) | Retention settings, storage paths (must match `data/loki` volume) |
| Alertmanager config (`config/alertmanager/alertmanager.yml`) | Prometheus `alerting.alertmanagers` URL, test alert routing |

---

## Cross-Plane Impact (Integration with Other Fawkes Planes)

| If you change... | Impact on other planes |
|---|---|
| OTEL Collector receiver port (4317/4318) | **deliveryd**: Jenkins pipeline traces sent here; update deliveryd OTEL SDK config |
| Loki port (3100) | Any external log shippers or apps pushing logs via OTLP/HTTP must be updated |
| Prometheus remote-write endpoint | **fawkes**: Full IDP deployment may scrape this Prometheus |
| Grafana admin credentials format | **developerd**: Developer tooling that embeds Grafana panels |
| Network name in `compose.yaml` | Other planes that join this network for cross-plane telemetry |

---

## Scripts Changes

| If you change... | You must also check... |
|---|---|
| Port numbers in health check scripts | Must match `compose.yaml` exposed ports |
| Container name references | Must match Compose service names (or use `docker compose ps`) |
| `run-acceptance-tests.sh` | All test files it calls in `tests/acceptance/` |
