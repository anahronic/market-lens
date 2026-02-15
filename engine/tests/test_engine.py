"""
DKP-PTL-REG v0.6 — Pytest-compatible test suite.

Tests structural properties and determinism of the engine.
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from engine.src.cli import run_engine
from engine.src.constants import BASE, HARDENED, PROTOCOL_VERSION, CONSTANTS_VERSION
from engine.src.reference_boundary import (
    normalize_string,
    extract_host,
    get_root_domain,
    canonicalize_timestamp,
    canonicalize_merchant_id,
    compute_evidence_hash,
    validate_and_normalize,
)
from engine.src.json_canonical import canonical_json
from engine.src.data_pipeline import clamp01

VECTORS_DIR = Path(__file__).parent / "test_vectors"
CURRENT_TIME_UTC = 1700000000


# -----------------------------------------------------------------------
# Constants Tests
# -----------------------------------------------------------------------


def test_protocol_version():
    assert PROTOCOL_VERSION == "0.6.0"


def test_constants_version():
    assert CONSTANTS_VERSION == "0.6.0"


def test_base_profile_values():
    assert BASE.profile_name == "BASE"
    assert BASE.N_eff_min == 3.0
    assert BASE.W_min == 1.0
    assert BASE.k_n == 0.22
    assert BASE.T_half_default == 1209600.0
    assert BASE.max_age_cutoff == 7776000.0
    assert BASE.domain_contribution_cap_percent == 0.30
    assert BASE.cluster_similarity_threshold == 0.92
    assert BASE.burst_threshold_multiplier == 4.0
    assert BASE.early_window_multiplier == 2.0
    assert BASE.stability_window_duration_seconds == 86400.0
    assert BASE.z_max == 6.0
    assert BASE.CS_display_threshold == 0.15


def test_hardened_profile_values():
    assert HARDENED.profile_name == "HARDENED"
    assert HARDENED.N_eff_min == 3.5
    assert HARDENED.W_min == 1.5
    assert HARDENED.z_max == 4.5
    assert HARDENED.CS_display_threshold == 0.25


def test_profile_immutability():
    """Profiles are frozen dataclasses."""
    try:
        BASE.N_eff_min = 99.0
        assert False, "Should not be mutable"
    except AttributeError:
        pass


# -----------------------------------------------------------------------
# String Normalization Tests (REFERENCE-001 Section 3)
# -----------------------------------------------------------------------


def test_normalize_string_basic():
    assert normalize_string("  Hello World  ") == "hello world"


def test_normalize_string_unicode_casefold():
    # German sharp s: ß casefolds to ss
    assert normalize_string("Straße") == "strasse"


def test_normalize_string_none():
    assert normalize_string(None) == ""


def test_normalize_string_empty():
    assert normalize_string("") == ""


def test_normalize_string_tabs_newlines():
    assert normalize_string("\t  test  \n") == "test"


# -----------------------------------------------------------------------
# Domain Canonicalization Tests (REFERENCE-001 Section 4)
# -----------------------------------------------------------------------


def test_extract_host():
    assert extract_host("https://shop.example.com:443/path") == "shop.example.com"


def test_extract_host_missing():
    assert extract_host("not-a-url") is None


def test_root_domain_simple():
    result = get_root_domain("https://sub.shop.example.com/path")
    assert result == "example.com"


def test_root_domain_co_uk():
    result = get_root_domain("https://shop.example.co.uk/path")
    assert result == "example.co.uk"


def test_root_domain_localhost():
    result = get_root_domain("https://localhost/path")
    assert result == "localhost"


# -----------------------------------------------------------------------
# Timestamp Tests (REFERENCE-001 Section 6)
# -----------------------------------------------------------------------


def test_timestamp_integer():
    assert canonicalize_timestamp(1699000000, 1700000000) == 1699000000


def test_timestamp_float():
    assert canonicalize_timestamp(1699000000.7, 1700000000) == 1699000000


def test_timestamp_future_reject():
    # More than 5 seconds in the future
    assert canonicalize_timestamp(1700000010, 1700000000) is None


def test_timestamp_future_tolerance():
    # Within 5 seconds tolerance
    assert canonicalize_timestamp(1700000003, 1700000000) == 1700000003


def test_timestamp_iso8601():
    result = canonicalize_timestamp("2023-11-14T00:00:00Z", 1700000000)
    assert result is not None
    assert isinstance(result, int)


# -----------------------------------------------------------------------
# Merchant ID Tests (REFERENCE-001 Section 5)
# -----------------------------------------------------------------------


def test_merchant_id_normal():
    assert canonicalize_merchant_id("MyShop") == "myshop"


def test_merchant_id_none():
    assert canonicalize_merchant_id(None) == ""


def test_merchant_id_too_long():
    # 257 bytes should be rejected
    long_id = "a" * 257
    assert canonicalize_merchant_id(long_id) is None


# -----------------------------------------------------------------------
# JSON Canonical Tests
# -----------------------------------------------------------------------


def test_canonical_json_sorted_keys():
    result = canonical_json({"b": 1, "a": 2})
    assert result == '{"a":2,"b":1}'


def test_canonical_json_nested():
    result = canonical_json({"z": {"b": 1, "a": 2}, "a": 3})
    assert result == '{"a":3,"z":{"a":2,"b":1}}'


def test_canonical_json_no_whitespace():
    result = canonical_json({"key": "value"})
    assert " " not in result.replace('"value"', '"x"').replace('"key"', '"k"')


# -----------------------------------------------------------------------
# clamp01 Tests
# -----------------------------------------------------------------------


def test_clamp01_normal():
    assert clamp01(0.5) == 0.5


def test_clamp01_above():
    assert clamp01(1.5) == 1.0


def test_clamp01_below():
    assert clamp01(-0.5) == 0.0


# -----------------------------------------------------------------------
# Engine Output Schema Tests
# -----------------------------------------------------------------------

REQUIRED_OUTPUT_FIELDS = [
    "applied_profile",
    "protocol_version",
    "constants_version",
    "identity_scope_level",
    "P_ref",
    "MAD",
    "CS",
    "N_eff",
    "cold_start_flag",
    "insufficient_data_flag",
    "integrity_status",
]


def _load_and_run(input_file: str, profile: str = "BASE") -> dict:
    with open(VECTORS_DIR / input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return dict(run_engine(data, profile, CURRENT_TIME_UTC))


def test_output_schema_uniform():
    output = _load_and_run("uniform_market_input.json")
    for field in REQUIRED_OUTPUT_FIELDS:
        assert field in output, f"Missing field: {field}"


def test_output_schema_cold_start():
    output = _load_and_run("cold_start_input.json")
    for field in REQUIRED_OUTPUT_FIELDS:
        assert field in output, f"Missing field: {field}"


# -----------------------------------------------------------------------
# ColdStart Behavior Tests (DATA-001 Step 16)
# -----------------------------------------------------------------------


def test_cold_start_flag():
    output = _load_and_run("cold_start_input.json")
    assert output["cold_start_flag"] is True
    assert output["insufficient_data_flag"] is True
    assert output["P_ref"] is None
    assert output["MAD"] is None
    assert output["CS"] == 0.0
    assert output["integrity_status"] == "COLD_START"


# -----------------------------------------------------------------------
# Zero MAD Tests
# -----------------------------------------------------------------------


def test_zero_mad_price():
    output = _load_and_run("zero_mad_input.json")
    assert output["P_ref"] == 75.0
    assert output["MAD"] == 0.0
    assert output["cold_start_flag"] is False


# -----------------------------------------------------------------------
# Version Metadata Tests (GOV-001)
# -----------------------------------------------------------------------


def test_version_metadata():
    output = _load_and_run("uniform_market_input.json")
    assert output["applied_profile"] == "BASE"
    assert output["protocol_version"] == "0.6.0"
    assert output["constants_version"] == "0.6.0"


# -----------------------------------------------------------------------
# Determinism Tests
# -----------------------------------------------------------------------


def test_determinism_uniform():
    """Same input must produce identical output."""
    output1 = _load_and_run("uniform_market_input.json")
    output2 = _load_and_run("uniform_market_input.json")
    assert output1 == output2


def test_determinism_burst():
    output1 = _load_and_run("burst_attack_input.json")
    output2 = _load_and_run("burst_attack_input.json")
    assert output1 == output2


def test_determinism_cluster():
    output1 = _load_and_run("cluster_injection_input.json")
    output2 = _load_and_run("cluster_injection_input.json")
    assert output1 == output2


# -----------------------------------------------------------------------
# Profile Switching Tests
# -----------------------------------------------------------------------


def test_hardened_profile():
    output = _load_and_run("uniform_market_input.json", "HARDENED")
    assert output["applied_profile"] == "HARDENED"
    assert output["protocol_version"] == "0.6.0"


# -----------------------------------------------------------------------
# Integrity Status Tests (THREAT-001)
# -----------------------------------------------------------------------


def test_integrity_cold_start():
    output = _load_and_run("cold_start_input.json")
    assert output["integrity_status"] == "COLD_START"


def test_integrity_domain_dominance():
    output = _load_and_run("domain_dominance_input.json")
    assert output["integrity_status"] == "DOMAIN_DOMINANCE"


# -----------------------------------------------------------------------
# Rounding Tests
# -----------------------------------------------------------------------


def test_rounding_precision():
    """All numeric outputs must be rounded to 6 decimal places."""
    output = _load_and_run("uniform_market_input.json")
    for key in ["CS", "N_eff"]:
        val = output[key]
        if val is not None and isinstance(val, float):
            # Check that value has at most 6 decimal places
            s = f"{val:.10f}"
            decimal_part = s.split(".")[1]
            trailing = decimal_part[6:]
            assert trailing == "0000", f"{key}={val} has more than 6 decimals"
