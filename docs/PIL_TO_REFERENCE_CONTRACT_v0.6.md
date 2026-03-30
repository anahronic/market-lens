# PIL to Reference Handoff Contract

**Document ID:** DKP-PTL-REG-PIL-TO-REFERENCE-001  
**Version:** 0.6  
**Status:** LOCKED  

---

## References

- **PIL Extraction Spec:** DKP-PTL-REG-PIL-EXTRACTION-001 v0.3
- **Reference Spec:** DKP-PTL-REG-REFERENCE-001 v0.6

---

## 1. Input Contract

### Function Signature

```python
extract_pil_from_html(html: str, url: str, utc_year: int) -> dict
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `html` | `str` | Raw HTML content of product page |
| `url` | `str` | Source URL of the page |
| `utc_year` | `int` | Current UTC year for release_year parsing |

---

## 2. Output Contract

### Success Response

```json
{
  "pil_extraction_status": "OK",
  "PIL": {
    "brand": "...",
    "model": "...",
    "sku": "...",
    "condition": "...",
    "bundle_flag": "...",
    "warranty_type": "...",
    "region_variant": "...",
    "storage_or_size": "...",
    "release_year": "..."
  }
}
```

### Failure Response

```json
{
  "pil_extraction_status": "NO_MATCH|INSUFFICIENT_IDENTITY|CONFLICT_BLOCKED|INVALID_PAGE_UNIT"
}
```

### Valid Status Values

| Status | Description |
|--------|-------------|
| `OK` | Extraction successful, PIL object present |
| `NO_MATCH` | No product data found |
| `INSUFFICIENT_IDENTITY` | Model missing or C_extract < 3 |
| `CONFLICT_BLOCKED` | Conflicting product identity detected |
| `INVALID_PAGE_UNIT` | Page unit selection failed |

---

## 3. Field Mapping

### PIL → Observation Mapping

If `pil_extraction_status == "OK"`:

| PIL Field | Observation Field | Type |
|-----------|-------------------|------|
| `brand` | `product_identity_layer.brand` | string |
| `model` | `product_identity_layer.model` | string |
| `sku` | `product_identity_layer.sku` | string |
| `condition` | `product_identity_layer.condition` | string |
| `bundle_flag` | `product_identity_layer.bundle_flag` | string |
| `warranty_type` | `product_identity_layer.warranty_type` | string |
| `region_variant` | `product_identity_layer.region_variant` | string |
| `storage_or_size` | `product_identity_layer.storage_or_size` | string |
| `release_year` | `product_identity_layer.release_year` | string |

If `pil_extraction_status != "OK"`:

**Observation MUST be rejected.** No mapping occurs.

---

## 4. Constraints

### 4.1 No Transformation

- Values MUST be passed as-is
- No case changes allowed
- No trimming allowed
- No default substitution allowed

### 4.2 Empty String Preservation

- Empty string `""` MUST remain `""`  
- Empty string is NOT equivalent to `null` or missing
- Empty string is valid output

### 4.3 Mapping Cardinality

- Mapping is **1:1**
- Each PIL field maps to exactly one observation field
- No field splitting
- No field merging
- No field omission

### 4.4 Field Completeness

- All 9 PIL fields MUST be present on OK status
- No partial PIL objects allowed
- Field order MUST match schema definition

---

## 5. Implementation Rules

### 5.1 Consumer Contract

Any consumer of PIL extraction output MUST:

1. Check `pil_extraction_status` first
2. If not `OK` → reject observation
3. If `OK` → map all 9 fields without transformation
4. Preserve empty strings

### 5.2 Producer Contract

PIL extraction module MUST:

1. Return exactly one of the valid status values
2. Include `PIL` object only when status is `OK`
3. Include all 9 fields in `PIL` object
4. Use normalized strings (lowercase, trimmed, collapsed whitespace)
5. Output deterministic results for identical input

---

## 6. Validation

### 6.1 Schema Validation

Output MUST match:

```python
{
    "pil_extraction_status": str,  # Required
    "PIL": {                       # Required if status == "OK"
        "brand": str,
        "model": str,
        "sku": str,
        "condition": str,
        "bundle_flag": str,
        "warranty_type": str,
        "region_variant": str,
        "storage_or_size": str,
        "release_year": str,
    }
}
```

### 6.2 No Extra Fields

- Output MUST NOT contain any fields not defined above
- No `_debug`, `_meta`, or internal fields allowed
- Strict schema enforcement

---

## 7. Version Binding

This contract is bound to:

- PIL Extraction: v0.3
- Reference Schema: v0.6

Any change to PIL output format requires:

1. Version increment
2. Contract update
3. GOV-001 review

---

*End of Contract*
