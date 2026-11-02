"""
Safely extract npm tarballs.
"""

import shutil
import tarfile
from pathlib import Path

from teloce_npm.utils.errors import SecurityError, TeloceNpmError
from teloce_npm.utils.file_io import ensure_dir
from teloce_npm.utils.logging import logger


def extract_tarball(tarball_path: Path, extract_dir: Path) -> Path:
    """
    Extract a .tgz tarball safely.

    Args:
        tarball_path: Path to the downloaded .tgz file.
        extract_dir: The directory to extract the contents into.

    Returns:
        The path to the extracted package directory (usually `extract_dir/package`).
    """
    if not tarball_path.exists():
        raise TeloceNpmError(f"Tarball not found: {tarball_path}")

    # Ensure the extraction directory is clean
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    ensure_dir(extract_dir)

    logger.debug(f"Extracting {tarball_path.name} to {extract_dir}")

    try:
        with tarfile.open(tarball_path, "r:gz") as tar:
            # Security: Check for path traversal (Zip Slip vulnerability)
            for member in tar.getmembers():
                # Reject absolute paths or paths that try to go up directories
                if member.name.startswith("/") or ".." in member.name:
                    raise SecurityError(f"Unsafe path detected in tarball: {member.name}")

                # Reject symlinks and hard links to prevent attacks
                if member.issym() or member.islnk():
                    raise SecurityError(f"Symlinks are not allowed in npm tarballs: {member.name}")

            # Extract safely
            # Python 3.12+ has filter='data' for built-in safety,
            # but we do it manually above for older versions.
            tar.extractall(path=extract_dir)

        # npm tarballs always extract to a folder named "package"
        package_dir = extract_dir / "package"

        if not package_dir.exists():
            # Fallback: If it didn't use the standard "package" prefix, return the extract dir itself
            logger.warning(
                f"No 'package' folder found in {tarball_path.name}, using root extraction directory."
            )
            return extract_dir

        return package_dir

    except tarfile.TarError as e:
        raise TeloceNpmError(f"Failed to extract tarball {tarball_path}: {e}") from e
