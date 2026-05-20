# Production Hardening

## Environment validation before startup

Use the environment guard before bringing the stack up:

```bash
make check-env
```

`make up` runs this check automatically and blocks startup if
`GRAFANA_ADMIN_PASSWORD` is unset, empty, or a default value.

If the check fails, remediate with:

```bash
cp .env.example .env
$EDITOR .env
```

---

## Correct Directory Permissions

### Why `chmod 777` is dangerous

`chmod -R 777 data/` makes Prometheus TSDB, Grafana SQLite, Loki chunks, Tempo
trace data, and (if you store them there) datasource credentials readable and
writable by **every process on the host**. On a monitoring platform that exposes
service topology this is a disqualifying configuration for any non-localhost
deployment.

### Container UIDs

Each Grafana LGTM component runs as a specific unprivileged UID inside its
container:

| Service | Container UID | Directory |
|---|---|---|
| Grafana | 472 | `data/grafana` |
| Prometheus | 65534 (nobody) | `data/prometheus` |
| Alertmanager | 65534 (nobody) | `data/alertmanager` |
| Loki | 10001 | `data/loki` |
| Tempo | 10001 | `data/tempo` |
| Alloy | host user / root | `data/alloy` |

### Recommended: `make init`

`make init` creates each directory with `755` permissions using `install -d`
and prints the `chown` commands needed to assign the correct container UID as
owner:

```bash
make init
```

On Linux hosts, the container UID is usually different from your login UID, so
you need to `chown` after `make init`:

```bash
sudo chown -R 472 data/grafana
sudo chown -R 65534 data/prometheus data/alertmanager
sudo chown -R 10001 data/loki data/tempo
```

> **Note:** These `chown` commands are safe for freshly created directories. If
> you apply them to directories that already contain data (e.g., after a reset),
> verify that no other process owns files within those directories before running
> them.

On Docker Desktop (macOS/Windows) the Docker daemon handles UID mapping
automatically; `make init` alone is sufficient.

### Why `install -d` instead of `mkdir`

`install -d -m 755 <dir>` creates the directory and sets mode atomically. It
also succeeds silently when the directory already exists, making `make init`
idempotent.

### Last resort

If you cannot determine the correct UID (e.g., a third-party image without
documentation), you may temporarily set `chmod 777` on a **single-user
localhost machine only**:

```bash
chmod -R 777 data/    # ⚠️ localhost-only last resort
```

Never use `chmod 777` in any shared, networked, or production environment.

---

## Non-Localhost TLS

This stack ships with no TLS — all inter-service traffic uses plain HTTP inside
the Docker network. Before exposing any service beyond localhost:

1. **Put a reverse proxy in front of Grafana.** nginx, Caddy, and Traefik all
   provide automatic Let's Encrypt certificates. Example Caddy config:

   ```
   grafana.example.com {
     reverse_proxy localhost:3000
   }
   ```

   > **Note:** This example assumes Caddy runs on the host (not inside Docker
   > Compose). If Caddy is deployed as a Compose service in the same network,
   > use `grafana:3000` (the Compose service name) instead of `localhost:3000`.

2. **Do not expose Prometheus, Loki, Tempo, or Alertmanager ports externally.**
   Remove or restrict the `ports:` mappings in `compose.yaml` for those services
   and access them through Grafana only.

3. **Use `GF_SERVER_DOMAIN` and `GF_SERVER_ROOT_URL`** in `.env` so that Grafana
   generates correct redirect URLs behind the proxy.

4. **Restrict Alloy's Docker socket mount.** Alloy mounts
   `/var/run/docker.sock:ro` to discover container logs. On public hosts, ensure
   the Docker socket is not world-readable (`chmod 660 /var/run/docker.sock`).

---

## Inter-Service Authentication

### OTel Collector → downstream services

By default the OTel Collector sends telemetry to Prometheus, Tempo, and Loki
over plain HTTP with no authentication. To add mTLS between the collector and
Tempo or Loki:

1. Generate a CA and per-service certificates (e.g., using `step-ca` or
   `cfssl`).
2. Mount certificates into the relevant containers via `volumes:` in
   `compose.yaml`.
3. Add `tls:` blocks to the collector's exporter config and to the service's
   receiver config. Example for Tempo:

   ```yaml
   # config/otel/collector.yaml — exporter
   exporters:
     otlp/tempo:
       endpoint: "tempo:4317"
       tls:
         ca_file: /etc/certs/ca.crt
         cert_file: /etc/certs/collector.crt
         key_file: /etc/certs/collector.key

   # config/tempo/tempo.yaml — receiver
   distributor:
     receivers:
       otlp:
         protocols:
           grpc:
             tls:
               ca_file: /etc/certs/ca.crt
               cert_file: /etc/certs/tempo.crt
               key_file: /etc/certs/tempo.key
   ```

### Prometheus → scrape targets

Add `tls_config:` and `basic_auth:` to individual scrape jobs in
`config/prometheus/prometheus.yaml` when scraping authenticated endpoints.

### Grafana → datasources

Store datasource credentials in `.env` and reference them via environment
variable substitution in `config/grafana/provisioning/datasources/datasources.yaml`.
Never hardcode credentials in provisioning files.

---

## Network Isolation

### Docker network

All services share the `observability` bridge network defined in `compose.yaml`.
They communicate by Compose service name (e.g., `prometheus:9090`). No service
is on the host network by default.

To further restrict inter-service communication, use Docker network policies or
split services into multiple networks with explicit `networks:` declarations per
service.

### Host-level firewall

On a Linux host, use `ufw` or `iptables` to restrict which ports are reachable
from outside the host. Only port 3000 (Grafana) should be publicly reachable
when behind a reverse proxy; all other ports should be localhost-only:

```bash
# Allow Grafana only from the reverse proxy (adjust interface as needed)
ufw allow from 127.0.0.1 to any port 3000
ufw deny 9090    # Prometheus — internal only
ufw deny 3100    # Loki — internal only
ufw deny 3200    # Tempo — internal only
ufw deny 9093    # Alertmanager — internal only
```

---

## Secret Manager Integration

### Docker Secrets — plain Compose (file-based, no Swarm required)

For standard `docker compose` deployments (no Swarm), use a local file as the
secret source. This avoids storing passwords in `.env` and works on any Docker
host:

```yaml
# compose.yaml — file-based secret, no Swarm required
secrets:
  grafana_admin_password:
    file: ./secrets/grafana_admin_password.txt   # gitignored plain-text file

services:
  grafana:
    secrets:
      - grafana_admin_password
    environment:
      - GF_SECURITY_ADMIN_PASSWORD_FILE=/run/secrets/grafana_admin_password
```

Create the secret file (add `secrets/` to `.gitignore`):

```bash
mkdir -p secrets && chmod 700 secrets
echo "my-secure-password" > secrets/grafana_admin_password.txt
chmod 600 secrets/grafana_admin_password.txt
```

### Docker Secrets (Swarm mode — requires `docker swarm init`)

> **Note:** `external: true` secrets are a Swarm feature. They are **not**
> available to plain `docker compose` projects; use the file-based approach
> above unless you have already initialised a Swarm (`docker swarm init`).

If you are running in Swarm mode (`docker stack deploy`), migrate `.env` values
to Swarm-managed secrets:

```yaml
# compose.yaml — Swarm external secret
secrets:
  grafana_admin_password:
    external: true

services:
  grafana:
    secrets:
      - grafana_admin_password
    environment:
      - GF_SECURITY_ADMIN_PASSWORD_FILE=/run/secrets/grafana_admin_password
```

Initialise Swarm and create the secret:

```bash
# Only needed once per host
docker swarm init

# Read from a file — avoids the password appearing in shell history
echo "my-secure-password" > /tmp/grafana-pw && chmod 600 /tmp/grafana-pw
docker secret create grafana_admin_password /tmp/grafana-pw
rm /tmp/grafana-pw
```

Deploy with `docker stack deploy -c compose.yaml uFawkesObs` instead of
`docker compose up`.

### HashiCorp Vault

Use the Vault Agent sidecar or the `vault` CLI in an init container to populate
`.env` at startup. Alternatively, use the Vault Secrets Operator if you migrate
to Kubernetes.

### Cloud secret managers

AWS Secrets Manager, GCP Secret Manager, and Azure Key Vault all provide CLI
tools and SDKs that can write secrets to a local `.env` file during a CI/CD
pipeline step, keeping secrets out of the repository entirely.

---

## When NOT to Use This Tool

uFawkesObs is designed for small-to-medium engineering teams (3–15 people)
running Docker Compose workloads on a single host. It is **not** appropriate
for:

- **Teams with more than 50 engineers.** At that scale, single-instance
  Prometheus and Loki become bottlenecks. Consider Thanos or Cortex for
  Prometheus and distributed Loki or a managed service.

- **Multi-region deployments.** This stack has no built-in replication or
  global query federation. Use managed observability (Grafana Cloud, Datadog,
  Honeycomb) or a Kubernetes-native stack (kube-prometheus-stack, Loki Helm
  chart).

- **Regulated industries without additional hardening.** Environments subject
  to SOC 2, HIPAA, PCI-DSS, or ISO 27001 require audit logging, access
  controls, encryption at rest, and credential rotation that go beyond what
  this Compose stack provides out of the box. Treat this as a starting point
  that requires a formal security review before production use in regulated
  contexts.

- **Untrusted multi-tenant environments.** All telemetry shares one Prometheus,
  Loki, and Tempo instance with no tenant isolation. Do not co-mingle telemetry
  from different security domains.
