"""DKP-PTL-REG-CLIENT-001 v0.6 deterministic client interpretation."""

from __future__ import annotations

from typing import Any

from engine.src.constants import get_profile

T_NEAR = 0.05
T_LOW = 0.15
T_HIGH = 0.15

SIGNAL_TO_COLOR = {
    "BELOW_MARKET": "#C9A227",
    "SLIGHTLY_BELOW": "#E6C65C",
    "NEAR_MARKET": "#2ECC71",
    "SLIGHTLY_ABOVE": "#F39C12",
    "ABOVE_MARKET": "#E74C3C",
    "NO_DATA": "#95A5A6",
}

INTEGRITY_OVERLAY = {
    "NORMAL": None,
    "BURST_DETECTED": "warning_flag",
    "DOMAIN_DOMINANCE": "dominance_flag",
    "CLUSTER_COLLAPSE": "clustering_warning",
    "COLD_START": None,
}


def _get_overlay(integrity_status: Any) -> str | None:
    return INTEGRITY_OVERLAY.get(integrity_status, None)


def interpret_client_signal(payload: dict) -> dict:
    """Map registry output + page offer context to deterministic client signal."""
    registry_currency = payload.get("currency")
    registry_region = payload.get("region")
    offer_currency = payload.get("P_offer_currency")
    offer_region = payload.get("P_offer_region")

    reduced_identity_scope = (payload.get("identity_scope_level") or 0) > 0

    if offer_currency != registry_currency or offer_region != registry_region:
        return {
            "signal": "NO_DATA",
            "color": SIGNAL_TO_COLOR["NO_DATA"],
            "ppi": None,
            "overlay": _get_overlay(payload.get("integrity_status")),
            "reduced_identity_scope": reduced_identity_scope,
        }

    p_ref = payload.get("P_ref")
    cs = payload.get("CS")
    p_offer = payload.get("P_offer")

    if payload.get("cold_start_flag") is True or p_ref is None:
        return {
            "signal": "NO_DATA",
            "color": SIGNAL_TO_COLOR["NO_DATA"],
            "ppi": None,
            "overlay": _get_overlay(payload.get("integrity_status")),
            "reduced_identity_scope": reduced_identity_scope,
        }

    if p_offer is None:
        return {
            "signal": "NO_DATA",
            "color": SIGNAL_TO_COLOR["NO_DATA"],
            "ppi": None,
            "overlay": _get_overlay(payload.get("integrity_status")),
            "reduced_identity_scope": reduced_identity_scope,
        }

    if not isinstance(p_ref, (int, float)) or p_ref <= 0:
        return {
            "signal": "NO_DATA",
            "color": SIGNAL_TO_COLOR["NO_DATA"],
            "ppi": None,
            "overlay": _get_overlay(payload.get("integrity_status")),
            "reduced_identity_scope": reduced_identity_scope,
        }

    if not isinstance(cs, (int, float)) or cs < 0 or cs > 1:
        return {
            "signal": "NO_DATA",
            "color": SIGNAL_TO_COLOR["NO_DATA"],
            "ppi": None,
            "overlay": _get_overlay(payload.get("integrity_status")),
            "reduced_identity_scope": reduced_identity_scope,
        }

    profile_name = payload.get("applied_profile", "BASE")
    threshold = get_profile(profile_name).CS_display_threshold

    if cs < threshold:
        return {
            "signal": "NO_DATA",
            "color": SIGNAL_TO_COLOR["NO_DATA"],
            "ppi": None,
            "overlay": _get_overlay(payload.get("integrity_status")),
            "reduced_identity_scope": reduced_identity_scope,
        }

    ppi = (float(p_offer) - float(p_ref)) / float(p_ref)

    if ppi <= -T_LOW:
        signal = "BELOW_MARKET"
    elif -T_LOW < ppi < -T_NEAR:
        signal = "SLIGHTLY_BELOW"
    elif -T_NEAR <= ppi <= T_NEAR:
        signal = "NEAR_MARKET"
    elif T_NEAR < ppi < T_HIGH:
        signal = "SLIGHTLY_ABOVE"
    else:
        signal = "ABOVE_MARKET"

    return {
        "signal": signal,
        "color": SIGNAL_TO_COLOR[signal],
        "ppi": ppi,
        "overlay": _get_overlay(payload.get("integrity_status")),
        "reduced_identity_scope": reduced_identity_scope,
    }
