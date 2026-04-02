#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_DIR="${1:-/opt/finance-agent}"
DOMAIN="${2:-_}"
RUN_USER="${3:-$USER}"
RUN_GROUP="${4:-$RUN_USER}"

OUT_DIR="${ROOT_DIR}/deploy/generated"
mkdir -p "${OUT_DIR}"

sed \
  -e "s#__APP_DIR__#${APP_DIR}#g" \
  -e "s#__RUN_USER__#${RUN_USER}#g" \
  -e "s#__RUN_GROUP__#${RUN_GROUP}#g" \
  "${ROOT_DIR}/deploy/systemd/finance-agent.service.template" \
  > "${OUT_DIR}/finance-agent.service"

sed \
  -e "s#__DOMAIN__#${DOMAIN}#g" \
  "${ROOT_DIR}/deploy/nginx/finance-agent.conf.template" \
  > "${OUT_DIR}/finance-agent.nginx.conf"

echo "Generated files:"
echo "- ${OUT_DIR}/finance-agent.service"
echo "- ${OUT_DIR}/finance-agent.nginx.conf"
