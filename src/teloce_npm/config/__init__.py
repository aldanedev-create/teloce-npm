"""
Configuration handling for Teloce-NPM.
"""

from .defaults import DEFAULT_CONFIG
from .loader import load_config
from .schema import validate_config

__all__ = [
    "DEFAULT_CONFIG",
    "load_config",
    "validate_config",
]
