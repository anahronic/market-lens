/**
 * Background Service Worker for Market Lens Extension
 * 
 * Per Manifest V3 requirements. Handles:
 * - Message routing between popup and content scripts
 * - API communication
 * - State management (minimal)
 */

import type { IngestPayload, IngestResponse } from './types/index.js';

// API configuration
const API_BASE_URL = 'https://api.market-lens.dev';

/**
 * Message listener for extension communication.
 */
chrome.runtime.onMessage.addListener((message: unknown, _sender: chrome.runtime.MessageSender, sendResponse: (response: unknown) => void) => {
  const msg = message as { type?: string; payload?: IngestPayload };
  if (msg?.type === 'INGEST_REQUEST') {
    handleIngestRequest(msg.payload!)
      .then(sendResponse)
      .catch((error) => {
        sendResponse({
          success: false,
          error: error.message,
        });
      });
    return true; // Async response
  }
});

/**
 * Handle ingest submission request.
 */
async function handleIngestRequest(payload: IngestPayload): Promise<IngestResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/v1/ingest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Protocol-Version': '0.6.0',
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
 * Extension install/update handler.
 */
chrome.runtime.onInstalled.addListener((details) => {
  console.log('[Market Lens] Extension installed/updated:', details.reason);
});

console.log('[Market Lens] Background service worker started');
