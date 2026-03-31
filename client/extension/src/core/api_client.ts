/**
 * Ingest API Client per Phase 11 spec section 3.6.
 *
 * Endpoint: POST /v1/ingest
 *
 * Security constraints (per REG-001):
 * - Never send raw HTML
 * - Never send user data
 * - Never send cookies
 * - Only send canonical payload + hash
 */

import type { IngestPayload, IngestResponse, PILObject } from '../types/index.js';
import { normalizeText, extractRootDomain, normalizeTimestamp, validateTimestamp } from './normalize.js';
import { PROTOCOL_VERSION } from './constants.js';

/** API base URL - configurable */
const API_BASE_URL = 'https://api.market-lens.dev';

/**
 * Compute SHA256 hash of a string.
 *
 * @param data - String to hash
 * @returns Hex-encoded SHA256 hash
 */
async function sha256(data: string): Promise<string> {
  const encoder = new TextEncoder();
  const dataBuffer = encoder.encode(data);
  const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Build canonical JSON for evidence hash.
 * Per REFERENCE-001 section 8:
 * - UTF-8
 * - Lexicographically sorted keys
 * - No whitespace
 * - No trailing zeros in numbers
 */
function buildCanonicalJson(payload: Omit<IngestPayload, 'evidence_hash'>): string {
  // Sort PIL fields
  const sortedPil: Record<string, string> = {};
  const pilKeys = Object.keys(payload.product_identity_layer).sort();
  for (const key of pilKeys) {
    sortedPil[key] = payload.product_identity_layer[key as keyof PILObject];
  }

  // Build canonical object with sorted keys
  const canonical = {
    currency: payload.currency,
    domain_id: payload.domain_id,
    merchant_id: payload.merchant_id,
    price: payload.price,
    product_identity_layer: sortedPil,
    region: payload.region,
    timestamp: payload.timestamp,
  };

  // Stringify without whitespace
  return JSON.stringify(canonical);
}

/**
 * Compute evidence hash from payload.
 *
 * @param payload - Payload without evidence_hash
 * @returns SHA256 hash of canonical JSON
 */
export async function computeEvidenceHash(
  payload: Omit<IngestPayload, 'evidence_hash'>
): Promise<string> {
  const canonical = buildCanonicalJson(payload);
  return sha256(canonical);
}

/**
 * Validate payload before submission.
 * Per REFERENCE-001 section 9 rejection conditions.
 *
 * @param payload - Payload to validate
 * @returns Error message or null if valid
 */
export function validatePayload(payload: Omit<IngestPayload, 'evidence_hash'>): string | null {
  // Price validation
  if (payload.price <= 0) {
    return 'price <= 0';
  }
  if (!isFinite(payload.price)) {
    return 'price not finite';
  }

  // Currency validation
  if (!payload.currency) {
    return 'currency missing';
  }

  // Region validation
  if (!payload.region) {
    return 'region missing';
  }

  // Timestamp validation
  if (!validateTimestamp(payload.timestamp)) {
    return 'timestamp > now + 5s';
  }

  // Merchant ID length
  const merchantIdBytes = new TextEncoder().encode(payload.merchant_id);
  if (merchantIdBytes.length > 256) {
    return 'merchant_id length > 256 bytes';
  }

  // PIL validation
  const pil = payload.product_identity_layer;
  if (!pil.model) {
    return 'PIL model missing';
  }

  return null;
}

/**
 * Build ingest payload from extracted data.
 *
 * @param url - Page URL
 * @param price - Extracted price
 * @param currency - Extracted currency
 * @param pil - Extracted PIL
 * @param region - Region (default: from URL or 'il')
 * @param merchantId - Merchant ID (default: empty)
 * @returns IngestPayload ready for submission
 */
export async function buildIngestPayload(
  url: string,
  price: number,
  currency: string,
  pil: PILObject,
  region?: string,
  merchantId?: string
): Promise<IngestPayload> {
  // Extract domain
  let domainId: string;
  try {
    const parsed = new URL(url);
    domainId = extractRootDomain(parsed.hostname);
  } catch {
    throw new Error('Invalid URL');
  }

  // Determine region from URL if not provided
  let finalRegion = region;
  if (!finalRegion) {
    try {
      const parsed = new URL(url);
      const hostname = parsed.hostname.toLowerCase();
      if (hostname.endsWith('.il') || hostname.includes('.co.il')) {
        finalRegion = 'il';
      } else if (hostname.endsWith('.uk') || hostname.endsWith('.co.uk')) {
        finalRegion = 'uk';
      } else if (hostname.endsWith('.eu')) {
        finalRegion = 'eu';
      } else {
        finalRegion = 'us'; // Default
      }
    } catch {
      finalRegion = 'us';
    }
  }

  const timestamp = normalizeTimestamp(Date.now());

  const payloadWithoutHash: Omit<IngestPayload, 'evidence_hash'> = {
    domain_id: domainId,
    merchant_id: normalizeText(merchantId) || '',
    price,
    currency,
    region: finalRegion,
    timestamp,
    product_identity_layer: pil,
  };

  const evidenceHash = await computeEvidenceHash(payloadWithoutHash);

  return {
    ...payloadWithoutHash,
    evidence_hash: evidenceHash,
  };
}

/**
 * Submit observation to ingest API.
 *
 * @param payload - Validated ingest payload
 * @returns IngestResponse
 */
export async function submitToIngest(payload: IngestPayload): Promise<IngestResponse> {
  // Validate before sending
  const validationError = validatePayload(payload);
  if (validationError) {
    return {
      success: false,
      error: `Validation failed: ${validationError}`,
    };
  }

  try {
    const response = await fetch(`${API_BASE_URL}/v1/ingest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Protocol-Version': PROTOCOL_VERSION,
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return {
        success: false,
        error: `HTTP ${response.status}: ${errorText}`,
      };
    }

    const result = await response.json();
    return {
      success: true,
      submission_id: result.submission_id,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Network error',
    };
  }
}

/**
 * Get API health status.
 *
 * @returns true if API is reachable
 */
export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        'X-Protocol-Version': PROTOCOL_VERSION,
      },
    });
    return response.ok;
  } catch {
    return false;
  }
}
