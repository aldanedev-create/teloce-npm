"""
npm registry client and version resolution for Teloce-NPM.
"""

from .client import RegistryClient
from .metadata import extract_version_data
from .version_resolver import resolve_version

__all__ = [
    "RegistryClient",
    "extract_version_data",
    "resolve_version",
]
