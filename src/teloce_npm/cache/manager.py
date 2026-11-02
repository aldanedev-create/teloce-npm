"""
High-level cache management for Teloce-NPM.

Provides a clean API used by the install/add commands:

    cache = CacheManager(cache_dir)
    if cache.has(package_name, version, expected_integrity):
        # Cache hit — reuse
        wrapped_code = cache.get_wrapped(package_name, version)
    else:
        # Cache miss — download, verify, extract, wrap, then:
        cache.store(package_name, version, tarball_path, extracted_dir, wrapped_code, metadata)
"""

from pathlib import Path
from typing import Any, Optional

from teloce_npm.utils.errors import SecurityError
from teloce_npm.utils.hashing import verify_file_integrity
from teloce_npm.utils.logging import logger

from .storage import CacheStorage


class CacheManager:
    """High-level cache manager."""

    def __init__(self, cache_dir: Path):
        self.storage = CacheStorage(cache_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def has(self, package_name: str, version: str, expected_integrity: str) -> bool:
        """
        Check if a package version is cached AND its tarball matches the expected hash.

        If the cached tarball's hash does not match (e.g., the registry re-published),
        the cache entry is invalidated and False is returned.

        Args:
            package_name: The package name.
            version: The specific version.
            expected_integrity: The SHA-512 hash from the registry.

        Returns:
            True if the package is cached and the hash matches.
        """
        if not self.storage.exists(package_name, version):
            return False

        # If we have a tarball, verify its hash hasn't been tampered with.
        if self.storage.has_tarball(package_name, version):
            tarball_path = self.storage.tarball_path(package_name, version)
            try:
                verify_file_integrity(tarball_path, expected_integrity)
            except SecurityError as e:
                logger.warning(
                    f"Cached tarball for {package_name}@{version} failed integrity check: {e}. "
                    f"Invalidating cache entry."
                )
                self.storage.remove(package_name, version)
                return False

        # Also check the metadata integrity for defense-in-depth
        metadata = self.storage.load_metadata(package_name, version)
        if metadata and metadata.get("integrity") != expected_integrity:
            logger.warning(
                f"Cached metadata integrity mismatch for {package_name}@{version}. "
                f"Invalidating cache entry."
            )
            self.storage.remove(package_name, version)
            return False

        return True

    def get_wrapped(self, package_name: str, version: str) -> str:
        """
        Retrieve the wrapped JavaScript output from the cache.

        Should only be called after `has()` returns True.

        Raises:
            FileNotFoundError: If the wrapped output is missing.
        """
        code = self.storage.load_wrapped(package_name, version)
        if code is None:
            raise FileNotFoundError(
                f"Wrapped output missing from cache for {package_name}@{version}"
            )
        return code

    def get_extracted_dir(self, package_name: str, version: str) -> Path:
        """Return the path to the extracted package directory."""
        return self.storage.extracted_dir(package_name, version)

    def store(
        self,
        package_name: str,
        version: str,
        extracted_dir: Path,
        wrapped_code: str,
        metadata: dict[str, Any],
    ) -> None:
        """
        Store a freshly downloaded + wrapped package in the cache.

        Args:
            package_name: The package name.
            version: The specific version.
            extracted_dir: The extracted package directory (from downloader/extractor.py).
            wrapped_code: The wrapped JavaScript output.
            metadata: Registry metadata (integrity, tarball_url, scan_result, etc.).
        """
        # 1. Move the extracted directory into the cache
        target_extracted = self.storage.extracted_dir(package_name, version)
        if target_extracted.exists():
            import shutil

            shutil.rmtree(target_extracted)
        target_extracted.parent.mkdir(parents=True, exist_ok=True)
        import shutil

        shutil.move(str(extracted_dir), str(target_extracted))

        # 2. Save metadata
        self.storage.save_metadata(package_name, version, metadata)

        # 3. Save wrapped output
        self.storage.save_wrapped(package_name, version, wrapped_code)

        logger.debug(f"Stored {package_name}@{version} in cache")

    def get_metadata(self, package_name: str, version: str) -> Optional[dict[str, Any]]:
        """Retrieve metadata for a cached package."""
        return self.storage.load_metadata(package_name, version)

    def invalidate(self, package_name: str, version: str) -> bool:
        """Explicitly remove a cache entry (used by `teloce-npm remove`)."""
        return self.storage.remove(package_name, version)

    def clear_all(self) -> int:
        """Clear all cache entries (used by `teloce-npm clean`)."""
        return self.storage.clear_all()

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------
    def list_cached(self) -> list[dict[str, Any]]:
        """
        Return a summary of all cached packages.

        Used by `teloce-npm list` and `teloce-npm doctor`.
        """
        results: list[dict[str, Any]] = []
        if not self.storage.cache_dir.exists():
            return results

        for entry in self.storage.cache_dir.iterdir():
            if not entry.is_dir():
                continue
            metadata = entry / "metadata.json"
            wrapped = entry / "wrapped.js"
            if metadata.exists() and wrapped.exists():
                try:
                    import json

                    meta = json.loads(metadata.read_text(encoding="utf-8"))
                    results.append(
                        {
                            "name": meta.get("name", entry.name.split("@")[0]),
                            "version": meta.get("version", "unknown"),
                            "size": wrapped.stat().st_size,
                            "cached_at": meta.get("cached_at", "unknown"),
                        }
                    )
                except (json.JSONDecodeError, OSError):
                    continue
        return sorted(results, key=lambda x: (x["name"], x["version"]))
