#!/usr/bin/env bash
set -euo pipefail

WAIT_TIMEOUT="${WAIT_TIMEOUT:-120}"
WAIT_INTERVAL="${WAIT_INTERVAL:-2}"
CURL_CONNECT_TIMEOUT="${CURL_CONNECT_TIMEOUT:-5}"
CURL_MAX_TIME="${CURL_MAX_TIME:-10}"
WAIT_CONTEXT="${WAIT_CONTEXT:-host}"

readonly WAIT_TIMEOUT WAIT_INTERVAL CURL_CONNECT_TIMEOUT CURL_MAX_TIME WAIT_CONTEXT

if [[ "${WAIT_CONTEXT}" == "compose" ]]; then
  SERVICES=(
    "Prometheus|http://prometheus:9090/-/healthy"
    "Grafana|http://grafana:3000/api/health"
    "Loki|http://loki:3100/ready"
    "Tempo|http://tempo:3200/ready"
    "Alloy|http://alloy:12345/-/ready"
    "OTel Collector|http://otel-collector:8888/metrics"
    "Alertmanager|http://alertmanager:9093/-/healthy"
  )
else
  SERVICES=(
    "Prometheus|http://localhost:9090/-/healthy"
    "Grafana|http://localhost:3000/api/health"
    "Loki|http://localhost:3100/ready"
    "Tempo|http://localhost:3200/ready"
    "Alloy|http://localhost:12345/-/ready"
    "OTel Collector|http://localhost:8888/metrics"
    "Alertmanager|http://localhost:9093/-/healthy"
  )
fi
readonly SERVICES

declare -A SERVICE_READY=()

is_service_ready() {
  local url="$1"
  curl -fsS --connect-timeout "${CURL_CONNECT_TIMEOUT}" --max-time "${CURL_MAX_TIME}" "${url}" >/dev/null 2>&1
}

start_time=$(date +%s)
readonly start_time

echo "Waiting for core observability services (timeout: ${WAIT_TIMEOUT}s)"

while true; do
  now=$(date +%s)
  elapsed=$((now - start_time))

  all_ready=true

  for service in "${SERVICES[@]}"; do
    name="${service%%|*}"
    url="${service#*|}"

    if [[ "${SERVICE_READY[$name]:-false}" == "true" ]]; then
      continue
    fi

    if is_service_ready "${url}"; then
      SERVICE_READY["$name"]=true
      echo "✅ ${name} healthy (${elapsed}s)"
    else
      all_ready=false
    fi
  done

  if [[ "${all_ready}" == "true" ]]; then
    echo "========================================"
    echo "✅ All core services are healthy (${elapsed}s)"
    echo "========================================"
    exit 0
  fi

  if (( elapsed >= WAIT_TIMEOUT )); then
    echo "========================================"
    for service in "${SERVICES[@]}"; do
      name="${service%%|*}"
      if [[ "${SERVICE_READY[$name]:-false}" != "true" ]]; then
        echo "❌ ${name} not healthy (${elapsed}s)"
      fi
    done
    echo "❌ Timeout waiting for services after ${WAIT_TIMEOUT}s"
    echo "========================================"
    exit 1
  fi

  sleep "${WAIT_INTERVAL}"
done
