#!/usr/bin/env bash
# ============================================================================
# Market Lens — E2E Pipeline Test Runner
#
# Usage (on server):
#   cd ~/projects/market-lens
#   bash scripts/run_e2e_pipeline_test.sh
#
# Prerequisites:
#   - market-lens-api.service is active
#   - market-lens-worker.service is active
#   - Virtual environment with httpx installed
#   - MARKET_LENS_QUEUE_DIR set or default ./var/queue exists
#
# Exit codes:
#   0 - Test passed
#   1 - Test failed
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "============================================================"
echo "Market Lens E2E Pipeline Test"
echo "============================================================"
echo

# Check prerequisites
echo "[Pre-check] Verifying prerequisites..."

if ! systemctl is-active --quiet market-lens-api; then
    echo "ERROR: market-lens-api.service is not active"
    exit 1
fi
echo "  market-lens-api.service: active"

if ! systemctl is-active --quiet market-lens-worker; then
    echo "ERROR: market-lens-worker.service is not active"
    exit 1
fi
echo "  market-lens-worker.service: active"

# Determine queue directory
QUEUE_DIR="${MARKET_LENS_QUEUE_DIR:-./var/queue}"
echo "  Queue directory: $QUEUE_DIR"
echo

# Show system info
echo "[Info] System information:"
echo "  Hostname: $(hostname)"
echo "  Date UTC: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "  Git commit: $(git rev-parse --short HEAD)"
echo

# Activate virtual environment
if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
    echo "  Virtual environment: activated"
else
    echo "WARNING: venv/bin/activate not found, using system Python"
fi
echo

# Run Python e2e test
echo "[Test] Running e2e pipeline test..."
echo

python3 scripts/e2e_pipeline_check.py \
    --queue-dir "$QUEUE_DIR" \
    --endpoint "http://127.0.0.1:8000" \
    --timeout 30

EXIT_CODE=$?

echo
if [[ $EXIT_CODE -eq 0 ]]; then
    echo "============================================================"
    echo "RESULT: PASS"
    echo "============================================================"
else
    echo "============================================================"
    echo "RESULT: FAIL"
    echo "============================================================"
fi

exit $EXIT_CODE
