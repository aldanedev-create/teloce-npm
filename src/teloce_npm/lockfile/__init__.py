"""
Lockfile management for Teloce-NPM.

Records exact versions and integrity hashes for reproducible builds.
"""

from .manager import LockfileManager, LOCKFILE_FILENAME
from .verifier import LockfileVerifier
from .schema import (
    empty_lockfile,
    make_package_entry,
    validate_lockfile,
    get_package_versions,
    LOCKFILE_VERSION,
)

__all__ = [
    "LockfileManager",
    "LockfileVerifier",
    "LOCKFILE_FILENAME",
    "LOCKFILE_VERSION",
    "empty_lockfile",
    "make_package_entry",
    "validate_lockfile",
    "get_package_versions",
]