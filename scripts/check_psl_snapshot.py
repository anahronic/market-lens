#!/usr/bin/env python3
"""
Verify PSL snapshot integrity against artifact registry.

This script checks that the PSL-2026-01-01.dat file matches
the SHA256 hash recorded in the artifact registry.

Usage:
    python scripts/check_psl_snapshot.py [--verbose]

Exit codes:
    0  - PSL snapshot hash matches registry
    1  - Hash mismatch or file missing
    2  - Registry file missing
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256_file(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Verify PSL snapshot integrity")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    registry_path = root / "artifacts" / "Artifact_Registry_v0.6.json"
    
    # Check registry exists
    if not registry_path.exists():
        print(f"ERROR: Artifact registry not found: {registry_path}")
        sys.exit(2)
    
    # Load registry
    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)
    
    # Get expected PSL info
    psl_info = registry.get("psl_snapshot", {})
    expected_filename = psl_info.get("filename", "PSL-2026-01-01.dat")
    expected_hash = psl_info.get("sha256", "")
    
    if not expected_hash:
        print("ERROR: No PSL hash found in artifact registry")
        sys.exit(2)
    
    # Check PSL file exists
    psl_path = root / "engine" / "src" / "psl_snapshot" / expected_filename
    if not psl_path.exists():
        print(f"ERROR: PSL snapshot not found: {psl_path}")
        sys.exit(1)
    
    # Compute actual hash
    actual_hash = sha256_file(psl_path)
    
    if args.verbose:
        print(f"PSL file: {psl_path}")
        print(f"Expected SHA256: {expected_hash}")
        print(f"Actual SHA256:   {actual_hash}")
    
    # Compare
    if actual_hash == expected_hash:
        print(f"OK: PSL snapshot {expected_filename} hash verified")
        sys.exit(0)
    else:
        print(f"FAIL: PSL snapshot hash mismatch!")
        print(f"  Expected: {expected_hash}")
        print(f"  Actual:   {actual_hash}")
        sys.exit(1)


if __name__ == "__main__":
    main()
