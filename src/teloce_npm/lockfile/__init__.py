"""
Lockfile management for Teloce-NPM.

Records exact versions and integrity hashes for reproducible builds.
"""

from .manager import LOCKFILE_FILENAME, LockfileManager
from .schema import (
    LOCKFILE_VERSION,
    empty_lockfile,
    get_package_versions,
    make_package_entry,
    validate_lockfile,
)
from .verifier import LockfileVerifier

__all__ = [
    "LOCKFILE_FILENAME",
    "LOCKFILE_VERSION",
    "LockfileManager",
    "LockfileVerifier",
    "empty_lockfile",
    "get_package_versions",
    "make_package_entry",
    "validate_lockfile",
]
