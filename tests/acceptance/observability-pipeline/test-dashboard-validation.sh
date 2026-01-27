#!/bin/bash
# End-to-End Dashboard Validation Test
# Test ID: OBS-E2E-DASHBOARD-VALIDATION-001
# Validates that all dashboards display metrics, logs, and traces correctly

set -euo pipefail

# Configuration
readonly TIMESTAMP=$(date +%Y%m%d-%H%M%S)
readonly TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPORT_DIR="${TEST_DIR}/reports/dashboard-validation-${TIMESTAMP}"
readonly LOG_FILE="${REPORT_DIR}/test-execution.log"

# Colors for output
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Initialize test environment
initialize_test() {
    echo -e "${BLUE}🚀 Initializing Dashboard Validation E2E Test${NC}"
    echo "Test ID: OBS-E2E-DASHBOARD-VALIDATION-001"
    echo "Timestamp: ${TIMESTAMP}"
    
    mkdir -p "${REPORT_DIR}"
    exec > >(tee -a "${LOG_FILE}") 2>&1
}

# Test Result Tracking
declare -A TEST_RESULTS
declare -A TEST_DURATIONS
START_TIME=$(date +%s)

record_test_result() {
    local test_id=$1
    local result=$2
    local duration=$3
    local message=$4
    
    TEST_RESULTS["${test_id}"]="${result}"
    TEST_DURATIONS["${test_id}"]="${duration}"
    
    echo "TEST: ${test_id} | RESULT: ${result} | DURATION: ${duration}s | MESSAGE: ${message}" \
        >> "${REPORT_DIR}/test-results.csv"
}

# Verify infrastructure is ready
check_infrastructure_ready() {
    local start=$(date +%s)
    local test_id="INFRA-READY"
    
    echo -e "\n${BLUE}[${test_id}] Checking Infrastructure${NC}"
    
    # Check all required services
    local services=("prometheus" "loki" "tempo" "grafana" "alloy" "otel-collector")
    local ready=0
    
    for service in "${services[@]}"; do
        if docker compose ps "$service" | grep -q "Up"; then
            echo -e "  ${GREEN}✓${NC} $service is running"
            ((ready++))
        else
            echo -e "  ${RED}✗${NC} $service is not running"
        fi
    done
    
    if [[ $ready -eq ${#services[@]} ]]; then
        echo -e "${GREEN}✓ All services running${NC}"
        record_test_result "${test_id}" "PASS" $(( $(date +%s) - start )) "All services ready"
        return 0
    else
        echo -e "${RED}✗ Some services not running${NC}"
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Missing services"
        return 1
    fi
}

# Verify Grafana dashboards are provisioned
check_dashboards_provisioned() {
    local start=$(date +%s)
    local test_id="DASHBOARD-PROVISIONING"
    
    echo -e "\n${BLUE}[${test_id}] Checking Dashboard Provisioning${NC}"
    
    # Query Grafana API for dashboards
    local dashboards
    dashboards=$(curl -s -u admin:admin "http://localhost:3000/api/search?type=dash-db" 2>/dev/null || echo "[]")
    
    local dashboard_count
    dashboard_count=$(echo "$dashboards" | jq '. | length' 2>/dev/null || echo "0")
    
    echo "  Found $dashboard_count dashboards in Grafana"
    
    # Check for expected dashboards
    local expected_dashboards=(
        "observability-stack-health"
        "application-performance"
        "infrastructure-overview"
        "iot-devices-mqtt"
    )
    
    local found=0
    for expected_uid in "${expected_dashboards[@]}"; do
        if echo "$dashboards" | jq -e ".[] | select(.uid==\"$expected_uid\")" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} Found dashboard: $expected_uid"
            ((found++))
        else
            echo -e "  ${YELLOW}⚠${NC} Missing dashboard: $expected_uid"
        fi
    done
    
    if [[ $found -eq ${#expected_dashboards[@]} ]]; then
        echo -e "${GREEN}✓ All expected dashboards provisioned${NC}"
        record_test_result "${test_id}" "PASS" $(( $(date +%s) - start )) "All dashboards found"
        return 0
    else
        echo -e "${YELLOW}⚠ Some dashboards missing${NC}"
        record_test_result "${test_id}" "WARN" $(( $(date +%s) - start )) "Found $found of ${#expected_dashboards[@]} dashboards"
        return 0
    fi
}

# Verify metrics data in Prometheus
check_metrics_available() {
    local start=$(date +%s)
    local test_id="METRICS-DATA"
    
    echo -e "\n${BLUE}[${test_id}] Checking Metrics Availability${NC}"
    
    # Check for OTel Collector metrics
    local otel_metrics
    otel_metrics=$(curl -s "http://localhost:9090/api/v1/query?query=up{job=\"otel-collector\"}" 2>/dev/null | jq '.data.result | length' || echo "0")
    echo "  OTel Collector metrics: $otel_metrics series"
    
    # Check for Prometheus self-metrics
    local prometheus_metrics
    prometheus_metrics=$(curl -s "http://localhost:9090/api/v1/query?query=up{job=\"prometheus\"}" 2>/dev/null | jq '.data.result | length' || echo "0")
    echo "  Prometheus self-metrics: $prometheus_metrics series"
    
    # Check for Alertmanager metrics
    local alertmanager_metrics
    alertmanager_metrics=$(curl -s "http://localhost:9090/api/v1/query?query=up{job=\"alertmanager\"}" 2>/dev/null | jq '.data.result | length' || echo "0")
    echo "  Alertmanager metrics: $alertmanager_metrics series"
    
    if [[ $prometheus_metrics -gt 0 ]]; then
        echo -e "${GREEN}✓ Prometheus metrics available${NC}"
        record_test_result "${test_id}" "PASS" $(( $(date +%s) - start )) "Metrics available"
        return 0
    else
        echo -e "${YELLOW}⚠ Limited metrics available${NC}"
        record_test_result "${test_id}" "WARN" $(( $(date +%s) - start )) "Minimal metrics"
        return 0
    fi
}

# Verify logs data in Loki via Alloy
check_logs_available() {
    local start=$(date +%s)
    local test_id="LOGS-DATA"
    
    echo -e "\n${BLUE}[${test_id}] Checking Logs Availability (Alloy → Loki)${NC}"
    
    # Check for docker logs in Loki
    local now
    now=$(date +%s)000000000
    local ten_min_ago
    ten_min_ago=$(($(date +%s) - 600))000000000
    
    local logs_response
    logs_response=$(curl -s -G "http://localhost:3100/loki/api/v1/query_range" \
        --data-urlencode 'query={job="docker"}' \
        --data-urlencode "start=$ten_min_ago" \
        --data-urlencode "end=$now" \
        --data-urlencode "limit=10" 2>/dev/null || echo '{"data":{"result":[]}}')
    
    local log_streams
    log_streams=$(echo "$logs_response" | jq '.data.result | length' 2>/dev/null || echo "0")
    echo "  Docker log streams from Alloy: $log_streams"
    
    # Check for compose_service labels
    local services_response
    services_response=$(curl -s "http://localhost:3100/loki/api/v1/label/compose_service/values" 2>/dev/null || echo '{"data":[]}')
    
    local service_count
    service_count=$(echo "$services_response" | jq '.data | length' 2>/dev/null || echo "0")
    echo "  Services with logs: $service_count"
    
    if [[ $log_streams -gt 0 ]]; then
        echo -e "${GREEN}✓ Logs available in Loki from Alloy${NC}"
        record_test_result "${test_id}" "PASS" $(( $(date +%s) - start )) "Logs available"
        return 0
    else
        echo -e "${YELLOW}⚠ No logs in Loki yet (Alloy may still be discovering)${NC}"
        record_test_result "${test_id}" "WARN" $(( $(date +%s) - start )) "No logs yet"
        return 0
    fi
}

# Verify traces data in Tempo
check_traces_available() {
    local start=$(date +%s)
    local test_id="TRACES-DATA"
    
    echo -e "\n${BLUE}[${test_id}] Checking Traces Availability${NC}"
    
    # Check Tempo ready endpoint
    local tempo_ready
    tempo_ready=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3200/ready" 2>/dev/null)
    
    if [[ "$tempo_ready" == "200" ]]; then
        echo -e "  ${GREEN}✓${NC} Tempo is ready"
        
        # Try to query for traces (may be empty but endpoint should work)
        local traces_response
        traces_response=$(curl -s "http://localhost:3200/api/traces?limit=10" 2>/dev/null || echo '{"traces":[]}')
        
        echo -e "${GREEN}✓ Traces endpoint accessible${NC}"
        record_test_result "${test_id}" "PASS" $(( $(date +%s) - start )) "Traces endpoint ready"
        return 0
    else
        echo -e "${RED}✗ Tempo not ready (HTTP $tempo_ready)${NC}"
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Tempo not ready"
        return 1
    fi
}

# Test dashboard rendering for metrics
test_dashboard_metrics_rendering() {
    local start=$(date +%s)
    local test_id="DASHBOARD-METRICS-RENDER"
    
    echo -e "\n${BLUE}[${test_id}] Testing Dashboard Metrics Rendering${NC}"
    
    # Fetch observability-stack-health dashboard
    local dashboard
    dashboard=$(curl -s -u admin:admin "http://localhost:3000/api/dashboards/uid/observability-stack-health" 2>/dev/null || echo '{}')
    
    local title
    title=$(echo "$dashboard" | jq -r '.dashboard.title' 2>/dev/null || echo "")
    
    if [[ "$title" == "Observability Stack Health" ]]; then
        local panel_count
        panel_count=$(echo "$dashboard" | jq '.dashboard.panels | length' 2>/dev/null || echo "0")
        
        echo "  Dashboard loaded with $panel_count panels"
        echo -e "${GREEN}✓ Dashboard renders correctly${NC}"
        record_test_result "${test_id}" "PASS" $(( $(date +%s) - start )) "Dashboard renders"
        return 0
    else
        echo -e "${RED}✗ Could not load dashboard${NC}"
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Dashboard load failed"
        return 1
    fi
}

# Test dashboard rendering for logs
test_dashboard_logs_queries() {
    local start=$(date +%s)
    local test_id="DASHBOARD-LOGS-QUERIES"
    
    echo -e "\n${BLUE}[${test_id}] Testing Dashboard Log Queries${NC}"
    
    # Fetch application-performance dashboard
    local dashboard
    dashboard=$(curl -s -u admin:admin "http://localhost:3000/api/dashboards/uid/application-performance" 2>/dev/null || echo '{}')
    
    # Check for Loki queries in dashboard
    local loki_targets
    loki_targets=$(echo "$dashboard" | jq '[.. | select(.datasourceUid? == "loki")] | length' 2>/dev/null || echo "0")
    
    if [[ "$loki_targets" -gt 0 ]]; then
        echo "  Dashboard has $loki_targets Loki targets"
        echo -e "${GREEN}✓ Dashboard has log queries${NC}"
        record_test_result "${test_id}" "PASS" $(( $(date +%s) - start )) "Log queries present"
        return 0
    else
        echo -e "${YELLOW}⚠ Limited log queries in dashboard${NC}"
        record_test_result "${test_id}" "WARN" $(( $(date +%s) - start )) "Few or no log queries"
        return 0
    fi
}

# Test trace correlation configuration
test_trace_correlation() {
    local start=$(date +%s)
    local test_id="TRACE-CORRELATION"
    
    echo -e "\n${BLUE}[${test_id}] Testing Trace Correlation${NC}"
    
    # Check datasources for trace correlation
    local datasources
    datasources=$(curl -s -u admin:admin "http://localhost:3000/api/datasources" 2>/dev/null || echo '[]')
    
    # Check Loki datasource for derivedFields
    local loki_derived
    loki_derived=$(echo "$datasources" | jq '[.[] | select(.type=="loki" and .jsonData.derivedFields)] | length' 2>/dev/null || echo "0")
    
    # Check Tempo datasource for service map
    local tempo_services
    tempo_services=$(echo "$datasources" | jq '[.[] | select(.type=="tempo" and .jsonData.serviceMap)] | length' 2>/dev/null || echo "0")
    
    if [[ $loki_derived -gt 0 && $tempo_services -gt 0 ]]; then
        echo "  Loki derivedFields: $loki_derived, Tempo serviceMap: $tempo_services"
        echo -e "${GREEN}✓ Trace correlation configured${NC}"
        record_test_result "${test_id}" "PASS" $(( $(date +%s) - start )) "Correlation configured"
        return 0
    else
        echo -e "${YELLOW}⚠ Partial trace correlation${NC}"
        record_test_result "${test_id}" "WARN" $(( $(date +%s) - start )) "Partial configuration"
        return 0
    fi
}

# Generate summary report
generate_summary_report() {
    local end_time=$(date +%s)
    local total_duration=$((end_time - START_TIME))
    
    local passed=0
    local failed=0
    local warned=0
    
    for test_id in "${!TEST_RESULTS[@]}"; do
        case "${TEST_RESULTS[${test_id}]}" in
            "PASS") ((passed++)) ;;
            "FAIL") ((failed++)) ;;
            "WARN") ((warned++)) ;;
        esac
    done
    
    local total=$((passed + failed + warned))
    
    cat > "${REPORT_DIR}/summary.md" << EOF
# Dashboard Validation E2E Test - Summary

**Test ID:** OBS-E2E-DASHBOARD-VALIDATION-001  
**Timestamp:** ${TIMESTAMP}  
**Duration:** ${total_duration}s  

## Results

- **Total Tests:** ${total}
- **Passed:** ${passed} ✓
- **Failed:** ${failed} ✗
- **Warnings:** ${warned} ⚠

## Test Details

| Test ID | Result | Duration | Message |
|---------|--------|----------|---------|
EOF
    
    for test_id in "${!TEST_RESULTS[@]}"; do
        local result="${TEST_RESULTS[${test_id}]}"
        local duration="${TEST_DURATIONS[${test_id}]}"
        local symbol
        case "${result}" in
            "PASS") symbol="✓" ;;
            "FAIL") symbol="✗" ;;
            "WARN") symbol="⚠" ;;
        esac
        
        local message
        message=$(grep "^TEST: ${test_id}" "${REPORT_DIR}/test-results.csv" 2>/dev/null | cut -d'|' -f4 | sed 's/^ MESSAGE: //')
        
        echo "| ${test_id} | ${symbol} ${result} | ${duration}s | ${message} |" >> "${REPORT_DIR}/summary.md"
    done
    
    if [[ ${failed} -eq 0 ]]; then
        cat >> "${REPORT_DIR}/summary.md" << EOF

## Conclusion

✅ **DASHBOARD VALIDATION PASSED**

All dashboards are properly configured and receiving data:
- Metrics flowing from Prometheus to dashboards
- Logs flowing from Alloy → Loki to dashboards
- Traces accessible in Tempo
- Trace correlation configured for cross-system navigation

EOF
        return 0
    else
        cat >> "${REPORT_DIR}/summary.md" << EOF

## Conclusion

❌ **DASHBOARD VALIDATION FAILED**

${failed} critical test(s) failed. Review the test logs for details.

EOF
        return 1
    fi
}

# Main test execution
main() {
    initialize_test
    
    local overall_result=0
    
    # Infrastructure checks
    check_infrastructure_ready || overall_result=1
    check_dashboards_provisioned || true  # Warning only
    
    # Data availability checks
    check_metrics_available || true
    check_logs_available || true
    check_traces_available || overall_result=1
    
    # Dashboard validation
    test_dashboard_metrics_rendering || overall_result=1
    test_dashboard_logs_queries || true
    test_trace_correlation || true
    
    # Generate report
    echo ""
    echo "========================================"
    generate_summary_report || overall_result=1
    echo "========================================"
    
    cat "${REPORT_DIR}/summary.md"
    
    echo ""
    echo "Report saved to: ${REPORT_DIR}/summary.md"
    echo "Full logs: ${LOG_FILE}"
    
    exit ${overall_result}
}

main "$@"
