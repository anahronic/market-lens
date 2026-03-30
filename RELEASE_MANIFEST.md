# Release Manifest

**Document ID:** ML-RELEASE-MANIFEST-001  
**Version:** 1.0  
**Status:** Freeze  
**Release:** v0.6.0  
**Date:** 2026-03-31  

---

## Release Package

**Name:** Market Lens Release Package v0.6.0  
**Purpose:** Public release bundle containing normative specifications, legal documentation, deterministic implementation, and conformance tests.  

---

## Included Directories

| Directory | Purpose |
|-----------|---------|
| `specs/` | Normative protocol specifications |
| `docs/` | Release documentation |
| `docs/legal/` | Legal documents |
| `artifacts/` | Version registry and hash artifacts |
| `client/pil_extraction/` | PIL extraction implementation |
| `tests/pil_extraction/` | Conformance test suite |
| `.github/workflows/` | CI conformance workflow |

---

## Included Normative Documents

| Document ID | Version | File |
|-------------|---------|------|
| DKP-PTL-REG-001 | 0.6 | `specs/DKP-PTL-REG-001.md` |
| DKP-PTL-REG-DATA-001 | 0.6 | `specs/DKP-PTL-REG-DATA-001.md` |
| DKP-PTL-REG-CONSTANTS-001 | 0.6 | `specs/DKP-PTL-REG-CONSTANTS-001.md` |
| DKP-PTL-REG-REFERENCE-001 | 0.6 | `specs/DKP-PTL-REG-REFERENCE-001.md` |
| DKP-PTL-REG-THREAT-001 | 0.6 | `specs/DKP-PTL-REG-THREAT-001.md` |
| DKP-PTL-REG-GOV-001 | 0.6 | `specs/DKP-PTL-REG-GOV-001.md` |
| DKP-PTL-REG-CLIENT-001 | 0.6 | `specs/DKP-PTL-REG-CLIENT-001.md` |
| DKP-PTL-REG-PIL-EXTRACTION-001 | 0.3 | `specs/DKP-PTL-REG-PIL-EXTRACTION-001.md` |
| DKP-PTL-REG-PIL-TEST-VECTORS-001 | 0.1 | `specs/DKP-PTL-REG-PIL-TEST-VECTORS-001.md` |

---

## Included Legal Documents

| Document ID | Version | Status | File |
|-------------|---------|--------|------|
| ML-LEGAL-PRIVACY-001 | 1.0 | Freeze | `docs/legal/Privacy_Policy.md` |
| ML-LEGAL-TOU-001 | 1.0 | Freeze | `docs/legal/Terms_of_Use.md` |
| ML-LEGAL-DISCLAIMER-001 | 1.0 | Freeze | `docs/legal/Disclaimer.md` |
| ML-LEGAL-DISPUTE-001 | 1.0 | Freeze | `docs/legal/Data_Dispute_Policy.md` |

---

## Included Implementation Scope

**Module:** `client/pil_extraction/`

| File | Purpose |
|------|---------|
| `__init__.py` | Package init |
| `constants.py` | Canonical constants and patterns |
| `extractor.py` | Main extraction pipeline |
| `mappings.py` | Field mapping rules |
| `normalization.py` | Text normalization functions |
| `page_unit.py` | Page unit detection |
| `schemas.py` | Output schemas |
| `source_collectors.py` | Source precedence logic |
| `title_parser.py` | Title parsing |
| `url_tokens.py` | URL token extraction |
| `README.md` | Module documentation |

---

## Included Tests

**Suite:** `tests/pil_extraction/`

| File | Tests | Purpose |
|------|-------|---------|
| `test_pil_vectors.py` | 22 | Official test vectors + meta |
| `test_contract.py` | 9 | Output contract validation |
| `test_artifacts.py` | 1 | Artifact hash verification |
| `test_regression.py` | 31 | Regression coverage |
| `test_runner_pil.py` | 20 | Standalone runner |
| `vectors/pil_vectors_v0_1.json` | — | Test vector data |

---

## Excluded Files Policy

The following are explicitly excluded from the release package:

- `__pycache__/` — Python bytecode cache
- `.pytest_cache/` — pytest cache
- `.mypy_cache/` — mypy cache
- `.venv/`, `venv/` — Virtual environments
- `.git/` — Version control history
- `.DS_Store`, `Thumbs.db` — OS metadata
- Editor temp files (`*.swp`, `*~`)
- Backup files
- Local scratch notes
- Obsolete draft documents
- Legacy experiment files outside release scope

---

## Version Statement

**Normative documents retain original versions:**

- Protocol bundle: v0.6
- PIL Extraction spec: v0.3
- PIL Test Vectors spec: v0.1

**Release/Legal layer documents use Version 1.0 Freeze:**

- All documents in `docs/legal/`
- `README.md`
- `RELEASE_MANIFEST.md`
- `ASSEMBLY_REPORT.md`

This separation ensures governance compliance: normative specifications are not retroactively re-versioned; only release packaging documents receive the 1.0 Freeze marker.

---

## Package Purpose Statement

This package is assembled for:

- **Publication:** Public release of Market Lens v0.6.0
- **Audit:** Complete artifact set for compliance review
- **Reproducibility:** All normative logic frozen and version-bound
- **Deployment:** Ready for integration or distribution

---

## Validation Commands

### Syntax Check

```bash
python -m py_compile client/pil_extraction/*.py
```

### Official Test Vectors

```bash
python tests/pil_extraction/test_runner_pil.py
```

### Full Conformance Suite

```bash
pytest tests/pil_extraction/ -v
```

### Artifact Hash Validation

```bash
pytest tests/pil_extraction/test_artifacts.py -v
```

---

*End of Document*
