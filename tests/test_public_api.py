"""The Python helpers in `teloce_npm` (install, add, remove, ...)."""

import json

import teloce_npm
from teloce_npm.commands.install import InstallCommand

from .commands._helpers import fake_install, setup_project


def test_add_accepts_keyword_options(tmp_path, monkeypatch):
    root = setup_project(tmp_path)
    seen = {}

    def fake(self, name, version_range, no_verify, ignore_lock=False):
        seen["no_verify"] = no_verify
        return fake_install(self, name, version_range, no_verify)

    monkeypatch.setattr(InstallCommand, "_install_package", fake)
    assert teloce_npm.add("lodash", project_root=root, no_verify=True) == 0
    assert seen == {"no_verify": True}
    assert json.loads((root / "teloce-npm.json").read_text())["packages"] == ["lodash"]


def test_helpers_return_the_exit_code_and_honour_project_root(tmp_path, monkeypatch):
    root = setup_project(tmp_path)
    monkeypatch.setattr(InstallCommand, "_install_package", fake_install)
    (root / "teloce-npm.json").write_text(json.dumps({"packages": ["dayjs"]}), encoding="utf-8")
    assert teloce_npm.install(project_root=root) == 0
    assert teloce_npm.remove("dayjs", project_root=root) == 0
    assert teloce_npm.clean(project_root=root) == 0
