"""
Tests for teloce_npm.commands.add.AddCommand.

Scope: `add` is a thin alias for `install <pkg>`. Verify delegation.
"""

from unittest.mock import patch

from teloce_npm.commands.add import AddCommand
from teloce_npm.commands.install import InstallCommand

from ._helpers import setup_project


def test_add_delegates_to_install(tmp_path):
    root = setup_project(tmp_path)
    captured = {}

    def fake_execute(self, packages=None, production=False, verbose=False, no_verify=False):
        captured["packages"] = packages
        captured["no_verify"] = no_verify
        return 0

    with patch.object(InstallCommand, "execute", fake_execute):
        result = AddCommand(root).execute("lodash")

    assert result == 0
    assert captured["packages"] == ["lodash"]
    assert captured["no_verify"] is False


def test_add_passes_no_verify_flag(tmp_path):
    root = setup_project(tmp_path)
    captured = {}

    def fake_execute(self, packages=None, production=False, verbose=False, no_verify=False):
        captured["no_verify"] = no_verify
        return 0

    with patch.object(InstallCommand, "execute", fake_execute):
        AddCommand(root).execute("lodash", options={"no_verify": True})

    assert captured["no_verify"] is True


def test_add_accepts_version_spec(tmp_path):
    root = setup_project(tmp_path)
    captured = {}

    def fake_execute(self, packages=None, production=False, verbose=False, no_verify=False):
        captured["packages"] = packages
        return 0

    with patch.object(InstallCommand, "execute", fake_execute):
        AddCommand(root).execute("lodash@4.17.21")

    assert captured["packages"] == ["lodash@4.17.21"]
