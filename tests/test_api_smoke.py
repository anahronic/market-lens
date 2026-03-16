"""
DKP-PTL-REG v0.6 — API Smoke Tests

Smoke tests for API endpoints ensuring deterministic behavior.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from service.version_info import PROTOCOL_VERSION, CONSTANTS_VERSION


client = TestClient(app)


# ---------------------------------------------------------------------------
# Health Endpoint Tests
# ---------------------------------------------------------------------------

def test_health_returns_ok():
    """Health endpoint returns ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "market-lens-api"


def test_health_includes_versions():
    """Health endpoint includes protocol and constants versions."""
    response = client.get("/health")
    data = response.json()
    assert data["protocol_version"] == PROTOCOL_VERSION
    assert data["constants_version"] == CONSTANTS_VERSION


# ---------------------------------------------------------------------------
# Version Endpoint Tests
# ---------------------------------------------------------------------------

def test_version_returns_all_fields():
    """Version endpoint returns all required fields."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    
    required_fields = [
        "protocol_version",
        "constants_version",
        "engine_version",
        "service_mode",
        "active_profile_default",
        "psl_version",
    ]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"


def test_version_protocol_values():
    """Version endpoint returns correct protocol version."""
    response = client.get("/version")
    data = response.json()
    assert data["protocol_version"] == "0.6.0"
    assert data["constants_version"] == "0.6.0"


# ---------------------------------------------------------------------------
# Evaluate Endpoint Tests
# ---------------------------------------------------------------------------

def test_evaluate_minimal_valid_batch():
    """Evaluate endpoint accepts minimal valid batch."""
    payload = {
        "observations": [
            {
                "source_url": "https://shop.example.com/product/1",
                "merchant_id": "test_merchant",
                "price": 100.0,
                "currency": "usd",
                "region": "us",
                "timestamp": 1699900000,
                "product_identity_layer": {
                    "brand": "TestBrand",
                    "model": "TestModel",
                    "sku": "SKU001",
                    "condition": "new",
                    "bundle_flag": "false",
                    "warranty_type": "standard",
                    "region_variant": "",
                    "storage_or_size": "256gb",
                    "release_year": "2025",
                },
            },
        ],
        "current_time_utc": 1700000000,
        "applied_profile": "BASE",
    }
    
    response = client.post("/v1/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert data["protocol_version"] == "0.6.0"
    assert data["constants_version"] == "0.6.0"
    assert data["applied_profile"] == "BASE"
    assert "result" in data


def test_evaluate_all_invalid_batch():
    """Evaluate endpoint handles all-invalid batch gracefully."""
    payload = {
        "observations": [
            {
                "source_url": "not-a-url",
                "merchant_id": "test",
                "price": -10.0,  # Invalid: negative price
                "currency": "usd",
                "region": "us",
                "timestamp": 1699900000,
                "product_identity_layer": {
                    "brand": "Test",
                    "model": "Test",
                    "sku": "Test",
                    "condition": "new",
                    "bundle_flag": "",
                    "warranty_type": "",
                    "region_variant": "",
                    "storage_or_size": "",
                    "release_year": "",
                },
            },
        ],
        "current_time_utc": 1700000000,
        "applied_profile": "BASE",
    }
    
    response = client.post("/v1/evaluate", json=payload)
    # Should return 422 for invalid price (Pydantic validation)
    assert response.status_code == 422


def test_evaluate_deterministic_repeated_request():
    """Same request returns identical deterministic output."""
    payload = {
        "observations": [
            {
                "source_url": "https://shop1.com/p",
                "merchant_id": "m1",
                "price": 50.0,
                "currency": "usd",
                "region": "us",
                "timestamp": 1699900000,
                "product_identity_layer": {
                    "brand": "B1",
                    "model": "M1",
                    "sku": "S1",
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
                "price": 52.0,
                "currency": "usd",
                "region": "us",
                "timestamp": 1699910000,
                "product_identity_layer": {
                    "brand": "B1",
                    "model": "M1",
                    "sku": "S1",
                    "condition": "new",
                    "bundle_flag": "",
                    "warranty_type": "",
                    "region_variant": "",
                    "storage_or_size": "",
                    "release_year": "2025",
                },
            },
        ],
        "current_time_utc": 1700000000,
        "applied_profile": "BASE",
    }
    
    response1 = client.post("/v1/evaluate", json=payload)
    response2 = client.post("/v1/evaluate", json=payload)
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json() == response2.json()


def test_evaluate_explicit_profile_handling():
    """Evaluate respects explicit profile selection."""
    payload = {
        "observations": [
            {
                "source_url": "https://shop.example.com/product/1",
                "merchant_id": "test_merchant",
                "price": 100.0,
                "currency": "usd",
                "region": "us",
                "timestamp": 1699900000,
                "product_identity_layer": {
                    "brand": "TestBrand",
                    "model": "TestModel",
                    "sku": "SKU001",
                    "condition": "new",
                    "bundle_flag": "false",
                    "warranty_type": "standard",
                    "region_variant": "",
                    "storage_or_size": "256gb",
                    "release_year": "2025",
                },
            },
        ],
        "current_time_utc": 1700000000,
        "applied_profile": "HARDENED",
    }
    
    response = client.post("/v1/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["applied_profile"] == "HARDENED"


def test_evaluate_response_envelope_structure():
    """Evaluate response has correct envelope structure."""
    payload = {
        "observations": [],
        "current_time_utc": 1700000000,
        "applied_profile": "BASE",
    }
    
    response = client.post("/v1/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Check envelope fields
    assert "status" in data
    assert "protocol_version" in data
    assert "constants_version" in data
    assert "applied_profile" in data
    assert "accepted_count" in data
    assert "rejected_count" in data
    assert "rejection_reasons_summary" in data
    assert "result" in data
    
    # Check result fields
    result = data["result"]
    assert "identity_scope_level" in result
    assert "P_ref" in result
    assert "MAD" in result
    assert "CS" in result
    assert "N_eff" in result
    assert "cold_start_flag" in result
    assert "insufficient_data_flag" in result
    assert "integrity_status" in result


# ---------------------------------------------------------------------------
# Ingest Endpoint Tests
# ---------------------------------------------------------------------------

def test_ingest_creates_job(tmp_path, monkeypatch):
    """Ingest endpoint creates queue job."""
    # Use temp directory for queue
    monkeypatch.setenv("MARKET_LENS_QUEUE_DIR", str(tmp_path))
    
    # Reset cached config
    from service.runtime import reset_runtime_config
    from api.deps import get_config
    reset_runtime_config()
    get_config.cache_clear()
    
    payload = {
        "observations": [{"test": "data"}],
        "current_time_utc": 1700000000,
        "applied_profile": "BASE",
    }
    
    response = client.post("/v1/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert "job_id" in data
    assert "accepted_timestamp" in data
    assert data["observations_count"] == 1
    
    # Verify job file exists
    pending_dir = tmp_path / "pending"
    job_files = list(pending_dir.glob("*.json"))
    assert len(job_files) == 1
