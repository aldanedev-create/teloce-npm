"""
Tests for teloce_npm.commands.clean.CleanCommand.

Scope: full wipe of cache, output, lockfile, and HTML injection.
"""

import json

from teloce_npm.commands.clean import CleanCommand


def _setup_dirty(tmp_path):
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "index.html").write_text(
        "<html><head>"
        "<!-- TELOCE-NPM-START -->"
        '<script src="/static/teloce-npm/loader.js"></script>'
        "<!-- TELOCE-NPM-END -->"
        "</head></html>",
        encoding="utf-8",
    )
    (tmp_path / "teloce-npm.json").write_text("{}", encoding="utf-8")
    (tmp_path / "teloce-npm.lock").write_text(
        json.dumps({
            "lockfile_version": "1.0.0",
            "generated_at": "2025-01-01T00:00:00Z",
            "packages": {},
        }),
        encoding="utf-8",
    )
    (tmp_path / "dist" / "static" / "teloce-npm").mkdir(parents=True)
    (tmp_path / "dist" / "static" / "teloce-npm" / "lodash.js").write_text("x")
    (tmp_path / ".teloce-npm" / "cache").mkdir(parents=True)
    return tmp_path


def test_clean_removes_output_dir(tmp_path):
    root = _setup_dirty(tmp_path)

    CleanCommand(root).execute()

    assert not (root / "dist" / "static" / "teloce-npm").exists()


def test_clean_removes_lockfile(tmp_path):
    root = _setup_dirty(tmp_path)

    CleanCommand(root).execute()

    assert not (root / "teloce-npm.lock").exists()


def test_clean_removes_html_injection(tmp_path):
    root = _setup_dirty(tmp_path)

    CleanCommand(root).execute()

    html = (root / "templates" / "index.html").read_text()
    assert "TELOCE-NPM-START" not in html


def test_clean_removes_cache(tmp_path):
    root = _setup_dirty(tmp_path)

    CleanCommand(root).execute()

    cache_entries = list((root / ".teloce-npm" / "cache").iterdir())
    assert cache_entries == []