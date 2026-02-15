#!/bin/bash
# Initialize git repo for Market Lens
set -e

cd /home/anahronic/market-lens

# Init git
git init

# Configure git
git config user.email "anahronic@users.noreply.github.com"
git config user.name "anahronic"

# Generate artifact registry
python3 generate_artifact_registry.py

# Remove temp files
rm -f show_expected.py dump_expected.py _output_dump.txt

# Stage all files
git add -A

# Show status
git status

echo "=== Git init complete ==="
