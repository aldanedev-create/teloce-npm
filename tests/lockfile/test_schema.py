"""
Tests for teloce_npm.lockfile.schema.

Scope: only the pure functions (empty_lockfile, make_package_entry,
validate_lockfile, get_package_versions).
Does NOT test LockfileManager (that's test_manager.py).
"""

import pytest

from teloce_npm.lockfile.schema import (
    empty_lockfile,
    make_package_entry,
    validate_lockfile,
    get_package_versions,
    LOCKFILE_VERSION,
)


# ---------------------------------------------------------------------------
# empty_lockfile()
# ---------------------------------------------------------------------------
def test_empty_lockfile_has_version():
    lock = empty_lockfile()
    assert lock["lockfile_version"] == LOCKFILE_VERSION


def test_empty_lockfile_has_generated_at():
    lock = empty_lockfile()
    assert "generated_at" in lock
    assert isinstance(lock["generated_at"], str)


def test_empty_lockfile_has_empty_packages():
    assert empty_lockfile()["packages"] == {}


def test_empty_lockfiles_are_independent():
    """Each call must return a fresh dict (no shared mutable state)."""
    a = empty_lockfile()
    b = empty_lockfile()
    a["packages"]["foo"] = {}
    assert b["packages"] == {}


# ---------------------------------------------------------------------------
# make_package_entry()
# ---------------------------------------------------------------------------
def test_make_package_entry_includes_all_keys():
    entry = make_package_entry(
        version="4.17.21",
        resolved_url="https://reg.example.com/lodash-4.17.21.tgz",
        integrity="sha512-abc",
        wrapped_filename="lodash.js",
        size=1024,
    )

    for key in ("version", "resolved", "integrity", "dependencies",
                "wrapped", "size", "scanned_at", "scan_result"):
        assert key in entry


def test_make_package_entry_defaults():
    entry = make_package_entry("1.0.0", "https://x", "sha512-x", "pkg.js", 100)
    assert entry["dependencies"] == {}
    assert entry["scan_result"] == "clean"


def test_make_package_entry_preserves_values():
    entry = make_package_entry(
        version="4.17.21",
        resolved_url="https://reg.example.com/p.tgz",
        integrity="sha512-xyz",
        wrapped_filename="lodash.js",
        size=2048,
        dependencies={"dayjs": "^1.0.0"},
        scan_result="warnings",
    )
    assert entry["version"] == "4.17.21"
    assert entry["integrity"] == "sha512-xyz"
    assert entry["size"] == 2048
    assert entry["dependencies"] == {"dayjs": "^1.0.0"}
    assert entry["scan_result"] == "warnings"


# ---------------------------------------------------------------------------
# validate_lockfile()
# ---------------------------------------------------------------------------
def test_validate_empty_lockfile_passes():
    validate_lockfile(empty_lockfile())


def test_validate_missing_lockfile_version_raises():
    with pytest.raises(Exception, match="lockfile_version"):
        validate_lockfile({"packages": {}})


def test_validate_wrong_version_raises():
    with pytest.raises(Exception, match="Unsupported"):
        validate_lockfile({"lockfile_version": "9.9.9", "packages": {}})


def test_validate_missing_packages_raises():
    with pytest.raises(Exception, match="packages"):
        validate_lockfile({"lockfile_version": LOCKFILE_VERSION})


def test_validate_non_dict_packages_raises():
    with pytest.raises(Exception, match="packages"):
        validate_lockfile({
            "lockfile_version": LOCKFILE_VERSION,
            "packages": "not-a-dict",
        })


def test_validate_entry_missing_required_key_raises():
    lock = empty_lockfile()
    lock["packages"]["lodash"] = {
        "version": "4.17.21",
        # missing: resolved, integrity, wrapped, size
    }
    with pytest.raises(Exception, match="missing"):
        validate_lockfile(lock)


def test_validate_entry_non_int_size_raises():
    lock = empty_lockfile()
    lock["packages"]["lodash"] = {
        "version": "4.17.21",
        "resolved": "https://x",
        "integrity": "sha512-x",
        "wrapped": "lodash.js",
        "size": "not-an-int",
    }
    with pytest.raises(Exception, match="size"):
        validate_lockfile(lock)


def test_validate_entry_bad_integrity_prefix_raises():
    lock = empty_lockfile()
    lock["packages"]["lodash"] = {
        "version": "4.17.21",
        "resolved": "https://x",
        "integrity": "md5-not-sha512",
        "wrapped": "lodash.js",
        "size": 100,
    }
    with pytest.raises(Exception, match="SHA-512"):
        validate_lockfile(lock)


def test_validate_valid_package_entry_passes():
    lock = empty_lockfile()
    lock["packages"]["lodash"] = make_package_entry(
        "4.17.21", "https://x", "sha512-abc", "lodash.js", 100
    )
    validate_lockfile(lock)  # should not raise


# ---------------------------------------------------------------------------
# get_package_versions()
# ---------------------------------------------------------------------------
def test_get_package_versions_empty():
    assert get_package_versions(empty_lockfile()) == {}


def test_get_package_versions_returns_name_version_map():
    lock = empty_lockfile()
    lock["packages"]["lodash"] = make_package_entry(
        "4.17.21", "https://x", "sha512-a", "lodash.js", 1
    )
    lock["packages"]["dayjs"] = make_package_entry(
        "1.11.0", "https://y", "sha512-b", "dayjs.js", 2
    )

    assert get_package_versions(lock) == {
        "lodash": "4.17.21",
        "dayjs": "1.11.0",
    }