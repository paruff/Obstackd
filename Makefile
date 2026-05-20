.PHONY: help init check-env up up-apps down logs status test-unit test-acceptance test

# Grafana runs as UID 472
GRAFANA_UID := 472
# Prometheus and Alertmanager run as nobody (UID 65534)
NOBODY_UID := 65534
# Loki and Tempo run as UID 10001
LGTM_UID := 10001

## help: print this help message
help:
	@grep -E '^## [a-z]' Makefile | sed 's/^## //' | awk -F': ' '{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

## init: create data directories with mode 755 and print required chown commands
init:
	@echo "Creating data directories (mode 755) — run the chown commands printed below to set ownership..."
	install -d -m 755 data/grafana
	install -d -m 755 data/prometheus
	install -d -m 755 data/alertmanager
	install -d -m 755 data/loki
	install -d -m 755 data/tempo
	install -d -m 755 data/alloy
	@echo ""
	@echo "⚠️  On Linux, if containers cannot write to data/ directories, run:"
	@echo "   sudo chown -R $(GRAFANA_UID) data/grafana         # Grafana UID"
	@echo "   sudo chown -R $(NOBODY_UID) data/prometheus data/alertmanager  # nobody UID"
	@echo "   sudo chown -R $(LGTM_UID) data/loki data/tempo   # Loki/Tempo UID"
	@echo "   (Alloy mounts data/alloy as root; no chown needed)"
	@echo ""
	@echo "✅ data/ directories ready"

## check-env: validate required environment variables
check-env:
	./scripts/check-env.sh

## up: start the core observability stack
up: check-env
	docker compose --profile core up -d

## up-apps: start the core stack plus demo telemetry generator
up-apps: check-env
	docker compose --profile core --profile apps up -d

## down: stop all services
down:
	docker compose down

## logs: tail logs for all running services
logs:
	docker compose logs -f

## status: show running containers and health endpoints
status:
	docker compose ps
	@echo ""
	@echo "Health endpoints:"
	@curl -sf http://localhost:9090/-/ready  > /dev/null && echo "  ✅ Prometheus  :9090" || echo "  ❌ Prometheus  :9090"
	@curl -sf http://localhost:3200/ready    > /dev/null && echo "  ✅ Tempo       :3200" || echo "  ❌ Tempo       :3200"
	@curl -sf http://localhost:3100/ready    > /dev/null && echo "  ✅ Loki        :3100" || echo "  ❌ Loki        :3100"
	@curl -sf http://localhost:3000/api/health > /dev/null && echo "  ✅ Grafana     :3000" || echo "  ❌ Grafana     :3000"
	@curl -sf http://localhost:9093/-/healthy > /dev/null && echo "  ✅ Alertmanager:9093" || echo "  ❌ Alertmanager:9093"
	@curl -sf http://localhost:8888/metrics > /dev/null && echo "  ✅ OTel Coll.  :8888" || echo "  ❌ OTel Coll.  :8888"
	@curl -sf http://localhost:12345/-/ready > /dev/null && echo "  ✅ Alloy       :12345" || echo "  ❌ Alloy       :12345"

## test-unit: run unit tests only
test-unit:
	pip install -q -r tests/unit/requirements.txt
	pytest tests/unit/

## test-acceptance: run acceptance tests (requires stack to be running: make up)
test-acceptance:
	@echo "Running acceptance tests — stack must already be up (run 'make up' first)"
	./tests/acceptance/observability-pipeline/test-otel-pipeline.sh

## test: run unit tests then acceptance tests (requires stack to be running: make up)
test: test-unit test-acceptance
