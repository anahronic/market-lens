"""
JSON Canonical Serialization (JCS) per REFERENCE-001 v0.6

Deterministic JSON serialization:
- UTF-8 encoding
- Lexicographically sorted keys (recursive)
- No whitespace
- No trailing zeros in numbers
- No insignificant decimal expansion
"""

import json
import math
from typing import Any


def _canonical_number(value: float) -> str:
    """
    Serialize a number per JCS rules.

    IEEE 754 double precision representation.
    No trailing zeros. No insignificant decimal expansion.
    Integers rendered without decimal point.
    """
    if math.isnan(value) or math.isinf(value):
        raise ValueError(f"Non-finite number not allowed in JCS: {value}")

    # If value is an integer, render without decimal
    if isinstance(value, int):
        return str(value)

    if isinstance(value, float) and value == math.floor(value) and abs(value) < 2**53:
        return str(int(value))

    # Use repr for full precision, then strip trailing zeros
    # Python's repr gives enough digits to round-trip
    s = repr(value)
    if "e" in s or "E" in s:
        # Scientific notation — normalize
        return s
    if "." in s:
        s = s.rstrip("0").rstrip(".")
        if s == "-0":
            s = "0"
        return s
    return s


def _serialize_value(value: Any) -> str:
    """Serialize a single JSON value per JCS."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return _canonical_number(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        elements = [_serialize_value(item) for item in value]
        return "[" + ",".join(elements) + "]"
    if isinstance(value, dict):
        return canonical_json(value)
    raise TypeError(f"Unsupported type for JCS: {type(value)}")


def canonical_json(obj: dict) -> str:
    """
    Produce canonical JSON string per JCS specification.

    Keys sorted lexicographically (byte-order on UTF-8).
    No whitespace. Recursive.
    """
    if not isinstance(obj, dict):
        return _serialize_value(obj)

    sorted_keys = sorted(obj.keys())
    pairs = []
    for key in sorted_keys:
        k_str = json.dumps(key, ensure_ascii=False)
        v_str = _serialize_value(obj[key])
        pairs.append(f"{k_str}:{v_str}")
    return "{" + ",".join(pairs) + "}"


def canonical_json_bytes(obj: dict) -> bytes:
    """Produce canonical JSON as UTF-8 bytes."""
    return canonical_json(obj).encode("utf-8")
