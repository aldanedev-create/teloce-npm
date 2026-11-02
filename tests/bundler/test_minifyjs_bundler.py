"""
Tests for teloce_npm.bundler.minifyjs_bundler.MinifyJSBundler.

Scope: config handling, entry-point resolution, output collection, and
error paths. The actual esbuild binary is NOT invoked — instead, the
minifyjs.bundle function is mocked so tests run fast and deterministically.

If minifyjs is not installed, the tests that require it are skipped.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from teloce_npm.bundler.minifyjs_bundler import (
    MinifyJSBundler,
    MinifyJSNotAvailable,
    _diag_severity,
    _diag_text,
)
from teloce_npm.utils.errors import TeloceNpmError

# Skip the whole file if minifyjs isn't installed — but the import
# path we mock against is `teloce_npm.bundler.minifyjs_bundler._import_minifyjs`
# so we can still test config/entrypoint logic even without minifyjs.
try:
    import minifyjs  # noqa: F401

    HAS_MINIFYJS = True
except ImportError:
    HAS_MINIFYJS = False


def _make_package(tmp_path, package_json: dict, entry_content: str = "export default 42;"):
    """Create a minimal extracted package directory."""
    pkg_dir = tmp_path / "package"
    pkg_dir.mkdir()
    (pkg_dir / "package.json").write_text(json.dumps(package_json), encoding="utf-8")
    entry_name = package_json.get("main") or package_json.get("module") or "index.js"
    (pkg_dir / entry_name).write_text(entry_content, encoding="utf-8")
    return pkg_dir


def _mock_result(output_file: Path, diagnostics=None):
    """Build a fake MinifyJS Result."""
    result = MagicMock()
    result.has_errors = False
    result.diagnostics = diagnostics or []
    result.bytes_saved = 100
    return result


# ---------------------------------------------------------------------------
# Config parsing
# ---------------------------------------------------------------------------
def test_default_config_is_applied():
    b = MinifyJSBundler()
    assert b.minify is True
    assert b.target == "es2020"
    assert b.format == "esm"
    assert b.platform == "browser"
    assert b.splitting is False
    assert b.tree_shaking is True
    assert b.packages == "bundle"


def test_custom_config_is_respected():
    b = MinifyJSBundler(
        {
            "minify": False,
            "target": "es2018",
            "format": "iife",
            "splitting": True,
            "platform": "neutral",
            "sourcemap": "inline",
            "tree_shaking": False,
            "packages": "external",
            "external": ["react"],
            "define": {"process.env.NODE_ENV": '"production"'},
            "drop": ["console"],
        }
    )
    assert b.minify is False
    assert b.target == "es2018"
    assert b.format == "iife"
    assert b.splitting is True
    assert b.platform == "neutral"
    assert b.sourcemap == "inline"
    assert b.tree_shaking is False
    assert b.packages == "external"
    assert b.external == ["react"]
    assert b.define == {"process.env.NODE_ENV": '"production"'}
    assert b.drop == ["console"]


# ---------------------------------------------------------------------------
# Entry-point resolution
# ---------------------------------------------------------------------------
def test_resolve_entry_uses_module_field(tmp_path):
    pkg = _make_package(
        tmp_path,
        {"name": "x", "module": "esm.js", "main": "cjs.js"},
        entry_content="export default 1;",
    )
    (pkg / "esm.js").write_text("export default 1;", encoding="utf-8")
    (pkg / "cjs.js").write_text("module.exports = 1;", encoding="utf-8")

    b = MinifyJSBundler()
    entry = b._resolve_entry(pkg, "x")
    assert entry.name == "esm.js"


def test_resolve_entry_falls_back_to_main(tmp_path):
    pkg = _make_package(tmp_path, {"name": "x", "main": "index.js"})

    b = MinifyJSBundler()
    entry = b._resolve_entry(pkg, "x")
    assert entry.name == "index.js"


def test_resolve_entry_falls_back_to_index(tmp_path):
    pkg = _make_package(tmp_path, {"name": "x"})
    (pkg / "index.js").write_text("var x = 1;", encoding="utf-8")

    b = MinifyJSBundler()
    entry = b._resolve_entry(pkg, "x")
    assert entry.name == "index.js"


def test_resolve_entry_missing_package_json_raises(tmp_path):
    pkg = tmp_path / "package"
    pkg.mkdir()

    b = MinifyJSBundler()
    with pytest.raises(TeloceNpmError, match=r"No package\.json"):
        b._resolve_entry(pkg, "x")


def test_resolve_entry_invalid_json_raises(tmp_path):
    pkg = tmp_path / "package"
    pkg.mkdir()
    (pkg / "package.json").write_text("{ not json", encoding="utf-8")

    b = MinifyJSBundler()
    with pytest.raises(TeloceNpmError, match=r"Invalid package\.json"):
        b._resolve_entry(pkg, "x")


def test_resolve_entry_no_matches_raises(tmp_path):
    pkg = _make_package(tmp_path, {"name": "x", "main": "missing.js"})
    (pkg / "missing.js").unlink()

    b = MinifyJSBundler()
    with pytest.raises(TeloceNpmError, match="Could not resolve entry"):
        b._resolve_entry(pkg, "x")


# ---------------------------------------------------------------------------
# bundle_package — happy paths
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not HAS_MINIFYJS, reason="minifyjs not installed")
def test_bundle_package_writes_output(tmp_path):
    pkg = _make_package(tmp_path, {"name": "lodash", "main": "index.js"})
    out_dir = tmp_path / "dist"

    b = MinifyJSBundler({"minify": True})
    result = b.bundle_package(pkg, "lodash", out_dir)

    assert result["output_files"], "bundle should produce at least one file"
    assert all(Path(p).exists() for p in result["output_files"])
    assert result["bundle_dir"] == out_dir / "lodash"


@pytest.mark.skipif(not HAS_MINIFYJS, reason="minifyjs not installed")
def test_bundle_package_preserves_scoped_name(tmp_path):
    pkg = _make_package(tmp_path, {"name": "@scope/pkg", "main": "index.js"})
    out_dir = tmp_path / "dist"

    b = MinifyJSBundler()
    result = b.bundle_package(pkg, "@scope/pkg", out_dir)

    assert result["bundle_dir"].name == "scope_pkg"


# ---------------------------------------------------------------------------
# bundle_package — mocked bundle() to test error paths without esbuild
# ---------------------------------------------------------------------------
def test_bundle_package_missing_minifyjs_raises(tmp_path):
    pkg = _make_package(tmp_path, {"name": "x", "main": "index.js"})

    b = MinifyJSBundler()
    with (
        patch(
            "teloce_npm.bundler.minifyjs_bundler._import_minifyjs",
            side_effect=MinifyJSNotAvailable("minifyjs is not installed"),
        ),
        pytest.raises(MinifyJSNotAvailable, match="not installed"),
    ):
        b.bundle_package(pkg, "x", tmp_path / "dist")


def test_bundle_package_bundle_error_raises(tmp_path):
    pkg = _make_package(tmp_path, {"name": "x", "main": "index.js"})

    class FakeBundleError(Exception):
        pass

    def fake_import():
        def fake_bundle(**kwargs):
            raise FakeBundleError("esbuild failed")

        return fake_bundle, FakeBundleError

    b = MinifyJSBundler()
    with (
        patch(
            "teloce_npm.bundler.minifyjs_bundler._import_minifyjs",
            side_effect=fake_import,
        ),
        pytest.raises(TeloceNpmError, match="MinifyJS failed to bundle"),
    ):
        b.bundle_package(pkg, "x", tmp_path / "dist")


def test_bundle_package_diagnostics_with_error_raises(tmp_path):
    pkg = _make_package(tmp_path, {"name": "x", "main": "index.js"})

    class FakeBundleError(Exception):
        pass

    # Fake diagnostic object with severity="error"
    class FakeDiag:
        severity = "error"
        text = "Unresolved import './missing'"

    def fake_import():
        def fake_bundle(**kwargs):
            result = MagicMock()
            result.has_errors = True
            result.diagnostics = [FakeDiag()]
            result.bytes_saved = 0
            return result

        return fake_bundle, FakeBundleError

    b = MinifyJSBundler()
    with (
        patch(
            "teloce_npm.bundler.minifyjs_bundler._import_minifyjs",
            side_effect=fake_import,
        ),
        pytest.raises(TeloceNpmError, match="Bundle errors"),
    ):
        b.bundle_package(pkg, "x", tmp_path / "dist")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def test_safe_name_replaces_special_chars():
    assert MinifyJSBundler._safe_name("@scope/pkg") == "scope_pkg"
    assert MinifyJSBundler._safe_name("chart.js") == "chart_js"
    assert MinifyJSBundler._safe_name("lodash") == "lodash"


def test_diag_severity_handles_object():
    diag = MagicMock()
    diag.severity = "ERROR"
    assert _diag_severity(diag) == "error"


def test_diag_severity_handles_dict():
    assert _diag_severity({"severity": "warning"}) == "warning"


def test_diag_severity_handles_missing():
    assert _diag_severity(object()) == ""


def test_diag_text_handles_object():
    diag = MagicMock()
    diag.text = "some issue"
    assert _diag_text(diag) == "some issue"


def test_diag_text_handles_dict():
    assert _diag_text({"text": "boom"}) == "boom"


def test_diag_text_falls_back_to_str():
    assert "no text" in _diag_text("no text attr here")
