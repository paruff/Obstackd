# Agent Instructions — Obstackd

> Universal instructions for all agents: GitHub Copilot, VS Code agent mode, Claude.
> Obstackd is the **Observability Plane** of the Fawkes IDP family.
> It provides OpenTelemetry, Prometheus, Tempo, and Grafana via Docker Compose.
> **Do not modify this file without maintainer approval.**

---

## 1. What Obstackd Is

Obstackd is a self-hosted, GitOps-first observability platform delivered as Docker Compose.
It is a sub-plane of [Fawkes IDP](https://github.com/paruff/fawkes) and can be deployed
standalone or integrated with `deliveryd` (CI/CD plane) and `developerd` (developer plane).

**Stack:**
| Service | Version | Role |
|---|---|---|
| OpenTelemetry Collector | v0.99.0 | Telemetry ingestion and routing |
| Prometheus | v2.50.1 | Metrics storage and querying |
| Tempo | v2.3.1 | Distributed tracing backend |
| Grafana | v10.4.2 | Visualisation and dashboards |
| Docker Compose | latest stable | Service orchestration |

**Repository:** github.com/paruff/Obstackd

---

## 2. Directory & File Map

| Path | Language | What Lives Here | Do Not |
|---|---|---|---|
| `compose.yaml` | YAML | Service definitions, networks, volumes | Hardcode ports that conflict with other planes |
| `config/` | YAML | Per-service configuration files (otel-collector, prometheus, tempo, grafana) | Put secrets or credentials here |
| `data/` | Various | Persistent volume mounts, seed dashboards, provisioning | Commit real telemetry data |
| `scripts/` | Bash | Start/stop helpers, health checks, smoke tests | Put business logic here |
| `tests/acceptance/` | YAML / Bash | Acceptance tests that verify the stack is healthy | Delete failing tests |
| `docs/` | Markdown | Runbooks, architecture decisions, configuration reference | |

---

## 3. Context Files — Read Before Generating Anything

| Priority | File | What You Learn |
|---|---|---|
| 1 | `AGENTS.md` (this file) | Stack, boundaries, PM contract |
| 2 | `compose.yaml` | Current service versions, ports, volumes, networks |
| 3 | `docs/ARCHITECTURE.md` | How services connect and depend on each other |
| 4 | `docs/KNOWN_LIMITATIONS.md` | Known issues — do not make these worse |
| 5 | `docs/CHANGE_IMPACT_MAP.md` | What breaks when a service config changes |

---

## 4. Architecture Rules — Never Violate These

### compose.yaml
- All service image versions must be **pinned** — no `latest` tags ever
- Secrets and passwords go in `.env` (gitignored) — never in `compose.yaml`
- All services must have `healthcheck:` defined
- Networks must be explicitly declared — no implicit default network
- Volumes for persistent data must be named, not anonymous

### config/ files
- Config files are **declarative** — no scripts or logic inside them
- OpenTelemetry collector config: exporters must match actual running services
- Prometheus scrape targets must match actual service names in `compose.yaml`
- Grafana datasources must reference services by Docker Compose service name, not `localhost`
- No credentials in config files — use environment variable substitution (`${VAR_NAME}`)

### scripts/
- `set -euo pipefail` at the top of every `.sh` file
- `shellcheck` must pass on all scripts
- No hardcoded container names — read from `compose.yaml` or environment variables
- Health check scripts must exit non-zero on failure

### tests/acceptance/
- Tests verify the stack is observable: metrics flowing, traces queryable, dashboards loading
- Tests must be runnable with `docker compose up` already running
- Every test has a clear pass/fail exit code

---

## 5. The PM–Agent Contract

### Agents MAY Do Without Asking
- Read any file
- Edit `config/` files, `scripts/`, `docs/`, `tests/acceptance/`
- Run: `docker compose config` (validate), `yamllint`, `shellcheck`
- Open draft PRs

### Agents MUST Ask Before
- Changing image versions in `compose.yaml`
- Adding or removing services from `compose.yaml`
- Changing exposed port numbers
- Modifying volume mount paths
- Adding new environment variables

### Agents Must NEVER
- Commit `.env` files, passwords, API keys, or tokens
- Use `latest` image tags
- Remove `healthcheck:` from any service
- Delete acceptance tests
- Push to `main` directly or merge their own PRs
- Apply `large-pr-approved` label (humans only)

---

## 6. Coding Standards

### YAML (all files)
- `yamllint` must pass (config in `.yamllint.yml`)
- 2-space indentation, no tabs
- Quoted strings for values that could be misread as other types

### Bash (scripts/)
- `set -euo pipefail` at top
- `shellcheck` must pass
- Functions over repeated blocks
- Descriptive variable names in UPPER_SNAKE_CASE

### Commits
- `feat(compose):`, `fix(config):`, `test(acceptance):`, `docs:`, `chore:`
- Reference issue number: `fix(prometheus): correct scrape interval (#8)`

---

## 7. PR Requirements

Every PR must include the AI-Assisted Review Block:
- What changed (one sentence per service affected)
- Services affected and how tested (`docker compose up` + acceptance tests)
- Any port or volume changes flagged
- Secrets check: confirmed nothing sensitive committed

---

## 8. Instability Safeguards

- PR size > 400 lines → CI blocks. `large-pr-approved` label to override (humans only).
- Image version bumps require the old and new version in the PR description
- Any change to Prometheus scrape config requires a note on which metrics will be affected
- Rework rate > 10%: stop adding features, fix instructions

---

## 9. Integration with Other Planes

Obstackd is designed to be consumed by:
- **deliveryd** — Jenkins metrics and pipeline traces flow into Obstackd
- **developerd** — Developer environment telemetry flows into Obstackd
- **fawkes** — Full IDP deployment uses Obstackd as its observability layer

When making changes, check `docs/CHANGE_IMPACT_MAP.md` for cross-plane impact.

---

## 10. See Also

- `.github/copilot-instructions.md` — Copilot-specific subset
- `.github/instructions/` — path-scoped instruction files
- `docs/PROMPT_LIBRARY.md` — tested prompt templates
- `docs/CHANGE_IMPACT_MAP.md` — cross-service and cross-plane impact
