"""
CLI command implementations for Teloce-NPM.

The BaseCommand provides shared setup (config, adapter, lockfile, cache,
registry client, scanner) so each command file focuses on its unique logic.
"""

import json
from pathlib import Path
from typing import Any, Optional, cast

from teloce_npm.adapters import get_adapter
from teloce_npm.cache import CacheManager
from teloce_npm.config import load_config
from teloce_npm.lockfile import LockfileManager
from teloce_npm.registry import RegistryClient
from teloce_npm.utils.logging import logger


def parse_package_spec(spec: str) -> tuple[str, str]:
    """
    Parse a package spec into (name, version_range).

    Examples:
        'lodash'                -> ('lodash', '*')
        'lodash@4.17.21'        -> ('lodash', '4.17.21')
        'lodash@^4.17.0'        -> ('lodash', '^4.17.0')
        '@types/node'           -> ('@types/node', '*')
        '@types/node@20.0.0'    -> ('@types/node', '20.0.0')
    """
    if spec.startswith("@"):
        # Scoped package
        if spec.count("@") >= 2:
            idx = spec.rfind("@")
            return spec[:idx], spec[idx + 1 :]
        return spec, "*"

    if "@" in spec:
        name, ver = spec.split("@", 1)
        return name, ver

    return spec, "*"


class BaseCommand:
    """Shared setup for all commands."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.config: dict[str, Any] = {}
        self.adapter: Any = None
        self.lockfile: Any = None
        self.cache: Any = None
        self.registry: Any = None

    def _setup(self, verbose: bool = False) -> None:
        """Load config, build adapter, lockfile, cache, and registry client."""
        import logging

        if verbose:
            logger.setLevel(logging.DEBUG)
            for h in logger.handlers:
                h.setLevel(logging.DEBUG)

        self.config = load_config(self.project_root)
        self.adapter = get_adapter(self.config, self.project_root)
        self.lockfile = LockfileManager(self.project_root)
        self.cache = CacheManager(self.config["cache_dir"])
        self.registry = RegistryClient(self.config["registry"])

    # ------------------------------------------------------------------
    # Config mutation (used by add/remove)
    # ------------------------------------------------------------------
    def _read_raw_config(self) -> dict:
        config_path = self.project_root / "teloce-npm.json"
        if config_path.exists():
            return cast(dict[Any, Any], json.loads(config_path.read_text(encoding="utf-8")))
        return {}

    def _write_raw_config(self, data: dict) -> None:
        config_path = self.project_root / "teloce-npm.json"
        config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Package list for generator.generate_all()
    # ------------------------------------------------------------------
    def _get_package_list(self) -> list:
        """Build the package list expected by generator.generate_all()."""
        data = self.lockfile.load()
        result = []
        for name, entry in data["packages"].items():
            result.append(
                {
                    "name": name,
                    "version": entry["version"],
                    "file": entry["wrapped"],
                    "size": entry["size"],
                    "integrity": entry["integrity"],
                    "dependencies": entry.get("dependencies", {}),
                    "workers": entry.get("workers", {}),
                }
            )
        return result


__all__ = ["BaseCommand", "parse_package_spec"]
