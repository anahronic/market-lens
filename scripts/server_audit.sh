#!/bin/bash
# DKP-PTL-REG v0.6 Server Audit Helper
#
# Collects runtime fingerprint from a remote server deployment.
# Requires SSH access to the server.
#
# Usage:
#   ./scripts/server_audit.sh [SSH_TARGET] [REMOTE_PATH]
#
# Example:
#   ./scripts/server_audit.sh root@dikenocracy.com /opt/market-lens
#
# Outputs:
#   - release_audit/server_fingerprint.json

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$REPO_ROOT/release_audit"

SSH_TARGET="${1:-root@dikenocracy.com}"
REMOTE_PATH="${2:-/opt/market-lens}"

echo "=============================================="
echo "DKP-PTL-REG v0.6 Server Audit"
echo "=============================================="
echo "SSH Target: $SSH_TARGET"
echo "Remote Path: $REMOTE_PATH"
echo ""

mkdir -p "$OUTPUT_DIR"

# Check SSH connectivity
echo "[1/4] Testing SSH connectivity..."
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$SSH_TARGET" "echo 'SSH OK'" 2>/dev/null; then
    echo "ERROR: Cannot connect to $SSH_TARGET"
    echo "Make sure SSH is configured and the server is reachable."
    exit 1
fi
echo "SSH connection verified."
echo ""

# Copy fingerprint collector to server
echo "[2/4] Copying fingerprint collector to server..."
scp -q "$SCRIPT_DIR/collect_runtime_fingerprint.py" "$SSH_TARGET:/tmp/"
echo "Collector script copied."
echo ""

# Run fingerprint collection on server
echo "[3/4] Collecting server fingerprint..."
ssh "$SSH_TARGET" "cd $REMOTE_PATH && python3 /tmp/collect_runtime_fingerprint.py -o /tmp/server_fingerprint.json --api-url http://localhost:8000"
echo ""

# Download fingerprint
echo "[4/4] Downloading server fingerprint..."
scp -q "$SSH_TARGET:/tmp/server_fingerprint.json" "$OUTPUT_DIR/server_fingerprint.json"
echo "Downloaded to: $OUTPUT_DIR/server_fingerprint.json"
echo ""

# Clean up remote temp files
ssh "$SSH_TARGET" "rm -f /tmp/collect_runtime_fingerprint.py /tmp/server_fingerprint.json" 2>/dev/null || true

echo "=============================================="
echo "Server Audit Complete"
echo "=============================================="

# If local fingerprint exists, run comparison
if [ -f "$OUTPUT_DIR/local_fingerprint.json" ]; then
    echo ""
    echo "Running fingerprint comparison..."
    python "$SCRIPT_DIR/compare_fingerprints.py" \
        "$OUTPUT_DIR/local_fingerprint.json" \
        "$OUTPUT_DIR/server_fingerprint.json"
else
    echo ""
    echo "Note: Run local_audit.sh first to enable fingerprint comparison."
fi
