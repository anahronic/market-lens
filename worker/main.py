"""
DKP-PTL-REG v0.6 — Background Worker

Simple polling worker for processing ingested observation batches.
Single-process safe with atomic file operations.
"""

import sys
import time
import logging
from typing import Dict, Any, Optional

from service.runtime import get_runtime_config
from service.version_info import PROTOCOL_VERSION, CONSTANTS_VERSION
from ingestion.normalize import normalize_batch
from ingestion.file_queue import (
    ensure_queue_dirs,
    claim_next_job,
    write_completed_job,
    write_failed_job,
    QueueJob,
)
from engine.src.cli import run_engine


# Configure logging to stdout only
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def process_job(job: QueueJob) -> Dict[str, Any]:
    """
    Process a single queued job.
    
    1. Extract payload
    2. Normalize observations
    3. Run engine
    4. Return result
    
    Raises exception on validation failure for proper error handling.
    """
    payload = job.payload
    
    # Extract job parameters
    raw_observations = payload.get("observations", [])
    current_time_utc = payload.get("current_time_utc")
    applied_profile = payload.get("applied_profile", "BASE")
    
    if current_time_utc is None:
        raise ValueError("Missing current_time_utc in job payload")
    
    if applied_profile not in ("BASE", "HARDENED"):
        raise ValueError(f"Invalid profile: {applied_profile}")
    
    # Normalize observations
    norm_result = normalize_batch(raw_observations, current_time_utc)
    
    # Prepare engine input
    engine_input: Dict[str, Any] = {
        "observations": norm_result.accepted_observations,
    }
    
    # Run engine
    if norm_result.accepted_count > 0:
        engine_output = run_engine(
            engine_input,
            applied_profile,
            current_time_utc,
        )
    else:
        # All observations rejected - return cold start result
        engine_output = {
            "applied_profile": applied_profile,
            "protocol_version": PROTOCOL_VERSION,
            "constants_version": CONSTANTS_VERSION,
            "identity_scope_level": None,
            "P_ref": None,
            "MAD": None,
            "CS": 0.0,
            "N_eff": 0.0,
            "cold_start_flag": True,
            "insufficient_data_flag": True,
            "integrity_status": "COLD_START",
        }
    
    # Build complete result
    return {
        "status": "ok",
        "protocol_version": PROTOCOL_VERSION,
        "constants_version": CONSTANTS_VERSION,
        "applied_profile": applied_profile,
        "accepted_count": norm_result.accepted_count,
        "rejected_count": norm_result.rejected_count,
        "rejection_reasons_summary": norm_result.rejection_reason_counts,
        "result": dict(engine_output),
    }


def run_worker_loop(
    queue_dir: str,
    poll_interval: int,
    max_iterations: Optional[int] = None,
) -> int:
    """
    Run the worker polling loop.
    
    Args:
        queue_dir: Path to queue directory
        poll_interval: Seconds between poll attempts
        max_iterations: Maximum iterations (None = infinite)
    
    Returns:
        Exit code (0 = success, 1 = error)
    """
    logger.info(f"Starting worker, queue_dir={queue_dir}, poll_interval={poll_interval}s")
    ensure_queue_dirs(queue_dir)
    
    iteration = 0
    processed = 0
    failed = 0
    
    try:
        while max_iterations is None or iteration < max_iterations:
            iteration += 1
            
            # Try to claim next job
            job = claim_next_job(queue_dir)
            
            if job is None:
                # No jobs available, wait
                logger.debug(f"No jobs available, sleeping {poll_interval}s")
                time.sleep(poll_interval)
                continue
            
            logger.info(f"Processing job {job.job_id}")
            
            try:
                result = process_job(job)
                write_completed_job(queue_dir, job, result)
                processed += 1
                logger.info(f"Completed job {job.job_id}")
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed job {job.job_id}: {error_msg}")
                write_failed_job(
                    queue_dir,
                    job,
                    error_msg,
                    {"exception_type": type(e).__name__},
                )
                failed += 1
        
        logger.info(f"Worker finished: processed={processed}, failed={failed}")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Worker error: {e}")
        return 1


def main() -> None:
    """Worker entry point."""
    config = get_runtime_config()
    
    logger.info("Market Lens Worker starting")
    logger.info(f"Protocol version: {PROTOCOL_VERSION}")
    logger.info(f"Constants version: {CONSTANTS_VERSION}")
    logger.info(f"Profile: {config.profile}")
    
    exit_code = run_worker_loop(
        queue_dir=config.queue_dir,
        poll_interval=config.poll_interval,
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
