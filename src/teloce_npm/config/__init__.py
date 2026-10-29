"""
Configuration handling for Teloce-NPM.
"""

from .loader import load_config
from .defaults import DEFAULT_CONFIG
from .schema import validate_config

__all__ = [
    "load_config",
    "DEFAULT_CONFIG",
    "validate_config",
]