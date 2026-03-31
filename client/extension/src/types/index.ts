/**
 * Type definitions for Market Lens Extension
 * Per DKP-PTL-REG-PIL-EXTRACTION-001 v0.3
 */

/** PIL extraction status codes */
export type PILExtractionStatus =
  | 'OK'
  | 'NO_MATCH'
  | 'INSUFFICIENT_IDENTITY'
  | 'CONFLICT_BLOCKED'
  | 'INVALID_PAGE_UNIT';

/** Capture status for UI feedback */
export type CaptureStatus =
  | 'OK'
  | 'INVALID_PAGE'
  | 'INSUFFICIENT_IDENTITY'
  | 'MULTIPLE_PRICE'
  | 'NO_PRICE'
  | 'NETWORK_ERROR'
  | 'VALIDATION_ERROR';

/** Product Identity Layer object */
export interface PILObject {
  brand: string;
  model: string;
  sku: string;
  condition: string;
  bundle_flag: string;
  warranty_type: string;
  region_variant: string;
  storage_or_size: string;
  release_year: string;
}

/** PIL extraction result */
export interface PILExtractionResult {
  pil_extraction_status: PILExtractionStatus;
  PIL?: PILObject;
}

/** Price extraction result */
export interface PriceExtractionResult {
  success: boolean;
  price?: number;
  currency?: string;
  raw_match?: string;
  error?: 'NO_PRICE' | 'MULTIPLE_PRICE' | 'INVALID_FORMAT';
}

/** Page unit selection result */
export interface PageUnitResult {
  success: boolean;
  element?: Element;
  title_element?: Element;
  price_element?: Element;
  failure_reason?: 'multiple_prices' | 'no_price' | 'no_title' | 'lca_exceeded';
}

/** DOM capture output */
export interface DOMCaptureResult {
  html: string;
  url: string;
  timestamp: number;
}

/** Source data from structured markup */
export interface SourceData {
  brand: string | null;
  model: string | null;
  name: string | null;
  sku: string | null;
  condition: string | null;
  size: string | null;
  has_offers: boolean;
}

/** Ingest payload per REFERENCE-001 */
export interface IngestPayload {
  domain_id: string;
  merchant_id: string;
  price: number;
  currency: string;
  region: string;
  timestamp: number;
  product_identity_layer: PILObject;
  evidence_hash: string;
}

/** Ingest API response */
export interface IngestResponse {
  success: boolean;
  submission_id?: string;
  error?: string;
}

/** Extension message types */
export type MessageType = 
  | 'CAPTURE_REQUEST'
  | 'CAPTURE_RESULT'
  | 'INGEST_REQUEST'
  | 'INGEST_RESULT';

export interface ExtensionMessage {
  type: MessageType;
  payload?: unknown;
}
