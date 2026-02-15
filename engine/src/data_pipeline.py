"""
DKP-PTL-REG-DATA-001 v0.6 — Deterministic Data Processing Pipeline

18-step deterministic pipeline executed exactly once in order.
No step may be skipped. No implicit recomputation. No recursion.

IEEE 754 double precision. Round half to even.
Stable sorting with deterministic tie-breaking.
"""

import hashlib
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .constants import ProfileConstants


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clamp01(x: float) -> float:
    """clamp01(x) = min(1, max(0, x))"""
    return min(1.0, max(0.0, x))


def _round6(x: float) -> float:
    """Round to 6 decimal places, half to even (Python default)."""
    return round(x, 6)


def _sha256_to_normalized_float(s: str) -> float:
    """
    SHA256(string)[0:64bits] normalized to [0,1].

    Per DATA-001 Step 10: take first 8 bytes of SHA256 hash,
    interpret as 64-bit unsigned integer, normalize to [0,1].
    """
    h = hashlib.sha256(s.encode("utf-8")).digest()
    # First 8 bytes as big-endian unsigned 64-bit integer
    val = int.from_bytes(h[:8], byteorder="big", signed=False)
    return val / (2**64 - 1)


# ---------------------------------------------------------------------------
# Observation wrapper for pipeline processing
# ---------------------------------------------------------------------------

@dataclass
class PipelineObservation:
    """An observation flowing through the 18-step pipeline."""

    index: int  # Original index for stable sorting
    price: float
    timestamp: int
    domain_id: str
    merchant_id: str
    evidence_hash: str
    age: float  # Computed in Step 2
    window_index: int = 0

    # Weights
    W_time: float = 1.0  # Step 3
    W_burst: float = 1.0  # Step 4 (per-domain, assigned to obs)
    W_raw: float = 1.0  # Step 5
    w: float = 0.0  # Final normalized weight (Step 8)

    # Similarity
    W_similarity: float = 1.0  # Step 10
    cluster_id: int = -1

    # Identity scope fields (for scope resolution)
    bundle_flag: str = ""
    warranty_type: str = ""

    # PIL fields for identity matching
    pil: Dict[str, str] = field(default_factory=dict)
    region: str = ""
    currency: str = ""

    # Tie-breaking key (Step 9)
    tie_key: Tuple[str, ...] = field(default_factory=tuple)

    # Discarded flag
    discarded: bool = False


# ---------------------------------------------------------------------------
# Pipeline Result
# ---------------------------------------------------------------------------

@dataclass
class PipelineResult:
    """Output of the 18-step pipeline."""

    P_ref: Optional[float] = None
    MAD: Optional[float] = None
    CS: float = 0.0
    N_eff: float = 0.0
    cold_start_flag: bool = False
    insufficient_data_flag: bool = False
    identity_scope_level: Optional[int] = None
    display_text: str = "Low Confidence"

    # For threat status computation
    burst_detected: bool = False
    domain_dominance_detected: bool = False
    cluster_weight_loss_ratio: float = 0.0

    # Internal: domain weights
    final_D_j: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Identity Scope Resolution (Pre-Processing Phase)
# ---------------------------------------------------------------------------

def _observations_match_level(
    a: PipelineObservation, b: PipelineObservation, level: int
) -> bool:
    """
    Check if two observations match at identity level.

    Level 0: Match all identity fields exactly.
    Level 1: Ignore bundle_flag.
    Level 2: Ignore bundle_flag and warranty_type.

    Missing fields treated as "".
    """
    # Compare PIL fields
    a_pil = a.pil
    b_pil = b.pil

    fields_to_compare = [
        "brand", "model", "sku", "condition",
        "region_variant", "storage_or_size", "release_year",
    ]

    if level < 1:
        fields_to_compare.append("bundle_flag")
    if level < 2:
        fields_to_compare.append("warranty_type")

    for f in fields_to_compare:
        val_a = a_pil.get(f, "")
        val_b = b_pil.get(f, "")
        if val_a != val_b:
            return False

    # Must also match region and currency
    if a.region != b.region or a.currency != b.currency:
        return False

    return True


def _resolve_identity_scope(
    O_all: List[PipelineObservation],
) -> Tuple[List[PipelineObservation], Optional[int]]:
    """
    Identity Scope Resolution per DATA-001 Pre-Processing Phase.

    For each level L in {0,1,2}:
      Construct O_L as subset of O_all sharing identity at level L.
      If |O_L| >= 2: select and break.

    Since all observations share identical OCV/region/currency (filtered upstream),
    we check PIL fields at each level. We use the first observation as reference
    and find all matching observations.

    Actually per spec: O_L is the subset where ALL share identity at level L.
    This means: find the largest group of mutually identical observations at level L.
    """
    if len(O_all) == 0:
        return [], None

    for level in (0, 1, 2):
        # Group observations by identity at this level
        groups: Dict[str, List[PipelineObservation]] = {}
        for obs in O_all:
            # Build identity key at this level
            pil = obs.pil
            fields = [
                "brand", "model", "sku", "condition",
                "region_variant", "storage_or_size", "release_year",
            ]
            if level < 1:
                fields.append("bundle_flag")
            if level < 2:
                fields.append("warranty_type")

            key_parts = [pil.get(f, "") for f in fields]
            key_parts.append(obs.region)
            key_parts.append(obs.currency)
            key = "|".join(key_parts)
            groups.setdefault(key, []).append(obs)

        # Find the largest group at this level
        best_group: List[PipelineObservation] = []
        for g in groups.values():
            if len(g) > len(best_group):
                best_group = g

        if len(best_group) >= 2:
            return best_group, level

    # No level found with >= 2 observations
    return [], None


# ---------------------------------------------------------------------------
# Core Pipeline Steps
# ---------------------------------------------------------------------------

def _step2_temporal_validation(
    observations: List[PipelineObservation],
    current_time_utc: int,
    max_age_cutoff: float,
) -> List[PipelineObservation]:
    """Step 2: Temporal Validation."""
    result = []
    for obs in observations:
        age = float(current_time_utc - obs.timestamp)
        if age < 0:
            continue  # Discard
        if age > max_age_cutoff:
            continue  # Discard
        obs.age = age
        swd = 86400.0  # stability_window_duration_seconds
        obs.window_index = int(math.floor(obs.timestamp / swd))
        result.append(obs)
    return result


def _step3_temporal_weight(
    observations: List[PipelineObservation],
    T_half_default: float,
) -> None:
    """Step 3: Temporal Weight — W_time_i = 2^(-age_i / T_half_default)"""
    for obs in observations:
        obs.W_time = 2.0 ** (-obs.age / T_half_default)


def _step4_burst_detection(
    observations: List[PipelineObservation],
    constants: ProfileConstants,
) -> Dict[str, float]:
    """
    Step 4: Burst Detection.

    For each domain j, compute burst_ratio and W_burst.
    Returns dict of domain_id -> W_burst_j.
    Also sets burst_detected flag.
    """
    swd = constants.stability_window_duration_seconds

    # Group observations by domain
    domain_obs: Dict[str, List[PipelineObservation]] = {}
    for obs in observations:
        domain_obs.setdefault(obs.domain_id, []).append(obs)

    # Compute global baseline (for N_baseline_j = 0 case)
    all_window_indices = set()
    for obs in observations:
        all_window_indices.add(obs.window_index)

    burst_detected = False
    domain_w_burst: Dict[str, float] = {}

    for domain_id, obs_list in domain_obs.items():
        # Group by window_index
        window_counts: Dict[int, int] = {}
        for obs in obs_list:
            window_counts[obs.window_index] = window_counts.get(obs.window_index, 0) + 1

        if not window_counts:
            domain_w_burst[domain_id] = 1.0
            continue

        # Most recent window
        sorted_windows = sorted(window_counts.keys())
        recent_window = sorted_windows[-1]
        N_recent_j = window_counts[recent_window]

        # Baseline: median of counts in last 7 windows (excluding current)
        baseline_windows = sorted_windows[-8:-1] if len(sorted_windows) > 1 else []
        baseline_counts = [window_counts.get(w, 0) for w in baseline_windows]

        # Fill missing windows with 0
        if len(baseline_windows) < 7 and len(sorted_windows) > 1:
            # Consider windows that exist
            all_domain_windows = sorted_windows[:-1][-7:]
            baseline_counts = [window_counts.get(w, 0) for w in all_domain_windows]

        if len(baseline_counts) < 3:
            burst_threshold_effective = constants.early_window_multiplier
        else:
            burst_threshold_effective = constants.burst_threshold_multiplier

        # N_baseline_j = median of baseline counts
        if len(baseline_counts) == 0:
            N_baseline_j = 0.0
        else:
            sorted_counts = sorted(baseline_counts)
            mid = len(sorted_counts) // 2
            if len(sorted_counts) % 2 == 0 and len(sorted_counts) > 0:
                N_baseline_j = (sorted_counts[mid - 1] + sorted_counts[mid]) / 2.0
            else:
                N_baseline_j = float(sorted_counts[mid])

        if N_baseline_j == 0:
            # Use global baseline
            global_counts = []
            for w in sorted(all_window_indices):
                count = 0
                for o in observations:
                    if o.window_index == w:
                        count += 1
                global_counts.append(count)
            if global_counts:
                sorted_gc = sorted(global_counts)
                mid = len(sorted_gc) // 2
                if len(sorted_gc) % 2 == 0:
                    N_baseline_j = (sorted_gc[mid - 1] + sorted_gc[mid]) / 2.0
                else:
                    N_baseline_j = float(sorted_gc[mid])

        burst_ratio_j = N_recent_j / max(N_baseline_j, 1.0)

        if burst_ratio_j > burst_threshold_effective:
            domain_w_burst[domain_id] = 1.0 / burst_ratio_j
            burst_detected = True
        else:
            domain_w_burst[domain_id] = 1.0

    return domain_w_burst


def _step5_raw_weight(
    observations: List[PipelineObservation],
    domain_w_burst: Dict[str, float],
) -> None:
    """Step 5: Raw Observation Weight — W_raw_i = W_time_i × W_burst_j"""
    for obs in observations:
        obs.W_burst = domain_w_burst.get(obs.domain_id, 1.0)
        obs.W_raw = obs.W_time * obs.W_burst


def _step6_domain_aggregation(
    observations: List[PipelineObservation],
) -> Tuple[Dict[str, float], float]:
    """
    Step 6: Domain Aggregation.

    D_j_raw = Σ W_raw_i (over observations in domain j)
    Total_raw = Σ D_j_raw
    """
    D_j_raw: Dict[str, float] = {}
    for obs in observations:
        if obs.discarded:
            continue
        D_j_raw[obs.domain_id] = D_j_raw.get(obs.domain_id, 0.0) + obs.W_raw
    Total_raw = sum(D_j_raw.values())
    return D_j_raw, Total_raw


def _step7_domain_cap(
    D_j_raw: Dict[str, float],
    Total_raw: float,
    cap_percent: float,
) -> Tuple[Dict[str, float], float, bool]:
    """
    Step 7: Domain Cap.

    D_j_capped = min(D_j_raw, cap_percent × Total_raw)
    Returns (D_j_capped, Total_capped, domain_dominance_detected)
    """
    D_j_capped: Dict[str, float] = {}
    domain_dominance = False
    for domain_id, d_raw in D_j_raw.items():
        cap = cap_percent * Total_raw
        if d_raw > cap:
            D_j_capped[domain_id] = cap
            domain_dominance = True
        else:
            D_j_capped[domain_id] = d_raw
    Total_capped = sum(D_j_capped.values())
    return D_j_capped, Total_capped, domain_dominance


def _step8_domain_normalization(
    observations: List[PipelineObservation],
    D_j_raw: Dict[str, float],
    D_j_capped: Dict[str, float],
    Total_capped: float,
) -> Dict[str, float]:
    """
    Step 8: Domain Normalization and Observation Weights.

    D_j = D_j_capped / Total_capped
    w_i = W_raw_i × (D_j / D_j_raw)

    Returns D_j (normalized domain weights).
    """
    D_j: Dict[str, float] = {}
    for domain_id, d_capped in D_j_capped.items():
        D_j[domain_id] = d_capped / Total_capped if Total_capped > 0 else 0.0

    for obs in observations:
        if obs.discarded:
            obs.w = 0.0
            continue
        d_raw = D_j_raw.get(obs.domain_id, 0.0)
        d_norm = D_j.get(obs.domain_id, 0.0)
        if d_raw == 0.0:
            obs.w = 0.0
        else:
            obs.w = obs.W_raw * (d_norm / d_raw)

    return D_j


def _step9_weighted_median(
    observations: List[PipelineObservation],
) -> Optional[float]:
    """
    Step 9: Preliminary Reference Price (weighted median).

    Sort tuples (p_i, tie_key_i, w_i) ascending by:
    1. p_i
    2. tie_key_i (lexicographic)

    tie_key_i = (domain_id, merchant_id, t_i, p_i) — all UTF-8 lowercase.

    Find smallest k such that cumulative Σ w_i >= 0.5
    P_ref_pre = p_k
    """
    active = [obs for obs in observations if not obs.discarded and obs.w > 0]
    if not active:
        return None

    # Build tie keys
    for obs in active:
        obs.tie_key = (
            obs.domain_id,
            obs.merchant_id,
            str(obs.timestamp),
            str(obs.price),
        )

    # Stable sort by (price, tie_key)
    active.sort(key=lambda o: (o.price, o.tie_key))

    total_w = sum(o.w for o in active)
    if total_w == 0:
        return None

    cumulative = 0.0
    for obs in active:
        cumulative += obs.w
        if cumulative >= 0.5 * total_w:
            return obs.price

    # Should not reach here, but return last price
    return active[-1].price


def _step10_similarity_groups(
    observations: List[PipelineObservation],
    P_ref_pre: float,
    max_age_cutoff: float,
    similarity_threshold: float,
) -> float:
    """
    Step 10: Similarity Groups.

    Compute feature vectors, cosine similarity, union-find clustering.
    Apply W_similarity_i = 1/n_k.
    Update W_raw_i = W_raw_i × W_similarity_i.

    Returns cluster_weight_loss_ratio for threat status.
    """
    active = [obs for obs in observations if not obs.discarded]
    if not active:
        return 0.0

    total_raw_before = sum(obs.W_raw for obs in active)

    # Compute feature vectors
    feature_vectors: Dict[int, List[float]] = {}
    for obs in active:
        # normalized_price
        normalized_price = obs.price / P_ref_pre if P_ref_pre > 0 else 0.0
        # normalized_time
        normalized_time = obs.age / max_age_cutoff if max_age_cutoff > 0 else 0.0
        # domain_hash
        if obs.domain_id == "":
            domain_hash = 0.0
        else:
            domain_hash = _sha256_to_normalized_float(obs.domain_id)
        # merchant_hash
        if obs.merchant_id == "":
            merchant_hash = 0.0
        else:
            merchant_hash = _sha256_to_normalized_float(obs.merchant_id)

        fv = [normalized_price, normalized_time, domain_hash, merchant_hash]

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in fv))
        if norm != 0.0:
            fv = [x / norm for x in fv]

        feature_vectors[obs.index] = fv

    # Determine which observations can be clustered together:
    # Two observations may be considered for clustering iff they share domain_id OR merchant_id
    # Sort active observations by (price, tie_key) for deterministic union-find
    sorted_active = sorted(active, key=lambda o: (o.price, o.tie_key))

    # Union-Find
    parent: Dict[int, int] = {obs.index: obs.index for obs in sorted_active}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            # Deterministic: always merge higher index into lower
            if rx < ry:
                parent[ry] = rx
            else:
                parent[rx] = ry

    # Compare pairs — only those sharing domain_id OR merchant_id
    for i_idx in range(len(sorted_active)):
        for j_idx in range(i_idx + 1, len(sorted_active)):
            a = sorted_active[i_idx]
            b = sorted_active[j_idx]

            # Check clustering eligibility
            shares_domain = (a.domain_id != "" and a.domain_id == b.domain_id)
            shares_merchant = (a.merchant_id != "" and a.merchant_id == b.merchant_id)

            if not (shares_domain or shares_merchant):
                continue

            # Compute cosine similarity
            fv_a = feature_vectors[a.index]
            fv_b = feature_vectors[b.index]
            dot = sum(x * y for x, y in zip(fv_a, fv_b))

            if dot >= similarity_threshold:
                union(a.index, b.index)

    # Collect clusters
    clusters: Dict[int, List[PipelineObservation]] = {}
    for obs in sorted_active:
        root = find(obs.index)
        clusters.setdefault(root, []).append(obs)

    # Apply W_similarity_i = 1/n_k
    for cluster_obs_list in clusters.values():
        n_k = len(cluster_obs_list)
        for obs in cluster_obs_list:
            obs.W_similarity = 1.0 / n_k
            obs.W_raw = obs.W_raw * obs.W_similarity

    total_raw_after = sum(obs.W_raw for obs in active)

    # Compute cluster weight loss ratio for THREAT-001
    if total_raw_before > 0:
        loss = total_raw_before - total_raw_after
        cluster_weight_loss_ratio = loss / total_raw_before
    else:
        cluster_weight_loss_ratio = 0.0

    return cluster_weight_loss_ratio


def _step12_outlier_filtering(
    observations: List[PipelineObservation],
    P_ref_pre: float,
    z_max: float,
) -> None:
    """
    Step 12: Outlier Filtering.

    MAD_pre = median(|p_i - P_ref_pre|)
    z_i = |p_i - P_ref_pre| / MAD_pre (if MAD_pre != 0, else z_i = 0)
    If z_i > z_max → discard observation
    """
    active = [obs for obs in observations if not obs.discarded]
    if not active:
        return

    deviations = sorted([abs(obs.price - P_ref_pre) for obs in active])

    # Compute median of deviations
    n = len(deviations)
    if n == 0:
        return
    mid = n // 2
    if n % 2 == 0:
        MAD_pre = (deviations[mid - 1] + deviations[mid]) / 2.0
    else:
        MAD_pre = deviations[mid]

    for obs in active:
        if MAD_pre == 0.0:
            z_i = 0.0
        else:
            z_i = abs(obs.price - P_ref_pre) / MAD_pre
        if z_i > z_max:
            obs.discarded = True


# ---------------------------------------------------------------------------
# Main Pipeline Execution
# ---------------------------------------------------------------------------

def execute_pipeline(
    observations_raw: List[Dict[str, Any]],
    constants: ProfileConstants,
    current_time_utc: int,
) -> PipelineResult:
    """
    Execute the full 18-step deterministic pipeline per DATA-001 v0.6.

    Observations must already be validated/normalized by REFERENCE-001.
    Each dict must have: price, timestamp, domain_id, merchant_id,
    evidence_hash, pil, region, currency, bundle_flag, warranty_type.
    """
    result = PipelineResult()

    # Initialize state per DATA-001 Section 0
    cold_start_flag = False
    insufficient_data_flag = False
    P_ref: Optional[float] = None
    MAD: Optional[float] = None
    CS = 0.0
    N_eff = 0.0

    # Convert to PipelineObservation
    O_all: List[PipelineObservation] = []
    for i, raw in enumerate(observations_raw):
        obs = PipelineObservation(
            index=i,
            price=raw["price"],
            timestamp=raw["timestamp"],
            domain_id=raw["domain_id"],
            merchant_id=raw["merchant_id"],
            evidence_hash=raw["evidence_hash"],
            age=0.0,
            pil=raw.get("pil", {}),
            region=raw.get("region", ""),
            currency=raw.get("currency", ""),
            bundle_flag=raw.get("bundle_flag", ""),
            warranty_type=raw.get("warranty_type", ""),
        )
        # Pre-compute tie_key for deterministic sorting
        obs.tie_key = (
            obs.domain_id,
            obs.merchant_id,
            str(obs.timestamp),
            str(obs.price),
        )
        O_all.append(obs)

    # -----------------------------------------------------------------------
    # Identity Scope Resolution (Pre-Processing Phase)
    # Executes exactly once before Step 1.
    # -----------------------------------------------------------------------
    O, identity_scope_level = _resolve_identity_scope(O_all)
    result.identity_scope_level = identity_scope_level

    if len(O) == 0:
        # No valid observations
        result.P_ref = None
        result.MAD = None
        result.CS = 0.0
        result.N_eff = 0.0
        result.cold_start_flag = True
        result.insufficient_data_flag = True
        return result

    # -----------------------------------------------------------------------
    # Step 1: Deterministic Processing Order begins
    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------
    # Step 2: Temporal Validation
    # -----------------------------------------------------------------------
    O = _step2_temporal_validation(O, current_time_utc, constants.max_age_cutoff)
    if len(O) == 0:
        result.P_ref = None
        result.MAD = None
        result.CS = 0.0
        result.N_eff = 0.0
        result.cold_start_flag = True
        result.insufficient_data_flag = True
        return result

    # -----------------------------------------------------------------------
    # Step 3: Temporal Weight
    # -----------------------------------------------------------------------
    _step3_temporal_weight(O, constants.T_half_default)

    # -----------------------------------------------------------------------
    # Step 4: Burst Detection
    # -----------------------------------------------------------------------
    domain_w_burst = _step4_burst_detection(O, constants)

    # Check if burst was detected (for threat status)
    burst_detected = False
    for obs in O:
        wb = domain_w_burst.get(obs.domain_id, 1.0)
        if wb < 1.0:
            burst_detected = True
            break
    result.burst_detected = burst_detected

    # -----------------------------------------------------------------------
    # Step 5: Raw Observation Weight
    # -----------------------------------------------------------------------
    _step5_raw_weight(O, domain_w_burst)

    # -----------------------------------------------------------------------
    # Step 6: Domain Aggregation
    # -----------------------------------------------------------------------
    D_j_raw, Total_raw = _step6_domain_aggregation(O)

    # -----------------------------------------------------------------------
    # Step 7: Domain Cap
    # -----------------------------------------------------------------------
    D_j_capped, Total_capped, domain_dominance = _step7_domain_cap(
        D_j_raw, Total_raw, constants.domain_contribution_cap_percent
    )
    result.domain_dominance_detected = domain_dominance

    if Total_capped == 0.0:
        result.P_ref = None
        result.MAD = None
        result.N_eff = 0.0
        result.CS = 0.0
        result.cold_start_flag = True
        result.insufficient_data_flag = True
        return result

    # -----------------------------------------------------------------------
    # Step 8: Domain Normalization and Observation Weights
    # -----------------------------------------------------------------------
    D_j = _step8_domain_normalization(O, D_j_raw, D_j_capped, Total_capped)

    # -----------------------------------------------------------------------
    # Step 9: Preliminary Reference Price
    # -----------------------------------------------------------------------
    P_ref_pre = _step9_weighted_median(O)
    if P_ref_pre is None:
        result.P_ref = None
        result.MAD = None
        result.N_eff = 0.0
        result.CS = 0.0
        result.cold_start_flag = True
        result.insufficient_data_flag = True
        return result

    # -----------------------------------------------------------------------
    # Step 10: Similarity Groups
    # -----------------------------------------------------------------------
    # Save total W_raw before similarity for threat status
    cluster_weight_loss_ratio = _step10_similarity_groups(
        O, P_ref_pre, constants.max_age_cutoff, constants.cluster_similarity_threshold
    )
    result.cluster_weight_loss_ratio = cluster_weight_loss_ratio

    # -----------------------------------------------------------------------
    # Step 11: Single Deterministic Recompute
    # Repeat Steps 6-7-8-9 exactly once. No further repetitions allowed.
    # -----------------------------------------------------------------------
    D_j_raw, Total_raw = _step6_domain_aggregation(O)
    D_j_capped, Total_capped, dom_dom_2 = _step7_domain_cap(
        D_j_raw, Total_raw, constants.domain_contribution_cap_percent
    )
    if dom_dom_2:
        result.domain_dominance_detected = True

    if Total_capped == 0.0:
        result.P_ref = None
        result.MAD = None
        result.N_eff = 0.0
        result.CS = 0.0
        result.cold_start_flag = True
        result.insufficient_data_flag = True
        return result

    D_j = _step8_domain_normalization(O, D_j_raw, D_j_capped, Total_capped)
    P_ref_pre = _step9_weighted_median(O)
    if P_ref_pre is None:
        result.P_ref = None
        result.MAD = None
        result.N_eff = 0.0
        result.CS = 0.0
        result.cold_start_flag = True
        result.insufficient_data_flag = True
        return result

    # -----------------------------------------------------------------------
    # Step 12: Outlier Filtering
    # -----------------------------------------------------------------------
    _step12_outlier_filtering(O, P_ref_pre, constants.z_max)

    # -----------------------------------------------------------------------
    # Step 13: Post-Outlier Renormalization
    # Recompute Steps 6-8 on remaining observations.
    # -----------------------------------------------------------------------
    D_j_raw, Total_raw = _step6_domain_aggregation(O)
    D_j_capped, Total_capped, dom_dom_3 = _step7_domain_cap(
        D_j_raw, Total_raw, constants.domain_contribution_cap_percent
    )
    if dom_dom_3:
        result.domain_dominance_detected = True

    # Check Σ w_i = 0
    if Total_capped == 0.0:
        result.P_ref = None
        result.MAD = None
        result.N_eff = 0.0
        result.CS = 0.0
        result.cold_start_flag = True
        result.insufficient_data_flag = True
        return result

    D_j = _step8_domain_normalization(O, D_j_raw, D_j_capped, Total_capped)
    result.final_D_j = dict(D_j)

    # Check Σ w_i after normalization
    sum_w = sum(obs.w for obs in O if not obs.discarded)
    if sum_w == 0.0:
        result.P_ref = None
        result.MAD = None
        result.N_eff = 0.0
        result.CS = 0.0
        result.cold_start_flag = True
        result.insufficient_data_flag = True
        return result

    # -----------------------------------------------------------------------
    # Step 14: Final Reference Price
    # -----------------------------------------------------------------------
    P_ref = _step9_weighted_median(O)
    if P_ref is None:
        result.P_ref = None
        result.MAD = None
        result.N_eff = 0.0
        result.CS = 0.0
        result.cold_start_flag = True
        result.insufficient_data_flag = True
        return result

    # MAD = median(|p_i - P_ref|) — unweighted in v0.6
    remaining = [obs for obs in O if not obs.discarded]
    if remaining:
        abs_devs = sorted([abs(obs.price - P_ref) for obs in remaining])
        n = len(abs_devs)
        mid = n // 2
        if n % 2 == 0:
            MAD = (abs_devs[mid - 1] + abs_devs[mid]) / 2.0
        else:
            MAD = abs_devs[mid]
    else:
        MAD = None

    # -----------------------------------------------------------------------
    # Step 15: Effective Sample Size
    # -----------------------------------------------------------------------
    active_obs = [obs for obs in O if not obs.discarded]
    sum_w = sum(obs.w for obs in active_obs)
    sum_w2 = sum(obs.w ** 2 for obs in active_obs)

    if sum_w2 > 0:
        N_eff = (sum_w ** 2) / sum_w2
    else:
        N_eff = 0.0

    # -----------------------------------------------------------------------
    # Step 16: ColdStart Check
    # -----------------------------------------------------------------------
    if sum_w < constants.W_min or N_eff < constants.N_eff_min:
        result.P_ref = None
        result.MAD = None
        result.CS = 0.0
        result.N_eff = _round6(N_eff)
        result.cold_start_flag = True
        result.insufficient_data_flag = True
        return result

    # -----------------------------------------------------------------------
    # Step 17: Confidence Score
    # -----------------------------------------------------------------------
    CS_core = 1.0 - math.exp(-constants.k_n * N_eff)
    W_recency = sum_w
    max_D_j = max(D_j.values()) if D_j else 0.0
    W_diversity = 1.0 - max_D_j
    CS = clamp01(CS_core * W_recency * W_diversity)

    # -----------------------------------------------------------------------
    # Step 18: Display Rule
    # -----------------------------------------------------------------------
    if CS < constants.CS_display_threshold:
        display_text = "Low Confidence"
    else:
        display_text = f"Market Reference Price = {_round6(P_ref)}"

    # Populate result
    result.P_ref = _round6(P_ref)
    result.MAD = _round6(MAD) if MAD is not None else None
    result.CS = _round6(CS)
    result.N_eff = _round6(N_eff)
    result.cold_start_flag = False
    result.insufficient_data_flag = False
    result.display_text = display_text
    result.final_D_j = dict(D_j)

    return result
