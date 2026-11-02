"""
Tests for teloce_npm.injector.injector.

Scope: only injection / removal mechanics (no idempotency checks here —
those live in test_idempotency.py).
"""

import pytest

from teloce_npm.injector.injector import (
    inject_scripts,
    remove_scripts,
    START_MARKER,
    END_MARKER,
)


SCRIPTS = (
    '<script src="/static/teloce-npm/loader.js" defer></script>\n'
    '<script src="/static/teloce-npm/use.js" defer></script>'
)


def _write_html(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# inject_scripts — target location
# ---------------------------------------------------------------------------
def test_injects_before_head_close(tmp_path):
    html = _write_html(
        tmp_path / "index.html",
        "<html><head><title>x</title></head><body></body></html>",
    )

    inject_scripts(html, SCRIPTS)

    content = html.read_text(encoding="utf-8")
    head_end = content.index("</head>")
    marker = content.index(START_MARKER)
    assert marker < head_end


def test_injects_before_body_close_when_no_head(tmp_path):
    html = _write_html(
        tmp_path / "index.html",
        "<html><body><p>hi</p></body></html>",
    )

    inject_scripts(html, SCRIPTS)

    content = html.read_text(encoding="utf-8")
    assert START_MARKER in content
    body_end = content.index("</body>")
    marker = content.index(START_MARKER)
    assert marker < body_end


def test_appends_when_no_head_or_body(tmp_path):
    html = _write_html(tmp_path / "fragment.html", "<div>partial</div>")

    inject_scripts(html, SCRIPTS)

    content = html.read_text(encoding="utf-8")
    assert START_MARKER in content
    assert END_MARKER in content


# ---------------------------------------------------------------------------
# Marker preservation
# ---------------------------------------------------------------------------
def test_wraps_scripts_in_markers(tmp_path):
    html = _write_html(tmp_path / "index.html", "<html><head></head></html>")

    inject_scripts(html, SCRIPTS)

    content = html.read_text(encoding="utf-8")
    assert START_MARKER in content
    assert END_MARKER in content
    assert content.index(START_MARKER) < content.index(END_MARKER)


def test_scripts_appear_between_markers(tmp_path):
    html = _write_html(tmp_path / "index.html", "<html><head></head></html>")

    inject_scripts(html, SCRIPTS)

    content = html.read_text(encoding="utf-8")
    start = content.index(START_MARKER)
    end = content.index(END_MARKER)
    middle = content[start:end]
    assert "loader.js" in middle
    assert "use.js" in middle


# ---------------------------------------------------------------------------
# Preserves existing content
# ---------------------------------------------------------------------------
def test_preserves_developer_html(tmp_path):
    original = (
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head><title>My App</title></head>\n"
        "<body>\n"
        "<div id='app'></div>\n"
        "<p>Don't touch this</p>\n"
        "</body>\n"
        "</html>\n"
    )
    html = _write_html(tmp_path / "index.html", original)

    inject_scripts(html, SCRIPTS)

    content = html.read_text(encoding="utf-8")
    assert "My App" in content
    assert "Don't touch this" in content
    assert '<div id="app">' in content or "<div id='app'>" in content


# ---------------------------------------------------------------------------
# remove_scripts
# ---------------------------------------------------------------------------
def test_remove_scripts_removes_block(tmp_path):
    html = _write_html(tmp_path / "index.html", "<html><head></head></html>")
    inject_scripts(html, SCRIPTS)

    remove_scripts(html)

    content = html.read_text(encoding="utf-8")
    assert START_MARKER not in content
    assert END_MARKER not in content


def test_remove_scripts_preserves_original(tmp_path):
    original = "<html><head><title>Keep me</title></head><body></body></html>"
    html = _write_html(tmp_path / "index.html", original)
    inject_scripts(html, SCRIPTS)
    remove_scripts(html)

    assert html.read_text(encoding="utf-8") == original


def test_remove_on_clean_file_is_noop(tmp_path):
    original = "<html><head></head></html>"
    html = _write_html(tmp_path / "index.html", original)

    remove_scripts(html)

    assert html.read_text(encoding="utf-8") == original


def test_remove_on_missing_file_is_noop(tmp_path):
    # Should not raise
    remove_scripts(tmp_path / "nonexistent.html")