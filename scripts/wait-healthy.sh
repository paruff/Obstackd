#!/usr/bin/env bash
set -euo pipefail

TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-120}"
SLEEP_SECONDS="${SLEEP_SECONDS:-2}"
CURL_CONNECT_TIMEOUT="${CURL_CONNECT_TIMEOUT:-5}"
CURL_MAX_TIME="${CURL_MAX_TIME:-10}"

wait_for_endpoint() {
  local name="$1"
  local url="$2"
  local deadline
  deadline=$((SECONDS + TIMEOUT_SECONDS))

  until curl -fsS --connect-timeout "${CURL_CONNECT_TIMEOUT}" --max-time "${CURL_MAX_TIME}" "$url" > /dev/null; do
    if (( SECONDS >= deadline )); then
      echo "Timed out waiting for ${name} at ${url}"
      return 1
    fi
    sleep "$SLEEP_SECONDS"
  done

  echo "Healthy: ${name}"
}

wait_for_endpoint "Prometheus" "http://localhost:9090/-/ready"
wait_for_endpoint "Grafana" "http://localhost:3000/api/health"
wait_for_endpoint "Tempo" "http://localhost:3200/ready"
wait_for_endpoint "Loki" "http://localhost:3100/ready"
wait_for_endpoint "OTel Collector" "http://localhost:8888/metrics"
wait_for_endpoint "Alloy" "http://localhost:12345/metrics"
