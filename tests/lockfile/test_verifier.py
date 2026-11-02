"""
Tests for teloce_npm.lockfile.verifier.LockfileVerifier.

Scope: verification behavior (verify_against_cache, verify_versions, is_valid, report).
Uses real LockfileManager and CacheManager in tmp_path.
"""

import pytest

from teloce_npm.cache.manager import CacheManager
from teloce_npm.lockfile.manager import LockfileManager
from teloce_npm.lockfile.verifier import LockfileVerifier
from teloce_npm.utils.errors import LockfileMismatch
from teloce_npm.utils.hashing import compute_sha512


def _setup_cached_package(
    cache, tmp_path, name, version, tarball_content, lockfile_integrity, wrapped="code"
):
    """Populate the cache with a package + tarball."""
    src = tmp_path / f"src_{name}_{version}"
    src.mkdir()
    (src / "package.json").write_text("{}")
    cache.store(
        package_name=name,
        version=version,
        extracted_dir=src,
        wrapped_code=wrapped,
        metadata={"integrity": lockfile_integrity, "tarball_url": "https://x"},
    )
    cache.storage.tarball_path(name, version).write_bytes(tarball_content)


@pytest.fixture
def setup(tmp_path):
    lockfile = LockfileManager(tmp_path)
    cache = CacheManager(tmp_path / "cache")
    verifier = LockfileVerifier(lockfile, cache)
    return lockfile, cache, verifier, tmp_path


# ---------------------------------------------------------------------------
# verify_against_cache — happy paths
# ---------------------------------------------------------------------------
def test_verify_against_cache_all_ok(setup):
    lockfile, cache, verifier, tmp = setup
    content = b"tarball content"
    real = compute_sha512(content)

    _setup_cached_package(cache, tmp, "lodash", "4.17.21", content, real)
    lockfile.add_package("lodash", "4.17.21", "https://x", real, "lodash.js", 100)

    result = verifier.verify_against_cache()
    assert result["ok"] is True
    assert result["missing"] == []
    assert result["corrupted"] == []


# ---------------------------------------------------------------------------
# verify_against_cache — missing packages
# ---------------------------------------------------------------------------
def test_verify_against_cache_detects_missing(setup):
    lockfile, _cache, verifier, _tmp = setup
    lockfile.add_package("lodash", "4.17.21", "https://x", "sha512-abc", "lodash.js", 100)

    result = verifier.verify_against_cache()
    assert result["ok"] is False
    assert "lodash@4.17.21" in result["missing"]


# ---------------------------------------------------------------------------
# verify_against_cache — corrupted tarballs
# ---------------------------------------------------------------------------
def test_verify_against_cache_detects_corruption(setup):
    lockfile, cache, verifier, tmp = setup
    content = b"original"
    real = compute_sha512(content)

    _setup_cached_package(cache, tmp, "lodash", "4.17.21", content, real)
    lockfile.add_package("lodash", "4.17.21", "https://x", real, "lodash.js", 100)

    # Corrupt the tarball AFTER populating
    cache.storage.tarball_path("lodash", "4.17.21").write_bytes(b"tampered")

    result = verifier.verify_against_cache()
    assert result["ok"] is False
    assert "lodash@4.17.21" in result["corrupted"]


# ---------------------------------------------------------------------------
# verify_against_cache — extra packages (in cache, not in lockfile)
# ---------------------------------------------------------------------------
def test_verify_against_cache_detects_extra(setup):
    _lockfile, cache, verifier, tmp = setup
    content = b"x"
    real = compute_sha512(content)

    _setup_cached_package(cache, tmp, "dayjs", "1.11.0", content, real)
    # Not added to lockfile — this is an "extra"

    result = verifier.verify_against_cache()
    assert "dayjs@1.11.0" in result["extra"]


# ---------------------------------------------------------------------------
# verify_against_cache — empty lockfile
# ---------------------------------------------------------------------------
def test_verify_against_cache_empty(setup):
    _lockfile, _cache, verifier, _tmp = setup
    result = verifier.verify_against_cache()
    assert result["ok"] is True


# ---------------------------------------------------------------------------
# verify_versions
# ---------------------------------------------------------------------------
def test_verify_versions_matching(setup):
    lockfile, _cache, verifier, _tmp = setup
    lockfile.add_package("lodash", "4.17.21", "https://x", "sha512-a", "lodash.js", 1)

    # Should not raise
    verifier.verify_versions({"lodash": "4.17.21"})


def test_verify_versions_missing_package_raises(setup):
    _lockfile, _cache, verifier, _tmp = setup
    with pytest.raises(LockfileMismatch, match="missing from lockfile"):
        verifier.verify_versions({"lodash": "4.17.21"})


def test_verify_versions_version_mismatch_raises(setup):
    lockfile, _cache, verifier, _tmp = setup
    lockfile.add_package("lodash", "4.17.21", "https://x", "sha512-a", "lodash.js", 1)

    with pytest.raises(LockfileMismatch, match="does not match"):
        verifier.verify_versions({"lodash": "4.17.22"})


def test_verify_versions_empty_expected_passes(setup):
    _lockfile, _cache, verifier, _tmp = setup
    verifier.verify_versions({})  # should not raise


# ---------------------------------------------------------------------------
# is_valid()
# ---------------------------------------------------------------------------
def test_is_valid_false_when_lockfile_missing(setup):
    _lockfile, _cache, verifier, _tmp = setup
    assert verifier.is_valid() is False


def test_is_valid_true_when_everything_ok(setup):
    lockfile, cache, verifier, tmp = setup
    content = b"data"
    real = compute_sha512(content)

    _setup_cached_package(cache, tmp, "lodash", "4.17.21", content, real)
    lockfile.add_package("lodash", "4.17.21", "https://x", real, "lodash.js", 1)
    lockfile.save()

    assert verifier.is_valid() is True


# ---------------------------------------------------------------------------
# report()
# ---------------------------------------------------------------------------
def test_report_when_lockfile_missing(setup):
    _lockfile, _cache, verifier, _tmp = setup
    report = verifier.report()
    assert "NOT FOUND" in report


def test_report_when_ok(setup):
    lockfile, cache, verifier, tmp = setup
    content = b"data"
    real = compute_sha512(content)

    _setup_cached_package(cache, tmp, "lodash", "4.17.21", content, real)
    lockfile.add_package("lodash", "4.17.21", "https://x", real, "lodash.js", 1)
    lockfile.save()

    report = verifier.report()
    assert "OK" in report
    assert "Packages locked: 1" in report


def test_report_when_missing_package(setup):
    lockfile, _cache, verifier, _tmp = setup
    lockfile.add_package("lodash", "4.17.21", "https://x", "sha512-a", "lodash.js", 1)
    lockfile.save()

    report = verifier.report()
    assert "Missing" in report or "missing" in report
