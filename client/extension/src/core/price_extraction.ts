/**
 * Price Extraction Module per DKP-PTL-REG-PIL-EXTRACTION-001 v0.3 section 2.
 *
 * FIXED CONTRACT:
 * - Uses price_regex_v1
 * - Exactly 1 price -> OK
 * - 0 or >1 prices -> reject
 *
 * This module does NOT interpret or transform prices.
 * It only extracts and validates presence.
 */

import type { PriceExtractionResult } from '../types/index.js';
import {
  PRICE_REGEX_V1,
  CURRENCY_SYMBOLS,
  CURRENCY_CODES,
  CURRENCY_SYMBOL_TO_CODE,
} from './constants.js';

/**
 * Parse a price string to extract numeric value and currency.
 *
 * @param priceStr - Raw matched price string
 * @returns Object with price and currency, or null if invalid
 */
function parsePriceString(priceStr: string): { price: number; currency: string } | null {
  // Find currency
  let currency: string | null = null;

  // Check for symbols
  for (const symbol of CURRENCY_SYMBOLS) {
    if (priceStr.includes(symbol)) {
      currency = CURRENCY_SYMBOL_TO_CODE[symbol] || null;
      break;
    }
  }

  // Check for codes if no symbol found
  if (!currency) {
    const upperStr = priceStr.toUpperCase();
    for (const code of CURRENCY_CODES) {
      if (upperStr.includes(code)) {
        currency = code;
        break;
      }
    }
  }

  if (!currency) {
    return null;
  }

  // Extract numeric part
  // Remove currency symbols/codes and normalize
  let numericStr = priceStr
    .replace(/[₪$€£]/g, '')
    .replace(/USD|ILS|EUR|GBP/gi, '')
    .replace(/[,\s]/g, '')
    .trim();

  const price = parseFloat(numericStr);

  if (isNaN(price) || !isFinite(price)) {
    return null;
  }

  return { price, currency };
}

/**
 * Extract price from text content.
 *
 * Per spec section 2:
 * - A page unit is valid ONLY if exactly one price candidate exists
 * - If multiple -> INVALID_PAGE_UNIT
 *
 * @param text - Text content to search for prices
 * @returns PriceExtractionResult
 */
export function extractPrice(text: string): PriceExtractionResult {
  if (!text) {
    return {
      success: false,
      error: 'NO_PRICE',
    };
  }

  // Reset regex state
  PRICE_REGEX_V1.lastIndex = 0;

  // Find all matches
  const matches: string[] = [];
  let match: RegExpExecArray | null;

  // Create new regex for each search to ensure clean state
  const regex = new RegExp(PRICE_REGEX_V1.source, PRICE_REGEX_V1.flags);

  while ((match = regex.exec(text)) !== null) {
    matches.push(match[0]);
  }

  // Deduplicate by normalized price value
  const uniquePrices = new Map<string, { raw: string; parsed: { price: number; currency: string } }>();

  for (const rawMatch of matches) {
    const parsed = parsePriceString(rawMatch);
    if (parsed) {
      // Create normalized key: currency + price
      const key = `${parsed.currency}:${parsed.price.toFixed(2)}`;
      if (!uniquePrices.has(key)) {
        uniquePrices.set(key, { raw: rawMatch, parsed });
      }
    }
  }

  if (uniquePrices.size === 0) {
    return {
      success: false,
      error: 'NO_PRICE',
    };
  }

  if (uniquePrices.size > 1) {
    return {
      success: false,
      error: 'MULTIPLE_PRICE',
    };
  }

  // Exactly one price
  const [, entry] = [...uniquePrices.entries()][0];

  return {
    success: true,
    price: entry.parsed.price,
    currency: entry.parsed.currency,
    raw_match: entry.raw,
  };
}

/**
 * Extract price from HTML element.
 *
 * @param element - DOM element to extract price from
 * @returns PriceExtractionResult
 */
export function extractPriceFromElement(element: Element): PriceExtractionResult {
  const text = element.textContent || '';
  return extractPrice(text);
}

/**
 * Validate extracted price per REFERENCE-001 section 9.
 *
 * Rejection conditions:
 * - price <= 0
 * - price not finite
 * - currency missing
 *
 * @param result - Price extraction result
 * @returns true if valid, false otherwise
 */
export function validatePrice(result: PriceExtractionResult): boolean {
  if (!result.success) {
    return false;
  }

  if (result.price === undefined || result.price <= 0) {
    return false;
  }

  if (!isFinite(result.price)) {
    return false;
  }

  if (!result.currency) {
    return false;
  }

  return true;
}
