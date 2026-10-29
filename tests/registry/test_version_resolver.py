"""
Tests for teloce_npm.registry.version_resolver.resolve_version.

Scope: pure SemVer logic, no I/O.
"""

import pytest

from teloce_npm.registry import resolve_version
from teloce_npm.utils.errors import PackageNotFoundError


def _metadata(versions, latest=None):
    return {
        "name": "test-pkg",
        "dist-tags": {"latest": latest} if latest else {},
        "versions": {v: {"name": "test-pkg", "version": v} for v in versions},
    }


# ---------------------------------------------------------------------------
# 'latest' resolution
# ---------------------------------------------------------------------------
def test_resolve_latest_tag():
    meta = _metadata(["1.0.0", "1.5.0", "2.0.0"], latest="2.0.0")
    assert resolve_version(meta, "latest") == "2.0.0"


def test_resolve_empty_string_as_latest():
    meta = _metadata(["1.0.0", "2.0.0"], latest="2.0.0")
    assert resolve_version(meta, "") == "2.0.0"


def test_resolve_none_as_latest():
    meta = _metadata(["1.0.0", "2.0.0"], latest="2.0.0")
    assert resolve_version(meta, None) == "2.0.0"


def test_resolve_latest_with_no_tag_raises():
    meta = _metadata(["1.0.0"])  # no dist-tags.latest
    with pytest.raises(PackageNotFoundError, match="latest"):
        resolve_version(meta, "latest")


# ---------------------------------------------------------------------------
# Exact match
# ---------------------------------------------------------------------------
def test_resolve_exact_version():
    meta = _metadata(["1.0.0", "1.5.0", "2.0.0"], latest="2.0.0")
    assert resolve_version(meta, "1.5.0") == "1.5.0"


def test_resolve_exact_prerelease():
    meta = _metadata(["1.0.0", "2.0.0-beta.1"], latest="1.0.0")
    assert resolve_version(meta, "2.0.0-beta.1") == "2.0.0-beta.1"


# ---------------------------------------------------------------------------
# Caret (^) ranges
# ---------------------------------------------------------------------------
def test_resolve_caret_range_picks_highest_compatible():
    meta = _metadata(["1.0.0", "1.5.0", "1.9.3", "2.0.0"], latest="2.0.0")
    assert resolve_version(meta, "^1.0.0") == "1.9.3"


def test_resolve_caret_range_does_not_cross_major():
    meta = _metadata(["1.0.0", "2.0.0"], latest="2.0.0")
    # ^2.0.0 must not return 3.x or 1.x (only 2.x available here)
    assert resolve_version(meta, "^2.0.0") == "2.0.0"


# ---------------------------------------------------------------------------
# Tilde (~) ranges
# ---------------------------------------------------------------------------
def test_resolve_tilde_range_picks_highest_minor():
    meta = _metadata(["1.2.0", "1.2.5", "1.3.0", "2.0.0"], latest="2.0.0")
    assert resolve_version(meta, "~1.2.0") == "1.2.5"


# ---------------------------------------------------------------------------
# Excludes prereleases by default
# ---------------------------------------------------------------------------
def test_resolve_range_ignores_prerelease():
    meta = _metadata(
        ["1.0.0", "1.5.0", "1.9.0-beta.1"],
        latest="1.0.0",
    )
    # ^1.0.0 must pick 1.5.0, NOT 1.9.0-beta.1
    assert resolve_version(meta, "^1.0.0") == "1.5.0"


def test_resolve_range_with_only_prereleases_raises():
    meta = _metadata(["1.0.0-beta.1", "1.0.0-rc.2"], latest="1.0.0-beta.1")
    with pytest.raises(PackageNotFoundError, match="No versions"):
        resolve_version(meta, "^1.0.0")


# ---------------------------------------------------------------------------
# No match
# ---------------------------------------------------------------------------
def test_resolve_no_match_raises():
    meta = _metadata(["1.0.0"], latest="1.0.0")
    with pytest.raises(PackageNotFoundError, match="No versions"):
        resolve_version(meta, "^5.0.0")


def test_resolve_invalid_range_raises():
    meta = _metadata(["1.0.0"], latest="1.0.0")
    with pytest.raises(PackageNotFoundError):
        resolve_version(meta, "not-a-range")