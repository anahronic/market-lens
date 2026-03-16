"""
DKP-PTL-REG v0.6 — Version Information

Single source of truth for version strings.
Import from engine.src.constants to avoid duplication.
"""

from engine.src.constants import PROTOCOL_VERSION, CONSTANTS_VERSION

# Service-specific version info
ENGINE_VERSION = "0.6.0"
SERVICE_NAME = "market-lens"
PSL_VERSION = "PSL-2026-01-01"


def get_version_info() -> dict:
    """Return complete version information dictionary."""
    return {
        "protocol_version": PROTOCOL_VERSION,
        "constants_version": CONSTANTS_VERSION,
        "engine_version": ENGINE_VERSION,
        "service_name": SERVICE_NAME,
        "psl_version": PSL_VERSION,
    }
