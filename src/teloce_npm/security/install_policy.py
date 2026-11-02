"""
Block install scripts in npm packages.

Install scripts (preinstall, install, postinstall) execute arbitrary
commands during `npm install`. Since Teloce-NPM never runs install
scripts, we block packages that contain them by default.
"""

import json
from pathlib import Path

from teloce_npm.utils.errors import SecurityError
from teloce_npm.utils.logging import logger

# Packages known to have safe install scripts (for native bindings, etc.)
# These are explicitly allow-listed.
ALLOWED_SCRIPTS: set[str] = {
    "esbuild",
    "sharp",
    "canvas",
    "bcrypt",
    "node-sass",
    "puppeteer",
    "playwright",
}


BLOCKED_SCRIPTS = ["preinstall", "install", "postinstall"]


def check_install_scripts(package_dir: Path, package_name: str) -> bool:
    """
    Check if a package contains blocked install scripts.

    Args:
        package_dir: The extracted package directory.
        package_name: The package name.

    Returns:
        True if the package is safe (no blocked scripts).

    Raises:
        SecurityError: If the package contains blocked install scripts.
    """
    package_json_path = package_dir / "package.json"

    if not package_json_path.exists():
        logger.warning(f"No package.json found for {package_name}")
        return True

    try:
        with open(package_json_path, encoding="utf-8") as f:
            package_json = json.load(f)
    except json.JSONDecodeError as e:
        raise SecurityError(f"Invalid package.json for {package_name}: {e}") from e

    scripts = package_json.get("scripts", {})

    for script_name in BLOCKED_SCRIPTS:
        if script_name in scripts:
            # Check if the package is allow-listed
            if package_name in ALLOWED_SCRIPTS:
                logger.debug(
                    f"Allowing install script '{script_name}' for allow-listed package '{package_name}'"
                )
                continue

            raise SecurityError(
                f"Package '{package_name}' contains a '{script_name}' script:\n"
                f"  {scripts[script_name]}\n"
                f"Install scripts are blocked by default for security reasons.\n"
                f"Use `--no-verify` to override (DANGEROUS!) or add the package "
                f"to the ALLOWED_SCRIPTS list in install_policy.py."
            )

    return True
