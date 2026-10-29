"""
Tests for teloce_npm.utils.file_io.
"""

import pytest
from pathlib import Path

from teloce_npm.utils.file_io import read_file, write_file_atomic, ensure_dir


# ---------------------------------------------------------------------------
# read_file
# ---------------------------------------------------------------------------
def test_read_file_returns_utf8_content(tmp_path):
    path = tmp_path / "hello.txt"
    path.write_text("héllo wörld", encoding="utf-8")
    assert read_file(path) == "héllo wörld"


def test_read_file_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_file(tmp_path / "does-not-exist.txt")


def test_read_file_empty(tmp_path):
    path = tmp_path / "empty.txt"
    path.write_text("", encoding="utf-8")
    assert read_file(path) == ""


# ---------------------------------------------------------------------------
# write_file_atomic
# ---------------------------------------------------------------------------
def test_write_file_atomic_writes_content(tmp_path):
    path = tmp_path / "out.txt"
    write_file_atomic(path, "content")
    assert path.read_text(encoding="utf-8") == "content"


def test_write_file_atomic_creates_parent_dirs(tmp_path):
    path = tmp_path / "deeply" / "nested" / "out.txt"
    write_file_atomic(path, "hello")
    assert path.exists()
    assert path.read_text(encoding="utf-8") == "hello"


def test_write_file_atomic_overwrites(tmp_path):
    path = tmp_path / "out.txt"
    path.write_text("old", encoding="utf-8")
    write_file_atomic(path, "new")
    assert path.read_text(encoding="utf-8") == "new"


def test_write_file_atomic_leaves_no_temp_files(tmp_path):
    path = tmp_path / "out.txt"
    write_file_atomic(path, "content")

    # No leftover *.tmp files should exist
    leftover = list(tmp_path.glob("*.tmp")) + list(tmp_path.glob(".*.tmp"))
    assert leftover == [], f"Leftover temp files: {leftover}"


def test_write_file_atomic_handles_unicode(tmp_path):
    path = tmp_path / "unicode.txt"
    write_file_atomic(path, "日本語 emoji 🎉")
    assert path.read_text(encoding="utf-8") == "日本語 emoji 🎉"


# ---------------------------------------------------------------------------
# ensure_dir
# ---------------------------------------------------------------------------
def test_ensure_dir_creates_directory(tmp_path):
    target = tmp_path / "new" / "nested" / "dir"
    ensure_dir(target)
    assert target.is_dir()


def test_ensure_dir_is_idempotent(tmp_path):
    target = tmp_path / "existing"
    target.mkdir()
    ensure_dir(target)  # should not raise
    assert target.is_dir()