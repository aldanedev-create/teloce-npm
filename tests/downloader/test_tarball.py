"""
Tests for teloce_npm.downloader.tarball.download_tarball.

Scope: HTTP download + integrity verification.
All HTTP is mocked.

Uses `unittest.mock.patch` on `requests.get` inside the tarball module.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from teloce_npm.downloader import download_tarball
from teloce_npm.utils.errors import RegistryError, SecurityError
from teloce_npm.utils.hashing import compute_sha512


def _make_mock_response(chunks, status=200):
    """Build a mock response that supports the `with` context manager."""
    resp = MagicMock()
    resp.status_code = status
    resp.iter_content.return_value = chunks

    if status >= 400:
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f"HTTP {status}"
        )

    # __enter__ returns the response itself
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    return resp


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------
def test_download_tarball_saves_file(tmp_path):
    content = b"fake tarball bytes"
    integrity = compute_sha512(content)
    dest = tmp_path / "pkg.tgz"

    mock_resp = _make_mock_response([content])
    with patch("teloce_npm.downloader.tarball.requests.get", return_value=mock_resp):
        result = download_tarball(
            tarball_url="https://reg.example.com/pkg.tgz",
            dest_path=dest,
            expected_integrity=integrity,
        )

    assert result == dest
    assert dest.exists()
    assert dest.read_bytes() == content


def test_download_tarball_handles_multiple_chunks(tmp_path):
    chunks = [b"part1-", b"part2-", b"part3"]
    full = b"".join(chunks)
    integrity = compute_sha512(full)
    dest = tmp_path / "pkg.tgz"

    mock_resp = _make_mock_response(chunks)
    with patch("teloce_npm.downloader.tarball.requests.get", return_value=mock_resp):
        download_tarball(
            tarball_url="https://reg.example.com/pkg.tgz",
            dest_path=dest,
            expected_integrity=integrity,
        )

    assert dest.read_bytes() == full


def test_download_tarball_creates_parent_dirs(tmp_path):
    content = b"data"
    integrity = compute_sha512(content)
    dest = tmp_path / "deeply" / "nested" / "pkg.tgz"

    mock_resp = _make_mock_response([content])
    with patch("teloce_npm.downloader.tarball.requests.get", return_value=mock_resp):
        download_tarball(
            tarball_url="https://reg.example.com/pkg.tgz",
            dest_path=dest,
            expected_integrity=integrity,
        )

    assert dest.exists()


# ---------------------------------------------------------------------------
# Integrity failure
# ---------------------------------------------------------------------------
def test_download_tarball_integrity_mismatch_raises(tmp_path):
    content = b"real content"
    wrong_integrity = "sha512-" + "A" * 86
    dest = tmp_path / "pkg.tgz"

    mock_resp = _make_mock_response([content])
    with patch("teloce_npm.downloader.tarball.requests.get", return_value=mock_resp):
        with pytest.raises(SecurityError, match="Integrity check failed"):
            download_tarball(
                tarball_url="https://reg.example.com/pkg.tgz",
                dest_path=dest,
                expected_integrity=wrong_integrity,
            )


def test_download_tarball_integrity_mismatch_deletes_file(tmp_path):
    content = b"real content"
    wrong_integrity = "sha512-" + "A" * 86
    dest = tmp_path / "pkg.tgz"

    mock_resp = _make_mock_response([content])
    with patch("teloce_npm.downloader.tarball.requests.get", return_value=mock_resp):
        with pytest.raises(SecurityError):
            download_tarball(
                tarball_url="https://reg.example.com/pkg.tgz",
                dest_path=dest,
                expected_integrity=wrong_integrity,
            )

    # The corrupted file must be removed
    assert not dest.exists()


# ---------------------------------------------------------------------------
# HTTP errors
# ---------------------------------------------------------------------------
def test_download_tarball_http_500_raises_registry_error(tmp_path):
    dest = tmp_path / "pkg.tgz"
    mock_resp = _make_mock_response([], status=500)

    with patch("teloce_npm.downloader.tarball.requests.get", return_value=mock_resp):
        with pytest.raises(RegistryError, match="Failed to download"):
            download_tarball(
                tarball_url="https://reg.example.com/pkg.tgz",
                dest_path=dest,
                expected_integrity="sha512-whatever",
            )


def test_download_tarball_network_error_raises_registry_error(tmp_path):
    dest = tmp_path / "pkg.tgz"

    with patch(
        "teloce_npm.downloader.tarball.requests.get",
        side_effect=requests.exceptions.ConnectionError("no route"),
    ):
        with pytest.raises(RegistryError, match="Failed to download"):
            download_tarball(
                tarball_url="https://reg.example.com/pkg.tgz",
                dest_path=dest,
                expected_integrity="sha512-whatever",
            )


def test_download_tarball_cleans_up_on_network_error(tmp_path):
    dest = tmp_path / "pkg.tgz"

    with patch(
        "teloce_npm.downloader.tarball.requests.get",
        side_effect=requests.exceptions.ConnectionError("no route"),
    ):
        with pytest.raises(RegistryError):
            download_tarball(
                tarball_url="https://reg.example.com/pkg.tgz",
                dest_path=dest,
                expected_integrity="sha512-whatever",
            )

    assert not dest.exists()