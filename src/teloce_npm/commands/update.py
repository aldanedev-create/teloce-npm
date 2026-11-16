"""
`teloce-npm update [package]` — update packages to the latest allowed version.
"""

from typing import Optional

from teloce_npm.commands import BaseCommand, parse_package_spec
from teloce_npm.commands.install import InstallCommand


class UpdateCommand(BaseCommand):

    def execute(self, package: Optional[str] = None) -> int:
        self._setup()
        self.adapter.prepare()

        locked = self.lockfile.list_packages()
        targets = {package: "*"} if package else locked

        if not targets:
            print("No packages to update.")
            return 0

        # Respect the range recorded in teloce-npm.json ("d3@^7" never jumps to d3 8);
        # packages without a range follow the registry's latest version.
        ranges = {}
        for spec in self.config.get("packages", []):
            spec_name, spec_range = parse_package_spec(spec)
            ranges[spec_name] = spec_range

        print(f"Updating {len(targets)} package(s)...")
        installer = InstallCommand(project_root=self.project_root)
        installer._setup()

        updated = 0
        failed: list[str] = []
        for name in targets:
            locked_version = self.lockfile.get_package_version(name)
            try:
                metadata = self.registry.get_package_metadata(name)
                from teloce_npm.registry import resolve_version

                latest = resolve_version(metadata, ranges.get(name, "latest"))

                if latest == locked_version:
                    print(f"  [UP-TO-DATE] {name}@{locked_version}")
                    continue

                print(f"  [UPDATE] {name}: {locked_version} -> {latest}")
                resolved = installer._install_package(
                    name, f"={latest}", no_verify=False, ignore_lock=True
                )
                if resolved:
                    updated += 1
                else:
                    # Blocked by a security check or failed: the old version stays locked.
                    print(
                        f"  [FAILED] {name}: {latest} was not installed; keeping {locked_version}"
                    )
                    failed.append(name)
            except Exception as e:
                print(f"  [ERROR] {name}: {e}")
                failed.append(name)

        # Regenerate + inject
        from teloce_npm.generator import generate_all

        generate_all(
            self._get_package_list(),
            self.adapter.output_dir,
            base_path=self.adapter.get_base_path(),
        )
        self.adapter.inject_scripts()
        self.lockfile.save()

        print(f"\n{updated} package(s) updated.")
        if failed:
            print(f"{len(failed)} failed: {', '.join(failed)}")
            return 1
        return 0
