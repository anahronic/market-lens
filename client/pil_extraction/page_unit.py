"""
Page unit selection per DKP-PTL-REG-PIL-EXTRACTION-001 v0.3 sections 2, 7.

Price presence contract:
- A price candidate is valid if it contains digit + currency symbol/code.
- Exactly one price candidate must exist per page unit.

Page unit:
- Product page: full page
- Listing page: LCA(title_node, price_node)

Deterministic tie-breaking:
- Title candidates: h1 > h2 > h3, then DOM order (first wins)
- Price candidates: DOM order (first wins)
- LCA selection: closest to title node (minimum depth)
"""

import re
from typing import Optional, Tuple, List
from bs4 import BeautifulSoup, Tag, NavigableString

from client.pil_extraction.schemas import PageUnitResult
from client.pil_extraction.normalization import normalize_text
from client.pil_extraction.constants import (
    PRICE_REGEX_V1,  # SINGLE SOURCE OF TRUTH for price pattern
    LCA_MAX_DEPTH,
)


def find_price_candidates(element: Tag) -> List[Tag]:
    """
    Find all elements containing valid price candidates.
    A price candidate must contain currency symbol/code and digit.
    
    Uses PRICE_REGEX_V1 from constants.py (single source of truth).
    Returns candidates in DOM order for deterministic tie-breaking.
    """
    candidates = []
    
    # Get all text-bearing elements
    for node in element.descendants:
        if isinstance(node, NavigableString):
            text = str(node).strip()
            if not text:
                continue
            
            # Check if text matches price pattern from constants
            if PRICE_REGEX_V1.search(text):
                # Get the parent element
                parent = node.parent
                if parent and isinstance(parent, Tag):
                    if parent not in candidates:
                        candidates.append(parent)
    
    return candidates


def find_title_candidates(element: Tag) -> List[Tag]:
    """
    Find title candidates in order of preference:
    h1 > h2 > h3 > first significant text element
    """
    candidates = []
    
    # Priority order
    for tag in ["h1", "h2", "h3"]:
        found = element.find_all(tag)
        candidates.extend(found)
        if found:
            break
    
    return candidates


def get_ancestors(element: Tag) -> List[Tag]:
    """Get list of ancestors from element to root."""
    ancestors = []
    current = element.parent
    while current and isinstance(current, Tag):
        ancestors.append(current)
        current = current.parent
    return ancestors


def find_lca(node_a: Tag, node_b: Tag) -> Optional[Tag]:
    """
    Find Lowest Common Ancestor of two nodes.
    """
    if node_a == node_b:
        return node_a
    
    # Get ancestors of both
    ancestors_a = set(get_ancestors(node_a))
    ancestors_a.add(node_a)
    
    # Walk up from node_b until we find common ancestor
    current = node_b
    while current:
        if current in ancestors_a:
            return current
        current = current.parent if hasattr(current, 'parent') else None
    
    return None


def depth_from(ancestor: Tag, descendant: Tag) -> int:
    """Count depth from ancestor to descendant."""
    depth = 0
    current = descendant
    while current and current != ancestor:
        depth += 1
        current = current.parent if hasattr(current, 'parent') else None
    return depth


def select_page_unit(soup: BeautifulSoup) -> PageUnitResult:
    """
    Select page unit per spec section 7.
    
    For listing pages: LCA(title_node, price_node)
    Constraints:
    - LCA depth must not exceed 10 levels above title node
    - If multiple LCAs exist, choose closest to title node
    - Exactly one price candidate must exist in the page unit
    """
    body = soup.find("body")
    if not body:
        return PageUnitResult(success=False, failure_reason="no_body")
    
    # Find title candidates
    title_candidates = find_title_candidates(body)
    if not title_candidates:
        return PageUnitResult(success=False, failure_reason="no_title")
    
    # Find price candidates in entire body
    all_price_candidates = find_price_candidates(body)
    
    if not all_price_candidates:
        return PageUnitResult(success=False, failure_reason="no_price")
    
    # Try to find valid page unit for first title
    title_node = title_candidates[0]
    
    # Find LCA for each price candidate
    best_lca = None
    best_price = None
    best_depth = float('inf')
    
    for price_node in all_price_candidates:
        lca = find_lca(title_node, price_node)
        if lca is None:
            continue
        
        # Check depth constraint
        title_depth = depth_from(lca, title_node)
        if title_depth > LCA_MAX_DEPTH:
            continue
        
        # Prefer closest LCA to title
        if title_depth < best_depth:
            best_depth = title_depth
            best_lca = lca
            best_price = price_node
    
    if best_lca is None:
        return PageUnitResult(success=False, failure_reason="no_valid_lca")
    
    # Count price candidates within the LCA
    prices_in_lca = find_price_candidates(best_lca)
    
    if len(prices_in_lca) == 0:
        return PageUnitResult(success=False, failure_reason="no_price_in_unit")
    
    if len(prices_in_lca) > 1:
        return PageUnitResult(success=False, failure_reason="multiple_prices")
    
    return PageUnitResult(
        success=True,
        title_node=title_node,
        price_node=best_price,
        lca_root=best_lca,
    )


def has_valid_price(element: Tag) -> bool:
    """Check if element or its descendants contain exactly one valid price."""
    prices = find_price_candidates(element)
    return len(prices) == 1


def get_title_text(page_unit: PageUnitResult) -> str:
    """Extract text from title node."""
    if page_unit.title_node is None:
        return ""
    return page_unit.title_node.get_text(strip=True)
