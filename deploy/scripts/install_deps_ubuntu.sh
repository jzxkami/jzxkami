#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y \
  git \
  python3 \
  python3-venv \
  python3-pip \
  nginx \
  certbot \
  python3-certbot-nginx

echo "Installed base dependencies."
