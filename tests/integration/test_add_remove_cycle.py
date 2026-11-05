"""
Integration test: add a package → verify state → remove → verify cleanup.
"""

import json

import pytest

from teloce_npm.commands.install import InstallCommand
from teloce_npm.commands.remove import RemoveCommand
from teloce_npm.registry import RegistryClient
from teloce_npm.utils.hashing import compute_sha512

from ._helpers import fake_registry_metadata, make_fake_tarball, setup_project


@pytest.fixture
def mocked_pipeline(monkeypatch):
    tarball_bytes = make_fake_tarball()
    integrity = compute_sha512(tarball_bytes)

    def fake_download(tarball_url, dest_path, expected_integrity, **kwargs):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(tarball_bytes)
        return dest_path

    def fake_extract(tarball_path, extract_dir, *args, **kwargs):
        from teloce_npm.downloader import extract_tarball

        return extract_tarball(tarball_path, extract_dir)

    def fake_wrap(extracted, name):
        return f"window['{name}'] = {{}};"

    def fake_get_metadata(self, name):
        return fake_registry_metadata(name, "4.17.21", integrity)

    monkeypatch.setattr("teloce_npm.commands.install.download_tarball", fake_download)
    monkeypatch.setattr("teloce_npm.commands.install.extract_tarball", fake_extract)
    monkeypatch.setattr("teloce_npm.commands.install.wrap_package", fake_wrap)
    monkeypatch.setattr(
        "teloce_npm.commands.install.check_vulnerabilities",
        lambda n, v: [],
    )
    monkeypatch.setattr(RegistryClient, "get_package_metadata", fake_get_metadata)


def test_add_then_remove_full_cleanup(tmp_path, mocked_pipeline):
    root = setup_project(tmp_path, vel_content="")  # no .vel uses yet

    # 1. Install lodash
    InstallCommand(root).execute(packages=["lodash"], no_verify=True)

    # Verify installed
    config = json.loads((root / "teloce-npm.json").read_text())
    assert "lodash" in config["packages"]
    assert (root / "dist/static/teloce-npm/lodash.js").exists()
    lock = json.loads((root / "teloce-npm.lock").read_text())
    assert "lodash" in lock["packages"]
    html = (root / "templates/index.html").read_text()
    assert "TELOCE-NPM-START" in html

    # 2. Remove lodash
    result = RemoveCommand(root).execute("lodash")
    assert result == 0

    # Verify all state is clean
    config = json.loads((root / "teloce-npm.json").read_text())
    assert "lodash" not in config["packages"]

    assert not (root / "dist/static/teloce-npm/lodash.js").exists()

    lock = json.loads((root / "teloce-npm.lock").read_text())
    assert "lodash" not in lock["packages"]

    html = (root / "templates/index.html").read_text()
    assert "TELOCE-NPM-START" not in html  # no packages remain


def test_add_multiple_then_remove_one_keeps_html(tmp_path, mocked_pipeline):
    root = setup_project(tmp_path, vel_content="")

    InstallCommand(root).execute(packages=["lodash", "dayjs"], no_verify=True)

    RemoveCommand(root).execute("lodash")

    # dayjs remains, so injection must remain
    html = (root / "templates/index.html").read_text()
    assert "TELOCE-NPM-START" in html

    lock = json.loads((root / "teloce-npm.lock").read_text())
    assert "lodash" not in lock["packages"]
    assert "dayjs" in lock["packages"]
