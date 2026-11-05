"""
Download npm tarballs securely and verify their integrity.

Safety properties:
  * only https (or loopback) URLs, optionally restricted to allowed hosts,
    re-checked on every redirect hop;
  * a hard cap on the download size;
  * the file is written to a temporary name, verified, and only then moved to
    its final path, so a partial or tampered download is never left behind;
  * transient failures (timeouts, 429/5xx) are retried with backoff.
"""

import base64
import hashlib
import os
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Optional

import requests

from teloce_npm.security.validation import validate_url
from teloce_npm.utils import retry
from teloce_npm.utils.errors import RegistryError, SecurityError
from teloce_npm.utils.file_io import ensure_dir
from teloce_npm.utils.logging import logger

DEFAULT_MAX_BYTES = 100 * 1024 * 1024
MAX_REDIRECTS = 5
_REDIRECT_STATUS = (301, 302, 303, 307, 308)
_CONNECT_READ_TIMEOUT = (10, 30)


def _sha512_tokens(integrity: str) -> list[str]:
    """Return the sha512 SRI tokens in `integrity` (npm may list several hashes)."""
    tokens = [t for t in integrity.split() if t.startswith("sha512-")]
    if not tokens:
        algorithm = integrity.split("-", 1)[0] if "-" in integrity else "unknown"
        raise SecurityError(
            f"Unsupported integrity algorithm '{algorithm}': a sha512 hash is required."
        )
    return tokens


def download_tarball(
    tarball_url: str,
    dest_path: Path,
    expected_integrity: str,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    allowed_hosts: Optional[Iterable[str]] = None,
    attempts: int = retry.DEFAULT_ATTEMPTS,
) -> Path:
    """
    Download a tarball and verify its SHA-512 integrity before keeping it.

    Raises:
        RegistryError: If the download fails (after retries).
        SecurityError: If the URL is not allowed, the file is too large, or the
            integrity check fails.
    """
    hosts = list(allowed_hosts) if allowed_hosts is not None else None
    validate_url(tarball_url, hosts, what="Tarball URL")
    expected = _sha512_tokens(expected_integrity)

    ensure_dir(dest_path.parent)
    last_error: Optional[Exception] = None

    for attempt in range(max(1, attempts)):
        if attempt:
            retry.sleep(retry.backoff_delay(attempt - 1, getattr(last_error, "retry_after", None)))
        try:
            return _download_once(tarball_url, dest_path, expected, max_bytes, hosts)
        except _Retryable as error:
            last_error = error
            logger.debug(f"Retrying download of {tarball_url} ({error})")
        except requests.exceptions.RequestException as error:
            last_error = error
            if not isinstance(
                error,
                (
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.ChunkedEncodingError,
                ),
            ):
                break
            logger.debug(f"Retrying download of {tarball_url} ({error})")

    raise RegistryError(f"Failed to download {tarball_url}: {last_error}") from last_error


class _Retryable(Exception):
    """A transient HTTP failure (429/5xx)."""

    def __init__(self, status: int, retry_after: Optional[str] = None):
        super().__init__(f"HTTP {status}")
        self.retry_after = retry_after


def _download_once(
    url: str,
    dest_path: Path,
    expected: list[str],
    max_bytes: int,
    allowed_hosts: Optional[list[str]],
) -> Path:
    fd, temp_name = tempfile.mkstemp(dir=dest_path.parent, prefix=f".{dest_path.name}.", suffix=".part")
    temp_path = Path(temp_name)
    try:
        hasher = hashlib.sha512()
        total = 0
        current = url
        with os.fdopen(fd, "wb") as out:
            for _hop in range(MAX_REDIRECTS + 1):
                with requests.get(
                    current,
                    stream=True,
                    timeout=_CONNECT_READ_TIMEOUT,
                    allow_redirects=False,
                    headers={"Accept-Encoding": "identity"},
                ) as response:
                    if response.status_code in _REDIRECT_STATUS:
                        location = response.headers.get("Location")
                        current = validate_url(
                            requests.compat.urljoin(current, str(location)),
                            allowed_hosts,
                            what="Redirect target",
                        )
                        continue
                    if response.status_code in retry.RETRYABLE_STATUS:
                        raise _Retryable(response.status_code, response.headers.get("Retry-After"))
                    response.raise_for_status()

                    declared = response.headers.get("Content-Length")
                    if isinstance(declared, str) and declared.isdigit() and int(declared) > max_bytes:
                        raise SecurityError(
                            f"Tarball is {int(declared)} bytes, over the {max_bytes} byte limit: {url}"
                        )
                    for chunk in response.iter_content(chunk_size=64 * 1024):
                        if not chunk:
                            continue
                        total += len(chunk)
                        if total > max_bytes:
                            raise SecurityError(f"Tarball exceeds the {max_bytes} byte limit: {url}")
                        out.write(chunk)
                        hasher.update(chunk)
                    break
            else:
                raise RegistryError(f"Too many redirects while downloading {url}")

        computed = "sha512-" + base64.b64encode(hasher.digest()).decode("ascii")
        if computed not in expected:
            raise SecurityError(
                f"Integrity check failed for {url}\n"
                f"Expected: {' '.join(expected)}\n"
                f"Computed: {computed}"
            )
        os.replace(temp_path, dest_path)
        logger.debug(f"Successfully downloaded and verified {dest_path.name}")
        return dest_path
    finally:
        # Never leave a partial or unverified file behind.
        if temp_path.exists():
            temp_path.unlink()
