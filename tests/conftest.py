"""
Shared pytest fixtures for Teloce-NPM tests.
"""

import pytest
from pathlib import Path


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal Teloce project structure for tests."""
    (tmp_path / "templates").mkdir()
    (tmp_path / "static" / "js").mkdir(parents=True)
    (tmp_path / "templates" / "index.html").write_text(
        "<!DOCTYPE html><html><head></head><body></body></html>",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def sample_config() -> dict:
    """Return a valid, complete config dict (matching DEFAULT_CONFIG shape)."""
    return {
        "packages": ["lodash"],
        "entry_html": "templates/index.html",
        "output_dir": "dist/static/teloce-npm",
        "cache_dir": ".teloce-npm/cache",
        "registry": "https://registry.npmjs.org",
        "security": {
            "verify_integrity": True,
            "scan_malware": True,
            "block_install_scripts": True,
            "check_vulnerabilities": True,
        },
    }


@pytest.fixture
def known_bytes() -> bytes:
    """A fixed byte string for hashing tests."""
    return b"hello world"