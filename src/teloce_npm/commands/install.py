"""
`teloce-npm install` — the primary build command.

Two modes:
    - `teloce-npm install`              → scan .vel + config, install everything
    - `teloce-npm install <pkg> [...]`  → install specific packages and add to config
"""

import tempfile
from pathlib import Path
from typing import List

from teloce_npm.commands import BaseCommand, parse_package_spec
from teloce_npm.scanner import scan_project
from teloce_npm.registry import extract_version_data, resolve_version
from teloce_npm.downloader import download_tarball, extract_tarball
from teloce_npm.security import (
    SecurityPolicy,
    run_security_checks,
    check_vulnerabilities,
)
from teloce_npm.wrapper import wrap_package
from teloce_npm.generator import generate_all
from teloce_npm.utils.errors import PackageNotFoundError
from teloce_npm.utils.file_io import write_file_atomic


class InstallCommand(BaseCommand):

    def execute(
        self,
        packages: List[str] = None,
        production: bool = False,
        verbose: bool = False,
        no_verify: bool = False,
    ) -> int:
        self._setup(verbose=verbose)
        print("Teloce-NPM Install")
        print("=" * 40)

        # 1. Prepare adapter
        self.adapter.prepare()

        # 2. Branch based on whether packages were provided
        if packages:
            return self._install_specific(packages, no_verify)
        return self._install_from_scan(no_verify)

    # ------------------------------------------------------------------
    # Mode A: Install specific packages
    # ------------------------------------------------------------------
    def _install_specific(self, packages: List[str], no_verify: bool) -> int:
        """
        Install specific packages by spec and add them to teloce-npm.json.

        This is the multi-package equivalent of `teloce-npm add`.
        """
        print(f"\n[1/5] Installing {len(packages)} package(s)...")

        installed = []
        raw_config = self._read_raw_config()
        raw_config.setdefault("packages", [])

        for spec in packages:
            name, version_range = parse_package_spec(spec)
            print(f"\n  → {name}@{version_range}")
            try:
                resolved = self._install_package(name, version_range, no_verify)
                if resolved:
                    installed.append(name)
                    # Register in config
                    if spec not in raw_config["packages"]:
                        raw_config["packages"].append(spec)
            except Exception as e:
                print(f"    [ERROR] {e}")

        if not installed:
            print("\n  No packages installed.")
            return 1

        # Persist config changes
        self._write_raw_config(raw_config)

        # Regenerate runtime files
        print("\n[2/5] Generating runtime files...")
        generate_all(
            self._get_package_list(),
            self.adapter.output_dir,
            base_path=self.adapter.get_base_path(),
        )

        # Inject
        print("\n[3/5] Injecting scripts...")
        self.adapter.inject_scripts()

        # Save lockfile
        print("\n[4/5] Saving lockfile...")
        self.lockfile.save()

        print(f"\n[5/5] Installed {len(installed)} package(s): {', '.join(installed)}")
        print(f"  Output: {self.adapter.output_dir}")
        return 0

    # ------------------------------------------------------------------
    # Mode B: Scan .vel + config, install everything
    # ------------------------------------------------------------------
    def _install_from_scan(self, no_verify: bool) -> int:
        """Scan .vel files + config and install all required packages."""
        print("\n[1/6] Scanning for packages...")
        required = {}

        # From .vel files
        uses = scan_project(self.project_root)
        for use in uses:
            required[use["package"]] = "*"

        # From teloce-npm.json
        for pkg_spec in self.config.get("packages", []):
            name, ver = parse_package_spec(pkg_spec)
            required[name] = ver

        if not required:
            print("  No packages declared. Nothing to install.")
            return 0

        print(f"  Found {len(required)} package(s):")
        for name in sorted(required):
            print(f"    - {name}")

        print("\n[2/6] Installing packages...")
        installed = []
        for name, version_range in sorted(required.items()):
            try:
                resolved = self._install_package(name, version_range, no_verify)
                if resolved:
                    installed.append(name)
            except Exception as e:
                print(f"  [ERROR] {name}: {e}")

        if not installed:
            print("\n  No packages installed successfully.")
            return 1

        print("\n[3/6] Generating runtime files...")
        generate_all(
            self._get_package_list(),
            self.adapter.output_dir,
            base_path=self.adapter.get_base_path(),
        )

        print("\n[4/6] Injecting scripts...")
        self.adapter.inject_scripts()

        print("\n[5/6] Saving lockfile...")
        self.lockfile.save()

        print(f"\n[6/6] Installation complete!")
        print(f"  {len(installed)} package(s) installed")
        print(f"  Output: {self.adapter.output_dir}")
        return 0

    # ------------------------------------------------------------------
    # Shared: install a single package
    # ------------------------------------------------------------------
    def _install_package(self, name: str, version_range: str, no_verify: bool):
        # Check lockfile for locked version (reproducibility)
        locked_version = self.lockfile.get_package_version(name)

        try:
            metadata = self.registry.get_package_metadata(name)
        except PackageNotFoundError:
            print(f"  [SKIP] {name}: not found in registry")
            return None

        # Resolve version (prefer locked version if available)
        if locked_version:
            resolved = locked_version
            try:
                version_data = extract_version_data(metadata, resolved)
            except PackageNotFoundError:
                print(f"  [WARN] {name}: locked version {resolved} unavailable, re-resolving")
                resolved = resolve_version(metadata, version_range)
                version_data = extract_version_data(metadata, resolved)
        else:
            resolved = resolve_version(metadata, version_range)
            version_data = extract_version_data(metadata, resolved)

        integrity = version_data["integrity"]

        # Cache hit
        if self.cache.has(name, resolved, integrity):
            print(f"    [CACHED] {name}@{resolved}")
            wrapped = self.cache.get_wrapped(name, resolved)
            write_file_atomic(self.adapter.wrapped_file_path(name), wrapped)
            self._update_lockfile(name, resolved, version_data, wrapped)
            return resolved

        # Download
        print(f"    [DOWNLOADING] {name}@{resolved}...")
        tarball = download_tarball(
            tarball_url=version_data["tarball_url"],
            dest_path=self.cache.storage.tarball_path(name, resolved),
            expected_integrity=integrity,
        )

        # Extract + security + wrap
        with tempfile.TemporaryDirectory(dir=self.cache.storage.cache_dir) as tmpdir:
            extracted = extract_tarball(tarball, Path(tmpdir) / "extract")

            if not no_verify:
                policy = SecurityPolicy.from_config(self.config["security"])
                result = run_security_checks(extracted, name, policy)
                if not result["safe"]:
                    print(f"    [BLOCKED] {name}: security checks failed")
                    for f in result["findings"]:
                        print(f"      - [{f['severity']}] {f['message']}")
                    return None

                vulns = check_vulnerabilities(name, resolved)
                for v in vulns:
                    print(f"    [VULN] {name}: {v['id']} - {v['summary']}")

            try:
                wrapped = wrap_package(extracted, name)
            except Exception as e:
                print(f"    [ERROR] {name}: wrap failed - {e}")
                return None

            self.cache.store(
                package_name=name,
                version=resolved,
                extracted_dir=extracted,
                wrapped_code=wrapped,
                metadata={
                    "integrity": integrity,
                    "tarball_url": version_data["tarball_url"],
                    "scan_result": "clean",
                },
            )

        write_file_atomic(self.adapter.wrapped_file_path(name), wrapped)
        self._update_lockfile(name, resolved, version_data, wrapped)
        print(f"    [INSTALLED] {name}@{resolved}")
        return resolved

    def _update_lockfile(self, name, resolved, version_data, wrapped):
        self.lockfile.add_package(
            package_name=name,
            version=resolved,
            resolved_url=version_data["tarball_url"],
            integrity=version_data["integrity"],
            wrapped_filename=self.adapter.wrapped_file_path(name).name,
            size=len(wrapped),
            dependencies=version_data.get("dependencies", {}),
            scan_result="clean",
        )