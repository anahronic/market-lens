/**
 * Version-locked constants per DKP-PTL-REG-PIL-EXTRACTION-001 v0.3
 * All constants MUST be immutable and version-bound.
 * 
 * TypeScript port of client/pil_extraction/constants.py
 * This module maintains EXACT behavioral equivalence with the Python implementation.
 */

/** Specification version */
export const PIL_EXTRACTION_VERSION = '0.3';

/** Protocol version */
export const PROTOCOL_VERSION = '0.6.0';

/**
 * DICTIONARY_NOISE_v1 per spec section 19.
 * These tokens are removed from model parsing.
 */
export const DICTIONARY_NOISE_V1: ReadonlySet<string> = new Set([
  'new',
  'sale',
  'best',
  'free',
  'shipping',
  'deal',
  'discount',
  'promo',
  'item',
  'product',
]);

/**
 * Price regex per spec section 2.
 * CANONICAL PATTERN: currency symbol/code must be present + digits
 * Supports currency before OR after the number.
 * 
 * Pattern: ([₪$€£]|USD|ILS|EUR|GBP)?\s?[0-9]{1,3}([,\s][0-9]{3})*(\.[0-9]{1,2})?
 */
export const PRICE_REGEX_V1 = /([₪$€£]|USD|ILS|EUR|GBP)\s*[0-9]{1,3}(?:[,\s][0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]{1,3}(?:[,\s][0-9]{3})*(?:\.[0-9]{1,2})?\s*([₪$€£]|USD|ILS|EUR|GBP)/gi;

/** Currency symbols set */
export const CURRENCY_SYMBOLS: ReadonlySet<string> = new Set(['₪', '$', '€', '£']);

/** Currency ISO codes */
export const CURRENCY_CODES: ReadonlySet<string> = new Set(['USD', 'ILS', 'EUR', 'GBP']);

/** Currency symbol to code mapping */
export const CURRENCY_SYMBOL_TO_CODE: Readonly<Record<string, string>> = {
  '₪': 'ILS',
  '$': 'USD',
  '€': 'EUR',
  '£': 'GBP',
};

/**
 * Storage/size regex per spec section 12.9.
 * Pattern: [0-9]+(gb|tb|w|cm|inch)
 */
export const STORAGE_REGEX_V1 = /([0-9]+)(gb|tb|w|cm|inch)/gi;

/**
 * Tokenization regex per spec section 12.1.
 * Split by [\s,|()[\]]+
 */
export const TOKENIZE_REGEX = /[\s,|()\[\]]+/;

/**
 * Allowed chars after normalization per spec section 8.
 * Pattern: [a-z0-9 \-/+.&]
 */
export const ALLOWED_CHARS_REGEX = /[^a-z0-9 \-/+.&]/g;

/** Model constraints per spec section 12.3 */
export const MODEL_MAX_BYTES = 128;

/** Release year bounds per spec section 12.10 */
export const RELEASE_YEAR_MIN = 1970;

/** LCA depth bound per spec section 7.2 */
export const LCA_MAX_DEPTH = 10;

/** URL token limit per spec section 11 */
export const URL_MAX_TOKENS = 3;

/** Validity gate minimum C_extract per spec section 13 */
export const MIN_C_EXTRACT = 2;

/**
 * Non-brand tokens: these appear in URL but are product line names, not manufacturers.
 * Per test vectors, these should NOT be extracted as brand even if in URL.
 */
export const NON_BRAND_TOKENS: ReadonlySet<string> = new Set([
  'steam',       // Steam Deck is by Valve
  'macbook',     // MacBook is by Apple
  'iphone',      // iPhone is by Apple
  'ipad',        // iPad is by Apple
  'galaxy',      // Galaxy is by Samsung
  'pixel',       // Pixel is by Google
  'surface',     // Surface is by Microsoft
  'thinkpad',    // ThinkPad is by Lenovo
  'playstation', // PlayStation is by Sony
  'xbox',        // Xbox is by Microsoft
]);

/** Common URL path segments to filter from URL tokens */
export const URL_PATH_NOISE: ReadonlySet<string> = new Set([
  'product',
  'products',
  'p',
  'item',
  'items',
  'search',
]);

/**
 * Condition mapping - synonyms to canonical values.
 * Multi-token phrases listed for phrase matching.
 */
export const CONDITION_PHRASES: ReadonlyArray<[string, string]> = [
  ['open box', 'open_box'],
  ['open-box', 'open_box'],
  ['openbox', 'open_box'],
  ['pre-owned', 'used'],
  ['pre owned', 'used'],
  ['preowned', 'used'],
];

export const CONDITION_SYNONYMS: Readonly<Record<string, string>> = {
  'new': 'new',
  'renewed': 'refurbished',
  'refurbished': 'refurbished',
  'refurb': 'refurbished',
  'used': 'used',
};

/**
 * Bundle detection keywords - TIGHTENED.
 * "with" alone is NOT sufficient - must be a product term.
 */
export const BUNDLE_KEYWORDS: ReadonlySet<string> = new Set([
  'kit',
  'bundle',
  'combo',
  'set',
  'package',
]);

/** Bundle phrase patterns - more specific than single "with" */
export const BUNDLE_PHRASES: ReadonlyArray<string> = [
  'with charger',
  'with case',
  'with accessories',
  'with battery',
  'with stand',
  'with mount',
];

/** Warranty keywords */
export const WARRANTY_KEYWORDS: Readonly<Record<string, string>> = {
  'manufacturer warranty': 'manufacturer',
  'mfr warranty': 'manufacturer',
  'official warranty': 'official',
  'local warranty': 'local',
  'international warranty': 'international',
  'no warranty': 'none',
};

/** Region detection in URL */
export const REGION_URL_TOKENS: Readonly<Record<string, string>> = {
  'il': 'il',
  'israel': 'il',
  'us': 'us',
  'usa': 'us',
  'uk': 'uk',
  'eu': 'eu',
  'global': 'global',
};

/** Timestamp validation tolerance (seconds) */
export const TIMESTAMP_FUTURE_TOLERANCE = 5;
