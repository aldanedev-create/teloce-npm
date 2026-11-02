"""
Tests for the DEFAULT_CONFIG values themselves.

This file only tests the raw default values defined in
`teloce_npm.config.defaults`. The loading/merging logic is tested
in `tests/config/test_loader.py`, and validation in
`tests/config/test_schema.py`.
"""

from teloce_npm.config.defaults import DEFAULT_CONFIG


def test_packages_default_is_empty_list():
    assert DEFAULT_CONFIG["packages"] == []
    assert isinstance(DEFAULT_CONFIG["packages"], list)


def test_entry_html_default():
    assert DEFAULT_CONFIG["entry_html"] == "templates/index.html"


def test_output_dir_default():
    assert DEFAULT_CONFIG["output_dir"] == "dist/static/teloce-npm"


def test_cache_dir_default():
    assert DEFAULT_CONFIG["cache_dir"] == ".teloce-npm/cache"


def test_registry_default():
    assert DEFAULT_CONFIG["registry"] == "https://registry.npmjs.org"


def test_security_block_is_dict_with_all_keys():
    security = DEFAULT_CONFIG["security"]
    assert isinstance(security, dict)
    for key in (
        "verify_integrity",
        "scan_malware",
        "block_install_scripts",
        "check_vulnerabilities",
    ):
        assert key in security, f"Missing security key: {key}"
        assert security[key] is True, f"{key} should default to True"
