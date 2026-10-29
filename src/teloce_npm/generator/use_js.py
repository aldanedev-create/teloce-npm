"""
Generate `use.js` — the window.use() runtime.
"""

from pathlib import Path
from string import Template
from typing import Any, Dict, List

from teloce_npm.utils.logging import logger


TEMPLATE_PATH = Path(__file__).parent / "templates" / "use.js.tmpl"


def generate_use_js(packages: List[Dict[str, Any]]) -> str:
    """
    Generate the contents of `use.js`.

    Args:
        packages: A list of package dicts, each with at least:
            - name (str): The npm package name.
            - version (str): The installed version.

    Returns:
        The `use.js` content as a string.
    """
    # Build a {name: version} map for diagnostics
    if packages:
        lines = []
        for pkg in sorted(packages, key=lambda p: p["name"]):
            lines.append(f'        "{pkg["name"]}": "{pkg["version"]}"')
        available_packages = ",\n".join(lines)
    else:
        available_packages = "        // no packages installed"

    template = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))
    return template.substitute(available_packages=available_packages)


def write_use_js(packages: List[Dict[str, Any]], output_dir: Path) -> Path:
    """
    Generate and write `use.js` to the output directory.

    Returns:
        The path to the written file.
    """
    from teloce_npm.utils.file_io import write_file_atomic

    content = generate_use_js(packages)
    output_dir.mkdir(parents=True, exist_ok=True)
    use_path = output_dir / "use.js"
    write_file_atomic(use_path, content)
    logger.debug(f"Wrote use.js to {use_path}")
    return use_path