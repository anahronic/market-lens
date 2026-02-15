#!/usr/bin/env python3
"""Determinism check: run each vector twice, compare byte-for-byte.

This script NEVER modifies any file. It is safe for CI.
"""
import json
import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.src.cli import run_engine

VECTORS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "engine", "tests", "test_vectors",
)
CASES = [
    "uniform_market", "burst_attack", "domain_dominance",
    "cluster_injection", "cold_start", "zero_mad",
]

all_pass = True
for name in CASES:
    with open(os.path.join(VECTORS_DIR, f"{name}_input.json")) as f:
        data = json.load(f)
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
