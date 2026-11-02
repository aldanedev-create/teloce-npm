"""
Tests for teloce_npm.injector.html_scanner.get_entry_html.

Scope: only entry_html resolution and validation.
This is the "entry_html targeting" test — verifies that the
configured entry_html is used, not a hardcoded index.html.
"""

import pytest

from teloce_npm.injector.html_scanner import get_entry_html
from teloce_npm.utils.errors import ConfigError


def _make(path, content="<html></html>"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------
def test_returns_path_when_file_exists(tmp_path):
    entry = _make(tmp_path / "templates" / "index.html")
    result = get_entry_html(entry)
    assert result == entry


def test_uses_any_configured_filename(tmp_path):
    """Verify it respects whatever path is passed, not a hardcoded index.html."""
    entry = _make(tmp_path / "templates" / "layout.html")
    result = get_entry_html(entry)
    assert result.name == "layout.html"


def test_accepts_nested_paths(tmp_path):
    entry = _make(tmp_path / "a" / "b" / "c" / "entry.html")
    result = get_entry_html(entry)
    assert result.exists()


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------
def test_missing_file_raises_config_error(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        get_entry_html(tmp_path / "missing.html")


def test_directory_path_raises(tmp_path):
    dir_path = tmp_path / "templates"
    dir_path.mkdir()

    with pytest.raises(ConfigError, match="not a file"):
        get_entry_html(dir_path)


# ---------------------------------------------------------------------------
# Non-.html extensions: warning only, does not raise
# ---------------------------------------------------------------------------
def test_non_html_extension_does_not_raise(tmp_path):
    """Per implementation, non-.html extension logs a warning but returns."""
    entry = _make(tmp_path / "templates" / "index.jinja")
    result = get_entry_html(entry)
    assert result == entry
