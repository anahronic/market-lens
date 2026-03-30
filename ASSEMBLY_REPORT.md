# Assembly Report

**Document ID:** ML-RELEASE-ASSEMBLY-001  
**Version:** 1.0  
**Status:** Freeze  
**Release:** v0.6.0  
**Date:** 2026-03-31  

---

## 1. Legal Documents Created

| Document | ID | Version | Status | Path |
|----------|----|---------|--------|------|
| Privacy Policy | ML-LEGAL-PRIVACY-001 | 1.0 | Freeze | `docs/legal/Privacy_Policy.md` |
| Terms of Use | ML-LEGAL-TOU-001 | 1.0 | Freeze | `docs/legal/Terms_of_Use.md` |
| Disclaimer | ML-LEGAL-DISCLAIMER-001 | 1.0 | Freeze | `docs/legal/Disclaimer.md` |
| Data Dispute Policy | ML-LEGAL-DISPUTE-001 | 1.0 | Freeze | `docs/legal/Data_Dispute_Policy.md` |

**Status:** All 4 legal documents created and publication-ready.

---

## 2. Release Documents Included

| Document | Path |
|----------|------|
| Deterministic Release Report v0.6.0 | `docs/Deterministic_Release_Report_v0.6.0.md` |
| Release Freeze Note v0.6.0 | `docs/RELEASE_FREEZE_NOTE_v0.6.0.md` |
| PIL to Reference Contract v0.6 | `docs/PIL_TO_REFERENCE_CONTRACT_v0.6.md` |
| PIL Extraction Alignment Report | `docs/PIL_EXTRACTION_ALIGNMENT_REPORT.md` |
| README | `README.md` |
| Release Manifest | `RELEASE_MANIFEST.md` |
| Assembly Report | `ASSEMBLY_REPORT.md` |

---

## 3. Normative Documents Copied

| Document ID | Original Version | Path |
|-------------|------------------|------|
| DKP-PTL-REG-001 | 0.6 | `specs/DKP-PTL-REG-001.md` |
| DKP-PTL-REG-DATA-001 | 0.6 | `specs/DKP-PTL-REG-DATA-001.md` |
| DKP-PTL-REG-CONSTANTS-001 | 0.6 | `specs/DKP-PTL-REG-CONSTANTS-001.md` |
| DKP-PTL-REG-REFERENCE-001 | 0.6 | `specs/DKP-PTL-REG-REFERENCE-001.md` |
| DKP-PTL-REG-THREAT-001 | 0.6 | `specs/DKP-PTL-REG-THREAT-001.md` |
| DKP-PTL-REG-GOV-001 | 0.6 | `specs/DKP-PTL-REG-GOV-001.md` |
| DKP-PTL-REG-CLIENT-001 | 0.6 | `specs/DKP-PTL-REG-CLIENT-001.md` |
| DKP-PTL-REG-PIL-EXTRACTION-001 | 0.3 | `specs/DKP-PTL-REG-PIL-EXTRACTION-001.md` |
| DKP-PTL-REG-PIL-TEST-VECTORS-001 | 0.1 | `specs/DKP-PTL-REG-PIL-TEST-VECTORS-001.md` |

**Version Status:** All normative documents retain their original frozen versions. No documents were re-versioned to 1.0.

---

## 4. Implementation Files Included

| File | Path |
|------|------|
| `__init__.py` | `client/pil_extraction/__init__.py` |
| `constants.py` | `client/pil_extraction/constants.py` |
| `extractor.py` | `client/pil_extraction/extractor.py` |
| `mappings.py` | `client/pil_extraction/mappings.py` |
| `normalization.py` | `client/pil_extraction/normalization.py` |
| `page_unit.py` | `client/pil_extraction/page_unit.py` |
| `schemas.py` | `client/pil_extraction/schemas.py` |
| `source_collectors.py` | `client/pil_extraction/source_collectors.py` |
| `title_parser.py` | `client/pil_extraction/title_parser.py` |
| `url_tokens.py` | `client/pil_extraction/url_tokens.py` |
| `README.md` | `client/pil_extraction/README.md` |

**Total:** 11 implementation files

---

## 5. Tests Included

| File | Path |
|------|------|
| `__init__.py` | `tests/pil_extraction/__init__.py` |
| `test_artifacts.py` | `tests/pil_extraction/test_artifacts.py` |
| `test_contract.py` | `tests/pil_extraction/test_contract.py` |
| `test_pil_vectors.py` | `tests/pil_extraction/test_pil_vectors.py` |
| `test_regression.py` | `tests/pil_extraction/test_regression.py` |
| `test_runner_pil.py` | `tests/pil_extraction/test_runner_pil.py` |
| `pil_vectors_v0_1.json` | `tests/pil_extraction/vectors/pil_vectors_v0_1.json` |

**Total:** 7 test files

---

## 6. Artifacts Included

| File | Path |
|------|------|
| Artifact Registry v0.6.0 | `artifacts/Artifact_Registry_v0.6.0.json` |
| Version Inventory v0.6.0 | `artifacts/Version_Inventory_v0.6.0.json` |

---

## 7. CI Workflow Included

| File | Path |
|------|------|
| PIL Conformance Workflow | `.github/workflows/pil-conformance.yml` |

---

## 8. Files Excluded as Garbage

The following were explicitly excluded from the release package:

| Category | Examples |
|----------|----------|
| Python cache | `__pycache__/`, `*.pyc` |
| Test cache | `.pytest_cache/` |
| Type cache | `.mypy_cache/` |
| Virtual envs | `.venv/`, `venv/` |
| Version control | `.git/` |
| OS metadata | `.DS_Store`, `Thumbs.db` |
| Editor temps | `*.swp`, `*~` |
| Other services | `api/`, `worker/`, `ingestion/`, `service/`, `engine/`, `deploy/`, `scripts/` |
| Non-release docs | Draft files, scratch notes |

---

## 9. Version Governance Compliance

### Normative Document Versions Preserved

| Document | Version in Source | Version in Package |
|----------|-------------------|-------------------|
| DKP-PTL-REG-001 | 0.6 | 0.6 ✓ |
| DKP-PTL-REG-DATA-001 | 0.6 | 0.6 ✓ |
| DKP-PTL-REG-CONSTANTS-001 | 0.6 | 0.6 ✓ |
| DKP-PTL-REG-REFERENCE-001 | 0.6 | 0.6 ✓ |
| DKP-PTL-REG-THREAT-001 | 0.6 | 0.6 ✓ |
| DKP-PTL-REG-GOV-001 | 0.6 | 0.6 ✓ |
| DKP-PTL-REG-CLIENT-001 | 0.6 | 0.6 ✓ |
| DKP-PTL-REG-PIL-EXTRACTION-001 | 0.3 | 0.3 ✓ |
| DKP-PTL-REG-PIL-TEST-VECTORS-001 | 0.1 | 0.1 ✓ |

**Result:** No normative documents were re-versioned to 1.0. All original versions preserved.

### Legal/Release Layer Versions

| Document Type | Version | Status |
|---------------|---------|--------|
| Legal documents (4) | 1.0 | Freeze |
| README | 1.0 | Freeze |
| RELEASE_MANIFEST | 1.0 | Freeze |
| ASSEMBLY_REPORT | 1.0 | Freeze |

**Result:** Only release packaging documents received Version 1.0 Freeze.

---

## 10. Validation Results

### Tests Executed (Source Repository)

| Test Suite | Result |
|------------|--------|
| Official Test Vectors (20) | 20/20 PASS |
| Pytest Full Suite | 79/79 PASS |

### Package Integrity

| Check | Result |
|-------|--------|
| Total files in package | 41 |
| Garbage files detected | 0 |
| Empty required files | 0 |
| Duplicate document IDs | 0 |
| File link consistency | PASS |
| Artifact registry present | PASS |
| Version inventory present | PASS |

---

## 11. Package Summary

| Metric | Count |
|--------|-------|
| Legal documents | 4 |
| Normative specs | 9 |
| Release docs | 7 |
| Artifact files | 2 |
| Implementation files | 11 |
| Test files | 7 |
| CI workflows | 1 |
| **Total files** | **41** |

---

## 12. Conclusion

### Package Status: READY

The release package is:

- **Complete:** All required documents, implementation, and tests included
- **Clean:** No garbage files, cache directories, or obsolete content
- **Version-consistent:** Normative docs retain original versions; legal/release docs use 1.0 Freeze
- **Tested:** 79/79 tests pass in source repository
- **Publication-ready:** Suitable for distribution or audit

---

*End of Document*
