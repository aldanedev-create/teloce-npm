"""
Integration test: verify that injection targets the configured
`entry_html`, not a hardcoded `index.html`.
"""

import json

import pytest

from teloce_npm.commands.install import InstallCommand
from teloce_npm.registry import RegistryClient
from teloce_npm.utils.hashing import compute_sha512

from ._helpers import fake_registry_metadata, make_fake_tarball, setup_project


@pytest.fixture
def mocked_pipeline(monkeypatch):
    tarball_bytes = make_fake_tarball()
    integrity = compute_sha512(tarball_bytes)

    def fake_download(tarball_url, dest_path, expected_integrity):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(tarball_bytes)
        return dest_path

    def fake_extract(tarball_path, extract_dir):
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


def test_injection_targets_custom_entry_html(tmp_path, mocked_pipeline):
    """Configure entry_html=layout.html — injection must go there, not index.html."""
    root = setup_project(
        tmp_path,
        entry_html="templates/layout.html",
        vel_content="Use lodash from teloce-npm\n",
    )
    # Write a decoy index.html that must NOT be modified
    (root / "templates" / "index.html").write_text(
        "<html><head></head><body>untouched</body></html>"
    )
    # Update config to point at layout.html
    config_data = json.loads((root / "teloce-npm.json").read_text())
    config_data["entry_html"] = "templates/layout.html"
    (root / "teloce-npm.json").write_text(json.dumps(config_data))

    InstallCommand(root).execute(no_verify=True)

    # layout.html must be injected
    layout = (root / "templates" / "layout.html").read_text()
    assert "TELOCE-NPM-START" in layout
    assert "loader.js" in layout

    # index.html must be untouched
    decoy = (root / "templates" / "index.html").read_text()
    assert "TELOCE-NPM-START" not in decoy


def test_injection_defaults_to_index_html(tmp_path, mocked_pipeline):
    """When entry_html is not configured, default is templates/index.html."""
    root = setup_project(tmp_path)  # uses default entry_html

    InstallCommand(root).execute(no_verify=True)

    html = (root / "templates" / "index.html").read_text()
    assert "TELOCE-NPM-START" in html


def test_injection_uses_configured_base_path(tmp_path, mocked_pipeline):
    """Custom base_path in config must appear in injected script URLs."""
    root = setup_project(
        tmp_path,
        vel_content="Use lodash from teloce-npm\n",
    )
    config_data = json.loads((root / "teloce-npm.json").read_text())
    config_data["base_path"] = "/custom/prefix"
    (root / "teloce-npm.json").write_text(json.dumps(config_data))

    InstallCommand(root).execute(no_verify=True)

    html = (root / "templates" / "index.html").read_text()
    assert "/custom/prefix/loader.js" in html
    assert "/custom/prefix/use.js" in html


def test_injection_appends_to_fragment_html(tmp_path, mocked_pipeline):
    """HTML without <head> or <body> should still get scripts appended."""
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "fragment.html").write_text("<div>partial content</div>")
    (tmp_path / "static" / "js").mkdir(parents=True)
    (tmp_path / "static" / "js" / "App.vel").write_text("Use lodash from teloce-npm\n")
    (tmp_path / "teloce-npm.json").write_text(
        json.dumps(
            {
                "entry_html": "templates/fragment.html",
            }
        )
    )

    InstallCommand(tmp_path).execute(no_verify=True)

    html = (tmp_path / "templates" / "fragment.html").read_text()
    assert "TELOCE-NPM-START" in html
    assert "<div>partial content</div>" in html  # original preserved
