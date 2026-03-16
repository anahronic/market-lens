"""
DKP-PTL-REG v0.6 — Deterministic Normalization Boundary

This module provides deterministic normalization helpers aligned with REFERENCE-001.
Delegates to engine.src.reference_boundary for core normalization logic.

Functions are pure and return structured results with rejection reasons.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from collections import Counter

from engine.src.reference_boundary import (
    normalize_string as _engine_normalize_string,
    extract_host as _engine_extract_host,
    get_root_domain as _engine_get_root_domain,
    canonicalize_timestamp as _engine_canonicalize_timestamp,
    canonicalize_merchant_id as _engine_canonicalize_merchant_id,
    compute_evidence_hash as _engine_compute_evidence_hash,
    normalize_pil as _engine_normalize_pil,
    validate_and_normalize as _engine_validate_and_normalize,
    NormalizedObservation,
)


# ---------------------------------------------------------------------------
# Re-export core normalization functions for service use
# ---------------------------------------------------------------------------

def normalize_string(value: Any) -> str:
    """
    Canonical string normalization per REFERENCE-001 Section 3.
    
    - UTF-8 encoding
    - NFC normalization
    - Trim ASCII whitespace only
    - Locale-independent casefold
    - Missing field = ""
    """
    return _engine_normalize_string(value)


def normalize_timestamp(
    timestamp_value: Any,
    current_time_utc: int,
) -> Optional[int]:
    """
    Canonicalize timestamp per REFERENCE-001 Section 6.
    
    - Accept ISO-8601 or numeric epoch
    - Convert to UTC
    - Floor to integer seconds
    - Reject if > current_time_utc + 5 seconds
    
    Returns None if invalid (observation should be rejected).
    """
    return _engine_canonicalize_timestamp(timestamp_value, current_time_utc)


def extract_domain_id(source_url: str) -> Optional[str]:
    """
    Extract root domain (eTLD+1) from source_url per REFERENCE-001 Section 4.
    
    - Parse URL via RFC 3986
    - Extract and normalize host
    - Remove port
    - Apply PSL to get eTLD+1
    
    Returns None if parsing fails.
    """
    return _engine_get_root_domain(source_url)


def build_evidence_hash(
    domain_id: str,
    merchant_id: str,
    price: float,
    currency: str,
    timestamp: int,
    region: str,
    pil: Dict[str, str],
) -> str:
    """
    Compute evidence_hash as SHA256(canonical_payload) per REFERENCE-001 Section 8.
    
    Uses JCS canonical JSON with lexicographically sorted keys.
    """
    return _engine_compute_evidence_hash(
        domain_id, merchant_id, price, currency, timestamp, region, pil
    )


# ---------------------------------------------------------------------------
# Rejection Reason Codes
# ---------------------------------------------------------------------------

class RejectionReason:
    """Deterministic rejection reason codes."""
    
    INVALID_PRICE = "invalid_price"
    MISSING_CURRENCY = "missing_currency"
    MISSING_REGION = "missing_region"
    INVALID_DOMAIN = "invalid_domain"
    INVALID_MERCHANT_ID = "invalid_merchant_id"
    INVALID_TIMESTAMP = "invalid_timestamp"
    FUTURE_TIMESTAMP = "future_timestamp"
    MISSING_PIL = "missing_pil"
    NORMALIZATION_ERROR = "normalization_error"


# ---------------------------------------------------------------------------
# Structured Normalization Results
# ---------------------------------------------------------------------------

@dataclass
class NormalizationResult:
    """Result of normalizing a single observation."""
    
    accepted: bool
    observation: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None


@dataclass
class BatchNormalizationResult:
    """Result of normalizing a batch of observations."""
    
    accepted_observations: List[Dict[str, Any]] = field(default_factory=list)
    rejected_observations: List[Dict[str, Any]] = field(default_factory=list)
    rejection_reason_counts: Dict[str, int] = field(default_factory=dict)
    
    @property
    def accepted_count(self) -> int:
        return len(self.accepted_observations)
    
    @property
    def rejected_count(self) -> int:
        return len(self.rejected_observations)


# ---------------------------------------------------------------------------
# Observation Normalization with Rejection Tracking
# ---------------------------------------------------------------------------

def normalize_observation(
    raw_obs: Dict[str, Any],
    current_time_utc: int,
) -> NormalizationResult:
    """
    Normalize a single observation with detailed rejection tracking.
    
    Returns NormalizationResult with acceptance status and reason if rejected.
    """
    try:
        # Price validation
        price = raw_obs.get("price")
        if price is None:
            return NormalizationResult(
                accepted=False,
                rejection_reason=RejectionReason.INVALID_PRICE,
            )
        try:
            price = float(price)
            import math
            if not math.isfinite(price) or price <= 0:
                return NormalizationResult(
                    accepted=False,
                    rejection_reason=RejectionReason.INVALID_PRICE,
                )
        except (TypeError, ValueError):
            return NormalizationResult(
                accepted=False,
                rejection_reason=RejectionReason.INVALID_PRICE,
            )
        
        # Currency validation
        currency = raw_obs.get("currency")
        if currency is None or normalize_string(currency) == "":
            return NormalizationResult(
                accepted=False,
                rejection_reason=RejectionReason.MISSING_CURRENCY,
            )
        currency = normalize_string(currency)
        
        # Region validation
        region = raw_obs.get("region")
        if region is None or normalize_string(region) == "":
            return NormalizationResult(
                accepted=False,
                rejection_reason=RejectionReason.MISSING_REGION,
            )
        region = normalize_string(region)
        
        # Domain extraction
        source_url = raw_obs.get("source_url", "")
        domain_id = extract_domain_id(source_url)
        if domain_id is None:
            # Try direct domain_id
            direct_domain = raw_obs.get("domain_id")
            if direct_domain is not None:
                domain_id = normalize_string(direct_domain)
            else:
                return NormalizationResult(
                    accepted=False,
                    rejection_reason=RejectionReason.INVALID_DOMAIN,
                )
        
        # Merchant ID
        merchant_id_raw = raw_obs.get("merchant_id")
        merchant_id = _engine_canonicalize_merchant_id(merchant_id_raw)
        if merchant_id is None:
            return NormalizationResult(
                accepted=False,
                rejection_reason=RejectionReason.INVALID_MERCHANT_ID,
            )
        
        # Timestamp
        timestamp_raw = raw_obs.get("timestamp")
        timestamp = normalize_timestamp(timestamp_raw, current_time_utc)
        if timestamp is None:
            return NormalizationResult(
                accepted=False,
                rejection_reason=RejectionReason.INVALID_TIMESTAMP,
            )
        
        # PIL
        pil_raw = raw_obs.get("product_identity_layer")
        if pil_raw is None:
            return NormalizationResult(
                accepted=False,
                rejection_reason=RejectionReason.MISSING_PIL,
            )
        pil = _engine_normalize_pil(pil_raw)
        if pil is None:
            return NormalizationResult(
                accepted=False,
                rejection_reason=RejectionReason.MISSING_PIL,
            )
        
        # Compute evidence hash
        evidence_hash = build_evidence_hash(
            domain_id, merchant_id, price, currency, timestamp, region, pil
        )
        
        # Build normalized observation dict
        normalized = {
            "domain_id": domain_id,
            "merchant_id": merchant_id,
            "price": price,
            "currency": currency,
            "timestamp": timestamp,
            "region": region,
            "pil": pil,
            "evidence_hash": evidence_hash,
            "source_url": str(source_url),
            "bundle_flag": pil.get("bundle_flag", ""),
            "warranty_type": pil.get("warranty_type", ""),
        }
        
        return NormalizationResult(
            accepted=True,
            observation=normalized,
        )
        
    except Exception:
        return NormalizationResult(
            accepted=False,
            rejection_reason=RejectionReason.NORMALIZATION_ERROR,
        )


def normalize_batch(
    raw_observations: List[Dict[str, Any]],
    current_time_utc: int,
) -> BatchNormalizationResult:
    """
    Normalize a batch of observations with aggregate rejection tracking.
    
    Returns BatchNormalizationResult with accepted/rejected lists and counts.
    """
    result = BatchNormalizationResult()
    rejection_counter: Counter[str] = Counter()
    
    for raw_obs in raw_observations:
        norm_result = normalize_observation(raw_obs, current_time_utc)
        
        if norm_result.accepted and norm_result.observation is not None:
            result.accepted_observations.append(norm_result.observation)
        else:
            result.rejected_observations.append({
                "original": raw_obs,
                "reason": norm_result.rejection_reason,
            })
            if norm_result.rejection_reason:
                rejection_counter[norm_result.rejection_reason] += 1
    
    result.rejection_reason_counts = dict(rejection_counter)
    return result
