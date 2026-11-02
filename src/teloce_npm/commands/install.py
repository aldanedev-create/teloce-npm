"""
`teloce-npm install` — the primary build command.

Two modes:
    - `teloce-npm install`              → scan .vel + config, install everything
    - `teloce-npm install <pkg> [...]`  → install specific packages and add to config

Wrapping strategy:
    - bundling.mode == "never"   → Tree-sitter wrapper only
    - bundling.mode == "always"  → MinifyJS bundler only
    - bundling.mode == "auto"    → Tree-sitter first, fall back to MinifyJS

All package writes go through either:
    - self.adapter.wrapped_file_path(name)  (Tree-sitter)
    - <output_dir>/<safe_name>/<safe_name>.js  (MinifyJS)
"""

import shutil
import tempfile
from pathlib import Path
from typing import Optional, cast

from teloce_npm.bundler.asset_pipeline import copy_worker_assets, discover_worker_assets
from teloce_npm.commands import BaseCommand, parse_package_spec
from teloce_npm.downloader import download_tarball, extract_tarball
from teloce_npm.generator import generate_all
from teloce_npm.registry import extract_version_data, resolve_version
from teloce_npm.scanner import scan_project
from teloce_npm.security import (
    SecurityPolicy,
    check_vulnerabilities,
    run_security_checks,
)
from teloce_npm.utils.errors import PackageNotFoundError, TeloceNpmError
from teloce_npm.utils.file_io import write_file_atomic
from teloce_npm.utils.logging import logger
from teloce_npm.wrapper import wrap_package


class InstallCommand(BaseCommand):

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def execute(
        self,
        packages: Optional[list[str]] = None,
        production: bool = False,
        verbose: bool = False,
        no_verify: bool = False,
    ) -> int:
        self._setup(verbose=verbose)
        print("Teloce-NPM Install")
        print("=" * 40)

        # Prepare adapter (validates entry_html, creates output_dir)
        self.adapter.prepare()

        # Branch based on whether packages were provided
        if packages:
            return self._install_specific(packages, no_verify)
        return self._install_from_scan(no_verify)

    # ------------------------------------------------------------------
    # Mode A: Install specific packages (with config mutation)
    # ------------------------------------------------------------------
    def _install_specific(self, packages: list[str], no_verify: bool) -> int:
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
        self._sync_teloce_source_assets()

        print("\n[3/5] Injecting scripts...")
        self.adapter.inject_scripts()

        print("\n[4/5] Saving lockfile...")
        self.lockfile.save()

        print(f"\n[5/5] Installed {len(installed)} package(s): {', '.join(installed)}")
        print(f"  Output: {self.adapter.output_dir}")
        return 0

    # ------------------------------------------------------------------
    # Mode B: Scan .vel + config, install everything
    # ------------------------------------------------------------------
    def _install_from_scan(self, no_verify: bool) -> int:
        print("\n[1/6] Scanning for packages...")
        required = {}

        # From .vel / .html files
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
        self._sync_teloce_source_assets()

        print("\n[4/6] Injecting scripts...")
        self.adapter.inject_scripts()

        print("\n[5/6] Saving lockfile...")
        self.lockfile.save()

        print("\n[6/6] Installation complete!")
        print(f"  {len(installed)} package(s) installed")
        print(f"  Output: {self.adapter.output_dir}")
        return 0

    # ------------------------------------------------------------------
    # Core: install a single package
    # ------------------------------------------------------------------
    def _install_package(
        self,
        name: str,
        version_range: str,
        no_verify: bool,
    ) -> Optional[str]:
        """
        Install a single package. Returns the resolved version on success,
        None on failure.
        """
        # 1. Determine resolved version (lockfile wins for reproducibility)
        locked_version = self.lockfile.get_package_version(name)

        try:
            metadata = self.registry.get_package_metadata(name)
        except PackageNotFoundError:
            print(f"    [SKIP] {name}: not found in registry")
            return None

        if locked_version:
            resolved = locked_version
            try:
                version_data = extract_version_data(metadata, resolved)
            except PackageNotFoundError:
                print(f"    [WARN] {name}: locked version {resolved} unavailable, " f"re-resolving")
                resolved = resolve_version(metadata, version_range)
                version_data = extract_version_data(metadata, resolved)
        else:
            resolved = resolve_version(metadata, version_range)
            version_data = extract_version_data(metadata, resolved)

        integrity = version_data["integrity"]

        # 2. Cache hit → reuse
        if self.cache.has(name, resolved, integrity):
            print(f"    [CACHED] {name}@{resolved}")
            wrapped = self.cache.get_wrapped(name, resolved)
            previous_entry = self.lockfile.get_package(name) or {}
            wrapped_filename = previous_entry.get("wrapped", self._default_wrapped_filename(name))
            write_file_atomic(self.adapter.output_dir / wrapped_filename, wrapped)
            bundle_dir = self.adapter.output_dir / self._safe_package_name(name)
            copy_worker_assets(self.cache.get_extracted_dir(name, resolved), bundle_dir)
            self._update_lockfile(
                name,
                resolved,
                version_data,
                wrapped,
                wrapped_filename=wrapped_filename,
            )
            return str(resolved)

        # 3. Cache miss → download
        print(f"    [DOWNLOADING] {name}@{resolved}...")
        tarball = download_tarball(
            tarball_url=version_data["tarball_url"],
            dest_path=self.cache.storage.tarball_path(name, resolved),
            expected_integrity=integrity,
        )

        # 4. Extract into a temp dir inside the cache (cheap moves)
        with tempfile.TemporaryDirectory(dir=self.cache.storage.cache_dir) as tmpdir:
            extracted = extract_tarball(tarball, Path(tmpdir) / "extract")

            # 5. Security checks
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

            # 6. Wrap or bundle (3-tuple: code, size, already_written_path)
            try:
                wrapped_code, wrapped_size, already_written = self._wrap_or_bundle(extracted, name)
            except Exception as e:
                print(f"    [ERROR] {name}: wrapping failed - {e}")
                return None

            # 7. Write to output (unless the bundler already did)
            if already_written is None:
                write_file_atomic(
                    self.adapter.wrapped_file_path(name),
                    wrapped_code,
                )

            # 8. Store in cache
            self.cache.store(
                package_name=name,
                version=resolved,
                extracted_dir=extracted,
                wrapped_code=wrapped_code,
                metadata={
                    "integrity": integrity,
                    "tarball_url": version_data["tarball_url"],
                    "scan_result": "clean",
                },
            )

        # 9. Update lockfile
        self._update_lockfile(
            name,
            resolved,
            version_data,
            wrapped_code,
            wrapped_size=wrapped_size,
            wrapped_filename=self._wrapped_filename(already_written, name),
        )

        print(f"    [INSTALLED] {name}@{resolved}")
        return str(resolved)

    # ------------------------------------------------------------------
    # Wrapping dispatch (Tree-sitter vs MinifyJS)
    # ------------------------------------------------------------------
    def _wrap_or_bundle(
        self,
        extracted: Path,
        name: str,
    ) -> tuple[str, int, Optional[Path]]:
        """
        Returns (wrapped_code, wrapped_size, already_written_path).

        If `already_written_path` is not None, the caller must skip the
        write_file_atomic step — the bundler wrote the file directly.
        """
        mode = self.config["bundling"]["mode"]

        if mode == "always":
            return self._bundle_via_minifyjs(extracted, name)
        if mode == "auto":
            return self._try_wrap_with_fallback(extracted, name)

        # mode == "never"
        code = wrap_package(extracted, name)
        return code, len(code), None

    def _try_wrap_with_fallback(
        self,
        extracted: Path,
        name: str,
    ) -> tuple[str, int, Optional[Path]]:
        """
        Try Tree-sitter first; fall back to MinifyJS on failure.
        """
        try:
            code = wrap_package(extracted, name)
            return code, len(code), None
        except Exception as e:
            logger.info(
                f"[auto] Tree-sitter wrapper failed for {name}, " f"falling back to MinifyJS: {e}"
            )
            return self._bundle_via_minifyjs(extracted, name)

    def _bundle_via_minifyjs(
        self,
        extracted: Path,
        name: str,
    ) -> tuple[str, int, Optional[Path]]:
        """
        Bundle the package using MinifyJS. Writes output directly to
        adapter.output_dir; returns the primary bundle's content, its size,
        and its on-disk path (so the caller skips re-writing).
        """
        from teloce_npm.bundler import MinifyJSBundler, MinifyJSNotAvailable

        try:
            bundler = MinifyJSBundler(self.config["bundling"])
            result = bundler.bundle_package(
                extracted_dir=extracted,
                package_name=name,
                output_dir=self.adapter.output_dir,
            )
        except MinifyJSNotAvailable as error:
            raise TeloceNpmError(
                f"Package '{name}' requires bundling, but MinifyJS is unavailable.\n"
                f"Reinstall teloce-npm to restore its required MinifyJS dependency.\n"
                f"Or set bundling.mode to 'never' if this package should work "
                f"without bundling."
            ) from error

        output_files = [Path(p) for p in cast(list[str], result["output_files"])]
        total_size = sum(p.stat().st_size for p in output_files)
        primary = output_files[0]
        code = primary.read_text(encoding="utf-8")

        logger.debug(
            f"Bundled {name} via MinifyJS: " f"{len(output_files)} file(s), {total_size} bytes"
        )
        return code, total_size, primary

    # ------------------------------------------------------------------
    # Lockfile update
    # ------------------------------------------------------------------
    def _update_lockfile(
        self,
        name: str,
        resolved: str,
        version_data: dict,
        wrapped: str,
        wrapped_size: Optional[int] = None,
        wrapped_filename: Optional[str] = None,
    ) -> None:
        size = wrapped_size if wrapped_size is not None else len(wrapped)
        self.lockfile.add_package(
            package_name=name,
            version=resolved,
            resolved_url=version_data["tarball_url"],
            integrity=version_data["integrity"],
            wrapped_filename=wrapped_filename or self._default_wrapped_filename(name),
            size=size,
            dependencies=version_data.get("dependencies", {}),
            workers=self._worker_map(name),
            scan_result="clean",
        )

    def _default_wrapped_filename(self, name: str) -> str:
        """Return the package path used by the non-bundled wrapper."""
        return str(
            self.adapter.wrapped_file_path(name).relative_to(self.adapter.output_dir).as_posix()
        )

    def _safe_package_name(self, name: str) -> str:
        return name.replace("@", "").replace("/", "_").replace("-", "_").replace(".", "_")

    def _worker_map(self, name: str) -> dict[str, str]:
        safe_name = self._safe_package_name(name)
        workers = discover_worker_assets(self.adapter.output_dir / safe_name)
        return {label: f"{safe_name}/{relative}" for label, relative in workers.items()}

    def _wrapped_filename(self, output_path: Optional[Path], name: str) -> str:
        """Return a manifest/lockfile path for a bundled or wrapped package."""
        if output_path is None:
            return self._default_wrapped_filename(name)
        return output_path.relative_to(self.adapter.output_dir).as_posix()

    def _sync_teloce_source_assets(self) -> None:
        """Mirror standard dist/static assets into Teloce-Py's source tree."""
        try:
            relative = self.adapter.output_dir.relative_to(self.project_root / "dist" / "static")
        except ValueError:
            return

        source_dir = self.project_root / "static" / relative
        if source_dir.exists():
            shutil.rmtree(source_dir)
        shutil.copytree(self.adapter.output_dir, source_dir)
