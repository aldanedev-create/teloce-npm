"""
Shared utilities for Teloce-NPM.
"""

from .errors import (
    TeloceNpmError,
    ConfigError,
    RegistryError,
    SecurityError,
    LockfileMismatch,
    PackageNotFoundError,
)
from .hashing import (
    compute_sha512,
    compute_file_sha512,
    verify_integrity,
    verify_file_integrity,
)
from .file_io import (
    read_file,
    write_file_atomic,
    ensure_dir,
)
from .logging import get_logger, logger

__all__ = [
    # Errors
    "TeloceNpmError",
    "ConfigError",
    "RegistryError",
    "SecurityError",
    "LockfileMismatch",
    "PackageNotFoundError",
    # Hashing
    "compute_sha512",
    "compute_file_sha512",
    "verify_integrity",
    "verify_file_integrity",
    # File I/O
    "read_file",
    "write_file_atomic",
    "ensure_dir",
    # Logging
    "get_logger",
    "logger",
]