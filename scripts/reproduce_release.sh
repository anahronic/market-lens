#!/bin/bash
# ==============================================================================
# PHASE 10: REPRODUCIBILITY VERIFICATION SCRIPT
# ==============================================================================
# Document ID: ML-REPRODUCE-001
# Version: 1.0
# Purpose: Verify deterministic reproducibility of PIL extraction release v0.6.0
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

echo "============================================================"
echo "PHASE 10: REPRODUCIBILITY VERIFICATION"
echo "Market Lens PIL Extraction Release v0.6.0"
echo "============================================================"
echo ""

# ------------------------------------------------------------------------------
# STEP 1: Environment Check
# ------------------------------------------------------------------------------
echo "[STEP 1] Environment Check"
echo "------------------------------------------------------------"
echo "Python version: $(python3 --version)"
echo "Working directory: $REPO_ROOT"
echo ""

# ------------------------------------------------------------------------------
# STEP 2: Dependency Installation
# ------------------------------------------------------------------------------
echo "[STEP 2] Dependency Check"
echo "------------------------------------------------------------"
python3 -c "import pytest; print(f'pytest: {pytest.__version__}')" 2>/dev/null || pip install pytest
python3 -c "import bs4; print(f'beautifulsoup4: {bs4.__version__}')" 2>/dev/null || pip install beautifulsoup4
python3 -c "import lxml; print(f'lxml: {lxml.__version__}')" 2>/dev/null || pip install lxml
echo ""

# ------------------------------------------------------------------------------
# STEP 3: Artifact Hash Verification
# ------------------------------------------------------------------------------
echo "[STEP 3] Artifact Hash Verification"
echo "------------------------------------------------------------"
PYTHONPATH="$REPO_ROOT" pytest tests/pil_extraction/test_artifacts.py -v --tb=short
echo ""

# ------------------------------------------------------------------------------
# STEP 4: PIL Test Vectors (20 official)
# ------------------------------------------------------------------------------
echo "[STEP 4] PIL Test Vectors (20 official)"
echo "------------------------------------------------------------"
PYTHONPATH="$REPO_ROOT" python3 tests/pil_extraction/test_runner_pil.py
echo ""

# ------------------------------------------------------------------------------
# STEP 5: Full Test Suite
# ------------------------------------------------------------------------------
echo "[STEP 5] Full Test Suite"
echo "------------------------------------------------------------"
PYTHONPATH="$REPO_ROOT" pytest tests/pil_extraction -v --tb=short
echo ""

# ------------------------------------------------------------------------------
# STEP 6: Determinism Verification (3 runs)
# ------------------------------------------------------------------------------
echo "[STEP 6] Determinism Verification"
echo "------------------------------------------------------------"
python3 << 'PYEOF'
import json
import hashlib
from pathlib import Path

vectors_file = Path("tests/pil_extraction/vectors/pil_vectors_v0_1.json")
vectors = json.loads(vectors_file.read_text())

from client.pil_extraction import extract_pil_from_html

determinism_pass = True
for vector in vectors:
    html = vector["input"]["html"]
    url = vector["input"].get("url", "")
    utc_year = vector["input"].get("utc_year", 2026)
    
    outputs = [
        hashlib.sha256(json.dumps(extract_pil_from_html(html, url, utc_year), sort_keys=True).encode()).hexdigest()[:16]
        for _ in range(3)
    ]
    
    if len(set(outputs)) != 1:
        determinism_pass = False
        print(f"FAIL: {vector['test_id']}")

if determinism_pass:
    print("DETERMINISM: PASS (all 20 vectors, 3 runs each)")
else:
    print("DETERMINISM: FAIL")
    exit(1)
PYEOF
echo ""

# ------------------------------------------------------------------------------
# STEP 7: Vector Count Lock Verification
# ------------------------------------------------------------------------------
echo "[STEP 7] Vector Count Lock"
echo "------------------------------------------------------------"
VECTOR_COUNT=$(python3 -c "import json; print(len(json.load(open('tests/pil_extraction/vectors/pil_vectors_v0_1.json'))))")
echo "Vector count: $VECTOR_COUNT"
if [ "$VECTOR_COUNT" -ne 20 ]; then
    echo "ERROR: Expected exactly 20 test vectors, found $VECTOR_COUNT"
    exit 1
fi
echo "PASS: 20/20 vectors present"
echo ""

# ------------------------------------------------------------------------------
# FINAL REPORT
# ------------------------------------------------------------------------------
echo "============================================================"
echo "REPRODUCIBILITY VERIFICATION COMPLETE"
echo "============================================================"
echo ""
echo "Registry Version: 0.6.0"
echo "PIL Extraction Spec: DKP-PTL-REG-PIL-EXTRACTION-001 v0.3"
echo "Test Vectors: DKP-PTL-REG-PIL-TEST-VECTORS-001 v0.1"
echo ""
echo "STATUS: PASS"
echo "============================================================"
