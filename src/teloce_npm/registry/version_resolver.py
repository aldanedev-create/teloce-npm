"""
Resolve npm version ranges (e.g., '^1.0.0', 'latest') to specific versions.
"""

import semver
from typing import Dict, Any, List

from teloce_npm.utils.errors import PackageNotFoundError
from teloce_npm.utils.logging import logger

def resolve_version(raw_metadata: Dict[str, Any], requested_range: str) -> str:
    """
    Resolve a requested version range to the highest matching specific version.
    
    Args:
        raw_metadata: The full JSON response from the registry.
        requested_range: The version requested by the user (e.g., 'latest', '^1.0.0', '4.17.21').
        
    Returns:
        The specific version string (e.g., '4.17.21').
    """
    versions_dict = raw_metadata.get("versions", {})
    dist_tags = raw_metadata.get("dist-tags", {})
    package_name = raw_metadata.get("name", "unknown")

    # 1. Handle 'latest' or empty string
    if requested_range in ("latest", "", None):
        latest = dist_tags.get("latest")
        if not latest:
            raise PackageNotFoundError(f"No 'latest' tag found for package '{package_name}'.")
        return latest

    # 2. Handle exact match (e.g., '4.17.21')
    if requested_range in versions_dict:
        return requested_range

    # 3. Handle SemVer ranges (e.g., '^1.0.0')
    # We filter out pre-release versions (like 1.0.0-beta) unless explicitly requested
    valid_versions = []
    for v in versions_dict.keys():
        if semver.VersionInfo.isvalid(v) and not semver.VersionInfo.parse(v).prerelease:
            valid_versions.append(v)

    try:
        # Find all versions that satisfy the range
        matching_versions = [v for v in valid_versions if semver.match(v, requested_range)]
        
        if not matching_versions:
            raise PackageNotFoundError(
                f"No versions of '{package_name}' match the range '{requested_range}'."
            )

        # Return the highest matching version
        highest_version = str(max(matching_versions, key=lambda v: semver.VersionInfo.parse(v)))
        logger.debug(f"Resolved {package_name}@{requested_range} to {highest_version}")
        return highest_version

    except ValueError as e:
        raise PackageNotFoundError(f"Invalid version range '{requested_range}' for '{package_name}': {e}")