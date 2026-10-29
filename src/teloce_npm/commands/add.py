"""
`teloce-npm add <package>` — install a single package and register it in config.
"""

from teloce_npm.commands import BaseCommand, parse_package_spec
from teloce_npm.commands.install import InstallCommand


class AddCommand(BaseCommand):

    def execute(self, package: str, options: dict = None) -> int:
        options = options or {}
        self._setup(verbose=options.get("verbose", False))

        name, version_range = parse_package_spec(package)
        print(f"Adding {name}@{version_range}...")

        # 1. Run the full install pipeline for this single package
        installer = InstallCommand(project_root=self.project_root)
        installer._setup()
        installer.adapter.prepare()

        try:
            resolved = installer._install_package(
                name, version_range, no_verify=options.get("no_verify", False)
            )
        except Exception as e:
            print(f"[ERROR] {e}")
            return 1

        if not resolved:
            print(f"[ERROR] Failed to install {name}")
            return 1

        # 2. Register in teloce-npm.json so future installs know about it
        raw = self._read_raw_config()
        raw.setdefault("packages", [])
        if package not in raw["packages"]:
            raw["packages"].append(package)
        self._write_raw_config(raw)

        # 3. Regenerate runtime files
        package_list = installer._get_package_list()
        from teloce_npm.generator import generate_all
        generate_all(
            package_list,
            installer.adapter.output_dir,
            base_path=installer.adapter.get_base_path(),
        )

        # 4. Inject scripts
        installer.adapter.inject_scripts()

        # 5. Save lockfile
        installer.lockfile.save()

        print(f"\n{name}@{resolved} installed successfully.")
        print(f"  Output: {installer.adapter.wrapped_file_path(name)}")
        return 0