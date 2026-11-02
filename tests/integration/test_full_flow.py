"""
End-to-end integration test: .vel file → install → generate → inject.

Real pipeline runs: scanner, config, cache, lockfile, generator, injector.
Mocked boundaries: registry HTTP, downloader (avoids real network),
and wrapper (real Tree-sitter is tested separately).
"""

import json

import pytest

from teloce_npm.commands.install import InstallCommand
from teloce_npm.registry import RegistryClient
from teloce_npm.utils.hashing import compute_sha512

from ._helpers import fake_registry_metadata, make_fake_tarball, setup_project


@pytest.fixture
def mocked_pipeline(monkeypatch):
    """
    Mock all network + wrapping boundaries so the pipeline runs offline.

    Uses a real tarball bytes and matching integrity, so cache.store()
    and cache.has() don't invalidate on repeat runs.
    """
    tarball_bytes = make_fake_tarball()
    integrity = compute_sha512(tarball_bytes)

    def fake_download(tarball_url, dest_path, expected_integrity):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(tarball_bytes)
        return dest_path

    def fake_extract(tarball_path, extract_dir):
        # Let the real extractor run on the real tarball
        from teloce_npm.downloader import extract_tarball

        return extract_tarball(tarball_path, extract_dir)

    def fake_wrap(extracted, name):
        return f"window['{name}'] = {{}};"

    def fake_get_metadata(self, name):
        return fake_registry_metadata(name, "4.17.21", integrity)

    def fake_vulns(name, version):
        return []

    monkeypatch.setattr("teloce_npm.commands.install.download_tarball", fake_download)
    monkeypatch.setattr("teloce_npm.commands.install.extract_tarball", fake_extract)
    monkeypatch.setattr("teloce_npm.commands.install.wrap_package", fake_wrap)
    monkeypatch.setattr("teloce_npm.commands.install.check_vulnerabilities", fake_vulns)
    monkeypatch.setattr(RegistryClient, "get_package_metadata", fake_get_metadata)

    return {"tarball": tarball_bytes, "integrity": integrity}


def test_full_pipeline_creates_all_artifacts(tmp_path, mocked_pipeline):
    root = setup_project(tmp_path)

    result = InstallCommand(root).execute(no_verify=True)

    assert result == 0

    # 1. Output files exist
    out = root / "dist" / "static" / "teloce-npm"
    assert (out / "lodash.js").exists()
    assert (out / "manifest.json").exists()
    assert (out / "use.js").exists()
    assert (out / "loader.js").exists()

    # 2. Lockfile populated
    lock = json.loads((root / "teloce-npm.lock").read_text())
    assert "lodash" in lock["packages"]
    assert lock["packages"]["lodash"]["version"] == "4.17.21"

    # 3. Manifest is valid
    manifest = json.loads((out / "manifest.json").read_text())
    assert "lodash" in manifest["packages"]
    assert manifest["packages"]["lodash"]["file"] == "lodash.js"

    # 4. HTML injection
    html = (root / "templates" / "index.html").read_text()
    assert "TELOCE-NPM-START" in html
    assert "loader.js" in html
    assert "use.js" in html
    assert "TELOCE-NPM-END" in html


def test_full_pipeline_is_idempotent(tmp_path, mocked_pipeline):
    root = setup_project(tmp_path)

    InstallCommand(root).execute(no_verify=True)
    html_after_first = (root / "templates" / "index.html").read_text()

    InstallCommand(root).execute(no_verify=True)
    html_after_second = (root / "templates" / "index.html").read_text()

    # HTML should be identical (no duplicate markers)
    assert html_after_first == html_after_second
    assert html_after_first.count("TELOCE-NPM-START") == 1


def test_full_pipeline_preserves_developer_html(tmp_path, mocked_pipeline):
    root = setup_project(tmp_path)
    original_title = "<title>Test</title>"

    InstallCommand(root).execute(no_verify=True)

    html = (root / "templates" / "index.html").read_text()
    assert original_title in html
    assert "<div id='app'></div>" in html


def test_full_pipeline_second_install_hits_cache(tmp_path, mocked_pipeline, capsys):
    root = setup_project(tmp_path)

    InstallCommand(root).execute(no_verify=True)
    capsys.readouterr()  # clear

    InstallCommand(root).execute(no_verify=True)
    captured = capsys.readouterr()

    # Second install should hit cache
    assert "CACHED" in captured.out
