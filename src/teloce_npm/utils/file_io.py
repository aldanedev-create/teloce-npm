"""
Safe and atomic file read/write operations.
"""

import os
import tempfile
from pathlib import Path
from .errors import TeloceNpmError

def read_file(path: Path) -> str:
    """
    Read a file as UTF-8 text.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_text(encoding="utf-8")

def write_file_atomic(path: Path, content: str) -> None:
    """
    Write text to a file safely using an atomic operation.
    
    This prevents file corruption if the process crashes mid-write.
    It writes to a temporary file first, then replaces the original.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a temporary file in the same directory (to ensure same filesystem)
    fd, temp_path_str = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temp_path = Path(temp_path_str)
    
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        # Atomically replace the original file
        temp_path.replace(path)
    except Exception as e:
        # Clean up the temp file if something goes wrong
        if temp_path.exists():
            temp_path.unlink()
        raise TeloceNpmError(f"Failed to write file {path}: {e}")

def ensure_dir(path: Path) -> None:
    """
    Ensure a directory exists.
    """
    path.mkdir(parents=True, exist_ok=True)