"""
Tests for teloce_npm.registry.client.RegistryClient.

Scope: HTTP behavior only. All requests are mocked.
Does NOT test metadata parsing (test_metadata.py).
Does NOT test version resolution (test_version_resolver.py).
"""

from unittest.mock import MagicMock

import pytest
import requests

from teloce_npm.registry import RegistryClient
from teloce_npm.utils.errors import RegistryError, PackageNotFoundError


def _mock_response(status=200, json_data=None):
    """Build a MagicMock that mimics requests.Response."""
    resp = MagicMock()
    resp.status_code = status
    if status >= 400:
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f"HTTP {status}"
        )
    resp.json.return_value = json_data or {}
    return resp


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------
def test_client_strips_trailing_slash():
    client = RegistryClient("https://registry.npmjs.org/")
    assert client.registry_url == "https://registry.npmjs.org"


def test_client_sets_user_agent_header():
    client = RegistryClient("https://registry.npmjs.org")
    ua = client.session.headers.get("User-Agent", "")
    assert ua.startswith("Teloce-NPM/")


def test_client_sets_accept_json_header():
    client = RegistryClient("https://registry.npmjs.org")
    assert client.session.headers.get("Accept") == "application/json"


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------
def test_get_package_metadata_returns_json(monkeypatch):
    client = RegistryClient("https://registry.npmjs.org")
    expected = {"name": "lodash", "versions": {}}
    monkeypatch.setattr(client.session, "get", lambda *a, **k: _mock_response(json_data=expected))

    result = client.get_package_metadata("lodash")

    assert result == expected


def test_get_package_metadata_encodes_scoped_package(monkeypatch):
    client = RegistryClient("https://registry.npmjs.org")
    captured = {}

    def fake_get(url, **kwargs):
        captured["url"] = url
        return _mock_response(json_data={"name": "@types/node"})

    monkeypatch.setattr(client.session, "get", fake_get)
    client.get_package_metadata("@types/node")

    # '/' must be encoded to %2F, '@' to %40
    assert "@types" not in captured["url"]
    assert "%40types%2Fnode" in captured["url"]


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------
def test_get_package_metadata_404_raises_package_not_found(monkeypatch):
    client = RegistryClient("https://registry.npmjs.org")
    monkeypatch.setattr(client.session, "get", lambda *a, **k: _mock_response(status=404))

    with pytest.raises(PackageNotFoundError, match="not found"):
        client.get_package_metadata("does-not-exist")


def test_get_package_metadata_500_raises_registry_error(monkeypatch):
    client = RegistryClient("https://registry.npmjs.org")
    monkeypatch.setattr(client.session, "get", lambda *a, **k: _mock_response(status=500))

    with pytest.raises(RegistryError, match="Network error"):
        client.get_package_metadata("broken")


def test_get_package_metadata_timeout_raises_registry_error(monkeypatch):
    client = RegistryClient("https://registry.npmjs.org")

    def fake_get(*args, **kwargs):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr(client.session, "get", fake_get)

    with pytest.raises(RegistryError, match="Timeout"):
        client.get_package_metadata("slow")


def test_get_package_metadata_request_exception_raises_registry_error(monkeypatch):
    client = RegistryClient("https://registry.npmjs.org")

    def fake_get(*args, **kwargs):
        raise requests.exceptions.ConnectionError("no route to host")

    monkeypatch.setattr(client.session, "get", fake_get)

    with pytest.raises(RegistryError, match="Network error"):
        client.get_package_metadata("anything")