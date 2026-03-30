"""
Version-locked constants per DKP-PTL-REG-PIL-EXTRACTION-001 v0.3.
All constants MUST be immutable and version-bound.

This module is the SINGLE SOURCE OF TRUTH for:
- Price regex
- Storage regex
- Tokenize regex
- Allowed chars regex
- Condition synonyms
- Bundle keywords
- Warranty keywords
- Region tokens
- Noise dictionary
"""

import re
from typing import FrozenSet

# Specification version
PIL_EXTRACTION_VERSION = "0.3"

# DICTIONARY_NOISE_v1 per spec section 19
# These tokens are removed from model parsing.
DICTIONARY_NOISE_V1: FrozenSet[str] = frozenset({
    "new",
    "sale",
    "best",
    "free",
    "shipping",
    "deal",
    "discount",
    "promo",
})

# Price regex per spec section 2
# (₪|$|€|£|USD|ILS|EUR|GBP)?\s?[0-9]{1,3}([,\s][0-9]{3})*(\.[0-9]{1,2})?
# CANONICAL PATTERN: currency symbol/code must be present + digits
# Supports currency before OR after the number
PRICE_REGEX_V1 = re.compile(
    r"([₪$€£]|USD|ILS|EUR|GBP)\s*[0-9]{1,3}(?:[,\s][0-9]{3})*(?:\.[0-9]{1,2})?"
    r"|"
    r"[0-9]{1,3}(?:[,\s][0-9]{3})*(?:\.[0-9]{1,2})?\s*([₪$€£]|USD|ILS|EUR|GBP)",
    re.IGNORECASE
)

# Price presence regex - must contain currency symbol/code AND digit
CURRENCY_SYMBOLS = frozenset({"₪", "$", "€", "£"})
CURRENCY_CODES = frozenset({"USD", "ILS", "EUR", "GBP"})

# Storage/size regex per spec section 12.9
# [0-9]+(gb|tb|w|cm|inch)
STORAGE_REGEX_V1 = re.compile(r"([0-9]+)(gb|tb|w|cm|inch)", re.IGNORECASE)

# Tokenization regex per spec section 12.1
# Split by [\s,|()[\]]+
TOKENIZE_REGEX = re.compile(r"[\s,|()\[\]]+")

# Allowed chars after normalization per spec section 8
# [a-z0-9 \-/+.&]
ALLOWED_CHARS_REGEX = re.compile(r"[^a-z0-9 \-/+.&]")

# Model constraints per spec section 12.3
MODEL_MAX_BYTES = 128

# Release year bounds per spec section 12.10
RELEASE_YEAR_MIN = 1970

# LCA depth bound per spec section 7.2
LCA_MAX_DEPTH = 10

# URL token limit per spec section 11
URL_MAX_TOKENS = 3

# Validity gate minimum C_extract per spec section 13
MIN_C_EXTRACT = 2

# Non-brand tokens: these appear in URL but are product line names, not manufacturers
# Per test vectors, these should NOT be extracted as brand even if in URL
NON_BRAND_TOKENS: FrozenSet[str] = frozenset({
    "steam",       # Steam Deck is by Valve
    "macbook",     # MacBook is by Apple
    "iphone",      # iPhone is by Apple
    "ipad",        # iPad is by Apple
    "galaxy",      # Galaxy is by Samsung
    "pixel",       # Pixel is by Google
    "surface",     # Surface is by Microsoft
    "thinkpad",    # ThinkPad is by Lenovo
    "playstation", # PlayStation is by Sony
    "xbox",        # Xbox is by Microsoft
})

# Common URL path segments to filter from URL tokens
URL_PATH_NOISE: FrozenSet[str] = frozenset({
    "product",
    "products",
    "p",
    "item",
    "items",
    "search",
})

# Condition mapping - synonyms to canonical values
# Multi-token phrases MUST come before single-token fallbacks for matching order
CONDITION_PHRASES = [
    ("open box", "open_box"),
    ("open-box", "open_box"),
    ("openbox", "open_box"),
    ("pre-owned", "used"),
    ("pre owned", "used"),
    ("preowned", "used"),
]

CONDITION_SYNONYMS = {
    "new": "new",
    "renewed": "refurbished",
    "refurbished": "refurbished",
    "refurb": "refurbished",
    "used": "used",
}

# Bundle detection keywords - TIGHTENED
# "with" alone is NOT sufficient - must be a product term
BUNDLE_KEYWORDS: FrozenSet[str] = frozenset({
    "kit",
    "bundle",
    "combo",
    "set",
    "package",
})

# Bundle phrase patterns - more specific than single "with"
BUNDLE_PHRASES = [
    "with charger",
    "with case",
    "with accessories",
    "with battery",
    "with stand",
    "with mount",
]

# Warranty keywords
WARRANTY_KEYWORDS = {
    "manufacturer warranty": "manufacturer",
    "mfr warranty": "manufacturer", 
    "official warranty": "official",
    "local warranty": "local",
    "international warranty": "international",
    "no warranty": "none",
}

# Region detection in URL
REGION_URL_TOKENS = {
    "il": "il",
    "israel": "il",
    "us": "us",
    "usa": "us",
    "uk": "uk",
    "eu": "eu",
    "global": "global",
}
