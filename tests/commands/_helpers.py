"""Shared helpers for command tests (not collected by pytest)."""

import json
from pathlib import Path


def setup_project(tmp_path: Path, packages=None) -> Path:
    """Create a minimal Teloce project structure in tmp_path."""
    (tmp_path / "templates").mkdir(exist_ok=True)
    (tmp_path / "templates" / "index.html").write_text(
        "<!DOCTYPE html><html><head></head><body></body></html>",
        encoding="utf-8",
    )
    (tmp_path / "static" / "js").mkdir(parents=True, exist_ok=True)
    config = {"packages": packages or []}
    (tmp_path / "teloce-npm.json").write_text(json.dumps(config), encoding="utf-8")
    return tmp_path


def fake_install(self, name, version_range, no_verify):
    """Fake _install_package that updates lockfile + writes output."""
    self.lockfile.add_package(
        package_name=name,
        version="1.0.0",
        resolved_url=f"https://fake/{name}-1.0.0.tgz",
        integrity=f"sha512-{name}",
        wrapped_filename=f"{name}.js",
        size=100,
        dependencies={},
        scan_result="clean",
    )
    out_path = self.adapter.wrapped_file_path(name)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(f"window['{name}'] = {{}};", encoding="utf-8")
    return "1.0.0"


def fake_metadata(name, version="1.0.0", description="fake"):
    """Fake registry metadata for a single-version package."""
    return {
        "name": name,
        "dist-tags": {"latest": version},
        "versions": {
            version: {
                "name": name,
                "version": version,
                "description": description,
                "dist": {
                    "tarball": f"https://fake/{name}-{version}.tgz",
                    "integrity": f"sha512-{name}",
                },
                "dependencies": {},
                "scripts": {},
            }
        },
    }
