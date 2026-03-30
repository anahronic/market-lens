"""
Main PIL extraction per DKP-PTL-REG-PIL-EXTRACTION-001 v0.3.

Public API:
    extract_pil_from_html(html: str, url: str, utc_year: int) -> dict

EXTRACTION PIPELINE:
1. Parse HTML
2. Collect sources S1-S5
3. Select page unit (with deterministic tie-breaking)
4. Extract title from page unit
5. Run conflict detection
6. Parse all fields following precedence rules
7. Apply validity gate
8. Build and return result

PRECEDENCE MODEL (per spec):
- Field-wise precedence: S1 > S2 > S3 > S4 > S5
- For each field, use the highest-precedence source that provides it
- This is NOT merging (which is prohibited) - it's field-level selection

STATUSES:
- OK: Extraction successful
- NO_MATCH: No product structure found
- INSUFFICIENT_IDENTITY: Model missing or C_extract < 2
- CONFLICT_BLOCKED: Irreconcilable conflict between sources
- INVALID_PAGE_UNIT: Multiple prices or structural issue
"""

from bs4 import BeautifulSoup
from typing import Any

from client.pil_extraction.schemas import (
    PILObject,
    ExtractionResult,
    PILExtractionStatus,
)
from client.pil_extraction.normalization import normalize_text, extract_tokens
from client.pil_extraction.source_collectors import (
    collect_s1_jsonld,
    collect_s2_microdata,
    collect_s3_meta,
    collect_s4_dom_title,
    collect_s5_url_tokens,
    select_best_s1,
    SourceData,
)
from client.pil_extraction.page_unit import (
    select_page_unit,
    get_title_text,
)
from client.pil_extraction.title_parser import (
    parse_brand,
    parse_model,
    parse_sku,
    parse_condition,
    parse_bundle_flag,
    parse_warranty_type,
    parse_region_variant,
    parse_storage_or_size,
    parse_release_year,
)
from client.pil_extraction.url_tokens import extract_url_tokens
from client.pil_extraction.mappings import check_irreconcilable_conflict
from client.pil_extraction.constants import MIN_C_EXTRACT, DICTIONARY_NOISE_V1


# Output contract constants - v0.6.0
_VALID_STATUSES = frozenset(["OK", "NO_MATCH", "INSUFFICIENT_IDENTITY", "CONFLICT_BLOCKED", "INVALID_PAGE_UNIT"])
_PIL_FIELDS = ("brand", "model", "sku", "condition", "bundle_flag", "warranty_type", "region_variant", "storage_or_size", "release_year")


class OutputContractViolation(Exception):
    """Raised when output violates the strict PIL contract."""
    pass


def _validate_output_contract(output: dict) -> None:
    """
    Validate output against strict PIL contract.
    
    Raises OutputContractViolation if any constraint is violated.
    Per DKP-PTL-REG-PIL-TO-REFERENCE-001 v0.6:
    - No extra fields allowed
    - No missing fields allowed
    - All values must be strings
    - Status must be valid
    """
    # Validate status
    status = output.get("pil_extraction_status")
    if status is None:
        raise OutputContractViolation("Missing pil_extraction_status")
    if status not in _VALID_STATUSES:
        raise OutputContractViolation(f"Invalid status: {status}")
    
    if status == "OK":
        # Must have PIL object
        if "PIL" not in output:
            raise OutputContractViolation("Status OK but PIL object missing")
        
        pil = output["PIL"]
        
        # Check for extra fields in PIL
        pil_keys = set(pil.keys())
        expected_keys = set(_PIL_FIELDS)
        extra = pil_keys - expected_keys
        if extra:
            raise OutputContractViolation(f"Extra PIL fields: {extra}")
        
        # Check for missing fields in PIL
        missing = expected_keys - pil_keys
        if missing:
            raise OutputContractViolation(f"Missing PIL fields: {missing}")
        
        # All values must be strings
        for field in _PIL_FIELDS:
            val = pil[field]
            if not isinstance(val, str):
                raise OutputContractViolation(f"PIL field {field} is not string: {type(val)}")
        
        # Check for extra top-level fields
        allowed_top = {"pil_extraction_status", "PIL"}
        actual_top = set(output.keys())
        extra_top = actual_top - allowed_top
        if extra_top:
            raise OutputContractViolation(f"Extra top-level fields: {extra_top}")
    else:
        # Non-OK status must NOT have PIL
        if "PIL" in output:
            raise OutputContractViolation(f"Status {status} but PIL object present")
        
        # Only pil_extraction_status allowed
        if set(output.keys()) != {"pil_extraction_status"}:
            extra = set(output.keys()) - {"pil_extraction_status"}
            raise OutputContractViolation(f"Extra fields on failure: {extra}")


def _make_failure_result(status: str) -> dict:
    """Create validated failure result."""
    result = {"pil_extraction_status": status}
    _validate_output_contract(result)
    return result


def _make_ok_result(pil: PILObject) -> dict:
    """Create validated OK result."""
    result = ExtractionResult(pil_extraction_status="OK", pil=pil)
    output = result.to_dict()
    _validate_output_contract(output)
    return output


def extract_pil_from_html(html: str, url: str, utc_year: int) -> dict:
    """
    Extract Product Identity Layer from HTML.
    
    Args:
        html: Raw HTML string
        url: Page URL
        utc_year: Current UTC year for release year validation
        
    Returns:
        dict with pil_extraction_status and optional PIL object
    """
    # STEP 1: Parse HTML
    soup = BeautifulSoup(html, "html.parser")
    
    # STEP 2: Collect sources S1-S5
    s1_list = collect_s1_jsonld(soup)
    s1 = select_best_s1(s1_list)
    
    s2_list = collect_s2_microdata(soup)
    s2 = s2_list[0] if s2_list else None
    
    s3 = collect_s3_meta(soup)
    
    # STEP 3: Select page unit (with deterministic tie-breaking)
    page_unit = select_page_unit(soup)
    
    if not page_unit.success:
        if page_unit.failure_reason == "multiple_prices":
            return _make_failure_result("INVALID_PAGE_UNIT")
        if page_unit.failure_reason == "no_price":
            return _make_failure_result("NO_MATCH")
        if page_unit.failure_reason == "no_title":
            return _make_failure_result("NO_MATCH")
        return _make_failure_result("INVALID_PAGE_UNIT")
    
    # STEP 4: Extract title from page unit
    title_text = get_title_text(page_unit)
    
    # S4: DOM title
    s4 = collect_s4_dom_title(title_text)
    
    # S5: URL tokens (using canonical extractor from url_tokens.py)
    url_tokens = extract_url_tokens(url)
    s5 = collect_s5_url_tokens(url)
    
    # STEP 5: Run conflict detection
    s1_model = s1.model if s1 else None
    title_model_for_conflict = _extract_model_from_title(title_text, s1, s2, s3)
    
    if s1_model and title_model_for_conflict:
        if check_irreconcilable_conflict(s1_model, title_model_for_conflict):
            return _make_failure_result("CONFLICT_BLOCKED")
    
    # STEP 6: Parse all fields following field-wise precedence (S1 > S2 > S3 > S4 > S5)
    # Brand
    brand = parse_brand(
        s1_brand=s1.brand if s1 else None,
        s2_brand=s2.brand if s2 else None,
        s3_brand=s3.brand if s3 else None,
        title_text=title_text,
        url_tokens=url_tokens,
    )
    
    # Model - S1 > S2 > S3 > S4 (title)
    s1_model_val = s1.model if s1 else None
    s2_model_val = s2.model if s2 else None
    s3_model_val = None  # S3 meta tags don't typically have model field
    
    model = parse_model(
        s1_model=s1_model_val,
        s2_model=s2_model_val,
        s3_model=s3_model_val,
        title_text=title_text,
        brand=brand,
    )
    
    # SKU - S1 > S2 > S3
    sku = parse_sku(
        s1_sku=s1.sku if s1 else None,
        s2_sku=s2.sku if s2 else None,
        s3_sku=s3.sku if s3 else None,
    )
    
    # Condition - S1 > S2 > S3 > S4 (title)
    condition = parse_condition(
        s1_condition=s1.condition if s1 else None,
        s2_condition=s2.condition if s2 else None,
        s3_condition=s3.condition if s3 else None,
        title_text=title_text,
    )
    
    # Bundle flag - from title and S1 name
    bundle_flag = parse_bundle_flag(
        title_text=title_text,
        s1_name=s1.name if s1 else None,
    )
    
    # Warranty - from title
    warranty_type = parse_warranty_type(title_text)
    
    # Region variant - from URL
    region_variant = parse_region_variant(url)
    
    # Storage/size - S1 > S2 > S4 (title)
    storage_or_size = parse_storage_or_size(
        s1_size=s1.size if s1 else None,
        s2_size=s2.size if s2 else None,
        title_text=title_text,
    )
    
    # Release year - from title
    release_year = parse_release_year(title_text, utc_year)
    
    # STEP 7: Apply validity gate per spec section 13
    if not model:
        return _make_failure_result("INSUFFICIENT_IDENTITY")
    
    # C_extract = brand (1 if present) + model_token_count + sku (1 if present)
    c_extract = _count_c_extract(brand, model, sku)
    if c_extract < MIN_C_EXTRACT:
        return _make_failure_result("INSUFFICIENT_IDENTITY")
    
    # STEP 8: Build and return result
    pil = PILObject(
        brand=brand,
        model=model,
        sku=sku,
        condition=condition,
        bundle_flag=bundle_flag,
        warranty_type=warranty_type,
        region_variant=region_variant,
        storage_or_size=storage_or_size,
        release_year=release_year,
    )
    
    return _make_ok_result(pil)


def _extract_model_from_title(
    title_text: str,
    s1: SourceData | None,
    s2: SourceData | None,
    s3: SourceData | None,
) -> str | None:
    """
    Extract model from title for conflict detection.
    
    This is a simplified extraction for detecting conflicts,
    not for the final model field value.
    """
    if not title_text:
        return None
    
    brand = None
    for source in [s1, s2, s3]:
        if source and source.brand:
            brand = source.brand
            break
    
    normalized = normalize_text(title_text)
    if brand and normalized.startswith(brand + " "):
        normalized = normalized[len(brand) + 1:]
    
    # Get first significant tokens as model candidate
    tokens = extract_tokens(normalized)
    model_tokens = [t for t in tokens if t not in DICTIONARY_NOISE_V1][:4]
    
    return " ".join(model_tokens) if model_tokens else None


def _count_c_extract(brand: str, model: str, sku: str) -> int:
    """
    Count C_extract per spec section 13.
    
    C_extract = brand (1 if present) + model_token_count + sku (1 if present)
    
    This ensures sufficient identity information is present.
    """
    count = 0
    if brand:
        count += 1
    if model:
        count += len(model.split())
    if sku:
        count += 1
    return count
