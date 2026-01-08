#!/bin/bash
# CI/CD E2E Test Runner
# Manages test execution in different scenarios

set -euo pipefail

# Configuration
readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly TEST_DIR="${PROJECT_ROOT}/tests/acceptance/observability-pipeline"
readonly COMPOSE_FILE="${PROJECT_ROOT}/compose.yaml"

# Colors
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Function to check if services are running
check_services_running() {
    echo -e "${BLUE}Checking if services are already running...${NC}"
    
    local all_running=true
    
    if ! docker compose ps otel-collector 2>/dev/null | grep -q "Up"; then
        echo "OTel Collector is not running"
        all_running=false
    fi
    
    if ! docker compose ps prometheus 2>/dev/null | grep -q "Up"; then
        echo "Prometheus is not running"
        all_running=false
    fi
    
    if ! docker compose ps grafana 2>/dev/null | grep -q "Up"; then
        echo "Grafana is not running"
        all_running=false
    fi
    
    if [[ "${all_running}" == "true" ]]; then
        echo -e "${GREEN}✅ All services are running${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Some services are not running${NC}"
        return 1
    fi
}

# Function to start monitoring stack
start_monitoring_stack() {
    echo -e "${BLUE}Starting monitoring stack...${NC}"
    
    # Create data directories if they don't exist
    mkdir -p "${PROJECT_ROOT}/data/prometheus" "${PROJECT_ROOT}/data/grafana"
    chmod -R 777 "${PROJECT_ROOT}/data/" 2>/dev/null || true
    
    # Start services
    docker compose --profile core up -d
    
    # Wait for services to be ready
    echo -e "${BLUE}Waiting for services to be ready...${NC}"
    local max_wait=60
    local elapsed=0
    local interval=5
    
    while [ $elapsed -lt $max_wait ]; do
        if check_services_running >/dev/null 2>&1; then
            break
        fi
        sleep $interval
        elapsed=$((elapsed + interval))
        echo "  Waiting... ($elapsed/$max_wait seconds)"
    done
    
    # Additional wait for services to stabilize
    echo "Allowing services to stabilize..."
    sleep 30
    
    # Verify services are running
    if ! docker compose ps | grep -q "Up"; then
        echo -e "${RED}❌ Services failed to start${NC}"
        docker compose logs --tail=50
        return 1
    fi
    
    echo -e "${GREEN}✅ Monitoring stack started successfully${NC}"
    return 0
}

# Function to stop monitoring stack
stop_monitoring_stack() {
    if [[ "${CLEANUP:-false}" == "true" ]]; then
        echo -e "${BLUE}Cleaning up monitoring stack...${NC}"
        docker compose --profile core down -v
        echo -e "${GREEN}✅ Stack cleaned up${NC}"
    else
        echo -e "${YELLOW}Skipping cleanup (use --cleanup to clean up)${NC}"
    fi
}

# Function to run specific test scenario
run_test_scenario() {
    local scenario=$1
    
    case "${scenario}" in
        "full-pipeline")
            echo -e "${BLUE}Running full pipeline acceptance test...${NC}"
            "${TEST_DIR}/test-otel-pipeline.sh"
            ;;
        "quick-check")
            echo -e "${BLUE}Running quick health check...${NC}"
            # Quick check: just verify endpoints are reachable
            curl -sf http://localhost:8889/metrics | grep -q "otelcol_process_uptime" && \
            curl -sf http://localhost:9090/-/healthy >/dev/null && \
            curl -sf http://localhost:3000/api/health >/dev/null
            ;;
        *)
            echo -e "${RED}Unknown scenario: ${scenario}${NC}"
            return 1
            ;;
    esac
}

# Function to generate documentation
generate_documentation() {
    local report_dir=$(find "${TEST_DIR}/reports" -type d -name "2*" 2>/dev/null | sort -r | head -1)
    
    if [[ -n "${report_dir}" ]] && [[ -f "${report_dir}/summary.md" ]]; then
        echo -e "${BLUE}Test report available at: ${report_dir}/summary.md${NC}"
    fi
}

# Main execution
main() {
    local scenario="${SCENARIO:-full-pipeline}"
    local start_services="${START_SERVICES:-auto}"
    
    echo "========================================="
    echo "Observability Pipeline Acceptance Test"
    echo "========================================="
    echo "Scenario: ${scenario}"
    echo ""
    
    # Determine if we need to start services
    if [[ "${start_services}" == "auto" ]]; then
        if ! check_services_running; then
            start_monitoring_stack || exit 1
        fi
    elif [[ "${start_services}" == "yes" ]]; then
        start_monitoring_stack || exit 1
    fi
    
    # Run the specified test scenario
    if run_test_scenario "${scenario}"; then
        echo ""
        echo -e "${GREEN}=========================================${NC}"
        echo -e "${GREEN}✅ Test scenario '${scenario}' PASSED${NC}"
        echo -e "${GREEN}=========================================${NC}"
        
        # Generate documentation
        generate_documentation
        
        # Clean up if requested
        stop_monitoring_stack
        
        exit 0
    else
        echo ""
        echo -e "${RED}=========================================${NC}"
        echo -e "${RED}❌ Test scenario '${scenario}' FAILED${NC}"
        echo -e "${RED}=========================================${NC}"
        
        # Capture failure details
        echo ""
        echo -e "${YELLOW}=== Failure Diagnostics ===${NC}"
        docker compose logs --tail=50 otel-collector prometheus grafana 2>/dev/null || true
        
        # Generate documentation even on failure
        generate_documentation
        
        # Clean up if requested
        stop_monitoring_stack
        
        exit 1
    fi
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --scenario)
            SCENARIO="$2"
            shift 2
            ;;
        --start-services)
            START_SERVICES="yes"
            shift
            ;;
        --no-start-services)
            START_SERVICES="no"
            shift
            ;;
        --cleanup)
            CLEANUP=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --scenario SCENARIO     Test scenario to run (default: full-pipeline)"
            echo "                          Options: full-pipeline, quick-check"
            echo "  --start-services        Force start services before test"
            echo "  --no-start-services     Don't start services (assume already running)"
            echo "  --cleanup               Stop and clean up services after test"
            echo "  --help                  Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Run with auto service detection"
            echo "  $0 --scenario quick-check             # Run quick health check"
            echo "  $0 --cleanup                          # Run test and clean up after"
            echo "  $0 --start-services --cleanup         # Start, test, and clean up"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run main function
main
