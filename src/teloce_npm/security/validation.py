"""
Validation of untrusted names, versions and URLs.

Package names, version strings and tarball URLs come from user config, from
registry responses and (for bundler dependencies) from package code. They end
up in file paths, URLs and generated JavaScript, so they are validated at the
points where they enter the system.
"""

import ipaddress
import re
from collections.abc import Iterable
from typing import Optional
from urllib.parse import urlparse

from teloce_npm.utils.errors import SecurityError

# npm names: lowercase for new packages, but legacy packages (JSONStream,
# Base64, ...) contain capitals. Scoped names are `@scope/name`.
_NAME_RE = re.compile(r"^(?:@[A-Za-z0-9][A-Za-z0-9._~-]*/)?[A-Za-z0-9][A-Za-z0-9._~-]*$")
_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
_RESERVED_NAMES = frozenset({"node_modules", "favicon.ico"})
MAX_NAME_LENGTH = 214
MAX_VERSION_LENGTH = 256


def validate_package_name(name: object) -> str:
    """Return `name` if it is a well-formed npm package name, else raise SecurityError."""
    if (
        not isinstance(name, str)
        or not name
        or len(name) > MAX_NAME_LENGTH
        or not _NAME_RE.fullmatch(name)
        or name.split("/")[-1] in _RESERVED_NAMES
    ):
        raise SecurityError(f"Invalid npm package name: {str(name)[:80]!r}")
    return name


def validate_version(version: object) -> str:
    """Return `version` if it is a concrete semver version, else raise SecurityError."""
    if (
        not isinstance(version, str)
        or len(version) > MAX_VERSION_LENGTH
        or not _VERSION_RE.fullmatch(version)
    ):
        raise SecurityError(f"Invalid package version: {str(version)[:80]!r}")
    return version


def _is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def host_of(url: str) -> str:
    """Lower-cased host name of a URL ('' if it has none)."""
    return (urlparse(url).hostname or "").lower()


def validate_url(url: object, allowed_hosts: Optional[Iterable[str]] = None, *, what: str = "URL") -> str:
    """
    Check that `url` is https (http is only accepted for loopback hosts such as
    a local mirror), carries no credentials, and, if `allowed_hosts` is given,
    points at one of those hosts.
    """
    if not isinstance(url, str) or not url:
        raise SecurityError(f"Missing {what}.")
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if not host:
        raise SecurityError(f"{what} has no host: {url[:120]!r}")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and _is_loopback(host)):
        raise SecurityError(f"{what} must use https: {url[:120]!r}")
    if parsed.username or parsed.password:
        raise SecurityError(f"{what} must not contain credentials: {host}")
    if allowed_hosts is not None and host not in {h.lower() for h in allowed_hosts}:
        raise SecurityError(
            f"{what} points at '{host}', which is not an allowed registry host. "
            f"Allowed: {', '.join(sorted(h.lower() for h in allowed_hosts))}. "
            "Add the registry to security.allowed_registries if you trust it."
        )
    return url
