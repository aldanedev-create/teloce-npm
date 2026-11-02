"""
Lockfile verification for Teloce-NPM.

Answers the question: "Does the current project state match what
the lockfile says it should be?"
"""

from typing import Any

from teloce_npm.cache import CacheManager
from teloce_npm.utils.errors import LockfileMismatch
from teloce_npm.utils.hashing import verify_file_integrity

from .manager import LockfileManager


class LockfileVerifier:
    """Verifies lockfile consistency against the local cache and registry."""

    def __init__(self, lockfile_manager: LockfileManager, cache_manager: CacheManager):
        self.lockfile = lockfile_manager
        self.cache = cache_manager

    # ------------------------------------------------------------------
    # Verification against cache
    # ------------------------------------------------------------------
    def verify_against_cache(self) -> dict[str, Any]:
        """
        Verify that every package in the lockfile is present in the cache
        and that its cached tarball hash matches the locked integrity hash.

        Returns:
            A dict with:
                - 'ok': bool
                - 'missing': list of packages missing from cache
                - 'corrupted': list of packages whose hash doesn't match
                - 'extra': list of packages in cache but not in lockfile
        """
        lockfile_packages = self.lockfile.load()["packages"]
        result: dict[str, Any] = {
            "ok": True,
            "missing": [],
            "corrupted": [],
            "extra": [],
        }

        # 1. Check every locked package is in the cache
        for pkg_name, entry in lockfile_packages.items():
            version = entry["version"]
            expected_integrity = entry["integrity"]

            if not self.cache.storage.exists(pkg_name, version):
                result["missing"].append(f"{pkg_name}@{version}")
                result["ok"] = False
                continue

            # Verify the cached tarball hash matches the lockfile
            if self.cache.storage.has_tarball(pkg_name, version):
                try:
                    verify_file_integrity(
                        self.cache.storage.tarball_path(pkg_name, version),
                        expected_integrity,
                    )
                except Exception:
                    result["corrupted"].append(f"{pkg_name}@{version}")
                    result["ok"] = False

        # 2. Check for packages in cache that are not in lockfile
        cached = self.cache.list_cached()
        for cached_pkg in cached:
            if cached_pkg["name"] not in lockfile_packages:
                result["extra"].append(f"{cached_pkg['name']}@{cached_pkg['version']}")

        return result

    # ------------------------------------------------------------------
    # Verification against expected versions
    # ------------------------------------------------------------------
    def verify_versions(
        self,
        expected: dict[str, str],
    ) -> None:
        """
        Verify that the lockfile versions match the expected versions.

        Args:
            expected: A dict of {package_name: version} representing
                      what the .vel files currently require.

        Raises:
            LockfileMismatch: If any package version differs or is missing.
        """
        locked = self.lockfile.list_packages()
        errors = []

        for pkg_name, expected_version in expected.items():
            if pkg_name not in locked:
                errors.append(
                    f"Package '{pkg_name}' is required by .vel but missing from lockfile."
                )
            elif locked[pkg_name] != expected_version:
                errors.append(
                    f"Package '{pkg_name}' lockfile version ({locked[pkg_name]}) "
                    f"does not match the required version ({expected_version})."
                )

        if errors:
            raise LockfileMismatch(
                "Lockfile does not match project requirements:\n  - " + "\n  - ".join(errors)
            )

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def is_valid(self) -> bool:
        """
        Quick check: does the lockfile exist and pass cache verification?
        """
        if not self.lockfile.exists():
            return False
        result = self.verify_against_cache()
        return bool(result["ok"])

    def report(self) -> str:
        """
        Generate a human-readable report for `teloce-npm doctor`.

        Returns:
            A multi-line string describing the state of the lockfile and cache.
        """
        result = self.verify_against_cache()
        lines = ["Lockfile verification report:"]

        if not self.lockfile.exists():
            lines.append("  Lockfile: NOT FOUND")
            return "\n".join(lines)

        lines.append(f"  Lockfile: {self.lockfile.path}")
        lines.append(f"  Packages locked: {len(self.lockfile.list_packages())}")

        if result["ok"]:
            lines.append("  Status: OK (all packages present and verified)")
        else:
            if result["missing"]:
                lines.append(f"  Missing from cache ({len(result['missing'])}):")
                for pkg in result["missing"]:
                    lines.append(f"    - {pkg}")
            if result["corrupted"]:
                lines.append(f"  Corrupted ({len(result['corrupted'])}):")
                for pkg in result["corrupted"]:
                    lines.append(f"    - {pkg}")
            if result["extra"]:
                lines.append(f"  Extra in cache ({len(result['extra'])}):")
                for pkg in result["extra"]:
                    lines.append(f"    - {pkg}")

        return "\n".join(lines)
