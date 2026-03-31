/**
 * Normalization module per DKP-PTL-REG-PIL-EXTRACTION-001 v0.3 section 8
 * and DKP-PTL-REG-REFERENCE-001 v0.6 section 3.
 *
 * CANONICAL NORMALIZATION PATH (single source of truth):
 * 1. NFC normalization
 * 2. Remove zero-width characters
 * 3. Trim whitespace
 * 4. Collapse multiple spaces to single
 * 5. Case-fold (lowercase)
 *
 * FIELD-SPECIFIC TRANSFORMATIONS (applied separately):
 * - Inch notation: '"' -> 'inch', '″' -> 'inch'
 * - Ampersand: '&' -> 'and'
 *
 * TypeScript port of client/pil_extraction/normalization.py
 */

import { TOKENIZE_REGEX } from './constants.js';

/**
 * Zero-width characters to remove.
 */
const ZERO_WIDTH_CHARS: ReadonlySet<string> = new Set([
  '\u200b', // zero-width space
  '\u200c', // zero-width non-joiner
  '\u200d', // zero-width joiner
  '\ufeff', // BOM / zero-width no-break space
  '\u2060', // word joiner
  '\u00ad', // soft hyphen
]);

/**
 * Apply canonical normalization per spec section 8.
 *
 * This is the BASE normalizer - no semantic transformations.
 * Use field-specific functions for semantic transforms like inch/ampersand.
 *
 * @param text - Raw input text (may be null/undefined)
 * @returns Normalized string (lowercase, single spaces, no zero-width chars)
 */
export function normalizeText(text: string | null | undefined): string {
  if (text == null) {
    return '';
  }

  // NFC normalization
  let normalized = text.normalize('NFC');

  // Remove zero-width characters
  normalized = [...normalized]
    .filter((c) => !ZERO_WIDTH_CHARS.has(c))
    .join('');

  // Trim
  normalized = normalized.trim();

  // Collapse spaces (all whitespace to single space)
  normalized = normalized.replace(/\s+/g, ' ');

  // Case-fold (lowercase)
  normalized = normalized.toLowerCase();

  return normalized;
}

/**
 * Normalize text with display-friendly semantic transformations.
 *
 * Applies:
 * - Base normalization
 * - '&' -> ' and '
 * - Inch marks -> 'inch'
 *
 * Use for: title, model, brand, condition, storage_or_size
 * Do NOT use for: SKU
 */
export function normalizeForDisplay(text: string | null | undefined): string {
  let normalized = normalizeText(text);

  // Ampersand -> "and"
  normalized = normalized.replace(/&/g, ' and ');

  // Inch notation variants -> "inch"
  normalized = normalized.replace(/"/g, 'inch');
  normalized = normalized.replace(/″/g, 'inch');
  normalized = normalized.replace(/''/g, 'inch');

  // Clean up extra spaces from replacements
  normalized = normalized.replace(/\s+/g, ' ').trim();

  return normalized;
}

/**
 * Extract tokens from text per spec section 12.1.
 *
 * Split by: [\s,|()[\]]+
 *
 * @param text - Normalized text
 * @returns Array of non-empty tokens
 */
export function extractTokens(text: string): string[] {
  if (!text) {
    return [];
  }
  return text
    .split(TOKENIZE_REGEX)
    .filter((token) => token.length > 0);
}

/**
 * Remove characters not in allowed set per spec section 8.
 * Allowed: [a-z0-9 \-/+.&]
 *
 * @param text - Input text
 * @returns Text with only allowed characters
 */
export function removeDisallowedChars(text: string): string {
  return text.replace(/[^a-z0-9 \-/+.&]/g, '');
}

/**
 * Normalize domain per REFERENCE-001 section 4.
 *
 * @param host - Raw hostname
 * @returns Normalized hostname (lowercase, trimmed)
 */
export function normalizeDomain(host: string): string {
  return normalizeText(host);
}

/**
 * Extract root domain from hostname.
 * 
 * Per REFERENCE-001 section 4.2, this should use PSL.
 * For MVP, we use a simple eTLD+1 approximation.
 * 
 * @param host - Normalized hostname
 * @returns Root domain (eTLD+1 approximation)
 */
export function extractRootDomain(host: string): string {
  const normalized = normalizeDomain(host);
  
  // Handle common multi-part TLDs
  const multiPartTLDs = ['.co.uk', '.co.il', '.com.au', '.co.nz', '.org.uk'];
  
  for (const tld of multiPartTLDs) {
    if (normalized.endsWith(tld)) {
      const parts = normalized.slice(0, -tld.length).split('.');
      if (parts.length > 0) {
        return parts[parts.length - 1] + tld;
      }
      return normalized;
    }
  }
  
  // Standard case: take last two parts
  const parts = normalized.split('.');
  if (parts.length <= 2) {
    return normalized;
  }
  return parts.slice(-2).join('.');
}

/**
 * Normalize timestamp per REFERENCE-001 section 6.
 *
 * @param timestamp - Input timestamp (ISO string, epoch ms, or epoch seconds)
 * @returns Unix epoch seconds (integer)
 */
export function normalizeTimestamp(timestamp: string | number | Date): number {
  let date: Date;

  if (timestamp instanceof Date) {
    date = timestamp;
  } else if (typeof timestamp === 'string') {
    date = new Date(timestamp);
  } else if (typeof timestamp === 'number') {
    // Detect if milliseconds (> year 2001 in seconds would be > 1e12)
    if (timestamp > 1e12) {
      date = new Date(timestamp);
    } else {
      date = new Date(timestamp * 1000);
    }
  } else {
    throw new Error('Invalid timestamp format');
  }

  if (isNaN(date.getTime())) {
    throw new Error('Invalid timestamp');
  }

  // Return floor of seconds
  return Math.floor(date.getTime() / 1000);
}

/**
 * Validate timestamp is not in the future.
 * Per REFERENCE-001 section 6: timestamp > now + 5s -> reject
 *
 * @param timestampSeconds - Unix epoch seconds
 * @returns true if valid, false if too far in future
 */
export function validateTimestamp(timestampSeconds: number): boolean {
  const now = Math.floor(Date.now() / 1000);
  const tolerance = 5; // seconds
  return timestampSeconds <= now + tolerance;
}

/**
 * Extract Latin tokens from mixed-script text.
 * Handles text like "שואב Dreame L10S" -> ["dreame", "l10s"]
 * 
 * @param text - Input text (may contain non-Latin characters)
 * @returns Array of Latin tokens (lowercase)
 */
export function extractLatinTokens(text: string): string[] {
  if (!text) {
    return [];
  }
  
  // Match sequences of Latin letters and numbers (model identifiers)
  const latinPattern = /[a-zA-Z][a-zA-Z0-9]*/g;
  const matches = text.match(latinPattern) || [];
  
  return matches
    .map(m => m.toLowerCase())
    .filter(m => m.length > 1); // Ignore single characters
}

