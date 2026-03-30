# PIL Extraction Module

Deterministic Product Identity Layer extraction per **DKP-PTL-REG-PIL-EXTRACTION-001 v0.3**.

## Overview

This module implements extraction of Product Identity Layer (PIL) fields from HTML pages. It is:

- **Deterministic**: Same input → same output
- **Offline**: No network/ML/external dependencies
- **Conformant**: Passes all 20 official test vectors

## Installation

```bash
pip install -e ".[pil]"
```

Or include dependencies directly:
```bash
pip install beautifulsoup4 lxml
```

## Usage

```python
from client.pil_extraction import extract_pil_from_html

result = extract_pil_from_html(
    html="<html>...</html>",
    url="https://example.com/product/bosch-rotak-32",
    utc_year=2026
)

# Result is either success:
# {
#   "pil_extraction_status": "OK",
#   "PIL": {
#     "brand": "bosch",
#     "model": "rotak 32 1200w",
#     "sku": "rotak32-1200",
#     ...
#   }
# }
#
# Or failure:
# {"pil_extraction_status": "INSUFFICIENT_IDENTITY"}
```

## Output Schema

When `pil_extraction_status == "OK"`:

| Field | Type | Description |
|-------|------|-------------|
| brand | str | Brand name (lowercase) |
| model | str | Model identifier |
| sku | str | Stock keeping unit |
| condition | str | "new", "refurbished", "used", or "" |
| bundle_flag | str | "standalone" or "bundle" |
| warranty_type | str | Warranty info if present |
| region_variant | str | Region variant if present |
| storage_or_size | str | Storage/size (e.g., "128gb", "55inch") |
| release_year | str | YYYY if valid (1970 ≤ year ≤ current+2) |

## Failure Statuses

| Status | Description |
|--------|-------------|
| `OK` | Extraction successful |
| `INVALID_PAGE_UNIT` | Multiple prices or missing title/price |
| `INSUFFICIENT_IDENTITY` | Model could not be determined (C_extract < 2) |
| `CONFLICT_BLOCKED` | Irreconcilable conflict between sources |
| `NO_MATCH` | No product structure found |

## Running Tests

```bash
# CLI runner (human-readable output)
PYTHONPATH=. python tests/pil_extraction/test_runner_pil.py

# Pytest
PYTHONPATH=. pytest tests/pil_extraction/test_pil_vectors.py -v
```

## CI Integration

The PIL conformance workflow runs on all changes to `client/pil_extraction/**` or `tests/pil_extraction/**`.

Any test failure blocks merge. This is by design — the harness validates strict spec conformance.

## Specification References

- [DKP-PTL-REG-PIL-EXTRACTION-001 v0.3](../Protocols/DKP-PTL-REG-PIL-EXTRACTION-001.md)
- [DKP-PTL-REG-PIL-TEST-VECTORS-001 v0.1](../Protocols/DKP-PTL-REG-PIL-TEST-VECTORS-001.md)

## Module Structure

```
client/pil_extraction/
├── __init__.py          # Public API
├── schemas.py           # Pydantic schemas
├── constants.py         # Version-locked constants
├── normalization.py     # UTF-8 + NFC normalization
├── source_collectors.py # S1-S5 source collection
├── page_unit.py         # LCA page unit detection
├── title_parser.py      # Brand/model parsing
├── url_tokens.py        # URL token extraction
├── mappings.py          # Conflict detection
└── extractor.py         # Main extraction logic
```
