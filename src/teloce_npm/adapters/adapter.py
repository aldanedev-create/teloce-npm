"""
Framework-agnostic project adapter for Teloce-NPM.

The adapter is the single point of contact between the command layer
and the file system. It knows:

    - Where the entry HTML file lives (from config)
    - Where generated files should be written (from config)
    - What URL prefix the developer uses to serve those files

It is framework-agnostic: it never imports Flask, Django, or FastAPI.
It only knows about files on disk.

Example:

    from teloce_npm.adapters import get_adapter

    adapter = get_adapter(config, project_root)
    paths = adapter.prepare()          # validates files, creates dirs
    adapter.inject_scripts()           # injects into entry_html
    adapter.remove_scripts()           # reverts injection
"""

from pathlib import Path
from typing import Any, Optional

from teloce_npm.utils.errors import ConfigError
from teloce_npm.utils.logging import logger


class ProjectAdapter:
    """
    A framework-agnostic view of a Teloce-NPM project layout.

    Created by `get_adapter()`. All paths are already resolved to
    absolute Path objects by `config.loader.load_config()`.
    """

    def __init__(self, config: dict[str, Any], project_root: Path):
        self.config = config
        self.project_root = project_root

        # These are already absolute Path objects from the config loader
        self.entry_html: Path = config["entry_html"]
        self.output_dir: Path = config["output_dir"]
        self.cache_dir: Path = config["cache_dir"]

    # ------------------------------------------------------------------
    # Preparation
    # ------------------------------------------------------------------
    def prepare(self) -> dict[str, Any]:
        """
        Prepare the project for a Teloce-NPM run.

        Validates that:
            - The entry HTML file exists and is readable.
            - The output directory exists (creates it if missing).

        Returns:
            A dict with 'entry_html', 'output_dir', and 'base_path'.

        Raises:
            ConfigError: If the entry HTML is missing.
        """
        # Validate the entry HTML
        if not self.entry_html.exists():
            raise ConfigError(
                f"Entry HTML file not found: {self.entry_html}\n"
                f"Check the 'entry_html' setting in teloce-npm.json."
            )
        if not self.entry_html.is_file():
            raise ConfigError(f"Entry HTML path is not a file: {self.entry_html}")

        # Ensure the output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        base_path = self.get_base_path()
        logger.debug(
            f"Adapter prepared: entry_html={self.entry_html}, "
            f"output_dir={self.output_dir}, base_path={base_path}"
        )

        return {
            "entry_html": self.entry_html,
            "output_dir": self.output_dir,
            "base_path": base_path,
        }

    # ------------------------------------------------------------------
    # Base path
    # ------------------------------------------------------------------
    def get_base_path(self) -> str:
        """
        Return the URL prefix under which output_dir is served.

        Resolution order:
            1. If `base_path` is explicitly set in config, use it.
            2. Otherwise, derive it from output_dir. If output_dir
               contains a 'static' segment, everything from 'static'
               onward becomes the URL path (e.g., 'dist/static/teloce-npm'
               -> '/static/teloce-npm').
            3. Fallback: '/static/teloce-npm'.

        This lets developers move output_dir (e.g., to 'build/')
        without having to also update base_path in most cases.
        """
        # Explicit override wins
        explicit = self.config.get("base_path")
        if explicit:
            return explicit.rstrip("/") or "/"

        # Auto-derive from output_dir
        parts = self.output_dir.parts
        if "static" in parts:
            idx = parts.index("static")
            derived = "/" + "/".join(parts[idx:])
            logger.debug(f"Derived base_path from output_dir: {derived}")
            return derived

        # Fallback
        return "/static/teloce-npm"

    # ------------------------------------------------------------------
    # Injection
    # ------------------------------------------------------------------
    def inject_scripts(self, base_path: Optional[str] = None) -> None:
        """
        Inject the runtime <script> tags into the entry HTML file.

        Delegates to injector.apply_injection(). Safe to call repeatedly.

        Args:
            base_path: Override the URL prefix. Defaults to get_base_path().
        """
        from teloce_npm.injector import apply_injection

        bp = base_path or self.get_base_path()
        apply_injection(self.entry_html, base_path=bp)

    def remove_scripts(self) -> None:
        """
        Remove previously injected <script> tags from the entry HTML file.

        Delegates to injector.revert_injection(). Safe to call if no
        tags were injected.
        """
        from teloce_npm.injector import revert_injection

        revert_injection(self.entry_html)

    # ------------------------------------------------------------------
    # File paths
    # ------------------------------------------------------------------
    def wrapped_file_path(self, package_name: str) -> Path:
        """
        Return the path where a package's wrapped output should be written.

        e.g., for package 'lodash' -> output_dir / 'lodash.js'
        """
        safe_name = self._safe_filename(package_name)
        return self.output_dir / f"{safe_name}.js"

    def manifest_path(self) -> Path:
        return self.output_dir / "manifest.json"

    def use_js_path(self) -> Path:
        return self.output_dir / "use.js"

    def loader_js_path(self) -> Path:
        return self.output_dir / "loader.js"

    def _safe_filename(self, package_name: str) -> str:
        """
        Convert a package name into a safe file name.
        e.g., '@scope/pkg' -> 'scope_pkg', 'chart.js' -> 'chart_js'
        """
        return package_name.replace("@", "").replace("/", "_").replace("-", "_").replace(".", "_")

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------
    def summary(self) -> dict[str, Any]:
        """Return a diagnostic summary for `teloce-npm doctor`."""
        return {
            "entry_html": {
                "path": str(self.entry_html),
                "exists": self.entry_html.exists(),
            },
            "output_dir": {
                "path": str(self.output_dir),
                "exists": self.output_dir.exists(),
            },
            "cache_dir": {
                "path": str(self.cache_dir),
                "exists": self.cache_dir.exists(),
            },
            "base_path": self.get_base_path(),
        }


def get_adapter(config: dict[str, Any], project_root: Optional[Path] = None) -> ProjectAdapter:
    """
    Factory function to build a ProjectAdapter from a config dict.

    Args:
        config: The config dict from teloce_npm.config.load_config().
        project_root: The project root. Defaults to the parent of entry_html's
                      templates directory, or the current working directory.

    Returns:
        A ready-to-use ProjectAdapter.
    """
    if project_root is None:
        # Try to derive project root from entry_html if it lives under templates/
        entry = config["entry_html"]
        project_root = entry.parent.parent if entry.parent.name == "templates" else Path.cwd()

    return ProjectAdapter(config, project_root)
