# Public Release v0.6.0

**Document ID:** ML-RELEASE-v0.6.0  
**Version:** 1.0  
**Status:** Freeze  
**Date:** 2026-03-31  

---

## 1. Release Overview

This is the **deterministic public release** of Market Lens PIL Extraction v0.6.0.

### Release Type
- **Component:** PIL (Product Identity Linkage) Extraction
- **Purpose:** Deterministic product identity extraction from HTML
- **Audience:** Third-party verification, audit, reproducibility testing

---

## 2. Version Binding

| Component | Version | Status |
|-----------|---------|--------|
| Protocol | 0.6.0 | LOCKED |
| Constants | 0.6.0 | LOCKED |
| PIL Extraction Spec | 0.3 | LOCKED |
| Test Vectors | 0.1 | LOCKED |

---

## 3. Normative Documents

| Document ID | Version | Path |
|-------------|---------|------|
| DKP-PTL-REG-001 | 0.6 | `specs/DKP-PTL-REG-001.md` |
| DKP-PTL-REG-DATA-001 | 0.6 | `specs/DKP-PTL-REG-DATA-001.md` |
| DKP-PTL-REG-CONSTANTS-001 | 0.6 | `specs/DKP-PTL-REG-CONSTANTS-001.md` |
| DKP-PTL-REG-REFERENCE-001 | 0.6 | `specs/DKP-PTL-REG-REFERENCE-001.md` |
| DKP-PTL-REG-THREAT-001 | 0.6 | `specs/DKP-PTL-REG-THREAT-001.md` |
| DKP-PTL-REG-GOV-001 | 0.6 | `specs/DKP-PTL-REG-GOV-001.md` |
| DKP-PTL-REG-CLIENT-001 | 0.3 | `specs/DKP-PTL-REG-CLIENT-001.md` |
| DKP-PTL-REG-PIL-EXTRACTION-001 | 0.3 | `specs/DKP-PTL-REG-PIL-EXTRACTION-001.md` |
| DKP-PTL-REG-PIL-TEST-VECTORS-001 | 0.1 | `specs/DKP-PTL-REG-PIL-TEST-VECTORS-001.md` |

---

## 4. Artifact Registry

### Location
```
artifacts/Artifact_Registry_v0.6.0.json
```

### Contents
- SHA256 hashes for all normative documents
- SHA256 hashes for PIL extraction implementation
- SHA256 hashes for test files
- SHA256 hashes for CI workflow

### Verification
```bash
PYTHONPATH=. pytest tests/pil_extraction/test_artifacts.py -v
```

---

## 5. Test Vectors

### Location
```
tests/pil_extraction/vectors/pil_vectors_v0_1.json
```

### Count
- **20 official test vectors** (pil_tv_0001 through pil_tv_0020)
- Locked per DKP-PTL-REG-PIL-TEST-VECTORS-001 v0.1

### Verification
```bash
PYTHONPATH=. python tests/pil_extraction/test_runner_pil.py
```

---

## 6. How to Reproduce

### Prerequisites
```bash
pip install pytest beautifulsoup4 lxml
```

### Full Verification
```bash
bash scripts/reproduce_release.sh
```

### Manual Steps
1. Clone repository
2. Install dependencies
3. Run artifact hash verification
4. Run test vectors
5. Run full test suite
6. Verify determinism (3 runs per vector)

---

## 7. Determinism Guarantee

### Verified Properties
- Same input → same output (bit-for-bit)
- 20 vectors × 3 runs = 60 identical outputs
- No randomness in extraction pipeline
- No external dependencies that vary

### Validation Result
```
DETERMINISM STATUS: PASS
VECTORS TESTED: 20
RUNS PER VECTOR: 3
```

---

## 8. Build Environment

| Property | Value |
|----------|-------|
| OS | Linux |
| Python | 3.10+ |
| beautifulsoup4 | 4.10.0+ |
| lxml | 4.8.0+ |

---

## 9. Release Artifacts

| Artifact | Path |
|----------|------|
| Artifact Registry | `artifacts/Artifact_Registry_v0.6.0.json` |
| Version Inventory | `artifacts/Version_Inventory_v0.6.0.json` |
| Version Manifest | `artifacts/version_manifest_v0.6.0.json` |
| Reproducibility Script | `scripts/reproduce_release.sh` |
| CI Workflow | `.github/workflows/pil-conformance.yml` |

---

## 10. Validation Summary

| Check | Status |
|-------|--------|
| Artifact hashes match | ✓ PASS |
| Test vectors pass (20/20) | ✓ PASS |
| Full test suite (79/79) | ✓ PASS |
| Determinism verified | ✓ PASS |
| Vector count lock (20) | ✓ PASS |

---

## 11. Constraints

### PROHIBITED
- Changing formulas
- Changing constants
- Changing pipeline logic
- Adding heuristics
- Adding ML/AI
- Changing rounding

### REQUIRED FOR CHANGES
- Version increment per GOV-001
- New test vectors
- Updated artifact registry
- Full re-verification

---

## 12. Release Status

```
RELEASE STATUS: PASS
```

---

*This release is deterministic, reproducible, and verifiable by any third party.*

*End of Document*
