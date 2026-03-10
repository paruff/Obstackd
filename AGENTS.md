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
| OpenTelemetry Collector | v0.103.1 | Telemetry ingestion and routing |
| Prometheus | v2.52.0 | Metrics storage and querying |
| Alertmanager | v0.27.0 | Alert routing and deduplication |
| Tempo | v2.5.0 | Distributed tracing backend |
| Loki | v2.9.10 | Log aggregation and storage |
| Alloy | v1.12.2 | Log collection (replaced Promtail) |
| Grafana | v10.4.5 | Visualisation and dashboards |
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
## 10.  Model Selection Policy

Obstackd is a Docker Compose observability stack: Prometheus, Grafana, Loki, Tempo,
and OpenTelemetry Collector (Alloy). All configuration is YAML, River (Alloy DSL),
and JSON (Grafana dashboards).

> **Budget context:** Shared Copilot Pro budget (300 premium requests/month across all
> repos). GPT-4.1 multiplier is 0 — completely free — and is the default for all tasks.
> The coding agent uses exactly 1 premium request per session × the model multiplier.

### Model Ladder

| Level | Model | Multiplier | Rule |
|---|---|---|---|
| L0 — Free default | GPT-4.1 | 0 | Use for ALL tasks unless explicitly listed otherwise below |
| L0 — Free lightweight | GPT-5 mini | 0 | Single-file YAML edits: version bumps, label changes, one-line additions |
| L1 — Trial (Grafana only) | Gemini 3 Flash | 0.33 | Trial ONLY for Grafana dashboard JSON — see note below before using |
| L2 — Justified premium | GPT-5.1-Codex | 1 | PromQL rules and Grafana JSON if Gemini 3 Flash trial fails; requires label `model:gpt-5.1-codex` |
| PROHIBITED | Claude Opus 4.6 fast | 30 | Never — 30× multiplier. Blocked without explicit written budget approval |
| AVOID | Claude Opus / Sonnet | 1–3 | No Obstackd task type justifies these models |

### Task → Model Routing Table

| Task type | Model | Cost | Notes |
|---|---|---|---|
| Single YAML edit (version bump, label, port) | GPT-5 mini | 0 | |
| Docker Compose multi-service edit | GPT-4.1 | 0 | |
| Alloy River syntax (cAdvisor, node-exporter) | GPT-4.1 | 0 | Specify River config syntax explicitly — not Prometheus config syntax |
| Prometheus scrape config addition | GPT-5 mini | 0 | Simple YAML block addition; provide existing scrape config as reference |
| DevLake Docker Compose integration | GPT-4.1 | 0 | Large block but known pattern; provide DevLake docs link in issue |
| OTEL Collector standard pipeline edit | GPT-4.1 | 0 | Standard receiver/processor/exporter changes only — see AI pipeline note below |
| OTEL Collector AI/LLM pipeline (gen_ai.*) | GPT-5.1-Codex | 1 | Adding new AI exporters risks breaking existing pipelines; free models miss guard clauses |
| Version upgrade (Prometheus / Loki / Tempo) | GPT-5 mini | 0 | Single version string in compose.yaml; must include breaking change notes in issue body |
| Version upgrade (Grafana) | GPT-4.1 | 0 | Grafana upgrades sometimes require dashboard JSON migration; GPT-4.1 handles this |
| PromQL recording rules | GPT-5.1-Codex | 1 | Free models produce vector() arithmetic errors and missing or vector(0) guards |
| PromQL alerting rules (DORA) | GPT-5.1-Codex | 1 | Same — vector arithmetic and threshold logic requires Codex |
| Grafana dashboard JSON — DORA panels | Gemini 3 Flash | 0.33 | Trial: measure PR revision count over first 3 uses before committing — see note |
| Grafana dashboard JSON — AI/LLM panels | GPT-5.1-Codex | 1 | AI dashboard JSON is more complex than DORA; start with Codex not Gemini |
| Cross-plane documentation (Markdown) | GPT-5 mini | 0 | |
| Observability runbooks | GPT-5 mini | 0 | Must include exact LogQL queries, kubectl commands, and Grafana dashboard links in issue body |
| Interactive IDE chat (VS Code) | Claude Haiku 4.5 | 0.33 | Chat only — do not assign agent tasks to Haiku |
| Manual PR comment invocation | GPT-4.1 | 0 | Use `@copilot` with no `+model` suffix — omitting the selector defaults to GPT-4.1 free |

### Gemini 3 Flash trial note (Grafana dashboard JSON)

Gemini 3 Flash scores 63.8% on SWE-bench vs GPT-5.1-Codex at a higher level, but costs
0.33x vs 1x. For Grafana dashboard JSON specifically, the structured output quality may
be sufficient at lower cost. Before committing to Gemini 3 Flash for all dashboard work:

1. Assign the first 3 Grafana JSON issues to Gemini 3 Flash
2. Record PR revision count for each (target: ≤1 revision per PR)
3. If revision count is ≤1 across all 3: adopt Gemini 3 Flash for DORA dashboards
4. If revision count exceeds 1 on any PR: switch to GPT-5.1-Codex and update this table

Until the trial is complete, GPT-5.1-Codex remains the safe default for all Grafana JSON.

### Required issue body format

Every issue assigned to the Copilot coding agent must include this block:

```
**Suggested model:** [GPT-4.1 / GPT-5 mini / Gemini 3 Flash / GPT-5.1-Codex]
**Task type:** [YAML edit / Docker Compose / PromQL / Grafana JSON / OTEL / docs]
**Files to edit:** [explicit list — agent must not create new files unless listed here]
**Reference file:** [path to existing config to use as pattern]
**Do not touch:** [files or services outside the scope of this issue]
**Breaking changes to check:** [version-specific migration notes if applicable]
**Acceptance criteria:**
- [ ] [measurable criterion 1]
- [ ] [measurable criterion 2]
```

### Escalation rule

If rework rate for a task type exceeds 20% after 5 completed PRs with the recommended model:

1. First improve the issue body — add file targets, reference configs, breaking change notes
2. If rework rate is still above 20% after improving the issue body, escalate to the next model tier
3. Document the decision in this section with the date and evidence

### Budget guardrails

- Never use `@copilot +modelname` in PR comments unless GPT-4.1 has already failed on the same task
- The expected premium spend for Obstackd is ~8 requests/month at 20 issues/week:
  - PromQL rules: ~4 sessions at 1x = 4 requests
  - Grafana AI dashboard JSON: ~2 sessions at 1x = 2 requests
  - Grafana DORA JSON (Gemini trial): ~3 sessions at 0.33x = ~1 request
  - IDE chat: ~220 messages/month at 0.33x = ~73 requests (shared with other repos)
- If Gemini 3 Flash trial succeeds, Obstackd premium agent spend drops to ~3 requests/month

---
## 11. See Also

- `.github/copilot-instructions.md` — Copilot-specific subset
- `.github/instructions/` — path-scoped instruction files
- `docs/PROMPT_LIBRARY.md` — tested prompt templates
- `docs/CHANGE_IMPACT_MAP.md` — cross-service and cross-plane impact
