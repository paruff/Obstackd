---
name: Docker Compose Instructions
description: Applied automatically when working on compose.yaml
applyTo: "compose.yaml,docker-compose*.yml,docker-compose*.yaml"
---

# Docker Compose Instructions — Obstackd

## Read First
- `AGENTS.md` → compose.yaml rules
- `docs/CHANGE_IMPACT_MAP.md` — what breaks when services change

## Pinned Versions — Always

```yaml
# ✅ Pinned
services:
  prometheus:
    image: prom/prometheus:v2.50.1

# ❌ Never
services:
  prometheus:
    image: prom/prometheus:latest
    image: prom/prometheus  # implicit latest
```

## Every Service Needs a Healthcheck

```yaml
# ✅ Required pattern
services:
  prometheus:
    image: prom/prometheus:v2.50.1
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  grafana:
    image: grafana/grafana:v10.4.2
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3000/api/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Secrets in .env Only

```yaml
# ✅ Reference from environment
services:
  grafana:
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}

# ❌ Never inline
services:
  grafana:
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
```

## Named Volumes, Explicit Networks

```yaml
# ✅ Named volumes and explicit networks
volumes:
  prometheus_data:
  grafana_data:
  tempo_data:

networks:
  observability:
    driver: bridge

services:
  prometheus:
    volumes:
      - prometheus_data:/prometheus
    networks:
      - observability

# ❌ Anonymous volumes, implicit network
services:
  prometheus:
    volumes:
      - /prometheus  # anonymous
```

## Service Dependencies

```yaml
services:
  grafana:
    depends_on:
      prometheus:
        condition: service_healthy
      tempo:
        condition: service_healthy
```

## Labels on Every Service

```yaml
services:
  prometheus:
    labels:
      - "plane=obstackd"
      - "component=metrics"
      - "managed-by=fawkes"
```
