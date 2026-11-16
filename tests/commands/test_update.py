"""
Tests for teloce_npm.commands.update.UpdateCommand.

Scope: version bumping logic. Registry + install are mocked.
"""

import json

from teloce_npm.commands.install import InstallCommand
from teloce_npm.commands.update import UpdateCommand
from teloce_npm.registry import RegistryClient

from ._helpers import fake_metadata, setup_project


def _setup_installed(tmp_path, packages=None):
    if packages is None:
        packages = {"lodash": "1.0.0"}
    root = setup_project(tmp_path, packages=list(packages.keys()))
    (root / "teloce-npm.lock").write_text(
        json.dumps(
            {
                "lockfile_version": "1.0.0",
                "generated_at": "2025-01-01T00:00:00Z",
                "packages": {
                    name: {
                        "version": ver,
                        "resolved": f"https://fake/{name}.tgz",
                        "integrity": f"sha512-{name}",
                        "dependencies": {},
                        "wrapped": f"{name}.js",
                        "size": 100,
                        "scanned_at": "2025-01-01T00:00:00Z",
                        "scan_result": "clean",
                    }
                    for name, ver in packages.items()
                },
            }
        ),
        encoding="utf-8",
    )
    return root


def test_update_all_reports_no_packages_when_empty(tmp_path, capsys):
    root = setup_project(tmp_path)  # no packages in lockfile
    result = UpdateCommand(root).execute()
    assert result == 0
    captured = capsys.readouterr()
    assert "No packages to update" in captured.out


def test_update_skips_already_latest(tmp_path, monkeypatch, capsys):
    root = _setup_installed(tmp_path, {"lodash": "4.17.21"})

    monkeypatch.setattr(
        RegistryClient,
        "get_package_metadata",
        lambda self, name: fake_metadata(name, version="4.17.21"),
    )

    install_calls = []

    def fake_install(self, name, version_range, no_verify, ignore_lock=False):
        install_calls.append(name)
        return version_range.lstrip("=")

    monkeypatch.setattr(InstallCommand, "_install_package", fake_install)

    UpdateCommand(root).execute()

    captured = capsys.readouterr()
    assert "UP-TO-DATE" in captured.out
    assert install_calls == []


def test_update_bumps_version(tmp_path, monkeypatch, capsys):
    root = _setup_installed(tmp_path, {"lodash": "1.0.0"})

    monkeypatch.setattr(
        RegistryClient,
        "get_package_metadata",
        lambda self, name: fake_metadata(name, version="2.0.0"),
    )

    install_calls = []

    def fake_install(self, name, version_range, no_verify, ignore_lock=False):
        # `update` must replace the lock entry, not be pinned to it.
        assert ignore_lock is True
        install_calls.append((name, version_range))
        return "2.0.0"

    monkeypatch.setattr(InstallCommand, "_install_package", fake_install)

    UpdateCommand(root).execute()

    captured = capsys.readouterr()
    assert "UPDATE" in captured.out
    assert install_calls == [("lodash", "=2.0.0")]


def _registry_with(monkeypatch, versions, latest):
    metadata = {
        "name": "lodash",
        "dist-tags": {"latest": latest},
        "versions": {v: {} for v in versions},
    }
    monkeypatch.setattr(RegistryClient, "get_package_metadata", lambda self, name: metadata)


def test_update_respects_the_range_in_config(tmp_path, monkeypatch, capsys):
    root = _setup_installed(tmp_path, {"lodash": "4.0.0"})
    (root / "teloce-npm.json").write_text(
        json.dumps({"packages": ["lodash@^4.0.0"]}), encoding="utf-8"
    )
    _registry_with(monkeypatch, ["4.0.0", "4.17.21", "5.0.0"], latest="5.0.0")
    installed = []

    def fake_install(self, name, version_range, no_verify, ignore_lock=False):
        installed.append(version_range)
        return version_range.lstrip("=")

    monkeypatch.setattr(InstallCommand, "_install_package", fake_install)
    assert UpdateCommand(root).execute() == 0
    assert installed == ["=4.17.21"]  # never 5.0.0


def test_update_without_a_range_follows_latest(tmp_path, monkeypatch):
    root = _setup_installed(tmp_path, {"lodash": "4.0.0"})
    _registry_with(monkeypatch, ["4.0.0", "5.0.0"], latest="5.0.0")
    installed = []

    def fake_install(self, name, version_range, no_verify, ignore_lock=False):
        installed.append(version_range)
        return version_range.lstrip("=")

    monkeypatch.setattr(InstallCommand, "_install_package", fake_install)
    UpdateCommand(root).execute()
    assert installed == ["=5.0.0"]


def test_blocked_update_is_reported_and_fails_the_command(tmp_path, monkeypatch, capsys):
    root = _setup_installed(tmp_path, {"lodash": "4.0.0"})
    _registry_with(monkeypatch, ["4.0.0", "5.0.0"], latest="5.0.0")
    monkeypatch.setattr(InstallCommand, "_install_package", lambda self, *a, **k: None)
    assert UpdateCommand(root).execute() == 1
    out = capsys.readouterr().out
    assert "[FAILED] lodash" in out and "keeping 4.0.0" in out
    assert "0 package(s) updated" in out
