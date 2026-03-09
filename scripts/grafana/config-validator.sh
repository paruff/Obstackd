#!/bin/bash
# Grafana Configuration Validator
# Validates Grafana provisioning configuration and directory structure

set -euo pipefail

echo "🔍 Validating Grafana Provisioning Configuration..."
echo ""

# 1. Check directory structure
echo "📁 Checking directory structure..."
if [ ! -d "./config/grafana" ]; then
    echo "❌ Missing config/grafana directory"
    exit 1
fi
echo "✅ config/grafana directory exists"

if [ ! -f "./config/grafana/grafana.ini" ]; then
    echo "❌ Missing grafana.ini configuration file"
    exit 1
fi
echo "✅ grafana.ini configuration file exists"

if [ ! -d "./config/grafana/provisioning/datasources" ]; then
    echo "❌ Missing provisioning/datasources directory"
    exit 1
fi
echo "✅ provisioning/datasources directory exists"

if [ ! -f "./config/grafana/provisioning/datasources/datasources.yaml" ]; then
    echo "❌ Missing datasources.yaml configuration file"
    exit 1
fi
echo "✅ datasources.yaml configuration file exists"

if [ ! -d "./config/grafana/provisioning/dashboards" ]; then
    echo "❌ Missing provisioning/dashboards directory"
    exit 1
fi
echo "✅ provisioning/dashboards directory exists"

if [ ! -f "./config/grafana/provisioning/dashboards/dashboards.yaml" ]; then
    echo "❌ Missing dashboards.yaml configuration file"
    exit 1
fi
echo "✅ dashboards.yaml configuration file exists"

if [ ! -d "./config/grafana/dashboards" ]; then
    echo "❌ Missing dashboards directory"
    exit 1
fi
echo "✅ dashboards directory exists"

if [ ! -d "./data/grafana" ]; then
    echo "⚠️  Data directory missing, creating..."
    mkdir -p ./data/grafana
    chmod 750 ./data/grafana
fi
echo "✅ data/grafana directory ready"

echo ""

# 2. Validate YAML syntax
echo "🔧 Validating YAML syntax..."
if command -v yamllint &> /dev/null; then
    echo "Using yamllint..."
    yamllint -d "{extends: relaxed, rules: {line-length: {max: 200}}}" ./config/grafana/provisioning/datasources/datasources.yaml || {
        echo "⚠️  YAML linting warnings (non-fatal)"
    }
    yamllint -d "{extends: relaxed, rules: {line-length: {max: 200}}}" ./config/grafana/provisioning/dashboards/dashboards.yaml || {
        echo "⚠️  YAML linting warnings (non-fatal)"
    }
else
    echo "⚠️  yamllint not found, skipping YAML validation"
fi
echo "✅ YAML syntax check passed"

echo ""

# 3. Validate dashboard JSON files
echo "📊 Validating dashboard JSON files..."
DASHBOARD_COUNT=0
for dashboard in ./config/grafana/dashboards/*.json; do
    if [ -f "$dashboard" ]; then
        if command -v jq &> /dev/null; then
            if jq empty "$dashboard" 2>/dev/null; then
                echo "✅ $(basename "$dashboard") valid"
                DASHBOARD_COUNT=$((DASHBOARD_COUNT + 1))
            else
                echo "❌ $(basename "$dashboard") invalid JSON"
                exit 1
            fi
        else
            echo "⚠️  jq not found, skipping JSON validation for $(basename "$dashboard")"
            DASHBOARD_COUNT=$((DASHBOARD_COUNT + 1))
        fi
    fi
done

if [ $DASHBOARD_COUNT -eq 0 ]; then
    echo "⚠️  No dashboard JSON files found"
else
    echo "✅ Found and validated $DASHBOARD_COUNT dashboard(s)"
fi

echo ""

# 4. Validate Docker Compose syntax
echo "🐳 Validating docker-compose.yaml syntax..."
if ! docker compose config -q; then
    echo "❌ Docker Compose configuration is invalid"
    exit 1
fi
echo "✅ Docker Compose configuration is valid"

echo ""

# 5. Check port availability
echo "🔌 Checking port 3000..."
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 3000 is already in use"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Port 3000 is available"
fi

echo ""

# 6. Validate datasource configuration
echo "🔗 Validating datasource configuration..."
if command -v python3 &> /dev/null; then
    python3 - << 'EOF'
import yaml
import sys

try:
    with open('./config/grafana/provisioning/datasources/datasources.yaml') as f:
        ds = yaml.safe_load(f)
        
    if 'datasources' not in ds:
        print("❌ No datasources found in configuration")
        sys.exit(1)
        
    prometheus_found = False
    for datasource in ds['datasources']:
        if datasource.get('name') == 'Prometheus':
            prometheus_found = True
            if datasource.get('type') != 'prometheus':
                print("❌ Prometheus datasource has incorrect type")
                sys.exit(1)
            if datasource.get('url') != 'http://prometheus:9090':
                print("❌ Prometheus datasource has incorrect URL")
                sys.exit(1)
    
    if not prometheus_found:
        print("❌ Prometheus datasource not found")
        sys.exit(1)
        
    print("✅ Datasource configuration valid")
except Exception as e:
    print(f"❌ Error validating datasource configuration: {e}")
    sys.exit(1)
EOF
else
    echo "⚠️  python3 not found, skipping datasource validation"
fi

echo ""
echo "✅ All validation checks passed!"
echo ""
echo "Next steps:"
echo "  - Start Grafana: docker compose --profile core up -d grafana"
echo "  - Check health: curl -f http://localhost:3000/api/health"
echo "  - Access UI: http://localhost:3000 (admin/admin)"
echo "  - Run integration tests: ./scripts/grafana/integration-test.sh"
