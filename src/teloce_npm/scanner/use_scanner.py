"""
Extract Use declarations from .vel and .html files.
"""

import re
from pathlib import Path
from typing import List, Dict, Any
from teloce_npm.utils.file_io import read_file
from teloce_npm.utils.logging import logger
from .file_walker import find_source_files

# Regex to match lines like: 
# Use apple from teloce-npm
# Use @scope/package from teloce-npm
# Use lodash@^4.17.0 from teloce-npm (optional versioning in the future)
USE_PATTERN = re.compile(
    r"^\s*Use\s+([@a-zA-Z0-9_\-/\.]+)\s+from\s+teloce-npm\s*$", 
    re.IGNORECASE
)

def scan_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Scan a single file for Use declarations.
    
    Args:
        file_path: Path to the .vel or .html file.
        
    Returns:
        A list of dictionaries containing package name, file, and line number.
    """
    uses = []
    try:
        content = read_file(file_path)
    except Exception as e:
        logger.warning(f"Could not read file {file_path}: {e}")
        return uses

    for line_num, line in enumerate(content.splitlines(), start=1):
        match = USE_PATTERN.match(line)
        if match:
            package_name = match.group(1)
            uses.append({
                "package": package_name,
                "file": str(file_path),
                "line": line_num
            })
            
    return uses

def scan_project(root_dir: Path) -> List[Dict[str, Any]]:
    """
    Scan the entire project for Use declarations.
    
    Args:
        root_dir: The root directory of the project.
        
    Returns:
        A flat list of all Use declarations found.
    """
    all_uses = []
    source_files = find_source_files(root_dir)
    
    for file_path in source_files:
        # Skip the entry HTML file if it somehow contains Use declarations (it shouldn't)
        # We can scan it anyway; if it has no 'Use' lines, it will just return an empty list.
        uses = scan_file(file_path)
        all_uses.extend(uses)

    # Deduplicate while preserving the first occurrence for reporting
    # (The install command will handle unique package extraction later, 
    # but this keeps the output clean for logging).
    seen = set()
    unique_uses = []
    for use in all_uses:
        # Create a unique key based on package name and file
        key = (use["package"], use["file"])
        if key not in seen:
            seen.add(key)
            unique_uses.append(use)

    return unique_uses