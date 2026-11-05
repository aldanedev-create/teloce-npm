"""Registry client hardening: input validation, response checks, retries."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from teloce_npm.registry import RegistryClient
from teloce_npm.utils.errors import RegistryError, SecurityError


def _resp(status=200, data=None):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = data if data is not None else {}
    if status >= 400:
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(f"HTTP {status}")
    return resp


@pytest.mark.parametrize("name", ["../etc/passwd", "a/b", "", "..", "x y", "lodash\n"])
def test_invalid_package_name_never_reaches_the_network(name):
    client = RegistryClient("https://registry.npmjs.org")
    with patch.object(client.session, "get") as get:
        with pytest.raises(SecurityError):
            client.get_package_metadata(name)
        get.assert_not_called()


def test_registry_must_answer_for_the_requested_package():
    client = RegistryClient("https://registry.npmjs.org")
    with patch.object(client.session, "get", return_value=_resp(data={"name": "something-else"})):
        with pytest.raises(SecurityError, match="something-else"):
            client.get_package_metadata("lodash")


def test_name_comparison_ignores_case():
    client = RegistryClient("https://registry.npmjs.org")
    with patch.object(client.session, "get", return_value=_resp(data={"name": "JSONStream"})):
        assert client.get_package_metadata("jsonstream")["name"] == "JSONStream"


def test_http_registry_url_is_rejected_but_loopback_is_allowed():
    with pytest.raises(SecurityError):
        RegistryClient("http://registry.example.com")
    assert RegistryClient("http://localhost:4873/").registry_url == "http://localhost:4873"


def test_transient_errors_are_retried():
    client = RegistryClient("https://registry.npmjs.org")
    replies = [_resp(503), requests.exceptions.ConnectionError("reset"), _resp(data={"name": "lodash"})]
    with patch.object(client.session, "get", side_effect=replies) as get:
        assert client.get_package_metadata("lodash")["name"] == "lodash"
    assert get.call_count == 3


def test_persistent_failure_is_reported_after_retries():
    client = RegistryClient("https://registry.npmjs.org")
    with patch.object(client.session, "get", return_value=_resp(503)) as get:
        with pytest.raises(RegistryError):
            client.get_package_metadata("lodash")
    assert get.call_count == 3


def test_not_found_is_not_retried():
    client = RegistryClient("https://registry.npmjs.org")
    with patch.object(client.session, "get", return_value=_resp(404)) as get:
        with pytest.raises(Exception, match="not found"):
            client.get_package_metadata("nope")
    assert get.call_count == 1
