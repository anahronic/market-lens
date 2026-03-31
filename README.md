# Market Lens Release Package

**Document ID:** ML-RELEASE-README-001  
**Version:** 1.0  
**Status:** Freeze  
**Release:** v0.6.0  
**Date:** 2026-03-31  

---

## What This Package Is

This is the **release-ready bundle** for Market Lens v0.6.0 — a deterministic price observation and measurement platform. The package contains:

- Normative protocol specifications
- Legal documentation
- PIL (Product Identity Linkage) extraction implementation
- Conformance test suite
- CI workflow for automated validation

---

## What Is Included

### Normative Documents (`specs/`)

| Document | Version | Status |
|----------|---------|--------|
| DKP-PTL-REG-001 (Protocol) | 0.6 | Frozen |
| DKP-PTL-REG-DATA-001 | 0.6 | Frozen |
| DKP-PTL-REG-CONSTANTS-001 | 0.6 | Frozen |
| DKP-PTL-REG-REFERENCE-001 | 0.6 | Frozen |
| DKP-PTL-REG-THREAT-001 | 0.6 | Frozen |
| DKP-PTL-REG-GOV-001 | 0.6 | Frozen |
| DKP-PTL-REG-CLIENT-001 | 0.6 | Frozen |
| DKP-PTL-REG-PIL-EXTRACTION-001 | 0.3 | Frozen |
| DKP-PTL-REG-PIL-TEST-VECTORS-001 | 0.1 | Frozen |

### Legal Documents (`docs/legal/`)

| Document | ID | Version |
|----------|----|---------|
| Privacy Policy | ML-LEGAL-PRIVACY-001 | 1.0 |
| Terms of Use | ML-LEGAL-TOU-001 | 1.0 |
| Disclaimer | ML-LEGAL-DISCLAIMER-001 | 1.0 |
| Data Dispute Policy | ML-LEGAL-DISPUTE-001 | 1.0 |

### Release Documentation (`docs/`)

- Deterministic Release Report v0.6.0
- Release Freeze Note v0.6.0
- PIL to Reference Contract v0.6
- PIL Extraction Alignment Report

### Artifacts (`artifacts/`)

- Artifact Registry v0.6.0 (SHA256 hashes)
- Version Inventory v0.6.0

### Implementation (`client/pil_extraction/`)

Deterministic PIL extraction module:
- `extractor.py` — Main extraction pipeline
- `constants.py` — Canonical constants
- `normalization.py` — Text normalization
- `schemas.py` — Output schemas
- `source_collectors.py` — Source precedence logic
- `title_parser.py` — Title parsing
- `url_tokens.py` — URL token extraction
- `page_unit.py` — Page unit detection
- `mappings.py` — Field mappings

### Tests (`tests/pil_extraction/`)

- `test_pil_vectors.py` — Official test vectors (20)
- `test_contract.py` — Output contract validation
- `test_artifacts.py` — Artifact hash validation
- `test_regression.py` — Regression test suite
- `test_runner_pil.py` — Standalone test runner
- `vectors/pil_vectors_v0_1.json` — Test vector data

### CI (`.github/workflows/`)

- `pil-conformance.yml` — Conformance gate workflow

---

## What Is NOT Included

- Raw observation data
- Production database content
- Other services (API, worker, ingestion)
- Development tooling
- Editor/IDE configuration
- Cache directories (`__pycache__`, `.pytest_cache`)
- Version control history (`.git`)

---

## Where to Find Things

| Content | Location |
|---------|----------|
| Protocol specifications | `specs/` |
| Legal documents | `docs/legal/` |
| Release reports | `docs/` |
| Artifact hashes | `artifacts/` |
| PIL implementation | `client/pil_extraction/` |
| Conformance tests | `tests/pil_extraction/` |
| CI workflow | `.github/workflows/` |

---

## Running Conformance Tests

### Prerequisites

```bash
pip install pytest beautifulsoup4 lxml
```

### Run All Tests

```bash
pytest tests/pil_extraction/ -v
```

### Run Official Test Vectors Only

```bash
python tests/pil_extraction/test_runner_pil.py
```

### Validate Artifact Hashes

```bash
pytest tests/pil_extraction/test_artifacts.py -v
```

---

## Deterministic Guarantee

This package is **deterministic and version-bound**:

- Normative logic is frozen in included specifications
- All outputs are reproducible given identical inputs
- Changes require version increment per GOV-001 governance
- Historical versions remain immutable

---

## License

This repository is **source-available** under the Market Lens Non-Commercial Source License v1.0.

**Permitted without permission:**
- Inspection, study, and learning
- Personal and academic use
- Research and reproducibility verification
- Non-commercial prototypes

**Requires written permission:**
- Commercial use of any kind

See [LICENSE](LICENSE) for complete terms.  
See [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) for commercial licensing information.

---

*End of Document*
