"""
Tests for teloce_npm.commands.remove.RemoveCommand.

Scope: cleanup of cache, output, lockfile, config, and HTML injection.
"""

import json

from teloce_npm.commands.remove import RemoveCommand


def _setup_installed(tmp_path, packages=("lodash",)):
    """Set up a project with packages installed."""
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "index.html").write_text(
        "<html><head></head><body></body></html>", encoding="utf-8"
    )
    (tmp_path / "teloce-npm.json").write_text(
        json.dumps({"packages": list(packages)}), encoding="utf-8"
    )
    (tmp_path / "teloce-npm.lock").write_text(
        json.dumps(
            {
                "lockfile_version": "1.0.0",
                "generated_at": "2025-01-01T00:00:00Z",
                "packages": {
                    p: {
                        "version": "1.0.0",
                        "resolved": f"https://fake/{p}.tgz",
                        "integrity": f"sha512-{p}",
                        "dependencies": {},
                        "wrapped": f"{p}.js",
                        "size": 100,
                        "scanned_at": "2025-01-01T00:00:00Z",
                        "scan_result": "clean",
                    }
                    for p in packages
                },
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "dist" / "static" / "teloce-npm"
    out.mkdir(parents=True)
    for p in packages:
        (out / f"{p}.js").write_text(f"window['{p}'] = {{}};")
    return tmp_path


def test_remove_clears_config_entry(tmp_path):
    root = _setup_installed(tmp_path, packages=("lodash", "dayjs"))

    RemoveCommand(root).execute("lodash")

    config = json.loads((root / "teloce-npm.json").read_text())
    assert "lodash" not in config["packages"]
    assert "dayjs" in config["packages"]


def test_remove_clears_lockfile_entry(tmp_path):
    root = _setup_installed(tmp_path, packages=("lodash",))

    RemoveCommand(root).execute("lodash")

    lock = json.loads((root / "teloce-npm.lock").read_text())
    assert "lodash" not in lock["packages"]


def test_remove_deletes_wrapped_file(tmp_path):
    root = _setup_installed(tmp_path, packages=("lodash",))

    RemoveCommand(root).execute("lodash")

    assert not (root / "dist" / "static" / "teloce-npm" / "lodash.js").exists()


def test_remove_last_package_removes_html_injection(tmp_path):
    root = _setup_installed(tmp_path, packages=("lodash",))

    RemoveCommand(root).execute("lodash")

    html = (root / "templates" / "index.html").read_text()
    assert "TELOCE-NPM-START" not in html


def test_remove_keeps_html_when_other_packages_remain(tmp_path):
    root = _setup_installed(tmp_path, packages=("lodash", "dayjs"))
    # Prime the injection by simulating a prior install
    from teloce_npm.adapters import get_adapter
    from teloce_npm.config import load_config

    cfg = load_config(root)
    adapter = get_adapter(cfg, root)
    adapter.prepare()
    adapter.inject_scripts()

    RemoveCommand(root).execute("lodash")

    html = (root / "templates" / "index.html").read_text()
    assert "TELOCE-NPM-START" in html


def test_remove_unknown_package_returns_zero(tmp_path):
    root = _setup_installed(tmp_path, packages=("lodash",))

    result = RemoveCommand(root).execute("unknown-pkg")

    assert result == 0  # idempotent
