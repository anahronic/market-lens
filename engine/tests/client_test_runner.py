"""DKP-PTL-REG v0.6 — Deterministic client test runner."""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from engine.src.client_interpretation import interpret_client_signal

VECTORS_PATH = Path(__file__).parent / "client_test_vectors.json"


def _matches_expected(actual: dict, expected: dict) -> bool:
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if isinstance(expected_value, float):
            if not isinstance(actual_value, (int, float)):
                return False
            if not math.isclose(float(actual_value), expected_value, rel_tol=0.0, abs_tol=1e-12):
                return False
        else:
            if actual_value != expected_value:
                return False
    return True


def run_client_test_case(case: dict) -> bool:
    name = case["name"]
    test_input = case["input"]
    expected = case["expected"]

    actual = interpret_client_signal(test_input)

    if _matches_expected(actual, expected):
        print(f"  [PASS] {name}")
        return True

    print(f"  [FAIL] {name}")
    print(f"    Expected: {expected}")
    print(f"    Got:      {actual}")
    return False


def run_all_client_tests() -> bool:
    with open(VECTORS_PATH, "r", encoding="utf-8") as f:
        vectors = json.load(f)

    print("=== Running Deterministic Client Test Vectors ===")
    print(f"Vectors file: {VECTORS_PATH}")
    print()

    passed = 0
    failed = 0

    for case in vectors:
        try:
            if run_client_test_case(case):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  [ERROR] {case.get('name', 'unknown')}: {e}")
            failed += 1

    print()
    print(f"Client Results: {passed} passed, {failed} failed, {passed + failed} total")

    return failed == 0


def main():
    ok = run_all_client_tests()
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
