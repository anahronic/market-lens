#!/usr/bin/env python3
"""
CLI runner for PIL extraction test vectors.
Per DKP-PTL-REG-PIL-TEST-VECTORS-001 v0.1 section 9.

LOCKED for v0.6.0:
- EXACTLY 20 vectors required
- Vector IDs must be pil_tv_0001 through pil_tv_0020
- Any deviation is a hard failure

Usage:
    python -m tests.pil_extraction.test_runner_pil [--json] [--verbose]
    
Output schema:
{
  "suite_id": "pil_vectors_v0_1",
  "pil_extraction_version": "0.3",
  "passed": 20,
  "failed": 0,
  "results": [
    {"test_id": "pil_tv_0001", "status": "PASS"}
  ]
}
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List


# LOCKED: Expected vector count and IDs
EXPECTED_VECTOR_COUNT = 20
EXPECTED_VECTOR_IDS = frozenset(f"pil_tv_{i:04d}" for i in range(1, 21))


def load_vectors() -> List[Dict[str, Any]]:
    """Load official test vectors."""
    vectors_path = Path(__file__).parent / "vectors" / "pil_vectors_v0_1.json"
    with open(vectors_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_vector_integrity(vectors: List[Dict[str, Any]]) -> None:
    """
    Validate vector set integrity per DKP-PTL-REG-PIL-TEST-VECTORS-001 v0.1.
    
    LOCKED for v0.6.0:
    - Exactly 20 vectors required
    - Vector IDs must match expected set
    - Any deviation is a hard failure
    
    Raises ValueError on any violation.
    """
    # Check count
    actual_count = len(vectors)
    if actual_count != EXPECTED_VECTOR_COUNT:
        raise ValueError(
            f"Vector count mismatch: expected {EXPECTED_VECTOR_COUNT}, got {actual_count}"
        )
    
    # Check IDs
    actual_ids = frozenset(v["test_id"] for v in vectors)
    
    missing = EXPECTED_VECTOR_IDS - actual_ids
    if missing:
        raise ValueError(f"Missing vectors: {sorted(missing)}")
    
    extra = actual_ids - EXPECTED_VECTOR_IDS
    if extra:
        raise ValueError(f"Extra vectors: {sorted(extra)}")
    
    # Check for duplicates
    if len(actual_ids) != actual_count:
        raise ValueError("Duplicate vector IDs detected")


def run_single_vector(vector: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    """
    Run a single test vector.
    Returns result dict with test_id, status, and optional details.
    """
    from client.pil_extraction import extract_pil_from_html
    
    test_id = vector["test_id"]
    inp = vector["input"]
    expected = vector["expected"]
    
    try:
        actual = extract_pil_from_html(
            html=inp["html"],
            url=inp["url"],
            utc_year=inp["utc_year"],
        )
    except Exception as e:
        return {
            "test_id": test_id,
            "status": "FAIL",
            "error": f"Exception: {type(e).__name__}: {e}",
        }
    
    # Compare
    mismatches = compare_results(expected, actual)
    
    if mismatches:
        result = {
            "test_id": test_id,
            "status": "FAIL",
            "mismatches": mismatches,
        }
        if verbose:
            result["expected"] = expected
            result["actual"] = actual
        return result
    
    return {"test_id": test_id, "status": "PASS"}


def compare_results(expected: Dict[str, Any], actual: Dict[str, Any]) -> List[str]:
    """Compare expected vs actual, return list of mismatches."""
    mismatches = []
    
    # Status
    exp_status = expected["pil_extraction_status"]
    act_status = actual.get("pil_extraction_status")
    
    if exp_status != act_status:
        mismatches.append(f"status: expected '{exp_status}', got '{act_status}'")
        return mismatches  # Don't compare PIL if status differs
    
    if exp_status != "OK":
        # Non-OK status, check no PIL present
        if "PIL" in actual:
            mismatches.append("unexpected PIL object on non-OK status")
        return mismatches
    
    # Compare PIL fields
    exp_pil = expected.get("PIL", {})
    act_pil = actual.get("PIL", {})
    
    pil_fields = [
        "brand", "model", "sku", "condition", "bundle_flag",
        "warranty_type", "region_variant", "storage_or_size", "release_year",
    ]
    
    for field in pil_fields:
        exp_val = exp_pil.get(field, "")
        act_val = act_pil.get(field, "")
        if exp_val != act_val:
            mismatches.append(f"{field}: expected '{exp_val}', got '{act_val}'")
    
    # Check extra fields
    extra = set(act_pil.keys()) - set(pil_fields)
    if extra:
        mismatches.append(f"extra fields: {extra}")
    
    return mismatches


def run_suite(verbose: bool = False) -> Dict[str, Any]:
    """
    Run full test suite.
    Returns result per spec section 9.
    
    LOCKED for v0.6.0: Validates vector integrity before running.
    """
    vectors = load_vectors()
    
    # LOCKED: Validate vector set integrity
    validate_vector_integrity(vectors)
    
    # Sort by test_id (lexical order per spec)
    vectors.sort(key=lambda v: v["test_id"])
    
    results = []
    passed = 0
    failed = 0
    
    for vector in vectors:
        result = run_single_vector(vector, verbose)
        results.append(result)
        
        if result["status"] == "PASS":
            passed += 1
        else:
            failed += 1
    
    return {
        "suite_id": "pil_vectors_v0_1",
        "pil_extraction_version": "0.3",
        "passed": passed,
        "failed": failed,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(
        description="PIL extraction test vector runner"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Include full expected/actual on failures",
    )
    args = parser.parse_args()
    
    # Run suite
    summary = run_suite(verbose=args.verbose)
    
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        # Human-readable output
        print(f"PIL Extraction Test Suite: {summary['suite_id']}")
        print(f"Extraction Version: {summary['pil_extraction_version']}")
        print("-" * 50)
        
        for result in summary["results"]:
            status = result["status"]
            test_id = result["test_id"]
            
            if status == "PASS":
                print(f"  ✓ {test_id}")
            else:
                print(f"  ✗ {test_id}")
                if "mismatches" in result:
                    for m in result["mismatches"]:
                        print(f"      - {m}")
                if "error" in result:
                    print(f"      - {result['error']}")
                if args.verbose and "expected" in result:
                    print(f"      expected: {json.dumps(result['expected'], indent=8)}")
                    print(f"      actual:   {json.dumps(result['actual'], indent=8)}")
        
        print("-" * 50)
        print(f"Passed: {summary['passed']}/{summary['passed'] + summary['failed']}")
        
        if summary["failed"] > 0:
            print(f"Failed: {summary['failed']}")
    
    # Exit code per spec
    sys.exit(1 if summary["failed"] > 0 else 0)


if __name__ == "__main__":
    main()
