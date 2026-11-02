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
            status = "ON " if val else "OFF"
            print(f"    [{status}] {key}")

        return 0
