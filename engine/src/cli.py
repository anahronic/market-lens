"""
DKP-PTL-REG Reference Engine v0.6 — CLI Entry Point

Usage:
    dkp-ptl-reg-engine run --input input.json --profile BASE --current_time_utc 1700000000

Deterministic. No implicit system clock reads.
All outputs include version metadata per GOV-001.
"""

import argparse
import json
import sys
from collections import OrderedDict
from typing import Any, Dict, List, Optional

from .constants import CONSTANTS_VERSION, PROTOCOL_VERSION, get_profile
from .data_pipeline import PipelineResult, execute_pipeline
from .reference_boundary import validate_observations
from .threat_status import compute_integrity_status


def _round6(x: Optional[float]) -> Optional[float]:
    """Round to 6 decimal places, half to even."""
    if x is None:
        return None
    return round(x, 6)


def _build_output(
    pipeline_result: PipelineResult,
    integrity_status: str,
    profile_name: str,
) -> OrderedDict:
    """
    Build deterministic output JSON with ordered keys per GOV-001.

    Output Schema Requirements (DATA-001 + THREAT-001):
    - applied_profile
    - protocol_version
    - constants_version
    - identity_scope_level
    - P_ref
    - MAD
    - CS
    - N_eff
    - cold_start_flag
    - insufficient_data_flag
    - integrity_status
    """
    output = OrderedDict()
    output["applied_profile"] = profile_name
    output["protocol_version"] = PROTOCOL_VERSION
    output["constants_version"] = CONSTANTS_VERSION
    output["identity_scope_level"] = pipeline_result.identity_scope_level
    output["P_ref"] = _round6(pipeline_result.P_ref)
    output["MAD"] = _round6(pipeline_result.MAD)
    output["CS"] = _round6(pipeline_result.CS)
    output["N_eff"] = _round6(pipeline_result.N_eff)
    output["cold_start_flag"] = pipeline_result.cold_start_flag
    output["insufficient_data_flag"] = pipeline_result.insufficient_data_flag
    output["integrity_status"] = integrity_status
    return output


def run_engine(
    input_data: Dict[str, Any],
    profile_name: str,
    current_time_utc: int,
) -> OrderedDict:
    """
    Execute the full Reference Engine pipeline.

    1. Validate/normalize observations (REFERENCE-001)
    2. Execute DATA-001 pipeline (Steps 1-18)
    3. Compute integrity_status (THREAT-001)
    4. Build output with version metadata (GOV-001)
    """
    constants = get_profile(profile_name)

    # Extract raw observations from input
    raw_observations = input_data.get("observations", [])

    # Step 0: Validate and normalize per REFERENCE-001
    normalized = validate_observations(raw_observations, current_time_utc)

    # Convert NormalizedObservation to dicts for pipeline
    obs_dicts: List[Dict[str, Any]] = []
    for obs in normalized:
        obs_dicts.append({
            "price": obs.price,
            "timestamp": obs.timestamp,
            "domain_id": obs.domain_id,
            "merchant_id": obs.merchant_id,
            "evidence_hash": obs.evidence_hash,
            "pil": obs.pil,
            "region": obs.region,
            "currency": obs.currency,
            "bundle_flag": obs.bundle_flag,
            "warranty_type": obs.warranty_type,
        })

    # Execute DATA-001 pipeline
    pipeline_result = execute_pipeline(obs_dicts, constants, current_time_utc)

    # Compute integrity_status per THREAT-001
    integrity_status = compute_integrity_status(pipeline_result, constants)

    # Build output
    return _build_output(pipeline_result, integrity_status, profile_name)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="dkp-ptl-reg-engine",
        description=(
            "DKP-PTL-REG Reference Engine v0.6 — "
            "Deterministic Price Transparency Engine"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 'run' command
    run_parser = subparsers.add_parser("run", help="Execute the engine pipeline")
    run_parser.add_argument(
        "--input",
        required=True,
        help="Path to input JSON file",
    )
    run_parser.add_argument(
        "--profile",
        required=True,
        choices=["BASE", "HARDENED"],
        help="Constants profile to apply",
    )
    run_parser.add_argument(
        "--current_time_utc",
        required=True,
        type=int,
        help="Current time as Unix epoch seconds (UTC). Engine never reads system clock.",
    )

    args = parser.parse_args()

    if args.command != "run":
        parser.print_help()
        sys.exit(1)

    # Load input
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            input_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)

    # Execute engine
    output = run_engine(input_data, args.profile, args.current_time_utc)

    # Output deterministic JSON (sorted keys are already ordered)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
