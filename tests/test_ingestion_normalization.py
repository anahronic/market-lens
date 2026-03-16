"""
DKP-PTL-REG v0.6 — Ingestion Normalization Tests

Tests for deterministic normalization behavior per REFERENCE-001.
"""

import pytest

from ingestion.normalize import (
    normalize_string,
    normalize_timestamp,
    extract_domain_id,
    build_evidence_hash,
    normalize_observation,
    normalize_batch,
    RejectionReason,
)


# ---------------------------------------------------------------------------
# String Normalization Tests (REFERENCE-001 Section 3)
# ---------------------------------------------------------------------------

def test_normalize_string_nfc():
    """NFC normalization is applied."""
    # Decomposed e-acute: e + combining acute
    decomposed = "caf\u0065\u0301"
    # Composed e-acute
    composed = "caf\u00e9"
    
    result = normalize_string(decomposed)
    # After NFC + casefold
    assert result == normalize_string(composed)


def test_normalize_string_ascii_trim_only():
    """Only ASCII whitespace is trimmed."""
    # Leading/trailing ASCII spaces
    assert normalize_string("  hello  ") == "hello"
    # Tabs and newlines
    assert normalize_string("\t\nhello\r\n") == "hello"
    # Non-breaking space is NOT trimmed (not ASCII whitespace)
    assert normalize_string("\u00a0hello\u00a0") == "\u00a0hello\u00a0"


def test_normalize_string_lowercase():
    """Locale-independent casefold is applied."""
    assert normalize_string("HELLO") == "hello"
    assert normalize_string("Hello World") == "hello world"
    # German sharp s
    assert normalize_string("Straße") == "strasse"


def test_normalize_string_missing_field():
    """Missing/None fields normalize to empty string."""
    assert normalize_string(None) == ""
    assert normalize_string("") == ""


# ---------------------------------------------------------------------------
# Timestamp Normalization Tests (REFERENCE-001 Section 6)
# ---------------------------------------------------------------------------

def test_normalize_timestamp_integer():
    """Integer timestamps pass through."""
    result = normalize_timestamp(1699900000, 1700000000)
    assert result == 1699900000


def test_normalize_timestamp_float_flooring():
    """Float timestamps are floored."""
    result = normalize_timestamp(1699900000.9, 1700000000)
    assert result == 1699900000


def test_normalize_timestamp_future_rejection():
    """Timestamps > current_time + 5 seconds are rejected."""
    # More than 5 seconds in future
    result = normalize_timestamp(1700000010, 1700000000)
    assert result is None


def test_normalize_timestamp_future_tolerance():
    """Timestamps within 5 seconds of current_time are accepted."""
    # Exactly 5 seconds in future
    result = normalize_timestamp(1700000005, 1700000000)
    assert result == 1700000005
    
    # 3 seconds in future
    result = normalize_timestamp(1700000003, 1700000000)
    assert result == 1700000003


def test_normalize_timestamp_iso8601():
    """ISO-8601 strings are parsed."""
    result = normalize_timestamp("2023-11-14T00:00:00Z", 1700000000)
    assert result is not None
    assert isinstance(result, int)


def test_normalize_timestamp_invalid():
    """Invalid timestamps return None."""
    assert normalize_timestamp("not-a-timestamp", 1700000000) is None
    assert normalize_timestamp(None, 1700000000) is None
    assert normalize_timestamp(float("inf"), 1700000000) is None


# ---------------------------------------------------------------------------
# Domain Extraction Tests (REFERENCE-001 Section 4)
# ---------------------------------------------------------------------------

def test_extract_domain_simple():
    """Simple domain extraction."""
    result = extract_domain_id("https://shop.example.com/path")
    assert result == "example.com"


def test_extract_domain_subdomain():
    """Subdomains collapse to root domain."""
    result = extract_domain_id("https://sub.shop.example.com/path")
    assert result == "example.com"


def test_extract_domain_with_port():
    """Port is removed."""
    result = extract_domain_id("https://shop.example.com:8080/path")
    assert result == "example.com"


def test_extract_domain_co_uk():
    """Multi-part TLDs handled correctly."""
    result = extract_domain_id("https://shop.example.co.uk/path")
    assert result == "example.co.uk"


def test_extract_domain_invalid():
    """Invalid URLs return None."""
    assert extract_domain_id("not-a-url") is None
    assert extract_domain_id("") is None


# ---------------------------------------------------------------------------
# Evidence Hash Tests (REFERENCE-001 Section 8)
# ---------------------------------------------------------------------------

def test_evidence_hash_stability():
    """Same inputs produce same hash."""
    pil = {
        "brand": "test",
        "model": "model",
        "sku": "sku",
        "condition": "new",
        "bundle_flag": "",
        "warranty_type": "",
        "region_variant": "",
        "storage_or_size": "",
        "release_year": "2025",
    }
    
    hash1 = build_evidence_hash(
        "example.com", "merchant", 100.0, "usd", 1699900000, "us", pil
    )
    hash2 = build_evidence_hash(
        "example.com", "merchant", 100.0, "usd", 1699900000, "us", pil
    )
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex


def test_evidence_hash_different_inputs():
    """Different inputs produce different hashes."""
    pil = {
        "brand": "test",
        "model": "model",
        "sku": "sku",
        "condition": "new",
        "bundle_flag": "",
        "warranty_type": "",
        "region_variant": "",
        "storage_or_size": "",
        "release_year": "2025",
    }
    
    hash1 = build_evidence_hash(
        "example.com", "merchant", 100.0, "usd", 1699900000, "us", pil
    )
    hash2 = build_evidence_hash(
        "example.com", "merchant", 101.0, "usd", 1699900000, "us", pil
    )
    
    assert hash1 != hash2


# ---------------------------------------------------------------------------
# Observation Normalization Tests
# ---------------------------------------------------------------------------

def test_normalize_observation_valid():
    """Valid observation is normalized."""
    raw = {
        "source_url": "https://shop.example.com/p",
        "merchant_id": "merchant",
        "price": 100.0,
        "currency": "USD",
        "region": "US",
        "timestamp": 1699900000,
        "product_identity_layer": {
            "brand": "Brand",
            "model": "Model",
            "sku": "SKU",
            "condition": "new",
            "bundle_flag": "",
            "warranty_type": "",
            "region_variant": "",
            "storage_or_size": "",
            "release_year": "2025",
        },
    }
    
    result = normalize_observation(raw, 1700000000)
    
    assert result.accepted is True
    assert result.observation is not None
    assert result.observation["price"] == 100.0
    assert result.observation["currency"] == "usd"  # Normalized
    assert result.observation["region"] == "us"  # Normalized
    assert result.observation["domain_id"] == "example.com"


def test_normalize_observation_invalid_price():
    """Invalid price causes rejection."""
    raw = {
        "source_url": "https://shop.example.com/p",
        "merchant_id": "merchant",
        "price": -10.0,
        "currency": "USD",
        "region": "US",
        "timestamp": 1699900000,
        "product_identity_layer": {},
    }
    
    result = normalize_observation(raw, 1700000000)
    
    assert result.accepted is False
    assert result.rejection_reason == RejectionReason.INVALID_PRICE


def test_normalize_observation_missing_currency():
    """Missing currency causes rejection."""
    raw = {
        "source_url": "https://shop.example.com/p",
        "merchant_id": "merchant",
        "price": 100.0,
        "currency": "",
        "region": "US",
        "timestamp": 1699900000,
        "product_identity_layer": {},
    }
    
    result = normalize_observation(raw, 1700000000)
    
    assert result.accepted is False
    assert result.rejection_reason == RejectionReason.MISSING_CURRENCY


# ---------------------------------------------------------------------------
# Batch Normalization Tests
# ---------------------------------------------------------------------------

def test_normalize_batch_mixed():
    """Batch with mixed valid/invalid observations."""
    observations = [
        {
            "source_url": "https://shop1.com/p",
            "merchant_id": "m1",
            "price": 100.0,
            "currency": "usd",
            "region": "us",
            "timestamp": 1699900000,
            "product_identity_layer": {
                "brand": "B",
                "model": "M",
                "sku": "S",
                "condition": "new",
                "bundle_flag": "",
                "warranty_type": "",
                "region_variant": "",
                "storage_or_size": "",
                "release_year": "2025",
            },
        },
        {
            "source_url": "https://shop2.com/p",
            "merchant_id": "m2",
            "price": -50.0,  # Invalid
            "currency": "usd",
            "region": "us",
            "timestamp": 1699900000,
            "product_identity_layer": {},
        },
    ]
    
    result = normalize_batch(observations, 1700000000)
    
    assert result.accepted_count == 1
    assert result.rejected_count == 1
    assert RejectionReason.INVALID_PRICE in result.rejection_reason_counts


def test_normalize_batch_deterministic_rejection_summary():
    """Rejection summary is deterministic."""
    observations = [
        {"price": -1, "currency": "usd", "region": "us", "timestamp": 1699900000, "product_identity_layer": {}},
        {"price": -2, "currency": "usd", "region": "us", "timestamp": 1699900000, "product_identity_layer": {}},
        {"price": 100, "currency": "", "region": "us", "timestamp": 1699900000, "product_identity_layer": {}},
    ]
    
    result1 = normalize_batch(observations, 1700000000)
    result2 = normalize_batch(observations, 1700000000)
    
    assert result1.rejection_reason_counts == result2.rejection_reason_counts
    assert result1.accepted_count == result2.accepted_count
    assert result1.rejected_count == result2.rejected_count
