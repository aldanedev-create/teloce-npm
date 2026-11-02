"""
Tests for teloce_npm.wrapper.umd.UmdWrapper.

Scope: only UMD passthrough wrapping.
"""

from teloce_npm.wrapper.umd import UmdWrapper


def _make_umd_package(tmp_path, index_js: str):
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()
    (package_dir / "index.js").write_text(index_js, encoding="utf-8")
    pj = {"name": "my-pkg", "main": "index.js"}
    return package_dir, pj


def test_umd_wraps_in_iife(tmp_path):
    src = "(function(root){ root.myLib = {}; })(this);"
    pkg_dir, pj = _make_umd_package(tmp_path, src)
    output = UmdWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert "function()" in output
    assert "})();" in output


def test_umd_includes_fake_module(tmp_path):
    src = "module.exports = { x: 1 };"
    pkg_dir, pj = _make_umd_package(tmp_path, src)
    output = UmdWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert "var module = { exports: {} };" in output


def test_umd_preserves_original_source(tmp_path):
    src = "var myUMD = function(){ return 42; };"
    pkg_dir, pj = _make_umd_package(tmp_path, src)
    output = UmdWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert src in output


def test_umd_attaches_to_window(tmp_path):
    src = "module.exports = { x: 1 };"
    pkg_dir, pj = _make_umd_package(tmp_path, src)
    output = UmdWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert "window['my_pkg']" in output