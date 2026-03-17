#!/usr/bin/env python3
"""Determinism check: run each vector twice, compare byte-for-byte.

This script NEVER modifies any file. It is safe for CI.
"""
import json
import sys
from pathlib import Path

_scripts_dir = str(Path(__file__).resolve().parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)
from path_safety import safe_resolve

# Derive repo root from this script's location
REPO_ROOT = Path(__file__).resolve().parent.parent

# Add repo root to sys.path so engine is importable
_repo_str = str(REPO_ROOT)
if _repo_str not in sys.path:
    sys.path.insert(0, _repo_str)
from engine.src.cli import run_engine

VECTORS_DIR = safe_resolve(REPO_ROOT, "engine/tests/test_vectors")

CASES = [
    "uniform_market", "burst_attack", "domain_dominance",
    "cluster_injection", "cold_start", "zero_mad",
]

all_pass = True
for name in CASES:
    input_path = safe_resolve(VECTORS_DIR, f"{name}_input.json")
    data = json.loads(input_path.read_text())
    o1 = json.dumps(run_engine(data, "BASE", 1700000000), indent=2, ensure_ascii=False)
    o2 = json.dumps(run_engine(data, "BASE", 1700000000), indent=2, ensure_ascii=False)
    if o1 == o2:
        print(f"  {name}: PASS (byte-for-byte)")
    else:
        print(f"  {name}: FAIL")
        all_pass = False

print()
if all_pass:
    print("DETERMINISM OVERALL: PASS")
else:
    print("DETERMINISM OVERALL: FAIL")
    sys.exit(1)
