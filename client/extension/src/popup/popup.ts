/**
 * Market Lens Extension Popup Script
 * 
 * Minimal UI per Phase 11 spec section 5:
 * - Button: "Capture Price"
 * - Status: OK, INVALID_PAGE, INSUFFICIENT_IDENTITY, MULTIPLE_PRICE
 * - No recommendations, no evaluations, no colors beyond status
 */

import type { CaptureStatus, PILObject } from '../types/index.js';

// UI Elements
const captureBtn = document.getElementById('capture-btn') as HTMLButtonElement;
const statusDiv = document.getElementById('status') as HTMLDivElement;
const statusIcon = document.getElementById('status-icon') as HTMLSpanElement;
const statusText = document.getElementById('status-text') as HTMLSpanElement;
const detailsDiv = document.getElementById('details') as HTMLDivElement;
const detailBrand = document.getElementById('detail-brand') as HTMLSpanElement;
const detailModel = document.getElementById('detail-model') as HTMLSpanElement;
const detailPrice = document.getElementById('detail-price') as HTMLSpanElement;
const detailSku = document.getElementById('detail-sku') as HTMLSpanElement;

// Status messages mapping
const STATUS_MESSAGES: Record<CaptureStatus, string> = {
  'OK': 'Price captured successfully',
  'INVALID_PAGE': 'Invalid page structure',
  'INSUFFICIENT_IDENTITY': 'Insufficient product identity',
  'MULTIPLE_PRICE': 'Multiple prices detected',
  'NO_PRICE': 'No price found',
  'NETWORK_ERROR': 'Network error',
  'VALIDATION_ERROR': 'Validation failed',
};

/**
 * Show status message.
 */
function showStatus(status: CaptureStatus): void {
  statusDiv.classList.remove('hidden', 'success', 'error', 'warning');
  statusIcon.className = 'status-icon';

  if (status === 'OK') {
    statusDiv.classList.add('success');
    statusIcon.classList.add('success');
  } else if (status === 'MULTIPLE_PRICE' || status === 'INSUFFICIENT_IDENTITY') {
    statusDiv.classList.add('warning');
    statusIcon.classList.add('warning');
  } else {
    statusDiv.classList.add('error');
    statusIcon.classList.add('error');
  }

  statusText.textContent = STATUS_MESSAGES[status] || status;
}

/**
 * Show extraction details.
 */
function showDetails(
  pil: PILObject | null,
  price: number | null,
  currency: string | null
): void {
  if (!pil) {
    detailsDiv.classList.add('hidden');
    return;
  }

  detailsDiv.classList.remove('hidden');
  detailBrand.textContent = pil.brand || '-';
  detailModel.textContent = pil.model || '-';
  detailSku.textContent = pil.sku || '-';
  
  if (price !== null && currency) {
    detailPrice.textContent = `${currency} ${price.toFixed(2)}`;
  } else {
    detailPrice.textContent = '-';
  }
}

/**
 * Set loading state.
 */
function setLoading(loading: boolean): void {
  captureBtn.disabled = loading;
  captureBtn.classList.toggle('loading', loading);
}

/**
 * Handle capture button click.
 */
async function handleCapture(): Promise<void> {
  setLoading(true);
  statusDiv.classList.add('hidden');
  detailsDiv.classList.add('hidden');

  try {
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab?.id) {
      showStatus('INVALID_PAGE');
      return;
    }

    // Execute content script to capture and extract
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: captureAndExtract,
    });

    const result = results[0]?.result;

    if (!result) {
      showStatus('INVALID_PAGE');
      return;
    }

    // Show result
    showStatus(result.status);
    
    if (result.status === 'OK' && result.pil) {
      showDetails(result.pil, result.price ?? null, result.currency ?? null);
    }

  } catch (error) {
    console.error('Capture error:', error);
    showStatus('NETWORK_ERROR');
  } finally {
    setLoading(false);
  }
}

/**
 * Content script function executed in page context.
 * This function is stringified and injected, so it must be self-contained.
 */
function captureAndExtract(): {
  status: CaptureStatus;
  pil?: PILObject;
  price?: number;
  currency?: string;
} {
  // Inline constants (since this runs in page context)
  const PRICE_REGEX = /([₪$€£]|USD|ILS|EUR|GBP)\s*[0-9]{1,3}(?:[,\s][0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]{1,3}(?:[,\s][0-9]{3})*(?:\.[0-9]{1,2})?\s*([₪$€£]|USD|ILS|EUR|GBP)/gi;
  
  const CURRENCY_MAP: Record<string, string> = {
    '₪': 'ILS', '$': 'USD', '€': 'EUR', '£': 'GBP',
  };

  // Find prices in document
  const body = document.body;
  if (!body) {
    return { status: 'INVALID_PAGE' };
  }

  const textContent = body.innerText;
  const matches = textContent.match(PRICE_REGEX);

  if (!matches || matches.length === 0) {
    return { status: 'NO_PRICE' };
  }

  // Deduplicate prices
  const uniquePrices = new Set<string>();
  for (const match of matches) {
    const normalized = match.replace(/[,\s]/g, '').toLowerCase();
    uniquePrices.add(normalized);
  }

  if (uniquePrices.size > 1) {
    return { status: 'MULTIPLE_PRICE' };
  }

  // Parse price
  const priceStr = matches[0];
  let currency = '';
  
  for (const [symbol, code] of Object.entries(CURRENCY_MAP)) {
    if (priceStr.includes(symbol)) {
      currency = code;
      break;
    }
  }
  
  if (!currency) {
    const codes = ['USD', 'ILS', 'EUR', 'GBP'];
    for (const code of codes) {
      if (priceStr.toUpperCase().includes(code)) {
        currency = code;
        break;
      }
    }
  }

  const numericStr = priceStr.replace(/[₪$€£]/g, '').replace(/USD|ILS|EUR|GBP/gi, '').replace(/[,\s]/g, '');
  const price = parseFloat(numericStr);

  if (isNaN(price) || price <= 0) {
    return { status: 'NO_PRICE' };
  }

  // Find title
  const titleEl = document.querySelector('h1, [itemprop="name"], h2, .product-title');
  if (!titleEl) {
    return { status: 'INSUFFICIENT_IDENTITY' };
  }

  const titleText = titleEl.textContent?.trim().toLowerCase() || '';
  if (!titleText) {
    return { status: 'INSUFFICIENT_IDENTITY' };
  }

  // Simple model extraction (first significant words)
  const tokens = titleText.split(/[\s,|()\[\]]+/).filter(t => t.length > 0);
  
  // Noise words to filter
  const noise = new Set(['new', 'sale', 'best', 'free', 'shipping', 'deal', 'discount', 'promo']);
  const cleanTokens = tokens.filter(t => !noise.has(t));
  
  if (cleanTokens.length < 2) {
    return { status: 'INSUFFICIENT_IDENTITY' };
  }

  // First token as brand (if looks like brand)
  const brand = cleanTokens[0];
  const model = cleanTokens.slice(1).join(' ');

  // Check for JSON-LD for better data
  let sku = '';
  let condition = '';
  
  const jsonldScript = document.querySelector('script[type="application/ld+json"]');
  if (jsonldScript) {
    try {
      const data = JSON.parse(jsonldScript.textContent || '');
      if (data['@type'] === 'Product') {
        sku = (data.sku || '').toLowerCase();
        const cond = data.itemCondition || '';
        if (cond.toLowerCase().includes('new')) condition = 'new';
        else if (cond.toLowerCase().includes('refurb')) condition = 'refurbished';
        else if (cond.toLowerCase().includes('used')) condition = 'used';
      }
    } catch {
      // Ignore JSON parse errors
    }
  }

  const pil: PILObject = {
    brand,
    model,
    sku,
    condition,
    bundle_flag: 'standalone',
    warranty_type: '',
    region_variant: '',
    storage_or_size: '',
    release_year: '',
  };

  return {
    status: 'OK',
    pil,
    price,
    currency,
  };
}

// Event listeners
captureBtn.addEventListener('click', handleCapture);
