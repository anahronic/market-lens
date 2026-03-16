"""
DKP-PTL-REG v0.6 — API Dependencies

Centralized dependency wiring for FastAPI application.
No global hidden state; explicit configuration loading.
"""

from functools import lru_cache
from typing import Callable, Dict, Any

from service.runtime import RuntimeConfig, get_runtime_config
from service.version_info import get_version_info
from engine.src.cli import run_engine


@lru_cache()
def get_config() -> RuntimeConfig:
    """Get runtime configuration (cached)."""
    return get_runtime_config()


def get_queue_path() -> str:
    """Get queue directory path from configuration."""
    config = get_config()
    return config.queue_dir


def get_default_profile() -> str:
    """Get default profile from configuration."""
    config = get_config()
    return config.profile


def get_engine_callable() -> Callable[[Dict[str, Any], str, int], Dict[str, Any]]:
    """
    Get engine callable for evaluation.
    
    Returns a function with signature:
        (input_data: dict, profile: str, current_time_utc: int) -> dict
    """
    return run_engine


def get_version() -> Dict[str, Any]:
    """Get version information dictionary."""
    return get_version_info()
