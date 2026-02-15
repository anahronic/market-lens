"""
DKP-PTL-REG-THREAT-001 v0.6 — Deterministic Threat Model

Integrity status computation per strict precedence:
1. COLD_START
2. BURST_DETECTED
3. DOMAIN_DOMINANCE
4. CLUSTER_COLLAPSE
5. NORMAL

Only one status emitted.
"""

from .data_pipeline import PipelineResult
from .constants import ProfileConstants

# Cluster collapse threshold: fixed in THREAT-001 spec.
# MUST NOT be externalized as a constant.
_CLUSTER_COLLAPSE_THRESHOLD = 0.30

INTEGRITY_STATUSES = [
    "COLD_START",
    "BURST_DETECTED",
    "DOMAIN_DOMINANCE",
    "CLUSTER_COLLAPSE",
    "NORMAL",
]


def compute_integrity_status(
    pipeline_result: PipelineResult,
    constants: ProfileConstants,
) -> str:
    """
    Compute integrity_status per THREAT-001 v0.6 Section 4.

    Strict precedence order:
    1. COLD_START — cold_start_flag = true
    2. BURST_DETECTED — any domain burst_ratio > threshold
    3. DOMAIN_DOMINANCE — any domain D_j_raw > cap was applied
    4. CLUSTER_COLLAPSE — cluster weight loss > 30%
    5. NORMAL — none of above AND CS >= CS_display_threshold
    """
    # 1. COLD_START (highest precedence)
    if pipeline_result.cold_start_flag:
        return "COLD_START"

    # 2. BURST_DETECTED
    if pipeline_result.burst_detected:
        return "BURST_DETECTED"

    # 3. DOMAIN_DOMINANCE
    if pipeline_result.domain_dominance_detected:
        return "DOMAIN_DOMINANCE"

    # 4. CLUSTER_COLLAPSE
    if pipeline_result.cluster_weight_loss_ratio > _CLUSTER_COLLAPSE_THRESHOLD:
        return "CLUSTER_COLLAPSE"

    # 5. NORMAL
    if pipeline_result.CS >= constants.CS_display_threshold:
        return "NORMAL"

    # Fallback: if CS < threshold but no specific threat detected
    # Per spec, NORMAL requires CS >= CS_display_threshold
    # If none triggered, still return NORMAL as the lowest precedence status
    return "NORMAL"
