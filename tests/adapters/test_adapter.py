"""
Tests for teloce_npm.adapters.adapter.ProjectAdapter.

Scope: path resolution, base_path derivation, injection delegation,
and factory behavior. No network, no registry, no bundling.
"""

import pytest

from teloce_npm.adapters import ProjectAdapter, get_adapter
from teloce_npm.utils.errors import ConfigError


def _make_config(project_root, **overrides):
    """Build a config dict matching the shape returned by load_config()."""
    config = {
        "packages": [],
        "entry_html": (project_root / "templates" / "index.html").resolve(),
        "output_dir": (project_root / "dist" / "static" / "teloce-npm").resolve(),
        "cache_dir": (project_root / ".teloce-npm" / "cache").resolve(),
        "registry": "https://registry.npmjs.org",
        "base_path": None,
        "security": {
            "verify_integrity": True,
            "scan_malware": True,
            "block_install_scripts": True,
            "check_vulnerabilities": True,
        },
        "bundling": {
            "mode": "auto",
            "minify": True,
            "target": "es2020",
            "format": "esm",
            "sourcemap": None,
            "splitting": False,
            "platform": "browser",
        },
        "_project_root": project_root,
    }
    config.update(overrides)
    return config


def _make_project(tmp_path, entry_html_name="index.html"):
    (tmp_path / "templates").mkdir(exist_ok=True)
    (tmp_path / "templates" / entry_html_name).write_text(
        "<!DOCTYPE html><html><head></head><body></body></html>",
        encoding="utf-8",
    )
    return tmp_path


# ---------------------------------------------------------------------------
# prepare()
# ---------------------------------------------------------------------------
def test_prepare_returns_paths(tmp_path):
    root = _make_project(tmp_path)
    adapter = ProjectAdapter(_make_config(root), root)

    paths = adapter.prepare()

    assert paths["entry_html"] == root / "templates" / "index.html"
    assert paths["output_dir"] == root / "dist" / "static" / "teloce-npm"
    assert "base_path" in paths


def test_prepare_creates_output_dir(tmp_path):
    root = _make_project(tmp_path)
    adapter = ProjectAdapter(_make_config(root), root)

    adapter.prepare()

    assert (root / "dist" / "static" / "teloce-npm").is_dir()


def test_prepare_missing_entry_html_raises(tmp_path):
    root = tmp_path
    (root / "templates").mkdir()
    # No index.html created

    adapter = ProjectAdapter(_make_config(root), root)
    with pytest.raises(ConfigError, match="not found"):
        adapter.prepare()


def test_prepare_directory_as_entry_html_raises(tmp_path):
    root = tmp_path
    (root / "templates" / "index.html").mkdir(parents=True)

    adapter = ProjectAdapter(_make_config(root), root)
    with pytest.raises(ConfigError, match="not a file"):
        adapter.prepare()


# ---------------------------------------------------------------------------
# get_base_path()
# ---------------------------------------------------------------------------
def test_base_path_explicit_override(tmp_path):
    root = _make_project(tmp_path)
    cfg = _make_config(root, base_path="/my/custom/prefix")
    adapter = ProjectAdapter(cfg, root)

    assert adapter.get_base_path() == "/my/custom/prefix"


def test_base_path_strips_trailing_slash(tmp_path):
    root = _make_project(tmp_path)
    cfg = _make_config(root, base_path="/my/prefix/")
    adapter = ProjectAdapter(cfg, root)

    assert adapter.get_base_path() == "/my/prefix"


def test_base_path_auto_derives_from_output_dir(tmp_path):
    root = _make_project(tmp_path)
    cfg = _make_config(root)  # base_path=None, output_dir=dist/static/teloce-npm
    adapter = ProjectAdapter(cfg, root)

    # Should extract from "static" onwards
    assert adapter.get_base_path() == "/static/teloce-npm"


def test_base_path_derives_when_static_in_middle(tmp_path):
    root = _make_project(tmp_path)
    cfg = _make_config(
        root,
        output_dir=(root / "build" / "static" / "teloce-npm").resolve(),
    )
    adapter = ProjectAdapter(cfg, root)

    assert adapter.get_base_path() == "/static/teloce-npm"


def test_base_path_fallback_when_no_static(tmp_path):
    root = _make_project(tmp_path)
    cfg = _make_config(
        root,
        output_dir=(root / "custom-out").resolve(),
    )
    adapter = ProjectAdapter(cfg, root)

    assert adapter.get_base_path() == "/static/teloce-npm"


# ---------------------------------------------------------------------------
# File path helpers
# ---------------------------------------------------------------------------
def test_wrapped_file_path_simple_name(tmp_path):
    root = _make_project(tmp_path)
    adapter = ProjectAdapter(_make_config(root), root)

    path = adapter.wrapped_file_path("lodash")
    assert path.name == "lodash.js"
    assert path.parent == adapter.output_dir


def test_wrapped_file_path_scoped_package(tmp_path):
    root = _make_project(tmp_path)
    adapter = ProjectAdapter(_make_config(root), root)

    path = adapter.wrapped_file_path("@types/node")
    assert path.name == "types_node.js"


def test_wrapped_file_path_dots_and_dashes(tmp_path):
    root = _make_project(tmp_path)
    adapter = ProjectAdapter(_make_config(root), root)

    assert adapter.wrapped_file_path("chart.js").name == "chart_js.js"
    assert adapter.wrapped_file_path("date-fns").name == "date_fns.js"


def test_manifest_path(tmp_path):
    root = _make_project(tmp_path)
    adapter = ProjectAdapter(_make_config(root), root)
    assert adapter.manifest_path().name == "manifest.json"


def test_use_js_path(tmp_path):
    root = _make_project(tmp_path)
    adapter = ProjectAdapter(_make_config(root), root)
    assert adapter.use_js_path().name == "use.js"


def test_loader_js_path(tmp_path):
    root = _make_project(tmp_path)
    adapter = ProjectAdapter(_make_config(root), root)
    assert adapter.loader_js_path().name == "loader.js"


# ---------------------------------------------------------------------------
# inject_scripts() / remove_scripts()
# ---------------------------------------------------------------------------
def test_inject_scripts_modifies_html(tmp_path):
    root = _make_project(tmp_path)
    adapter = ProjectAdapter(_make_config(root), root)
    adapter.prepare()

    adapter.inject_scripts()

    content = (root / "templates" / "index.html").read_text(encoding="utf-8")
    assert "TELOCE-NPM-START" in content
    assert "loader.js" in content


def test_inject_scripts_with_custom_base_path(tmp_path):
    root = _make_project(tmp_path)
    cfg = _make_config(root, base_path="/my/prefix")
    adapter = ProjectAdapter(cfg, root)
    adapter.prepare()

    adapter.inject_scripts()

    content = (root / "templates" / "index.html").read_text(encoding="utf-8")
    assert "/my/prefix/loader.js" in content


def test_remove_scripts_restores_html(tmp_path):
    root = _make_project(tmp_path)
    original = (root / "templates" / "index.html").read_text(encoding="utf-8")
    adapter = ProjectAdapter(_make_config(root), root)
    adapter.prepare()

    adapter.inject_scripts()
    adapter.remove_scripts()

    assert (root / "templates" / "index.html").read_text(encoding="utf-8") == original


# ---------------------------------------------------------------------------
# summary()
# ---------------------------------------------------------------------------
def test_summary_reports_paths(tmp_path):
    root = _make_project(tmp_path)
    adapter = ProjectAdapter(_make_config(root), root)
    adapter.prepare()

    summary = adapter.summary()

    assert summary["entry_html"]["exists"] is True
    assert summary["output_dir"]["exists"] is True
    assert summary["base_path"] == "/static/teloce-npm"


# ---------------------------------------------------------------------------
# get_adapter() factory
# ---------------------------------------------------------------------------
def test_get_adapter_derives_project_root_from_templates(tmp_path):
    root = _make_project(tmp_path)
    cfg = _make_config(root)
    # Remove _project_root to force derivation
    del cfg["_project_root"]

    adapter = get_adapter(cfg)

    assert adapter.project_root == root


def test_get_adapter_with_explicit_root(tmp_path):
    root = _make_project(tmp_path)
    adapter = get_adapter(_make_config(root), project_root=root)
    assert adapter.project_root == root
