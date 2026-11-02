"""
Local package cache for Teloce-NPM.

Stores extracted packages and wrapped JavaScript output to avoid
re-downloading and re-wrapping on every install.
"""

from .manager import CacheManager
from .storage import CacheStorage

__all__ = [
    "CacheManager",
    "CacheStorage",
]
