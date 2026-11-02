"""
Tests for teloce_npm.commands.info.InfoCommand.

Scope: registry query + output formatting. Registry mocked.
"""

from unittest.mock import patch

import pytest

from teloce_npm.commands.info import InfoCommand
from teloce_npm.registry import RegistryClient
from ._helpers import fake_metadata


def _setup_project(tmp_path):
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "index.html").write_text("<html></html>")
    (tmp_path / "teloce-npm.json").write_text("{}", encoding="utf-8")
    return tmp_path


def test_info_prints_package_details(tmp_path, monkeypatch, capsys):
    root = _setup_project(tmp_path)
    monkeypatch.setattr(
        RegistryClient, "get_package_metadata",
        lambda self, name: fake_metadata(name, version="4.17.21", description="Utility"),
    )

    result = InfoCommand(root).execute("lodash")

    captured = capsys.readouterr()
    assert result == 0
    assert "lodash@4.17.21" in captured.out
    assert "Utility" in captured.out


def test_info_reports_install_scripts(tmp_path, monkeypatch, capsys):
    root = _setup_project(tmp_path)
    meta = fake_metadata("evil", version="1.0.0")
    meta["versions"]["1.0.0"]["scripts"] = {"postinstall": "curl evil"}
    monkeypatch.setattr(
        RegistryClient, "get_package_metadata", lambda self, name: meta
    )

    InfoCommand(root).execute("evil")

    captured = capsys.readouterr()
    assert "BLOCKED" in captured.out or "postinstall" in captured.out


def test_info_handles_missing_package(tmp_path, monkeypatch, capsys):
    from teloce_npm.utils.errors import PackageNotFoundError
    root = _setup_project(tmp_path)

    def fail(self, name):
        raise PackageNotFoundError("not found")
    monkeypatch.setattr(RegistryClient, "get_package_metadata", fail)

    result = InfoCommand(root).execute("missing")

    assert result == 1