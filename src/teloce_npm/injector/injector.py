"""
Core marker-based HTML injection logic.
"""

import re
from pathlib import Path

from teloce_npm.utils.file_io import read_file, write_file_atomic
from teloce_npm.utils.logging import logger

START_MARKER = "<!-- TELOCE-NPM-START -->"
END_MARKER = "<!-- TELOCE-NPM-END -->"


def inject_scripts(entry_html_path: Path, scripts_html: str) -> None:
    """
    Inject the script tags into the entry HTML file safely.

    Args:
        entry_html_path: The path to the entry HTML file.
        scripts_html: The string of <script> tags to inject.
    """
    content = read_file(entry_html_path)

    # 1. Remove any existing injected block first (idempotency)
    content = _remove_block(content)

    # 2. Wrap the new scripts in markers
    block = f"\n{START_MARKER}\n{scripts_html}\n{END_MARKER}\n"

    # 3. Determine the best injection point
    if "</head>" in content:
        logger.debug("Injecting before </head>")
        content = content.replace("</head>", f"{block}</head>", 1)
    elif "</body>" in content:
        logger.debug("Injecting before </body>")
        content = content.replace("</body>", f"{block}</body>", 1)
    else:
        logger.debug("Appending to end of file (no </head> or </body> found)")
        content += block

    # 4. Write atomically
    write_file_atomic(entry_html_path, content)
    logger.info(f"Injected Teloce-NPM scripts into {entry_html_path.name}")


def remove_scripts(entry_html_path: Path) -> None:
    """
    Remove previously injected script tags from the entry HTML file.

    Args:
        entry_html_path: The path to the entry HTML file.
    """
    if not entry_html_path.exists():
        return

    content = read_file(entry_html_path)
    new_content = _remove_block(content)

    if content != new_content:
        write_file_atomic(entry_html_path, new_content)
        logger.info(f"Removed Teloce-NPM scripts from {entry_html_path.name}")


def _remove_block(content: str) -> str:
    """
    Remove the marker block from the content using regex.
    """
    pattern = f"\\n?{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}\\n?"
    # Use DOTALL to match across multiple lines
    return re.sub(pattern, "", content, flags=re.DOTALL)
