"""
DKP-PTL-REG v0.6 — Deterministic Test Runner

Generates expected outputs by running the engine, then verifies
byte-for-byte reproducibility on subsequent runs.

Test Vectors:
1. Uniform market
2. Burst attack
3. Domain dominance
4. Similarity cluster injection
5. Cold start
6. Zero MAD
"""

import json
import os
import sys
from collections import OrderedDict
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from engine.src.cli import run_engine

VECTORS_DIR = Path(__file__).parent / "test_vectors"
CURRENT_TIME_UTC = 1700000000  # Fixed deterministic time
PROFILE = "BASE"


TEST_CASES = [
    {
        "name": "uniform_market",
        "input_file": "uniform_market_input.json",
        "expected_file": "uniform_market_expected.json",
    },
    {
        "name": "burst_attack",
        "input_file": "burst_attack_input.json",
        "expected_file": "burst_attack_expected.json",
    },
    {
        "name": "domain_dominance",
        "input_file": "domain_dominance_input.json",
        "expected_file": "domain_dominance_expected.json",
    },
    {
        "name": "cluster_injection",
        "input_file": "cluster_injection_input.json",
        "expected_file": "cluster_injection_expected.json",
    },
    {
        "name": "cold_start",
        "input_file": "cold_start_input.json",
        "expected_file": "cold_start_expected.json",
    },
    {
        "name": "zero_mad",
        "input_file": "zero_mad_input.json",
        "expected_file": "zero_mad_expected.json",
    },
]


def run_test_vector(test_case: dict, generate: bool = False) -> bool:
    """
    Run a single test vector.

    If generate=True, creates the expected output file.
    Otherwise, compares engine output with expected output byte-for-byte.
    """
    input_path = VECTORS_DIR / test_case["input_file"]
    expected_path = VECTORS_DIR / test_case["expected_file"]

    with open(input_path, "r", encoding="utf-8") as f:
        input_data = json.load(f)

    # Run engine
    output = run_engine(input_data, PROFILE, CURRENT_TIME_UTC)

    # Serialize deterministically
    output_json = json.dumps(output, indent=2, ensure_ascii=False)

    if generate:
        with open(expected_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(output_json)
            f.write("\n")
        print(f"  [GENERATED] {test_case['name']}: {expected_path.name}")
        return True

    # Compare byte-for-byte
    if not expected_path.exists():
        print(f"  [MISSING] {test_case['name']}: expected file not found. Run with --generate first.")
        return False

    with open(expected_path, "r", encoding="utf-8") as f:
        expected_json = f.read().rstrip("\n")

    if output_json == expected_json:
        print(f"  [PASS] {test_case['name']}")
        return True
    else:
        print(f"  [FAIL] {test_case['name']}")
        print(f"    Expected: {expected_json[:200]}...")
        print(f"    Got:      {output_json[:200]}...")
        return False


def main():
    generate = "--generate" in sys.argv

    if generate:
        print("=== Generating Expected Test Vectors ===")
    else:
        print("=== Running Deterministic Test Vectors ===")
    print(f"Profile: {PROFILE}")
    print(f"current_time_utc: {CURRENT_TIME_UTC}")
    print()

    passed = 0
    failed = 0

    for tc in TEST_CASES:
        try:
            if run_test_vector(tc, generate=generate):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  [ERROR] {tc['name']}: {e}")
            failed += 1

    print()
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")

    if failed > 0 and not generate:
        sys.exit(1)


if __name__ == "__main__":
    main()
