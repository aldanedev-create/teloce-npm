"""
Custom exceptions for Teloce-NPM.
"""

class TeloceNpmError(Exception):
    """Base exception for all Teloce-NPM errors."""
    pass

class ConfigError(TeloceNpmError):
    """Raised when the configuration file is invalid or missing."""
    pass

class RegistryError(TeloceNpmError):
    """Raised when there is an issue communicating with the npm registry."""
    pass

class SecurityError(TeloceNpmError):
    """
    Raised when a security check fails.
    Examples: SHA-512 integrity mismatch, malware detected, blocked install scripts.
    """
    pass

class LockfileMismatch(TeloceNpmError):
    """Raised when the lockfile does not match the installed packages or integrity hashes."""
    pass

class PackageNotFoundError(TeloceNpmError):
    """Raised when a requested package or version cannot be found in the registry."""
    pass