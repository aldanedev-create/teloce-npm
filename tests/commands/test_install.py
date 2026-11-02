"""
Tests for teloce_npm.commands.install.InstallCommand.

Scope: orchestration (scan mode, specific-packages mode, config
mutation, generation, injection, lockfile save). The actual install
pipeline (download/extract/wrap) is mocked via `_install_package`.
"""

import json

import pytest

from teloce_npm.commands.install import InstallCommand
from ._helpers import setup_project, fake_install


# ---------------------------------------------------------------------------
# Scan mode
# ---------------------------------------------------------------------------
def test_scan_mode_with_no_uses_returns_zero(tmp_path, monkeypatch, capsys):
    root = setup_project(tmp_path)
    monkeypatch.setattr(InstallCommand, "_install_package", fake_install)

    result = InstallCommand(root).execute()

    assert result == 0
    captured = capsys.readouterr()
    assert "No packages declared" in captured.out


def test_scan_mode_picks_up_vel_declarations(tmp_path, monkeypatch, capsys):
    root = setup_project(tmp_path)
    (root / "static" / "js" / "App.vel").write_text(
        "Use lodash from teloce-npm\n", encoding="utf-8"
    )
    monkeypatch.setattr(InstallCommand, "_install_package", fake_install)

    result = InstallCommand(root).execute()

    assert result == 0
    captured = capsys.readouterr()
    assert "lodash" in captured.out


def test_scan_mode_uses_config_packages(tmp_path, monkeypatch):
    root = setup_project(tmp_path, packages=["dayjs"])
    monkeypatch.setattr(InstallCommand, "_install_package", fake_install)

    result = InstallCommand(root).execute()

    assert result == 0
    # dayjs should be installed (from config)
    lockfile = json.loads((root / "teloce-npm.lock").read_text())
    assert "dayjs" in lockfile["packages"]


def test_scan_mode_generates_runtime_files(tmp_path, monkeypatch):
    root = setup_project(tmp_path, packages=["lodash"])
    monkeypatch.setattr(InstallCommand, "_install_package", fake_install)

    InstallCommand(root).execute()

    out = root / "dist" / "static" / "teloce-npm"
    assert (out / "manifest.json").exists()
    assert (out / "use.js").exists()
    assert (out / "loader.js").exists()


def test_scan_mode_injects_into_html(tmp_path, monkeypatch):
    root = setup_project(tmp_path, packages=["lodash"])
    monkeypatch.setattr(InstallCommand, "_install_package", fake_install)

    InstallCommand(root).execute()

    html = (root / "templates" / "index.html").read_text()
    assert "TELOCE-NPM-START" in html


# ---------------------------------------------------------------------------
# Specific-packages mode
# ---------------------------------------------------------------------------
def test_specific_packages_installs_and_updates_config(tmp_path, monkeypatch):
    root = setup_project(tmp_path)
    monkeypatch.setattr(InstallCommand, "_install_package", fake_install)

    result = InstallCommand(root).execute(packages=["lodash"])

    assert result == 0
    config = json.loads((root / "teloce-npm.json").read_text())
    assert "lodash" in config["packages"]


def test_specific_packages_multiple(tmp_path, monkeypatch):
    root = setup_project(tmp_path)
    monkeypatch.setattr(InstallCommand, "_install_package", fake_install)

    result = InstallCommand(root).execute(packages=["lodash", "dayjs"])

    assert result == 0
    config = json.loads((root / "teloce-npm.json").read_text())
    assert "lodash" in config["packages"]
    assert "dayjs" in config["packages"]


def test_specific_packages_does_not_duplicate_config_entry(tmp_path, monkeypatch):
    root = setup_project(tmp_path, packages=["lodash"])
    monkeypatch.setattr(InstallCommand, "_install_package", fake_install)

    InstallCommand(root).execute(packages=["lodash"])

    config = json.loads((root / "teloce-npm.json").read_text())
    assert config["packages"].count("lodash") == 1


def test_specific_packages_version_spec_preserved_in_config(tmp_path, monkeypatch):
    root = setup_project(tmp_path)
    monkeypatch.setattr(InstallCommand, "_install_package", fake_install)

    InstallCommand(root).execute(packages=["lodash@4.17.21"])

    config = json.loads((root / "teloce-npm.json").read_text())
    assert "lodash@4.17.21" in config["packages"]


def test_specific_packages_failure_returns_one(tmp_path, monkeypatch):
    root = setup_project(tmp_path)

    def failing_install(self, name, version_range, no_verify):
        raise Exception("boom")

    monkeypatch.setattr(InstallCommand, "_install_package", failing_install)

    result = InstallCommand(root).execute(packages=["bad"])

    assert result == 1


# ---------------------------------------------------------------------------
# Lockfile behavior
# ---------------------------------------------------------------------------
def test_install_saves_lockfile_to_disk(tmp_path, monkeypatch):
    root = setup_project(tmp_path, packages=["lodash"])
    monkeypatch.setattr(InstallCommand, "_install_package", fake_install)

    InstallCommand(root).execute()

    assert (root / "teloce-npm.lock").exists()
    lock = json.loads((root / "teloce-npm.lock").read_text())
    assert "lodash" in lock["packages"]