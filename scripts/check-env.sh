#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

if [ -f "${ENV_FILE}" ]; then
  set -a
  # shellcheck disable=SC1090
  . "${ENV_FILE}"
  set +a
fi

export GRAFANA_ADMIN_PASSWORD="${GRAFANA_ADMIN_PASSWORD:-}"

if [ -z "${GRAFANA_ADMIN_PASSWORD}" ] || [ "${GRAFANA_ADMIN_PASSWORD}" = "admin" ] || [ "${GRAFANA_ADMIN_PASSWORD}" = "changeme" ] || [ "${GRAFANA_ADMIN_PASSWORD}" = "REPLACE_ME_set_a_real_password_here" ]; then
  cat <<'EOF'
❌ Refusing to start: GRAFANA_ADMIN_PASSWORD is missing or insecure.
Set a non-default Grafana admin password before starting the stack.

Remediation:
  cp .env.example .env
  $EDITOR .env
EOF
  exit 1
fi

echo "✅ Environment check passed: GRAFANA_ADMIN_PASSWORD is set."
