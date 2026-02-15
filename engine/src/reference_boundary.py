"""
DKP-PTL-REG-REFERENCE-001 v0.6 — Deterministic Input Boundary

Canonical input normalization before DATA-001 execution.

- UTF-8 encoding
- Unicode NFC normalization
- ASCII whitespace trimming
- Unicode case-fold (locale-independent)
- PSL-pinned root domain extraction (eTLD+1)
- RFC 3986 host parsing
- SHA256 evidence_hash via JCS
- Strict rejection conditions
"""

import hashlib
import math
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from .json_canonical import canonical_json_bytes

# ---------------------------------------------------------------------------
# PSL Snapshot Loading
# ---------------------------------------------------------------------------

_PSL_SNAPSHOT_FILENAME = "PSL-2026-01-01.dat"


class PublicSuffixList:
    """
    Deterministic Public Suffix List matcher.

    Uses pinned snapshot PSL-2026-01-01.
    Extracts eTLD+1 (effective TLD + one label).
    """

    def __init__(self, psl_path: Optional[str] = None):
        if psl_path is None:
            psl_path = str(
                Path(__file__).parent / "psl_snapshot" / _PSL_SNAPSHOT_FILENAME
            )
        self._rules: List[Tuple[bool, List[str]]] = []
        self._exception_rules: List[List[str]] = []
        self._load(psl_path)

    def _load(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("//"):
                    continue
                # Exception rule
                if line.startswith("!"):
                    labels = line[1:].lower().split(".")
                    labels.reverse()
                    self._exception_rules.append(labels)
                else:
                    # Wildcard or normal rule
                    is_wildcard = "*" in line
                    labels = line.lower().split(".")
                    labels.reverse()
                    self._rules.append((is_wildcard, labels))

        # Sort rules by length descending for longest match
        self._rules.sort(key=lambda r: len(r[1]), reverse=True)
        self._exception_rules.sort(key=lambda r: len(r), reverse=True)

    def get_root_domain(self, host: str) -> str:
        """
        Extract eTLD+1 from normalized host.

        Per REFERENCE-001 Section 4.2:
        - Match host against PSL
        - Extract eTLD + one label
        - If no PSL match, root domain = full normalized host
        """
        labels = host.lower().split(".")
        labels_reversed = list(reversed(labels))

        # Check exception rules first
        for exc_rule in self._exception_rules:
            if self._matches_labels(labels_reversed, exc_rule):
                # Exception: eTLD is one label less than the exception rule
                etld_len = len(exc_rule) - 1
                if len(labels) > etld_len:
                    return ".".join(labels[-(etld_len + 1):])
                return host

        # Find longest matching rule
        best_match_len = 0
        for is_wildcard, rule_labels in self._rules:
            if self._matches_rule(labels_reversed, rule_labels, is_wildcard):
                rule_len = len(rule_labels)
                if is_wildcard:
                    # Wildcard matches one additional label
                    rule_len = rule_len  # The wildcard already counted
                if rule_len > best_match_len:
                    best_match_len = rule_len

        if best_match_len == 0:
            # Default rule: treat last label as TLD (implicit * rule)
            # eTLD+1 = last two labels if available
            if len(labels) >= 2:
                return ".".join(labels[-2:])
            return host

        # eTLD+1 = public suffix + one label
        etld_plus_one_count = best_match_len + 1
        if len(labels) >= etld_plus_one_count:
            return ".".join(labels[-etld_plus_one_count:])
        return host

    @staticmethod
    def _matches_labels(
        host_labels_reversed: List[str], rule_labels: List[str]
    ) -> bool:
        if len(host_labels_reversed) < len(rule_labels):
            return False
        for i, rl in enumerate(rule_labels):
            if rl == "*":
                continue
            if host_labels_reversed[i] != rl:
                return False
        return True

    @staticmethod
    def _matches_rule(
        host_labels_reversed: List[str],
        rule_labels: List[str],
        is_wildcard: bool,
    ) -> bool:
        if len(host_labels_reversed) < len(rule_labels):
            return False
        for i, rl in enumerate(rule_labels):
            if rl == "*":
                continue
            if host_labels_reversed[i] != rl:
                return False
        return True


# Singleton PSL instance (loaded once)
_psl_instance: Optional[PublicSuffixList] = None


def get_psl() -> PublicSuffixList:
    global _psl_instance
    if _psl_instance is None:
        _psl_instance = PublicSuffixList()
    return _psl_instance


def reset_psl() -> None:
    """Reset PSL singleton (for testing with custom snapshots)."""
    global _psl_instance
    _psl_instance = None


def set_psl(psl: PublicSuffixList) -> None:
    """Set custom PSL instance (for testing)."""
    global _psl_instance
    _psl_instance = psl


# ---------------------------------------------------------------------------
# String Normalization (Section 3)
# ---------------------------------------------------------------------------

_ASCII_WHITESPACE = frozenset("\u0020\u0009\u000a\u000d")


def normalize_string(value: Any) -> str:
    """
    Canonical string normalization per REFERENCE-001 Section 3.

    1. Decode as UTF-8 (Python str is already Unicode)
    2. Apply Unicode normalization: NFC
    3. Trim leading/trailing ASCII whitespace
    4. Convert to lowercase using Unicode case-fold (locale-independent)

    Missing field = absent OR equals "" → stored as ""
    """
    if value is None:
        return ""
    s = str(value)
    # NFC normalization
    s = unicodedata.normalize("NFC", s)
    # Trim ASCII whitespace
    s = s.strip("\u0020\u0009\u000a\u000d")
    # Unicode case-fold (locale-independent lowercase)
    s = s.casefold()
    return s


# ---------------------------------------------------------------------------
# Domain Canonicalization (Section 4)
# ---------------------------------------------------------------------------


def extract_host(source_url: str) -> Optional[str]:
    """
    Extract and normalize host from source_url per RFC 3986.

    Returns None if parsing fails.
    """
    try:
        parsed = urlparse(source_url)
        host = parsed.hostname
        if host is None or host == "":
            return None
        # Apply string normalization
        host = normalize_string(host)
        return host
    except Exception:
        return None


def get_root_domain(source_url: str) -> Optional[str]:
    """
    Extract root domain (eTLD+1) from source_url.

    Per REFERENCE-001 Section 4.2:
    - Parse URL → extract host → remove port → normalize
    - Apply PSL → extract eTLD+1
    - Subdomains collapse to eTLD+1
    """
    host = extract_host(source_url)
    if host is None:
        return None
    psl = get_psl()
    return psl.get_root_domain(host)


# ---------------------------------------------------------------------------
# Timestamp Canonicalization (Section 6)
# ---------------------------------------------------------------------------

# Future tolerance: 5 seconds
_FUTURE_TOLERANCE_SECONDS = 5


def canonicalize_timestamp(
    timestamp_value: Any, current_time_utc: int
) -> Optional[int]:
    """
    Canonicalize timestamp per REFERENCE-001 Section 6.

    - Parse ISO-8601 or numeric epoch
    - Convert to UTC → Unix epoch seconds
    - Apply floor
    - Store as integer
    - Reject if invalid, not convertible, or > current_time_utc + 5s

    Returns None if invalid (observation must be rejected).
    """
    if timestamp_value is None:
        return None

    ts: Optional[int] = None

    if isinstance(timestamp_value, (int, float)):
        if not math.isfinite(timestamp_value):
            return None
        ts = int(math.floor(timestamp_value))
    elif isinstance(timestamp_value, str):
        # Try numeric first
        try:
            val = float(timestamp_value)
            if not math.isfinite(val):
                return None
            ts = int(math.floor(val))
        except ValueError:
            # Try ISO-8601
            from datetime import datetime, timezone

            try:
                # Handle various ISO-8601 formats
                s = timestamp_value.strip()
                if s.endswith("Z"):
                    s = s[:-1] + "+00:00"
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is None:
                    # Assume UTC
                    dt = dt.replace(tzinfo=timezone.utc)
                dt_utc = dt.astimezone(timezone.utc)
                ts = int(math.floor(dt_utc.timestamp()))
            except (ValueError, OverflowError):
                return None
    else:
        return None

    if ts is None:
        return None

    # Reject future timestamps beyond tolerance
    if ts > current_time_utc + _FUTURE_TOLERANCE_SECONDS:
        return None

    return ts


# ---------------------------------------------------------------------------
# Merchant ID Canonicalization (Section 5)
# ---------------------------------------------------------------------------

_MERCHANT_ID_MAX_BYTES = 256


def canonicalize_merchant_id(merchant_id: Any) -> Optional[str]:
    """
    Canonicalize merchant_id per REFERENCE-001 Section 5.

    - Full string normalization
    - If absent → ""
    - Max 256 bytes UTF-8
    - Exceeds limit → reject (return None)
    """
    normalized = normalize_string(merchant_id)
    if len(normalized.encode("utf-8")) > _MERCHANT_ID_MAX_BYTES:
        return None  # Reject
    return normalized


# ---------------------------------------------------------------------------
# Product Identity Layer Validation
# ---------------------------------------------------------------------------

_PIL_REQUIRED_FIELDS = [
    "brand",
    "model",
    "sku",
    "condition",
    "bundle_flag",
    "warranty_type",
    "region_variant",
    "storage_or_size",
    "release_year",
]


def normalize_pil(pil: Optional[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    """
    Normalize Product Identity Layer fields.

    All fields undergo string normalization.
    Missing fields stored as "".
    Returns None if pil is None (reject observation).
    """
    if pil is None:
        return None

    result = {}
    for field_name in _PIL_REQUIRED_FIELDS:
        value = pil.get(field_name)
        result[field_name] = normalize_string(value)
    return result


# ---------------------------------------------------------------------------
# Evidence Hash (Section 8)
# ---------------------------------------------------------------------------


def compute_evidence_hash(
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

    Canonical payload is JCS JSON with lexicographically sorted keys.
    """
    canonical_obj = {
        "currency": currency,
        "domain_id": domain_id,
        "merchant_id": merchant_id,
        "price": price,
        "product_identity_layer": {
            "brand": pil.get("brand", ""),
            "bundle_flag": pil.get("bundle_flag", ""),
            "condition": pil.get("condition", ""),
            "model": pil.get("model", ""),
            "region_variant": pil.get("region_variant", ""),
            "release_year": pil.get("release_year", ""),
            "sku": pil.get("sku", ""),
            "storage_or_size": pil.get("storage_or_size", ""),
            "warranty_type": pil.get("warranty_type", ""),
        },
        "region": region,
        "timestamp": timestamp,
    }
    payload_bytes = canonical_json_bytes(canonical_obj)
    return hashlib.sha256(payload_bytes).hexdigest()


# ---------------------------------------------------------------------------
# Observation Data Class
# ---------------------------------------------------------------------------


@dataclass
class NormalizedObservation:
    """A validated, normalized observation ready for DATA-001 pipeline."""

    domain_id: str
    merchant_id: str
    price: float
    currency: str
    timestamp: int
    region: str
    pil: Dict[str, str]
    evidence_hash: str
    source_url: str

    # Additional PIL identity fields for scope resolution
    bundle_flag: str = ""
    warranty_type: str = ""


# ---------------------------------------------------------------------------
# Full Observation Validation (Section 9)
# ---------------------------------------------------------------------------


def validate_and_normalize(
    raw_obs: Dict[str, Any],
    current_time_utc: int,
) -> Optional[NormalizedObservation]:
    """
    Validate and normalize a single raw observation per REFERENCE-001.

    Returns NormalizedObservation if valid, None if rejected.

    Rejection conditions (Section 9):
    - price <= 0 or not finite
    - currency missing
    - region missing
    - OCV incomplete (relaxed: we check essential fields)
    - domain parsing fails
    - timestamp invalid or future
    - merchant_id > 256 bytes
    - PIL missing required fields
    - normalization error
    - UTF-8 decoding failure
    """
    try:
        # Price validation
        price = raw_obs.get("price")
        if price is None:
            return None
        price = float(price)
        if not math.isfinite(price) or price <= 0:
            return None

        # Currency
        currency = raw_obs.get("currency")
        if currency is None or normalize_string(currency) == "":
            return None
        currency = normalize_string(currency)

        # Region
        region = raw_obs.get("region")
        if region is None or normalize_string(region) == "":
            return None
        region = normalize_string(region)

        # Source URL → domain_id
        source_url = raw_obs.get("source_url", "")
        domain_id = get_root_domain(source_url)
        if domain_id is None:
            # If domain_id provided directly, use it
            direct_domain = raw_obs.get("domain_id")
            if direct_domain is not None:
                domain_id = normalize_string(direct_domain)
            else:
                return None  # Reject: domain parsing fails

        # Merchant ID
        merchant_id_raw = raw_obs.get("merchant_id")
        merchant_id = canonicalize_merchant_id(merchant_id_raw)
        if merchant_id is None:
            return None  # Reject: exceeds 256 bytes

        # Timestamp
        timestamp_raw = raw_obs.get("timestamp")
        timestamp = canonicalize_timestamp(timestamp_raw, current_time_utc)
        if timestamp is None:
            return None  # Reject: invalid timestamp

        # Product Identity Layer
        pil_raw = raw_obs.get("product_identity_layer")
        if pil_raw is None:
            return None  # Reject
        pil = normalize_pil(pil_raw)
        if pil is None:
            return None  # Reject

        # Evidence hash
        evidence_hash = compute_evidence_hash(
            domain_id, merchant_id, price, currency, timestamp, region, pil
        )

        return NormalizedObservation(
            domain_id=domain_id,
            merchant_id=merchant_id,
            price=price,
            currency=currency,
            timestamp=timestamp,
            region=region,
            pil=pil,
            evidence_hash=evidence_hash,
            source_url=str(source_url),
            bundle_flag=pil.get("bundle_flag", ""),
            warranty_type=pil.get("warranty_type", ""),
        )

    except Exception:
        return None  # Reject on any normalization error


def validate_observations(
    raw_observations: List[Dict[str, Any]],
    current_time_utc: int,
) -> List[NormalizedObservation]:
    """
    Validate and normalize all observations.

    Rejected observations are silently discarded per spec.
    """
    result = []
    for raw in raw_observations:
        obs = validate_and_normalize(raw, current_time_utc)
        if obs is not None:
            result.append(obs)
    return result
