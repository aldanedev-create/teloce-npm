"""
Tests for teloce_npm.cache.manager.CacheManager.

Scope: high-level API (has/store/get_wrapped/list/invalidate/clear).
"""

import pytest

from teloce_npm.cache.manager import CacheManager
from teloce_npm.utils.hashing import compute_sha512


@pytest.fixture
def manager(tmp_path):
    return CacheManager(tmp_path / "cache")


def _populate(manager, name, version, integrity, wrapped="code"):
    """Helper: put a package in the cache state that `has()` expects."""
    pkg_dir = manager.storage.package_dir(name, version)
    pkg_dir.mkdir(parents=True)

    # tarball (matched to `integrity`)
    tarball = pkg_dir / "package.tgz"
    content = b"tarball bytes"
    tarball.write_bytes(content)
    real_integrity = compute_sha512(content)

    # extracted
    (pkg_dir / "extracted").mkdir()
    (pkg_dir / "extracted" / "package.json").write_text("{}")

    # wrapped
    (pkg_dir / "wrapped.js").write_text(wrapped)

    # metadata — record the integrity that matches the tarball
    manager.storage.save_metadata(name, version, {"integrity": real_integrity})

    return real_integrity


# ---------------------------------------------------------------------------
# has()
# ---------------------------------------------------------------------------
def test_has_returns_false_for_missing_package(manager):
    assert manager.has("lodash", "4.17.21", "sha512-whatever") is False


def test_has_returns_true_when_everything_matches(manager):
    integrity = _populate(manager, "lodash", "4.17.21", "ignored")
    assert manager.has("lodash", "4.17.21", integrity) is True


def test_has_returns_false_on_tarball_integrity_mismatch(manager):
    _populate(manager, "lodash", "4.17.21", "ignored")
    wrong = "sha512-" + "A" * 86

    assert manager.has("lodash", "4.17.21", wrong) is False
    # Cache entry must be invalidated
    assert not manager.storage.package_dir("lodash", "4.17.21").exists()


def test_has_returns_false_on_metadata_integrity_mismatch(manager):
    """Tarball matches, but metadata claims a different hash → invalidate."""
    real_integrity = _populate(manager, "lodash", "4.17.21", "ignored")

    # Overwrite metadata with a DIFFERENT hash
    manager.storage.save_metadata("lodash", "4.17.21", {"integrity": "sha512-other"})

    # Query with the tarball's real hash
    assert manager.has("lodash", "4.17.21", real_integrity) is False


# ---------------------------------------------------------------------------
# get_wrapped / get_extracted_dir
# ---------------------------------------------------------------------------
def test_get_wrapped_returns_code(manager):
    _populate(manager, "lodash", "4.17.21", "ignored", wrapped="window.lodash = 42;")
    code = manager.get_wrapped("lodash", "4.17.21")
    assert code == "window.lodash = 42;"


def test_get_wrapped_missing_raises(manager):
    with pytest.raises(FileNotFoundError):
        manager.get_wrapped("missing", "1.0.0")


def test_get_extracted_dir(manager):
    _populate(manager, "lodash", "4.17.21", "ignored")
    path = manager.get_extracted_dir("lodash", "4.17.21")
    assert path.name == "extracted"
    assert path.exists()


# ---------------------------------------------------------------------------
# store()
# ---------------------------------------------------------------------------
def test_store_moves_extracted_dir(tmp_path, manager):
    # Source extracted dir in a temp location (outside the cache)
    src = tmp_path / "src_extracted"
    src.mkdir()
    (src / "package.json").write_text('{"name": "lodash"}')

    manager.store(
        package_name="lodash",
        version="4.17.21",
        extracted_dir=src,
        wrapped_code="window.lodash = {};",
        metadata={"integrity": "sha512-x", "tarball_url": "https://x"},
    )

    # Source moved
    assert not src.exists()

    # Now in cache
    target = manager.storage.extracted_dir("lodash", "4.17.21")
    assert (target / "package.json").exists()
    assert manager.storage.wrapped_path("lodash", "4.17.21").read_text() == "window.lodash = {};"


def test_store_saves_metadata(tmp_path, manager):
    src = tmp_path / "src"
    src.mkdir()
    manager.store(
        package_name="pkg",
        version="1.0.0",
        extracted_dir=src,
        wrapped_code="code",
        metadata={"integrity": "sha512-x"},
    )

    meta = manager.get_metadata("pkg", "1.0.0")
    assert meta["integrity"] == "sha512-x"
    assert meta["name"] == "pkg"
    assert meta["version"] == "1.0.0"


def test_store_overwrites_existing_extracted(tmp_path, manager):
    # First store
    src1 = tmp_path / "src1"
    src1.mkdir()
    (src1 / "old.js").write_text("old")
    manager.store("pkg", "1.0.0", src1, "code1", {"integrity": "a"})

    # Second store with same name/version
    src2 = tmp_path / "src2"
    src2.mkdir()
    (src2 / "new.js").write_text("new")
    manager.store("pkg", "1.0.0", src2, "code2", {"integrity": "b"})

    target = manager.storage.extracted_dir("pkg", "1.0.0")
    assert (target / "new.js").exists()
    assert not (target / "old.js").exists()


# ---------------------------------------------------------------------------
# invalidate() / clear_all()
# ---------------------------------------------------------------------------
def test_invalidate_removes_entry(manager):
    _populate(manager, "lodash", "4.17.21", "ignored")
    assert manager.invalidate("lodash", "4.17.21") is True
    assert not manager.storage.package_dir("lodash", "4.17.21").exists()


def test_invalidate_missing_returns_false(manager):
    assert manager.invalidate("missing", "1.0.0") is False


def test_clear_all_removes_everything(manager):
    for name in ("a", "b", "c"):
        _populate(manager, name, "1.0.0", "ignored")
    count = manager.clear_all()
    assert count == 3


# ---------------------------------------------------------------------------
# list_cached()
# ---------------------------------------------------------------------------
def test_list_cached_empty(manager):
    assert manager.list_cached() == []


def test_list_cached_returns_summary(manager):
    _populate(manager, "lodash", "4.17.21", "ignored")
    _populate(manager, "dayjs", "1.11.0", "ignored")

    listing = manager.list_cached()

    assert len(listing) == 2
    names = {item["name"] for item in listing}
    assert names == {"lodash", "dayjs"}
    for item in listing:
        assert "version" in item
        assert "size" in item
        assert "cached_at" in item
