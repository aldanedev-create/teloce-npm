"""
`teloce-npm remove <package>` — remove a package from the project.
"""

from teloce_npm.commands import BaseCommand
from teloce_npm.generator import generate_all


class RemoveCommand(BaseCommand):

    def execute(self, package: str) -> int:
        self._setup()
        self.adapter.prepare()

        # 1. Remove from config
        raw = self._read_raw_config()
        if "packages" in raw and package in raw["packages"]:
            raw["packages"].remove(package)
            self._write_raw_config(raw)

        # 2. Remove from lockfile
        removed = self.lockfile.remove_package(package)
        if not removed:
            print(f"[INFO] {package} was not in the lockfile.")
        self.lockfile.save()

        # 3. Remove from cache
        version = None
        for pkg in self.cache.list_cached():
            if pkg["name"] == package:
                version = pkg["version"]
                break
        if version:
            self.cache.invalidate(package, version)

        # 4. Remove wrapped file from output
        wrapped_path = self.adapter.wrapped_file_path(package)
        if wrapped_path.exists():
            wrapped_path.unlink()

        # 5. Regenerate runtime files
        remaining = self._get_package_list()
        generate_all(
            remaining,
            self.adapter.output_dir,
            base_path=self.adapter.get_base_path(),
        )

        # 6. Update injection (or remove if no packages remain)
        if remaining:
            self.adapter.inject_scripts()
        else:
            self.adapter.remove_scripts()

        print(f"{package} removed.")
        return 0
