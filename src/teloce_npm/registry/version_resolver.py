"""
Resolve npm version ranges (e.g., '^1.0.0', 'latest') to specific versions.
"""

import re
from typing import Any, Optional

import semver

from teloce_npm.utils.errors import PackageNotFoundError
from teloce_npm.utils.logging import logger


def resolve_version(raw_metadata: dict[str, Any], requested_range: str) -> str:
    """
    Resolve a requested version range to the highest matching specific version.

    Args:
        raw_metadata: The full JSON response from the registry.
        requested_range: The version requested by the user (e.g., 'latest', '^1.0.0', '4.17.21').

    Returns:
        The specific version string (e.g., '4.17.21').
    """
    versions_dict = raw_metadata.get("versions", {})
    dist_tags = raw_metadata.get("dist-tags", {})
    package_name = raw_metadata.get("name", "unknown")

    # 1. Handle 'latest' or empty string
    if requested_range in ("latest", "", None):
        latest = dist_tags.get("latest")
        if not isinstance(latest, str) or not latest:
            raise PackageNotFoundError(f"No 'latest' tag found for package '{package_name}'.")
        return latest

    # 1b. Handle other dist-tags (e.g., 'next', 'beta')
    if requested_range in dist_tags and requested_range not in versions_dict:
        return str(dist_tags[requested_range])

    # 2. Handle exact match (e.g., '4.17.21')
    if requested_range in versions_dict:
        return requested_range

    # 3. Handle SemVer ranges (e.g., '^1.0.0')
    # We filter out pre-release versions (like 1.0.0-beta) unless explicitly requested
    valid_versions = []
    for v in versions_dict:
        if semver.VersionInfo.is_valid(v) and not semver.VersionInfo.parse(v).prerelease:
            valid_versions.append(v)

    try:
        # Find all versions that satisfy the range
        matching_versions = [v for v in valid_versions if _matches_range(v, requested_range)]

        if not matching_versions:
            raise PackageNotFoundError(
                f"No versions of '{package_name}' match the range '{requested_range}'."
            )

        # Return the highest matching version
        highest_version = str(max(matching_versions, key=lambda v: semver.VersionInfo.parse(v)))
        logger.debug(f"Resolved {package_name}@{requested_range} to {highest_version}")
        return highest_version

    except ValueError as e:
        raise PackageNotFoundError(
            f"Invalid version range '{requested_range}' for '{package_name}': {e}"
        ) from e


_PARTIAL_RE = re.compile(
    r"^[v=]*(\d+|[xX*])(?:\.(\d+|[xX*]))?(?:\.(\d+|[xX*]))?(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
_OPERATOR_SPACE_RE = re.compile(r"(>=|<=|>|<|=|~>|~|\^)\s+")

_Triple = tuple[int, int, int]
_Comparator = tuple[str, _Triple]


def _matches_range(version: str, requested_range: str) -> bool:
    """
    Match a version against an npm-style range.

    Supports exact versions, comparators (`>=1.2.3 <2`), caret and tilde
    ranges (including partials such as `^1.2` and `~1`), X-ranges (`1.x`,
    `1.2`, `*`), hyphen ranges (`1.2 - 2.3`) and `||` unions. Pre-release
    versions are filtered out before matching (see `resolve_version`).
    """
    parsed = semver.VersionInfo.parse(version)
    candidate: _Triple = (parsed.major, parsed.minor, parsed.patch)

    for alternative in requested_range.split("||"):
        comparators = _parse_comparator_set(alternative)
        if all(_compare(candidate, op, bound) for op, bound in comparators):
            return True
    return False


def _compare(candidate: _Triple, op: str, bound: _Triple) -> bool:
    if op == ">=":
        return candidate >= bound
    if op == ">":
        return candidate > bound
    if op == "<=":
        return candidate <= bound
    if op == "<":
        return candidate < bound
    return candidate == bound


def _parse_partial(text: str) -> tuple[Optional[int], Optional[int], Optional[int]]:
    """Parse `1`, `1.2`, `1.2.3`, `1.x`, `*` into (major, minor, patch); None = wildcard."""
    match = _PARTIAL_RE.match(text.strip())
    if not match:
        raise ValueError(f"{text.strip()!r} is not a valid version range")
    parts = [None if (g is None or g in "xX*") else int(g) for g in match.groups()]
    # A wildcard makes everything after it a wildcard too (1.x.3 -> 1.x.x).
    for index in range(1, 3):
        if parts[index - 1] is None:
            parts[index] = None
    return parts[0], parts[1], parts[2]


def _floor(partial: tuple[Optional[int], Optional[int], Optional[int]]) -> _Triple:
    return (partial[0] or 0, partial[1] or 0, partial[2] or 0)


def _ceiling(partial: tuple[Optional[int], Optional[int], Optional[int]]) -> Optional[_Triple]:
    """Exclusive upper bound of everything a partial version covers (None = unbounded)."""
    major, minor, patch = partial
    if major is None:
        return None
    if minor is None:
        return (major + 1, 0, 0)
    if patch is None:
        return (major, minor + 1, 0)
    return (major, minor, patch + 1)


def _parse_comparator_set(text: str) -> list[_Comparator]:
    text = text.strip()
    if " - " in text:
        low_text, high_text = text.split(" - ", 1)
        low, high = _parse_partial(low_text), _parse_partial(high_text)
        comparators: list[_Comparator] = [(">=", _floor(low))]
        if high[2] is not None:
            comparators.append(("<=", _floor(high)))
        else:
            ceiling = _ceiling(high)
            if ceiling is not None:
                comparators.append(("<", ceiling))
        return comparators

    comparators = []
    for token in _OPERATOR_SPACE_RE.sub(r"\1", text).split():
        comparators.extend(_parse_token(token))
    return comparators


def _parse_token(token: str) -> list[_Comparator]:
    operator_match = re.match(r"^(>=|<=|>|<|=|~>|~|\^)?(.*)$", token)
    assert operator_match is not None  # the pattern matches any string
    operator, rest = operator_match.group(1) or "", operator_match.group(2)
    partial = _parse_partial(rest)
    major, minor, patch = partial

    if major is None:  # `*`, `x`, `>=*` ...
        return []

    if operator in ("", "="):
        ceiling = _ceiling(partial)
        assert ceiling is not None
        if patch is not None:
            return [("=", (major, minor or 0, patch))]
        return [(">=", _floor(partial)), ("<", ceiling)]

    if operator in ("~", "~>"):
        ceiling = (major + 1, 0, 0) if minor is None else (major, minor + 1, 0)
        return [(">=", _floor(partial)), ("<", ceiling)]

    if operator == "^":
        if major > 0 or minor is None:
            ceiling = (major + 1, 0, 0)
        elif minor > 0 or patch is None:
            ceiling = (0, minor + 1, 0)
        else:
            ceiling = (0, 0, patch + 1)
        return [(">=", _floor(partial)), ("<", ceiling)]

    ceiling = _ceiling(partial)
    assert ceiling is not None
    if operator == ">=":
        return [(">=", _floor(partial))]
    if operator == ">":
        return [(">=", ceiling)] if patch is None else [(">", _floor(partial))]
    if operator == "<":
        return [("<", _floor(partial))]
    # "<="
    return [("<", ceiling)] if patch is None else [("<=", _floor(partial))]
