# Deterministic Release Report v0.6.0

**Document ID:** DKP-PTL-REG-RELEASE-REPORT-001  
**Version:** 0.6.0  
**Date:** 2026-03-30  
**Status:** FINAL  

---

## 1. Frozen Release Set

### 1.1 Protocol Specifications

| Document ID | Version | Path |
|-------------|---------|------|
| DKP-PTL-REG-001 | 0.6 | specs/dkp-ptl-reg/v0.6/DKP-PTL-REG-001.md |
| DKP-PTL-REG-DATA-001 | 0.6 | specs/dkp-ptl-reg/v0.6/DKP-PTL-REG-DATA-001.md |
| DKP-PTL-REG-CONSTANTS-001 | 0.6 | specs/dkp-ptl-reg/v0.6/DKP-PTL-REG-CONSTANTS-001.md |
| DKP-PTL-REG-REFERENCE-001 | 0.6 | specs/dkp-ptl-reg/v0.6/DKP-PTL-REG-REFERENCE-001.md |
| DKP-PTL-REG-THREAT-001 | 0.6 | specs/dkp-ptl-reg/v0.6/DKP-PTL-REG-THREAT-001.md |
| DKP-PTL-REG-GOV-001 | 0.6 | specs/dkp-ptl-reg/v0.6/DKP-PTL-REG-GOV-001.md |
| DKP-PTL-REG-CLIENT-001 | 0.3 | Protocols/DKP-PTL-REG-CLIENT-001.md |
| DKP-PTL-REG-PIL-EXTRACTION-001 | 0.3 | Protocols/DKP-PTL-REG-PIL-EXTRACTION-001.md |
| DKP-PTL-REG-PIL-TEST-VECTORS-001 | 0.1 | Protocols/DKP-PTL-REG-PIL-TEST-VECTORS-001.md |

### 1.2 Implementation Files

| Category | Count | Location |
|----------|-------|----------|
| PIL Extraction | 10 files | client/pil_extraction/*.py |
| Conformance Tests | 5 files | tests/pil_extraction/*.py |
| Test Vectors | 1 file | tests/pil_extraction/vectors/pil_vectors_v0_1.json |
| CI Workflow | 1 file | .github/workflows/pil-conformance.yml |

---

## 2. Version Binding

| Component | Version | Binding |
|-----------|---------|---------|
| Release | 0.6.0 | - |
| Protocol | 0.6.0 | Atomic with release |
| Constants | 0.6.0 | Atomic with protocol |
| PIL Extraction | 0.3 | Compatible with protocol |
| Test Vectors | 0.1 | Locked to PIL extraction |

**Version Coupling Rules:**
- Protocol and Constants versions are atomically coupled (CONSTANTS-001)
- PIL extraction is forward-compatible with protocol versions
- Test vectors are immutable for their specified PIL version

---

## 3. Artifact Registry

**File:** `artifacts/Artifact_Registry_v0.6.0.json`

**Contents:**
- 28 artifacts registered
- SHA256 hashes for all files
- Sorted by path (deterministic)
- Validated by test suite

**Registry Fields:**
- `version`: 0.6.0
- `protocol_version`: 0.6.0
- `pil_extraction_version`: 0.3
- `pil_vectors_version`: 0.1

---

## 4. Validation Commands Executed

```bash
# Syntax check
python -m py_compile client/pil_extraction/*.py tests/pil_extraction/*.py

# Official test vectors (20)
PYTHONPATH=. python tests/pil_extraction/test_runner_pil.py

# Full pytest suite (79 tests)
PYTHONPATH=. pytest tests/pil_extraction -v --tb=short
```

---

## 5. Validation Results

### 5.1 PIL Extraction Test Vectors

| Test Suite | Result |
|------------|--------|
| Official vectors | **20/20 PASS** |
| pil_tv_0001 - pil_tv_0020 | All passed |

### 5.2 Conformance Test Suite

| Test Category | Count | Result |
|---------------|-------|--------|
| Artifact Registry | 6 | PASS |
| Hash Validation | 3 | PASS |
| Completeness | 1 | PASS |
| Contract Validation | 16 | PASS |
| PIL Vectors (pytest) | 22 | PASS |
| Regression | 31 | PASS |
| **Total** | **79** | **PASS** |

### 5.3 Contract Verification

| Check | Result |
|-------|--------|
| Valid statuses (5) | ✅ |
| PIL fields (9) | ✅ |
| All fields string type | ✅ |
| OK has PIL object | ✅ |
| Non-OK has no PIL | ✅ |
| Deterministic output | ✅ |
| 1:1 mapping to REFERENCE | ✅ |
| Empty string preserved | ✅ |

### 5.4 Artifact Hash Validation

| Check | Result |
|-------|--------|
| All files exist | ✅ |
| All hashes match | ✅ |
| No unauthorized mods | ✅ |
| Required artifacts present | ✅ |
| Paths sorted | ✅ |

---

## 6. Release Package Confirmation

### 6.1 Deterministic

✅ **CONFIRMED**

- Output identical across repeated runs
- No random or time-dependent behavior
- Hash validation reproducible

### 6.2 Reproducible

✅ **CONFIRMED**

- All dependencies specified
- All versions locked
- CI workflow matches local results

### 6.3 Version-Locked

✅ **CONFIRMED**

- Artifact registry with SHA256 hashes
- Version inventory JSON
- Immutable test vectors

### 6.4 Audit-Ready

✅ **CONFIRMED**

- Complete artifact registry
- Hash verification tests
- Contract validation tests
- Alignment report present

---

## 7. Residual Issues

**Residual issues: none**

---

## 8. Release Approval

This release package has been validated and is:

- ✅ Deterministic
- ✅ Reproducible
- ✅ Version-locked
- ✅ Audit-ready

**Release Status: APPROVED for v0.6.0**

---

*End of Report*
