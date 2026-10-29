"""
Walk project directories to find .vel and .html source files.
"""

from pathlib import Path
from typing import List, Set
from teloce_npm.utils.logging import logger

# Directories to always ignore
IGNORE_DIRS: Set[str] = {
    ".git",
    ".github",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    "__pycache__",
    ".teloce-npm",
    ".pytest_cache",
    ".idea",
    ".vscode",
}

# File extensions to scan
SOURCE_EXTENSIONS: Set[str] = {".vel", ".html"}

def find_source_files(root_dir: Path) -> List[Path]:
    """
    Recursively find all .vel and .html files in the given directory,
    ignoring common build and dependency folders.
    
    Args:
        root_dir: The root directory of the project.
        
    Returns:
        A list of absolute paths to the source files.
    """
    if not root_dir.exists():
        logger.error(f"Project root does not exist: {root_dir}")
        return []

    source_files: List[Path] = []
    
    for path in root_dir.rglob("*"):
        # Skip if it's a directory
        if not path.is_file():
            continue
            
        # Skip if the extension is not what we want
        if path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
            
        # Skip if any part of the path is in IGNORE_DIRS
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
            
        source_files.append(path)

    logger.debug(f"Found {len(source_files)} source files in {root_dir}")
    return source_files