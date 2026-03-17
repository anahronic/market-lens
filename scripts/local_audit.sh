#!/bin/bash
# DKP-PTL-REG v0.6 Local Audit Helper
#
# Runs all local conformance checks and generates audit artifacts.
#
# Usage:
#   ./scripts/local_audit.sh [--output-dir DIR]
#
# Outputs:
#   - release_audit/release_conformance_report.json
#   - release_audit/version_inventory.json
#   - release_audit/local_fingerprint.json

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="${1:-$REPO_ROOT/release_audit}"

echo "=============================================="
echo "DKP-PTL-REG v0.6 Local Audit"
echo "=============================================="
echo "Repository: $REPO_ROOT"
echo "Output: $OUTPUT_DIR"
echo ""

mkdir -p "$OUTPUT_DIR"

# 1. Release conformance check
echo "[1/5] Running release conformance check..."
python -m scripts.release_audit -v -o "$OUTPUT_DIR/release_conformance_report.json"
echo ""

# 2. Version inventory
echo "[2/5] Generating version inventory..."
python "$SCRIPT_DIR/generate_version_inventory.py" -o "$OUTPUT_DIR/version_inventory.json"
echo ""

# 3. PSL snapshot verification
echo "[3/5] Verifying PSL snapshot..."
python "$SCRIPT_DIR/check_psl_snapshot.py" -v
echo ""

# 4. Runtime fingerprint
echo "[4/5] Collecting runtime fingerprint..."
python "$SCRIPT_DIR/collect_runtime_fingerprint.py" -o "$OUTPUT_DIR/local_fingerprint.json"
echo ""

# 5. Regenerate artifact registry
echo "[5/5] Regenerating artifact registry..."
python "$SCRIPT_DIR/generate_artifact_registry.py"
echo ""

echo "=============================================="
echo "Local Audit Complete"
echo "=============================================="
echo "Artifacts generated in: $OUTPUT_DIR"
ls -la "$OUTPUT_DIR"
echo ""

# Check conformance status
if grep -q '"overall_status": "PASS"' "$OUTPUT_DIR/release_conformance_report.json"; then
    echo "STATUS: PASS - Local release conformance verified"
    exit 0
else
    echo "STATUS: FAIL - Conformance issues detected"
    exit 1
fi
