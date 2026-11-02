"""
Tests for teloce_npm.version.

Verifies that version metadata constants are present, correctly formatted,
and internally consistent.
"""

import pytest

from teloce_npm.version import (
    VERSION,
    VERSION_INFO,
    __author__,  # noqa: F401
    __email__,  # noqa: F401
    __license__,  # noqa: F401
    __url__,  # noqa: F401
    __version__,
)


def test_version_is_string():
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_version_is_semver_like():
    """Version must look like X.Y.Z (possibly with suffix)."""
    parts = __version__.split(".")
    assert len(parts) >= 3, f"Expected at least 3 version parts, got {__version__}"


def test_version_matches_module_constant():
    assert __version__ == VERSION


def test_version_info_is_tuple_of_ints():
    assert isinstance(VERSION_INFO, tuple)
    assert len(VERSION_INFO) >= 3
    for part in VERSION_INFO:
        assert isinstance(part, int)


def test_version_info_matches_version():
    """VERSION_INFO must match the major.minor.patch of __version__."""
    parts = __version__.split(".")
    for i, expected_part in enumerate(VERSION_INFO[:3]):
        assert expected_part == int(parts[i])


@pytest.mark.parametrize("attr", ["__author__", "__email__", "__license__", "__url__"])
def test_metadata_is_non_empty_string(attr):
    value = globals()[attr]
    assert isinstance(value, str)
    assert len(value) > 0
