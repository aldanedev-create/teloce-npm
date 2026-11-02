"""
Generate `manifest.json` — the package manifest read by loader.js.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from string import Template
from typing import Any

from teloce_npm.utils.logging import logger

MANIFEST_VERSION = "1.0.0"
TEMPLATE_PATH = Path(__file__).parent / "templates" / "manifest.json.tmpl"


def generate_manifest(
    packages: list[dict[str, Any]],
    base_path: str = "/static/teloce-npm",
) -> str:
    """
    Generate the contents of `manifest.json`.

    Args:
        packages: A list of package dicts, each with keys:
            - name (str): The npm package name (e.g., "lodash").
            - version (str): The exact installed version.
            - file (str): The wrapped output filename (e.g., "lodash.js").
            - size (int): Size of the wrapped output in bytes.
            - integrity (str): The SHA-512 hash from the registry.
            - dependencies (dict): A {name: version_range} map (may be empty).
        base_path: The URL path prefix under which wrapped files are served.

    Returns:
        The manifest JSON content as a string.
    """
    # Build the packages block as a dict
    packages_block: dict[str, dict[str, Any]] = {}
    total_size = 0

    for pkg in packages:
        name = pkg["name"]
        packages_block[name] = {
            "version": pkg["version"],
            "file": pkg["file"],
            "size": pkg["size"],
            "integrity": pkg["integrity"],
            "dependencies": pkg.get("dependencies", {}),
            "workers": pkg.get("workers", {}),
        }
        total_size += pkg.get("size", 0)

    # Serialize packages block separately (avoids escaping issues)
    packages_json = json.dumps(packages_block, indent=2, sort_keys=True)

    # Load and fill the template
    template = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))
    content = template.substitute(
        manifest_version=MANIFEST_VERSION,
        generated_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        base_path=base_path,
        total_size=total_size,
        packages_json=packages_json,
    )

    # Validate that the result is still valid JSON
    try:
        json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Generated manifest is not valid JSON: {e}")
        raise

    return content


def write_manifest(
    packages: list[dict[str, Any]],
    output_dir: Path,
    base_path: str = "/static/teloce-npm",
) -> Path:
    """
    Generate and write `manifest.json` to the output directory.

    Returns:
        The path to the written file.
    """
    from teloce_npm.utils.file_io import write_file_atomic

    content = generate_manifest(packages, base_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    write_file_atomic(manifest_path, content)
    logger.debug(f"Wrote manifest to {manifest_path}")
    return manifest_path
