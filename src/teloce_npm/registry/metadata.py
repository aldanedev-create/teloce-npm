"""
Parse and extract data from raw npm registry metadata.
"""

from typing import Dict, Any, List
from teloce_npm.utils.errors import PackageNotFoundError

def extract_version_data(raw_metadata: Dict[str, Any], version: str) -> Dict[str, Any]:
    """
    Extract the critical data for a specific version of a package.
    
    Args:
        raw_metadata: The full JSON response from the registry.
        version: The specific version to extract (e.g., '4.17.21').
        
    Returns:
        A dictionary containing tarball_url, integrity, and dependencies.
    """
    versions = raw_metadata.get("versions", {})
    version_data = versions.get(version)

    if not version_data:
        raise PackageNotFoundError(
            f"Version '{version}' not found for package '{raw_metadata.get('name')}'."
        )

    dist = version_data.get("dist", {})
    
    # We strictly require the tarball URL and integrity hash
    tarball_url = dist.get("tarball")
    integrity = dist.get("integrity")

    if not tarball_url or not integrity:
        raise ValueError(f"Missing tarball or integrity hash for {raw_metadata.get('name')}@{version}")

    return {
        "name": raw_metadata.get("name"),
        "version": version,
        "description": version_data.get("description", ""),
        "tarball_url": tarball_url,
        "integrity": integrity,
        "dependencies": version_data.get("dependencies", {}),
        "scripts": version_data.get("scripts", {}) # Used by security scanner to block install scripts
    }