"""
Safely extract npm tarballs.

Tarballs come from the network and are treated as hostile. Members are
extracted one by one (never with `extractall`) and only plain files and
directories are accepted. Limits on member count and size stop decompression
bombs, and every destination is checked to stay inside the extraction root.
"""

import shutil
import tarfile
import zlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Optional

from teloce_npm.utils.errors import SecurityError, TeloceNpmError
from teloce_npm.utils.file_io import ensure_dir
from teloce_npm.utils.logging import logger

_CHUNK = 64 * 1024


@dataclass(frozen=True)
class ExtractionLimits:
    """Upper bounds for one tarball. The defaults fit very large packages (Monaco, three)."""

    max_files: int = 50_000
    max_total_bytes: int = 500 * 1024 * 1024
    max_file_bytes: int = 100 * 1024 * 1024


def _safe_relative_path(name: str) -> Optional[PurePosixPath]:
    """
    Validate a tar member name and return it as a relative path (None for the
    archive root itself). Raises SecurityError for anything that could escape.
    """
    if "\x00" in name or "\\" in name or name.startswith("/"):
        raise SecurityError(f"Unsafe path detected in tarball: {name!r}")
    parts = [part for part in name.split("/") if part not in ("", ".")]
    if any(part == ".." for part in parts):
        raise SecurityError(f"Unsafe path detected in tarball: {name!r}")
    # Windows drive letters ("C:foo") are never valid in an npm tarball.
    if parts and len(parts[0]) >= 2 and parts[0][1] == ":":
        raise SecurityError(f"Unsafe path detected in tarball: {name!r}")
    return PurePosixPath(*parts) if parts else None


def extract_tarball(
    tarball_path: Path,
    extract_dir: Path,
    limits: Optional[ExtractionLimits] = None,
) -> Path:
    """
    Extract a .tgz tarball safely.

    Returns:
        The path to the extracted package directory (usually `extract_dir/package`).

    Raises:
        SecurityError: For path traversal, links, special files or limit violations.
        TeloceNpmError: For unreadable or corrupt archives.
    """
    limits = limits or ExtractionLimits()

    if not tarball_path.exists():
        raise TeloceNpmError(f"Tarball not found: {tarball_path}")

    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    ensure_dir(extract_dir)
    root = extract_dir.resolve()

    logger.debug(f"Extracting {tarball_path.name} to {extract_dir}")

    files = 0
    total = 0
    try:
        with tarfile.open(tarball_path, "r:gz") as tar:
            for member in tar:
                relative = _safe_relative_path(member.name)

                if member.issym() or member.islnk():
                    raise SecurityError(f"Symlinks are not allowed in npm tarballs: {member.name}")
                if not (member.isreg() or member.isdir()):
                    raise SecurityError(f"Unsupported file type in tarball: {member.name}")
                if relative is None:
                    continue

                destination = (root / relative).resolve()
                if not destination.is_relative_to(root):
                    raise SecurityError(f"Unsafe path detected in tarball: {member.name!r}")

                if member.isdir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue

                files += 1
                total += member.size
                if files > limits.max_files:
                    raise SecurityError(f"Tarball has more than {limits.max_files} files.")
                if member.size > limits.max_file_bytes:
                    raise SecurityError(
                        f"File {member.name} is {member.size} bytes, over the "
                        f"{limits.max_file_bytes} byte limit."
                    )
                if total > limits.max_total_bytes:
                    raise SecurityError(
                        f"Tarball unpacks to more than {limits.max_total_bytes} bytes."
                    )

                source = tar.extractfile(member)
                if source is None:
                    raise SecurityError(f"Could not read tarball member: {member.name}")
                destination.parent.mkdir(parents=True, exist_ok=True)
                with source, open(destination, "wb") as out:
                    while chunk := source.read(_CHUNK):
                        out.write(chunk)
                # Never keep setuid/setgid/sticky or group/other write bits.
                destination.chmod(0o755 if member.mode & 0o100 else 0o644)

        package_dir = extract_dir / "package"
        if not package_dir.exists():
            logger.warning(
                f"No 'package' folder found in {tarball_path.name}, using root extraction directory."
            )
            return extract_dir
        return package_dir

    except (tarfile.TarError, EOFError, OSError, zlib.error) as e:
        raise TeloceNpmError(f"Failed to extract tarball {tarball_path}: {e}") from e
