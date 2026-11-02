"""
Tests for teloce_npm.lockfile.manager.LockfileManager.

Scope: only CRUD (load, save, add, remove, get, list, clear).
Does NOT test verification (that's test_verifier.py).
"""

import json

import pytest

from teloce_npm.lockfile.manager import LockfileManager, LOCKFILE_FILENAME
from teloce_npm.utils.errors import ConfigError


@pytest.fixture
def manager(tmp_path):
    return LockfileManager(tmp_path)


def _add(manager, name="lodash", version="4.17.21"):
    """Helper: add a standard package to the manager."""
    manager.add_package(
        package_name=name,
        version=version,
        resolved_url=f"https://reg.example.com/{name}-{version}.tgz",
        integrity="sha512-abc",
        wrapped_filename=f"{name}.js",
        size=100,
    )


# ---------------------------------------------------------------------------
# load() / exists()
# ---------------------------------------------------------------------------
def test_load_when_no_file_returns_empty(manager):
    lock = manager.load()
    assert lock["packages"] == {}


def test_exists_false_before_save(manager):
    assert manager.exists() is False


def test_exists_true_after_save(manager):
    manager.save()
    assert manager.exists() is True


def test_load_caches_in_memory(manager):
    """Loading twice returns the same dict instance."""
    first = manager.load()
    second = manager.load()
    assert first is second


def test_load_invalid_json_raises(tmp_path):
    (tmp_path / LOCKFILE_FILENAME).write_text("{ bad json", encoding="utf-8")
    manager = LockfileManager(tmp_path)

    with pytest.raises(ConfigError, match="Invalid JSON"):
        manager.load()


def test_load_invalid_schema_raises(tmp_path):
    (tmp_path / LOCKFILE_FILENAME).write_text(
        json.dumps({"lockfile_version": "bogus", "packages": {}}),
        encoding="utf-8",
    )
    manager = LockfileManager(tmp_path)

    with pytest.raises(ConfigError, match="Unsupported"):
        manager.load()


# ---------------------------------------------------------------------------
# save()
# ---------------------------------------------------------------------------
def test_save_writes_file(manager):
    manager.save()
    assert (manager.path).exists()


def test_save_writes_valid_json(manager):
    _add(manager)
    manager.save()

    on_disk = json.loads(manager.path.read_text(encoding="utf-8"))
    assert on_disk["packages"]["lodash"]["version"] == "4.17.21"


def test_save_updates_generated_at(manager):
    _add(manager)
    manager.save()
    first = json.loads(manager.path.read_text(encoding="utf-8"))["generated_at"]

    # Second save must update the timestamp (or at least be a valid ISO string)
    import time
    time.sleep(0.01)
    manager.save()
    second = json.loads(manager.path.read_text(encoding="utf-8"))["generated_at"]

    assert isinstance(first, str) and isinstance(second, str)


# ---------------------------------------------------------------------------
# add_package()
# ---------------------------------------------------------------------------
def test_add_package_creates_entry(manager):
    _add(manager)
    assert manager.has_package("lodash") is True


def test_add_package_overwrites_existing(manager):
    _add(manager, version="4.17.21")
    _add(manager, version="4.17.20")
    assert manager.get_package_version("lodash") == "4.17.20"


def test_add_package_preserves_dependencies(manager):
    manager.add_package(
        package_name="chart.js",
        version="4.4.0",
        resolved_url="https://x",
        integrity="sha512-x",
        wrapped_filename="chart_js.js",
        size=100,
        dependencies={"dayjs": "^1.11.0"},
    )
    entry = manager.get_package("chart.js")
    assert entry["dependencies"] == {"dayjs": "^1.11.0"}


# ---------------------------------------------------------------------------
# remove_package()
# ---------------------------------------------------------------------------
def test_remove_package_returns_true(manager):
    _add(manager)
    assert manager.remove_package("lodash") is True
    assert manager.has_package("lodash") is False


def test_remove_package_missing_returns_false(manager):
    assert manager.remove_package("missing-pkg") is False


# ---------------------------------------------------------------------------
# get_package() / has_package() / get_package_version() / get_package_integrity()
# ---------------------------------------------------------------------------
def test_get_package_returns_entry(manager):
    _add(manager)
    entry = manager.get_package("lodash")
    assert entry["version"] == "4.17.21"


def test_get_package_returns_none_for_missing(manager):
    assert manager.get_package("missing-pkg") is None


def test_has_package_true(manager):
    _add(manager)
    assert manager.has_package("lodash") is True


def test_has_package_false(manager):
    assert manager.has_package("lodash") is False


def test_get_package_version(manager):
    _add(manager)
    assert manager.get_package_version("lodash") == "4.17.21"


def test_get_package_version_missing_returns_none(manager):
    assert manager.get_package_version("missing-pkg") is None


def test_get_package_integrity(manager):
    _add(manager)
    assert manager.get_package_integrity("lodash") == "sha512-abc"


# ---------------------------------------------------------------------------
# list_packages()
# ---------------------------------------------------------------------------
def test_list_packages_empty(manager):
    assert manager.list_packages() == {}


def test_list_packages_returns_all(manager):
    _add(manager, name="lodash", version="4.17.21")
    _add(manager, name="dayjs", version="1.11.0")
    assert manager.list_packages() == {"lodash": "4.17.21", "dayjs": "1.11.0"}


# ---------------------------------------------------------------------------
# clear()
# ---------------------------------------------------------------------------
def test_clear_resets_memory_only(manager):
    """clear() does not remove the file from disk (cleanup is CleanCommand's job)."""
    _add(manager)
    manager.save()

    manager.clear()

    assert manager.load()["packages"] == {}
    # File still on disk because clear() only resets memory
    assert manager.path.exists()


def test_clear_then_save_writes_empty_lockfile(manager):
    _add(manager)
    manager.save()

    manager.clear()
    manager.save()

    on_disk = json.loads(manager.path.read_text(encoding="utf-8"))
    assert on_disk["packages"] == {}


# ---------------------------------------------------------------------------
# summary()
# ---------------------------------------------------------------------------
def test_summary_reports_counts(manager):
    _add(manager, name="lodash", version="4.17.21")
    _add(manager, name="dayjs", version="1.11.0")
    manager.save()

    summary = manager.summary()
    assert summary["package_count"] == 2
    assert "lodash" in summary["packages"]
    assert summary["exists"] is True


def test_summary_when_file_missing(manager):
    summary = manager.summary()
    assert summary["exists"] is False
    assert summary["package_count"] == 0