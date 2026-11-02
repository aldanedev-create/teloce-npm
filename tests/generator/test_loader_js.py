"""
Tests for teloce_npm.generator.loader_js.

Scope: only loader.js generation.
"""

from teloce_npm.generator.loader_js import generate_loader_js, write_loader_js


# ---------------------------------------------------------------------------
# generate_loader_js()
# ---------------------------------------------------------------------------
def test_contains_fetch_call():
    output = generate_loader_js()
    assert "fetch" in output


def test_manifest_url_substituted():
    output = generate_loader_js(base_path="/my/static/path")
    assert "/my/static/path/manifest.json" in output
    assert "${manifest_url}" not in output


def test_base_path_substituted():
    output = generate_loader_js(base_path="/custom/base")
    assert '"/custom/base"' in output
    assert "${base_path}" not in output


def test_custom_manifest_url():
    output = generate_loader_js(
        base_path="/unused",
        manifest_url="https://cdn.example.com/manifest.json",
    )
    assert "https://cdn.example.com/manifest.json" in output


def test_dispatches_ready_event():
    output = generate_loader_js()
    assert "teloce-npm-ready" in output


def test_has_dependency_ordering():
    output = generate_loader_js()
    # Should reference dependencies from manifest
    assert "dependencies" in output.lower()


def test_trailing_slash_stripped():
    output = generate_loader_js(base_path="/api/static/")
    # Should not produce //manifest.json
    assert "/api/static//" not in output


def test_wrapped_in_iife():
    output = generate_loader_js()
    assert "function()" in output
    assert "})();" in output


# ---------------------------------------------------------------------------
# write_loader_js()
# ---------------------------------------------------------------------------
def test_write_creates_file(tmp_path):
    path = write_loader_js(tmp_path / "out")
    assert path.exists()
    assert path.name == "loader.js"


def test_write_content_matches_generate(tmp_path):
    path = write_loader_js(tmp_path / "out", base_path="/x")
    on_disk = path.read_text(encoding="utf-8")
    assert on_disk == generate_loader_js(base_path="/x")