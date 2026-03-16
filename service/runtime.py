"""
DKP-PTL-REG v0.6 — Runtime Configuration

Centralized runtime configuration with deterministic defaults.
All configuration sourced from environment variables.
"""

import os
from dataclasses import dataclass
from typing import Literal

from engine.src.constants import PROTOCOL_VERSION, CONSTANTS_VERSION


ProfileType = Literal["BASE", "HARDENED"]

_VALID_PROFILES = {"BASE", "HARDENED"}


@dataclass(frozen=True)
class RuntimeConfig:
    """Immutable runtime configuration."""
    
    profile: ProfileType
    queue_dir: str
    poll_interval: int
    service_mode: str
    protocol_version: str
    constants_version: str


def _get_env_str(key: str, default: str) -> str:
    """Get string from environment with default."""
    return os.environ.get(key, default)


def _get_env_int(key: str, default: int) -> int:
    """Get integer from environment with default."""
    val = os.environ.get(key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default


def load_runtime_config() -> RuntimeConfig:
    """
    Load runtime configuration from environment variables.
    
    Environment variables:
    - MARKET_LENS_PROFILE: BASE or HARDENED (default: BASE)
    - MARKET_LENS_QUEUE_DIR: Queue directory path (default: ./var/queue)
    - MARKET_LENS_POLL_INTERVAL: Worker poll interval seconds (default: 5)
    - MARKET_LENS_SERVICE_MODE: Service mode string (default: local)
    """
    profile_str = _get_env_str("MARKET_LENS_PROFILE", "BASE").upper()
    
    if profile_str not in _VALID_PROFILES:
        raise ValueError(
            f"Invalid MARKET_LENS_PROFILE: {profile_str!r}. "
            f"Must be one of: {sorted(_VALID_PROFILES)}"
        )
    
    return RuntimeConfig(
        profile=profile_str,  # type: ignore
        queue_dir=_get_env_str("MARKET_LENS_QUEUE_DIR", "./var/queue"),
        poll_interval=_get_env_int("MARKET_LENS_POLL_INTERVAL", 5),
        service_mode=_get_env_str("MARKET_LENS_SERVICE_MODE", "local"),
        protocol_version=PROTOCOL_VERSION,
        constants_version=CONSTANTS_VERSION,
    )


# Default configuration instance
_default_config: RuntimeConfig | None = None


def get_runtime_config() -> RuntimeConfig:
    """Get or create default runtime configuration."""
    global _default_config
    if _default_config is None:
        _default_config = load_runtime_config()
    return _default_config


def reset_runtime_config() -> None:
    """Reset configuration (for testing)."""
    global _default_config
    _default_config = None
