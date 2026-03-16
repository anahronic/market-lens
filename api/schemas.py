"""
DKP-PTL-REG v0.6 — API Schemas

Pydantic models for API request/response validation.
Basic shape validation only; protocol logic handled in normalization layer.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Product Identity Layer
# ---------------------------------------------------------------------------

class ProductIdentityLayer(BaseModel):
    """Product Identity Layer fields per REFERENCE-001."""
    
    brand: str = ""
    model: str = ""
    sku: str = ""
    condition: str = ""
    bundle_flag: str = ""
    warranty_type: str = ""
    region_variant: str = ""
    storage_or_size: str = ""
    release_year: str = ""


# ---------------------------------------------------------------------------
# Observation Input
# ---------------------------------------------------------------------------

class RawObservationInput(BaseModel):
    """Raw observation input before normalization."""
    
    source_url: Optional[str] = None
    domain_id: Optional[str] = None
    merchant_id: Optional[str] = None
    price: float = Field(..., gt=0, description="Price must be positive")
    currency: str
    region: str
    timestamp: Any  # Can be int, float, or ISO-8601 string
    product_identity_layer: ProductIdentityLayer


# ---------------------------------------------------------------------------
# Evaluation Request/Response
# ---------------------------------------------------------------------------

class EvaluationRequest(BaseModel):
    """Request body for /v1/evaluate endpoint."""
    
    observations: List[RawObservationInput]
    current_time_utc: int = Field(..., description="Current time as Unix epoch seconds UTC")
    applied_profile: str = Field(default="BASE", pattern="^(BASE|HARDENED)$")
    metadata: Optional[Dict[str, Any]] = None


class EngineResult(BaseModel):
    """Engine computation result."""
    
    identity_scope_level: Optional[int] = None
    P_ref: Optional[float] = None
    MAD: Optional[float] = None
    CS: float = 0.0
    N_eff: float = 0.0
    cold_start_flag: bool = True
    insufficient_data_flag: bool = True
    integrity_status: str = "COLD_START"


class EvaluationResponse(BaseModel):
    """Response body for /v1/evaluate endpoint."""
    
    status: str = "ok"
    protocol_version: str
    constants_version: str
    applied_profile: str
    accepted_count: int
    rejected_count: int
    rejection_reasons_summary: Dict[str, int]
    result: EngineResult


# ---------------------------------------------------------------------------
# Ingest Request/Response
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    """Request body for /v1/ingest endpoint."""
    
    observations: List[Dict[str, Any]]
    current_time_utc: int
    applied_profile: str = Field(default="BASE", pattern="^(BASE|HARDENED)$")
    metadata: Optional[Dict[str, Any]] = None


class IngestResponse(BaseModel):
    """Response body for /v1/ingest endpoint."""
    
    status: str = "ok"
    job_id: str
    accepted_timestamp: float
    observations_count: int


# ---------------------------------------------------------------------------
# Health/Version Responses
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Response body for /health endpoint."""
    
    status: str = "ok"
    service: str = "market-lens-api"
    protocol_version: str
    constants_version: str


class VersionResponse(BaseModel):
    """Response body for /version endpoint."""
    
    protocol_version: str
    constants_version: str
    engine_version: str
    service_mode: str
    active_profile_default: str
    psl_version: str
