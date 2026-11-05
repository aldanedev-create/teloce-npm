"""npm-style version range matching (partials, x-ranges, hyphen, unions)."""

import pytest

from teloce_npm.registry.version_resolver import _matches_range, resolve_version
from teloce_npm.utils.errors import PackageNotFoundError

CASES = [
    # partial versions / x-ranges
    ("3.2.4", "3", True), ("4.0.0", "3", False), ("3.9.9", "3.x", True),
    ("3.2.4", "3.2", True), ("3.3.0", "3.2", False), ("3.2.9", "3.2.x", True),
    # caret
    ("1.2.3", "^1.2", True), ("2.0.0", "^1.2", False), ("0.2.9", "^0.2.3", True),
    ("0.3.0", "^0.2.3", False), ("0.0.3", "^0.0.3", True), ("0.0.4", "^0.0.3", False),
    ("0.9.0", "^0", True), ("1.0.0", "^0", False),
    # tilde
    ("1.2.9", "~1.2.3", True), ("1.3.0", "~1.2.3", False),
    ("1.9.0", "~1", True), ("2.0.0", "~1", False),
    # comparators
    ("1.5.0", ">=1.2.3 <2", True), ("2.0.0", ">=1.2.3 <2", False), ("1.2.2", ">= 1.2.3", False),
    ("3.0.0", ">2", True), ("2.9.0", ">2", False), ("2.9.0", "<=2", True), ("3.0.0", "<=2", False),
    # hyphen ranges
    ("2.5.0", "1 - 2", True), ("3.0.0", "1 - 2", False),
    ("1.2.3", "1.2.3 - 2.3.4", True), ("2.3.5", "1.2.3 - 2.3.4", False), ("2.3.9", "1.2 - 2.3", True),
    # unions / wildcards / exact
    ("1.0.5", "1.0.x || 2.x", True), ("2.4.0", "1.0.x || 2.x", True), ("1.1.0", "1.0.x || 2.x", False),
    ("9.9.9", "*", True), ("0.0.1", "", True),
    ("1.2.3", "1.2.3", True), ("1.2.4", "=1.2.3", False), ("1.2.3", "v1.2.3", True),
]


@pytest.mark.parametrize("version,spec,expected", CASES)
def test_matches_range(version, spec, expected):
    assert _matches_range(version, spec) is expected


def test_resolve_bare_major_picks_highest_in_major():
    metadata = {"name": "d3-array", "versions": {v: {} for v in ["2.9.0", "3.0.0", "3.2.4", "4.0.0"]}}
    assert resolve_version(metadata, "3") == "3.2.4"


def test_resolve_custom_dist_tag():
    metadata = {"name": "p", "versions": {"1.0.0": {}, "2.0.0-beta.1": {}}, "dist-tags": {"next": "2.0.0-beta.1"}}
    assert resolve_version(metadata, "next") == "2.0.0-beta.1"


def test_resolve_garbage_range_raises():
    with pytest.raises(PackageNotFoundError):
        resolve_version({"name": "p", "versions": {"1.0.0": {}}}, "not a range!")
