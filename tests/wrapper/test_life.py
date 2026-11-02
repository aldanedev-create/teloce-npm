"""
Tests for teloce_npm.wrapper.life.LifeWrapper (IIFE passthrough).

Scope: only the safety-closure wrapping.
"""

from teloce_npm.wrapper.life import LifeWrapper


def _make_life_package(tmp_path, index_js: str):
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()
    (package_dir / "index.js").write_text(index_js, encoding="utf-8")
    pj = {"name": "my-pkg", "main": "index.js"}
    return package_dir, pj


def test_life_wraps_in_iife(tmp_path):
    src = "window.myLib = (function(){ return {}; })();"
    pkg_dir, pj = _make_life_package(tmp_path, src)
    output = LifeWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert "function()" in output
    assert "})();" in output


def test_life_preserves_original_source(tmp_path):
    src = "window.myLib = (function(){ return 42; })();"
    pkg_dir, pj = _make_life_package(tmp_path, src)
    output = LifeWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert src in output


def test_life_warns_if_window_undefined(tmp_path):
    src = "var unused = 1;"
    pkg_dir, pj = _make_life_package(tmp_path, src)
    output = LifeWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert "window['my_pkg']" in output
    assert "console.warn" in output