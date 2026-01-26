#!/bin/bash
# End-to-End Loki Log Aggregation Acceptance Test
# Test ID: OBS-ACCEPTANCE-LOKI-001
# Validates that container logs are collected by Promtail and queryable in Loki

set -euo pipefail

# Configuration
readonly TIMESTAMP=$(date +%Y%m%d-%H%M%S)
readonly TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPORT_DIR="${TEST_DIR}/reports/loki-${TIMESTAMP}"
readonly LOG_FILE="${REPORT_DIR}/test-execution.log"
readonly SUCCESS_FILE="${REPORT_DIR}/SUCCESS"
readonly FAILURE_FILE="${REPORT_DIR}/FAILURE"

# Test Constants
readonly MAX_DURATION=120  # seconds
readonly RETRY_INTERVAL=5
readonly RETRY_ATTEMPTS=10

# Colors for output
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Initialize test environment
initialize_test() {
    echo -e "${BLUE}🚀 Initializing Loki Log Aggregation Acceptance Test${NC}"
    echo "Test ID: OBS-ACCEPTANCE-LOKI-001"
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

# Component Health Checks
check_loki_health() {
    local start=$(date +%s)
    local test_id="COMP-HEALTH-LOKI"
    
    echo -e "\n${BLUE}[${test_id}] Checking Loki Health${NC}"
    
    # Check ready endpoint
    local ready_status
    ready_status=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "http://localhost:3100/ready" 2>/dev/null)
    if [[ "${ready_status}" != "200" ]]; then
        echo -e "${RED}✗ Loki not ready (HTTP ${ready_status})${NC}"
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Loki not ready"
        return 1
    fi
    
    echo -e "${GREEN}✓ Loki is ready${NC}"
    record_test_result "${test_id}" "PASS" $(( $(date +%s) - start )) "Loki healthy"
    return 0
}

check_promtail_health() {
    local start=$(date +%s)
    local test_id="COMP-HEALTH-PROMTAIL"
    
    echo -e "\n${BLUE}[${test_id}] Checking Promtail Health${NC}"
    
    # Check targets endpoint
    local targets_output
    targets_output=$(curl -s -m 10 "http://localhost:9080/targets" 2>/dev/null)
    if [[ -z "${targets_output}" ]]; then
        echo -e "${RED}✗ Promtail targets endpoint unreachable${NC}"
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Promtail unreachable"
        return 1
    fi
    
    # Check if Promtail is discovering targets
    local active_targets
    active_targets=$(echo "${targets_output}" | jq -r '.activeTargets | length' 2>/dev/null || echo "0")
    
    echo "  Active targets discovered: ${active_targets}"
    
    if [[ "${active_targets}" -gt 0 ]]; then
        echo -e "${GREEN}✓ Promtail is discovering containers (${active_targets} targets)${NC}"
        record_test_result "${test_id}" "PASS" $(( $(date +%s) - start )) "Promtail discovering ${active_targets} targets"
        return 0
    else
        echo -e "${YELLOW}⚠ Promtail has no active targets yet${NC}"
        record_test_result "${test_id}" "WARN" $(( $(date +%s) - start )) "No active targets"
        return 0
    fi
}

# Test log ingestion
test_log_ingestion() {
    local start=$(date +%s)
    local test_id="LOG-INGESTION"
    
    echo -e "\n${BLUE}[${test_id}] Testing Log Ingestion${NC}"
    
    # Wait for logs to be ingested
    local attempt
    local logs_found=false
    
    for attempt in $(seq 1 ${RETRY_ATTEMPTS}); do
        echo "  Attempt ${attempt}/${RETRY_ATTEMPTS}: Querying Loki for container logs..."
        
        # Query Loki for any docker logs in the last 5 minutes
        local query_result
        local start_time=$(date -u -d '5 minutes ago' +%s)000000000
        local end_time=$(date -u +%s)000000000
        
        query_result=$(curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
            --data-urlencode 'query={job="docker"}' \
            --data-urlencode "start=${start_time}" \
            --data-urlencode "end=${end_time}" \
            --data-urlencode "limit=10" 2>/dev/null)
        
        # Check if we got results
        local result_count
        result_count=$(echo "${query_result}" | jq -r '.data.result | length' 2>/dev/null || echo "0")
        
        if [[ "${result_count}" -gt 0 ]]; then
            echo -e "${GREEN}✓ Found ${result_count} log streams${NC}"
            
            # Save sample logs
            echo "${query_result}" | jq '.' > "${REPORT_DIR}/loki-query-result.json"
            
            # Extract some sample log lines
            local sample_logs
            sample_logs=$(echo "${query_result}" | jq -r '.data.result[0].values[0][1]' 2>/dev/null || echo "")
            if [[ -n "${sample_logs}" ]]; then
                echo "  Sample log: ${sample_logs}"
            fi
            
            logs_found=true
            record_test_result "${test_id}" "PASS" $(( $(date +%s) - start )) "Logs ingested successfully (${result_count} streams)"
            return 0
        fi
        
        if [[ ${attempt} -lt ${RETRY_ATTEMPTS} ]]; then
            echo "  No logs found yet, waiting ${RETRY_INTERVAL}s..."
            sleep ${RETRY_INTERVAL}
        fi
    done
    
    echo -e "${RED}✗ No logs found after ${RETRY_ATTEMPTS} attempts${NC}"
    record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "No logs found"
    return 1
}

# Test log labels
test_log_labels() {
    local start=$(date +%s)
    local test_id="LOG-LABELS"
    
    echo -e "\n${BLUE}[${test_id}] Testing Log Labels${NC}"
    
    # Query Loki for available labels
    local labels_result
    labels_result=$(curl -s "http://localhost:3100/loki/api/v1/labels" 2>/dev/null)
    
    local labels
    labels=$(echo "${labels_result}" | jq -r '.data[]' 2>/dev/null | tr '\n' ' ')
    
    if [[ -z "${labels}" ]]; then
        echo -e "${YELLOW}⚠ No labels found${NC}"
        record_test_result "${test_id}" "WARN" $(( $(date +%s) - start )) "No labels found"
        return 0
    fi
    
    echo "  Available labels: ${labels}"
    
    # Check for expected labels
    local expected_labels=("job" "container")
    local missing_labels=""
    
    for label in "${expected_labels[@]}"; do
        if echo "${labels}" | grep -q "${label}"; then
            echo -e "  ${GREEN}✓${NC} Label '${label}' present"
        else
            echo -e "  ${YELLOW}⚠${NC} Label '${label}' missing"
            missing_labels="${missing_labels} ${label}"
        fi
    done
    
    if [[ -z "${missing_labels}" ]]; then
        record_test_result "${test_id}" "PASS" $(( $(date +%s) - start )) "All expected labels present"
        return 0
    else
        record_test_result "${test_id}" "WARN" $(( $(date +%s) - start )) "Missing labels:${missing_labels}"
        return 0
    fi
}

# Test LogQL query
test_logql_query() {
    local start=$(date +%s)
    local test_id="LOGQL-QUERY"
    
    echo -e "\n${BLUE}[${test_id}] Testing LogQL Query${NC}"
    
    # Query for a specific container (grafana)
    local query_result
    local start_time=$(date -u -d '10 minutes ago' +%s)000000000
    local end_time=$(date -u +%s)000000000
    
    query_result=$(curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
        --data-urlencode 'query={container="grafana"}' \
        --data-urlencode "start=${start_time}" \
        --data-urlencode "end=${end_time}" \
        --data-urlencode "limit=5" 2>/dev/null)
    
    local result_count
    result_count=$(echo "${query_result}" | jq -r '.data.result | length' 2>/dev/null || echo "0")
    
    if [[ "${result_count}" -gt 0 ]]; then
        echo -e "${GREEN}✓ LogQL query successful (${result_count} streams)${NC}"
        record_test_result "${test_id}" "PASS" $(( $(date +%s) - start )) "LogQL query successful"
        return 0
    else
        echo -e "${YELLOW}⚠ No results for Grafana container (may not have logs yet)${NC}"
        record_test_result "${test_id}" "WARN" $(( $(date +%s) - start )) "No results for specific container"
        return 0
    fi
}

# Test log-trace correlation configuration
test_trace_correlation_config() {
    local start=$(date +%s)
    local test_id="TRACE-CORRELATION-CONFIG"
    
    echo -e "\n${BLUE}[${test_id}] Testing Trace Correlation Configuration${NC}"
    
    # Check Grafana datasource configuration for Loki
    local datasource_file="/home/runner/work/Obstackd/Obstackd/config/grafana/provisioning/datasources/datasources.yaml"
    
    if [[ ! -f "${datasource_file}" ]]; then
        echo -e "${RED}✗ Datasource configuration file not found${NC}"
        record_test_result "${test_id}" "FAIL" $(( $(date +%s) - start )) "Datasource config not found"
        return 1
    fi
    
    # Check for derivedFields configuration
    if grep -q "derivedFields" "${datasource_file}"; then
        echo -e "${GREEN}✓ Loki datasource has derivedFields configuration${NC}"
        
        # Check for traceID pattern
        if grep -q "traceID" "${datasource_file}"; then
            echo -e "${GREEN}✓ TraceID correlation configured${NC}"
            record_test_result "${test_id}" "PASS" $(( $(date +%s) - start )) "Trace correlation configured"
            return 0
        else
            echo -e "${YELLOW}⚠ TraceID pattern not found${NC}"
            record_test_result "${test_id}" "WARN" $(( $(date +%s) - start )) "TraceID pattern missing"
            return 0
        fi
    else
        echo -e "${YELLOW}⚠ derivedFields not configured${NC}"
        record_test_result "${test_id}" "WARN" $(( $(date +%s) - start )) "derivedFields not configured"
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
    
    # Create summary report
    cat > "${REPORT_DIR}/summary.md" << EOF
# Loki Log Aggregation Acceptance Test - Summary

**Test ID:** OBS-ACCEPTANCE-LOKI-001  
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
    
    # Add test results
    for test_id in "${!TEST_RESULTS[@]}"; do
        local result="${TEST_RESULTS[${test_id}]}"
        local duration="${TEST_DURATIONS[${test_id}]}"
        local symbol
        case "${result}" in
            "PASS") symbol="✓" ;;
            "FAIL") symbol="✗" ;;
            "WARN") symbol="⚠" ;;
        esac
        
        # Get message from CSV
        local message
        message=$(grep "^TEST: ${test_id}" "${REPORT_DIR}/test-results.csv" | cut -d'|' -f4 | sed 's/^ MESSAGE: //')
        
        echo "| ${test_id} | ${symbol} ${result} | ${duration}s | ${message} |" >> "${REPORT_DIR}/summary.md"
    done
    
    # Add conclusion
    if [[ ${failed} -eq 0 ]]; then
        cat >> "${REPORT_DIR}/summary.md" << EOF

## Conclusion

✅ **ACCEPTANCE TEST PASSED**

All critical tests passed. Loki log aggregation is operational.

EOF
        touch "${SUCCESS_FILE}"
        return 0
    else
        cat >> "${REPORT_DIR}/summary.md" << EOF

## Conclusion

❌ **ACCEPTANCE TEST FAILED**

${failed} test(s) failed. Review the test logs for details.

EOF
        touch "${FAILURE_FILE}"
        return 1
    fi
}

# Main test execution
main() {
    initialize_test
    
    local overall_result=0
    
    # Run health checks
    check_loki_health || overall_result=1
    check_promtail_health || overall_result=1
    
    # Run functional tests
    test_log_ingestion || overall_result=1
    test_log_labels || overall_result=1
    test_logql_query || overall_result=1
    test_trace_correlation_config || overall_result=1
    
    # Generate report
    echo ""
    echo "========================================"
    generate_summary_report || overall_result=1
    echo "========================================"
    
    # Display summary
    cat "${REPORT_DIR}/summary.md"
    
    echo ""
    echo "Report saved to: ${REPORT_DIR}/summary.md"
    echo "Full logs: ${LOG_FILE}"
    
    exit ${overall_result}
}

# Run the tests
main "$@"
