/**
 * PIL Extraction Module per DKP-PTL-REG-PIL-EXTRACTION-001 v0.3.
 *
 * EXTRACTION PIPELINE:
 * 1. Parse HTML
 * 2. Collect sources S1-S5
 * 3. Select page unit (with deterministic tie-breaking)
 * 4. Extract title from page unit
 * 5. Run conflict detection
 * 6. Parse all fields following precedence rules
 * 7. Apply validity gate
 * 8. Build and return result
 *
 * PRECEDENCE MODEL (per spec):
 * - Field-wise precedence: S1 > S2 > S3 > S4 > S5
 * - For each field, use the highest-precedence source that provides it
 *
 * TypeScript port of client/pil_extraction/extractor.py
 */

import type {
  PILObject,
  PILExtractionResult,
  PILExtractionStatus,
  SourceData,
  PageUnitResult,
} from '../types/index.js';
import { normalizeText, normalizeForDisplay, extractTokens, extractLatinTokens } from './normalize.js';
import {
  DICTIONARY_NOISE_V1,
  MIN_C_EXTRACT,
  PRICE_REGEX_V1,
  STORAGE_REGEX_V1,
  RELEASE_YEAR_MIN,
  NON_BRAND_TOKENS,
  URL_PATH_NOISE,
  URL_MAX_TOKENS,
  CONDITION_PHRASES,
  CONDITION_SYNONYMS,
  BUNDLE_KEYWORDS,
  BUNDLE_PHRASES,
  WARRANTY_KEYWORDS,
  REGION_URL_TOKENS,
} from './constants.js';

// Valid statuses for output contract
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const VALID_STATUSES: ReadonlySet<PILExtractionStatus> = new Set([
  'OK',
  'NO_MATCH',
  'INSUFFICIENT_IDENTITY',
  'CONFLICT_BLOCKED',
  'INVALID_PAGE_UNIT',
]);

/**
 * Collect S1 (JSON-LD) product data.
 */
function collectS1JsonLd(doc: Document): SourceData[] {
  const results: SourceData[] = [];
  const scripts = doc.querySelectorAll('script[type="application/ld+json"]');

  for (const script of scripts) {
    try {
      const data = JSON.parse(script.textContent || '');
      const products = extractProductsFromJsonLd(data);
      results.push(...products);
    } catch {
      // Invalid JSON, skip
    }
  }

  return results;
}

function extractProductsFromJsonLd(data: unknown): SourceData[] {
  const results: SourceData[] = [];

  if (!data || typeof data !== 'object') {
    return results;
  }

  const obj = data as Record<string, unknown>;

  // Check if this is a Product
  if (obj['@type'] === 'Product') {
    results.push(parseProductObject(obj));
  }

  // Check @graph
  if (Array.isArray(obj['@graph'])) {
    for (const item of obj['@graph']) {
      if (item && typeof item === 'object' && (item as Record<string, unknown>)['@type'] === 'Product') {
        results.push(parseProductObject(item as Record<string, unknown>));
      }
    }
  }

  // Check if array of products
  if (Array.isArray(data)) {
    for (const item of data) {
      if (item && typeof item === 'object' && (item as Record<string, unknown>)['@type'] === 'Product') {
        results.push(parseProductObject(item as Record<string, unknown>));
      }
    }
  }

  return results;
}

function parseProductObject(obj: Record<string, unknown>): SourceData {
  const brand = extractBrandFromJsonLd(obj);
  const model = getString(obj, 'model');
  const name = getString(obj, 'name');
  const sku = getString(obj, 'sku');
  const condition = extractConditionFromJsonLd(obj);
  const size = getString(obj, 'size');
  const hasOffers = obj['offers'] !== undefined;

  return { brand, model, name, sku, condition, size, has_offers: hasOffers };
}

function extractBrandFromJsonLd(obj: Record<string, unknown>): string | null {
  const brand = obj['brand'];
  if (typeof brand === 'string') {
    return normalizeText(brand);
  }
  if (brand && typeof brand === 'object') {
    return normalizeText(getString(brand as Record<string, unknown>, 'name'));
  }
  return null;
}

function extractConditionFromJsonLd(obj: Record<string, unknown>): string | null {
  const condition = obj['itemCondition'] || obj['condition'];
  if (typeof condition === 'string') {
    // Normalize schema.org condition URLs
    const lc = condition.toLowerCase();
    if (lc.includes('newcondition') || lc === 'new') return 'new';
    if (lc.includes('refurbished')) return 'refurbished';
    if (lc.includes('used')) return 'used';
    return normalizeText(condition);
  }
  return null;
}

function getString(obj: Record<string, unknown>, key: string): string | null {
  const val = obj[key];
  if (typeof val === 'string' && val.trim()) {
    return normalizeText(val);
  }
  return null;
}

/**
 * Collect S2 (Microdata) product data.
 */
function collectS2Microdata(doc: Document): SourceData[] {
  const results: SourceData[] = [];
  const products = doc.querySelectorAll('[itemtype*="schema.org/Product"]');

  for (const product of products) {
    const brand = getItemprop(product, 'brand');
    const model = getItemprop(product, 'model');
    const name = getItemprop(product, 'name');
    const sku = getItemprop(product, 'sku');
    const condition = getItemprop(product, 'itemCondition');
    const size = getItemprop(product, 'size');
    const hasOffers = product.querySelector('[itemprop="offers"]') !== null;

    results.push({
      brand: brand ? normalizeText(brand) : null,
      model: model ? normalizeText(model) : null,
      name: name ? normalizeText(name) : null,
      sku: sku ? normalizeText(sku) : null,
      condition: condition ? normalizeText(condition) : null,
      size: size ? normalizeText(size) : null,
      has_offers: hasOffers,
    });
  }

  return results;
}

function getItemprop(container: Element, prop: string): string | null {
  const el = container.querySelector(`[itemprop="${prop}"]`);
  if (!el) return null;

  // Check content attribute first
  const content = el.getAttribute('content');
  if (content) return content;

  // Then text content
  return el.textContent?.trim() || null;
}

/**
 * Collect S3 (Meta tags) product data.
 */
function collectS3Meta(doc: Document): SourceData {
  const getMeta = (names: string[]): string | null => {
    for (const name of names) {
      const el = doc.querySelector(`meta[property="${name}"], meta[name="${name}"]`);
      if (el) {
        const content = el.getAttribute('content');
        if (content?.trim()) return normalizeText(content);
      }
    }
    return null;
  };

  return {
    brand: getMeta(['product:brand', 'og:brand']),
    model: getMeta(['product:model']),
    name: getMeta(['og:title', 'twitter:title']),
    sku: getMeta(['product:sku']),
    condition: getMeta(['product:condition']),
    size: getMeta(['product:size']),
    has_offers: false,
  };
}

/**
 * Select best S1 source per spec section 9.
 * Select object maximizing: count(non-empty PIL fields)
 * Tie-break: has offers > has sku > DOM order
 */
function selectBestS1(sources: SourceData[]): SourceData | null {
  if (sources.length === 0) return null;
  if (sources.length === 1) return sources[0];

  // Score each source
  const scored = sources.map((s, idx) => ({
    source: s,
    index: idx,
    fieldCount: countNonEmptyFields(s),
  }));

  // Sort by: fieldCount desc, has_offers desc, has_sku desc, index asc
  scored.sort((a, b) => {
    if (b.fieldCount !== a.fieldCount) return b.fieldCount - a.fieldCount;
    if (b.source.has_offers !== a.source.has_offers) return b.source.has_offers ? 1 : -1;
    if ((b.source.sku !== null) !== (a.source.sku !== null)) return b.source.sku !== null ? 1 : -1;
    return a.index - b.index;
  });

  return scored[0].source;
}

function countNonEmptyFields(s: SourceData): number {
  let count = 0;
  if (s.brand) count++;
  if (s.model) count++;
  if (s.name) count++;
  if (s.sku) count++;
  if (s.condition) count++;
  if (s.size) count++;
  return count;
}

/**
 * Extract URL tokens per spec section 11.
 */
function extractUrlTokens(url: string): string[] {
  try {
    const parsed = new URL(url);
    const path = parsed.pathname;

    // Split path into segments
    const segments = path
      .split('/')
      .filter((s) => s.length > 0)
      .filter((s) => !URL_PATH_NOISE.has(s.toLowerCase()));

    // Take last segment and split by hyphens
    if (segments.length === 0) return [];

    const lastSegment = segments[segments.length - 1];
    const tokens = lastSegment
      .split(/[-_]/)
      .map((t) => normalizeText(t))
      .filter((t) => t.length > 0)
      .slice(0, URL_MAX_TOKENS);

    return tokens;
  } catch {
    return [];
  }
}

/**
 * Find title element in DOM.
 */
function findTitleElement(doc: Document): Element | null {
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
    const el = doc.querySelector(selector);
    if (el && el.textContent?.trim()) {
      return el;
    }
  }

  return null;
}

/**
 * Find price elements in DOM.
 */
function findPriceElements(doc: Document): Element[] {
  const priceElements: Element[] = [];
  const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT, null);

  const seen = new Set<Element>();
  let node: Text | null;

  while ((node = walker.nextNode() as Text | null)) {
    const text = node.textContent || '';
    const regex = new RegExp(PRICE_REGEX_V1.source, PRICE_REGEX_V1.flags);

    if (regex.test(text)) {
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
 * Get depth (distance from root) of an element.
 */
function getElementDepth(element: Element): number {
  let depth = 0;
  let current: Node | null = element;
  while (current && current.parentNode) {
    depth++;
    current = current.parentNode;
  }
  return depth;
}

/**
 * Get path from element to root as array of nodes.
 */
function getPathToRoot(element: Element, maxDepth: number = 10): Element[] {
  const path: Element[] = [];
  let current: Element | null = element;
  
  while (current && path.length < maxDepth) {
    path.push(current);
    current = current.parentElement;
  }
  
  return path;
}

/**
 * Find Lowest Common Ancestor of two elements.
 * Max depth: 10 levels.
 * 
 * @param elem1 - First element (title)
 * @param elem2 - Second element (price)
 * @returns LCA element or null if not found within maxDepth
 */
function findLCA(elem1: Element, elem2: Element): Element | null {
  const MAX_DEPTH = 10;
  
  const path1 = getPathToRoot(elem1, MAX_DEPTH);
  const path2Set = new Set(getPathToRoot(elem2, MAX_DEPTH));
  
  // Find first common ancestor (closest to elem1)
  for (const node of path1) {
    if (path2Set.has(node)) {
      return node;
    }
  }
  
  return null;
}

/**
 * Count price elements within a subtree.
 */
function countPricesInSubtree(root: Element): number {
  const text = root.textContent || '';
  const regex = new RegExp(PRICE_REGEX_V1.source, 'gi');
  const matches = text.match(regex) || [];
  
  // Count unique price values
  const uniquePrices = new Set<string>();
  for (const match of matches) {
    const normalized = match.replace(/[,\s]/g, '').toLowerCase();
    uniquePrices.add(normalized);
  }
  
  return uniquePrices.size;
}

/**
 * Select page unit per spec section 7.
 * Uses LCA (Lowest Common Ancestor) to scope price/title to product cards.
 * 
 * For listing pages, finds the smallest subtree containing both title and price
 * with exactly one unique price.
 */
function selectPageUnit(doc: Document): PageUnitResult {
  const titleElement = findTitleElement(doc);
  if (!titleElement) {
    return { success: false, failure_reason: 'no_title' };
  }

  const priceElements = findPriceElements(doc);
  if (priceElements.length === 0) {
    return { success: false, failure_reason: 'no_price' };
  }

  // For each price element, find LCA with title and check price count within
  let bestResult: { lca: Element; price: Element; depth: number } | null = null;

  for (const priceEl of priceElements) {
    const lca = findLCA(titleElement, priceEl);
    if (!lca) continue;

    // Count unique prices within this LCA subtree
    const priceCount = countPricesInSubtree(lca);
    
    // Only accept if exactly one price in the subtree
    if (priceCount === 1) {
      const depth = getElementDepth(lca);
      
      // Choose deepest (most specific) LCA
      if (!bestResult || depth > bestResult.depth) {
        bestResult = { lca, price: priceEl, depth };
      }
    }
  }

  // If no valid LCA found, fall back to checking entire document
  if (!bestResult) {
    // Check if entire page has multiple distinct prices
    const allText = doc.body?.textContent || '';
    const regex = new RegExp(PRICE_REGEX_V1.source, 'gi');
    const matches = allText.match(regex) || [];
    
    const uniquePrices = new Set<string>();
    for (const match of matches) {
      const normalized = match.replace(/[,\s]/g, '').toLowerCase();
      uniquePrices.add(normalized);
    }

    if (uniquePrices.size > 1) {
      return { success: false, failure_reason: 'multiple_prices' };
    }

    // Single price in document, use first price element
    return {
      success: true,
      element: doc.body,
      title_element: titleElement,
      price_element: priceElements[0],
    };
  }

  return {
    success: true,
    element: bestResult.lca,
    title_element: titleElement,
    price_element: bestResult.price,
  };
}

/**
 * Parse brand from sources.
 * Handles multi-script text (e.g., Hebrew + Latin).
 */
function parseBrand(
  s1Brand: string | null,
  s2Brand: string | null,
  s3Brand: string | null,
  titleText: string,
  urlTokens: string[]
): string {
  // S1 > S2 > S3 precedence - only use structured data for brand
  if (s1Brand) return s1Brand;
  if (s2Brand) return s2Brand;
  if (s3Brand) return s3Brand;

  // Check URL first token against title (must be exact match at start)
  if (urlTokens.length > 0) {
    const firstToken = urlTokens[0];
    if (!NON_BRAND_TOKENS.has(firstToken) && !DICTIONARY_NOISE_V1.has(firstToken)) {
      const normalizedTitle = normalizeForDisplay(titleText);
      if (normalizedTitle.startsWith(firstToken + ' ')) {
        return firstToken;
      }
    }
  }

  // Multi-script: extract Latin brand from mixed text
  // e.g., "שואב Dreame L10S" -> "dreame"
  const hasNonLatin = /[^\x00-\x7F]/.test(titleText);
  if (hasNonLatin) {
    const latinTokens = extractLatinTokens(titleText);
    if (latinTokens.length > 0) {
      const brandCandidate = latinTokens[0];
      // Validate: at least 2 chars, not noise, and appears in URL tokens
      if (brandCandidate.length >= 2 && 
          !NON_BRAND_TOKENS.has(brandCandidate) &&
          !DICTIONARY_NOISE_V1.has(brandCandidate) &&
          urlTokens.includes(brandCandidate)) {
        return brandCandidate;
      }
    }
  }

  // NO brand extraction from title alone without structured/URL confirmation
  // This prevents listing pages from incorrectly extracting brand
  return '';
}

/**
 * Extract model from title text (S4 source) without brand prefix.
 * Used for conflict detection.
 */
function extractModelFromTitle(titleText: string, brand: string): string {
  let normalized = normalizeForDisplay(titleText);

  // Remove brand prefix if exists
  if (brand && normalized.startsWith(brand + ' ')) {
    normalized = normalized.slice(brand.length + 1);
  }

  // Remove noise tokens and price patterns
  const tokens = extractTokens(normalized);
  const cleanTokens = tokens.filter((t) => {
    if (DICTIONARY_NOISE_V1.has(t)) return false;
    const priceRegex = new RegExp(PRICE_REGEX_V1.source, PRICE_REGEX_V1.flags);
    if (priceRegex.test(t)) return false;
    return true;
  });

  if (cleanTokens.length === 0) return '';
  return cleanTokens.join(' ');
}

/**
 * Parse model from sources.
 * Handles multi-script text (e.g., Hebrew + Latin model identifiers).
 */
function parseModel(
  s1Model: string | null,
  s2Model: string | null,
  s3Model: string | null,
  titleText: string,
  brand: string
): string {
  // S1 > S2 > S3 precedence
  if (s1Model) return s1Model;
  if (s2Model) return s2Model;
  if (s3Model) return s3Model;

  // Check if text contains non-Latin characters
  const hasNonLatin = /[^\x00-\x7F]/.test(titleText);
  
  // For multi-script text, extract ONLY Latin tokens
  if (hasNonLatin) {
    const latinTokens = extractLatinTokens(titleText);
    // Remove brand from tokens
    const modelTokens = latinTokens.filter(t => t !== brand && !DICTIONARY_NOISE_V1.has(t));
    if (modelTokens.length > 0) {
      return modelTokens.join(' ');
    }
    return '';
  }

  // For Latin-only text, use standard extraction
  let normalized = normalizeForDisplay(titleText);

  // Remove brand prefix if exists
  if (brand && normalized.startsWith(brand + ' ')) {
    normalized = normalized.slice(brand.length + 1);
  }

  // Remove noise tokens and price patterns
  const tokens = extractTokens(normalized);
  const cleanTokens = tokens.filter((t) => {
    if (DICTIONARY_NOISE_V1.has(t)) return false;
    // Check if token is a price
    const priceRegex = new RegExp(PRICE_REGEX_V1.source, PRICE_REGEX_V1.flags);
    if (priceRegex.test(t)) return false;
    return true;
  });

  if (cleanTokens.length > 0) {
    const model = cleanTokens.join(' ');
    // Validate: must contain alphabetic char
    if (/[a-z]/.test(model)) {
      return model;
    }
  }

  return '';
}

/**
 * Parse SKU from sources.
 */
function parseSku(
  s1Sku: string | null,
  s2Sku: string | null,
  s3Sku: string | null
): string {
  // S1 > S2 > S3 precedence (no ampersand transform for SKU)
  if (s1Sku) return normalizeText(s1Sku) || '';
  if (s2Sku) return normalizeText(s2Sku) || '';
  if (s3Sku) return normalizeText(s3Sku) || '';
  return '';
}

/**
 * Parse condition from sources.
 */
function parseCondition(
  s1Condition: string | null,
  s2Condition: string | null,
  s3Condition: string | null,
  titleText: string
): string {
  // S1 > S2 > S3 precedence
  for (const cond of [s1Condition, s2Condition, s3Condition]) {
    if (cond) {
      const normalized = normalizeText(cond);
      if (CONDITION_SYNONYMS[normalized]) {
        return CONDITION_SYNONYMS[normalized];
      }
    }
  }

  // Check title for condition phrases
  const normalizedTitle = normalizeForDisplay(titleText);

  for (const [phrase, canonical] of CONDITION_PHRASES) {
    if (normalizedTitle.includes(phrase)) {
      return canonical;
    }
  }

  // Check single words
  const tokens = extractTokens(normalizedTitle);
  for (const token of tokens) {
    if (CONDITION_SYNONYMS[token]) {
      return CONDITION_SYNONYMS[token];
    }
  }

  return '';
}

/**
 * Parse bundle flag.
 */
function parseBundleFlag(titleText: string, s1Name: string | null): string {
  const normalized = normalizeForDisplay(titleText);
  const s1Normalized = s1Name ? normalizeForDisplay(s1Name) : '';

  // Check for bundle keywords
  const tokens = extractTokens(normalized);
  for (const token of tokens) {
    if (BUNDLE_KEYWORDS.has(token)) {
      return 'bundle';
    }
  }

  // Check S1 name
  const s1Tokens = extractTokens(s1Normalized);
  for (const token of s1Tokens) {
    if (BUNDLE_KEYWORDS.has(token)) {
      return 'bundle';
    }
  }

  // Check for bundle phrases
  for (const phrase of BUNDLE_PHRASES) {
    if (normalized.includes(phrase) || s1Normalized.includes(phrase)) {
      return 'bundle';
    }
  }

  return 'standalone';
}

/**
 * Parse warranty type.
 */
function parseWarrantyType(titleText: string): string {
  const normalized = normalizeForDisplay(titleText);

  for (const [phrase, canonical] of Object.entries(WARRANTY_KEYWORDS)) {
    if (normalized.includes(phrase)) {
      return canonical;
    }
  }

  return '';
}

/**
 * Parse region variant from URL.
 */
function parseRegionVariant(url: string): string {
  try {
    const parsed = new URL(url);
    const hostname = parsed.hostname.toLowerCase();
    const path = parsed.pathname.toLowerCase();

    // Check hostname TLD
    if (hostname.endsWith('.il')) return 'il';
    if (hostname.endsWith('.co.uk') || hostname.endsWith('.uk')) return 'uk';

    // Check path tokens
    for (const [token, region] of Object.entries(REGION_URL_TOKENS)) {
      if (path.includes('/' + token + '/') || path.includes('/' + token)) {
        return region;
      }
    }
  } catch {
    // Invalid URL
  }

  return '';
}

/**
 * Parse storage/size.
 */
function parseStorageOrSize(
  s1Size: string | null,
  s2Size: string | null,
  titleText: string
): string {
  // S1 > S2 precedence
  if (s1Size) {
    const normalized = normalizeForDisplay(s1Size);
    if (STORAGE_REGEX_V1.test(normalized)) {
      return normalized;
    }
  }

  if (s2Size) {
    const normalized = normalizeForDisplay(s2Size);
    if (STORAGE_REGEX_V1.test(normalized)) {
      return normalized;
    }
  }

  // Extract from title
  const normalized = normalizeForDisplay(titleText);
  const regex = new RegExp(STORAGE_REGEX_V1.source, STORAGE_REGEX_V1.flags);
  const match = regex.exec(normalized);

  if (match) {
    return match[0].toLowerCase();
  }

  return '';
}

/**
 * Parse release year.
 */
function parseReleaseYear(titleText: string, utcYear: number): string {
  const normalized = normalizeForDisplay(titleText);
  const yearRegex = /\b(19[7-9]\d|20[0-9]\d)\b/g;

  const matches: number[] = [];
  let match: RegExpExecArray | null;

  while ((match = yearRegex.exec(normalized)) !== null) {
    const year = parseInt(match[1], 10);
    if (year >= RELEASE_YEAR_MIN && year <= utcYear + 2) {
      matches.push(year);
    }
  }

  if (matches.length === 1) {
    return matches[0].toString();
  }

  return '';
}

/**
 * Count C_extract for validity gate.
 */
function countCExtract(brand: string, model: string, sku: string): number {
  let count = 0;
  if (brand) count += 1;
  if (model) count += model.split(' ').length;
  if (sku) count += 1;
  return count;
}

/**
 * Main extraction function.
 *
 * @param html - Raw HTML string
 * @param url - Page URL
 * @param utcYear - Current UTC year for release year validation
 * @returns PILExtractionResult
 */
export function extractPilFromHtml(
  html: string,
  url: string,
  utcYear: number
): PILExtractionResult {
  // Parse HTML
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, 'text/html');

  // Collect sources S1-S5
  const s1List = collectS1JsonLd(doc);
  const s1 = selectBestS1(s1List);

  const s2List = collectS2Microdata(doc);
  const s2 = s2List.length > 0 ? s2List[0] : null;

  const s3 = collectS3Meta(doc);

  // Select page unit
  const pageUnit = selectPageUnit(doc);

  if (!pageUnit.success) {
    if (pageUnit.failure_reason === 'multiple_prices') {
      return { pil_extraction_status: 'INVALID_PAGE_UNIT' };
    }
    if (pageUnit.failure_reason === 'no_price' || pageUnit.failure_reason === 'no_title') {
      return { pil_extraction_status: 'NO_MATCH' };
    }
    return { pil_extraction_status: 'INVALID_PAGE_UNIT' };
  }

  // Extract title
  const titleText = pageUnit.title_element?.textContent?.trim() || '';

  // URL tokens (S5)
  const urlTokens = extractUrlTokens(url);

  // CONFLICT DETECTION: Check S1.model vs S4 (visible title) model
  // Per spec: if S1.model ≠ S4.model after normalization → CONFLICT_BLOCKED
  if (s1?.model) {
    const s1Model = normalizeForDisplay(s1.model);
    const s4ModelRaw = extractModelFromTitle(titleText, '');
    const s4Model = normalizeForDisplay(s4ModelRaw);
    
    // Check if both are non-empty and different
    if (s1Model && s4Model && s1Model !== s4Model) {
      // Check for core identity conflict (not just different detail levels)
      // e.g., "EOS R6" vs "EOS R5" is a conflict
      // but "iPhone 13" vs "iPhone 13 128GB" is not
      if (!s4Model.includes(s1Model) && !s1Model.includes(s4Model)) {
        return { pil_extraction_status: 'CONFLICT_BLOCKED' };
      }
    }
  }

  // Parse all fields with precedence
  const brand = parseBrand(
    s1?.brand || null,
    s2?.brand || null,
    s3.brand,
    titleText,
    urlTokens
  );

  const model = parseModel(
    s1?.model || null,
    s2?.model || null,
    s3.model,
    titleText,
    brand
  );

  const sku = parseSku(
    s1?.sku || null,
    s2?.sku || null,
    s3.sku
  );

  const condition = parseCondition(
    s1?.condition || null,
    s2?.condition || null,
    s3.condition,
    titleText
  );

  const bundleFlag = parseBundleFlag(titleText, s1?.name || null);
  const warrantyType = parseWarrantyType(titleText);
  const regionVariant = parseRegionVariant(url);
  const storageOrSize = parseStorageOrSize(s1?.size || null, s2?.size || null, titleText);
  const releaseYear = parseReleaseYear(titleText, utcYear);

  // Validity gate
  if (!model) {
    return { pil_extraction_status: 'INSUFFICIENT_IDENTITY' };
  }

  const cExtract = countCExtract(brand, model, sku);
  if (cExtract < MIN_C_EXTRACT) {
    return { pil_extraction_status: 'INSUFFICIENT_IDENTITY' };
  }

  // Build result
  const pil: PILObject = {
    brand,
    model,
    sku,
    condition,
    bundle_flag: bundleFlag,
    warranty_type: warrantyType,
    region_variant: regionVariant,
    storage_or_size: storageOrSize,
    release_year: releaseYear,
  };

  return {
    pil_extraction_status: 'OK',
    PIL: pil,
  };
}
