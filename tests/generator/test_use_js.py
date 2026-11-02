"""
Tests for teloce_npm.generator.use_js.

Scope: only use.js generation.
"""

from teloce_npm.generator.use_js import generate_use_js, write_use_js


def _pkg(name, version="1.0.0"):
    return {
        "name": name,
        "version": version,
        "file": f"{name}.js",
        "size": 100,
        "integrity": "sha512-x",
        "dependencies": {},
    }


# ---------------------------------------------------------------------------
# generate_use_js()
# ---------------------------------------------------------------------------
def test_generates_window_use_function():
    output = generate_use_js([_pkg("lodash")])
    assert "window.use" in output


def test_output_includes_package_name():
    output = generate_use_js([_pkg("lodash", "4.17.21")])
    assert '"lodash": "4.17.21"' in output


def test_output_includes_multiple_packages():
    output = generate_use_js([_pkg("lodash"), _pkg("chart.js")])
    assert '"lodash"' in output
    assert '"chart.js"' in output


def test_output_is_wrapped_in_iife():
    output = generate_use_js([_pkg("lodash")])
    assert "function()" in output
    assert "})();" in output


def test_empty_packages_produces_valid_output():
    """No packages → still emits a valid IIFE with empty available map."""
    output = generate_use_js([])
    assert "window.use" in output
    assert "var available = {" in output


def test_output_does_not_contain_template_markers():
    """The template should be fully substituted."""
    output = generate_use_js([_pkg("lodash")])
    assert "${" not in output


# ---------------------------------------------------------------------------
# write_use_js()
# ---------------------------------------------------------------------------
def test_write_creates_file(tmp_path):
    path = write_use_js([_pkg("lodash")], tmp_path / "out")
    assert path.exists()
    assert path.name == "use.js"


def test_write_content_matches_generate(tmp_path):
    packages = [_pkg("lodash")]
    path = write_use_js(packages, tmp_path / "out")
    on_disk = path.read_text(encoding="utf-8")
    assert on_disk == generate_use_js(packages)


def test_write_creates_output_dir(tmp_path):
    target = tmp_path / "deeply" / "nested"
    path = write_use_js([_pkg("lodash")], target)
    assert path.exists()