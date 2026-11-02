"""
Lockfile CRUD operations for Teloce-NPM.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, cast

from teloce_npm.utils.errors import ConfigError
from teloce_npm.utils.file_io import read_file, write_file_atomic
from teloce_npm.utils.logging import logger

from .schema import (
    empty_lockfile,
    get_package_versions,
    make_package_entry,
    validate_lockfile,
)

LOCKFILE_FILENAME = "teloce-npm.lock"


class LockfileManager:
    """Manages reading, writing, and updating `teloce-npm.lock`."""

    def __init__(self, project_root: Path):
        self.path = project_root / LOCKFILE_FILENAME
        self._data: Optional[dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------
    def load(self) -> dict[str, Any]:
        """
        Load the lockfile from disk.

        Returns:
            The lockfile dictionary. If the file doesn't exist, returns an empty lockfile.
        """
        if self._data is not None:
            return self._data

        if not self.path.exists():
            logger.debug(f"No lockfile found at {self.path}, starting fresh.")
            self._data = empty_lockfile()
            return self._data

        try:
            raw = read_file(self.path)
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in {self.path}: {e}") from e

        validate_lockfile(data)
        self._data = data
        return self._data

    def save(self) -> None:
        """Persist the in-memory lockfile to disk."""
        if self._data is None:
            self.load()
        assert self._data is not None

        # Refresh the timestamp
        self._data["generated_at"] = datetime.now(timezone.utc).isoformat()

        # Write atomically
        write_file_atomic(self.path, json.dumps(self._data, indent=2))
        logger.debug(f"Saved lockfile to {self.path}")

    def exists(self) -> bool:
        """Return True if the lockfile exists on disk."""
        return self.path.exists()

    # ------------------------------------------------------------------
    # Package operations
    # ------------------------------------------------------------------
    def add_package(
        self,
        package_name: str,
        version: str,
        resolved_url: str,
        integrity: str,
        wrapped_filename: str,
        size: int,
        dependencies: Optional[dict[str, str]] = None,
        workers: Optional[dict[str, str]] = None,
        scan_result: str = "clean",
    ) -> None:
        """Add or update a package entry in the lockfile."""
        data = self.load()

        entry = make_package_entry(
            version=version,
            resolved_url=resolved_url,
            integrity=integrity,
            wrapped_filename=wrapped_filename,
            size=size,
            dependencies=dependencies,
            workers=workers,
            scan_result=scan_result,
        )

        data["packages"][package_name] = entry
        logger.debug(f"Added {package_name}@{version} to lockfile")

    def remove_package(self, package_name: str) -> bool:
        """
        Remove a package from the lockfile.

        Returns:
            True if the package was present and removed.
        """
        data = self.load()
        if package_name in data["packages"]:
            del data["packages"][package_name]
            logger.debug(f"Removed {package_name} from lockfile")
            return True
        return False

    def get_package(self, package_name: str) -> Optional[dict[str, Any]]:
        """Return the lockfile entry for a package, or None if absent."""
        return cast(Optional[dict[str, Any]], self.load()["packages"].get(package_name))

    def has_package(self, package_name: str) -> bool:
        """Return True if the package is in the lockfile."""
        return package_name in self.load()["packages"]

    def get_package_version(self, package_name: str) -> Optional[str]:
        """Return the locked version of a package, or None."""
        entry = self.get_package(package_name)
        return entry["version"] if entry else None

    def get_package_integrity(self, package_name: str) -> Optional[str]:
        """Return the locked integrity hash of a package, or None."""
        entry = self.get_package(package_name)
        return entry["integrity"] if entry else None

    def list_packages(self) -> dict[str, str]:
        """Return {package_name: version} for all locked packages."""
        return get_package_versions(self.load())

    def clear(self) -> None:
        """Clear all packages from the lockfile (used by `teloce-npm clean`)."""
        self._data = empty_lockfile()
        logger.debug("Cleared lockfile")

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------
    def summary(self) -> dict[str, Any]:
        """Return a summary of the lockfile (for `teloce-npm list` and `doctor`)."""
        data = self.load()
        return {
            "path": str(self.path),
            "exists": self.path.exists(),
            "lockfile_version": data["lockfile_version"],
            "generated_at": data["generated_at"],
            "package_count": len(data["packages"]),
            "packages": {
                name: {
                    "version": entry["version"],
                    "size": entry["size"],
                    "scan_result": entry.get("scan_result", "unknown"),
                }
                for name, entry in data["packages"].items()
            },
        }
