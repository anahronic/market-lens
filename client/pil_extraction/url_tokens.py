"""
URL token handling per DKP-PTL-REG-PIL-EXTRACTION-001 v0.3 section 11.

SINGLE SOURCE OF TRUTH for S5 URL token extraction.

Contract:
- Extract tokens from URL path AND query parameter values
- Split by: /, -, _
- Filter noise dictionary words
- Filter common path segments
- Limit to max 3 tokens
- Deterministic ordering preserved (path first, then query)

Restrictions per spec:
- max tokens used = 3
- S5 MUST NOT populate model if S1-S3 exist
"""

import re
from typing import List
from urllib.parse import urlparse, unquote, parse_qs

from client.pil_extraction.normalization import normalize_text
from client.pil_extraction.constants import (
    DICTIONARY_NOISE_V1,
    URL_MAX_TOKENS,
    URL_PATH_NOISE,
)


def extract_url_tokens(url: str) -> List[str]:
    """
    Extract tokens from URL (S5 source).
    
    CANONICAL S5 TOKEN EXTRACTION:
    1. Parse URL
    2. Split path by /, -, _
    3. Split query param values by space, -, _
    4. Normalize each token
    5. Filter noise and path segments
    6. Limit to URL_MAX_TOKENS (3)
    
    This is the ONLY function that should extract URL tokens.
    """
    parsed = urlparse(url)
    path = unquote(parsed.path)
    
    # Split path by /, -, _
    raw_tokens = re.split(r"[/\-_]", path)
    
    # Also extract tokens from query string values
    query_params = parse_qs(parsed.query)
    for values in query_params.values():
        for val in values:
            val_decoded = unquote(val)
            # Split query values by space, dash, underscore
            raw_tokens.extend(re.split(r"[\s\-_]", val_decoded))
    
    # Filter: non-empty, not in noise dictionary, not common path segment
    tokens = []
    for t in raw_tokens:
        t_clean = normalize_text(t)
        # Skip empty
        if not t_clean:
            continue
        # Skip noise dictionary words
        if t_clean in DICTIONARY_NOISE_V1:
            continue
        # Skip common path segments
        if t_clean in URL_PATH_NOISE:
            continue
        tokens.append(t_clean)
    
    # Limit to max tokens
    return tokens[:URL_MAX_TOKENS]


def can_use_url_for_model(
    s1_model: str,
    s2_model: str,
    s3_model: str,
) -> bool:
    """
    Per spec section 11: S5 MUST NOT populate model if S1-S3 exist.
    
    Returns True if URL tokens CAN be used for model (no structured model exists).
    Returns False if URL tokens MUST NOT be used (structured model exists).
    """
    return not (s1_model or s2_model or s3_model)
