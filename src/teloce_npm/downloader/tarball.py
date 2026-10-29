"""
Download npm tarballs securely and verify their integrity.
"""

import hashlib
import base64
from pathlib import Path
import requests

from teloce_npm.utils.errors import RegistryError, SecurityError
from teloce_npm.utils.logging import logger
from teloce_npm.utils.file_io import ensure_dir

def download_tarball(
    tarball_url: str, 
    dest_path: Path, 
    expected_integrity: str
) -> Path:
    """
    Download a tarball from the registry and verify its SHA-512 integrity on the fly.
    
    Args:
        tarball_url: The URL of the .tgz file.
        dest_path: The local path to save the downloaded file.
        expected_integrity: The expected SHA-512 hash from the registry (e.g., 'sha512-...').
        
    Returns:
        The path to the downloaded and verified tarball.
        
    Raises:
        RegistryError: If the download fails.
        SecurityError: If the integrity check fails.
    """
    ensure_dir(dest_path.parent)
    
    logger.debug(f"Downloading {tarball_url} to {dest_path}")
    
    # Initialize the SHA-512 hasher
    hasher = hashlib.sha512()

    try:
        # Stream the download to avoid loading the whole file into memory
        with requests.get(tarball_url, stream=True, timeout=30) as response:
            response.raise_for_status()
            
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        hasher.update(chunk)

        # Compute the final SRI hash format
        digest = hasher.digest()
        b64_digest = base64.b64encode(digest).decode("utf-8")
        computed_integrity = f"sha512-{b64_digest}"

        # Verify the integrity
        if computed_integrity != expected_integrity:
            # Delete the corrupted/malicious file immediately
            if dest_path.exists():
                dest_path.unlink()
                
            raise SecurityError(
                f"Integrity check failed for {tarball_url}\n"
                f"Expected: {expected_integrity}\n"
                f"Computed: {computed_integrity}"
            )

        logger.debug(f"Successfully downloaded and verified {dest_path.name}")
        return dest_path

    except requests.exceptions.RequestException as e:
        # Clean up partial download on failure
        if dest_path.exists():
            dest_path.unlink()
        raise RegistryError(f"Failed to download {tarball_url}: {e}")