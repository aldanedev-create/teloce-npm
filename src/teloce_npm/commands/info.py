"""
`teloce-npm info <package>` — show package details.
"""

from teloce_npm.commands import BaseCommand, parse_package_spec
from teloce_npm.registry import extract_version_data, resolve_version


class InfoCommand(BaseCommand):

    def execute(self, package: str) -> int:
        self._setup()

        name, version_range = parse_package_spec(package)
        try:
            metadata = self.registry.get_package_metadata(name)
            resolved = resolve_version(metadata, version_range)
            data = extract_version_data(metadata, resolved)
        except Exception as e:
            print(f"[ERROR] {e}")
            return 1

        print(f"{name}@{resolved}")
        print(f"  Description: {data.get('description', '(none)')}")
        print(f"  Tarball:     {data['tarball_url']}")
        print(f"  Integrity:   {data['integrity'][:40]}...")

        deps = data.get("dependencies", {})
        if deps:
            print(f"  Dependencies ({len(deps)}):")
            for dep, ver in deps.items():
                print(f"    - {dep}@{ver}")
        else:
            print("  Dependencies: none")

        scripts = data.get("scripts", {})
        blocked = [s for s in ("preinstall", "install", "postinstall") if s in scripts]
        if blocked:
            print(f"  Install scripts: {blocked} (BLOCKED by default)")
        else:
            print("  Install scripts: none")

        return 0