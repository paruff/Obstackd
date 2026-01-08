#!/bin/bash
# Prometheus Configuration Validator
# Validates Prometheus Docker Compose configuration and directory structure

set -e

# Prometheus version (should match compose.yaml)
PROMETHEUS_VERSION="v2.50.1"

echo "🔍 Validating Prometheus Docker Compose Configuration..."
echo ""

# 1. Check directory structure
echo "📁 Checking directory structure..."
if [ ! -d "./config/prometheus" ]; then
    echo "❌ Missing config/prometheus directory"
    exit 1
fi
echo "✅ config/prometheus directory exists"

if [ ! -f "./config/prometheus/prometheus.yaml" ]; then
    echo "❌ Missing prometheus.yaml configuration file"
    exit 1
fi
echo "✅ prometheus.yaml configuration file exists"

if [ ! -d "./data/prometheus" ]; then
    echo "⚠️  Data directory missing, creating..."
    mkdir -p ./data/prometheus
    chmod 750 ./data/prometheus
fi
echo "✅ data/prometheus directory ready"

echo ""

# 2. Validate Prometheus configuration
echo "🔧 Validating prometheus.yaml..."
if command -v promtool &> /dev/null; then
    echo "Using local promtool..."
    promtool check config ./config/prometheus/prometheus.yaml
else
    echo "Using docker to validate..."
    docker run --rm -v "$(pwd)/config/prometheus:/etc/prometheus" \
        --entrypoint promtool \
        "prom/prometheus:${PROMETHEUS_VERSION}" \
        check config /etc/prometheus/prometheus.yaml
fi
echo "✅ Prometheus configuration is valid"

echo ""

# 3. Validate Docker Compose syntax
echo "🐳 Validating docker-compose.yaml syntax..."
if ! docker compose config -q; then
    echo "❌ Docker Compose configuration is invalid"
    exit 1
fi
echo "✅ Docker Compose configuration is valid"

echo ""

# 4. Check port availability
echo "🔌 Checking port 9090..."
if lsof -Pi :9090 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 9090 is already in use"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Port 9090 is available"
fi

echo ""
echo "✅ All validation checks passed!"
echo ""
echo "Next steps:"
echo "  - Start Prometheus: docker compose --profile core up -d prometheus"
echo "  - Check health: curl -f http://localhost:9090/-/healthy"
echo "  - Access UI: http://localhost:9090"
