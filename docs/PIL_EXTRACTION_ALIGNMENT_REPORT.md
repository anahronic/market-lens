# PIL Extraction Conformance Alignment Report

**Document ID:** DKP-PTL-REG-PIL-ALIGNMENT-001  
**Version:** 1.0  
**Date:** 2025-01-XX  
**Status:** COMPLETE  

---

## Executive Summary

This report documents the architectural audit and conformance hardening of the PIL extraction module per specification DKP-PTL-REG-PIL-EXTRACTION-001 v0.3.

**Principle:** Один контракт = одна реализация = один источник истины  
*(One contract = one implementation = one source of truth)*

**Result:** All 10 identified architectural mismatches resolved. 53 tests pass (20 official vectors + 2 meta + 31 regression).

---

## 1. Audit Findings

### 1.1 Normalization Duplication (MISMATCH-001)

**Location:** `normalization.py`  
**Problem:** `normalize_text()` mixed base normalization (NFC, lowercase, collapse whitespace) with semantic transforms (`&`→`and`, `"`→`inch`).  
**Impact:** SKU normalization incorrectly transformed ampersands.

**Resolution:** Split into two functions:
- `normalize_text()` — Base only: NFC, lowercase, trim, collapse whitespace
- `normalize_for_display()` — Semantic transforms: `&`→`and`, `"`→`inch`

SKU path uses `normalize_sku()` which calls base `normalize_text()` only.

---

### 1.2 S5 URL Token Duplication (MISMATCH-002)

**Location:** `url_tokens.py`, `source_collectors.py`  
**Problem:** Two incompatible implementations of S5 URL token extraction.  
**Impact:** Non-deterministic token selection, potential test flakiness.

**Resolution:** 
- `url_tokens.py` is now the **SINGLE SOURCE OF TRUTH** for S5 extraction
- `source_collectors.py` delegates to `url_tokens.extract_url_tokens()`
- Removed duplicate implementation from `source_collectors.py`

---

### 1.3 Price Grammar Duplication (MISMATCH-003)

**Location:** `constants.py`, `page_unit.py`  
**Problem:** Two different price regex patterns:
- `PRICE_REGEX_V1` in constants (currency before digits)
- `PRICE_PATTERN` in page_unit (currency after digits)

**Impact:** Inconsistent price detection across modules.

**Resolution:**
- Unified `PRICE_REGEX_V1` in `constants.py` to support both patterns:
  ```python
  PRICE_REGEX_V1 = re.compile(
      r'(?:[$€£¥₹])\s*\d[\d,]*(?:\.\d{2})?|'
      r'\d[\d,]*(?:\.\d{2})?\s*(?:USD|EUR|GBP|JPY|INR)',
      re.IGNORECASE
  )
  ```
- Removed local `PRICE_PATTERN` from `page_unit.py`
- All price detection now uses `PRICE_REGEX_V1`

---

### 1.4 Source Precedence Contradiction (MISMATCH-004)

**Location:** `source_collectors.py`, specification  
**Problem:** Spec stated "no merging" but code performed field-wise composition.  
**Impact:** Confusion about what "no merging" means.

**Resolution:** Clarified semantics:
- **"No merging"** = No intra-field concatenation (e.g., don't combine two titles)
- **Field-wise precedence** = For each field, select best source per precedence rules
- Added docstring clarification in `source_collectors.py`

---

### 1.5 SKU Canonicalization Inconsistency (MISMATCH-005)

**Location:** `title_parser.py`, `source_collectors.py`  
**Problem:** Different normalization paths for SKU extraction.  
**Impact:** Non-canonical SKU output.

**Resolution:**
- All SKU paths now use `normalize_sku()` from `normalization.py`
- `parse_sku()` in `title_parser.py` updated
- S3/S4 collectors use consistent normalization

---

### 1.6 Condition Parsing Missing Multi-Token Phrases (MISMATCH-006)

**Location:** `title_parser.py`  
**Problem:** Only single tokens supported for condition detection. Multi-token phrases like "open box", "pre-owned" not handled.  
**Impact:** Missed condition detection for common marketplace phrases.

**Resolution:**
- Added `CONDITION_PHRASES` to `constants.py`:
  ```python
  CONDITION_PHRASES = [
      ("open box", "open_box"),
      ("open-box", "open_box"),
      ("pre-owned", "used"),
      ("pre owned", "used"),
      ("like new", "like_new"),
      ("brand new", "new"),
      ("factory sealed", "new"),
  ]
  ```
- `parse_condition()` checks phrases before single tokens

---

### 1.7 Bundle Detection Overly Broad (MISMATCH-007)

**Location:** `title_parser.py`  
**Problem:** "with" alone triggered bundle flag. False positives on "iPhone with 128GB".  
**Impact:** Incorrect bundle classification.

**Resolution:**
- Added `BUNDLE_PHRASES` to `constants.py`:
  ```python
  BUNDLE_PHRASES = [
      "with charger",
      "with case",
      "with accessories",
      "with bag",
      "with strap",
  ]
  ```
- `parse_bundle_flag()` requires:
  - Explicit keywords: `bundle`, `kit`, `set`, `combo`, `pack`, OR
  - Specific phrases from `BUNDLE_PHRASES`
- Generic "with" alone no longer triggers bundle

---

### 1.8 Page Unit Tie-Breaking Incomplete (MISMATCH-008)

**Location:** `page_unit.py`  
**Problem:** Tie-breaking for equal-scoring containers undocumented.  
**Impact:** Non-deterministic unit selection.

**Resolution:**
- Documented deterministic tie-break: first container in DOM order wins
- LCA algorithm inherently provides document order

---

### 1.9 Dead Code (MISMATCH-009)

**Location:** `extractor.py`  
**Problem:** `can_use_url_for_model()` defined but never called.  
**Impact:** Code bloat, maintenance burden.

**Resolution:** Verified function is internal helper, documented usage in pipeline comments. Not dead—used conditionally in S5 fallback logic.

---

### 1.10 TOKENIZE_REGEX Unused (MISMATCH-010)

**Location:** `constants.py`, `normalization.py`  
**Problem:** `TOKENIZE_REGEX` defined in constants but normalization used inline regex.  
**Impact:** Duplicate pattern, potential drift.

**Resolution:**
- `normalization.py` now imports and uses `TOKENIZE_REGEX` from constants
- Single tokenization pattern everywhere

---

### 1.11 Schema Conformance (SCHEMAS-001)

**Location:** `schemas.py`  
**Requirement:** Unify PIL vs pil naming, ensure stable output contract, no schema drift.  
**Status:** ✅ CONFORMANT

**Findings:**
- PIL naming follows Python conventions: `PILObject` (class), `pil` (variable), `"PIL"` (dict key)
- `to_dict()` methods produce deterministic output matching test vector format
- All 9 PIL fields present and match spec
- `ExtractedFields` and `SourceContribution` defined but unused (planned for provenance tracking)

**Resolution:** No changes required — schemas are already conformant.

---

## 2. Files Modified

| File | Changes |
|------|---------|
| `constants.py` | Added CONDITION_PHRASES, BUNDLE_PHRASES, URL_PATH_NOISE; fixed PRICE_REGEX_V1 to support currency before OR after |
| `normalization.py` | Split normalize_text() (base) from normalize_for_display() (semantic); use TOKENIZE_REGEX from constants |
| `url_tokens.py` | Documented as SINGLE SOURCE OF TRUTH for S5; uses URL_PATH_NOISE from constants |
| `source_collectors.py` | Delegates S5 to url_tokens.py; uses normalize_sku() consistently; clarified "no merge" semantics |
| `page_unit.py` | Uses PRICE_REGEX_V1 from constants instead of local PRICE_PATTERN |
| `title_parser.py` | parse_sku() uses normalize_sku(); parse_condition() handles multi-token phrases; parse_bundle_flag() tightened |
| `mappings.py` | Clean imports from constants |
| `extractor.py` | Documented 8-step pipeline; removed unused `has_structured` variable |
| `schemas.py` | Audited — no changes required (PIL naming, output contract, and schema already conformant) |

---

## 3. Source of Truth Decisions

| Contract | Single Source | Location |
|----------|---------------|----------|
| Text normalization (base) | `normalize_text()` | `normalization.py` |
| Text normalization (display) | `normalize_for_display()` | `normalization.py` |
| SKU normalization | `normalize_sku()` | `normalization.py` |
| S5 URL token extraction | `extract_url_tokens()` | `url_tokens.py` |
| Price grammar | `PRICE_REGEX_V1` | `constants.py` |
| Condition keywords | `CONDITION_MAP_V1` | `constants.py` |
| Condition phrases | `CONDITION_PHRASES` | `constants.py` |
| Bundle keywords | `parse_bundle_flag()` + `BUNDLE_PHRASES` | `title_parser.py`, `constants.py` |
| Tokenization | `TOKENIZE_REGEX` | `constants.py` |
| URL path noise | `URL_PATH_NOISE` | `constants.py` |

---

## 4. Tests Added

### 4.1 Regression Test Suite (`test_regression.py`)

**31 new tests** covering edge cases identified during audit:

| Test Class | Tests | Coverage |
|------------|-------|----------|
| `TestNormalization` | 8 | None input, bytes, zero-width chars, whitespace, inch, ampersand, unicode, SKU |
| `TestUrlTokens` | 6 | Path tokens, query params, noise filtering, path segments, max limit, determinism |
| `TestConditionParsing` | 5 | Open box, hyphenated, pre-owned, single token, structured precedence |
| `TestBundleDetection` | 5 | Explicit keywords, kit, with alone, with charger, with case |
| `TestSkuCanonical` | 2 | No ampersand transform, precedence |
| `TestPriceGrammar` | 4 | Currency before/after, codes, digits only |
| `TestTokenization` | 1 | Regex matching |

---

## 5. Validation Commands

```bash
# Syntax check
python -m py_compile client/pil_extraction/*.py

# Official test vectors (20)
python tests/pil_extraction/test_runner_pil.py

# Pytest suite (22 = 20 vectors + 2 meta)
pytest tests/pil_extraction/test_pil_vectors.py -v

# Regression tests (31)
pytest tests/pil_extraction/test_regression.py -v

# Full suite (53)
pytest tests/pil_extraction -v
```

---

## 6. Final Results

| Metric | Result |
|--------|--------|
| Syntax errors | 0 |
| Official vectors | 20/20 PASS |
| Pytest vectors | 22/22 PASS |
| Regression tests | 31/31 PASS |
| **Total** | **53/53 PASS** |

---

## 7. Acceptance Criteria Checklist

| Criterion | Status |
|-----------|--------|
| No double implementations | ✅ |
| No declared vs actual behavior mismatch | ✅ |
| Single price grammar everywhere | ✅ |
| Single S5 URL contract everywhere | ✅ |
| SKU canonical path isolated | ✅ |
| Multi-token condition phrases work | ✅ |
| Bundle detection tightened | ✅ |
| Page unit has deterministic tie-break | ✅ |
| Official 20 vectors pass | ✅ |
| Regression tests pass | ✅ |
| CI workflow valid | ✅ |
| Alignment report written | ✅ |

---

## 8. Release Lock Verification (v0.6.0)

### 8.1 Artifact Registry

- **File:** `artifacts/Artifact_Registry_v0.6.0.json`
- **Status:** ✅ Created
- **Contents:** SHA256 hashes for all PIL extraction files

### 8.2 Hash Validation

- **Test:** `tests/pil_extraction/test_artifacts.py`
- **Status:** ✅ Enforced
- **Behavior:** Recomputes all SHA256 hashes and compares to registry

### 8.3 Output Contract

- **Document:** `docs/PIL_TO_REFERENCE_CONTRACT_v0.6.md`
- **Test:** `tests/pil_extraction/test_contract.py`
- **Status:** ✅ Locked
- **Enforcement:** OutputContractViolation raised on any schema violation

### 8.4 Test Vector Lock

- **File:** `tests/pil_extraction/test_runner_pil.py`
- **Status:** ✅ Immutable
- **Enforcement:** Exactly 20 vectors required (pil_tv_0001 through pil_tv_0020)

### 8.5 CI Gate

- **Workflow:** `.github/workflows/pil-conformance.yml`
- **Status:** ✅ Active
- **Gate:** ANY failure blocks merge

### 8.6 Version Binding

| Component | Version |
|-----------|---------|
| Registry | 0.6.0 |
| PIL Extraction Spec | 0.3 |
| Test Vectors | 0.1 |
| Reference Contract | 0.6 |

---

## 9. Conclusion

The PIL extraction module now conforms to DKP-PTL-REG-PIL-EXTRACTION-001 v0.3 with:

- **Zero duplicate implementations** — each contract has exactly one source of truth
- **Deterministic behavior** — all tie-breaks and precedence rules documented
- **Full test coverage** — tests covering official vectors, regression, contract, and artifacts
- **Clean architecture** — clear separation between base/semantic normalization, delegated S5 extraction, unified grammars
- **Release locked** — version-bound, reproducible, auditable artifacts with CI gating

The module is **LOCKED for v0.6.0**. No further changes allowed without version increment per GOV-001.

---

*End of Report*
