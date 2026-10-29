"""
`teloce-npm list` — list installed packages.
"""

from teloce_npm.commands import BaseCommand


class ListCommand(BaseCommand):

    def execute(self) -> int:
        self._setup()

        packages = self.lockfile.list_packages()
        if not packages:
            print("No packages installed.")
            return 0

        print("Installed packages:\n")
        total_size = 0
        for name in sorted(packages):
            entry = self.lockfile.get_package(name)
            size = entry.get("size", 0)
            total_size += size
            file = entry.get("wrapped", "?")
            print(f"  {name}@{entry['version']}  ({_fmt_size(size)}, {file})")

        print(f"\nTotal: {len(packages)} package(s), {_fmt_size(total_size)}")
        return 0


def _fmt_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"