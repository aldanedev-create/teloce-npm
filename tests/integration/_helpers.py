"""Shared helpers for integration tests."""

import io
import json
import tarfile
from pathlib import Path

from teloce_npm.utils.hashing import compute_sha512


def make_fake_tarball(pkg_name: str = "lodash", version: str = "4.17.21") -> bytes:
    """
    Build a minimal, valid .tgz tarball with a `package/` prefix.
    Contains just package.json and index.js — enough for the wrapper
    to run and for security checks to pass.
    """
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        files = {
            "package/package.json": json.dumps({
                "name": pkg_name,
                "version": version,
                "main": "index.js",
                "scripts": {},
            }).encode("utf-8"),
            "package/index.js": b"module.exports = {};",
        }
        for name, content in files.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(content)
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(content))
    return buf.getvalue()


def fake_registry_metadata(pkg_name: str, version: str, integrity: str):
    """Fake registry JSON response for a single-version package."""
    return {
        "name": pkg_name,
        "dist-tags": {"latest": version},
        "versions": {
            version: {
                "name": pkg_name,
                "version": version,
                "description": "fake",
                "dist": {
                    "tarball": f"https://fake/{pkg_name}-{version}.tgz",
                    "integrity": integrity,
                },
                "dependencies": {},
                "scripts": {},
            }
        },
    }


def setup_project(tmp_path: Path, vel_content: str = "Use lodash from teloce-npm\n",
                  entry_html: str = "templates/index.html") -> Path:
    """Create a minimal project with a .vel file and entry HTML."""
    (tmp_path / "static" / "js").mkdir(parents=True, exist_ok=True)
    (tmp_path / "static" / "js" / "App.vel").write_text(vel_content, encoding="utf-8")

    entry_path = tmp_path / entry_html
    entry_path.parent.mkdir(parents=True, exist_ok=True)
    entry_path.write_text(
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head><title>Test</title></head>\n"
        "<body><div id='app'></div></body>\n"
        "</html>",
        encoding="utf-8",
    )

    (tmp_path / "teloce-npm.json").write_text(
        json.dumps({"packages": []}), encoding="utf-8"
    )
    return tmp_path