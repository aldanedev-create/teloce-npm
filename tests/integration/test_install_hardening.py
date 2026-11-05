"""End-to-end install behaviour: lockfile trust, frozen mode, cache scanning, vulnerabilities."""

import json

import pytest

from teloce_npm.commands.install import InstallCommand
from teloce_npm.registry import RegistryClient
from teloce_npm.utils.errors import PackageNotFoundError
from teloce_npm.utils.hashing import compute_sha512

from ._helpers import fake_registry_metadata, make_fake_tarball, setup_project


@pytest.fixture
def world(monkeypatch):
    """Offline registry whose integrity, vulnerabilities and missing packages can be changed per test."""
    tarball = make_fake_tarball()
    state = {"integrity": compute_sha512(tarball), "vulns": [], "missing": set(), "downloads": 0}

    def fake_download(tarball_url, dest_path, expected_integrity, **kwargs):
        state["downloads"] += 1
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(tarball)
        return dest_path

    def fake_metadata(self, name):
        if name in state["missing"]:
            raise PackageNotFoundError(name)
        return fake_registry_metadata(name, "4.17.21", state["integrity"])

    monkeypatch.setattr("teloce_npm.commands.install.download_tarball", fake_download)
    monkeypatch.setattr("teloce_npm.commands.install.wrap_package", lambda e, n: f"window['{n}'] = {{}};")
    monkeypatch.setattr("teloce_npm.commands.install.check_vulnerabilities", lambda n, v, **k: state["vulns"])
    monkeypatch.setattr(RegistryClient, "get_package_metadata", fake_metadata)
    return state


def _project(tmp_path, config=None):
    root = setup_project(tmp_path)
    (root / "teloce-npm.json").write_text(json.dumps({"packages": [], **(config or {})}), encoding="utf-8")
    return root


def _lock(root):
    return json.loads((root / "teloce-npm.lock").read_text())["packages"]


# ----------------------------------------------------------------- lockfile trust
def test_changed_registry_integrity_is_blocked_by_the_lockfile(tmp_path, world, capsys):
    root = _project(tmp_path)
    assert InstallCommand(root).execute() == 0
    locked = _lock(root)["lodash"]["integrity"]

    world["integrity"] = "sha512-" + "A" * 86 + "=="  # registry now serves different bytes
    (root / "dist").rename(tmp_path / "dist-old")  # force a rebuild, not just a cache copy
    code = InstallCommand(root).execute()

    out = capsys.readouterr().out
    assert code == 1
    assert "differs from the lockfile" in out
    assert _lock(root)["lodash"]["integrity"] == locked  # lock untouched


def test_lock_mismatch_check_can_be_turned_off(tmp_path, world):
    root = _project(tmp_path, {"security": {"require_lockfile_match": False}})
    assert InstallCommand(root).execute() == 0
    world["integrity"] = compute_sha512(make_fake_tarball()) + ""
    assert InstallCommand(root).execute() == 0


def test_update_replaces_the_lock_instead_of_being_pinned_to_it(tmp_path, world):
    root = _project(tmp_path)
    assert InstallCommand(root).execute() == 0

    world["integrity"] = compute_sha512(b"new release bytes")
    cmd = InstallCommand(root)
    cmd._setup()
    cmd.adapter.prepare()
    assert cmd._install_package("lodash", "*", no_verify=False) is None  # normal install: blocked
    assert cmd._install_package("lodash", "*", no_verify=False, ignore_lock=True) == "4.17.21"
    cmd.lockfile.save()
    assert _lock(root)["lodash"]["integrity"] == world["integrity"]


# ------------------------------------------------------------------- frozen mode
def test_frozen_install_fails_when_package_is_not_locked(tmp_path, world, capsys):
    root = _project(tmp_path)
    code = InstallCommand(root).execute(frozen=True)
    assert code == 1
    assert "--frozen-lockfile" in capsys.readouterr().out
    assert world["downloads"] == 0


def test_frozen_install_succeeds_with_a_matching_lock(tmp_path, world):
    root = _project(tmp_path)
    assert InstallCommand(root).execute() == 0
    assert InstallCommand(root).execute(frozen=True) == 0


# ---------------------------------------------------------------------- cache scan
def test_cache_from_unverified_install_is_rescanned(tmp_path, world, capsys):
    root = _project(tmp_path)
    assert InstallCommand(root).execute(no_verify=True) == 0
    cache = root / ".teloce-npm" / "cache"
    meta = json.loads(next(cache.glob("lodash@*/metadata.json")).read_text())
    assert meta["verified"] is False and meta["scan_result"] == "skipped"

    assert InstallCommand(root).execute() == 0  # normal run must not trust the unscanned entry
    out = capsys.readouterr().out
    assert "RESCAN" in out
    meta = json.loads(next(cache.glob("lodash@*/metadata.json")).read_text())
    assert meta["verified"] is True and meta["scan_result"] == "clean"


def test_cache_from_older_scanner_is_rescanned(tmp_path, world, capsys):
    root = _project(tmp_path)
    assert InstallCommand(root).execute() == 0
    meta_path = next((root / ".teloce-npm" / "cache").glob("lodash@*/metadata.json"))
    meta = json.loads(meta_path.read_text())
    meta["scanner_version"] = 0
    meta_path.write_text(json.dumps(meta))

    assert InstallCommand(root).execute() == 0
    assert "RESCAN" in capsys.readouterr().out


def test_verified_cache_is_reused(tmp_path, world, capsys):
    root = _project(tmp_path)
    assert InstallCommand(root).execute() == 0
    first = world["downloads"]
    assert InstallCommand(root).execute() == 0
    assert world["downloads"] == first
    assert "CACHED" in capsys.readouterr().out


# ---------------------------------------------------------------- vulnerabilities
CRITICAL = {"id": "GHSA-crit-0001", "summary": "RCE", "severity": "CRITICAL", "affected": []}
MEDIUM = {"id": "GHSA-med-0002", "summary": "ReDoS", "severity": "MEDIUM", "affected": []}


def test_critical_advisory_blocks_install(tmp_path, world, capsys):
    root = _project(tmp_path)
    world["vulns"] = [CRITICAL]
    assert InstallCommand(root).execute() == 1
    assert "critical advisory" in capsys.readouterr().out
    assert not (root / "teloce-npm.lock").exists() or "lodash" not in _lock(root)


def test_reviewed_advisory_id_is_allowed(tmp_path, world, capsys):
    root = _project(tmp_path, {"security": {"allow_vulnerabilities": ["GHSA-crit-0001"]}})
    world["vulns"] = [CRITICAL]
    assert InstallCommand(root).execute() == 0
    assert "VULN-ALLOWED" in capsys.readouterr().out


def test_non_critical_advisory_only_warns(tmp_path, world, capsys):
    root = _project(tmp_path)
    world["vulns"] = [MEDIUM]
    assert InstallCommand(root).execute() == 0
    assert "GHSA-med-0002" in capsys.readouterr().out


def test_fail_on_critical_can_be_disabled(tmp_path, world):
    root = _project(tmp_path, {"security": {"fail_on_critical": False}})
    world["vulns"] = [CRITICAL]
    assert InstallCommand(root).execute() == 0


def test_vulnerability_check_can_be_disabled(tmp_path, world, monkeypatch):
    called = []
    monkeypatch.setattr("teloce_npm.commands.install.check_vulnerabilities", lambda *a, **k: called.append(1) or [])
    root = _project(tmp_path, {"security": {"check_vulnerabilities": False}})
    assert InstallCommand(root).execute() == 0
    assert called == []


# ------------------------------------------------------------------- exit codes
def test_one_failed_package_makes_the_whole_install_fail(tmp_path, world, capsys):
    root = _project(tmp_path, {"packages": ["ghost-package"]})
    world["missing"] = {"ghost-package"}
    code = InstallCommand(root).execute()
    assert code == 1
    assert "FAILED: ghost-package" in capsys.readouterr().out
    assert "lodash" in _lock(root)  # the good package was still installed


def test_invalid_package_name_is_blocked(tmp_path, world, capsys):
    root = _project(tmp_path)
    cmd = InstallCommand(root)
    cmd._setup()
    assert cmd._install_package("../../etc/passwd", "*", no_verify=False) is None
    assert "Invalid npm package name" in capsys.readouterr().out
    assert world["downloads"] == 0
