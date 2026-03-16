"""
DKP-PTL-REG v0.6 — Filesystem Queue

Simple filesystem-based job queue for ingestion processing.
Atomic file operations using temp file + rename pattern.
"""

import json
import os
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Queue Directory Structure
# ---------------------------------------------------------------------------

PENDING_DIR = "pending"
PROCESSING_DIR = "processing"
COMPLETED_DIR = "completed"
FAILED_DIR = "failed"


@dataclass
class QueueJob:
    """Represents a queued job."""
    
    job_id: str
    payload: Dict[str, Any]
    created_at: float
    file_path: str


# ---------------------------------------------------------------------------
# Queue Directory Management
# ---------------------------------------------------------------------------

def ensure_queue_dirs(queue_base: str) -> None:
    """
    Ensure queue directory structure exists.
    
    Creates:
    - {queue_base}/pending/
    - {queue_base}/processing/
    - {queue_base}/completed/
    - {queue_base}/failed/
    """
    base = Path(queue_base)
    for subdir in [PENDING_DIR, PROCESSING_DIR, COMPLETED_DIR, FAILED_DIR]:
        (base / subdir).mkdir(parents=True, exist_ok=True)


def _get_queue_path(queue_base: str, subdir: str) -> Path:
    """Get path to a queue subdirectory."""
    return Path(queue_base) / subdir


# ---------------------------------------------------------------------------
# Job ID Generation
# ---------------------------------------------------------------------------

def _generate_job_id() -> str:
    """
    Generate a unique job ID.
    
    Uses UUID4 for uniqueness. Job IDs are only used for queue operations
    and never appear in engine outputs.
    """
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Atomic File Operations
# ---------------------------------------------------------------------------

def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    """
    Atomically write JSON to file using temp file + rename.
    
    Ensures no partial writes on same filesystem.
    """
    # Write to temp file in same directory for atomic rename
    dir_path = path.parent
    fd, temp_path = tempfile.mkstemp(suffix=".tmp", dir=str(dir_path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        # Atomic rename
        os.rename(temp_path, str(path))
    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def _read_json(path: Path) -> Dict[str, Any]:
    """Read JSON from file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Queue Operations
# ---------------------------------------------------------------------------

def enqueue_job(
    queue_base: str,
    payload: Dict[str, Any],
) -> str:
    """
    Enqueue a new job into the pending directory.
    
    Returns the job ID.
    """
    ensure_queue_dirs(queue_base)
    
    job_id = _generate_job_id()
    created_at = time.time()
    
    job_data = {
        "job_id": job_id,
        "created_at": created_at,
        "payload": payload,
    }
    
    pending_path = _get_queue_path(queue_base, PENDING_DIR)
    job_file = pending_path / f"{job_id}.json"
    
    _atomic_write_json(job_file, job_data)
    
    return job_id


def claim_next_job(queue_base: str) -> Optional[QueueJob]:
    """
    Atomically claim the next pending job for processing.
    
    Moves job from pending/ to processing/.
    Returns None if no jobs available.
    """
    pending_path = _get_queue_path(queue_base, PENDING_DIR)
    processing_path = _get_queue_path(queue_base, PROCESSING_DIR)
    
    if not pending_path.exists():
        return None
    
    # List pending jobs sorted by name (deterministic order)
    pending_files = sorted(pending_path.glob("*.json"))
    
    for pending_file in pending_files:
        processing_file = processing_path / pending_file.name
        
        try:
            # Atomic move from pending to processing
            os.rename(str(pending_file), str(processing_file))
            
            # Read job data
            job_data = _read_json(processing_file)
            
            return QueueJob(
                job_id=job_data["job_id"],
                payload=job_data["payload"],
                created_at=job_data["created_at"],
                file_path=str(processing_file),
            )
        except FileNotFoundError:
            # Job was claimed by another process
            continue
        except Exception:
            # Error reading job, skip it
            continue
    
    return None


def write_completed_job(
    queue_base: str,
    job: QueueJob,
    result: Dict[str, Any],
) -> str:
    """
    Write completed job result and move from processing/ to completed/.
    
    Returns path to completed result file.
    """
    completed_path = _get_queue_path(queue_base, COMPLETED_DIR)
    ensure_queue_dirs(queue_base)
    
    completion_data = {
        "job_id": job.job_id,
        "created_at": job.created_at,
        "completed_at": time.time(),
        "status": "completed",
        "result": result,
    }
    
    completed_file = completed_path / f"{job.job_id}.json"
    _atomic_write_json(completed_file, completion_data)
    
    # Remove processing file
    try:
        os.unlink(job.file_path)
    except OSError:
        pass
    
    return str(completed_file)


def write_failed_job(
    queue_base: str,
    job: QueueJob,
    error: str,
    error_details: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Write failed job error and move from processing/ to failed/.
    
    Returns path to failed result file.
    """
    failed_path = _get_queue_path(queue_base, FAILED_DIR)
    ensure_queue_dirs(queue_base)
    
    failure_data = {
        "job_id": job.job_id,
        "created_at": job.created_at,
        "failed_at": time.time(),
        "status": "failed",
        "error": error,
        "error_details": error_details or {},
        "original_payload": job.payload,
    }
    
    failed_file = failed_path / f"{job.job_id}.json"
    _atomic_write_json(failed_file, failure_data)
    
    # Remove processing file
    try:
        os.unlink(job.file_path)
    except OSError:
        pass
    
    return str(failed_file)


def list_pending_jobs(queue_base: str) -> List[str]:
    """List all pending job IDs."""
    pending_path = _get_queue_path(queue_base, PENDING_DIR)
    if not pending_path.exists():
        return []
    return [f.stem for f in sorted(pending_path.glob("*.json"))]


def list_processing_jobs(queue_base: str) -> List[str]:
    """List all processing job IDs."""
    processing_path = _get_queue_path(queue_base, PROCESSING_DIR)
    if not processing_path.exists():
        return []
    return [f.stem for f in sorted(processing_path.glob("*.json"))]
