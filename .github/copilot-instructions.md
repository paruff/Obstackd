# Copilot Instructions — Observability Lab

## 0. Mission

This repository defines a **long-lived, self-hosted, GitOps-first observability platform** based on:

- Docker Compose
- OpenTelemetry
- Prometheus, Tempo, Loki, Grafana

The system must be:

- Rebuildable from zero
- Fully declarative
- Fully defined by files in this repo
- Started only via: `docker compose up`
- With **zero manual UI or CLI setup steps**

Copilot must optimize for:

- Boring, reliable, explicit solutions
- Long-term operability
- Debuggability at 3am
- Reproducibility
- Minimal cleverness

---

## 1. Absolute Rules (Never Break These)

- ❌ Do NOT introduce manual setup steps
- ❌ Do NOT require clicking in UIs to finish configuration
- ❌ Do NOT store state inside containers
- ❌ Do NOT assume Kubernetes
- ❌ Do NOT use ad-hoc scripts if config files can do the job
- ❌ Do NOT change running containers via exec as part of the design

- ✅ Everything must be configured via files in this repo
- ✅ All configuration must be mounted read-only into containers
- ✅ All state must live in `./data/*`
- ✅ All services must be defined in `compose.yaml`
- ✅ All behavior must be reproducible from `git clone` + `docker compose up`

---

## 2. Architectural Invariants

- OpenTelemetry Collector is the **only ingestion point**
- All apps send OTLP to the collector
- The collector routes to:
  - Prometheus (metrics)
  - Tempo (traces)
  - Loki (logs)
- Grafana is **read-only UI**, fully provisioned via config files
- Docker Compose service names are the only service discovery mechanism

---

## 3. Repository Structure (Must Be Preserved)
.
├── compose.yaml
├── config/
│   ├── otel/
│   ├── prometheus/
│   ├── tempo/
│   ├── loki/
│   └── grafana/
│       ├── provisioning/
│       └── dashboards/
├── data/          # runtime state (gitignored)
├── apps/
└── docs/

Copilot must:

- Put configs in the correct subfolder
- Never inline large configs into compose.yaml
- Never move state into config folders
- Never mix concerns

---

## 4. How to Modify the System

When adding a new component:

1. Add its config under `config/<component>/`
2. Add its data directory under `data/<component>/`
3. Mount both in `compose.yaml`
4. Add Grafana provisioning if it affects visualization
5. Ensure `docker compose up` works from a clean repo

---

## 5. Compose File Rules

- Use explicit image tags (no `latest`)
- Use named or bind-mounted volumes under `./data`
- Mount configs read-only
- Use profiles (`core`, `apps`, `debug`)
- Set container names explicitly
- Prefer clarity over brevity

---

## 6. OpenTelemetry Rules

- OTel Collector config lives in: `config/otel/collector.yaml`
- Pipelines must be explicit:
  - metrics
  - traces
  - logs
- Always include:
  - batch processor
  - memory_limiter
- Prefer simple, readable pipelines over clever ones

---

## 7. Grafana Rules

- All datasources must be provisioned
- All dashboards must be file-based
- No manual dashboards
- No manual datasources
- No manual settings

Everything must survive deleting `./data/grafana` and restarting.

---

## 8. Demo / Golden Path Services

- Must live under: `apps/`
- Must be:
  - Self-contained
  - Buildable by compose
  - Instrumented with OpenTelemetry SDK
- Must send telemetry to: `otel-collector`

---

## 9. How to Structure Changes (Critical)

Copilot must:

- Keep changes **small and reviewable**
- Prefer adding new files over rewriting existing ones
- Avoid refactors unless explicitly asked
- Not mix unrelated concerns in one change
- Follow the current phase plan (Phase 0, 1, 2, 3, ...)

---

## 10. Validation Mindset

Every change must answer:

- How do we know this works?
- What UI / query / endpoint proves it?
- What breaks if this component is down?
- Can the whole system be deleted and rebuilt?

---

## 11. Tone and Style

- Prefer explicit over abstract
- Prefer boring over clever
- Prefer readable over compact
- Prefer configuration over code
- Prefer determinism over flexibility

---

## 12. If Anything Is Ambiguous

Copilot should:

- Ask for clarification
- Or follow the **most conservative, boring, explicit interpretation**

Never assume.

---

## 13. Prime Directive

> This repository is a **machine that turns Git into a running observability system**.  
> Anything that weakens reproducibility, debuggability, or clarity is a regression.
