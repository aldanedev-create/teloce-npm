"""
Tests for the idempotency guarantee of inject_scripts.

Scope: only repeated injection/removal behavior.
Verifies that running `teloce-npm install` multiple times produces
the same final HTML (no duplicated tags).
"""

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


def _make_html(tmp_path, content="<html><head></head><body></body></html>"):
    path = tmp_path / "index.html"
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Repeated injection
# ---------------------------------------------------------------------------
def test_inject_twice_only_one_block(tmp_path):
    html = _make_html(tmp_path)

    inject_scripts(html, SCRIPTS)
    inject_scripts(html, SCRIPTS)

    content = html.read_text(encoding="utf-8")
    assert content.count(START_MARKER) == 1
    assert content.count(END_MARKER) == 1


def test_inject_five_times_only_one_block(tmp_path):
    html = _make_html(tmp_path)

    for _ in range(5):
        inject_scripts(html, SCRIPTS)

    content = html.read_text(encoding="utf-8")
    assert content.count(START_MARKER) == 1
    assert content.count("loader.js") == 1
    assert content.count("use.js") == 1


def test_inject_with_different_scripts_still_one_block(tmp_path):
    html = _make_html(tmp_path)

    inject_scripts(html, SCRIPTS)
    new_scripts = '<script src="/v2/loader.js" defer></script>'
    inject_scripts(html, new_scripts)

    content = html.read_text(encoding="utf-8")
    assert content.count(START_MARKER) == 1
    assert "/v2/loader.js" in content
    assert "/static/teloce-npm/loader.js" not in content


# ---------------------------------------------------------------------------
# Inject / remove / inject
# ---------------------------------------------------------------------------
def test_remove_then_inject_restores_single_block(tmp_path):
    html = _make_html(tmp_path)

    inject_scripts(html, SCRIPTS)
    remove_scripts(html)
    inject_scripts(html, SCRIPTS)

    content = html.read_text(encoding="utf-8")
    assert content.count(START_MARKER) == 1


def test_remove_is_idempotent(tmp_path):
    html = _make_html(tmp_path)
    inject_scripts(html, SCRIPTS)

    remove_scripts(html)
    remove_scripts(html)
    remove_scripts(html)

    content = html.read_text(encoding="utf-8")
    assert START_MARKER not in content
    assert END_MARKER not in content


# ---------------------------------------------------------------------------
# Content outside markers is never touched
# ---------------------------------------------------------------------------
def test_inject_preserves_surrounding_content(tmp_path):
    html = _make_html(
        tmp_path,
        "<html>\n"
        "<head>\n"
        "<title>App</title>\n"
        "</head>\n"
        "<body>\n"
        "<div>below</div>\n"
        "</body>\n"
        "</html>\n",
    )

    inject_scripts(html, SCRIPTS)
    inject_scripts(html, SCRIPTS)

    content = html.read_text(encoding="utf-8")
    assert "<title>App</title>" in content
    assert "<div>below</div>" in content


def test_full_cycle_is_stable(tmp_path):
    """Inject → remove → inject → remove → inject → one block, original intact."""
    original = "<html><head><title>X</title></head><body><p>content</p></body></html>"
    html = _make_html(tmp_path, original)

    for _ in range(3):
        inject_scripts(html, SCRIPTS)
        remove_scripts(html)

    inject_scripts(html, SCRIPTS)

    content = html.read_text(encoding="utf-8")
    assert content.count(START_MARKER) == 1
    assert "<title>X</title>" in content
    assert "<p>content</p>" in content