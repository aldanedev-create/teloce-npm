"""
Tests for teloce_npm.scanner.file_walker.

Scope: only directory traversal.
Does NOT test Use extraction (that's test_use_scanner.py).
Does NOT test edge cases (that's test_edge_cases.py).
"""

from pathlib import Path

from teloce_npm.scanner.file_walker import (
    find_source_files,
    IGNORE_DIRS,
    SOURCE_EXTENSIONS,
)


def _make_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_finds_vel_files(tmp_path):
    _make_file(tmp_path / "static" / "js" / "App.vel")
    _make_file(tmp_path / "static" / "js" / "Other.vel")

    found = find_source_files(tmp_path)
    names = sorted(p.name for p in found)

    assert names == ["App.vel", "Other.vel"]


def test_finds_html_files(tmp_path):
    _make_file(tmp_path / "templates" / "index.html")
    _make_file(tmp_path / "templates" / "login.html")

    found = find_source_files(tmp_path)
    names = sorted(p.name for p in found)

    assert names == ["index.html", "login.html"]


def test_finds_mixed_extensions(tmp_path):
    _make_file(tmp_path / "App.vel")
    _make_file(tmp_path / "index.html")

    found = find_source_files(tmp_path)
    extensions = sorted(p.suffix for p in found)

    assert extensions == [".html", ".vel"]


def test_ignores_non_source_extensions(tmp_path):
    _make_file(tmp_path / "App.vel")
    _make_file(tmp_path / "README.md")
    _make_file(tmp_path / "styles.css")
    _make_file(tmp_path / "script.js")

    found = find_source_files(tmp_path)
    names = [p.name for p in found]

    assert names == ["App.vel"]


def test_ignores_git_directory(tmp_path):
    _make_file(tmp_path / ".git" / "hooks" / "pre-commit.vel")
    _make_file(tmp_path / "App.vel")

    found = find_source_files(tmp_path)
    names = [p.name for p in found]

    assert names == ["App.vel"]


def test_ignores_node_modules(tmp_path):
    _make_file(tmp_path / "node_modules" / "pkg" / "index.vel")
    _make_file(tmp_path / "App.vel")

    found = find_source_files(tmp_path)
    names = [p.name for p in found]

    assert names == ["App.vel"]


def test_ignores_dist_and_build(tmp_path):
    _make_file(tmp_path / "dist" / "App.vel")
    _make_file(tmp_path / "build" / "Other.vel")
    _make_file(tmp_path / "App.vel")

    found = find_source_files(tmp_path)
    names = [p.name for p in found]

    assert names == ["App.vel"]


def test_ignores_teloce_cache(tmp_path):
    _make_file(tmp_path / ".teloce-npm" / "cache" / "pkg" / "fake.vel")
    _make_file(tmp_path / "App.vel")

    found = find_source_files(tmp_path)
    names = [p.name for p in found]

    assert names == ["App.vel"]


def test_ignores_pycache(tmp_path):
    _make_file(tmp_path / "__pycache__" / "fake.vel")
    _make_file(tmp_path / "App.vel")

    found = find_source_files(tmp_path)
    names = [p.name for p in found]

    assert names == ["App.vel"]


def test_returns_empty_for_empty_dir(tmp_path):
    assert find_source_files(tmp_path) == []


def test_returns_empty_for_missing_root(tmp_path):
    missing = tmp_path / "does-not-exist"
    assert find_source_files(missing) == []


def test_returns_absolute_paths(tmp_path):
    _make_file(tmp_path / "App.vel")

    found = find_source_files(tmp_path)

    assert len(found) == 1
    assert found[0].is_absolute()


def test_finds_files_in_nested_directories(tmp_path):
    _make_file(tmp_path / "a" / "b" / "c" / "deep.vel")

    found = find_source_files(tmp_path)

    assert len(found) == 1
    assert found[0].name == "deep.vel"


def test_constant_extensions_are_lowercase():
    """The implementation lowercases suffixes; the constant should too."""
    for ext in SOURCE_EXTENSIONS:
        assert ext == ext.lower()
        assert ext.startswith(".")


def test_ignore_dirs_contains_expected_entries():
    """Regression guard: don't remove critical entries without a test change."""
    required = {"node_modules", "dist", ".git", ".teloce-npm"}
    assert required <= IGNORE_DIRS