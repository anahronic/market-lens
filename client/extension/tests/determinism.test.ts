/**
 * Determinism Validation Test
 * 
 * Per Phase 11 spec section 8.2:
 * Same HTML: run_1 == run_2 == run_3
 */

import { describe, it, expect } from 'vitest';
import { JSDOM } from 'jsdom';

// Sample HTML for determinism testing
const SAMPLE_HTML = `
<html>
  <head>
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Product",
        "brand": {"name": "Samsung"},
        "model": "Galaxy S24 Ultra",
        "sku": "SM-S928B",
        "itemCondition": "new",
        "size": "256GB"
      }
    </script>
  </head>
  <body>
    <h1>Samsung Galaxy S24 Ultra 256GB</h1>
    <div class="price">₪ 4,999</div>
  </body>
</html>
`;

const SAMPLE_URL = 'https://example.com/product/galaxy-s24-ultra-256gb';

/**
 * Simplified extraction function for determinism testing.
 */
function extractFromHtml(html: string, url: string, utcYear: number) {
  const dom = new JSDOM(html);
  const doc = dom.window.document;

  // Extract JSON-LD
  let jsonldData: Record<string, unknown> | null = null;
  const jsonldScript = doc.querySelector('script[type="application/ld+json"]');
  if (jsonldScript?.textContent) {
    try {
      jsonldData = JSON.parse(jsonldScript.textContent);
    } catch {
      // Ignore
    }
  }

  // Extract title
  const h1 = doc.querySelector('h1');
  const titleText = h1?.textContent?.trim().toLowerCase() || '';

  // Extract price - use correct regex from constants (with optional thousand separator)
  const priceRegex = /([₪$€£]|USD|ILS|EUR|GBP)\s*[0-9]{1,3}(?:[,\s]?[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]{1,3}(?:[,\s]?[0-9]{3})*(?:\.[0-9]{1,2})?\s*([₪$€£]|USD|ILS|EUR|GBP)/gi;
  const bodyText = doc.body?.textContent || '';
  const priceMatch = bodyText.match(priceRegex);

  // Build result
  const brand = jsonldData?.['brand'] 
    ? (typeof jsonldData['brand'] === 'object' 
        ? (jsonldData['brand'] as Record<string, unknown>)['name'] as string
        : jsonldData['brand'] as string)
    : '';

  return {
    brand: (brand || '').toLowerCase(),
    model: (jsonldData?.['model'] as string || '').toLowerCase(),
    sku: (jsonldData?.['sku'] as string || '').toLowerCase(),
    condition: jsonldData?.['itemCondition'] === 'new' ? 'new' : '',
    size: (jsonldData?.['size'] as string || '').toLowerCase(),
    title: titleText,
    price: priceMatch?.[0] || null,
    url,
  };
}

describe('Determinism Validation', () => {
  it('should produce identical output on 3 consecutive runs', () => {
    const results = [];

    for (let i = 0; i < 3; i++) {
      const result = extractFromHtml(SAMPLE_HTML, SAMPLE_URL, 2026);
      results.push(JSON.stringify(result));
    }

    expect(results[0]).toBe(results[1]);
    expect(results[1]).toBe(results[2]);
  });

  it('should produce consistent hash across runs', async () => {
    const hashes: string[] = [];

    for (let i = 0; i < 3; i++) {
      const result = extractFromHtml(SAMPLE_HTML, SAMPLE_URL, 2026);
      const canonical = JSON.stringify(result, Object.keys(result).sort());
      
      // Simple hash for testing (not crypto)
      let hash = 0;
      for (let j = 0; j < canonical.length; j++) {
        const char = canonical.charCodeAt(j);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
      }
      hashes.push(hash.toString(16));
    }

    expect(hashes[0]).toBe(hashes[1]);
    expect(hashes[1]).toBe(hashes[2]);
  });

  it('should extract expected fields from sample', () => {
    const result = extractFromHtml(SAMPLE_HTML, SAMPLE_URL, 2026);

    expect(result.brand).toBe('samsung');
    expect(result.model).toBe('galaxy s24 ultra');
    expect(result.sku).toBe('sm-s928b');
    expect(result.condition).toBe('new');
    expect(result.size).toBe('256gb');
    expect(result.price).toContain('4,999');
  });
});
