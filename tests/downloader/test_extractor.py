"""
Tests for teloce_npm.downloader.extractor.extract_tarball.

Scope: tar extraction + security checks.
Creates real .tgz files in tmp_path — no mocking needed.
"""

import io
import tarfile

import pytest

from teloce_npm.downloader import extract_tarball
from teloce_npm.utils.errors import TeloceNpmError, SecurityError


def _make_tarball(path, files):
    """
    Create a valid npm-style .tgz.

    Args:
        path: Destination .tgz path.
        files: Dict of {relpath_in_tarball: content_bytes_or_str}.
               Keys should typically start with 'package/'.
    """
    with tarfile.open(path, "w:gz") as tar:
        for relpath, content in files.items():
            data = content.encode("utf-8") if isinstance(content, str) else content
            info = tarfile.TarInfo(name=relpath)
            info.size = len(data)
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(data))


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------
def test_extract_tarball_extracts_files(tmp_path):
    tarball = tmp_path / "pkg.tgz"
    _make_tarball(tarball, {
        "package/package.json": '{"name": "test"}',
        "package/index.js": "module.exports = 1;",
    })
    extract_dir = tmp_path / "out"

    extract_tarball(tarball, extract_dir)

    assert (extract_dir / "package" / "package.json").exists()
    assert (extract_dir / "package" / "index.js").exists()


def test_extract_tarball_returns_package_dir(tmp_path):
    tarball = tmp_path / "pkg.tgz"
    _make_tarball(tarball, {"package/package.json": "{}"})
    extract_dir = tmp_path / "out"

    result = extract_tarball(tarball, extract_dir)

    assert result == extract_dir / "package"
    assert result.is_dir()


def test_extract_tarball_fallback_when_no_package_dir(tmp_path):
    """If the tarball has no top-level 'package/' dir, return extract_dir."""
    tarball = tmp_path / "pkg.tgz"
    _make_tarball(tarball, {"index.js": "module.exports = 1;"})
    extract_dir = tmp_path / "out"

    result = extract_tarball(tarball, extract_dir)

    assert result == extract_dir
    assert (result / "index.js").exists()


# ---------------------------------------------------------------------------
# Directory hygiene
# ---------------------------------------------------------------------------
def test_extract_tarball_cleans_existing_extract_dir(tmp_path):
    tarball = tmp_path / "pkg.tgz"
    _make_tarball(tarball, {"package/index.js": "new"})

    extract_dir = tmp_path / "out"
    extract_dir.mkdir()
    (extract_dir / "old-file.txt").write_text("stale")

    extract_tarball(tarball, extract_dir)

    # Old file should be gone (extract_dir was rmtree'd first)
    assert not (extract_dir / "old-file.txt").exists()
    assert (extract_dir / "package" / "index.js").exists()


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------
def test_extract_tarball_missing_file_raises(tmp_path):
    with pytest.raises(TeloceNpmError, match="not found"):
        extract_tarball(tmp_path / "nonexistent.tgz", tmp_path / "out")


def test_extract_tarball_invalid_gzip_raises(tmp_path):
    tarball = tmp_path / "bad.tgz"
    tarball.write_bytes(b"not a gzip file")
    extract_dir = tmp_path / "out"

    with pytest.raises(TeloceNpmError, match="Failed to extract"):
        extract_tarball(tarball, extract_dir)


# ---------------------------------------------------------------------------
# Security: path traversal
# ---------------------------------------------------------------------------
def test_extract_tarball_rejects_absolute_path(tmp_path):
    tarball = tmp_path / "pkg.tgz"
    _make_tarball(tarball, {"/etc/passwd": "malicious"})
    extract_dir = tmp_path / "out"

    with pytest.raises(SecurityError, match="Unsafe path"):
        extract_tarball(tarball, extract_dir)


def test_extract_tarball_rejects_relative_traversal(tmp_path):
    tarball = tmp_path / "pkg.tgz"
    _make_tarball(tarball, {"../../etc/passwd": "malicious"})
    extract_dir = tmp_path / "out"

    with pytest.raises(SecurityError, match="Unsafe path"):
        extract_tarball(tarball, extract_dir)


# ---------------------------------------------------------------------------
# Security: symlinks
# ---------------------------------------------------------------------------
def test_extract_tarball_rejects_symlink(tmp_path):
    """A symlink pointing outside the package must be rejected."""
    tarball = tmp_path / "pkg.tgz"

    with tarfile.open(tarball, "w:gz") as tar:
        # Add a valid file first
        data = b"{}"
        info = tarfile.TarInfo("package/package.json")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))

        # Add a symlink
        link = tarfile.TarInfo("package/evil-link")
        link.type = tarfile.SYMTYPE
        link.linkname = "/etc/passwd"
        tar.addfile(link)

    extract_dir = tmp_path / "out"

    with pytest.raises(SecurityError, match="Symlink"):
        extract_tarball(tarball, extract_dir)


# ---------------------------------------------------------------------------
# Round-trip sanity
# ---------------------------------------------------------------------------
def test_extract_tarball_round_trip(tmp_path):
    """Create → extract → verify content matches exactly."""
    tarball = tmp_path / "pkg.tgz"
    original = b"const x = 42;\nconsole.log(x);\n"
    _make_tarball(tarball, {"package/index.js": original})

    extract_dir = tmp_path / "out"
    package_dir = extract_tarball(tarball, extract_dir)

    extracted = (package_dir / "index.js").read_bytes()
    assert extracted == original