"""
Tests for teloce_npm.utils.hashing.

Uses self-consistency assertions (compute-then-verify) rather than
hardcoded digests so the tests stay correct across Python versions.
"""

import pytest

from teloce_npm.utils.errors import SecurityError
from teloce_npm.utils.hashing import (
    compute_file_sha512,
    compute_sha512,
    verify_file_integrity,
    verify_integrity,
)


# ---------------------------------------------------------------------------
# compute_sha512
# ---------------------------------------------------------------------------
def test_compute_sha512_format(known_bytes):
    digest = compute_sha512(known_bytes)
    assert digest.startswith("sha512-")


def test_compute_sha512_is_deterministic(known_bytes):
    assert compute_sha512(known_bytes) == compute_sha512(known_bytes)


def test_compute_sha512_differs_for_different_inputs():
    assert compute_sha512(b"a") != compute_sha512(b"b")


def test_compute_sha512_empty_input():
    digest = compute_sha512(b"")
    assert digest.startswith("sha512-")


# ---------------------------------------------------------------------------
# compute_file_sha512
# ---------------------------------------------------------------------------
def test_compute_file_sha512_matches_bytes(tmp_path):
    content = b"the quick brown fox jumps over the lazy dog"
    file_path = tmp_path / "sample.txt"
    file_path.write_bytes(content)

    assert compute_file_sha512(file_path) == compute_sha512(content)


def test_compute_file_sha512_empty_file(tmp_path):
    empty = tmp_path / "empty.bin"
    empty.write_bytes(b"")
    assert compute_file_sha512(empty) == compute_sha512(b"")


# ---------------------------------------------------------------------------
# verify_integrity (bytes)
# ---------------------------------------------------------------------------
def test_verify_integrity_accepts_matching_hash(known_bytes):
    expected = compute_sha512(known_bytes)
    assert verify_integrity(known_bytes, expected) is True


def test_verify_integrity_rejects_mismatch(known_bytes):
    wrong = "sha512-" + "A" * 86
    with pytest.raises(SecurityError, match="Integrity check failed"):
        verify_integrity(known_bytes, wrong)


# ---------------------------------------------------------------------------
# verify_file_integrity
# ---------------------------------------------------------------------------
def test_verify_file_integrity_accepts_matching_hash(tmp_path):
    file_path = tmp_path / "data.bin"
    file_path.write_bytes(b"data")
    expected = compute_sha512(b"data")

    assert verify_file_integrity(file_path, expected) is True


def test_verify_file_integrity_rejects_mismatch(tmp_path):
    file_path = tmp_path / "data.bin"
    file_path.write_bytes(b"data")
    wrong = "sha512-" + "B" * 86

    with pytest.raises(SecurityError):
        verify_file_integrity(file_path, wrong)
