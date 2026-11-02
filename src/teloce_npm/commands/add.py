"""
`teloce-npm add <package>` — install a single package and register it in config.
"""

from typing import Optional

from teloce_npm.commands import BaseCommand
from teloce_npm.commands.install import InstallCommand


class AddCommand(BaseCommand):

    def execute(self, package: str, options: Optional[dict] = None) -> int:
        options = options or {}
        return InstallCommand(project_root=self.project_root).execute(
            packages=[package],
            verbose=options.get("verbose", False),
            no_verify=options.get("no_verify", False),
        )
