"""`entry_html: null`: hosts that generate their own page (Flaxon, SSR) get the tags printed, not injected."""

import json

import pytest

from teloce_npm.commands.clean import CleanCommand
from teloce_npm.commands.doctor import DoctorCommand
from teloce_npm.commands.install import InstallCommand
from teloce_npm.config import load_config
from teloce_npm.utils.errors import ConfigError

from ._helpers import fake_install


def _project(tmp_path, extra=None):
    (tmp_path / "ui").mkdir()
    (tmp_path / "ui" / "app.html").write_text(
        "Use dayjs from teloce-npm\n\n<template><p>x</p></template>\n", encoding="utf-8"
    )
    config = {
        "entry_html": None,
        "output_dir": "public/teloce-npm",
        "base_path": "/teloce-npm",
        **(extra or {}),
    }
    (tmp_path / "teloce-npm.json").write_text(json.dumps(config), encoding="utf-8")
    return tmp_path


def test_null_entry_html_loads_as_none(tmp_path):
    root = _project(tmp_path)
    assert load_config(root)["entry_html"] is None


@pytest.mark.parametrize("bad", ["", 5, ["x"]])
def test_other_invalid_entry_html_values_still_fail(tmp_path, bad):
    root = _project(tmp_path, {"entry_html": bad})
    with pytest.raises(ConfigError):
        load_config(root)


def test_install_prints_the_tags_and_changes_no_html(tmp_path, monkeypatch, capsys):
    root = _project(tmp_path)
    monkeypatch.setattr(InstallCommand, "_install_package", fake_install)
    assert InstallCommand(root).execute() == 0
    out = capsys.readouterr().out
    assert "entry_html is null" in out
    assert '<script src="/teloce-npm/loader.js" defer></script>' in out
    assert '<script src="/teloce-npm/use.js" defer></script>' in out
    assert (root / "public" / "teloce-npm" / "loader.js").exists()
    assert not list(root.rglob("*.html")) or [p.name for p in root.rglob("*.html")] == ["app.html"]
    assert "TELOCE-NPM-START" not in (root / "ui" / "app.html").read_text()


def test_doctor_and_clean_work_without_an_entry_html(tmp_path, monkeypatch, capsys):
    root = _project(tmp_path)
    monkeypatch.setattr(InstallCommand, "_install_package", fake_install)
    InstallCommand(root).execute()
    capsys.readouterr()
    assert DoctorCommand(project_root=root).execute() == 0
    assert "entry_html is null" in capsys.readouterr().out
    assert CleanCommand(project_root=root).execute() == 0
    assert not (root / "public" / "teloce-npm").exists()
