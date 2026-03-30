"""
Pytest harness for PIL extraction test vectors.
Per DKP-PTL-REG-PIL-TEST-VECTORS-001 v0.1

Pass/fail rule (section 6):
1. pil_extraction_status matches exactly
2. if status is OK, every PIL field matches exactly
3. no extra fields are emitted
4. field values match exact normalized strings

Any mismatch is a failure. No partial pass.
"""

import json
import pytest
from pathlib import Path
from typing import Any, Dict


# Load test vectors
VECTORS_PATH = Path(__file__).parent / "vectors" / "pil_vectors_v0_1.json"


def load_vectors():
    """Load official test vectors."""
    with open(VECTORS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


VECTORS = load_vectors()


def vector_ids():
    """Generate test IDs from vectors."""
    return [v["test_id"] for v in VECTORS]


@pytest.mark.parametrize("vector", VECTORS, ids=vector_ids())
def test_pil_vector(vector: Dict[str, Any]):
    """
    Test a single PIL extraction vector.
    
    This test enforces exact match per specification.
    """
    from client.pil_extraction import extract_pil_from_html
    
    # Extract inputs
    test_id = vector["test_id"]
    inp = vector["input"]
    expected = vector["expected"]
    
    html = inp["html"]
    url = inp["url"]
    utc_year = inp["utc_year"]
    
    # Run extraction
    actual = extract_pil_from_html(html, url, utc_year)
    
    # Compare status first
    expected_status = expected["pil_extraction_status"]
    actual_status = actual.get("pil_extraction_status")
    
    assert actual_status == expected_status, (
        f"[{test_id}] Status mismatch:\n"
        f"  expected: {expected_status}\n"
        f"  actual:   {actual_status}"
    )
    
    # If not OK, we're done
    if expected_status != "OK":
        # Verify no PIL object present on failure
        assert "PIL" not in actual, f"[{test_id}] unexpected PIL object on non-OK status"
        return
    
    # Compare PIL fields
    expected_pil = expected["PIL"]
    actual_pil = actual.get("PIL", {})
    
    # Check exact field match
    pil_fields = [
        "brand",
        "model",
        "sku",
        "condition",
        "bundle_flag",
        "warranty_type",
        "region_variant",
        "storage_or_size",
        "release_year",
    ]
    
    mismatches = []
    for field in pil_fields:
        expected_val = expected_pil.get(field, "")
        actual_val = actual_pil.get(field, "")
        
        if expected_val != actual_val:
            mismatches.append(f"  {field}: expected '{expected_val}', got '{actual_val}'")
    
    # Check for extra fields
    extra_fields = set(actual_pil.keys()) - set(pil_fields)
    if extra_fields:
        mismatches.append(f"  extra fields: {extra_fields}")
    
    if mismatches:
        pytest.fail(
            f"[{test_id}] PIL field mismatch:\n" +
            "\n".join(mismatches) +
            f"\n\nExpected:\n{json.dumps(expected_pil, indent=2)}\n\n" +
            f"Actual:\n{json.dumps(actual_pil, indent=2)}"
        )


def test_all_vectors_loaded():
    """Ensure all 20 official vectors are loaded."""
    assert len(VECTORS) == 20, f"Expected 20 vectors, got {len(VECTORS)}"


def test_vector_ordering():
    """Ensure vectors are in lexical test_id order per spec section 9."""
    ids = [v["test_id"] for v in VECTORS]
    assert ids == sorted(ids), "Vectors must be in lexical test_id order"
