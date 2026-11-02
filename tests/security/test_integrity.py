"""
Tests for teloce_npm.security.integrity.IntegrityVerifier.

Scope: only the IntegrityVerifier wrapper interface.
SHA-512 math is tested separately in tests/utils/test_hashing.py.
"""

import pytest

from teloce_npm.security.integrity import IntegrityVerifier
from teloce_npm.utils.hashing import compute_sha512
from teloce_npm.utils.errors import SecurityError


def test_verify_tarball_matching_hash(tmp_path):
    content = b"fake tarball content"
    path = tmp_path / "pkg.tgz"
    path.write_bytes(content)

    verifier = IntegrityVerifier()
    assert verifier.verify_tarball(path, compute_sha512(content)) is True


def test_verify_tarball_mismatch_raises(tmp_path):
    path = tmp_path / "pkg.tgz"
    path.write_bytes(b"real content")
    wrong = "sha512-" + "A" * 86

    verifier = IntegrityVerifier()
    with pytest.raises(SecurityError, match="Integrity check failed"):
        verifier.verify_tarball(path, wrong)


def test_verify_bytes_matching():
    content = b"data"
    verifier = IntegrityVerifier()
    assert verifier.verify_bytes(content, compute_sha512(content)) is True


def test_verify_bytes_mismatch_raises():
    verifier = IntegrityVerifier()
    with pytest.raises(SecurityError):
        verifier.verify_bytes(b"data", "sha512-" + "B" * 86)


def test_compute_returns_sri_hash(tmp_path):
    path = tmp_path / "x.bin"
    path.write_bytes(b"content")

    verifier = IntegrityVerifier()
    assert verifier.compute(path) == compute_sha512(b"content")