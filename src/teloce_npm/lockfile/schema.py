"""
Lockfile schema and validation for Teloce-NPM.

The lockfile (`teloce-npm.lock`) records the exact version, integrity hash,
and source URL for every installed package. It is what makes builds reproducible.

Example:

    {
      "lockfile_version": "1.0.0",
      "generated_at": "2025-10-29T10:30:00Z",
      "packages": {
        "apple": {
          "version": "1.2.3",
          "resolved": "https://registry.npmjs.org/apple/-/apple-1.2.3.tgz",
          "integrity": "sha512-abc123...",
          "dependencies": {
            "lodash": "^4.17.21"
          },
          "wrapped": "apple.js",
          "size": 10240,
          "scanned_at": "2025-10-29T10:30:00Z",
          "scan_result": "clean"
        }
      }
    }
"""

from datetime import datetime, timezone
from typing import Dict, Any, List

from teloce_npm.utils.errors import ConfigError


LOCKFILE_VERSION = "1.0.0"

# Required keys for each package entry
REQUIRED_PACKAGE_KEYS = {
    "version",
    "resolved",
    "integrity",
    "wrapped",
    "size",
}


def empty_lockfile() -> Dict[str, Any]:
    """Return an empty but valid lockfile structure."""
    return {
        "lockfile_version": LOCKFILE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "packages": {},
    }


def make_package_entry(
    version: str,
    resolved_url: str,
    integrity: str,
    wrapped_filename: str,
    size: int,
    dependencies: Dict[str, str] = None,
    scan_result: str = "clean",
) -> Dict[str, Any]:
    """
    Build a single package entry for the lockfile.

    Args:
        version: The exact version (e.g., "4.17.21").
        resolved_url: The tarball URL from the registry.
        integrity: The SHA-512 hash in npm's SRI format.
        wrapped_filename: The name of the wrapped output file (e.g., "lodash.js").
        size: Size of the wrapped file in bytes.
        dependencies: Package dependencies from package.json.
        scan_result: The result of the malware scan ("clean" or "warnings").

    Returns:
        A dict representing the package entry.
    """
    return {
        "version": version,
        "resolved": resolved_url,
        "integrity": integrity,
        "dependencies": dependencies or {},
        "wrapped": wrapped_filename,
        "size": size,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "scan_result": scan_result,
    }


def validate_lockfile(lockfile: Dict[str, Any]) -> None:
    """
    Validate a lockfile structure.

    Raises:
        ConfigError: If the lockfile is malformed.
    """
    if not isinstance(lockfile, dict):
        raise ConfigError("Lockfile must be a JSON object.")

    if "lockfile_version" not in lockfile:
        raise ConfigError("Lockfile is missing 'lockfile_version'.")

    if lockfile["lockfile_version"] != LOCKFILE_VERSION:
        raise ConfigError(
            f"Unsupported lockfile version: {lockfile['lockfile_version']}. "
            f"Expected: {LOCKFILE_VERSION}. "
            f"Run `teloce-npm install` to regenerate."
        )

    if "packages" not in lockfile or not isinstance(lockfile["packages"], dict):
        raise ConfigError("Lockfile is missing a valid 'packages' object.")

    for pkg_name, pkg_entry in lockfile["packages"].items():
        if not isinstance(pkg_entry, dict):
            raise ConfigError(f"Lockfile entry for '{pkg_name}' must be an object.")

        missing = REQUIRED_PACKAGE_KEYS - set(pkg_entry.keys())
        if missing:
            raise ConfigError(
                f"Lockfile entry for '{pkg_name}' is missing required keys: "
                f"{', '.join(sorted(missing))}"
            )

        # Basic type checks
        if not isinstance(pkg_entry["size"], int):
            raise ConfigError(f"Lockfile entry '{pkg_name}.size' must be an integer.")
        if not pkg_entry["integrity"].startswith("sha512-"):
            raise ConfigError(
                f"Lockfile entry '{pkg_name}.integrity' must be a SHA-512 hash."
            )


def get_package_versions(lockfile: Dict[str, Any]) -> Dict[str, str]:
    """Extract a simple {name: version} mapping from a lockfile."""
    return {
        name: entry["version"]
        for name, entry in lockfile.get("packages", {}).items()
    }