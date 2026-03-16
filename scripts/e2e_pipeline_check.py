#!/usr/bin/env python3
"""
DKP-PTL-REG v0.6 — End-to-End Pipeline Test

Tests the full ingestion pipeline:
  API request → job created → worker processed → result written

Usage:
  python3 scripts/e2e_pipeline_check.py [--queue-dir DIR] [--endpoint URL] [--timeout SECS]

Environment:
  MARKET_LENS_QUEUE_DIR - Override queue directory path
  E2E_API_ENDPOINT - Override API endpoint (default: http://127.0.0.1:8000)

Exit codes:
  0 - Pipeline test passed
  1 - Pipeline test failed
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_QUEUE_DIR = "./var/queue"
DEFAULT_API_ENDPOINT = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT = 30  # seconds
POLL_INTERVAL = 1  # seconds


# ---------------------------------------------------------------------------
# Test Payload
# ---------------------------------------------------------------------------

def get_test_payload(current_time_utc: int) -> Dict[str, Any]:
    """
    Return minimal valid ingestion payload.
    
    Conforms to IngestRequest schema:
    - observations: List[Dict[str, Any]]
    - current_time_utc: int
    - applied_profile: str (BASE|HARDENED)
    """
    return {
        "observations": [
            {
                "source_url": "https://example.com/product/test-001",
                "domain_id": "example.com",
                "merchant_id": "test-merchant",
                "price": 99.99,
                "currency": "USD",
                "region": "US",
                "timestamp": current_time_utc - 3600,  # 1 hour ago
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
                "timestamp": current_time_utc - 1800,  # 30 min ago
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
        "current_time_utc": current_time_utc,
        "applied_profile": "BASE",
        "metadata": {
            "test": True,
            "test_type": "e2e_pipeline_check"
        }
    }


# ---------------------------------------------------------------------------
# Pipeline Steps
# ---------------------------------------------------------------------------

def step_1_send_ingest_request(
    endpoint: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Step 1: Send ingestion request to API.
    
    Returns ingest response with job_id.
    """
    url = f"{endpoint}/v1/ingest"
    
    print(f"[Step 1] Sending POST to {url}")
    print(f"         Payload observations: {len(payload['observations'])}")
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            print(f"         Response status: {result.get('status')}")
            print(f"         Job ID: {result.get('job_id')}")
            
            return result
            
    except httpx.HTTPStatusError as e:
        print(f"         ERROR: HTTP {e.response.status_code}")
        try:
            error_detail = e.response.json()
            print(f"         Detail: {error_detail}")
        except Exception:
            print(f"         Body: {e.response.text[:200]}")
        raise
    except httpx.RequestError as e:
        print(f"         ERROR: Request failed - {e}")
        raise


def step_2_verify_job_created(
    queue_dir: str,
    job_id: str,
    timeout: float,
) -> Optional[str]:
    """
    Step 2: Verify job file was created in pending or processing.
    
    Returns path to job file, or None if not found.
    """
    print(f"[Step 2] Verifying job {job_id} in queue")
    print(f"         Queue dir: {queue_dir}")
    
    queue_path = Path(queue_dir)
    pending_file = queue_path / "pending" / f"{job_id}.json"
    processing_file = queue_path / "processing" / f"{job_id}.json"
    completed_file = queue_path / "completed" / f"{job_id}.json"
    
    start = time.time()
    while time.time() - start < timeout:
        # Check if already completed
        if completed_file.exists():
            print(f"         Found in completed/")
            return str(completed_file)
        
        # Check pending
        if pending_file.exists():
            print(f"         Found in pending/")
            return str(pending_file)
        
        # Check processing (worker picked it up)
        if processing_file.exists():
            print(f"         Found in processing/")
            return str(processing_file)
        
        time.sleep(POLL_INTERVAL)
    
    print(f"         ERROR: Job file not found after {timeout}s")
    return None


def step_3_wait_for_completion(
    queue_dir: str,
    job_id: str,
    timeout: float,
) -> Optional[Dict[str, Any]]:
    """
    Step 3: Wait for job to be processed by worker.
    
    Returns completed job data, or None if timeout.
    """
    print(f"[Step 3] Waiting for worker to process job {job_id}")
    
    queue_path = Path(queue_dir)
    completed_file = queue_path / "completed" / f"{job_id}.json"
    failed_file = queue_path / "failed" / f"{job_id}.json"
    
    start = time.time()
    while time.time() - start < timeout:
        # Check completed
        if completed_file.exists():
            print(f"         Job completed!")
            with open(completed_file) as f:
                return json.load(f)
        
        # Check failed
        if failed_file.exists():
            print(f"         Job FAILED!")
            with open(failed_file) as f:
                failed_data = json.load(f)
            print(f"         Error: {failed_data.get('error', 'unknown')}")
            return None
        
        elapsed = time.time() - start
        print(f"         Waiting... ({elapsed:.1f}s)", end="\r")
        time.sleep(POLL_INTERVAL)
    
    print(f"\n         ERROR: Job not completed after {timeout}s")
    return None


def step_4_validate_result(completed_data: Dict[str, Any]) -> bool:
    """
    Step 4: Validate that result contains computation output.
    
    Returns True if result is valid, False otherwise.
    """
    print(f"[Step 4] Validating computation result")
    
    result = completed_data.get("result", {})
    
    # Check required fields
    required_fields = ["status", "protocol_version", "constants_version", "result"]
    for field in required_fields:
        if field not in result:
            print(f"         ERROR: Missing field: {field}")
            return False
    
    # Check nested result (engine output)
    engine_result = result.get("result", {})
    
    print(f"         status: {result.get('status')}")
    print(f"         protocol_version: {result.get('protocol_version')}")
    print(f"         constants_version: {result.get('constants_version')}")
    print(f"         applied_profile: {result.get('applied_profile')}")
    print(f"         accepted_count: {result.get('accepted_count')}")
    print(f"         rejected_count: {result.get('rejected_count')}")
    
    # Engine result fields
    print(f"         --- Engine Result ---")
    print(f"         P_ref: {engine_result.get('P_ref')}")
    print(f"         MAD: {engine_result.get('MAD')}")
    print(f"         CS: {engine_result.get('CS')}")
    print(f"         N_eff: {engine_result.get('N_eff')}")
    print(f"         cold_start_flag: {engine_result.get('cold_start_flag')}")
    print(f"         integrity_status: {engine_result.get('integrity_status')}")
    
    # Validate status is ok
    if result.get("status") != "ok":
        print(f"         ERROR: Result status is not 'ok'")
        return False
    
    # Result is valid (even cold start is valid - it means computation ran)
    print(f"         Result valid: computation executed")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_pipeline_test(
    queue_dir: str,
    endpoint: str,
    timeout: float,
) -> bool:
    """
    Run full pipeline test.
    
    Returns True on success, False on failure.
    """
    current_time_utc = int(time.time())
    
    print("=" * 60)
    print("Market Lens E2E Pipeline Test")
    print("=" * 60)
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print(f"Queue dir: {queue_dir}")
    print(f"Endpoint: {endpoint}")
    print(f"Timeout: {timeout}s")
    print("-" * 60)
    
    # Step 1: Send ingest request
    try:
        payload = get_test_payload(current_time_utc)
        ingest_response = step_1_send_ingest_request(endpoint, payload)
    except Exception as e:
        print(f"\nFAIL: Step 1 - Ingest request failed: {e}")
        return False
    
    job_id = ingest_response.get("job_id")
    if not job_id:
        print("\nFAIL: Step 1 - No job_id in response")
        return False
    
    print("-" * 60)
    
    # Step 2: Verify job created
    job_file = step_2_verify_job_created(queue_dir, job_id, timeout=5)
    if job_file is None:
        print(f"\nFAIL: Step 2 - Job file not created")
        return False
    
    print("-" * 60)
    
    # Step 3: Wait for completion
    completed_data = step_3_wait_for_completion(queue_dir, job_id, timeout)
    if completed_data is None:
        print(f"\nFAIL: Step 3 - Job not processed by worker")
        return False
    
    print("-" * 60)
    
    # Step 4: Validate result
    if not step_4_validate_result(completed_data):
        print(f"\nFAIL: Step 4 - Result validation failed")
        return False
    
    print("-" * 60)
    print("\nPASS: Pipeline test completed successfully")
    print(f"Job ID: {job_id}")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Market Lens E2E Pipeline Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--queue-dir",
        default=os.environ.get("MARKET_LENS_QUEUE_DIR", DEFAULT_QUEUE_DIR),
        help=f"Queue directory path (default: {DEFAULT_QUEUE_DIR})",
    )
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("E2E_API_ENDPOINT", DEFAULT_API_ENDPOINT),
        help=f"API endpoint URL (default: {DEFAULT_API_ENDPOINT})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    
    args = parser.parse_args()
    
    success = run_pipeline_test(
        queue_dir=args.queue_dir,
        endpoint=args.endpoint,
        timeout=args.timeout,
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
