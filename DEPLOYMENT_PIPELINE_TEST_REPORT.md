# DEPLOYMENT_PIPELINE_TEST_REPORT.md

---

## Test Metadata

| Field | Value |
|-------|-------|
| **Test Date UTC** | _TO BE FILLED_ |
| **Hostname** | dikenocracy.com (37.27.244.96) |
| **Active Git Commit** | _TO BE FILLED_ |
| **Protocol Version** | 0.6.0 |
| **Constants Version** | 0.6.0 |
| **Applied Profile** | BASE |

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

## Service Status

| Service | Status |
|---------|--------|
| `market-lens-api.service` | _TO BE FILLED_ |
| `market-lens-worker.service` | _TO BE FILLED_ |

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

- **Request**: `POST http://127.0.0.1:8000/v1/ingest`
- **Status**: _TO BE FILLED_
- **Job ID**: _TO BE FILLED_

### Step 2 — Job Created

- **File Path**: `{queue_dir}/pending/{job_id}.json`
- **Status**: _TO BE FILLED_

### Step 3 — Worker Processed

- **File Path**: `{queue_dir}/completed/{job_id}.json`
- **Status**: _TO BE FILLED_
- **Processing Time**: _TO BE FILLED_

### Step 4 — Result Validation

- **Engine Status**: _TO BE FILLED_
- **Protocol Version**: _TO BE FILLED_
- **Constants Version**: _TO BE FILLED_
- **Applied Profile**: _TO BE FILLED_
- **Accepted Count**: _TO BE FILLED_
- **Rejected Count**: _TO BE FILLED_
- **P_ref**: _TO BE FILLED_
- **MAD**: _TO BE FILLED_
- **CS**: _TO BE FILLED_
- **N_eff**: _TO BE FILLED_
- **Cold Start Flag**: _TO BE FILLED_
- **Integrity Status**: _TO BE FILLED_

---

## Test Result

| Step | Result |
|------|--------|
| Step 1 — API Request Accepted | _TO BE FILLED_ |
| Step 2 — Job File Created | _TO BE FILLED_ |
| Step 3 — Worker Processed Job | _TO BE FILLED_ |
| Step 4 — Result Valid | _TO BE FILLED_ |

**Overall Result**: _TO BE FILLED_ (PASS / FAIL)

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
