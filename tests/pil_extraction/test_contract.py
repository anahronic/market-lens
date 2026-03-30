"""
Contract validation tests for PIL extraction output.
Per DKP-PTL-REG-PIL-TO-REFERENCE-001 v0.6.

Tests:
1. Output schema validation
2. No extra fields
3. All 9 PIL fields present on OK
4. No PIL object on failure
5. Field types are strings only
"""

import pytest

from client.pil_extraction.extractor import (
    extract_pil_from_html,
    _validate_output_contract,
    OutputContractViolation,
    _VALID_STATUSES,
    _PIL_FIELDS,
)


# Test fixtures
VALID_OK_OUTPUT = {
    "pil_extraction_status": "OK",
    "PIL": {
        "brand": "apple",
        "model": "iphone 13",
        "sku": "a2633",
        "condition": "new",
        "bundle_flag": "standalone",
        "warranty_type": "",
        "region_variant": "",
        "storage_or_size": "128gb",
        "release_year": "",
    }
}

VALID_FAILURE_OUTPUT = {
    "pil_extraction_status": "NO_MATCH"
}

SIMPLE_HTML = """
<html>
<head>
<script type="application/ld+json">
{"@type":"Product","brand":{"name":"Apple"},"model":"iPhone 13","sku":"A2633","itemCondition":"new","size":"128GB"}
</script>
</head>
<body><h1>Apple iPhone 13 128GB</h1><span class="price">$999</span></body>
</html>
"""


class TestOutputSchemaValidation:
    """Test 1: Output schema validation."""
    
    def test_valid_ok_output_passes(self):
        """Valid OK output should pass validation."""
        _validate_output_contract(VALID_OK_OUTPUT)
    
    def test_valid_failure_output_passes(self):
        """Valid failure output should pass validation."""
        _validate_output_contract(VALID_FAILURE_OUTPUT)
    
    def test_missing_status_raises(self):
        """Missing status field should raise."""
        with pytest.raises(OutputContractViolation, match="Missing pil_extraction_status"):
            _validate_output_contract({})
    
    def test_invalid_status_raises(self):
        """Invalid status value should raise."""
        with pytest.raises(OutputContractViolation, match="Invalid status"):
            _validate_output_contract({"pil_extraction_status": "UNKNOWN"})
    
    def test_all_valid_statuses_accepted(self):
        """All valid status values should be accepted."""
        for status in _VALID_STATUSES:
            if status == "OK":
                output = {"pil_extraction_status": status, "PIL": VALID_OK_OUTPUT["PIL"]}
            else:
                output = {"pil_extraction_status": status}
            _validate_output_contract(output)


class TestNoExtraFields:
    """Test 2: No extra fields allowed."""
    
    def test_extra_top_level_field_raises(self):
        """Extra top-level field should raise."""
        output = {
            "pil_extraction_status": "OK",
            "PIL": VALID_OK_OUTPUT["PIL"],
            "_debug": "extra"
        }
        with pytest.raises(OutputContractViolation, match="Extra top-level fields"):
            _validate_output_contract(output)
    
    def test_extra_pil_field_raises(self):
        """Extra PIL field should raise."""
        pil = dict(VALID_OK_OUTPUT["PIL"])
        pil["extra_field"] = "value"
        output = {"pil_extraction_status": "OK", "PIL": pil}
        with pytest.raises(OutputContractViolation, match="Extra PIL fields"):
            _validate_output_contract(output)
    
    def test_extra_field_on_failure_raises(self):
        """Extra field on failure status should raise."""
        output = {
            "pil_extraction_status": "NO_MATCH",
            "reason": "some reason"
        }
        with pytest.raises(OutputContractViolation, match="Extra fields on failure"):
            _validate_output_contract(output)


class TestAllPilFieldsPresent:
    """Test 3: All 9 PIL fields must be present on OK status."""
    
    def test_all_nine_fields_present(self):
        """All 9 PIL fields must be present."""
        assert len(_PIL_FIELDS) == 9
        assert set(_PIL_FIELDS) == {
            "brand", "model", "sku", "condition", "bundle_flag",
            "warranty_type", "region_variant", "storage_or_size", "release_year"
        }
    
    def test_missing_field_raises(self):
        """Missing PIL field should raise."""
        for field in _PIL_FIELDS:
            pil = dict(VALID_OK_OUTPUT["PIL"])
            del pil[field]
            output = {"pil_extraction_status": "OK", "PIL": pil}
            with pytest.raises(OutputContractViolation, match="Missing PIL fields"):
                _validate_output_contract(output)


class TestNoPilOnFailure:
    """Test 4: No PIL object on failure status."""
    
    def test_pil_on_failure_raises(self):
        """PIL object on failure status should raise."""
        for status in _VALID_STATUSES:
            if status == "OK":
                continue
            output = {
                "pil_extraction_status": status,
                "PIL": VALID_OK_OUTPUT["PIL"]
            }
            with pytest.raises(OutputContractViolation, match="but PIL object present"):
                _validate_output_contract(output)
    
    def test_ok_without_pil_raises(self):
        """OK status without PIL should raise."""
        output = {"pil_extraction_status": "OK"}
        with pytest.raises(OutputContractViolation, match="PIL object missing"):
            _validate_output_contract(output)


class TestFieldTypesStringsOnly:
    """Test 5: Field types must be strings only."""
    
    def test_non_string_field_raises(self):
        """Non-string PIL field should raise."""
        test_cases = [
            ("brand", 123),
            ("model", None),
            ("sku", ["list"]),
            ("condition", {"dict": True}),
            ("bundle_flag", True),
        ]
        for field, value in test_cases:
            pil = dict(VALID_OK_OUTPUT["PIL"])
            pil[field] = value
            output = {"pil_extraction_status": "OK", "PIL": pil}
            with pytest.raises(OutputContractViolation, match=f"PIL field {field} is not string"):
                _validate_output_contract(output)


class TestIntegration:
    """Integration tests with real extraction."""
    
    def test_extract_produces_valid_output(self):
        """Extraction should produce valid output."""
        result = extract_pil_from_html(SIMPLE_HTML, "https://example.com/product", 2026)
        # Should not raise
        _validate_output_contract(result)
    
    def test_extract_failure_produces_valid_output(self):
        """Extraction failure should produce valid output."""
        result = extract_pil_from_html("<html><body>No product</body></html>", "https://example.com", 2026)
        # Should not raise
        _validate_output_contract(result)
    
    def test_output_deterministic(self):
        """Same input should produce identical output."""
        result1 = extract_pil_from_html(SIMPLE_HTML, "https://example.com/product", 2026)
        result2 = extract_pil_from_html(SIMPLE_HTML, "https://example.com/product", 2026)
        assert result1 == result2
