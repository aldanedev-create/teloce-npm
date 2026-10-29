"""
Low-level storage operations for the Teloce-NPM cache.

The cache layout is:

    <cache_dir>/
        <package_name>@<version>/
            metadata.json        # Integrity, download date, scan result
            package.tgz          # Original tarball from npm
            extracted/           # Extracted package files
                package.json
                index.js
                ...
            wrapped.js           # Browser-ready wrapped code
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from teloce_npm.utils.file_io import ensure_dir, write_file_atomic, read_file
from teloce_npm.utils.logging import logger


class CacheStorage:
    """Handles the on-disk layout of the package cache."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        ensure_dir(self.cache_dir)

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------
    def package_dir(self, package_name: str, version: str) -> Path:
        """Return the directory for a specific package version."""
        safe_name = package_name.replace("/", "__").replace("@", "_at_")
        return self.cache_dir / f"{safe_name}@{version}"

    def tarball_path(self, package_name: str, version: str) -> Path:
        return self.package_dir(package_name, version) / "package.tgz"

    def extracted_dir(self, package_name: str, version: str) -> Path:
        return self.package_dir(package_name, version) / "extracted"

    def wrapped_path(self, package_name: str, version: str) -> Path:
        return self.package_dir(package_name, version) / "wrapped.js"

    def metadata_path(self, package_name: str, version: str) -> Path:
        return self.package_dir(package_name, version) / "metadata.json"

    # ------------------------------------------------------------------
    # Existence checks
    # ------------------------------------------------------------------
    def exists(self, package_name: str, version: str) -> bool:
        """Return True if the package is cached (extracted + wrapped)."""
        return (
            self.extracted_dir(package_name, version).exists()
            and self.wrapped_path(package_name, version).exists()
            and self.metadata_path(package_name, version).exists()
        )

    def has_tarball(self, package_name: str, version: str) -> bool:
        return self.tarball_path(package_name, version).exists()

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------
    def save_metadata(
        self,
        package_name: str,
        version: str,
        metadata: Dict[str, Any],
    ) -> None:
        """Persist package metadata (integrity, download date, scan result)."""
        metadata = dict(metadata)  # don't mutate the caller's dict
        metadata.setdefault("cached_at", datetime.now(timezone.utc).isoformat())
        metadata["name"] = package_name
        metadata["version"] = version

        path = self.metadata_path(package_name, version)
        write_file_atomic(path, json.dumps(metadata, indent=2))
        logger.debug(f"Cached metadata for {package_name}@{version} at {path}")

    def save_wrapped(self, package_name: str, version: str, code: str) -> None:
        """Save the wrapped JavaScript output to the cache."""
        path = self.wrapped_path(package_name, version)
        write_file_atomic(path, code)
        logger.debug(f"Cached wrapped output for {package_name}@{version}")

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------
    def load_metadata(self, package_name: str, version: str) -> Optional[Dict[str, Any]]:
        """Load cached metadata. Returns None if not found or invalid."""
        path = self.metadata_path(package_name, version)
        if not path.exists():
            return None
        try:
            return json.loads(read_file(path))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Corrupted cache metadata for {package_name}@{version}: {e}")
            return None

    def load_wrapped(self, package_name: str, version: str) -> Optional[str]:
        """Load the wrapped JavaScript output. Returns None if not found."""
        path = self.wrapped_path(package_name, version)
        if not path.exists():
            return None
        try:
            return read_file(path)
        except OSError as e:
            logger.warning(f"Could not read cached wrapped output: {e}")
            return None

    # ------------------------------------------------------------------
    # Removal
    # ------------------------------------------------------------------
    def remove(self, package_name: str, version: str) -> bool:
        """Remove a specific package version from the cache."""
        path = self.package_dir(package_name, version)
        if path.exists():
            shutil.rmtree(path)
            logger.debug(f"Removed cache entry: {path}")
            return True
        return False

    def clear_all(self) -> int:
        """Remove all cache entries. Returns the number of entries removed."""
        if not self.cache_dir.exists():
            return 0
        count = 0
        for entry in self.cache_dir.iterdir():
            if entry.is_dir():
                shutil.rmtree(entry)
                count += 1
        logger.debug(f"Cleared {count} cache entries from {self.cache_dir}")
        return count