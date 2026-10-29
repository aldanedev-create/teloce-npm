"""
Locate the entry HTML file from configuration.
"""

from pathlib import Path
from teloce_npm.utils.errors import ConfigError
from teloce_npm.utils.logging import logger

def get_entry_html(entry_html_path: Path) -> Path:
    """
    Verify and return the configured entry HTML file.
    
    Args:
        entry_html_path: The absolute path resolved from config.
        
    Returns:
        The validated Path object.
        
    Raises:
        ConfigError: If the file does not exist or is not an HTML file.
    """
    if not entry_html_path.exists():
        raise ConfigError(
            f"Entry HTML file not found: {entry_html_path}\n"
            f"Please check the 'entry_html' setting in teloce-npm.json."
        )

    if not entry_html_path.is_file():
        raise ConfigError(
            f"Entry HTML path is not a file: {entry_html_path}"
        )

    if entry_html_path.suffix.lower() != ".html":
        logger.warning(
            f"Entry HTML file does not have a .html extension: {entry_html_path}"
        )

    logger.debug(f"Found entry HTML file: {entry_html_path}")
    return entry_html_path