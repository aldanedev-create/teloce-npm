"""Extraction hardening: special files, limits, path rules and permissions."""

import io
import stat
import tarfile

import pytest

from teloce_npm.downloader.extractor import ExtractionLimits, extract_tarball
from teloce_npm.utils.errors import SecurityError


def _tarball(tmp_path, members):
    """members: list of (name, bytes|None, type, mode)."""
    path = tmp_path / "t.tgz"
    with tarfile.open(path, "w:gz") as tar:
        for name, content, kind, mode in members:
            info = tarfile.TarInfo(name)
            info.type = kind
            info.mode = mode
            if content is not None:
                info.size = len(content)
                tar.addfile(info, io.BytesIO(content))
            else:
                tar.addfile(info)
    return path


def _file(name, content=b"x", mode=0o644):
    return (name, content, tarfile.REGTYPE, mode)


@pytest.mark.parametrize("kind", [tarfile.CHRTYPE, tarfile.BLKTYPE, tarfile.FIFOTYPE])
def test_device_files_and_fifos_are_rejected(tmp_path, kind):
    tarball = _tarball(tmp_path, [_file("package/package.json"), ("package/dev", None, kind, 0o666)])
    with pytest.raises(SecurityError, match="Unsupported file type"):
        extract_tarball(tarball, tmp_path / "out")


def test_hard_links_are_rejected(tmp_path):
    link = ("package/link", None, tarfile.LNKTYPE, 0o644)
    tarball = _tarball(tmp_path, [_file("package/package.json"), link])
    with pytest.raises(SecurityError, match="Symlinks"):
        extract_tarball(tarball, tmp_path / "out")


@pytest.mark.parametrize("name", ["package\\..\\evil.js", "C:evil.js"])
def test_backslash_and_drive_letter_names_are_rejected(tmp_path, name):
    tarball = _tarball(tmp_path, [_file(name)])
    with pytest.raises(SecurityError, match="Unsafe path"):
        extract_tarball(tarball, tmp_path / "out")


def test_dotdot_inside_a_file_name_is_allowed(tmp_path):
    tarball = _tarball(tmp_path, [_file("package/package.json"), _file("package/a..b.js")])
    package = extract_tarball(tarball, tmp_path / "out")
    assert (package / "a..b.js").exists()


def test_file_count_limit(tmp_path):
    tarball = _tarball(tmp_path, [_file(f"package/f{i}.js") for i in range(5)])
    with pytest.raises(SecurityError, match="more than 3 files"):
        extract_tarball(tarball, tmp_path / "out", ExtractionLimits(max_files=3))


def test_single_file_size_limit(tmp_path):
    tarball = _tarball(tmp_path, [_file("package/big.js", b"x" * 2000)])
    with pytest.raises(SecurityError, match="over the 1000 byte limit"):
        extract_tarball(tarball, tmp_path / "out", ExtractionLimits(max_file_bytes=1000))


def test_total_unpacked_size_limit(tmp_path):
    tarball = _tarball(tmp_path, [_file(f"package/f{i}.js", b"x" * 600) for i in range(3)])
    with pytest.raises(SecurityError, match="unpacks to more than"):
        extract_tarball(tarball, tmp_path / "out", ExtractionLimits(max_total_bytes=1500))


def test_decompression_bomb_is_stopped_by_declared_size(tmp_path):
    """A tiny .tgz that expands to a huge file is rejected before it is written."""
    tarball = _tarball(tmp_path, [_file("package/zeros.bin", b"\0" * (5 * 1024 * 1024))])
    assert tarball.stat().st_size < 20_000
    with pytest.raises(SecurityError):
        extract_tarball(tarball, tmp_path / "out", ExtractionLimits(max_file_bytes=1024 * 1024))
    assert not (tmp_path / "out" / "package" / "zeros.bin").exists()


def test_setuid_and_world_writable_bits_are_dropped(tmp_path):
    members = [_file("package/a.js", mode=0o4777), _file("package/run.sh", mode=0o2755)]
    package = extract_tarball(_tarball(tmp_path, members), tmp_path / "out")
    assert stat.S_IMODE((package / "a.js").stat().st_mode) == 0o755  # owner-exec bit kept, nothing else
    for name in ("a.js", "run.sh"):
        mode = (package / name).stat().st_mode
        assert not mode & (stat.S_ISUID | stat.S_ISGID | stat.S_IWGRP | stat.S_IWOTH)


def test_nothing_is_written_outside_the_extraction_root(tmp_path):
    tarball = _tarball(tmp_path, [_file("package/ok.js"), _file("package/../../escape.js")])
    with pytest.raises(SecurityError):
        extract_tarball(tarball, tmp_path / "sandbox" / "out")
    assert not (tmp_path / "escape.js").exists()
    assert not (tmp_path / "sandbox" / "escape.js").exists()
