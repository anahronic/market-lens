/**
 * Content Script for Market Lens Extension
 * 
 * Runs in page context. Passive by default - only activates on user action.
 * Per Phase 11 spec section 3.1:
 * - Passive mode by default
 * - Runs only by user action
 * - No background scraping
 */

import type { CaptureStatus, PILObject, DOMCaptureResult } from './types/index.js';
import { capturePageUnit, getFullPageHTML } from './core/dom_capture.js';
import { extractPilFromHtml } from './core/pil_extraction.js';
import { extractPrice, validatePrice } from './core/price_extraction.js';

/**
 * Message handler for extension messages.
 */
chrome.runtime.onMessage.addListener((message: unknown, _sender: chrome.runtime.MessageSender, sendResponse: (response: unknown) => void) => {
  const msg = message as { type?: string };
  if (msg?.type === 'CAPTURE_REQUEST') {
    handleCaptureRequest()
      .then(sendResponse)
      .catch((error) => {
        sendResponse({
          status: 'NETWORK_ERROR' as CaptureStatus,
          error: error.message,
        });
      });
    return true; // Async response
  }
});

/**
 * Handle capture request from popup.
 */
async function handleCaptureRequest(): Promise<{
  status: CaptureStatus;
  pil?: PILObject;
  price?: number;
  currency?: string;
  capture?: DOMCaptureResult;
}> {
  // Get current UTC year
  const utcYear = new Date().getUTCFullYear();

  // Capture page unit
  const capture = capturePageUnit();

  // Get full HTML for PIL extraction
  const html = getFullPageHTML();

  // Extract price first
  const priceResult = extractPrice(document.body?.textContent || '');

  if (!priceResult.success) {
    if (priceResult.error === 'MULTIPLE_PRICE') {
      return { status: 'MULTIPLE_PRICE' };
    }
    return { status: 'NO_PRICE' };
  }

  if (!validatePrice(priceResult)) {
    return { status: 'NO_PRICE' };
  }

  // Extract PIL
  const pilResult = extractPilFromHtml(html, window.location.href, utcYear);

  if (pilResult.pil_extraction_status !== 'OK') {
    // Map PIL status to capture status
    const statusMap: Record<string, CaptureStatus> = {
      'NO_MATCH': 'INVALID_PAGE',
      'INSUFFICIENT_IDENTITY': 'INSUFFICIENT_IDENTITY',
      'CONFLICT_BLOCKED': 'INVALID_PAGE',
      'INVALID_PAGE_UNIT': 'MULTIPLE_PRICE',
    };
    return {
      status: statusMap[pilResult.pil_extraction_status] || 'INVALID_PAGE',
    };
  }

  return {
    status: 'OK',
    pil: pilResult.PIL,
    price: priceResult.price,
    currency: priceResult.currency,
    capture,
  };
}

// Signal that content script is ready
console.log('[Market Lens] Content script loaded');
