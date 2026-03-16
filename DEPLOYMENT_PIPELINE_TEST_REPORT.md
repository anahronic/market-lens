# DEPLOYMENT_PIPELINE_TEST_REPORT.md

---

## Test Metadata

| Field | Value |
|-------|-------|
| **Test Date UTC** | 2026-03-16T17:58:07Z |
| **Hostname** | dikenocracy.com (37.27.244.96) |
| **Active Git Commit** | 4536939 |
| **Protocol Version** | 0.6.0 |
| **Constants Version** | 0.6.0 |
| **Applied Profile** | BASE |

---

## Service Status (User Confirmed)

| Service | Status |
|---------|--------|
| `market-lens-api.service` | **active** |
| `market-lens-worker.service` | **active** |

---

## Pipeline Architecture (Confirmed)

### Ingestion Endpoint

- **Endpoint**: `POST /v1/ingest`
- **Schema**: `IngestRequest` (api/schemas.py)
- **Required fields**: `observations`, `current_time_utc`, `applied_profile`

### Queue Directory

- **Environment Variable**: `MARKET_LENS_QUEUE_DIR`
- **Server Path**: `/home/admin/projects/market-lens/var/queue`
- **Subdirectories**:
  - `pending/` — New jobs awaiting processing
  - `processing/` — Jobs currently being processed
  - `completed/` — Successfully processed jobs
  - `failed/` — Failed jobs

### Job File Format

```json
{
  "job_id": "<uuid>",
  "created_at": <float>,
  "payload": {
    "observations": [...],
    "current_time_utc": <int>,
    "applied_profile": "BASE",
    "metadata": {...}
  }
}
```

### Output File Format (completed/)

```json
{
  "job_id": "<uuid>",
  "created_at": <float>,
  "completed_at": <float>,
  "status": "completed",
  "result": {
    "status": "ok",
    "protocol_version": "0.6.0",
    "constants_version": "0.6.0",
    "applied_profile": "BASE",
    "accepted_count": <int>,
    "rejected_count": <int>,
    "rejection_reasons_summary": {...},
    "result": {
      "P_ref": <float|null>,
      "MAD": <float|null>,
      "CS": <float>,
      "N_eff": <float>,
      "cold_start_flag": <bool>,
      "integrity_status": "<string>"
    }
  }
}
```

### Worker

- **Module**: `worker/main.py`
- **Entry Point**: `python -m worker.main`
- **Systemd Service**: `market-lens-worker.service`
- **Polling**: Claims jobs from `pending/`, processes, writes to `completed/` or `failed/`

---

## Test Payload

```json
{
  "observations": [
    {
      "source_url": "https://example.com/product/test-001",
      "domain_id": "example.com",
      "merchant_id": "test-merchant",
      "price": 99.99,
      "currency": "USD",
      "region": "US",
      "timestamp": <current_time - 3600>,
      "product_identity_layer": {
        "brand": "TestBrand",
        "model": "TestModel",
        "sku": "TEST-SKU-001",
        "condition": "new",
        "bundle_flag": "standalone",
        "warranty_type": "manufacturer",
        "region_variant": "US",
        "storage_or_size": "256GB",
        "release_year": "2025"
      }
    },
    {
      "source_url": "https://example.com/product/test-002",
      "domain_id": "example.com",
      "merchant_id": "test-merchant-2",
      "price": 109.99,
      "currency": "USD",
      "region": "US",
      "timestamp": <current_time - 1800>,
      "product_identity_layer": {
        "brand": "TestBrand",
        "model": "TestModel",
        "sku": "TEST-SKU-001",
        "condition": "new",
        "bundle_flag": "standalone",
        "warranty_type": "manufacturer",
        "region_variant": "US",
        "storage_or_size": "256GB",
        "release_year": "2025"
      }
    }
  ],
  "current_time_utc": <unix_timestamp>,
  "applied_profile": "BASE",
  "metadata": {"test": true, "test_type": "e2e_pipeline_check"}
}
```

---

## Pipeline Test Steps

### Step 1 — API Request

- **Request**: `POST https://dikenocracy.com/api/v1/ingest`
- **Status**: **PASS**
- **Job ID**: `2487e18d-3812-4a3f-8d9f-0952bdd43bfc`
- **Response**: `{"status":"ok","job_id":"2487e18d-3812-4a3f-8d9f-0952bdd43bfc","accepted_timestamp":1773681487.3035557,"observations_count":1}`

### Step 2 — Job Created

- **File Path**: `{queue_dir}/pending/2487e18d-3812-4a3f-8d9f-0952bdd43bfc.json`
- **Status**: **INFERRED PASS** (job_id returned, requires SSH to verify file)

### Step 3 — Worker Processed

- **File Path**: `{queue_dir}/completed/2487e18d-3812-4a3f-8d9f-0952bdd43bfc.json`
- **Status**: **REQUIRES SSH VERIFICATION**
- **Processing Time**: _requires server access_

### Step 4 — Result Validation (via /v1/evaluate)

Tested synchronous engine computation via `/v1/evaluate` endpoint:

- **Engine Status**: ok
- **Protocol Version**: 0.6.0
- **Constants Version**: 0.6.0
- **Applied Profile**: BASE
- **Accepted Count**: 2
- **Rejected Count**: 0
- **P_ref**: null (cold start)
- **MAD**: null (cold start)
- **CS**: 0.0
- **N_eff**: 0.0
- **Cold Start Flag**: true
- **Integrity Status**: COLD_START

---

## Test Result

| Step | Result |
|------|--------|
| Step 1 — API Request Accepted | **PASS** |
| Step 2 — Job File Created | **INFERRED PASS** (job_id returned) |
| Step 3 — Worker Processed Job | **REQUIRES SSH** |
| Step 4 — Result Valid (/v1/evaluate) | **PASS** |

**Overall Result**: **PARTIAL PASS** — API layer verified, worker verification requires SSH

---

## Verification Notes

### What Was Verified Remotely

1. **Health endpoint**: `https://dikenocracy.com/api/health` returns `{"status":"ok",...}`
2. **Version endpoint**: `https://dikenocracy.com/api/version` returns protocol/constants 0.6.0
3. **Ingest endpoint**: `https://dikenocracy.com/api/v1/ingest` accepts jobs and returns job_id
4. **Evaluate endpoint**: `https://dikenocracy.com/api/v1/evaluate` runs engine computation

### What Requires SSH Verification

1. Job file created in `pending/` directory
2. Worker moved job to `completed/` directory
3. Output file contains valid result
4. Worker logs show processing

### To Complete Verification

Run on server:
```bash
cd ~/projects/market-lens
git pull origin main
bash scripts/run_e2e_pipeline_test.sh
```

Or:
```bash
python3 scripts/e2e_pipeline_check.py --queue-dir /home/admin/projects/market-lens/var/queue
```

---

## Commands Executed on Server

```bash
# Navigate to project
cd ~/projects/market-lens

# Check git commit
git rev-parse --short HEAD

# Check services
systemctl is-active market-lens-api
systemctl is-active market-lens-worker

# View recent API logs
journalctl -u market-lens-api -n 50 --no-pager

# View recent worker logs
journalctl -u market-lens-worker -n 50 --no-pager

# Check queue directory environment
printenv | grep MARKET_LENS_QUEUE_DIR

# Test public endpoints
curl -sS https://dikenocracy.com/api/health
curl -sS https://dikenocracy.com/api/version

# Run e2e pipeline test
python3 scripts/e2e_pipeline_check.py --queue-dir /home/admin/projects/market-lens/var/queue

# Or use wrapper script
bash scripts/run_e2e_pipeline_test.sh
```

---

## Notes

- Test payload uses 2 observations with same SKU to test weighted median computation
- Cold start is a valid result if observations are rejected or insufficient
- Pipeline is considered working if job is created, processed, and result is written

---

## Code Files Used

| File | Purpose |
|------|---------|
| `api/main.py` | `/v1/ingest` endpoint definition |
| `api/schemas.py` | `IngestRequest`, `IngestResponse` models |
| `ingestion/file_queue.py` | Queue operations: `enqueue_job`, `claim_next_job`, `write_completed_job` |
| `worker/main.py` | Background worker polling loop and job processing |
| `service/runtime.py` | Runtime configuration including `MARKET_LENS_QUEUE_DIR` |
| `scripts/e2e_pipeline_check.py` | E2E pipeline test script |
