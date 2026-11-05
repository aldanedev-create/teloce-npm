"""
Generate `loader.js` — the async package loader.
"""

from pathlib import Path
import json
from string import Template
from typing import Optional

from teloce_npm.utils.logging import logger

TEMPLATE_PATH = Path(__file__).parent / "templates" / "loader.js.tmpl"


def generate_loader_js(
    base_path: str = "/static/teloce-npm",
    manifest_url: Optional[str] = None,
) -> str:
    """
    Generate the contents of `loader.js`.

    The loader is static: it reads manifest.json at runtime to
    discover which packages exist and how to load them. This means
    re-running `teloce-npm install` with a different set of packages
    does NOT require regenerating loader.js.

    Args:
        base_path: The URL path prefix under which wrapped files are served.
                   E.g., "/static/teloce-npm".
        manifest_url: The full URL to manifest.json. Defaults to
                      `{base_path}/manifest.json`.

    Returns:
        The `loader.js` content as a string.
    """
    if manifest_url is None:
        manifest_url = f"{base_path.rstrip('/')}/manifest.json"

    template = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))
    # JSON string literals are valid JavaScript, so quotes, backslashes and
    # line breaks in a configured path can never break out of the string.
    return template.substitute(
        base_path=json.dumps(base_path.rstrip("/")),
        manifest_url=json.dumps(manifest_url),
    )


def write_loader_js(
    output_dir: Path,
    base_path: str = "/static/teloce-npm",
    manifest_url: Optional[str] = None,
) -> Path:
    """
    Generate and write `loader.js` to the output directory.

    Returns:
        The path to the written file.
    """
    from teloce_npm.utils.file_io import write_file_atomic

    content = generate_loader_js(base_path=base_path, manifest_url=manifest_url)
    output_dir.mkdir(parents=True, exist_ok=True)
    loader_path = output_dir / "loader.js"
    write_file_atomic(loader_path, content)
    logger.debug(f"Wrote loader.js to {loader_path}")
    return loader_path
