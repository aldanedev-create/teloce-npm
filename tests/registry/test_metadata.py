"""
Tests for teloce_npm.registry.metadata.extract_version_data.

Scope: pure JSON parsing, no I/O, no HTTP.
"""

import pytest

from teloce_npm.registry import extract_version_data
from teloce_npm.utils.errors import PackageNotFoundError


SAMPLE_METADATA = {
    "name": "test-pkg",
    "dist-tags": {"latest": "2.0.0"},
    "versions": {
        "1.0.0": {
            "name": "test-pkg",
            "version": "1.0.0",
            "description": "first",
            "dist": {
                "tarball": "https://reg.example.com/test-pkg-1.0.0.tgz",
                "integrity": "sha512-v1",
            },
            "dependencies": {},
            "scripts": {},
        },
        "2.0.0": {
            "name": "test-pkg",
            "version": "2.0.0",
            "description": "second",
            "dist": {
                "tarball": "https://reg.example.com/test-pkg-2.0.0.tgz",
                "integrity": "sha512-v2",
            },
            "dependencies": {"lodash": "^4.0.0"},
            "scripts": {"postinstall": "echo hi"},
        },
    },
}


def test_extract_version_data_returns_expected_fields():
    data = extract_version_data(SAMPLE_METADATA, "2.0.0")

    assert data["name"] == "test-pkg"
    assert data["version"] == "2.0.0"
    assert data["tarball_url"] == "https://reg.example.com/test-pkg-2.0.0.tgz"
    assert data["integrity"] == "sha512-v2"
    assert data["description"] == "second"


def test_extract_version_data_includes_dependencies():
    data = extract_version_data(SAMPLE_METADATA, "2.0.0")
    assert data["dependencies"] == {"lodash": "^4.0.0"}


def test_extract_version_data_includes_scripts():
    data = extract_version_data(SAMPLE_METADATA, "2.0.0")
    assert data["scripts"] == {"postinstall": "echo hi"}


def test_extract_version_data_empty_deps_and_scripts():
    data = extract_version_data(SAMPLE_METADATA, "1.0.0")
    assert data["dependencies"] == {}
    assert data["scripts"] == {}


def test_extract_version_data_missing_version_raises():
    with pytest.raises(PackageNotFoundError, match="9.9.9"):
        extract_version_data(SAMPLE_METADATA, "9.9.9")


def test_extract_version_data_missing_tarball_raises():
    metadata = {
        "name": "x",
        "versions": {"1.0.0": {"dist": {"integrity": "sha512-x"}}},
    }
    with pytest.raises(ValueError, match="tarball"):
        extract_version_data(metadata, "1.0.0")


def test_extract_version_data_missing_integrity_raises():
    metadata = {
        "name": "x",
        "versions": {"1.0.0": {"dist": {"tarball": "https://x"}}},
    }
    with pytest.raises(ValueError, match="integrity"):
        extract_version_data(metadata, "1.0.0")


def test_extract_version_data_empty_versions_dict_raises():
    with pytest.raises(PackageNotFoundError):
        extract_version_data({"name": "x", "versions": {}}, "1.0.0")