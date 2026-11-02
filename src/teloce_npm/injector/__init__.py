"""
HTML Injection module for Teloce-NPM.

Handles safely inserting the runtime <script> tags into the
developer's entry HTML file without breaking template engines.
"""

from pathlib import Path

from teloce_npm.utils.logging import logger

from .html_scanner import get_entry_html
from .injector import inject_scripts, remove_scripts
from .tag_generator import generate_script_tags


def apply_injection(entry_html_path: Path, base_path: str = "/static/teloce-npm") -> None:
    """
    Complete workflow: Validate HTML -> Generate Tags -> Inject.

    Args:
        entry_html_path: The absolute path to the HTML file.
        base_path: The URL path prefix for the generated scripts.
    """
    # 1. Verify the file exists
    verified_path = get_entry_html(entry_html_path)

    # 2. Generate the tags
    tags = generate_script_tags(base_path)

    # 3. Inject them
    inject_scripts(verified_path, tags)


def revert_injection(entry_html_path: Path) -> None:
    """
    Complete workflow: Remove injected tags.

    Args:
        entry_html_path: The absolute path to the HTML file.
    """
    if not entry_html_path.exists():
        logger.warning(f"Entry HTML not found during cleanup: {entry_html_path}")
        return
    remove_scripts(entry_html_path)


__all__ = [
    "apply_injection",
    "generate_script_tags",
    "get_entry_html",
    "inject_scripts",
    "remove_scripts",
    "revert_injection",
]
