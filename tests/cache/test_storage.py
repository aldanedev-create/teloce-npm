"""
Tests for teloce_npm.cache.storage.CacheStorage.

Scope: only on-disk layout (paths + read/write/remove).
Integrity checks are in test_manager.py.
"""

import pytest

from teloce_npm.cache.storage import CacheStorage


@pytest.fixture
def storage(tmp_path):
    return CacheStorage(tmp_path / "cache")


# ---------------------------------------------------------------------------
# Path layout
# ---------------------------------------------------------------------------
def test_package_dir_layout(storage):
    path = storage.package_dir("lodash", "4.17.21")
    assert path.name == "lodash@4.17.21"


def test_package_dir_handles_slash(storage):
    """Scoped packages must not create nested directories."""
    path = storage.package_dir("@types/node", "20.0.0")
    assert "/" not in path.name
    # Should not contain a nested dir
    assert path.parent == storage.cache_dir


def test_package_dir_handles_scope(storage):
    path = storage.package_dir("@types/node", "20.0.0")
    assert "@types" not in path.name.split("@")[0] or "types" in path.name


def test_tarball_path_lives_in_package_dir(storage):
    pkg_dir = storage.package_dir("lodash", "4.17.21")
    assert storage.tarball_path("lodash", "4.17.21").parent == pkg_dir


def test_extracted_dir_lives_in_package_dir(storage):
    pkg_dir = storage.package_dir("lodash", "4.17.21")
    assert storage.extracted_dir("lodash", "4.17.21").parent == pkg_dir


def test_wrapped_path_lives_in_package_dir(storage):
    pkg_dir = storage.package_dir("lodash", "4.17.21")
    assert storage.wrapped_path("lodash", "4.17.21").parent == pkg_dir


def test_metadata_path_lives_in_package_dir(storage):
    pkg_dir = storage.package_dir("lodash", "4.17.21")
    assert storage.metadata_path("lodash", "4.17.21").parent == pkg_dir


# ---------------------------------------------------------------------------
# Existence
# ---------------------------------------------------------------------------
def test_exists_false_initially(storage):
    assert storage.exists("lodash", "4.17.21") is False


def test_exists_true_after_all_three_saved(storage, tmp_path):
    # Create extracted dir
    extracted = storage.extracted_dir("lodash", "4.17.21")
    extracted.mkdir(parents=True)
    (extracted / "package.json").write_text("{}")

    # Save wrapped
    storage.save_wrapped("lodash", "4.17.21", "window.lodash = {};")

    # Save metadata
    storage.save_metadata("lodash", "4.17.21", {"integrity": "sha512-x"})

    assert storage.exists("lodash", "4.17.21") is True


def test_has_tarball_false_initially(storage):
    assert storage.has_tarball("lodash", "4.17.21") is False


def test_has_tarball_true_after_save(storage):
    tarball = storage.tarball_path("lodash", "4.17.21")
    tarball.parent.mkdir(parents=True)
    tarball.write_bytes(b"fake tarball")

    assert storage.has_tarball("lodash", "4.17.21") is True


# ---------------------------------------------------------------------------
# Metadata round-trip
# ---------------------------------------------------------------------------
def test_save_and_load_metadata(storage):
    metadata = {
        "integrity": "sha512-abc",
        "tarball_url": "https://example.com/pkg.tgz",
        "scan_result": "clean",
    }
    storage.save_metadata("lodash", "4.17.21", metadata)

    loaded = storage.load_metadata("lodash", "4.17.21")
    assert loaded["integrity"] == "sha512-abc"
    assert loaded["name"] == "lodash"
    assert loaded["version"] == "4.17.21"
    assert "cached_at" in loaded


def test_load_metadata_missing_returns_none(storage):
    assert storage.load_metadata("missing-pkg", "1.0.0") is None


def test_load_metadata_corrupted_returns_none(storage):
    path = storage.metadata_path("lodash", "4.17.21")
    path.parent.mkdir(parents=True)
    path.write_text("{ not json", encoding="utf-8")

    assert storage.load_metadata("lodash", "4.17.21") is None


# ---------------------------------------------------------------------------
# Wrapped round-trip
# ---------------------------------------------------------------------------
def test_save_and_load_wrapped(storage):
    storage.save_wrapped("lodash", "4.17.21", "window.lodash = {};")

    loaded = storage.load_wrapped("lodash", "4.17.21")
    assert loaded == "window.lodash = {};"


def test_load_wrapped_missing_returns_none(storage):
    assert storage.load_wrapped("missing", "1.0.0") is None


# ---------------------------------------------------------------------------
# Removal
# ---------------------------------------------------------------------------
def test_remove_existing_returns_true(storage):
    storage.save_wrapped("lodash", "4.17.21", "code")
    assert storage.remove("lodash", "4.17.21") is True
    assert not storage.package_dir("lodash", "4.17.21").exists()


def test_remove_missing_returns_false(storage):
    assert storage.remove("missing", "1.0.0") is False


def test_clear_all_removes_everything(storage):
    for name in ("a", "b", "c"):
        storage.save_wrapped(name, "1.0.0", "code")

    count = storage.clear_all()
    assert count == 3

    for name in ("a", "b", "c"):
        assert not storage.package_dir(name, "1.0.0").exists()
