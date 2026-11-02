"""
Tests for teloce_npm.wrapper.cjs.CjsWrapper.

Scope: only CommonJS → browser transformation.
All tests use direct instantiation, no factory.
"""

from teloce_npm.wrapper.cjs import CjsWrapper


def _make_cjs_package(tmp_path, index_js: str, package_json=None):
    """Create a minimal CJS package_dir and return (package_dir, package_json)."""
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()
    (package_dir / "index.js").write_text(index_js, encoding="utf-8")
    pj = package_json or {"name": "my-pkg", "main": "index.js"}
    return package_dir, pj


# ---------------------------------------------------------------------------
# Structural output
# ---------------------------------------------------------------------------
def test_cjs_wraps_in_iife(tmp_path):
    pkg_dir, pj = _make_cjs_package(tmp_path, "module.exports = { a: 1 };")
    output = CjsWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert "function()" in output
    assert "})();" in output


def test_cjs_creates_fake_module_object(tmp_path):
    pkg_dir, pj = _make_cjs_package(tmp_path, "module.exports = { a: 1 };")
    output = CjsWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert "var module = { exports: {} };" in output
    assert "var exports = module.exports;" in output


def test_cjs_attaches_to_window(tmp_path):
    pkg_dir, pj = _make_cjs_package(tmp_path, "module.exports = { a: 1 };")
    output = CjsWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert "window['my_pkg']" in output


def test_cjs_dashes_become_underscores_in_window_name(tmp_path):
    pkg_dir, pj = _make_cjs_package(
        tmp_path, "module.exports = {};",
        package_json={"name": "my-cool-pkg", "main": "index.js"},
    )
    output = CjsWrapper(pkg_dir, "my-cool-pkg", pj).wrap()

    assert "window['my_cool_pkg']" in output


# ---------------------------------------------------------------------------
# require() transformation
# ---------------------------------------------------------------------------
def test_cjs_replaces_external_require_with_window(tmp_path):
    pkg_dir, pj = _make_cjs_package(
        tmp_path,
        "const _ = require('lodash');\nmodule.exports = { up: _.toUpper('hi') };",
    )
    output = CjsWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert "window.lodash" in output
    assert "require('lodash')" not in output


def test_cjs_replaces_scoped_require_with_safe_name(tmp_path):
    pkg_dir, pj = _make_cjs_package(
        tmp_path,
        "const t = require('@types/node');\nmodule.exports = t;",
    )
    output = CjsWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert "window.types_node" in output


def test_cjs_replaces_relative_require_with_undefined(tmp_path):
    pkg_dir, pj = _make_cjs_package(
        tmp_path,
        "const x = require('./utils');\nmodule.exports = x;",
    )
    output = CjsWrapper(pkg_dir, "my-pkg", pj).wrap()

    # Relative require becomes undefined (browser can't resolve)
    assert "require('./utils')" not in output
    assert "= undefined" in output


def test_cjs_preserves_original_comment(tmp_path):
    pkg_dir, pj = _make_cjs_package(
        tmp_path,
        "// my comment\nmodule.exports = 42;",
    )
    output = CjsWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert "// my comment" in output


def test_cjs_preserves_strings_with_require(tmp_path):
    """Strings containing 'require' must not be broken by the transformation."""
    pkg_dir, pj = _make_cjs_package(
        tmp_path,
        "var msg = \"call require('x')\";\nmodule.exports = msg;",
    )
    output = CjsWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert 'call require(\'x\')' in output