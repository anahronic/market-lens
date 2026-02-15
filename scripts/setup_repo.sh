#!/bin/bash
# Complete setup script for Market Lens repository
set -e

cd /home/anahronic/market-lens

# Remove temp files
rm -f show_expected.py dump_expected.py _output_dump.txt init_git.sh

# Generate artifact registry
python3 generate_artifact_registry.py

# Initialize git if not already done
if [ ! -d .git ]; then
    git init
    git config user.email "anahronic@users.noreply.github.com"
    git config user.name "anahronic"
fi

# Remove this script itself
rm -f setup_repo.sh

# Stage all files
git add -A

# Create initial commit
git commit -m "feat: DKP-PTL-REG Reference Engine v0.6 — initial deterministic implementation

Implements the canonical reference engine for DKP-PTL-REG v0.6:

- CONSTANTS-001: Dual-profile constants (BASE/HARDENED)
- REFERENCE-001: Input boundary normalization (NFC, PSL, JCS, SHA256)
- DATA-001: 18-step deterministic pipeline
- THREAT-001: Integrity status computation
- GOV-001: Version metadata and artifact registry

Includes:
- 6 mandatory test vectors (uniform, burst, domain dominance,
  cluster injection, cold start, zero MAD)
- 41 pytest unit tests
- GitHub Actions CI for Python 3.10/3.11/3.12
- Bundled PSL snapshot (PSL-2026-01-01.dat)
- Deterministic JSON canonicalization (JCS)

All outputs are bit-stable and reproducible.
protocol_version=0.6.0, constants_version=0.6.0"

git branch -M main

echo "=== Repository setup complete ==="
echo "Next: Create remote and push"
echo "  gh repo create market-lens --public"
echo "  git remote add origin https://github.com/anahronic/market-lens.git"
echo "  git push -u origin main"
