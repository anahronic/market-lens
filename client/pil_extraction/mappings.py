"""
Conflict resolution per DKP-PTL-REG-PIL-EXTRACTION-001 v0.3 section 14.

Rules:
- Higher precedence wins (S1 > S2 > S3 > S4 > S5)
- No merge where prohibited (field-wise is OK, intra-field is not)
- Irreconcilable conflict -> CONFLICT_BLOCKED

Conflict detection uses normalize_text for consistent comparison.
"""

import re
from typing import Dict, List, Optional, Tuple
from client.pil_extraction.normalization import normalize_text
from client.pil_extraction.constants import DICTIONARY_NOISE_V1


def detect_model_conflict(
    structured_model: Optional[str],  # From S1/S2/S3
    dom_model: Optional[str],          # From S4 (title)
) -> bool:
    """
    Detect irreconcilable model conflict per spec.
    
    A conflict exists when:
    - Both sources provide model
    - The models differ in core identity (not just marketing variations)
    
    Core conflict: if BOTH sources have unique numeric identifiers
    that differ, it's a conflict.
    Example: "EOS R6" vs "EOS R5" -> R6 != R5 -> conflict
    
    Uses normalize_text for consistent comparison.
    """
    if not structured_model or not dom_model:
        return False
    
    struct = normalize_text(structured_model)
    dom = normalize_text(dom_model)
    
    if not struct or not dom:
        return False
    
    # Extract core identifiers (alphanumeric sequences)
    struct_core = _extract_core_identifiers(struct)
    dom_core = _extract_core_identifiers(dom)
    
    if not struct_core or not dom_core:
        return False
    
    struct_set = set(struct_core)
    dom_set = set(dom_core)
    
    # If structured has tokens not in DOM at all
    struct_only = struct_set - dom_set
    dom_only = dom_set - struct_set
    
    # If there are tokens unique to each side, check for model number conflicts
    if struct_only and dom_only:
        # Check if unique tokens look like model identifiers (contain digits)
        for s in struct_only:
            if any(c.isdigit() for c in s):
                for d in dom_only:
                    if any(c.isdigit() for c in d):
                        # Both have numeric identifiers that differ -> conflict
                        return True
    
    return False


def _extract_core_identifiers(text: str) -> List[str]:
    """
    Extract alphanumeric identifier tokens from text.
    
    Uses DICTIONARY_NOISE_V1 from constants.py for consistent filtering.
    """
    # Find alphanumeric sequences (model numbers, etc.)
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    # Filter noise and single chars
    return [t for t in tokens if t not in DICTIONARY_NOISE_V1 and len(t) > 1]


def resolve_field_conflict(
    s1_value: Optional[str],
    s2_value: Optional[str],
    s3_value: Optional[str],
    s4_value: Optional[str],
    s5_value: Optional[str],
) -> Tuple[str, str]:
    """
    Resolve field value per precedence.
    Returns (value, source_id).
    
    Note: This is field-wise precedence, not merging.
    """
    if s1_value:
        return (normalize_text(s1_value), "S1")
    if s2_value:
        return (normalize_text(s2_value), "S2")
    if s3_value:
        return (normalize_text(s3_value), "S3")
    if s4_value:
        return (normalize_text(s4_value), "S4")
    if s5_value:
        return (normalize_text(s5_value), "S5")
    return ("", "")


def check_irreconcilable_conflict(
    s1_model: Optional[str],
    dom_title_model: Optional[str],
) -> bool:
    """
    Check for irreconcilable conflict that blocks extraction.
    Per spec section 14: core identity conflicts must block.
    """
    return detect_model_conflict(s1_model, dom_title_model)
