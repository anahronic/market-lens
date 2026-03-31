/**
 * DOM Capture Module per Phase 11 spec section 3.2.
 *
 * Captures page unit for PIL extraction without sending raw HTML externally.
 *
 * Functions:
 * - capture_page_unit(): Returns HTML, URL, timestamp
 */

import type { DOMCaptureResult, PageUnitResult } from '../types/index.js';
import { PRICE_REGEX_V1, LCA_MAX_DEPTH } from './constants.js';

/**
 * Find all elements containing price candidates.
 *
 * @param root - Root element to search
 * @returns Array of elements containing price text
 */
function findPriceElements(root: Element): Element[] {
  const priceElements: Element[] = [];

  // Walk the DOM looking for text nodes with price patterns
  const walker = document.createTreeWalker(
    root,
    NodeFilter.SHOW_TEXT,
    null
  );

  const seen = new Set<Element>();
  let node: Text | null;

  while ((node = walker.nextNode() as Text | null)) {
    const text = node.textContent || '';
    // Reset regex state
    PRICE_REGEX_V1.lastIndex = 0;
    
    if (PRICE_REGEX_V1.test(text)) {
      const parent = node.parentElement;
      if (parent && !seen.has(parent)) {
        priceElements.push(parent);
        seen.add(parent);
      }
    }
  }

  return priceElements;
}

/**
 * Find the most likely title element within a container.
 *
 * @param root - Root element to search
 * @returns Title element or null
 */
function findTitleElement(root: Element): Element | null {
  // Priority: h1 > h2 > h3 > [itemprop="name"] > .product-title > .title
  const selectors = [
    'h1',
    '[itemprop="name"]',
    'h2',
    '.product-title',
    '.product-name',
    '[data-testid="product-title"]',
    '.title',
    'h3',
  ];

  for (const selector of selectors) {
    const el = root.querySelector(selector);
    if (el && el.textContent?.trim()) {
      return el;
    }
  }

  return null;
}

/**
 * Find Lowest Common Ancestor of two elements.
 *
 * @param el1 - First element
 * @param el2 - Second element
 * @param maxDepth - Maximum depth to traverse up from el1
 * @returns LCA element or null if exceeded depth
 */
function findLCA(el1: Element, el2: Element, maxDepth: number): Element | null {
  // Get ancestors of el1 up to maxDepth
  const ancestors1 = new Set<Element>();
  let current: Element | null = el1;
  let depth = 0;

  while (current && depth <= maxDepth) {
    ancestors1.add(current);
    current = current.parentElement;
    depth++;
  }

  // Walk up from el2 until we find a common ancestor
  current = el2;
  while (current) {
    if (ancestors1.has(current)) {
      return current;
    }
    current = current.parentElement;
  }

  return null;
}

/**
 * Select page unit (LCA of title and price nodes).
 * Per spec section 7.
 *
 * @returns PageUnitResult with success status and elements
 */
export function selectPageUnit(): PageUnitResult {
  const body = document.body;
  if (!body) {
    return {
      success: false,
      failure_reason: 'no_title',
    };
  }

  // Find price elements
  const priceElements = findPriceElements(body);

  if (priceElements.length === 0) {
    return {
      success: false,
      failure_reason: 'no_price',
    };
  }

  if (priceElements.length > 1) {
    // Multiple prices - need to determine if they're for same product
    // For MVP, we check if they're within same container
    // If truly multiple distinct prices -> reject
    const uniquePrices = new Set<string>();
    for (const el of priceElements) {
      const text = el.textContent || '';
      PRICE_REGEX_V1.lastIndex = 0;
      const match = PRICE_REGEX_V1.exec(text);
      if (match) {
        // Normalize: remove spaces/commas, extract number
        const normalized = match[0].replace(/[,\s]/g, '');
        uniquePrices.add(normalized);
      }
    }

    if (uniquePrices.size > 1) {
      return {
        success: false,
        failure_reason: 'multiple_prices',
      };
    }
  }

  // Find title element
  const titleElement = findTitleElement(body);
  if (!titleElement) {
    return {
      success: false,
      failure_reason: 'no_title',
    };
  }

  // Find LCA
  const priceElement = priceElements[0];
  const lca = findLCA(titleElement, priceElement, LCA_MAX_DEPTH);

  if (!lca) {
    return {
      success: false,
      failure_reason: 'lca_exceeded',
    };
  }

  return {
    success: true,
    element: lca,
    title_element: titleElement,
    price_element: priceElement,
  };
}

/**
 * Capture page unit for PIL extraction.
 *
 * Returns:
 * - HTML of the page unit (LCA node)
 * - Current URL
 * - Timestamp (UTC)
 *
 * @returns DOMCaptureResult
 */
export function capturePageUnit(): DOMCaptureResult {
  const pageUnit = selectPageUnit();

  let html: string;
  if (pageUnit.success && pageUnit.element) {
    html = pageUnit.element.outerHTML;
  } else {
    // Fallback to full body
    html = document.body?.outerHTML || '';
  }

  return {
    html,
    url: window.location.href,
    timestamp: Math.floor(Date.now() / 1000),
  };
}

/**
 * Get visible text from title element.
 *
 * @param pageUnit - Page unit result with title element
 * @returns Normalized title text
 */
export function getTitleText(pageUnit: PageUnitResult): string {
  if (!pageUnit.success || !pageUnit.title_element) {
    return '';
  }
  return pageUnit.title_element.textContent?.trim() || '';
}

/**
 * Get full document HTML for PIL extraction.
 * Note: This is for local processing only - never sent to server.
 *
 * @returns Full page HTML
 */
export function getFullPageHTML(): string {
  return document.documentElement.outerHTML;
}
