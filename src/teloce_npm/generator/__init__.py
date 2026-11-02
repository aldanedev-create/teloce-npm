"""
Runtime file generation for Teloce-NPM.

Produces the three files the browser needs:
    - use.js       (defines window.use())
    - loader.js    (loads packages in dependency order)
    - manifest.json (package registry read by loader.js)
"""

from pathlib import Path
from typing import Any

from teloce_npm.utils.logging import logger

from .loader_js import generate_loader_js, write_loader_js
from .manifest import generate_manifest, write_manifest
from .use_js import generate_use_js, write_use_js


def generate_all(
    packages: list[dict[str, Any]],
    output_dir: Path,
    base_path: str = "/static/teloce-npm",
) -> dict[str, Path]:
    """
    Generate all three runtime files in one call.

    Args:
        packages: List of package dicts (name, version, file, size, integrity, dependencies).
        output_dir: Where to write the generated files.
        base_path: The URL prefix under which output_dir is served.

    Returns:
        A dict mapping filenames to their on-disk paths:
            {
                "manifest": Path(...),
                "use": Path(...),
                "loader": Path(...),
            }
    """
    logger.debug(f"Generating runtime files in {output_dir}")

    paths = {
        "manifest": write_manifest(packages, output_dir, base_path=base_path),
        "use": write_use_js(packages, output_dir),
        "loader": write_loader_js(output_dir, base_path=base_path),
    }

    logger.debug(f"Generated {len(paths)} runtime files for {len(packages)} package(s).")
    return paths


__all__ = [
    "generate_all",
    "generate_loader_js",
    "generate_manifest",
    "generate_use_js",
    "write_loader_js",
    "write_manifest",
    "write_use_js",
]
