"""
`teloce-npm add <package>` — install a single package and register it in config.
"""

from typing import Optional

from teloce_npm.commands import BaseCommand
from teloce_npm.commands.install import InstallCommand


class AddCommand(BaseCommand):

    def execute(
        self,
        package: str,
        options: Optional[dict] = None,
        *,
        verbose: bool = False,
        no_verify: bool = False,
    ) -> int:
        """
        Install `package` and register it in teloce-npm.json.

        Options can be given as keyword arguments or, for older callers, as an
        `options` dict (`{"verbose": ..., "no_verify": ...}`), which wins.
        """
        options = options or {}
        return InstallCommand(project_root=self.project_root).execute(
            packages=[package],
            verbose=options.get("verbose", verbose),
            no_verify=options.get("no_verify", no_verify),
        )
