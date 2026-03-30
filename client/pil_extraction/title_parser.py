"""
Field parsing per DKP-PTL-REG-PIL-EXTRACTION-001 v0.3 section 12.

Parsing rules for each PIL field with strict determinism.

IMPORTANT: Uses normalize_text for BASE normalization.
Field-specific semantic transforms are applied where appropriate.
SKU uses its own canonical path (normalize_sku).
"""

import re
from typing import Optional, List, Tuple

from client.pil_extraction.normalization import (
    normalize_text,
    normalize_for_display,
    normalize_sku,
    extract_tokens,
)
from client.pil_extraction.constants import (
    DICTIONARY_NOISE_V1,
    STORAGE_REGEX_V1,
    MODEL_MAX_BYTES,
    RELEASE_YEAR_MIN,
    CONDITION_PHRASES,
    CONDITION_SYNONYMS,
    BUNDLE_KEYWORDS,
    BUNDLE_PHRASES,
    WARRANTY_KEYWORDS,
    NON_BRAND_TOKENS,
)


def parse_brand(
    s1_brand: Optional[str],
    s2_brand: Optional[str],
    s3_brand: Optional[str],
    title_text: str,
    url_tokens: List[str],
) -> str:
    """
    Parse brand per spec section 12.2.
    
    Brand valid ONLY if:
    - exists in S1-S3
      OR
    - first title token (Latin) matches URL token AND not in NON_BRAND_TOKENS
      OR
    - for non-Latin prefix: find first Latin token that matches URL
    """
    # S1 > S2 > S3 precedence
    for brand in [s1_brand, s2_brand, s3_brand]:
        if brand:
            return normalize_text(brand)
    
    # Fallback: find first title token that appears in URL tokens
    title_tokens = extract_tokens(normalize_text(title_text))
    if not title_tokens or not url_tokens:
        return ""
    
    title_first = title_tokens[0]
    
    # Check if first token is non-Latin (Hebrew, etc.) - allow searching further
    first_is_latin = all(c.isascii() or c.isspace() for c in title_first)
    
    if first_is_latin:
        # Standard case: first token must be brand
        if title_first in NON_BRAND_TOKENS:
            return ""
        if title_first in url_tokens:
            return title_first
        return ""
    else:
        # Non-Latin prefix: search for first Latin token matching URL
        for title_token in title_tokens[1:]:  # Skip the non-Latin first token
            # Skip non-brand tokens
            if title_token in NON_BRAND_TOKENS:
                continue
            if title_token in url_tokens:
                return title_token
        return ""


def parse_model(
    s1_model: Optional[str],
    s2_model: Optional[str],
    s3_model: Optional[str],
    title_text: str,
    brand: str,
) -> str:
    """
    Parse model per spec section 12.3.
    
    Steps:
    1. Remove brand prefix/occurrence if exists
    2. Remove tokens in DICTIONARY_NOISE_v1
    3. Remove tokens matching price_regex_v1
    4. Remaining tokens -> contiguous segments
    5. Select segment with max length, tie-break earliest occurrence
    
    Constraints:
    - must contain >=1 alphabetic char
    - max 128 bytes
    """
    # S1 > S2 > S3 precedence for structured model
    for model in [s1_model, s2_model, s3_model]:
        if model:
            normalized = normalize_text(model)
            if _is_valid_model(normalized):
                return normalized
    
    # Parse from title
    normalized_title = normalize_text(title_text)
    if not normalized_title:
        return ""
    
    # Step 1: Remove brand - either at start or find and take what's after
    if brand:
        if normalized_title.startswith(brand + " "):
            normalized_title = normalized_title[len(brand) + 1:]
        elif normalized_title.startswith(brand):
            normalized_title = normalized_title[len(brand):]
        elif (" " + brand + " ") in normalized_title:
            # Brand is in the middle - take everything after brand
            idx = normalized_title.find(" " + brand + " ")
            normalized_title = normalized_title[idx + len(brand) + 2:]  # +2 for the two spaces
        elif normalized_title.endswith(" " + brand):
            # Brand at end - take everything before
            normalized_title = normalized_title[:-(len(brand) + 1)]
    
    # Step 2-3: Tokenize and filter
    tokens = extract_tokens(normalized_title)
    filtered_tokens = []
    removal_indices = set()
    
    for i, token in enumerate(tokens):
        # Remove noise dictionary words
        if token in DICTIONARY_NOISE_V1:
            removal_indices.add(i)
            continue
        # Remove price-like tokens (just digits with optional currency)
        # BUT keep 4-digit years (1970-2100 range)
        if re.match(r"^[₪$€£]?[0-9,.\s]+[₪$€£]?$", token):
            # Check if it's a potential year (4 digits)
            if re.match(r"^(19[7-9]\d|20\d\d|21[0-9]\d)$", token):
                # Could be a year, keep it
                pass
            else:
                removal_indices.add(i)
                continue
        filtered_tokens.append((i, token))
    
    if not filtered_tokens:
        return ""
    
    # Step 4: Find contiguous segments (no removal gaps)
    segments = []
    current_segment = []
    last_idx = -2
    
    for idx, token in filtered_tokens:
        if idx == last_idx + 1:
            # Contiguous
            current_segment.append(token)
        else:
            # Gap - start new segment
            if current_segment:
                segments.append(current_segment)
            current_segment = [token]
        last_idx = idx
    
    if current_segment:
        segments.append(current_segment)
    
    if not segments:
        return ""
    
    # Step 5: Select segment with max length, tie-break earliest
    best_segment = max(segments, key=lambda s: len(s))
    model = " ".join(best_segment)
    
    # Validate
    if not _is_valid_model(model):
        return ""
    
    return model


def _is_valid_model(model: str) -> bool:
    """Check model validity per spec section 12.3."""
    if not model:
        return False
    
    # Must contain at least 1 alphabetic char
    if not any(c.isalpha() for c in model):
        return False
    
    # Max 128 bytes
    if len(model.encode("utf-8")) > MODEL_MAX_BYTES:
        return False
    
    return True


def parse_sku(
    s1_sku: Optional[str],
    s2_sku: Optional[str],
    s3_sku: Optional[str],
) -> str:
    """
    Parse SKU per spec. S1 > S2 > S3 precedence.
    
    USES normalize_sku for SKU-specific canonical path.
    SKU: lowercase, alphanumeric + hyphen only.
    """
    for sku in [s1_sku, s2_sku, s3_sku]:
        if sku:
            return normalize_sku(sku)
    return ""


def parse_condition(
    s1_condition: Optional[str],
    s2_condition: Optional[str],
    s3_condition: Optional[str],
    title_text: str,
) -> str:
    """
    Parse condition per spec section 12.5.
    
    Priority:
    1. S1 > S2 > S3 structured data
    2. Multi-token phrases in title (open box, pre-owned)
    3. Single-token fallback in title (new, used, refurbished)
    
    Map synonyms to canonical values.
    """
    # S1 > S2 > S3 precedence
    for condition in [s1_condition, s2_condition, s3_condition]:
        if condition:
            cond_lower = condition.lower()
            # Check single-word synonyms
            if cond_lower in CONDITION_SYNONYMS:
                return CONDITION_SYNONYMS[cond_lower]
            # Check if it contains a known condition word
            for key, val in CONDITION_SYNONYMS.items():
                if key in cond_lower:
                    return val
    
    # Check title for condition
    normalized_title = normalize_text(title_text)
    
    # First check multi-token phrases (higher priority)
    for phrase, canonical in CONDITION_PHRASES:
        if phrase in normalized_title:
            return canonical
    
    # Then check single-token fallback
    tokens = extract_tokens(normalized_title)
    for token in tokens:
        if token in CONDITION_SYNONYMS:
            return CONDITION_SYNONYMS[token]
    
    return ""


def parse_bundle_flag(title_text: str, s1_name: Optional[str] = None) -> str:
    """
    Parse bundle flag per spec section 12.6.
    
    TIGHTENED DETECTION:
    1. Check for explicit bundle keywords (kit, bundle, combo, set, package)
    2. Check for specific bundle phrases (with charger, with case, etc.)
    
    "with" alone is NOT sufficient - too many false positives.
    """
    search_text = normalize_text(title_text)
    if s1_name:
        search_text = search_text + " " + normalize_text(s1_name)
    
    tokens = extract_tokens(search_text)
    
    # Check explicit bundle keywords
    for token in tokens:
        if token in BUNDLE_KEYWORDS:
            return "bundle"
    
    # Check specific bundle phrases
    for phrase in BUNDLE_PHRASES:
        if phrase in search_text:
            return "bundle"
    
    return "standalone"


def parse_warranty_type(
    title_text: str,
    structured_warranty: Optional[str] = None,
) -> str:
    """Parse warranty type per spec section 12.7."""
    if structured_warranty:
        return normalize_text(structured_warranty)
    
    normalized = normalize_text(title_text)
    
    for phrase, warranty_type in WARRANTY_KEYWORDS.items():
        if phrase in normalized:
            return warranty_type
    
    return ""


def parse_region_variant(url: str) -> str:
    """Parse region variant per spec section 12.8."""
    from client.pil_extraction.constants import REGION_URL_TOKENS
    from urllib.parse import urlparse
    
    parsed = urlparse(url)
    path_parts = parsed.path.lower().split("/")
    
    for part in path_parts:
        if part in REGION_URL_TOKENS:
            return REGION_URL_TOKENS[part]
    
    return ""


def parse_storage_or_size(
    s1_size: Optional[str],
    s2_size: Optional[str],
    title_text: str,
) -> str:
    """
    Parse storage/size per spec section 12.9.
    Regex: [0-9]+(gb|tb|w|cm|inch)
    """
    # Check structured sources first
    for size in [s1_size, s2_size]:
        if size:
            normalized = normalize_text(size)
            match = STORAGE_REGEX_V1.search(normalized)
            if match:
                return match.group(0)
    
    # Parse from title
    normalized_title = normalize_text(title_text)
    match = STORAGE_REGEX_V1.search(normalized_title)
    if match:
        return match.group(0)
    
    return ""


def parse_release_year(title_text: str, utc_year: int) -> str:
    """
    Parse release year per spec section 12.10.
    Valid if: 1970 <= year <= current_year + 2
    """
    normalized = normalize_text(title_text)
    
    # Find 4-digit year patterns
    year_pattern = re.compile(r"\b(19[7-9][0-9]|20[0-9]{2})\b")
    matches = year_pattern.findall(normalized)
    
    max_valid_year = utc_year + 2
    
    for year_str in matches:
        year = int(year_str)
        if RELEASE_YEAR_MIN <= year <= max_valid_year:
            return year_str
    
    return ""
