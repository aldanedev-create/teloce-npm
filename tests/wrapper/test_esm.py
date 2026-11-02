"""
Tests for teloce_npm.wrapper.esm.EsmWrapper.

Scope: only ES Module → browser transformation.
"""

from teloce_npm.wrapper.esm import EsmWrapper


def _make_esm_package(tmp_path, index_js: str, package_json=None):
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()
    (package_dir / "index.mjs").write_text(index_js, encoding="utf-8")
    pj = package_json or {"name": "my-pkg", "type": "module", "main": "index.mjs"}
    return package_dir, pj


# ---------------------------------------------------------------------------
# Structural output
# ---------------------------------------------------------------------------
def test_esm_wraps_in_iife(tmp_path):
    pkg_dir, pj = _make_esm_package(tmp_path, "export default 42;")
    output = EsmWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert "function()" in output
    assert "})();" in output


def test_esm_attaches_default_export_to_window(tmp_path):
    pkg_dir, pj = _make_esm_package(tmp_path, "export default { a: 1 };")
    output = EsmWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert "window['my_pkg']" in output
    assert "__default_export" in output


def test_esm_attaches_empty_object_when_no_default(tmp_path):
    pkg_dir, pj = _make_esm_package(
        tmp_path, "const x = 1;\nexport { x };"
    )
    output = EsmWrapper(pkg_dir, "my-pkg", pj).wrap()

    # Empty object is the fallback
    assert "window['my_pkg']" in output
    assert "typeof __default_export" in output


# ---------------------------------------------------------------------------
# import transformation
# ---------------------------------------------------------------------------
def test_esm_replaces_default_import_with_window(tmp_path):
    pkg_dir, pj = _make_esm_package(
        tmp_path,
        "import lodash from 'lodash';\nexport default lodash;",
    )
    output = EsmWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert "window.lodash" in output
    assert "import lodash" not in output


def test_esm_replaces_named_import_with_destructuring(tmp_path):
    pkg_dir, pj = _make_esm_package(
        tmp_path,
        "import { toUpper } from 'lodash';\nexport default toUpper;",
    )
    output = EsmWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert "const { toUpper } = window.lodash" in output


# ---------------------------------------------------------------------------
# export transformation
# ---------------------------------------------------------------------------
def test_esm_strips_default_export_keyword(tmp_path):
    pkg_dir, pj = _make_esm_package(tmp_path, "export default 42;")
    output = EsmWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert "export default" not in output
    assert "var __default_export = 42;" in output


def test_esm_handles_export_const(tmp_path):
    pkg_dir, pj = _make_esm_package(
        tmp_path, "export const VERSION = '1.0.0';"
    )
    output = EsmWrapper(pkg_dir, "my-pkg", pj).wrap()

    assert "export const" not in output