"""
Base interface for all package wrappers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any

from teloce_npm.utils.logging import logger

class BaseWrapper(ABC):
    """Abstract base class for wrapping npm packages for the browser."""

    def __init__(self, package_dir: Path, package_name: str, package_json: Dict[str, Any]):
        self.package_dir = package_dir
        self.package_name = package_name
        self.package_json = package_json

    @abstractmethod
    def wrap(self) -> str:
        """Transform the package code into browser-compatible JavaScript."""
        pass

    def _find_entry_file(self) -> Path:
        """Find the entry file based on package.json fields."""
        candidates = [
            self.package_json.get("module"),
            self.package_json.get("browser"),
            self.package_json.get("main"),
            "index.js"
        ]
        
        for candidate in candidates:
            if candidate and isinstance(candidate, str):
                candidate = candidate.lstrip("./")
                entry_path = self.package_dir / candidate
                if entry_path.exists() and entry_path.is_file():
                    return entry_path
                    
        raise FileNotFoundError(
            f"Could not find entry file for '{self.package_name}'."
        )

    def _window_name(self) -> str:
        """Convert the package name to a safe JavaScript identifier."""
        return (
            self.package_name
            .replace("@", "")
            .replace("/", "_")
            .replace("-", "_")
            .replace(".", "_")
        )