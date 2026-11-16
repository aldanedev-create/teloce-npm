"""
`teloce-npm doctor` — diagnose project setup.
"""

import sys

from teloce_npm.commands import BaseCommand
from teloce_npm.lockfile import LockfileVerifier
from teloce_npm.version import __version__


class DoctorCommand(BaseCommand):

    def execute(self) -> int:
        self._setup()

        print("Teloce-NPM Doctor")
        print("=" * 40)
        print(f"  Python:         {sys.version.split()[0]}")
        print(f"  Teloce-NPM:     {__version__}")
        print(f"  Registry:       {self.config['registry']}")

        summary = self.adapter.summary()
        if summary["entry_html"]["path"] is None:
            print("\n  Entry HTML:     none (entry_html is null; nothing is injected)")
        else:
            print(f"\n  Entry HTML:     {summary['entry_html']['path']}")
            print(f"    Exists:       {summary['entry_html']['exists']}")
        print(f"  Output dir:     {summary['output_dir']['path']}")
        print(f"    Exists:       {summary['output_dir']['exists']}")
        print(f"  Cache dir:      {summary['cache_dir']['path']}")
        print(f"    Exists:       {summary['cache_dir']['exists']}")
        print(f"  Base path:      {summary['base_path']}")

        # Lockfile verification
        verifier = LockfileVerifier(self.lockfile, self.cache)
        print()
        print(verifier.report())

        # Cache status
        cached = self.cache.list_cached()
        print(f"\n  Cached packages: {len(cached)}")
        for pkg in cached:
            print(f"    - {pkg['name']}@{pkg['version']}")

        # Security policy
        print("\n  Security policy:")
        for key, val in self.config["security"].items():
            if isinstance(val, bool):
                print(f"    [{'ON ' if val else 'OFF'}] {key}")
            else:
                print(f"    {key}: {_describe_setting(val)}")

        return 0


def _describe_setting(value: object) -> str:
    """Short, readable form of a non-boolean security setting."""
    if isinstance(value, dict):
        if not value:
            return "none"
        return "; ".join(f"{name}: {', '.join(kinds)}" for name, kinds in value.items())
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "none"
    return str(value)
