#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${1:-dikenocracy.com}"

echo "HEAD /api/health"
curl -I "https://${DOMAIN}/api/health" || true
echo

echo "GET /api/health"
curl -s "https://${DOMAIN}/api/health" || true
echo
echo

echo "GET /api/version"
curl -s "https://${DOMAIN}/api/version" || true
echo
