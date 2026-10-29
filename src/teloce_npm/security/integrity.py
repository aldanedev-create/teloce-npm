"""
SHA-512 integrity verification for Teloce-NPM.
"""

from pathlib import Path

from teloce_npm.utils.hashing import (
    compute_file_sha512,
    verify_file_integrity,
    verify_integrity,
)
from teloce_npm.utils.errors import SecurityError
from teloce_npm.utils.logging import logger


class IntegrityVerifier:
    """
    Verifies package integrity against registry-provided SHA-512 hashes.
    """

    def verify_tarball(self, tarball_path: Path, expected_integrity: str) -> bool:
        """
        Verify a downloaded tarball against its expected SHA-512 hash.
        
        Args:
            tarball_path: Path to the downloaded .tgz file.
            expected_integrity: The hash from the npm registry (e.g., 'sha512-...').
            
        Returns:
            True if the hash matches.
            
        Raises:
            SecurityError: If the hash does not match.
        """
        logger.debug(f"Verifying integrity of {tarball_path.name}")
        
        try:
            return verify_file_integrity(tarball_path, expected_integrity)
        except SecurityError as e:
            logger.error(f"Integrity check failed for {tarball_path.name}")
            raise e

    def verify_bytes(self, data: bytes, expected_integrity: str) -> bool:
        """
        Verify raw bytes against an expected SHA-512 hash.
        """
        return verify_integrity(data, expected_integrity)

    def compute(self, tarball_path: Path) -> str:
        """
        Compute the SHA-512 hash of a file in npm's SRI format.
        """
        return compute_file_sha512(tarball_path)