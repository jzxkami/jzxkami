#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${1:-$(pwd)}"
cd "${APP_DIR}"

if [[ ! -f "requirements.txt" ]]; then
  echo "requirements.txt not found in ${APP_DIR}" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found" >&2
  exit 1
fi

python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

mkdir -p data outputs/charts

echo "Setup done. Next: edit .env, then configure systemd/nginx." 
