"""Download hardening: URL policy, size cap, atomic writes, redirects, retries."""

import base64
import hashlib
from unittest.mock import MagicMock, patch

import pytest
import requests

from teloce_npm.downloader import download_tarball
from teloce_npm.utils.errors import RegistryError, SecurityError

URL = "https://registry.npmjs.org/pkg/-/pkg-1.0.0.tgz"
DATA = b"tarball-bytes" * 100


def _sri(data: bytes) -> str:
    return "sha512-" + base64.b64encode(hashlib.sha512(data).digest()).decode()


def _response(chunks=(DATA,), status=200, headers=None):
    resp = MagicMock()
    resp.status_code = status
    resp.headers = headers or {}
    resp.iter_content.return_value = list(chunks)
    if status >= 400:
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(f"HTTP {status}")
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    return resp


def _get(*responses):
    return patch("teloce_npm.downloader.tarball.requests.get", side_effect=list(responses))


def _leftovers(directory):
    return [p.name for p in directory.iterdir()]


def test_plain_http_url_is_rejected(tmp_path):
    with pytest.raises(SecurityError, match="https"):
        download_tarball("http://registry.npmjs.org/p.tgz", tmp_path / "p.tgz", _sri(DATA))


def test_url_with_credentials_is_rejected(tmp_path):
    with pytest.raises(SecurityError, match="credentials"):
        download_tarball("https://user:pw@registry.npmjs.org/p.tgz", tmp_path / "p.tgz", _sri(DATA))


def test_host_outside_allowlist_is_rejected_before_any_request(tmp_path):
    with patch("teloce_npm.downloader.tarball.requests.get") as get:
        with pytest.raises(SecurityError, match="not an allowed registry host"):
            download_tarball(
                "https://evil.example.com/p.tgz",
                tmp_path / "p.tgz",
                _sri(DATA),
                allowed_hosts=["registry.npmjs.org"],
            )
        get.assert_not_called()


def test_redirect_to_other_host_is_rejected(tmp_path):
    redirect = _response(status=302, headers={"Location": "https://evil.example.com/p.tgz"})
    with _get(redirect), pytest.raises(SecurityError, match="not an allowed registry host"):
        download_tarball(URL, tmp_path / "p.tgz", _sri(DATA), allowed_hosts=["registry.npmjs.org"])
    assert _leftovers(tmp_path) == []


def test_redirect_within_allowed_host_is_followed(tmp_path):
    redirect = _response(status=301, headers={"Location": "/mirror/p.tgz"})
    with _get(redirect, _response()):
        path = download_tarball(URL, tmp_path / "p.tgz", _sri(DATA), allowed_hosts=["registry.npmjs.org"])
    assert path.read_bytes() == DATA


def test_redirect_loop_is_cut_off(tmp_path):
    loop = [_response(status=302, headers={"Location": URL}) for _ in range(10)]
    with _get(*loop), pytest.raises(RegistryError, match="redirects"):
        download_tarball(URL, tmp_path / "p.tgz", _sri(DATA), attempts=1)


def test_declared_content_length_over_limit_is_rejected(tmp_path):
    big = _response(headers={"Content-Length": "999999999"})
    with _get(big), pytest.raises(SecurityError, match="byte limit"):
        download_tarball(URL, tmp_path / "p.tgz", _sri(DATA), max_bytes=1000)
    assert _leftovers(tmp_path) == []


def test_streamed_size_over_limit_is_rejected_without_content_length(tmp_path):
    chunks = [b"x" * 600, b"x" * 600]
    with _get(_response(chunks)), pytest.raises(SecurityError, match="byte limit"):
        download_tarball(URL, tmp_path / "p.tgz", _sri(b"x" * 1200), max_bytes=1000)
    assert _leftovers(tmp_path) == []


def test_failed_integrity_leaves_no_file_and_keeps_existing_good_file(tmp_path):
    dest = tmp_path / "p.tgz"
    dest.write_bytes(b"previous good download")
    with _get(_response()), pytest.raises(SecurityError, match="Integrity check failed"):
        download_tarball(URL, dest, _sri(b"something else"))
    assert dest.read_bytes() == b"previous good download"
    assert _leftovers(tmp_path) == ["p.tgz"]  # no .part file left behind


def test_unsupported_hash_algorithm_is_rejected(tmp_path):
    with pytest.raises(SecurityError, match="sha512"):
        download_tarball(URL, tmp_path / "p.tgz", "sha1-AAAAAAAAAAAAAAAAAAAAAAAAAAA=")


def test_any_listed_sha512_hash_may_match(tmp_path):
    with _get(_response()):
        path = download_tarball(URL, tmp_path / "p.tgz", f"sha512-wrong {_sri(DATA)}")
    assert path.exists()


def test_transient_server_error_is_retried(tmp_path):
    with _get(_response(status=503), _response(status=502), _response()) as get:
        path = download_tarball(URL, tmp_path / "p.tgz", _sri(DATA))
    assert get.call_count == 3
    assert path.read_bytes() == DATA


def test_connection_error_is_retried_then_reported(tmp_path):
    error = requests.exceptions.ConnectionError("reset")
    with patch("teloce_npm.downloader.tarball.requests.get", side_effect=error) as get:
        with pytest.raises(RegistryError, match="Failed to download"):
            download_tarball(URL, tmp_path / "p.tgz", _sri(DATA), attempts=3)
    assert get.call_count == 3


def test_client_error_is_not_retried(tmp_path):
    with _get(_response(status=404)) as get, pytest.raises(RegistryError):
        download_tarball(URL, tmp_path / "p.tgz", _sri(DATA))
    assert get.call_count == 1
