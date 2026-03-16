"""
DKP-PTL-REG v0.6 — FastAPI Application

Market Lens API exposing deterministic price transparency engine.
"""

import time
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from api.schemas import (
    EvaluationRequest,
    EvaluationResponse,
    EngineResult,
    IngestRequest,
    IngestResponse,
    HealthResponse,
    VersionResponse,
)
from api.deps import (
    get_config,
    get_queue_path,
    get_default_profile,
    get_engine_callable,
    get_version,
)
from ingestion.normalize import normalize_batch
from ingestion.file_queue import enqueue_job, ensure_queue_dirs
from service.version_info import PROTOCOL_VERSION, CONSTANTS_VERSION


app = FastAPI(
    title="Market Lens API",
    description="DKP-PTL-REG v0.6 — Deterministic Price Transparency Engine",
    version="0.6.0",
)


# ---------------------------------------------------------------------------
# Health and Version Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns service status and version information.
    """
    return HealthResponse(
        status="ok",
        service="market-lens-api",
        protocol_version=PROTOCOL_VERSION,
        constants_version=CONSTANTS_VERSION,
    )


@app.get("/version", response_model=VersionResponse)
def version() -> VersionResponse:
    """
    Version information endpoint.
    
    Returns detailed version and configuration information.
    """
    config = get_config()
    version_info = get_version()
    
    return VersionResponse(
        protocol_version=version_info["protocol_version"],
        constants_version=version_info["constants_version"],
        engine_version=version_info["engine_version"],
        service_mode=config.service_mode,
        active_profile_default=config.profile,
        psl_version=version_info["psl_version"],
    )


# ---------------------------------------------------------------------------
# Evaluate Endpoint
# ---------------------------------------------------------------------------

@app.post("/v1/evaluate", response_model=EvaluationResponse)
def evaluate(request: EvaluationRequest) -> EvaluationResponse:
    """
    Evaluate observations using deterministic engine.
    
    Normalizes observations per REFERENCE-001, runs DATA-001 pipeline,
    and returns deterministic results with version metadata.
    """
    # Convert Pydantic models to dicts for normalization
    raw_observations = [obs.model_dump() for obs in request.observations]
    
    # Normalize observations with rejection tracking
    norm_result = normalize_batch(raw_observations, request.current_time_utc)
    
    # Prepare engine input
    engine_input: Dict[str, Any] = {
        "observations": norm_result.accepted_observations,
    }
    
    # Run engine
    engine = get_engine_callable()
    
    if norm_result.accepted_count > 0:
        engine_output = engine(
            engine_input,
            request.applied_profile,
            request.current_time_utc,
        )
    else:
        # All observations rejected - return cold start result
        engine_output = {
            "applied_profile": request.applied_profile,
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
    
    # Build response
    result = EngineResult(
        identity_scope_level=engine_output.get("identity_scope_level"),
        P_ref=engine_output.get("P_ref"),
        MAD=engine_output.get("MAD"),
        CS=engine_output.get("CS", 0.0),
        N_eff=engine_output.get("N_eff", 0.0),
        cold_start_flag=engine_output.get("cold_start_flag", True),
        insufficient_data_flag=engine_output.get("insufficient_data_flag", True),
        integrity_status=engine_output.get("integrity_status", "COLD_START"),
    )
    
    return EvaluationResponse(
        status="ok",
        protocol_version=PROTOCOL_VERSION,
        constants_version=CONSTANTS_VERSION,
        applied_profile=request.applied_profile,
        accepted_count=norm_result.accepted_count,
        rejected_count=norm_result.rejected_count,
        rejection_reasons_summary=norm_result.rejection_reason_counts,
        result=result,
    )


# ---------------------------------------------------------------------------
# Ingest Endpoint
# ---------------------------------------------------------------------------

@app.post("/v1/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> IngestResponse:
    """
    Ingest raw observations into processing queue.
    
    Does not compute engine result. Normalizes enough for safe serialization
    and enqueues payload for background worker processing.
    """
    queue_path = get_queue_path()
    ensure_queue_dirs(queue_path)
    
    # Build queue payload
    payload = {
        "observations": request.observations,
        "current_time_utc": request.current_time_utc,
        "applied_profile": request.applied_profile,
        "metadata": request.metadata,
    }
    
    # Enqueue job
    accepted_timestamp = time.time()
    job_id = enqueue_job(queue_path, payload)
    
    return IngestResponse(
        status="ok",
        job_id=job_id,
        accepted_timestamp=accepted_timestamp,
        observations_count=len(request.observations),
    )


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------

@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=400,
        content={"status": "error", "detail": str(exc)},
    )
