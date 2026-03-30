"""
Normalization module per DKP-PTL-REG-PIL-EXTRACTION-001 v0.3 section 8.

CANONICAL NORMALIZATION PATH (single source of truth):

1. UTF-8 decode (if bytes)
2. NFC normalization
3. Remove zero-width characters
4. Trim whitespace
5. Collapse multiple spaces to single
6. Case-fold (lowercase)

FIELD-SPECIFIC TRANSFORMATIONS (applied separately, not in base normalize):
- Inch notation: '"' -> 'inch', '″' -> 'inch', "''" -> 'inch'
- Ampersand: '&' -> 'and'

These are in separate helpers because:
- SKU should NOT get & -> and transformation
- Not all fields need inch normalization
"""

import unicodedata
import re
from typing import Optional

from client.pil_extraction.constants import TOKENIZE_REGEX

# Zero-width characters to remove
ZERO_WIDTH_CHARS = frozenset({
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\ufeff",  # BOM / zero-width no-break space
    "\u2060",  # word joiner
    "\u00ad",  # soft hyphen
})

# Collapse multiple spaces to single space
COLLAPSE_SPACES_RE = re.compile(r"\s+")


def normalize_text(text: Optional[str]) -> str:
    """
    Apply canonical normalization per spec section 8.
    
    This is the BASE normalizer - no semantic transformations.
    Use field-specific functions for semantic transforms like inch/ampersand.
    
    Args:
        text: Raw input text (may be None or bytes)
        
    Returns:
        Normalized string (lowercase, single spaces, no zero-width chars)
    """
    if text is None:
        return ""
    
    # Handle bytes input
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    
    # NFC normalization
    text = unicodedata.normalize("NFC", text)
    
    # Remove zero-width characters
    text = "".join(c for c in text if c not in ZERO_WIDTH_CHARS)
    
    # Trim
    text = text.strip()
    
    # Collapse spaces
    text = COLLAPSE_SPACES_RE.sub(" ", text)
    
    # Case-fold (lowercase)
    text = text.casefold()
    
    return text


def normalize_for_display(text: Optional[str]) -> str:
    """
    Normalize text with display-friendly semantic transformations.
    
    Applies:
    - Base normalization
    - '&' -> ' and '
    - Inch marks -> 'inch'
    
    Use for: title, model, brand, condition, storage_or_size
    Do NOT use for: SKU
    """
    normalized = normalize_text(text)
    
    # Semantic replacements
    # Ampersand -> "and"
    normalized = normalized.replace("&", " and ")
    
    # Inch notation variants -> "inch"
    normalized = normalized.replace('"', 'inch')
    normalized = normalized.replace("″", "inch")
    normalized = normalized.replace("''", "inch")
    
    # Re-collapse spaces after substitutions
    normalized = COLLAPSE_SPACES_RE.sub(" ", normalized).strip()
    
    return normalized


def normalize_sku(text: Optional[str]) -> str:
    """
    Normalize SKU: lowercase, alphanumeric + hyphen only.
    
    SKU has its own canonical path - no semantic transforms.
    """
    if text is None:
        return ""
    
    # Base normalization first  
    text = normalize_text(text)
    
    # SKU: only alphanumeric and hyphen
    result = []
    for c in text:
        if c.isalnum() or c == "-":
            result.append(c)
    return "".join(result)


def extract_tokens(text: str) -> list[str]:
    """
    Tokenize per spec section 12.1.
    Split by [\\s,|()[\\]]+
    
    Uses TOKENIZE_REGEX from constants.py (single source of truth).
    """
    if not text:
        return []
    
    # Split using canonical tokenize regex
    tokens = TOKENIZE_REGEX.split(text)
    
    # Remove empty tokens
    return [t for t in tokens if t]
