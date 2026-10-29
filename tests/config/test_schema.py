"""
Tests for teloce_npm.config.schema.validate_config.

Only tests the schema validator in isolation. The loader's merge-then-
validate flow is tested separately in test_loader.py.
"""

import pytest

from teloce_npm.config.schema import validate_config
from teloce_npm.utils.errors import ConfigError


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------
def test_valid_config_passes(sample_config):
    validate_config(sample_config)  # should not raise


# ---------------------------------------------------------------------------
# Missing required keys
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "missing_key",
    ["packages", "entry_html", "output_dir", "registry", "security"],
)
def test_missing_required_key_raises(sample_config, missing_key):
    config = dict(sample_config)
    del config[missing_key]

    with pytest.raises(ConfigError, match=missing_key):
        validate_config(config)


# ---------------------------------------------------------------------------
# Type validation
# ---------------------------------------------------------------------------
def test_non_list_packages_raises(sample_config):
    config = dict(sample_config, packages="lodash")
    with pytest.raises(ConfigError, match="packages"):
        validate_config(config)


def test_packages_with_non_string_item_raises(sample_config):
    config = dict(sample_config, packages=["lodash", 42])
    with pytest.raises(ConfigError, match="packages"):
        validate_config(config)


def test_non_string_entry_html_raises(sample_config):
    config = dict(sample_config, entry_html=123)
    with pytest.raises(ConfigError, match="entry_html"):
        validate_config(config)


def test_non_string_output_dir_raises(sample_config):
    config = dict(sample_config, output_dir=["dist"])
    with pytest.raises(ConfigError, match="output_dir"):
        validate_config(config)


def test_non_string_registry_raises(sample_config):
    config = dict(sample_config, registry=None)
    with pytest.raises(ConfigError, match="registry"):
        validate_config(config)


# ---------------------------------------------------------------------------
# Registry URL validation
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("bad_registry", ["ftp://example.com", "registry.npmjs.org", ""])
def test_registry_without_http_raises(sample_config, bad_registry):
    config = dict(sample_config, registry=bad_registry)
    with pytest.raises(ConfigError, match="registry"):
        validate_config(config)


def test_registry_with_http_scheme_passes(sample_config):
    config = dict(sample_config, registry="http://my-mirror.internal")
    validate_config(config)  # should not raise


# ---------------------------------------------------------------------------
# Security block validation
# ---------------------------------------------------------------------------
def test_non_dict_security_raises(sample_config):
    config = dict(sample_config, security=True)
    with pytest.raises(ConfigError, match="security"):
        validate_config(config)


@pytest.mark.parametrize(
    "missing_key",
    ["verify_integrity", "scan_malware", "block_install_scripts", "check_vulnerabilities"],
)
def test_missing_security_key_raises(sample_config, missing_key):
    security = dict(sample_config["security"])
    del security[missing_key]
    config = dict(sample_config, security=security)

    with pytest.raises(ConfigError, match=missing_key):
        validate_config(config)


@pytest.mark.parametrize(
    "security_key",
    ["verify_integrity", "scan_malware", "block_install_scripts", "check_vulnerabilities"],
)
def test_non_bool_security_value_raises(sample_config, security_key):
    security = dict(sample_config["security"])
    security[security_key] = "yes"
    config = dict(sample_config, security=security)

    with pytest.raises(ConfigError, match=security_key):
        validate_config(config)