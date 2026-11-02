"""
Tests for teloce_npm.commands.list.ListCommand.

Scope: output formatting. Uses a pre-populated lockfile.
"""

import json

from teloce_npm.commands.list import ListCommand


def _setup_lockfile(tmp_path, packages):
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "index.html").write_text("<html></html>")
    (tmp_path / "teloce-npm.json").write_text("{}", encoding="utf-8")
    (tmp_path / "teloce-npm.lock").write_text(
        json.dumps({
            "lockfile_version": "1.0.0",
            "generated_at": "2025-01-01T00:00:00Z",
            "packages": packages,
        }),
        encoding="utf-8",
    )


def _entry(version, size):
    return {
        "version": version,
        "resolved": f"https://fake/{version}.tgz",
        "integrity": "sha512-x",
        "dependencies": {},
        "wrapped": "pkg.js",
        "size": size,
        "scanned_at": "2025-01-01T00:00:00Z",
        "scan_result": "clean",
    }


def test_list_empty_prints_no_packages(tmp_path, capsys):
    _setup_lockfile(tmp_path, {})

    result = ListCommand(tmp_path).execute()

    captured = capsys.readouterr()
    assert result == 0
    assert "No packages installed" in captured.out


def test_list_shows_installed_packages(tmp_path, capsys):
    _setup_lockfile(tmp_path, {
        "lodash": _entry("4.17.21", 1024),
        "dayjs": _entry("1.11.0", 512),
    })

    ListCommand(tmp_path).execute()

    captured = capsys.readouterr()
    assert "lodash@4.17.21" in captured.out
    assert "dayjs@1.11.0" in captured.out
    assert "Total: 2 package(s)" in captured.out


def test_list_formats_sizes(tmp_path, capsys):
    _setup_lockfile(tmp_path, {
        "a": _entry("1.0.0", 500),
        "b": _entry("1.0.0", 2048),
    })

    ListCommand(tmp_path).execute()

    captured = capsys.readouterr()
    assert "500.0 B" in captured.out or "500 B" in captured.out
    assert "2.0 KB" in captured.out