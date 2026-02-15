"""
DKP-PTL-REG-CONSTANTS-001 v0.6 — Deterministic Constants Registry

Dual-profile parameter lock: BASE and HARDENED.
All constants within a profile form an atomic deterministic set.

IEEE 754 double precision. Round half to even.
Round all externally exposed metrics to 6 decimal places.
"""

from dataclasses import dataclass

PROTOCOL_VERSION = "0.6.0"
CONSTANTS_VERSION = "0.6.0"


@dataclass(frozen=True)
class ProfileConstants:
    """Atomic deterministic constant set for a single profile."""

    profile_name: str

    # Section 4: Coverage Threshold
    N_eff_min: float

    # Section 5: Minimum Weight Threshold
    W_min: float

    # Section 6: Confidence Curve Constant
    k_n: float

    # Section 7: Temporal Decay Constants (seconds)
    T_half_default: float  # 14 days = 1209600s
    max_age_cutoff: float  # 90 days = 7776000s

    # Section 8: Domain Contribution Constraint
    domain_contribution_cap_percent: float

    # Section 9: Similarity Threshold
    cluster_similarity_threshold: float

    # Section 10: Burst Detection Constants
    burst_threshold_multiplier: float
    early_window_multiplier: float
    stability_window_duration_seconds: float  # 24 hours = 86400s

    # Section 11: Outlier Control Constants
    z_max: float

    # Section 12: Display Threshold
    CS_display_threshold: float


BASE = ProfileConstants(
    profile_name="BASE",
    N_eff_min=3.0,
    W_min=1.0,
    k_n=0.22,
    T_half_default=1209600.0,
    max_age_cutoff=7776000.0,
    domain_contribution_cap_percent=0.30,
    cluster_similarity_threshold=0.92,
    burst_threshold_multiplier=4.0,
    early_window_multiplier=2.0,
    stability_window_duration_seconds=86400.0,
    z_max=6.0,
    CS_display_threshold=0.15,
)

HARDENED = ProfileConstants(
    profile_name="HARDENED",
    N_eff_min=3.5,
    W_min=1.5,
    k_n=0.22,
    T_half_default=1209600.0,
    max_age_cutoff=7776000.0,
    domain_contribution_cap_percent=0.30,
    cluster_similarity_threshold=0.92,
    burst_threshold_multiplier=4.0,
    early_window_multiplier=2.0,
    stability_window_duration_seconds=86400.0,
    z_max=4.5,
    CS_display_threshold=0.25,
)

PROFILES = {
    "BASE": BASE,
    "HARDENED": HARDENED,
}


def get_profile(name: str) -> ProfileConstants:
    """Return profile by name. Raises ValueError if unknown."""
    if name not in PROFILES:
        raise ValueError(
            f"Unknown profile: {name!r}. Must be one of: {sorted(PROFILES.keys())}"
        )
    return PROFILES[name]
