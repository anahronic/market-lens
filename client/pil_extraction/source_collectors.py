"""
Source collectors per DKP-PTL-REG-PIL-EXTRACTION-001 v0.3 section 5-6.

Source classes:
  S1: JSON-LD
  S2: Microdata / RDFa
  S3: Meta tags
  S4: DOM visible text
  S5: URL tokens

Precedence: S1 > S2 > S3 > S4 > S5

NOTE ON "NO MERGING":
The spec declares "No merging allowed" for sources. This means:
- For a given FIELD, use the highest-precedence source that provides it
- Do NOT combine partial data from multiple sources for a single field

FIELD-WISE precedence IS allowed (brand from S1, model from S4 if S1 lacks model).
This is not the same as merging.

This module only COLLECTS data from sources.
Precedence resolution happens in extractor.py.
"""

import json
import re
from typing import Optional
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup, Tag

from client.pil_extraction.normalization import normalize_text, normalize_sku
from client.pil_extraction.url_tokens import extract_url_tokens
from client.pil_extraction.constants import (
    REGION_URL_TOKENS,
)


class SourceData:
    """Data collected from a single source."""
    def __init__(self, source_id: str):
        self.source_id = source_id
        self.brand: Optional[str] = None
        self.model: Optional[str] = None
        self.sku: Optional[str] = None
        self.condition: Optional[str] = None
        self.size: Optional[str] = None
        self.name: Optional[str] = None  # product name, may contain brand+model
        self.region: Optional[str] = None
        self.offers: bool = False
        self.dom_order: int = 0  # for tie-breaking

    def pil_field_count(self) -> int:
        """Count non-empty PIL-relevant fields for JSON-LD selection."""
        count = 0
        if self.brand:
            count += 1
        if self.model:
            count += 1
        if self.sku:
            count += 1
        if self.condition:
            count += 1
        if self.size:
            count += 1
        return count


def collect_s1_jsonld(soup: BeautifulSoup) -> list[SourceData]:
    """
    S1: Collect Product objects from JSON-LD scripts.
    Per spec section 9: select object maximizing count(non-empty PIL fields).
    """
    results = []
    scripts = soup.find_all("script", type="application/ld+json")
    
    dom_order = 0
    for script in scripts:
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue
        
        # Handle single object or array
        objects = data if isinstance(data, list) else [data]
        
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            
            # Check for Product type
            obj_type = obj.get("@type", "")
            if isinstance(obj_type, list):
                is_product = "Product" in obj_type
            else:
                is_product = obj_type == "Product"
            
            if not is_product:
                # Check @graph if present
                graph = obj.get("@graph", [])
                for item in graph:
                    if isinstance(item, dict):
                        item_type = item.get("@type", "")
                        if (isinstance(item_type, list) and "Product" in item_type) or item_type == "Product":
                            results.append(_parse_jsonld_product(item, dom_order))
                            dom_order += 1
                continue
            
            results.append(_parse_jsonld_product(obj, dom_order))
            dom_order += 1
    
    return results


def _parse_jsonld_product(obj: dict, dom_order: int) -> SourceData:
    """Parse a JSON-LD Product object into SourceData."""
    source = SourceData("S1")
    source.dom_order = dom_order
    
    # Brand
    brand = obj.get("brand")
    if isinstance(brand, dict):
        source.brand = normalize_text(brand.get("name"))
    elif isinstance(brand, str):
        source.brand = normalize_text(brand)
    
    # Model
    source.model = normalize_text(obj.get("model"))
    
    # SKU - use normalize_sku for SKU-specific path
    sku_raw = obj.get("sku")
    if sku_raw:
        source.sku = normalize_sku(sku_raw)
    
    # Condition
    condition = obj.get("itemCondition", "")
    if isinstance(condition, str):
        source.condition = _normalize_condition(condition)
    
    # Size
    source.size = normalize_text(obj.get("size"))
    
    # Name
    source.name = normalize_text(obj.get("name"))
    
    # Offers presence
    source.offers = "offers" in obj and obj["offers"]
    
    return source


def collect_s2_microdata(soup: BeautifulSoup) -> list[SourceData]:
    """
    S2: Collect Product from Microdata (itemscope/itemtype/itemprop).
    """
    results = []
    
    # Find elements with Product itemtype
    product_scopes = soup.find_all(
        attrs={"itemscope": True, "itemtype": re.compile(r"schema\.org/Product", re.I)}
    )
    
    dom_order = 0
    for scope in product_scopes:
        source = SourceData("S2")
        source.dom_order = dom_order
        
        # Find itemprop values within this scope
        for prop in scope.find_all(attrs={"itemprop": True}):
            prop_name = prop.get("itemprop", "").lower()
            value = prop.get("content") or prop.get_text(strip=True)
            
            if prop_name == "brand":
                source.brand = normalize_text(value)
            elif prop_name == "model":
                source.model = normalize_text(value)
            elif prop_name == "sku":
                source.sku = normalize_sku(value)  # SKU-specific normalization
            elif prop_name == "itemcondition":
                source.condition = _normalize_condition(value)
            elif prop_name == "name":
                source.name = normalize_text(value)
            elif prop_name == "size":
                source.size = normalize_text(value)
        
        results.append(source)
        dom_order += 1
    
    return results


def _normalize_condition(value: str) -> str:
    """Normalize condition values from structured data."""
    value_lower = value.lower()
    if "new" in value_lower:
        return "new"
    elif "refurbished" in value_lower or "renewed" in value_lower:
        return "refurbished"
    elif "used" in value_lower:
        return "used"
    return normalize_text(value)


def collect_s3_meta(soup: BeautifulSoup) -> SourceData:
    """
    S3: Collect product data from meta tags.
    """
    source = SourceData("S3")
    
    # og:title
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        source.name = normalize_text(og_title["content"])
    
    # product:brand
    brand_meta = soup.find("meta", property="product:brand")
    if brand_meta and brand_meta.get("content"):
        source.brand = normalize_text(brand_meta["content"])
    
    # product:condition
    condition_meta = soup.find("meta", property="product:condition")
    if condition_meta and condition_meta.get("content"):
        source.condition = _normalize_condition(condition_meta["content"])
    
    # product:sku - use SKU-specific normalization
    sku_meta = soup.find("meta", property="product:sku")
    if sku_meta and sku_meta.get("content"):
        source.sku = normalize_sku(sku_meta["content"])
    
    return source


def collect_s4_dom_title(title_text: str) -> SourceData:
    """
    S4: Collect product data from visible DOM title.
    """
    source = SourceData("S4")
    source.name = normalize_text(title_text)
    return source


def collect_s5_url_tokens(url: str) -> SourceData:
    """
    S5: Collect tokens from URL.
    
    DELEGATES to url_tokens.extract_url_tokens() - the single source of truth.
    """
    source = SourceData("S5")
    
    # Use canonical URL token extraction from url_tokens.py
    tokens = extract_url_tokens(url)
    
    # Store as combined name
    source.name = " ".join(tokens) if tokens else None
    
    # Check for region in URL path
    parsed = urlparse(url)
    path_parts = unquote(parsed.path).lower().split("/")
    
    for part in path_parts:
        if part in REGION_URL_TOKENS:
            source.region = REGION_URL_TOKENS[part]
            break
    
    return source


def select_best_s1(sources: list[SourceData]) -> Optional[SourceData]:
    """
    Select best JSON-LD product per spec section 9.
    
    Deterministic selection:
    1. Score = count(non-empty PIL fields) - HIGHEST wins
    2. Tie-break: has offers (True wins)
    3. Tie-break: has sku (True wins)
    4. Tie-break: DOM order (FIRST wins)
    """
    if not sources:
        return None
    
    # Sort by: score desc, has_offers desc, has_sku desc, dom_order asc
    def sort_key(s: SourceData):
        return (
            -s.pil_field_count(),
            not s.offers,
            not bool(s.sku),
            s.dom_order,
        )
    
    sorted_sources = sorted(sources, key=sort_key)
    return sorted_sources[0]
