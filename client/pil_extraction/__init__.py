"""
DKP-PTL-REG-PIL-EXTRACTION-001 v0.3 Reference Implementation.

This module provides deterministic Product Identity Layer (PIL) extraction
from rendered webpages per the specification.

Public API:
    extract_pil_from_html(html: str, url: str, utc_year: int) -> dict
"""

from client.pil_extraction.extractor import extract_pil_from_html

__all__ = ["extract_pil_from_html"]
