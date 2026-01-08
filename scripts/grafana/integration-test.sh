#!/bin/bash
# Grafana Integration Test
# Tests Grafana provisioning, datasources, and dashboards

set -e

TIMEOUT=120
INTERVAL=5
ELAPSED=0
ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}

echo "🚀 Starting Grafana integration test..."
echo ""

# Check if Grafana is already running
if docker compose ps grafana 2>/dev/null | grep -q "Up"; then
    echo "✅ Grafana is already running"
else
    echo "Starting Grafana..."
    docker compose --profile core up -d grafana
fi

echo ""
echo "⏳ Waiting for Grafana to be ready..."

while [ $ELAPSED -lt $TIMEOUT ]; do
    # Check container health
    if docker compose ps grafana 2>/dev/null | grep -q "(healthy)"; then
        echo "✅ Grafana container is healthy"
        break
    fi
    
    # Check for provisioning errors in logs
    if docker compose logs grafana 2>&1 | grep -i "error.*provisioning" | grep -v "context canceled"; then
        echo "❌ Provisioning error detected in logs"
        echo ""
        echo "Recent logs:"
        docker compose logs --tail=50 grafana
        exit 1
    fi
    
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
    echo "  Waiting... ($ELAPSED/$TIMEOUT seconds)"
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "❌ Timeout waiting for Grafana to be healthy"
    echo ""
    echo "Container status:"
    docker compose ps grafana
    echo ""
    echo "Recent logs:"
    docker compose logs --tail=50 grafana
    exit 1
fi

echo ""

# Wait a bit more for API to be fully ready
sleep 5

# Test 1: Health Check
echo "🔍 Test 1: Health Check"
HEALTH_RESPONSE=$(curl -s -f "http://localhost:3000/api/health" || echo "")
if [ -z "$HEALTH_RESPONSE" ]; then
    echo "❌ Failed to reach health endpoint"
    exit 1
fi

if command -v jq &> /dev/null; then
    if echo "$HEALTH_RESPONSE" | jq -e '.database == "ok"' > /dev/null 2>&1; then
        echo "✅ Health check passed"
    else
        echo "❌ Database not healthy"
        echo "Response: $HEALTH_RESPONSE"
        exit 1
    fi
else
    echo "✅ Health endpoint reachable (jq not available for detailed check)"
fi

echo ""

# Test 2: Datasource Provisioning
echo "🔍 Test 2: Datasource Provisioning"
DATASOURCES=$(curl -s -u "admin:$ADMIN_PASSWORD" "http://localhost:3000/api/datasources" || echo "[]")

if command -v jq &> /dev/null; then
    PROMETHEUS_DS=$(echo "$DATASOURCES" | jq '.[] | select(.name=="Prometheus")')
    
    if [ -z "$PROMETHEUS_DS" ]; then
        echo "❌ Prometheus datasource not found"
        echo "Available datasources:"
        echo "$DATASOURCES" | jq -r '.[].name // "none"'
        exit 1
    fi
    
    echo "✅ Prometheus datasource found"
    
    # Verify datasource properties
    DS_TYPE=$(echo "$PROMETHEUS_DS" | jq -r '.type')
    DS_URL=$(echo "$PROMETHEUS_DS" | jq -r '.url')
    DS_DEFAULT=$(echo "$PROMETHEUS_DS" | jq -r '.isDefault')
    
    if [ "$DS_TYPE" != "prometheus" ]; then
        echo "❌ Datasource type is $DS_TYPE, expected prometheus"
        exit 1
    fi
    
    if [ "$DS_URL" != "http://prometheus:9090" ]; then
        echo "❌ Datasource URL is $DS_URL, expected http://prometheus:9090"
        exit 1
    fi
    
    if [ "$DS_DEFAULT" != "true" ]; then
        echo "⚠️  Datasource is not set as default"
    fi
    
    echo "✅ Datasource configuration validated"
else
    echo "✅ Datasources endpoint reachable (jq not available for detailed check)"
fi

echo ""

# Test 3: Dashboard Provisioning
echo "🔍 Test 3: Dashboard Provisioning"
DASHBOARDS=$(curl -s -u "admin:$ADMIN_PASSWORD" "http://localhost:3000/api/search?type=dash-db" || echo "[]")

if command -v jq &> /dev/null; then
    DASHBOARD_COUNT=$(echo "$DASHBOARDS" | jq 'length')
    echo "Found $DASHBOARD_COUNT dashboard(s)"
    
    # Check for required dashboards
    REQUIRED_DASHBOARDS=("node-exporter" "prometheus" "otel-collector")
    
    for dashboard_uid in "${REQUIRED_DASHBOARDS[@]}"; do
        FOUND=$(echo "$DASHBOARDS" | jq -e --arg uid "$dashboard_uid" '.[] | select(.uid==$uid)' > /dev/null 2>&1 && echo "yes" || echo "no")
        
        if [ "$FOUND" == "yes" ]; then
            TITLE=$(echo "$DASHBOARDS" | jq -r --arg uid "$dashboard_uid" '.[] | select(.uid==$uid) | .title')
            echo "✅ Found dashboard: $TITLE (uid: $dashboard_uid)"
        else
            echo "❌ Dashboard not found: $dashboard_uid"
            exit 1
        fi
    done
    
    if [ "$DASHBOARD_COUNT" -lt "${#REQUIRED_DASHBOARDS[@]}" ]; then
        echo "❌ Insufficient dashboards provisioned"
        exit 1
    fi
    
    echo "✅ All required dashboards provisioned"
else
    echo "✅ Dashboards endpoint reachable (jq not available for detailed check)"
fi

echo ""

# Test 4: Datasource Connectivity (if Prometheus is running)
if docker compose ps prometheus 2>/dev/null | grep -q "Up"; then
    echo "🔍 Test 4: Datasource Connectivity"
    
    if command -v jq &> /dev/null; then
        DS_UID=$(echo "$DATASOURCES" | jq -r '.[] | select(.name=="Prometheus") | .uid')
        
        if [ -n "$DS_UID" ] && [ "$DS_UID" != "null" ]; then
            QUERY_RESPONSE=$(curl -s -u "admin:$ADMIN_PASSWORD" -X POST \
                -H "Content-Type: application/json" \
                -d "{\"queries\":[{\"refId\":\"A\",\"datasource\":{\"uid\":\"$DS_UID\"},\"expr\":\"up\",\"instant\":true}]}" \
                "http://localhost:3000/api/ds/query" || echo "{}")
            
            if echo "$QUERY_RESPONSE" | jq -e '.results' > /dev/null 2>&1; then
                echo "✅ Datasource connectivity validated"
            else
                echo "⚠️  Could not validate datasource connectivity"
                echo "Response: $QUERY_RESPONSE"
            fi
        else
            echo "⚠️  Could not get datasource UID"
        fi
    else
        echo "⚠️  jq not available, skipping connectivity test"
    fi
else
    echo "⚠️  Test 4: Skipped (Prometheus not running)"
fi

echo ""
echo "✅ All integration tests passed!"
echo ""
echo "Grafana is accessible at: http://localhost:3000"
echo "Username: admin"
echo "Password: $ADMIN_PASSWORD"
echo ""
echo "To view logs: docker compose logs -f grafana"
echo "To restart: docker compose restart grafana"
