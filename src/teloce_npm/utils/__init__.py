"""
Shared utilities for Teloce-NPM.
"""

from .errors import (
    ConfigError,
    LockfileMismatch,
    PackageNotFoundError,
    RegistryError,
    SecurityError,
    TeloceNpmError,
)
from .file_io import (
    ensure_dir,
    read_file,
    write_file_atomic,
)
from .hashing import (
    compute_file_sha512,
    compute_sha512,
    verify_file_integrity,
    verify_integrity,
)
from .logging import get_logger, logger

__all__ = [
    "ConfigError",
    "LockfileMismatch",
    "PackageNotFoundError",
    "RegistryError",
    "SecurityError",
    # Errors
    "TeloceNpmError",
    "compute_file_sha512",
    # Hashing
    "compute_sha512",
    "ensure_dir",
    # Logging
    "get_logger",
    "logger",
    # File I/O
    "read_file",
    "verify_file_integrity",
    "verify_integrity",
    "write_file_atomic",
]
