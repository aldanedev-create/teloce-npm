"""
Factory for wrapping npm packages for the browser.

Detects the package format (CJS, ESM, UMD, IIFE) and applies the correct wrapper.
"""

import json
from pathlib import Path
from typing import Any

from teloce_npm.utils.errors import TeloceNpmError
from teloce_npm.utils.logging import logger

from .base import BaseWrapper
from .cjs import CjsWrapper
from .esm import EsmWrapper
from .life import LifeWrapper
from .umd import UmdWrapper


def detect_format(package_json: dict[str, Any]) -> str:
    """
    Detect the module format based on package.json fields.

    Returns:
        One of: 'esm', 'umd', 'iife', 'cjs'
    """
    # Explicit ESM
    if package_json.get("type") == "module":
        return "esm"

    # Has a dedicated ESM entry point
    if package_json.get("module"):
        return "esm"

    # Has a dedicated browser entry point
    if package_json.get("browser") and isinstance(package_json["browser"], str):
        return "umd"

    # Check the main file name
    main = package_json.get("main", "")
    if isinstance(main, str):
        if "umd" in main.lower():
            return "umd"
        if "iife" in main.lower() or "browser" in main.lower():
            return "iife"

    # Default to CommonJS
    return "cjs"


def wrap_package(package_dir: Path, package_name: str) -> str:
    """
    Detect the package format and wrap it accordingly.

    Args:
        package_dir: The extracted directory containing package.json.
        package_name: The name of the package (e.g., 'lodash').

    Returns:
        The wrapped JavaScript code as a string.
    """
    package_json_path = package_dir / "package.json"
    if not package_json_path.exists():
        raise TeloceNpmError(
            f"Missing package.json for '{package_name}'. "
            f"The tarball may be corrupted or malformed."
        )

    with open(package_json_path, encoding="utf-8") as f:
        package_json = json.load(f)

    # Map format strings to wrapper classes
    wrapper_map: dict[str, type[BaseWrapper]] = {
        "esm": EsmWrapper,
        "umd": UmdWrapper,
        "iife": LifeWrapper,
        "cjs": CjsWrapper,
    }

    detected_format = detect_format(package_json)
    wrapper_class = wrapper_map[detected_format]

    logger.debug(
        f"Detected format '{detected_format}' for '{package_name}'. "
        f"Using {wrapper_class.__name__}."
    )

    wrapper = wrapper_class(package_dir, package_name, package_json)
    return wrapper.wrap()


__all__ = [
    "BaseWrapper",
    "CjsWrapper",
    "EsmWrapper",
    "LifeWrapper",
    "UmdWrapper",
    "detect_format",
    "wrap_package",
]
