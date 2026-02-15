# Market Lens

**Deterministic Price Transparency Engine (DKP-PTL-REG v0.6 Reference Implementation)**

> ⚠️ **Frozen v0.6.0. All specifications, constants, and test vectors are immutable. Any change requires a version bump to v0.7+ with full regeneration of test vectors and artifact registry.**

---

## Project Description

Market Lens is the canonical reference implementation of the DKP-PTL-REG v0.6 Pricing Transparency Registry Protocol. It provides a fully deterministic, evidence-bound engine for computing market reference prices from publicly observable price observations.

The engine:
- Validates and normalizes input observations per **REFERENCE-001 v0.6**
- Executes the 18-step deterministic pipeline per **DATA-001 v0.6**
- Applies atomic constant profiles (BASE / HARDENED) per **CONSTANTS-001 v0.6**
- Computes integrity status per **THREAT-001 v0.6**
- Emits versioned output per **GOV-001 v0.6**

### Language Choice: Python

Python was chosen for the reference implementation because:
1. **IEEE 754 compliance**: Python `float` is IEEE 754 double precision by specification
2. **Deterministic rounding**: Python's `round()` uses banker's rounding (round half to even) — exactly as required
3. **No implicit locale**: Python string operations are locale-independent by default
4. **Readability**: Reference implementations prioritize auditability over performance
5. **Cross-platform**: Identical behavior across Linux, macOS, and Windows

---

## Architecture Summary

```
Input JSON (observations)
       │
       ▼
┌─────────────────────────┐
│  REFERENCE-001          │  Input Boundary
│  - NFC normalization    │
│  - PSL domain extract   │
│  - Timestamp canon.     │
│  - Evidence hash (JCS)  │
│  - Rejection filtering  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  DATA-001 Pipeline      │  18 Deterministic Steps
│  - Identity scope       │
│  - Temporal validation  │
│  - Burst detection      │
│  - Domain cap           │
│  - Weighted median      │
│  - Similarity clusters  │
│  - Outlier filtering    │
│  - Confidence score     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  THREAT-001             │  Integrity Status
│  - COLD_START           │
│  - BURST_DETECTED       │
│  - DOMAIN_DOMINANCE     │
│  - CLUSTER_COLLAPSE     │
│  - NORMAL               │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Output JSON            │  Versioned, Deterministic
│  - P_ref, MAD, CS       │
│  - N_eff                │
│  - integrity_status     │
│  - applied_profile      │
│  - protocol_version     │
│  - constants_version    │
└─────────────────────────┘
```

---

## Determinism Guarantees

This engine guarantees:

| Requirement | Implementation |
|---|---|
| IEEE 754 double precision | Python native `float` |
| Round half to even | Python `round()` (banker's rounding) |
| 6 decimal places for exposed metrics | Applied before output serialization |
| Stable sorting | Python `list.sort()` is stable (Timsort) |
| No randomness | No `random`, no `uuid`, no entropy sources |
| No ML | No machine learning, no adaptive thresholds |
| No network calls | Engine is fully offline |
| No system locale | Unicode casefold, NFC normalization |
| No system timezone | All times are UTC integer seconds |
| No implicit recomputation | Step 11 recompute occurs exactly once |
| No recursion | Linear pipeline execution |
| Deterministic tie-breaking | Binary comparison of (domain_id, merchant_id, timestamp, price) |

Given identical input and identical `current_time_utc`, the engine **MUST** produce byte-identical JSON output across all compliant environments.

---

## Version Coupling Rules

Per **GOV-001 v0.6**:

- `protocol_version` = `0.6.0`
- `constants_version` = `0.6.0`

These are atomically coupled. Any modification to any constant requires:
1. `protocol_version` increment
2. `constants_version` increment
3. Public changelog publication
4. Regeneration of official test vectors

No silent modification is permitted.

---

## CLI Usage

### Basic Usage

```bash
dkp-ptl-reg-engine run \
  --input input.json \
  --profile BASE \
  --current_time_utc 1700000000
```

### Running as Python Module

```bash
python -m engine.src run \
  --input input.json \
  --profile BASE \
  --current_time_utc 1700000000
```

### Parameters

| Parameter | Required | Description |
|---|---|---|
| `--input` | Yes | Path to input JSON file containing observations |
| `--profile` | Yes | Constants profile: `BASE` or `HARDENED` |
| `--current_time_utc` | Yes | Current time as Unix epoch seconds (UTC). Engine never reads system clock implicitly. |

### Input JSON Format

```json
{
  "observations": [
    {
      "source_url": "https://shop.example.com/product/123",
      "merchant_id": "example_merchant",
      "price": 99.99,
      "currency": "usd",
      "region": "us",
      "timestamp": 1699900000,
      "product_identity_layer": {
        "brand": "BrandName",
        "model": "ModelX",
        "sku": "SKU001",
        "condition": "new",
        "bundle_flag": "false",
        "warranty_type": "standard",
        "region_variant": "",
        "storage_or_size": "256gb",
        "release_year": "2025"
      }
    }
  ]
}
```

### Output JSON Format

```json
{
  "applied_profile": "BASE",
  "protocol_version": "0.6.0",
  "constants_version": "0.6.0",
  "identity_scope_level": 0,
  "P_ref": 100.0,
  "MAD": 1.5,
  "CS": 0.482351,
  "N_eff": 4.876543,
  "cold_start_flag": false,
  "insufficient_data_flag": false,
  "integrity_status": "NORMAL"
}
```

---

## Reproducibility Instructions

### Prerequisites

- Python >= 3.10
- No external dependencies required (stdlib only)

### Setup

```bash
git clone https://github.com/anahronic/market-lens.git
cd market-lens
pip install -e .
```

### Verify Test Vectors (byte-for-byte)

```bash
# Compare engine output against committed expected.json files
python -m engine.tests.test_runner

# Run full pytest suite
pytest engine/tests/ -v
```

### Verify Determinism

```bash
# Run each test vector twice and compare in-memory (no file writes)
python scripts/det_check.py
```

### Verify PSL Snapshot

```bash
sha256sum engine/src/psl_snapshot/PSL-2026-01-01.dat
```

Expected SHA256: `edee63489085821c1744bbc9225bb1ff9edd34f8451f1379273e124ebf5083cf`

This must match the value recorded in `artifact_registry/Artifact_Registry_v0.6.json`.

---

## PSL Snapshot

| Property | Value |
|---|---|
| Filename | `PSL-2026-01-01.dat` |
| Location | `engine/src/psl_snapshot/` |
| Version | PSL-2026-01-01 |
| SHA256 | `edee63489085821c1744bbc9225bb1ff9edd34f8451f1379273e124ebf5083cf` |

The PSL snapshot is version-pinned per **REFERENCE-001 v0.6** and must not be modified without a version increment.

---

## Test Vectors

Six mandatory deterministic test vectors are included:

| Test Vector | Scenario | Key Assertions |
|---|---|---|
| `uniform_market` | 5 domains, similar prices | Stable P_ref, NORMAL status |
| `burst_attack` | One domain floods observations | BURST_DETECTED, weight suppression |
| `domain_dominance` | One domain > 30% weight | DOMAIN_DOMINANCE, cap enforcement |
| `cluster_injection` | Near-duplicate Sybil injection | Cluster penalty, similarity discount |
| `cold_start` | Single observation only | COLD_START, P_ref=null, CS=0 |
| `zero_mad` | All identical prices | MAD=0, no outlier exclusion |

---

## Repository Structure

```
market-lens/
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
├── RELEASE_CHECKLIST_v0.6.0.md
├── .github/
│   └── workflows/
│       └── ci.yml
├── engine/
│   ├── __init__.py
│   ├── src/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── cli.py
│   │   ├── constants.py
│   │   ├── data_pipeline.py
│   │   ├── json_canonical.py
│   │   ├── reference_boundary.py
│   │   ├── threat_status.py
│   │   └── psl_snapshot/
│   │       └── PSL-2026-01-01.dat
│   └── tests/
│       ├── __init__.py
│       ├── test_engine.py
│       ├── test_runner.py
│       └── test_vectors/
│           ├── *_input.json
│           └── *_expected.json
├── Protocols/
│   ├── DKP-PTL-REG-001.md
│   ├── DKP-PTL-REG-DATA-001.md
│   ├── DKP-PTL-REG-CONSTANTS-001_.md
│   ├── DKP-PTL-REG-REFERENCE-001.md
│   ├── DKP-PTL-REG-THREAT-001.md
│   ├── DKP-PTL-REG-GOV-001.md
│   └── DKP-PTL-REG Implementation Roadmap.md
├── artifact_registry/
│   └── Artifact_Registry_v0.6.json
└── scripts/
    ├── det_check.py
    ├── generate_artifact_registry.py
    ├── dump_expected.py
    ├── show_expected.py
    ├── init_git.sh
    └── setup_repo.sh
```

---

## Specification Alignment

This implementation is aligned with the following frozen specifications:

| Document | Version | Status |
|---|---|---|
| DKP-PTL-REG-001 | v0.6 | Frozen |
| DKP-PTL-REG-DATA-001 | v0.6 | Frozen |
| DKP-PTL-REG-CONSTANTS-001 | v0.6 | Frozen |
| DKP-PTL-REG-REFERENCE-001 | v0.6 | Frozen |
| DKP-PTL-REG-THREAT-001 | v0.6 | Frozen |
| DKP-PTL-REG-GOV-001 | v0.6 | Frozen |

---

## License

MIT License. See [LICENSE](LICENSE).
