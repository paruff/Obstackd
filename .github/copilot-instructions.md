# Copilot Instructions — Obstackd (Observability Plane)

> Loaded automatically every Copilot session.
> Full rules in `AGENTS.md` — read it for any non-trivial task.

## Stack at a Glance

OpenTelemetry Collector · Prometheus · Tempo · Grafana — all via Docker Compose.

## Context Files — Read These First

1. `AGENTS.md` — stack map, boundaries, PM contract
2. `compose.yaml` — current service versions and ports
3. `docs/ARCHITECTURE.md` — how services connect
4. `docs/KNOWN_LIMITATIONS.md` — do not make these worse
5. `docs/CHANGE_IMPACT_MAP.md` — what breaks when configs change

## Hard Rules

- **No `latest` image tags** — always pinned versions
- **No secrets in any committed file** — `.env` only (gitignored)
- **Every service needs `healthcheck:`** — never remove one
- **`yamllint` must pass** — config in `.yamllint.yml`
- **`shellcheck` must pass** — on all `scripts/*.sh`
- **`set -euo pipefail`** — top of every bash script
- Grafana datasources reference services by Compose service name, not `localhost`

## What Requires Human Approval

- Image version changes in `compose.yaml`
- Adding or removing services
- Port number changes
- Volume mount path changes

## PR Requirement

Every PR needs the AI-Assisted Review Block: services affected, how tested, port/volume changes flagged, secrets check passed.

## PR Size

400 lines → CI blocks. `large-pr-approved` label to override (humans only).

## Commits

`feat(compose):`, `fix(config):`, `test(acceptance):`, `docs:`, `chore:`

## Prompts

Use `docs/PROMPT_LIBRARY.md` for: Docker Compose changes, OTEL config, Prometheus rules, Grafana dashboards, acceptance tests.
