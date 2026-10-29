"""
SHA-512 hashing utilities for package integrity verification.
"""

import hashlib
import base64
from pathlib import Path
from .errors import SecurityError

def compute_sha512(data: bytes) -> str:
    """
    Compute the SHA-512 hash of the given bytes in npm's SRI format.
    
    Args:
        data: The raw bytes to hash.
        
    Returns:
        A string in the format 'sha512-<base64_encoded_hash>'.
    """
    digest = hashlib.sha512(data).digest()
    b64_digest = base64.b64encode(digest).decode("utf-8")
    return f"sha512-{b64_digest}"

def compute_file_sha512(file_path: Path) -> str:
    """
    Compute the SHA-512 hash of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        A string in the format 'sha512-<base64_encoded_hash>'.
    """
    hasher = hashlib.sha512()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large tarballs efficiently
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
            
    digest = hasher.digest()
    b64_digest = base64.b64encode(digest).decode("utf-8")
    return f"sha512-{b64_digest}"

def verify_integrity(data: bytes, expected_integrity: str) -> bool:
    """
    Verify that the computed hash matches the expected registry hash.
    
    Args:
        data: The raw bytes to verify.
        expected_integrity: The hash from the npm registry (e.g., 'sha512-...').
        
    Returns:
        True if the hashes match.
        
    Raises:
        SecurityError: If the hashes do not match.
    """
    computed = compute_sha512(data)
    if computed != expected_integrity:
        raise SecurityError(
            f"Integrity check failed!\n"
            f"Expected: {expected_integrity}\n"
            f"Computed: {computed}"
        )
    return True

def verify_file_integrity(file_path: Path, expected_integrity: str) -> bool:
    """
    Verify that the computed file hash matches the expected registry hash.
    
    Raises:
        SecurityError: If the hashes do not match.
    """
    computed = compute_file_sha512(file_path)
    if computed != expected_integrity:
        raise SecurityError(
            f"Integrity check failed for file: {file_path}\n"
            f"Expected: {expected_integrity}\n"
            f"Computed: {computed}"
        )
    return True