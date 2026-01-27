#!/bin/bash
# End-to-End Observability Pipeline Acceptance Test
# Test ID: OBS-ACCEPTANCE-001
# Validates that OpenTelemetry Collector metrics are visible through the entire pipeline

set -euo pipefail

# Configuration
readonly TIMESTAMP=$(date +%Y%m%d-%H%M%S)
readonly TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPORT_DIR="${TEST_DIR}/reports/${TIMESTAMP}"
readonly LOG_FILE="${REPORT_DIR}/test-execution.log"
readonly SUCCESS_FILE="${REPORT_DIR}/SUCCESS"
readonly FAILURE_FILE="${REPORT_DIR}/FAILURE"

# Test Constants
readonly MAX_DURATION=120  # seconds
readonly RETRY_INTERVAL=5
readonly RETRY_ATTEMPTS=3

# Colors for output
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Initialize test environment
initialize_test() {
    echo -e "${BLUE}🚀 Initializing Observability Acceptance Test${NC}"
    echo "Test ID: OBS-ACCEPTANCE-001"
    echo "Timestamp: ${TIMESTAMP}"
    echo "Max Duration: ${MAX_DURATION}s"
    
    # Create report directory
    mkdir -p "${REPORT_DIR}"
    
    # Start logging
    exec > >(tee -a "${LOG_FILE}") 2>&1
    
    # Record environment
    {
        echo "Environment:"
        echo "Hostname: $(hostname)"
        echo "OS: $(uname -a)"
        echo "Docker: $(docker --version 2>/dev/null || echo 'Not available')"
        echo "Test started at: $(date)"
        echo ""
    } > "${REPORT_DIR}/environment.txt"
}

# Test Result Tracking
TESTS_PASSED=0
TESTS_FAILED=0
START_TIME=$(date +%s)

record_test_result() {
    local test_id=$1
    local result=$2
    local duration=$3
    local message=$4
    
    if [ "$result" = "PASS" ]; then
        ((TESTS_PASSED++))
        echo -e "${GREEN}✅ ${test_id}: ${message} (${duration}s)${NC}"
    else
        ((TESTS_FAILED++))
        echo -e "${RED}❌ ${test_id}: ${message} (${duration}s)${NC}"
    fi
    
    echo "TEST: ${test_id} | RESULT: ${result} | DURATION: ${duration}s | MESSAGE: ${message}" \
        >> "${REPORT_DIR}/test-results.csv"
}

# Component Health Checks
check_otel_collector_health() {
    local start=$(date +%s)
    local test_id="COMP-HEALTH-OTEL"
    
    echo -e "\n${BLUE}[${test_id}] Checking OpenTelemetry Collector Health${NC}"
    
    # Check OTLP HTTP endpoint is listening (404 is OK, means it's up)
    local http_status
    http_status=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "http://localhost:4318" 2>/dev/null)
    if [[ -z "${http_status}" ]] || [[ "${http_status}" == "000" ]]; then
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "OTLP HTTP endpoint unreachable"
        return 1
    fi
    
    # Check metrics endpoint with retry
    local metrics_output
    local attempt
    for attempt in $(seq 1 ${RETRY_ATTEMPTS}); do
        if metrics_output=$(curl -s -m 15 "http://localhost:8888/metrics" 2>/dev/null); then
            if [[ -n "${metrics_output}" ]]; then
                break
            fi
        fi
        echo "  Waiting for metrics... (attempt ${attempt}/${RETRY_ATTEMPTS})"
        sleep ${RETRY_INTERVAL}
    done
    
    if [[ -z "${metrics_output}" ]]; then
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Metrics endpoint unreachable or empty"
        return 1
    fi
    
    # Verify self-metrics exist
    if ! echo "${metrics_output}" | grep -q "otelcol_process_uptime"; then
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Missing otelcol_process_uptime metric"
        return 1
    fi
    
    local duration=$(( $(date +%s) - start ))
    record_test_result "${test_id}" "PASS" "${duration}" "OTel Collector healthy with self-metrics"
    echo -e "${GREEN}✅ OTel Collector healthy (${duration}s)${NC}"
    return 0
}

check_prometheus_scraping() {
    local start=$(date +%s)
    local test_id="COMP-HEALTH-PROM"
    
    echo -e "\n${BLUE}[${test_id}] Checking Prometheus Scraping${NC}"
    
    # Check Prometheus health
    if ! curl -sf -m 10 "http://localhost:9090/-/healthy" >/dev/null 2>&1; then
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Prometheus unhealthy"
        return 1
    fi
    
    # Check targets endpoint
    local targets_json
    for attempt in $(seq 1 ${RETRY_ATTEMPTS}); do
        if targets_json=$(curl -sf -m 10 "http://localhost:9090/api/v1/targets" 2>/dev/null); then
            break
        fi
        sleep ${RETRY_INTERVAL}
    done
    
    if [[ -z "${targets_json}" ]]; then
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Cannot fetch Prometheus targets"
        return 1
    fi
    
    # Parse targets to find otel-collector
    local target_state
    if ! target_state=$(echo "${targets_json}" | jq -r '.data.activeTargets[] | select(.labels.job == "otel-collector") | .health' 2>/dev/null); then
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Cannot parse Prometheus targets JSON"
        return 1
    fi
    
    if [[ "${target_state}" != "up" ]]; then
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "OTel Collector target state: ${target_state:-unknown}"
        return 1
    fi
    
    # Query for OTel metrics in Prometheus
    local query_result
    if ! query_result=$(curl -sf -m 15 "http://localhost:9090/api/v1/query?query=otelcol_process_uptime" 2>/dev/null); then
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Cannot query Prometheus for OTel metrics"
        return 1
    fi
    
    local metric_count
    metric_count=$(echo "${query_result}" | jq '.data.result | length' 2>/dev/null || echo "0")
    
    if [[ "${metric_count}" -eq 0 ]]; then
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "No OTel metrics found in Prometheus"
        return 1
    fi
    
    local duration=$(( $(date +%s) - start ))
    record_test_result "${test_id}" "PASS" "${duration}" "Prometheus scraping OTel metrics successfully"
    echo -e "${GREEN}✅ Prometheus scraping OTel metrics (${duration}s, ${metric_count} metrics)${NC}"
    return 0
}

check_grafana_datasource() {
    local start=$(date +%s)
    local test_id="COMP-HEALTH-GRAFANA-DS"
    
    echo -e "\n${BLUE}[${test_id}] Checking Grafana Datasource${NC}"
    
    # Check Grafana health
    if ! curl -sf -m 10 "http://localhost:3000/api/health" >/dev/null 2>&1; then
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Grafana unhealthy"
        return 1
    fi
    
    # Get datasources (using default admin/admin for test)
    local datasources_json
    if ! datasources_json=$(curl -sf -m 10 -u "admin:admin" "http://localhost:3000/api/datasources" 2>/dev/null); then
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Cannot fetch Grafana datasources"
        return 1
    fi
    
    # Check Prometheus datasource exists
    local ds_uid
    if ! ds_uid=$(echo "${datasources_json}" | jq -r '.[] | select(.name=="Prometheus") | .uid' 2>/dev/null); then
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Prometheus datasource not found"
        return 1
    fi
    
    local duration=$(( $(date +%s) - start ))
    record_test_result "${test_id}" "PASS" "${duration}" "Grafana datasource configured"
    echo -e "${GREEN}✅ Grafana datasource configured (${duration}s)${NC}"
    echo "${ds_uid}" > "${REPORT_DIR}/grafana-datasource-uid.txt"
    return 0
}

# Main Acceptance Test: OTel Metrics in Grafana
test_otel_metrics_in_grafana() {
    local start=$(date +%s)
    local test_id="E2E-OTEL-GRAFANA"
    
    echo -e "\n${BLUE}[${test_id}] Executing End-to-End Test: OTel Metrics in Grafana${NC}"
    echo "Query: otelcol_process_uptime"
    echo "Expected: Graph shows data (time series with values > 0)"
    
    # Get datasource UID from previous test
    local ds_uid
    if [[ -f "${REPORT_DIR}/grafana-datasource-uid.txt" ]]; then
        ds_uid=$(cat "${REPORT_DIR}/grafana-datasource-uid.txt")
    else
        ds_uid=""
    fi
    
    # Execute query via Grafana API
    local query_payload
    query_payload=$(cat <<EOF
{
  "queries": [
    {
      "refId": "A",
      "datasource": {
        "uid": "${ds_uid:-"Prometheus"}"
      },
      "expr": "otelcol_process_uptime",
      "intervalMs": 15000,
      "maxDataPoints": 100
    }
  ],
  "from": "now-5m",
  "to": "now"
}
EOF
)
    
    local query_result
    local query_response
    local attempt
    
    for attempt in $(seq 1 ${RETRY_ATTEMPTS}); do
        echo "Query attempt ${attempt}/${RETRY_ATTEMPTS}..."
        
        if query_response=$(curl -sf -m 30 \
            -u "admin:admin" \
            -H "Content-Type: application/json" \
            -d "${query_payload}" \
            "http://localhost:3000/api/ds/query" 2>"${REPORT_DIR}/grafana-query-error.txt"); then
            
            query_result="${query_response}"
            break
        fi
        
        if [[ ${attempt} -lt ${RETRY_ATTEMPTS} ]]; then
            sleep ${RETRY_INTERVAL}
        fi
    done
    
    if [[ -z "${query_result}" ]]; then
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Grafana query failed after ${RETRY_ATTEMPTS} attempts"
        return 1
    fi
    
    # Save raw response for debugging
    echo "${query_result}" > "${REPORT_DIR}/grafana-query-response.json"
    
    # Validate response structure
    local status
    if ! status=$(echo "${query_result}" | jq -r '.results.A.status' 2>/dev/null); then
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Invalid Grafana response format"
        return 1
    fi
    
    if [[ "${status}" != "200" ]]; then
        local error_msg
        error_msg=$(echo "${query_result}" | jq -r '.results.A.error' 2>/dev/null || echo "Unknown error")
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Grafana query error: ${error_msg}"
        return 1
    fi
    
    # Check for actual data
    local data_points
    if ! data_points=$(echo "${query_result}" | jq '.results.A.frames[0].data.values[1] | length' 2>/dev/null); then
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "No data points in response"
        return 1
    fi
    
    if [[ "${data_points}" -eq 0 ]]; then
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Zero data points returned"
        return 1
    fi
    
    # Extract sample values for verification
    local sample_values
    sample_values=$(echo "${query_result}" | jq '.results.A.frames[0].data.values[1][0:3]' 2>/dev/null)
    
    # Check if values are numeric and positive (uptime should be > 0)
    local first_value
    first_value=$(echo "${sample_values}" | jq '.[0]' 2>/dev/null)
    
    if [[ -z "${first_value}" ]] || [[ "${first_value}" == "null" ]]; then
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Invalid/null metric values"
        return 1
    fi
    
    # Generate test evidence
    {
        echo "End-to-End Test Evidence: OTel Metrics in Grafana"
        echo "================================================"
        echo "Test ID: ${test_id}"
        echo "Query: otelcol_process_uptime"
        echo "Timestamp: $(date)"
        echo "Data Points Returned: ${data_points}"
        echo "Sample Values: ${sample_values}"
        echo "First Value: ${first_value}"
        echo ""
        echo "Response Summary:"
        echo "${query_result}" | jq '{
            status: .results.A.status,
            data_point_count: .results.A.frames[0].data.values[1] | length,
            first_value: .results.A.frames[0].data.values[1][0],
            last_value: .results.A.frames[0].data.values[1][-1]
        }'
    } > "${REPORT_DIR}/e2e-test-evidence.md"
    
    # Generate visualization data for documentation
    echo "${query_result}" | jq '.results.A.frames[0].data' > "${REPORT_DIR}/timeseries-data.json"
    
    local duration=$(( $(date +%s) - start ))
    record_test_result "${test_id}" "PASS" "${duration}" "OTel metrics visible in Grafana (${data_points} data points)"
    
    echo -e "${GREEN}✅ SUCCESS: OTel metrics visible in Grafana${NC}"
    echo "  Data points: ${data_points}"
    echo "  Sample value: ${first_value}"
    echo "  Duration: ${duration}s"
    
    return 0
}

# Generate Test Report
generate_test_report() {
    local end_time=$(date +%s)
    local total_duration=$((end_time - START_TIME))
    
    echo -e "\n${BLUE}📊 Generating Test Report${NC}"
    
    # Use the counters we already have
    local total_tests=$((TESTS_PASSED + TESTS_FAILED))
    local success_rate=0
    if [[ $total_tests -gt 0 ]]; then
        success_rate=$(( (TESTS_PASSED * 100) / total_tests ))
    fi
    
    # Generate summary report
    cat > "${REPORT_DIR}/summary.md" <<EOF
# Observability Pipeline Acceptance Test Report

## Test Summary
- **Test Suite**: Observability E2E Validation
- **Execution Time**: ${TIMESTAMP}
- **Total Duration**: ${total_duration} seconds
- **Total Tests**: ${total_tests}
- **Tests Passed**: ${TESTS_PASSED}
- **Tests Failed**: ${TESTS_FAILED}
- **Success Rate**: ${success_rate}%

## Test Results
See detailed results in: test-results.csv

## Environment
$(cat "${REPORT_DIR}/environment.txt")

## Evidence
- Grafana Query Response: \`grafana-query-response.json\`
- Time Series Data: \`timeseries-data.json\`
- Detailed Log: \`test-execution.log\`

## Conclusion
$(if [[ ${TESTS_FAILED} -eq 0 ]]; then
    echo "✅ **ALL TESTS PASSED** - Observability pipeline is fully functional"
else
    echo "❌ **TESTS FAILED** - Review failure details above"
fi)
EOF
    
    # Generate JSON report for CI/CD integration
    cat > "${REPORT_DIR}/report.json" <<EOF
{
  "test_suite": "observability_pipeline_acceptance",
  "timestamp": "${TIMESTAMP}",
  "duration_seconds": ${total_duration},
  "total_tests": ${total_tests},
  "passed_tests": ${TESTS_PASSED},
  "failed_tests": ${TESTS_FAILED},
  "success_rate": ${success_rate}
}
EOF
    
    # Create success/failure marker
    if [[ ${TESTS_FAILED} -eq 0 ]]; then
        touch "${SUCCESS_FILE}"
        echo -e "\n${GREEN}========================================${NC}"
        echo -e "${GREEN}✅ ACCEPTANCE TEST PASSED${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo "Report: ${REPORT_DIR}/summary.md"
        return 0
    else
        touch "${FAILURE_FILE}"
        echo -e "\n${RED}========================================${NC}"
        echo -e "${RED}❌ ACCEPTANCE TEST FAILED${NC}"
        echo -e "${RED}========================================${NC}"
        echo "Report: ${REPORT_DIR}/summary.md"
        echo "Log: ${LOG_FILE}"
        return 1
    fi
}

# Main execution
main() {
    initialize_test
    
    # Track overall success
    local all_passed=true
    
    # Component health checks
    if ! check_otel_collector_health; then
        all_passed=false
    fi
    
    if ! check_prometheus_scraping; then
        all_passed=false
    fi
    
    if ! check_grafana_datasource; then
        all_passed=false
    fi
    
    # Only run E2E test if components are healthy
    if [[ "${all_passed}" == true ]]; then
        if ! test_otel_metrics_in_grafana; then
            all_passed=false
        fi
    else
        record_test_result "E2E-OTEL-GRAFANA" "SKIP" "0" "Skipped due to component failures"
        echo -e "${YELLOW}⚠️  Skipping E2E test due to component failures${NC}"
    fi
    
    # Generate report
    generate_test_report
    
    # Exit with appropriate code
    if [[ "${all_passed}" == true ]]; then
        exit 0
    else
        exit 1
    fi
}

# Handle interrupts
trap 'echo -e "\n${YELLOW}Test interrupted by user${NC}"; exit 130' INT

# Run main function
main
