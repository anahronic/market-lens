# DKP-PTL-REG v0.6 Release Audit Runbook

This document provides step-by-step procedures for auditing the Market Lens deployment against the frozen DKP-PTL-REG v0.6 protocol specification.

## Purpose

The release audit verifies that:
1. **Repository state** matches the frozen v0.6 specification
2. **Local runtime** uses correct artifacts and versions
3. **Server runtime** matches local deployment state

## Prerequisites

- Python 3.10+
- Git repository with clean working directory
- SSH access to server (for server audit)
- `curl` for API health checks

## Quick Start

```bash
# Full local audit (recommended first step)
./scripts/local_audit.sh

# Server audit (requires SSH)
./scripts/server_audit.sh root@dikenocracy.com /opt/market-lens
```

## Audit Components

### 1. Release Conformance Check

Verifies all release artifacts against the frozen specification.

```bash
python -m scripts.release_audit -v
```

**Checks performed:**
- Artifact registry integrity
- PSL snapshot hash verification
- Test vector completeness (6 cases)
- Spec bundle presence (6 documents)
- Version string consistency

**Expected output:**
```
Overall status: PASS
```

### 2. PSL Snapshot Verification

Verifies the Public Suffix List snapshot matches the recorded hash.

```bash
python scripts/check_psl_snapshot.py -v
```

**Location:** `engine/src/psl_snapshot/PSL-2026-01-01.dat`

### 3. Artifact Registry

The artifact registry contains SHA256 hashes of all specification-relevant files.

```bash
# Regenerate registry (updates hashes)
python scripts/generate_artifact_registry.py

# View registry
cat artifacts/Artifact_Registry_v0.6.json
```

**Registry sections:**
- `psl_snapshot` - PSL file hash
- `spec_documents` - Protocol specification hashes
- `canonical_specs` - Normalized spec bundle hashes
- `source_files` - Engine source code hashes
- `test_vectors` - Test vector file hashes

### 4. Version Inventory

Catalogs all version strings across the repository.

```bash
python scripts/generate_version_inventory.py
```

**Version sources:**
- `engine/src/constants.py`: `PROTOCOL_VERSION`, `CONSTANTS_VERSION`
- `service/version_info.py`: `ENGINE_VERSION`, `PSL_VERSION`
- `artifacts/Artifact_Registry_v0.6.json`

**Version Semantics Mapping Rule:**
- Document versions use MAJOR.MINOR format (e.g., "0.6")
- Code versions use SEMVER format (e.g., "0.6.0")
- Mapping: Document version X.Y maps to code version X.Y.Z
- PSL versions follow PSL-YYYY-MM-DD format

**Expected versions:**
- Protocol: `0.6.0`
- Constants: `0.6.0`
- Engine: `0.6.0`
- PSL: `PSL-2026-01-01`

### 5. Runtime Fingerprint Collection

Collects a snapshot of the runtime state for comparison.

```bash
# Local fingerprint
python scripts/collect_runtime_fingerprint.py

# With API query (if server running locally)
python scripts/collect_runtime_fingerprint.py --api-url http://localhost:8000
```

**Fingerprint includes:**
- Git commit and branch
- System information
- Artifact hashes
- Embedded version strings
- API version (if queried)

### 6. Fingerprint Comparison

Compares local and server fingerprints to detect discrepancies.

```bash
python scripts/compare_fingerprints.py \
    release_audit/local_fingerprint.json \
    release_audit/server_fingerprint.json
```

**Critical checks:**
- Git commit match
- Artifact hash match
- Version string match

## Full Audit Procedure

### Step 1: Local Audit

```bash
cd /path/to/market-lens
./scripts/local_audit.sh
```

This generates:
- `release_audit/release_conformance_report.json`
- `release_audit/version_inventory.json`
- `release_audit/local_fingerprint.json`

### Step 2: Verify Local Results

```bash
# Check conformance status
cat release_audit/release_conformance_report.json | jq '.summary'

# Expected:
# {
#   "total_checks": 22,
#   "passed": 22,
#   "failed": 0,
#   "warnings": 0,
#   "overall_status": "PASS"
# }
```

### Step 3: Server Audit

```bash
./scripts/server_audit.sh root@dikenocracy.com /opt/market-lens
```

This:
1. Tests SSH connectivity
2. Copies fingerprint collector to server
3. Runs fingerprint collection remotely
4. Downloads server fingerprint
5. Compares with local fingerprint

### Step 4: Review Comparison

If discrepancies are found, review:
- Git commits (is server at expected version?)
- Artifact hashes (were files modified on server?)
- Version strings (configuration drift?)

## Manual Server Checks

### Check API Health

```bash
curl -s https://dikenocracy.com/api/health | jq .
# Expected: {"status":"ok","service":"market-lens-api","protocol_version":"0.6.0",...}
```

### Check API Version

```bash
curl -s https://dikenocracy.com/api/version | jq .
# Expected: {"protocol_version":"0.6.0","constants_version":"0.6.0","engine_version":"0.6.0",...}
```

### Check Service Status (on server)

```bash
ssh root@dikenocracy.com "systemctl status market-lens-api market-lens-worker"
```

## Test Vector Verification

Run the engine against official test vectors:

```bash
cd engine
python -m pytest tests/ -v
```

To package test vectors for distribution:

```bash
python scripts/package_test_vectors.py
# Creates: artifacts/official_test_vectors_v0.6.zip
```

## Troubleshooting

### Conformance Check Fails

1. Check which specific check failed in the report
2. For hash mismatches: regenerate artifact registry and compare
3. For missing files: verify repository is complete

### SSH Connection Fails

1. Verify SSH key is loaded: `ssh-add -l`
2. Test connection: `ssh -v root@dikenocracy.com`
3. Check firewall/security groups

### Version Mismatch

1. Check git status: `git status`
2. Verify correct branch: `git branch -v`
3. Compare commits: local vs server

## Output Files Reference

| File | Purpose |
|------|---------|
| `release_audit/current_repo_state.json` | Initial audit findings |
| `release_audit/release_conformance_report.json` | Full conformance check results |
| `release_audit/version_inventory.json` | All version strings catalog |
| `release_audit/local_fingerprint.json` | Local runtime snapshot |
| `release_audit/server_fingerprint.json` | Server runtime snapshot |
| `artifacts/Artifact_Registry_v0.6.json` | SHA256 hashes of all artifacts |
| `artifacts/official_test_vectors_v0.6.zip` | Official test vectors archive |
| `test_vectors/v0.6/MANIFEST.json` | Test vector package manifest |

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/local_audit.sh` | Full local audit workflow |
| `scripts/server_audit.sh` | Server fingerprint collection |
| `scripts/check_psl_snapshot.py` | PSL hash verification |
| `scripts/generate_artifact_registry.py` | Regenerate artifact registry |
| `scripts/generate_version_inventory.py` | Catalog version strings |
| `scripts/collect_runtime_fingerprint.py` | Collect runtime state |
| `scripts/compare_fingerprints.py` | Compare local vs server |
| `scripts/package_test_vectors.py` | Package test vectors |
| `python -m scripts.release_audit` | Full conformance check |

## Protocol Version: v0.6

This runbook is specific to DKP-PTL-REG v0.6.0 (frozen).

For governance and versioning policy, see:
- `specs/dkp-ptl-reg/v0.6/DKP-PTL-REG-GOV-001.md`

## Runtime Data Directories

The following directories contain runtime/generated data and are excluded from version control:

| Directory | Purpose | Location (server) |
|-----------|---------|-------------------|
| `var/queue/pending/` | Jobs awaiting processing | `/home/admin/projects/market-lens/var/queue/pending/` |
| `var/queue/processing/` | Jobs currently being processed | `/home/admin/projects/market-lens/var/queue/processing/` |
| `var/queue/completed/` | Successfully processed jobs | `/home/admin/projects/market-lens/var/queue/completed/` |
| `var/queue/failed/` | Failed jobs | `/home/admin/projects/market-lens/var/queue/failed/` |
| `logs/` | Application logs | Varies by deployment |

These directories are listed in `.gitignore` and should never be committed. They are created automatically by the worker service at runtime.
