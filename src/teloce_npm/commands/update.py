"""
`teloce-npm update [package]` — update packages to the latest allowed version.
"""

from typing import Optional

from teloce_npm.commands import BaseCommand
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

        print(f"Updating {len(targets)} package(s)...")
        installer = InstallCommand(project_root=self.project_root)
        installer._setup()

        updated = 0
        for name in targets:
            locked_version = self.lockfile.get_package_version(name)
            try:
                metadata = self.registry.get_package_metadata(name)
                from teloce_npm.registry import resolve_version

                latest = resolve_version(metadata, "latest")

                if latest == locked_version:
                    print(f"  [UP-TO-DATE] {name}@{locked_version}")
                    continue

                print(f"  [UPDATE] {name}: {locked_version} -> {latest}")
                installer._install_package(name, f"={latest}", no_verify=False)
                updated += 1
            except Exception as e:
                print(f"  [ERROR] {name}: {e}")

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
        return 0
