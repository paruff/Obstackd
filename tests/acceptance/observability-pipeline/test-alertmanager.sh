#!/bin/bash
# Alertmanager Integration Test
# Test ID: ALERT-ACCEPTANCE-001
# Validates that Alertmanager is integrated with Prometheus and can receive alerts

set -euo pipefail

# Configuration
readonly TIMESTAMP=$(date +%Y%m%d-%H%M%S)
readonly TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPORT_DIR="${TEST_DIR}/reports/${TIMESTAMP}"
readonly LOG_FILE="${REPORT_DIR}/test-execution.log"

# Test Constants
readonly MAX_WAIT=120
readonly RETRY_INTERVAL=5

# Colors for output
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Initialize test environment
initialize_test() {
    echo -e "${BLUE}🚀 Initializing Alertmanager Integration Test${NC}"
    echo "Test ID: ALERT-ACCEPTANCE-001"
    echo "Timestamp: ${TIMESTAMP}"
    echo "Max Wait: ${MAX_WAIT}s"

    mkdir -p "${REPORT_DIR}"
    exec > >(tee -a "${LOG_FILE}") 2>&1

    {
        echo "Environment:"
        echo "Hostname: $(hostname)"
        echo "Test started at: $(date)"
        echo ""
    } > "${REPORT_DIR}/environment.txt"
}

# Test Result Tracking
declare -A TEST_RESULTS
START_TIME=$(date +%s)

record_test_result() {
    local test_id=$1
    local result=$2
    local message=$3

    TEST_RESULTS["${test_id}"]="${result}"

    echo "TEST: ${test_id} | RESULT: ${result} | MESSAGE: ${message}" \
        >> "${REPORT_DIR}/test-results.csv"
}

# Test: Alertmanager is running and healthy
test_alertmanager_health() {
    local test_id="ALERT-HEALTH-001"
    echo -e "\n${BLUE}[${test_id}] Testing Alertmanager Health${NC}"

    # Check health endpoint
    if curl -sf http://localhost:9093/-/healthy > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Alertmanager is healthy${NC}"
        record_test_result "${test_id}" "PASS" "Alertmanager health check passed"
        return 0
    else
        echo -e "${RED}❌ Alertmanager health check failed${NC}"
        record_test_result "${test_id}" "FAIL" "Alertmanager not healthy"
        return 1
    fi
}

# Test: Alertmanager ready endpoint
test_alertmanager_ready() {
    local test_id="ALERT-READY-001"
    echo -e "\n${BLUE}[${test_id}] Testing Alertmanager Ready State${NC}"

    if curl -sf http://localhost:9093/-/ready > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Alertmanager is ready${NC}"
        record_test_result "${test_id}" "PASS" "Alertmanager ready check passed"
        return 0
    else
        echo -e "${RED}❌ Alertmanager ready check failed${NC}"
        record_test_result "${test_id}" "FAIL" "Alertmanager not ready"
        return 1
    fi
}

# Test: Prometheus can reach Alertmanager
test_prometheus_alertmanager_connection() {
    local test_id="ALERT-PROMETHEUS-001"
    echo -e "\n${BLUE}[${test_id}] Testing Prometheus to Alertmanager Connection${NC}"

    # Query Prometheus for Alertmanager targets
    local response
    response=$(curl -s http://localhost:9090/api/v1/targets 2>/dev/null || echo "")

    if echo "${response}" | grep -q "alertmanager"; then
        echo -e "${GREEN}✅ Prometheus is configured to send alerts to Alertmanager${NC}"
        record_test_result "${test_id}" "PASS" "Prometheus connected to Alertmanager"
        return 0
    else
        echo -e "${RED}❌ Prometheus not connected to Alertmanager${NC}"
        record_test_result "${test_id}" "FAIL" "Prometheus cannot reach Alertmanager"
        return 1
    fi
}

# Test: Alert rules are loaded in Prometheus
test_alert_rules_loaded() {
    local test_id="ALERT-RULES-001"
    echo -e "\n${BLUE}[${test_id}] Testing Alert Rules Loaded${NC}"

    local response
    response=$(curl -s http://localhost:9090/api/v1/rules 2>/dev/null || echo "")

    # Check if rules are loaded
    if echo "${response}" | grep -q '"type":"alerting"'; then
        local rule_count
        rule_count=$(echo "${response}" | grep -o '"type":"alerting"' | wc -l)
        echo -e "${GREEN}✅ Alert rules loaded: ${rule_count} rules found${NC}"
        record_test_result "${test_id}" "PASS" "Alert rules loaded (${rule_count} rules)"
        return 0
    else
        echo -e "${RED}❌ No alert rules found${NC}"
        record_test_result "${test_id}" "FAIL" "No alert rules loaded"
        return 1
    fi
}

# Test: Alertmanager API is accessible
test_alertmanager_api() {
    local test_id="ALERT-API-001"
    echo -e "\n${BLUE}[${test_id}] Testing Alertmanager API${NC}"

    # Get alerts from API
    local response
    response=$(curl -s http://localhost:9093/api/v2/alerts 2>/dev/null || echo "")

    if [[ "${response}" == "[]" ]] || echo "${response}" | grep -q '\['; then
        echo -e "${GREEN}✅ Alertmanager API is accessible${NC}"
        record_test_result "${test_id}" "PASS" "Alertmanager API working"
        return 0
    else
        echo -e "${RED}❌ Alertmanager API not accessible${NC}"
        record_test_result "${test_id}" "FAIL" "Alertmanager API failed"
        return 1
    fi
}

# Test: Alertmanager configuration is valid
test_alertmanager_config() {
    local test_id="ALERT-CONFIG-001"
    echo -e "\n${BLUE}[${test_id}] Testing Alertmanager Configuration${NC}"

    # Wait a moment for metrics to update
    sleep 2

    # Check if Alertmanager config was loaded successfully
    local response
    response=$(curl -s http://localhost:9093/metrics 2>/dev/null || echo "")

    if echo "${response}" | grep -q 'alertmanager_config_last_reload_successful 1'; then
        echo -e "${GREEN}✅ Alertmanager configuration is valid${NC}"
        record_test_result "${test_id}" "PASS" "Configuration loaded successfully"
        return 0
    else
        echo -e "${RED}❌ Alertmanager configuration may be invalid${NC}"
        record_test_result "${test_id}" "FAIL" "Configuration reload failed"
        return 1
    fi
}

# Test: Grafana can access Alertmanager datasource
test_grafana_alertmanager_datasource() {
    local test_id="ALERT-GRAFANA-001"
    echo -e "\n${BLUE}[${test_id}] Testing Grafana Alertmanager Datasource${NC}"

    # Check if Grafana has Alertmanager datasource
    local response
    response=$(curl -s -u admin:admin http://localhost:3000/api/datasources 2>/dev/null || echo "")

    if echo "${response}" | grep -q '"type":"alertmanager"'; then
        echo -e "${GREEN}✅ Grafana has Alertmanager datasource configured${NC}"
        record_test_result "${test_id}" "PASS" "Grafana datasource configured"
        return 0
    else
        echo -e "${YELLOW}⚠️  Grafana Alertmanager datasource not found${NC}"
        record_test_result "${test_id}" "WARN" "Datasource not configured"
        return 1
    fi
}

# Test: Alert routing configuration
test_alert_routing() {
    local test_id="ALERT-ROUTING-001"
    echo -e "\n${BLUE}[${test_id}] Testing Alert Routing Configuration${NC}"

    # Get Alertmanager config
    local response
    response=$(curl -s http://localhost:9093/api/v2/status 2>/dev/null || echo "")

    if echo "${response}" | grep -q 'route:'; then
        echo -e "${GREEN}✅ Alert routing is configured${NC}"
        record_test_result "${test_id}" "PASS" "Alert routing configured"
        return 0
    else
        echo -e "${RED}❌ Alert routing configuration missing${NC}"
        record_test_result "${test_id}" "FAIL" "No routing configuration"
        return 1
    fi
}

# Generate summary report
generate_summary() {
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    local warned_tests=0

    for test_id in "${!TEST_RESULTS[@]}"; do
        total_tests=$((total_tests + 1))
        case "${TEST_RESULTS[${test_id}]}" in
            PASS)
                passed_tests=$((passed_tests + 1))
                ;;
            FAIL)
                failed_tests=$((failed_tests + 1))
                ;;
            WARN)
                warned_tests=$((warned_tests + 1))
                ;;
        esac
    done

    local duration=$(($(date +%s) - START_TIME))

    {
        echo "# Alertmanager Integration Test Summary"
        echo ""
        echo "**Test ID:** ALERT-ACCEPTANCE-001"
        echo "**Timestamp:** ${TIMESTAMP}"
        echo "**Duration:** ${duration}s"
        echo ""
        echo "## Results"
        echo ""
        echo "- Total Tests: ${total_tests}"
        echo "- Passed: ${passed_tests}"
        echo "- Failed: ${failed_tests}"
        echo "- Warnings: ${warned_tests}"
        echo ""
        echo "## Test Details"
        echo ""
        while IFS='|' read -r test result message; do
            echo "- [${result}] ${test}: ${message}"
        done < <(grep "^TEST:" "${REPORT_DIR}/test-results.csv" | sed 's/TEST: //' | tr '|' '\n' | paste -d'|' - - -)
        echo ""
        echo "## Conclusion"
        echo ""
        if [[ ${failed_tests} -eq 0 ]]; then
            echo "✅ **All critical tests passed**"
        else
            echo "❌ **${failed_tests} test(s) failed**"
        fi
    } > "${REPORT_DIR}/summary.md"

    cat "${REPORT_DIR}/summary.md"
}

# Main execution
main() {
    initialize_test

    local all_passed=true

    # Run all tests
    test_alertmanager_health || all_passed=false
    test_alertmanager_ready || all_passed=false
    test_prometheus_alertmanager_connection || all_passed=false
    test_alert_rules_loaded || all_passed=false
    test_alertmanager_api || all_passed=false
    test_alertmanager_config || all_passed=false
    test_grafana_alertmanager_datasource || true  # Non-critical
    test_alert_routing || all_passed=false

    # Generate summary
    echo ""
    echo -e "${BLUE}=== Generating Test Summary ===${NC}"
    generate_summary

    # Final result
    echo ""
    if [[ "${all_passed}" == "true" ]]; then
        echo -e "${GREEN}=========================================${NC}"
        echo -e "${GREEN}✅ ALERTMANAGER INTEGRATION TEST PASSED${NC}"
        echo -e "${GREEN}=========================================${NC}"
        touch "${REPORT_DIR}/SUCCESS"
        return 0
    else
        echo -e "${RED}=========================================${NC}"
        echo -e "${RED}❌ ALERTMANAGER INTEGRATION TEST FAILED${NC}"
        echo -e "${RED}=========================================${NC}"
        touch "${REPORT_DIR}/FAILURE"
        return 1
    fi
}

# Run main function
main
